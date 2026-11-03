#!/usr/bin/env python3
"""Rewrite each subagent row as `◐ engineer (sonnet ▰▰▱▱▱)  writing the failing test  1.2k  4m12s`.

Icon, agent, a group with the model and the effort meter (low ▰▱▱▱▱ … max ▰▰▰▰▰), label, tokens, elapsed time (running
rows only). Columns line up across rows and the label column stops at 48. A narrow row drops parts in order: the label
shrinks, then the tokens go, then the meter, then the model group, then the label.

The icon changes once per refresh tick (about 5 s). A running agent's spinner ◐◓◑◒ turns a quarter on each tick its
token count grew, and shows ○ once the count has stood still for three ticks. A task seen to finish shows its icon
(✓ completed, ✗ failed, ■ killed) inverted for one tick and bold for the next; then completed and killed rows fade,
failed rows stay bright. To tell ticks apart the script keeps a small memory per session in
`~/.cache/cv-kit/rows/<session_id>.json`; `--register` deletes files older than a day.

Claude Code runs this as `subagentStatusLine` (settings.json): stdin is one JSON object with `columns`, `tasks` and the
base hook fields, stdout is one `{"id", "content"}` line per row to rewrite, ANSI colours allowed (`NO_COLOR` turns them
off). Any error prints nothing, so the default rows stay.

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
ICONS = {"completed": ("✓", "32"), "failed": ("✗", "31"), "killed": ("■", "90")}
SPINNER = "◐◓◑◒"
DIM, BOLD, RUNNING, STALLED = "2", "1", "1;33", "2;33"
STALL_TICKS = 3  # ticks without new tokens before a running row shows ○
SETTLE = 2  # ticks a finished icon stays highlighted: inverted, then bold
FADES = ("completed", "killed")
NAME_MAX, LABEL_MAX = 16, 48
# Widest first, the first that fits wins: (model group, effort meter, tokens, fewest label columns; None = no label).
STEPS = ((True, True, True, 20), (True, True, False, 20), (True, False, False, 16), (False, False, False, 12),
         (False, False, False, 6), (False, False, False, None))
GAP = [("  ", "")]
CONTROL = re.compile(r"[\x00-\x1f\x7f]+")
SESSION = re.compile(r"[A-Za-z0-9_-]{1,128}")
MEMORY_TTL = 86400  # seconds

Cell = list[tuple[str, str]]  # (text, SGR code); "" = plain


def char_width(ch: str) -> int:
    if unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in "WF" else 1


def width(cell: Cell) -> int:
    return sum(char_width(ch) for text, _ in cell for ch in text)


def rstrip(cell: Cell) -> Cell:
    out = list(cell)
    while out and not out[-1][0].strip():
        out.pop()
    if out:
        out[-1] = (out[-1][0].rstrip(), out[-1][1])
    return out


def clip(cell: Cell, limit: int) -> Cell:
    """Cut to `limit` visible columns, the last one an ellipsis."""
    if width(cell) <= limit:
        return cell
    out, used = [], 0
    for text, style in cell:
        kept = ""
        for ch in text:
            if used + char_width(ch) > limit - 1:
                return rstrip(out + [(kept, style)]) + [("…", "")]
            kept += ch
            used += char_width(ch)
        out.append((kept, style))
    return out


def pad(cell: Cell, size: int, right: bool = False) -> Cell:
    space = [(" " * (size - width(cell)), "")]
    return space + cell if right else cell + space


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


def remember(memory: dict, seen: dict, task_id: str, status: str, tokens) -> tuple[int, int]:
    """Spinner frame and ticks since the status changed, from last tick's `memory`; this tick goes into `seen`."""
    tokens = tokens if number(tokens) else 0
    try:
        old_status, old_tokens, frame, since = memory[task_id]
        frame, since, grew = int(frame), max(0, int(since)), tokens > float(old_tokens)
    except (KeyError, TypeError, ValueError):  # first sight: a task that is already finished does not flash
        old_status, frame, since, grew = status, 0, SETTLE, False
    if status != old_status:
        since = 0 if old_status == "running" else SETTLE
    else:
        since, frame = min(since + 1, SETTLE), frame + grew
    seen[task_id] = [status, tokens, frame % len(SPINNER), since]
    return frame, since


def stalled(samples) -> bool:
    if not isinstance(samples, list) or len(samples) <= STALL_TICKS:
        return False
    tail = samples[-STALL_TICKS - 1:]
    return all(value == tail[0] for value in tail)


def icon(status: str, frame: int, since: int, samples) -> tuple[str, str]:
    if status == "running":
        return ("○", STALLED) if stalled(samples) else (SPINNER[frame % len(SPINNER)], RUNNING)
    glyph, color = ICONS.get(status, ("○", DIM))
    return glyph, (f"1;7;{color}", f"1;{color}", color)[min(since, SETTLE)]


