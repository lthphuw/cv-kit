#!/usr/bin/env python3
"""Rewrite each subagent row as aligned columns: `● engineer  sonnet  ▰▰▱▱▱  4m12s  1.2k  <label>`.

Icon = status (● running, ✓ completed, ✗ failed, ■ killed), then agent, model, effort meter (low ▰▱▱▱▱ … max ▰▰▰▰▰),
elapsed time (running rows only), tokens, label. Columns line up across rows; a column nobody has is dropped.

Claude Code runs this as `subagentStatusLine` (settings.json): stdin is one JSON object with `columns` and `tasks`,
stdout is one `{"id", "content"}` line per row to rewrite, ANSI colours allowed (`NO_COLOR` turns them off). Any error
prints nothing, so the default rows stay.

Claude Code leaves `${CLAUDE_PLUGIN_ROOT}` empty in a plugin's `subagentStatusLine` (seen on 2.1.317), so at
SessionStart `--register` writes this plugin's root to `~/.cache/cv-kit/plugin-root` and the command reads it.
"""
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

MODELS = ("haiku", "sonnet", "opus", "fable")
LEVELS = ("low", "medium", "high", "xhigh", "max")
LEVEL_COLORS = ("32", "36", "33", "38;5;208", "31")  # green, cyan, yellow, orange, red
ICONS = {"running": ("●", "33"), "completed": ("✓", "32"), "failed": ("✗", "31"), "killed": ("■", "90")}
DIM, BOLD = "2", "1"
NAME_MAX = 16
COLUMNS = ("icon", "name", "model", "effort", "elapsed", "tokens", "label")
RIGHT = ("elapsed", "tokens")
CONTROL = re.compile(r"[\x00-\x1f\x7f]+")

Cell = list[tuple[str, str]]  # (text, SGR code); "" = plain


def char_width(ch: str) -> int:
    if unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in "WF" else 1


def width(cell: Cell) -> int:
    return sum(char_width(ch) for text, _ in cell for ch in text)


def clip(cell: Cell, limit: int) -> Cell:
    """Cut to `limit` visible columns, the last one an ellipsis."""
    if width(cell) <= limit:
        return cell
    out, used = [], 0
    for text, style in cell:
        kept = ""
        for ch in text:
            if used + char_width(ch) > limit - 1:
                return out + [(kept, style), ("…", "")]
            kept += ch
            used += char_width(ch)
        out.append((kept, style))
    return out


def compact(count: float) -> str:
    for size, unit in ((1e6, "M"), (1e3, "k")):
        if count >= size:
            value = count / size
            return (f"{value:.1f}".rstrip("0").rstrip(".") if value < 10 else f"{value:.0f}") + unit
    return str(int(count))


def number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


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


def effort_meter(effort) -> Cell:
    if number(effort):
        return [(f"≤{compact(effort)}", "")]  # a thinking-token budget instead of a level
    if not isinstance(effort, str) or not effort.strip():
        return []
    level = effort.strip().lower()
    if level not in LEVELS:
        return [(level[:6], "")]
    filled = LEVELS.index(level) + 1
    return [("▰" * filled, LEVEL_COLORS[filled - 1]), ("▱" * (len(LEVELS) - filled), DIM)]


def cells(task: dict, now_ms: float) -> dict[str, Cell]:
    status = str(task.get("status") or "")
    name = str(task.get("agentType") or "").removeprefix("cv-kit:") or str(task.get("name") or "") or "agent"
    label = re.sub(r" +", " ", CONTROL.sub(" ", str(task.get("label") or task.get("description") or ""))).strip()
    row = {
        "name": clip([(name, BOLD)], NAME_MAX),
        "model": [(short_model(task.get("model")), "")],
        "effort": effort_meter(task.get("effort")),
        "elapsed": [],
        "tokens": [(compact(task["tokenCount"]), DIM)] if number(task.get("tokenCount")) else [],
        "label": [(label, "")],
    }
    if status == "running":  # a finished task has no end time, so a clock would keep counting
        try:
            row["elapsed"] = [(elapsed(float(task["startTime"]), now_ms), DIM)]
        except (KeyError, TypeError, ValueError):
            pass
    else:  # finished rows fade so the running ones stand out
        row = {key: [(text, DIM) for text, _ in cell] for key, cell in row.items()}
    row["icon"] = [ICONS.get(status, ("○", DIM))]
    return row


def line(row: dict[str, Cell], widths: dict[str, int]) -> Cell:
    out: Cell = []
    for column in COLUMNS:
        if not widths[column]:
            continue
        pad = [(" " * (widths[column] - width(row[column])), "")]
        cell = row[column] if column == "label" else pad + row[column] if column in RIGHT else row[column] + pad
        out += ([(" " if column == "name" else "  ", "")] if out else []) + cell
    while out and not out[-1][0].strip():
        out.pop()
    return out


def paint(cell: Cell, color: bool) -> str:
    return "".join(f"\x1b[{style}m{text}\x1b[0m" if color and style and text else text for text, style in cell)


def render(payload: dict, now_ms: float, color: bool = True) -> list[str]:
    built = []
    for task in payload.get("tasks", []):
        try:
            built.append((task["id"], cells(task, now_ms)))
        except Exception:  # one bad row keeps its default; the others still render
            continue
    widths = {column: max((width(row[column]) for _, row in built), default=0) for column in COLUMNS}
    columns = payload.get("columns")
    lines = []
    for task_id, row in built:
        cell = line(row, widths)
        if isinstance(columns, int) and columns > 0:
            cell = clip(cell, columns)
        lines.append(json.dumps({"id": task_id, "content": paint(cell, color)}))
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
        out = render(payload, time.time() * 1000, color=not os.environ.get("NO_COLOR"))
        if out:
            print("\n".join(out))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
