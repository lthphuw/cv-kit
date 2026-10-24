"""The evidence gate: a hook that stops 'done' being claimed after code edits with no passing test run."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))

import evidence_gate as gate  # noqa: E402

SID = "session-1"


def bash(command: str, event: str = "PostToolUse", sid: str = SID) -> dict:
    return {"hook_event_name": event, "session_id": sid, "tool_name": "Bash", "tool_input": {"command": command}}


def edit(path: str, sid: str = SID) -> dict:
    return {"hook_event_name": "PostToolUse", "session_id": sid, "tool_name": "Edit", "tool_input": {"file_path": path}}


def stop(sid: str = SID, **extra) -> dict:
    return {"hook_event_name": "Stop", "session_id": sid, "stop_hook_active": False, **extra}


@pytest.fixture
def state(tmp_path: Path) -> Path:
    return tmp_path / "gate"


def run(state: Path, *events: dict):
    """Feed the events in order; return the last reply."""
    reply = None
    for event in events:
        reply = gate.handle(event, state)
    return reply


class TestArming:
    def test_does_nothing_until_armed(self, state):
        assert run(state, edit("src/a.py"), stop()) is None

    def test_arm_then_edit_then_stop_blocks(self, state):
        gate.arm(SID, state)
        reply = run(state, edit("src/a.py"), stop())
        assert reply["decision"] == "block"
        assert "no test" in reply["reason"].lower()

    def test_sessions_are_separate(self, state):
        gate.arm(SID, state)
        assert run(state, edit("src/a.py", sid="other"), stop(sid="other")) is None

    @pytest.mark.parametrize("sid", ["../../etc/passwd", "a/b", "", "x" * 500])
    def test_a_hostile_session_id_stays_inside_the_state_folder(self, state, sid):
        gate.arm(sid, state)
        assert all(state in p.parents for p in state.rglob("*") if p.is_file())
        assert not (state.parent / "etc").exists()


class TestVerdict:
    def test_a_passing_test_run_after_the_edit_allows_stopping(self, state):
        gate.arm(SID, state)
        assert run(state, edit("src/a.py"), bash("pytest -q"), stop()) is None

    def test_a_failed_test_run_blocks_and_says_it_failed(self, state):
        gate.arm(SID, state)
        reply = run(state, edit("src/a.py"), bash("pytest -q", event="PostToolUseFailure"), stop())
        assert reply["decision"] == "block"
        assert "failed" in reply["reason"].lower()

    def test_an_edit_after_a_green_run_makes_it_stale(self, state):
        gate.arm(SID, state)
        reply = run(state, edit("src/a.py"), bash("pytest"), edit("src/b.py"), stop())
        assert reply["decision"] == "block"

    def test_blocks_once_per_stale_state_so_it_cannot_loop(self, state):
        gate.arm(SID, state)
        first = run(state, edit("src/a.py"), stop())
        second = run(state, stop())
        assert first["decision"] == "block"
        assert second is None

    def test_a_new_edit_after_the_nudge_arms_the_gate_again(self, state):
        gate.arm(SID, state)
        run(state, edit("src/a.py"), stop())
        assert run(state, edit("src/a.py"), stop())["decision"] == "block"

    def test_stop_hook_active_never_blocks(self, state):
        gate.arm(SID, state)
        assert run(state, edit("src/a.py"), stop(stop_hook_active=True)) is None

    def test_a_turn_with_no_edit_is_left_alone(self, state):
        gate.arm(SID, state)
        assert run(state, stop()) is None

    def test_does_not_fight_a_test_run_still_in_the_background(self, state):
        gate.arm(SID, state)
        assert run(state, edit("src/a.py"), stop(background_tasks=[{"id": "b1"}])) is None

    def test_subagent_stop_uses_the_same_ledger(self, state):
        gate.arm(SID, state)
        reply = run(state, edit("src/a.py"), {**stop(), "hook_event_name": "SubagentStop"})
        assert reply["decision"] == "block"


class TestWhatCounts:
    @pytest.mark.parametrize("path", ["README.md", "docs/guide.rst", "notes.txt", "data.json", "image.png"])
    def test_a_non_code_edit_is_ignored(self, state, path):
        gate.arm(SID, state)
        assert run(state, edit(path), stop()) is None

    @pytest.mark.parametrize("path", ["a.py", "a.pyi", "a.cc", "a.cpp", "a.h", "a.hpp", "a.cu", "CMakeLists.txt",
                                      "build.cmake", "tests/test_a.py"])
    def test_a_code_edit_counts(self, state, path):
        gate.arm(SID, state)
        assert run(state, edit(path), stop())["decision"] == "block"

    @pytest.mark.parametrize("command", [
        "pytest", "pytest -q tests/test_a.py", "python -m pytest -x", "python3 -m pytest", "uv run pytest",
        "ctest --test-dir build --output-on-failure", "cd build && ctest", "tox", "make test",
        "cmake --build build && ctest --test-dir build", "./build/foo_test", "go test ./...", "cargo test",
    ])
    def test_a_test_command_is_recognised(self, state, command):
        gate.arm(SID, state)
        assert run(state, edit("a.py"), bash(command), stop()) is None

    @pytest.mark.parametrize("command", [
        "ls", "git status", "pytest --collect-only", "pytest --help", "pytest --version", "echo pytest",
        "pytest | tail -5", "pytest || true", "pytest; echo done", "ruff check .", "cmake --build build",
    ])
    def test_a_command_that_proves_nothing_is_not_a_green_run(self, state, command):
        gate.arm(SID, state)
        assert run(state, edit("a.py"), bash(command), stop())["decision"] == "block"

    def test_a_pipe_is_trusted_with_pipefail(self, state):
        gate.arm(SID, state)
        assert run(state, edit("a.py"), bash("set -o pipefail; pytest | tail -5"), stop()) is None


class TestRobustness:
    def test_bad_input_never_raises(self, state):
        assert gate.handle({}, state) is None
        assert gate.handle({"hook_event_name": "Stop"}, state) is None
        assert gate.handle({"hook_event_name": "PostToolUse", "session_id": SID, "tool_input": None}, state) is None

    def test_a_corrupt_state_file_is_replaced(self, state):
        gate.arm(SID, state)
        for path in state.rglob("*.json"):
            path.write_text("{not json")
        assert run(state, edit("a.py"), stop()) is None


class TestCommandLine:
    def script(self, *args: str, stdin: str = "", home: Path) -> subprocess.CompletedProcess:
        env = {"HOME": str(home), "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin", "CV_KIT_GATE_DIR": str(home / "g")}
        return subprocess.run([sys.executable, str(ROOT / "hooks/evidence_gate.py"), *args], input=stdin, env=env,
                              capture_output=True, text=True, check=False)

    def test_arm_prints_one_factual_line(self, tmp_path):
        result = self.script("arm", SID, home=tmp_path)
        assert result.returncode == 0
        assert result.stdout.strip().startswith("Evidence gate: armed")

    def test_a_block_is_printed_as_json_with_exit_zero(self, tmp_path):
        self.script("arm", SID, home=tmp_path)
        self.script(stdin=json.dumps(edit("src/a.py")), home=tmp_path)
        result = self.script(stdin=json.dumps(stop()), home=tmp_path)
        assert result.returncode == 0
        assert json.loads(result.stdout)["decision"] == "block"

    def test_garbage_on_stdin_exits_zero_silently(self, tmp_path):
        result = self.script(stdin="not json", home=tmp_path)
        assert (result.returncode, result.stdout) == (0, "")
