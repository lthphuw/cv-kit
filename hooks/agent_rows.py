#!/usr/bin/env python3
"""cv-kit's status line: one row for the main session.

    ● main           opus   ▰▰▰▱▱  ctx ▰▰▰▱▱▱▱▱▱▱ 32% of 200k  $0.42  +156 −23         12m

Claude Code's own agent panel lists each subagent below the status line, so this draws nothing for them.

- `--register` runs at SessionStart (hooks/hooks.json): it writes this plugin's root to
  `~/.cache/cv-kit/agent-rows-root`, refreshes the launcher scripts/install_statusline.py installed, and deletes the
  logs and row memory that older versions left in `~/.cache/cv-kit`, once they are a day old.
- With no flag, it is the status line: stdin is the status line JSON, stdout the row. `--ascii` draws with ASCII only.
  Other flags, such as the old `--no-main`, are ignored.

Standard library only; any error prints nothing and exits 0, so the status line stays as it was.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path.home() / ".cache" / "cv-kit"
LAUNCHER = Path.home() / ".claude" / "cv-kit" / "statusline.py"
LAUNCHER_SOURCE = Path(__file__).with_name("statusline_launcher.py")
MODELS = ("haiku", "sonnet", "opus", "fable")
LEVELS = ("low", "medium", "high", "xhigh", "max")
LEVEL_COLORS = ("32", "36", "33", "38;5;208", "31")  # green, cyan, yellow, orange, red
DIM, BOLD, DONE, FAILED, BLOCKED, MAIN = "2", "1", "32", "31", "33", "1;34"
TASK_MAX, NOW_MAX = 32, 32
LOG_TTL = 86400  # seconds
# Widest first, the first that fits wins: (fewest cost columns or None = no cost column, fewest context columns or
# None = no context column, effort meter, model).
STEPS = ((16, 16, True, True), (10, 12, True, True), (None, 12, True, True), (None, 12, False, True),
         (None, 12, False, False), (None, 6, False, False), (None, None, False, False))
GLYPHS = {
    False: {"on": "▰", "off": "▱", "main": "●", "ell": "…", "minus": "−", "fast": "⚡", "none": "—"},
    True: {"on": "#", "off": "-", "main": "*", "ell": "...", "minus": "-", "fast": "^", "none": "-"},
}

Cell = list[tuple[str, str]]  # (text, SGR code); "" = plain


def number(value, default=0):
    """`value` when it is a finite number (not a bool), else `default`."""
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
        return value
    return default


# --- cells -------------------------------------------------------------------------------------------------------


def char_width(ch: str) -> int:
    if unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in "WF" else 1


def width(cell: Cell) -> int:
    return sum(char_width(ch) for text, _ in cell for ch in text)


def clip(cell: Cell, limit: int, ell: str = "…") -> Cell:
    """Cut to `limit` visible columns, ending in `ell`."""
    if width(cell) <= limit:
        return cell
    room = limit - len(ell)
    if room < 1:
        return [(ell[:max(0, limit)], "")]
    out, used = [], 0
    for text, style in cell:
        kept = ""
        for ch in text:
            if used + char_width(ch) > room:
                out.append((kept, style))
                while out and not out[-1][0].strip():  # no padding left before the ellipsis
                    out.pop()
                if out:
                    out[-1] = (out[-1][0].rstrip(), out[-1][1])
                return out + [(ell, "")]
            kept += ch
            used += char_width(ch)
        out.append((kept, style))
    return out


def pad(cell: Cell, size: int, right: bool = False) -> Cell:
    space = [(" " * max(0, size - width(cell)), "")]
    return space + cell if right else cell + space


def short_clock(ms: float) -> str:
    """A session's length: `45s`, `12m`, `1h05m`."""
    minutes = max(0, int(ms // 60_000))
    if minutes >= 60:
        return f"{minutes // 60}h{minutes % 60:02d}m"
    return f"{minutes}m" if minutes else f"{max(0, int(ms // 1000))}s"


def compact(count: float) -> str:
    for size, unit in ((1e6, "M"), (1e3, "k")):
        if count >= size:
            value = count / size
            return (f"{value:.1f}".rstrip("0").rstrip(".") if value < 10 else f"{value:.0f}") + unit
    return str(int(count))


def short_model(model: str) -> str:
    return next((m for m in MODELS if m in model.lower()), model)


def bar(filled: int, cells: int, style: str, g: dict) -> Cell:
    return [(g["on"] * filled, style), (g["off"] * (cells - filled), DIM)]


def effort_meter(effort: str, g: dict) -> Cell:
    level = effort.strip().lower()
    if not level:
        return []
    if level not in LEVELS:
        return [(level[:6], "")]
    filled = LEVELS.index(level) + 1
    return bar(filled, len(LEVELS), LEVEL_COLORS[filled - 1], g)


def main_row(payload: dict, g: dict) -> dict | None:
    """The main session's cells, or None when the payload says nothing about it."""
    model_info = payload.get("model") if isinstance(payload.get("model"), dict) else {}
    window = payload.get("context_window") if isinstance(payload.get("context_window"), dict) else {}
    cost = payload.get("cost") if isinstance(payload.get("cost"), dict) else {}
    effort = payload.get("effort") if isinstance(payload.get("effort"), dict) else {}
    if not (model_info or window or cost):
        return None
    ident = short_model(str(model_info.get("id") or ""))
    model = ident if ident in MODELS else short_model(str(model_info.get("display_name") or "")).lower()
    model_cell = [(model, DIM)] if model else []
    if model and payload.get("fast_mode") is True:
        model_cell.append((g["fast"], BLOCKED))
    task: list[Cell] = []
    pct = number(window.get("used_percentage"), None)
    if window and pct is not None:
        pct = max(0, min(100, round(pct)))
        style = DONE if pct < 50 else BLOCKED if pct < 80 else FAILED
        size = number(window.get("context_window_size"))
        label, tail = [("ctx ", DIM)], [(f" {pct}%", "")]
        of = [(f" of {compact(size)}", DIM)] if size > 0 else []
        ten, five = bar(round(pct / 10), 10, style, g), bar(round(pct / 20), 5, style, g)
        task = [label + ten + tail + of, label + ten + tail, label + five + tail, label + [(f"{pct}%", "")],
                [(f"{pct}%", "")]]
    elif window:
        task = [[("ctx ", DIM), (g["none"], DIM)]]
    now: list[Cell] = []
    usd = number(cost.get("total_cost_usd"), None)
    if usd is not None:
        money = [(f"${usd:.0f}" if usd >= 100 else f"${usd:.2f}", "")]
        added, removed = int(number(cost.get("total_lines_added"))), int(number(cost.get("total_lines_removed")))
        lines = [(f"  +{added} {g['minus']}{removed}", DIM)] if added or removed else []
        now = [money + lines, money] if lines else [money]
    duration = number(cost.get("total_duration_ms"), None)
    has_time = duration is not None
    return {"icon": (g["main"], MAIN), "name": [("main", BOLD)], "model": model_cell,
            "meter": effort_meter(str(effort.get("level") or ""), g), "task": task, "now": now,
            "time": [(short_clock(duration), "")] if has_time else []}


# --- layout ------------------------------------------------------------------------------------------------------


def best(variants: list[Cell], size: int, ell: str) -> Cell:
    """The widest variant that fits `size`, else the narrowest one cut to it."""
    for cell in variants:
        if width(cell) <= size:
            return cell
    return clip(variants[-1], size, ell) if variants else []


def want(row: dict, key: str) -> int:
    return width(row[key][0]) if row[key] else 0


def layout(row: dict, columns: int) -> dict:
    """The widest step whose row fits `columns` (0 = no limit), as column widths; 0 means the column is left out."""
    name_w, time_w = width(row["name"]), width(row["time"])
    task_want, now_want = min(TASK_MAX, want(row, "task")), min(NOW_MAX, want(row, "now"))
    for now_min, task_min, meter_on, model_on in STEPS:
        widths = {"name": name_w, "time": time_w, "model": width(row["model"]) if model_on else 0,
                  "meter": width(row["meter"]) if meter_on else 0}
        fixed = 2 + name_w + sum(1 + widths[k] for k in ("model", "meter") if widths[k])
        fixed += 2 + time_w if time_w else 0
        room = (columns - fixed - 2) if columns else 10 ** 6
        task_w = now_w = 0
        if task_min is None:
            pass
        elif now_min is not None and now_want:
            task_w, now_w = task_want, now_want
            if task_w + 2 + now_w > room:
                now_w = max(min(now_min, now_want), room - 2 - task_w)
            if task_w + 2 + now_w > room:
                task_w = max(min(task_min, task_w), room - 2 - now_w)
            if task_w + 2 + now_w > room:
                continue
        else:
            task_w = min(task_want, room)
            if task_w < min(task_min, task_want):
                continue
        return {**widths, "task": task_w, "now": now_w}
    raise AssertionError("the last step always fits")


def line(row: dict, widths: dict, g: dict) -> Cell:
    icon, style = row["icon"]
    out: Cell = [(icon, style), (" ", "")] + pad(row["name"], widths["name"])
    for key in ("model", "meter"):
        if widths[key]:
            out += [(" ", "")] + pad(clip(row[key], widths[key], g["ell"]), widths[key])
    for key in ("task", "now"):
        if widths[key]:
            out += [("  ", "")] + pad(best(row[key], widths[key], g["ell"]), widths[key])
    if widths["time"]:
        out += [("  ", "")] + pad(row["time"], widths["time"], right=True)
    while out and not out[-1][0].strip():
        out.pop()
    if out:
        out[-1] = (out[-1][0].rstrip(), out[-1][1])
    return out


def paint(cell: Cell, color: bool) -> str:
    return "".join(f"\x1b[{style}m{text}\x1b[0m" if color and style and text else text for text, style in cell)


def render(main: dict | None, columns: int = 0, color: bool = True, ascii: bool = False) -> list[str]:
    """The main row as one string, cut to `columns` (0 = no limit); none when the payload says nothing about it."""
    g = GLYPHS[ascii]
    row = main_row(main, g) if isinstance(main, dict) else None
    if not row:
        return []
    cell = line(row, layout(row, columns), g)
    return [paint(clip(cell, columns, g["ell"]) if columns else cell, color)]


# --- the command line --------------------------------------------------------------------------------------------


def write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(f"{path.name}.{os.getpid()}")
    part.write_bytes(data)
    os.replace(part, path)


def register() -> None:
    # shortcut: one pointer per user, the last session to start wins; fine while every copy draws the same row.
    try:
        write_atomic(CACHE / "agent-rows-root", str(ROOT).encode("utf-8"))
    except OSError:
        pass
    try:  # keep an installed launcher in step with this version; never install one unasked
        if LAUNCHER.is_file() and LAUNCHER.read_bytes() != LAUNCHER_SOURCE.read_bytes():
            write_atomic(LAUNCHER, LAUNCHER_SOURCE.read_bytes())
    except OSError:
        pass
    cutoff = time.time() - LOG_TTL
    # agents/ holds the agent logs of cv-kit 0.11 and older; rows/ is the row memory of 0.9.1 and older
    for folder in (CACHE / "agents", CACHE / "rows"):
        try:
            for path in folder.iterdir():
                try:
                    if path.stat().st_mtime < cutoff:
                        path.unlink()
                except OSError:
                    continue
        except OSError:
            pass


def status_line(raw: str, ascii: bool = False) -> list[str]:
    try:
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return []
        columns = os.environ.get("COLUMNS", "")
        return render(payload, columns=int(columns) if columns.isdigit() else 0,
                      color=not os.environ.get("NO_COLOR"), ascii=ascii or bool(os.environ.get("CV_KIT_ASCII")))
    except Exception:
        return []


def write_lines(lines: list[str]) -> None:
    """Print as UTF-8 whatever the console's encoding (a Windows console defaults to a code page)."""
    if lines:
        sys.stdout.buffer.write(("\n".join(lines) + "\n").encode("utf-8"))
        sys.stdout.flush()


def main(argv: list[str]) -> int:
    try:
        raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
        if "--register" in argv:
            register()
        else:
            write_lines(status_line(raw, ascii="--ascii" in argv))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
