"""Evidence gate: after a code edit, a turn may not end until a test command has passed.

One script for every event it listens to (see hooks/hooks.json). It keeps a small ledger per session:

    arm <session id>    called by the `develop` skill; until then the gate does nothing
    PostToolUse         Edit/Write of a code file marks any earlier green run stale; a passing test command is green
    PostToolUseFailure  a failing test command is recorded as red
    Stop, SubagentStop  block once per stale state with a reason; never twice for the same edit

The gate is a nudge, not a lock: it blocks at most once per edit, never when `stop_hook_active` is set or a
background task is running, and any error lets the turn end. Claude Code also caps consecutive Stop blocks at eight.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import sys
import time
from pathlib import Path

CODE_SUFFIXES = {".py", ".pyi", ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx", ".cu", ".cuh", ".inl",
                 ".ipp", ".cmake", ".go"}
CODE_NAMES = {"CMakeLists.txt"}
EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
RUNNERS = {"pytest", "py.test", "tox", "nox", "ctest", "unittest"}
NOT_A_RUN = {"--collect-only", "--co", "--help", "-h", "--version", "--fixtures", "--markers", "--setup-plan",
             "--show-only", "-N"}
WRAPPERS = {"time", "env", "nice", "command", "exec"}
SESSION_RE = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
SEGMENT_SPLIT = re.compile(r"&&|(?<!\|)\|(?!\|)")
SINGLE_PIPE = re.compile(r"(?<!\|)\|(?!\|)")
MAX_AGE_SECONDS = 7 * 24 * 3600


def state_dir() -> Path:
    override = os.environ.get("CV_KIT_GATE_DIR")
    return Path(override) if override else Path.home() / ".cache" / "cv-kit" / "gate"


def _file(state: Path, session: str) -> Path:
    name = session if SESSION_RE.match(session) else hashlib.sha256(session.encode()).hexdigest()[:32]
    return state / f"{name}.json"


def _load(state: Path, session: str) -> dict | None:
    try:
        data = json.loads(_file(state, session).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) and data.get("armed") is True else None


def _save(state: Path, session: str, data: dict) -> None:
    state.mkdir(parents=True, exist_ok=True)
    target = _file(state, session)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(data), encoding="utf-8")
    os.replace(temporary, target)


def arm(session: str, state: Path) -> None:
    """Start the ledger for a session and drop ledgers that have not been touched for a week."""
    state.mkdir(parents=True, exist_ok=True)
    for old in state.glob("*.json"):
        if time.time() - old.stat().st_mtime > MAX_AGE_SECONDS:
            old.unlink(missing_ok=True)
    _save(state, session, {"armed": True, "seq": 0, "edit": 0, "green": 0, "red": 0, "nudged": 0})


def _tokens(segment: str) -> list[str]:
    try:
        tokens = shlex.split(segment)
    except ValueError:
        tokens = segment.split()
    while tokens:
        head = tokens[0]
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", head) or head in WRAPPERS:
            tokens = tokens[1:]
        elif head in {"uv", "poetry", "pipenv", "pdm", "hatch"} and tokens[1:2] == ["run"]:
            tokens = tokens[2:]
            while tokens and tokens[0].startswith("-"):
                tokens = tokens[1:]
        elif head in {"python", "python3"} and tokens[1:2] == ["-m"]:
            tokens = tokens[2:]
        else:
            break
    return tokens


def _is_test_segment(segment: str) -> bool:
    tokens = _tokens(segment)
    if not tokens or NOT_A_RUN & set(tokens):
        return False
    head, rest = tokens[0], tokens[1:]
    if head in RUNNERS:
        return True
    if head in {"make", "ninja"}:
        return any(t in {"test", "check"} for t in rest)
    if head in {"go", "cargo"}:
        return rest[:1] == ["test"]
    return head.endswith("_test") and ("/" in head)


def runs_tests(command: str) -> bool:
    """True if any part of the command is a test run, whatever its exit status was."""
    return any(_is_test_segment(s) for s in SEGMENT_SPLIT.split(command))


def proves_green(command: str) -> bool:
    """True if a zero exit status of this command means the tests passed."""
    if "||" in command:
        return False
    chunks = [c for c in re.split(r"[;\n]", command) if c.strip()]
    if not chunks:
        return False
    last = chunks[-1]
    if SINGLE_PIPE.search(last) and "pipefail" not in command:
        return False
    return any(_is_test_segment(s) for s in SEGMENT_SPLIT.split(last))


def is_code_file(path: str) -> bool:
    p = Path(path)
    return p.suffix.lower() in CODE_SUFFIXES or p.name in CODE_NAMES


def _reason(data: dict) -> str:
    if data["red"] > data["edit"]:
        status = "the last test run after that edit failed"
    else:
        status = "no test command has passed since that edit"
    return (f"Code was edited and {status}. Run the project's tests and show the result, or say which tests could "
            "not run and why. If the request was only for a failing test (the red step), say so instead.")


def handle(event: dict, state: Path) -> dict | None:
    """Update the ledger for one hook event; return a Stop/SubagentStop block, or None."""
    try:
        name, session = event.get("hook_event_name"), event.get("session_id")
        if not isinstance(name, str) or not isinstance(session, str):
            return None
        data = _load(state, session)
        if data is None:
            return None
        tool_input = event.get("tool_input") if isinstance(event.get("tool_input"), dict) else {}
        if name in {"PostToolUse", "PostToolUseFailure"}:
            tool = event.get("tool_name")
            command = tool_input.get("command")
            if tool in EDIT_TOOLS and isinstance(tool_input.get("file_path"), str) and name == "PostToolUse":
                if is_code_file(tool_input["file_path"]):
                    data["seq"] += 1
                    data["edit"] = data["seq"]
            elif tool == "Bash" and isinstance(command, str):
                if name == "PostToolUse" and proves_green(command):
                    data["seq"] += 1
                    data["green"] = data["seq"]
                elif name == "PostToolUseFailure" and runs_tests(command):
                    data["seq"] += 1
                    data["red"] = data["seq"]
            _save(state, session, data)
            return None
        if name in {"Stop", "SubagentStop"}:
            if event.get("stop_hook_active") or event.get("background_tasks"):
                return None
            if data["edit"] <= data["green"] or data["nudged"] >= data["edit"]:
                return None
            data["nudged"] = data["edit"]
            _save(state, session, data)
            return {"decision": "block", "reason": _reason(data)}
    except (OSError, KeyError, TypeError, ValueError):
        return None
    return None


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args[:1] == ["arm"]:
        session = args[1] if len(args) > 1 else ""
        if not session:
            print("Evidence gate: not armed (no session id)")
            return 0
        arm(session, state_dir())
        print("Evidence gate: armed for this session. After a code edit, a turn cannot end until a test "
              "command has passed.")
        return 0
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    reply = handle(event, state_dir()) if isinstance(event, dict) else None
    if reply:
        print(json.dumps(reply))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