def cells(task: dict, now_ms: float, frame: int, since: int) -> dict[str, Cell]:
    status = str(task.get("status") or "")
    name = str(task.get("agentType") or "").removeprefix("cv-kit:") or str(task.get("name") or "") or "agent"
    label = re.sub(r" +", " ", CONTROL.sub(" ", str(task.get("label") or task.get("description") or ""))).strip()
    model = short_model(task.get("model"))
    row = {
        "name": clip([(name, BOLD)], NAME_MAX),
        "model": [(model, "")] if model else [],
        "meter": effort_meter(task.get("effort")),
        "label": [(label, "")] if label else [],
        "tokens": [(compact(task["tokenCount"]), DIM)] if number(task.get("tokenCount")) else [],
        "time": [],
    }
    if status == "running":  # a finished task has no end time, so a clock would keep counting
        try:
            row["time"] = [(elapsed(float(task["startTime"]), now_ms), "")]
        except (KeyError, TypeError, ValueError):
            pass
    if status in FADES and since >= SETTLE:  # finished rows fade so the running ones stand out
        row = {key: [(text, DIM) for text, _ in cell] for key, cell in row.items()}
    row["icon"] = [icon(status, frame, since, task.get("tokenSamples"))]
    return row


def head(row: dict[str, Cell], model: bool, meter: bool) -> Cell:
    group = row["model"] if model else []
    if model and meter and row["meter"]:
        group = group + ([(" ", "")] if group else []) + row["meter"]
    return row["name"] + ([(" (", DIM)] + group + [(")", DIM)] if group else [])


def layout(rows: list[dict[str, Cell]], columns) -> tuple[tuple[bool, bool], dict[str, int]]:
    """The widest step whose row fits `columns`, and each column's width. The last step always fits after a clip."""
    label_max = min(LABEL_MAX, max(width(row["label"]) for row in rows))
    time_w = max(width(row["time"]) for row in rows)
    for model, meter, tokens, label_min in STEPS:
        head_w = max(width(head(row, model, meter)) for row in rows)
        tokens_w = max(width(row["tokens"]) for row in rows) if tokens else 0
        fixed = 2 + head_w + (2 + tokens_w if tokens_w else 0) + (2 + time_w if time_w else 0)
        room = columns - fixed - 2 if columns else label_max
        label_w = 0
        if label_min is not None:
            if room < min(label_min, label_max):
                continue
            label_w = min(label_max, room)
        return (model, meter), {"head": head_w, "label": label_w, "tokens": tokens_w, "time": time_w}


def line(row: dict[str, Cell], step: tuple[bool, bool], widths: dict[str, int]) -> Cell:
    out = row["icon"] + [(" ", "")] + pad(head(row, *step), widths["head"])
    for column in ("label", "tokens", "time"):
        if widths[column]:
            out += GAP + pad(clip(row[column], widths[column]), widths[column], right=column != "label")
    return rstrip(out)


def paint(cell: Cell, color: bool) -> str:
    return "".join(f"\x1b[{style}m{text}\x1b[0m" if color and style and text else text for text, style in cell)


def render(payload: dict, now_ms: float, color: bool = True, memory: dict | None = None) -> list[str]:
    """One JSON line per task. `memory` holds last tick's state and is replaced by this tick's."""
    memory = {} if memory is None else memory
    seen, built = {}, []
    for task in payload.get("tasks", []):
        try:
            task_id, status = task["id"], str(task.get("status") or "")
            frame, since = remember(memory, seen, str(task_id), status, task.get("tokenCount"))
            built.append((task_id, cells(task, now_ms, frame, since)))
        except Exception:  # one bad row keeps its default; the others still render
            continue
    memory.clear()
    memory.update(seen)
    if not built:
        return []
    columns = payload.get("columns")
    columns = columns if isinstance(columns, int) and columns > 0 else 0
    step, widths = layout([row for _, row in built], columns)
    lines = []
    for task_id, row in built:
        cell = line(row, step, widths)
        lines.append(json.dumps({"id": task_id, "content": paint(clip(cell, columns) if columns else cell, color)}))
    return lines


def memory_file(payload: dict) -> Path | None:
    session = payload.get("session_id")
    if isinstance(session, str) and SESSION.fullmatch(session):
        return Path.home() / ".cache" / "cv-kit" / "rows" / f"{session}.json"
    return None


def load_memory(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(f"{path.name}.{os.getpid()}")
    part.write_text(text, encoding="utf-8")
    os.replace(part, path)


def register() -> None:
    folder = Path.home() / ".cache" / "cv-kit"
    # shortcut: one pointer per user, the last session to start wins; fine while every copy renders the same rows.
    try:
        write_atomic(folder / "plugin-root", str(Path(__file__).resolve().parents[1]))
    except OSError:
        pass
    cutoff = time.time() - MEMORY_TTL
    try:
        for path in (folder / "rows").iterdir():
            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink()
            except OSError:
                continue
    except OSError:
        pass


def main() -> int:
    if "--register" in sys.argv[1:]:
        register()
        return 0
    try:
        payload = json.loads(sys.stdin.read())
        path = memory_file(payload)
        memory = load_memory(path) if path else {}
        out = render(payload, time.time() * 1000, color=not os.environ.get("NO_COLOR"), memory=memory)
        if out:
            print("\n".join(out))
        if path:
            try:
                write_atomic(path, json.dumps(memory))
            except OSError:
                pass
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
