#!/usr/bin/env python3
"""cv-kit's status line launcher. scripts/install_statusline.py copies it to `~/.claude/cv-kit/statusline.py`.

The `statusLine` command is only `<python> <this file> <config>`: no shell syntax, so it runs the same through sh,
Git Bash and PowerShell. Each settings file gets its own config, `statusline-<id>.json` beside this file. A copy at
a fixed path survives plugin updates, which move the plugin root; `agent_rows.py --register` refreshes the copy at
each session start.

On each refresh it reads the status line JSON from stdin, then:

1. runs the user's own status line command, if the config names one, through the shell Claude Code would have used
   (`shell`), with the same stdin, and keeps its output when it exits 0 within `timeout` seconds; past that it kills
   it (the whole tree on Windows, where a grandchild holding the pipe would stall the read) and moves on. When
   Claude Code cancels the launcher, SIGTERM takes the user's command with it;
2. loads `hooks/agent_rows.py` from the plugin root in `~/.cache/cv-kit/agent-rows-root` and adds its rows.

It prints both as UTF-8 and always exits 0: Claude Code blanks the whole status line when the command fails, so a
missing plugin or a broken config must never cost the user their own line. Standard library only.
"""
from __future__ import annotations

import importlib.util
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

POINTER = Path.home() / ".cache" / "cv-kit" / "agent-rows-root"
TIMEOUT = 10  # seconds
CHILD: subprocess.Popen | None = None  # the user's command while it runs


def load_config(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def stop(signum, frame) -> None:
    if CHILD is not None:
        kill_tree(CHILD)
    os._exit(0)


def own_line(config: dict, raw: bytes) -> str:
    global CHILD
    own, shell = config.get("own"), config.get("shell")
    if not isinstance(own, str) or not own or not isinstance(shell, list) or not all(isinstance(s, str) for s in shell):
        return ""
    timeout = config.get("timeout", TIMEOUT)
    timeout = timeout if isinstance(timeout, (int, float)) and not isinstance(timeout, bool) else TIMEOUT
    window = {"creationflags": 0x08000000} if os.name == "nt" else {}  # CREATE_NO_WINDOW
    try:
        CHILD = child = subprocess.Popen([*shell, own], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=subprocess.DEVNULL, **window)
    except (OSError, ValueError):
        return ""
    try:
        out, _ = child.communicate(raw, timeout=timeout)
    except subprocess.TimeoutExpired:
        kill_tree(child)
        return ""
    except (OSError, ValueError):
        return ""
    return out.decode("utf-8", errors="replace").rstrip("\r\n") if child.returncode == 0 else ""


def kill_tree(child: subprocess.Popen) -> None:
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(child.pid)], capture_output=True, timeout=5)
        else:
            child.kill()
    except (OSError, subprocess.SubprocessError):
        pass


def rows(config: dict, raw: bytes) -> list[str]:
    try:
        script = Path(POINTER.read_text(encoding="utf-8").strip()) / "hooks" / "agent_rows.py"
        spec = importlib.util.spec_from_file_location("cv_kit_agent_rows", script)
        if spec is None or spec.loader is None or not script.is_file():
            return []
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        text = raw.decode("utf-8", errors="replace")
        try:
            return module.status_line(text, ascii=config.get("ascii") is True,
                                      main=config.get("main", True) is not False)
        except TypeError:  # the pointer names a 0.10 plugin root, whose status_line takes only the input
            return module.status_line(text)
    except Exception:
        return []


def main() -> int:
    try:
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, stop)
        raw = sys.stdin.buffer.read()
        config = load_config(Path(sys.argv[1])) if len(sys.argv) > 1 else {}
        out = [line for line in [own_line(config, raw)] if line] + rows(config, raw)
        if out:
            sys.stdout.buffer.write(("\n".join(out) + "\n").encode("utf-8"))
            sys.stdout.flush()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
