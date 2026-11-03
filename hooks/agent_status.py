#!/usr/bin/env python3
"""Rewrite each subagent row: `engineer · sonnet · 4m12s · 1.2k tok · running · <label>`.

Claude Code runs this as `subagentStatusLine` (settings.json): stdin is one JSON object with `columns` and `tasks`,
stdout is one `{"id", "content"}` line per row to rewrite. Any error prints nothing, so the default rows stay.

Claude Code leaves `${CLAUDE_PLUGIN_ROOT}` empty in a plugin's `subagentStatusLine` (seen on 2.1.317), so at
SessionStart `--register` writes this plugin's root to `~/.cache/cv-kit/plugin-root` and the command reads it.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

MODELS = ("haiku", "sonnet", "opus", "fable")
CONTROL = re.compile(r"[\x00-\x1f\x7f]+")


def elapsed(start_ms, now_ms) -> str:
    seconds = max(0, int((now_ms - start_ms) // 1000))
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}h{minutes:02d}m"
    return f"{minutes}m{secs:02d}s" if minutes else f"{secs}s"


def short_model(model) -> str:
    text = str(model or "")
    return next((m for m in MODELS if m in text.lower()), text)


def tokens(count) -> str:
    if isinstance(count, bool) or not isinstance(count, (int, float)) or count <= 0:
        return ""
    return f"{count / 1000:.1f}k tok" if count >= 1000 else f"{int(count)} tok"


def row(task: dict, now_ms: float, columns) -> str:
    name = str(task.get("agentType") or "").removeprefix("cv-kit:") or str(task.get("name") or "") or "agent"
    status = str(task.get("status") or "")
    parts = [name, short_model(task.get("model"))]
    if status == "running":  # a finished task has no end time, so a clock would keep counting
        try:
            parts.append(elapsed(float(task["startTime"]), now_ms))
        except (KeyError, TypeError, ValueError):
            pass
    parts.append(tokens(task.get("tokenCount")))
    parts.append(status)
    parts.append(CONTROL.sub(" ", str(task.get("label") or task.get("description") or "")).strip())
    text = re.sub(r" +", " ", " · ".join(p for p in parts if p))
    if isinstance(columns, int) and 0 < columns < len(text):
        text = text[: max(columns - 1, 0)] + "…"
    return text


def render(payload: dict, now_ms: float) -> list[str]:
    lines = []
    columns = payload.get("columns")
    for task in payload.get("tasks", []):
        try:
            lines.append(json.dumps({"id": task["id"], "content": row(task, now_ms, columns)}))
        except Exception:  # one bad row keeps its default; the others still render
            continue
    return lines


def register() -> None:
    # shortcut: one pointer per user, the last session to start wins; fine while every copy renders the same rows.
    try:
        folder = Path.home() / ".cache" / "cv-kit"
        folder.mkdir(parents=True, exist_ok=True)
        part = folder / f"plugin-root.{os.getpid()}"
        part.write_text(str(Path(__file__).resolve().parents[1]), encoding="utf-8")
        os.replace(part, folder / "plugin-root")
    except OSError:
        pass


def main() -> int:
    if "--register" in sys.argv[1:]:
        register()
        return 0
    try:
        payload = json.loads(sys.stdin.read())
        out = render(payload, time.time() * 1000)
        if out:
            print("\n".join(out))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
