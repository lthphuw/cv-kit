#!/usr/bin/env python3
"""cv-kit's status line: a row for the main session, then one row per subagent, all on one grid.

    ● main           opus   ▰▰▰▱▱  ctx ▰▰▰▱▱▱▱▱▱▱ 32% of 200k  $0.42  +156 −23         12m
    ◐ engineer       sonnet ▰▰▰▱▱  tracker core: failing test  Bash pytest -q   1m40s  4m12s
    ✓ explorer       haiku  ▰▱▱▱▱  frames reach the writer at pipeline.py:57            17s

Claude Code sends a status line command no subagent data, so the plugin's hooks collect it (hooks/hooks.json):

- `--event` runs on PreToolUse, PostToolUse and PostToolUseFailure of the Agent tool, SubagentStart and SubagentStop.
  It appends one JSON line per event to `~/.cache/cv-kit/agents/<session_id>.jsonl`. The Agent call gives the type,
  description, model and effort; the start and stop give the clock, and the stop gives the `STATUS:` line that
  hooks/concise.md asks every subagent to start its report with. A call pairs with the next start of its type under
  the same prompt, and the `agentId` in PostToolUse corrects the pair when two calls of one type ran together.
- `--activity` runs, async, on every tool call. Only calls made inside a subagent (they carry `agent_id`) are logged:
  the tool and its main argument, then its end. A `SubagentHandback` report counts as the STATUS line.
- `--register` runs at SessionStart: it writes this plugin's root to `~/.cache/cv-kit/agent-rows-root`, refreshes the
  launcher scripts/install_statusline.py installed, deletes logs older than a day, and on a resume logs a reset:
  agents still marked running died with the old process and show `■`.
- With no flag, it is the status line: stdin is the status line JSON, stdout the rows. `--ascii` draws with ASCII only,
  `--no-main` leaves out the main row.

Appends are whole lines: one write on an O_APPEND file on macOS and Linux, under a lock file on Windows. Standard
library only; any error prints nothing and exits 0, so a hook never blocks and the status line stays as it was.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
import time
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path.home() / ".cache" / "cv-kit"
LAUNCHER = Path.home() / ".claude" / "cv-kit" / "statusline.py"
LAUNCHER_SOURCE = Path(__file__).with_name("statusline_launcher.py")
MODELS = ("haiku", "sonnet", "opus", "fable")
LEVELS = ("low", "medium", "high", "xhigh", "max")
LEVEL_COLORS = ("32", "36", "33", "38;5;208", "31")  # green, cyan, yellow, orange, red
DIM, BOLD, RUNNING, DONE, FAILED, BLOCKED, MAIN, ACTIVE = "2", "1", "1;33", "32", "31", "33", "1;34", "36"
MAX_ROWS = 6
RECENT_MS = 60_000  # without a prompt id, a finished row shows this long
TOOL_CLOCK_MS = 10_000  # a tool shows its own clock once it has run this long
NAME_MAX, TASK_MAX, NOW_MAX = 16, 32, 32
DESC_MAX, ARG_MAX, SUMMARY_MAX = 200, 120, 160
LOG_TTL = 86400  # seconds
TOOL_LINES = 4000  # a long session's log: only the latest tool lines are parsed, every second
# Widest first, the first that fits wins: (tool clock, fewest activity columns or None = no activity column,
# fewest task columns or None = no task column, effort meter, model).
STEPS = ((True, 16, 16, True, True), (False, 16, 16, True, True), (False, 10, 12, True, True),
         (False, None, 12, True, True), (False, None, 12, False, True), (False, None, 12, False, False),
         (False, None, 6, False, False), (False, None, None, False, False))
CONTROL = re.compile(r"[\x00-\x1f\x7f]+")
SESSION = re.compile(r"[A-Za-z0-9_-]{1,128}")
AGENT_NAME = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
FRONT_MODEL = re.compile(r"^model:\s*(\S+)\s*$", re.M)
STATUS = re.compile(r"^\W*status\W*:\W*(done|blocked|failed)\b[ \t:*\-–—]*(.*)$", re.I | re.M)
GLYPHS = {
    False: {"spin": "◐◓◑◒", "on": "▰", "off": "▱", "done": "✓", "failed": "✗", "blocked": "!", "lost": "■",
            "main": "●", "ell": "…", "minus": "−", "fast": "⚡", "think": "thinking…", "none": "—"},
    True: {"spin": "|/-\\", "on": "#", "off": "-", "done": "+", "failed": "x", "blocked": "!", "lost": "#",
           "main": "*", "ell": "...", "minus": "-", "fast": "^", "think": "thinking...", "none": "-"},
}

Cell = list[tuple[str, str]]  # (text, SGR code); "" = plain


# --- the log -----------------------------------------------------------------------------------------------------


def log_path(folder: Path, session) -> Path | None:
    return folder / f"{session}.jsonl" if isinstance(session, str) and SESSION.fullmatch(session) else None


def short_id(value) -> str:
    return str(value or "").removeprefix("agent-")


def flat(text) -> str:
    return re.sub(r"\s+", " ", CONTROL.sub(" ", str(text or ""))).strip()


def outcome(text) -> tuple[str, str] | None:
    """`(done|blocked|failed, summary)` from the first STATUS line of a report, or None."""
    if not isinstance(text, str):
        return None
    match = STATUS.search(text[:4000])
    return (match.group(1).lower(), flat(match.group(2))[:SUMMARY_MAX]) if match else None


def tool_label(name: str) -> str:
    parts = name.split("__")
    return parts[-1] if name.startswith("mcp__") and len(parts) > 2 else name


def tool_arg(name: str, tool_input) -> str:
    """The part of a tool call worth seeing: a command, a file name, a pattern, a host."""
    args = tool_input if isinstance(tool_input, dict) else {}
    if name in ("Bash", "PowerShell"):
        value = str(args.get("command") or "").strip().split("\n")[0]
    elif name in ("Read", "Edit", "Write", "MultiEdit", "NotebookEdit"):
        value = re.split(r"[\\/]", str(args.get("file_path") or args.get("notebook_path") or ""))[-1]
    elif name in ("Grep", "Glob"):
        value = args.get("pattern")
    elif name == "WebFetch":
        try:
            value = urlsplit(str(args.get("url") or "")).hostname
        except ValueError:
            value = ""
    elif name == "WebSearch":
        value = args.get("query")
    elif name == "Agent":
        value = args.get("subagent_type") or args.get("description")
    elif name == "Skill":
        value = args.get("skill")
    else:
        value = ""
    return flat(value)[:ARG_MAX]


def event_lines(payload: dict, now_ms: float, activity: bool = False) -> list[dict]:
    """The log lines for one hook payload; none when the event is not about a subagent."""
    name, prompt = payload.get("hook_event_name"), payload.get("prompt_id")
    agent = short_id(payload.get("agent_id"))
    if activity:  # tool calls made inside a subagent
        tool, tu = str(payload.get("tool_name") or ""), payload.get("tool_use_id")
        if not agent or not tool:
            return []
        if name == "PreToolUse" and tool == "SubagentHandback":
            got = outcome((payload.get("tool_input") or {}).get("message"))
            return [{"e": "outcome", "t": now_ms, "id": agent, "st": got[0], "sum": got[1]}] if got else []
        if name == "PreToolUse":
            return [{"e": "tool", "t": now_ms, "id": agent, "tu": tu, "tool": tool_label(tool),
                     "arg": tool_arg(tool, payload.get("tool_input"))}]
        if name in ("PostToolUse", "PostToolUseFailure"):
            return [{"e": "tooldone", "t": now_ms, "id": agent, "tu": tu}]
        return []
    if name in ("PreToolUse", "PostToolUse", "PostToolUseFailure") and payload.get("tool_name") == "Agent":
        tool_input, tu = payload.get("tool_input") or {}, payload.get("tool_use_id")
        if name == "PreToolUse":
            return [{"e": "call", "t": now_ms, "tu": tu, "p": prompt,
                     "type": str(tool_input.get("subagent_type") or "general-purpose"),
                     "desc": flat(tool_input.get("description"))[:DESC_MAX],
                     "model": str(tool_input.get("model") or ""), "effort": str(tool_input.get("effort") or "")}]
        if name == "PostToolUseFailure":
            return [{"e": "fail", "t": now_ms, "tu": tu}]
        response = payload.get("tool_response")
        agent_id = response.get("agentId") if isinstance(response, dict) else None
        if not agent_id:
            return []
        return [{"e": "link", "t": now_ms, "tu": tu, "id": short_id(agent_id),
                 "bg": response.get("status") == "async_launched"}]  # PostToolUse at launch: a background agent
    if name in ("SubagentStart", "SubagentStop") and payload.get("agent_type") and agent:
        if name == "SubagentStart":
            return [{"e": "start", "t": now_ms, "id": agent, "type": str(payload["agent_type"]), "p": prompt}]
        line = {"e": "stop", "t": now_ms, "id": agent, "type": str(payload["agent_type"])}
        got = outcome(payload.get("last_assistant_message"))
        return [{**line, "st": got[0], "sum": got[1]} if got else line]
    if name == "SessionStart" and payload.get("source") == "resume":  # a new process: no agent kept running
        return [{"e": "reset", "t": now_ms}]
    return []


def append(path: Path, text: str) -> None:
    """Append one line so that writers in other processes never split it."""
    data = text.encode("utf-8")
    if os.name == "nt":  # Windows emulates O_APPEND with a seek and a write, so take a lock
        import msvcrt

        with open(path.with_suffix(".lock"), "a+b") as lock:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
            try:
                with open(path, "ab") as out:
                    out.write(data)
            finally:
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
        return
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)


def log_event(payload: dict, now_ms: float, folder: Path, activity: bool = False) -> None:
    path = log_path(folder, payload.get("session_id"))
    lines = event_lines(payload, now_ms, activity) if path else []
    if not lines:
        return
    folder.mkdir(parents=True, exist_ok=True)
    for line in lines:
        append(path, json.dumps(line, ensure_ascii=False) + "\n")


def read_events(path: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    lines = text.splitlines()
    tools = [i for i, raw in enumerate(lines) if raw.startswith('{"e": "tool')]
    old = set(tools[:-TOOL_LINES]) if len(tools) > TOOL_LINES else set()  # only the latest tool matters
    events = []
    for i, raw in enumerate(lines):
        if i in old:
            continue
        try:
            event = json.loads(raw)
        except ValueError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def number(value, default=0):
    """`value` when it is a finite number (not a bool), else `default`."""
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
        return value
    return default


def fold(events: list[dict]) -> list[dict]:
    """One dict per agent, in the order they first started."""
    agents: dict[str, dict] = {}
    first: dict[str, tuple[float, object]] = {}  # agent id -> time and prompt of its first start
    calls: list[dict] = []
    links: dict[str, str] = {}  # tool_use_id -> agent id
    background: set[str] = set()
    failures: dict[str, float] = {}  # tool_use_id -> time
    tools: dict[str, list[dict]] = {}  # agent id -> tool starts
    ended: set[tuple[str, object]] = set()  # (agent id, tool_use_id) of finished tools
    outcomes: dict[str, tuple[float, str, str]] = {}  # agent id -> time, status, summary
    for event in events:
        kind, agent_id, at = event.get("e"), event.get("id"), event.get("t")
        if kind == "call":
            calls.append(event)
        elif kind == "link" and event.get("tu") and agent_id:
            links[event["tu"]] = agent_id
            if event.get("bg"):
                background.add(agent_id)
        elif kind == "fail" and event.get("tu"):
            failures[event["tu"]] = number(at)
        elif kind == "start" and agent_id:
            first.setdefault(agent_id, (number(at), event.get("p")))
            agent = agents.setdefault(agent_id, {"id": agent_id, "type": event.get("type", ""), "label": "",
                                                 "model": "", "effort": "", "prompt": None, "start": at,
                                                 "end": None, "failed": False, "lost": False, "background": False,
                                                 "activity": None, "outcome": None, "summary": ""})
            # a resumed agent runs again, under the prompt that resumed it
            agent.update(start=at, end=None, lost=False, prompt=event.get("p") or agent["prompt"])
        elif kind == "stop" and agent_id in agents:
            agents[agent_id]["end"] = at
            if event.get("st"):
                outcomes[agent_id] = (number(at), event["st"], event.get("sum", ""))
        elif kind == "outcome" and agent_id and event.get("st"):
            outcomes[agent_id] = (number(at), event["st"], event.get("sum", ""))
        elif kind == "tool" and agent_id:
            tools.setdefault(agent_id, []).append(event)
        elif kind == "tooldone" and agent_id:
            ended.add((agent_id, event.get("tu")))
        elif kind == "reset":
            for agent in agents.values():
                if agent["end"] is None:
                    agent["end"], agent["lost"] = at, True
    paired: dict[str, dict] = {}
    for call in calls:  # the agentId from PostToolUse is certain
        agent_id = links.get(call.get("tu"))
        if agent_id in agents and agent_id not in paired:
            paired[agent_id], call["used"] = call, True
    for agent_id, agent in agents.items():  # the rest pair in order: same type, same prompt, started after the call
        if agent_id in paired:
            continue
        started, prompt = first[agent_id]
        for call in calls:
            failed_before = failures.get(call.get("tu"), float("inf")) < started  # it never started an agent
            same_prompt = not (prompt and call.get("p")) or call.get("p") == prompt
            if (not call.get("used") and call.get("type") == agent["type"] and same_prompt and not failed_before
                    and number(call.get("t")) <= started):
                paired[agent_id], call["used"] = call, True
                break
    for agent_id, agent in agents.items():
        call = paired.get(agent_id, {})
        agent.update(label=call.get("desc", ""), model=call.get("model", ""), effort=call.get("effort", ""),
                     background=agent_id in background, prompt=agent["prompt"] or call.get("p"))
        if agent["end"] is None and call.get("tu") in failures:
            agent["end"], agent["failed"] = failures[call["tu"]], True
        run_start = number(agent["start"])  # only this run's tools and report count
        mine = [t for t in tools.get(agent_id, []) if number(t.get("t")) >= run_start]
        if mine:
            latest = max(mine, key=lambda t: number(t.get("t")))
            agent["activity"] = {"tool": latest.get("tool", ""), "arg": latest.get("arg", ""), "t": latest.get("t"),
                                 "done": (agent_id, latest.get("tu")) in ended}
        got = outcomes.get(agent_id)
        if got and got[0] >= run_start:
            agent["outcome"], agent["summary"] = got[1], got[2]
    return list(agents.values())


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


def fade(cell: Cell) -> Cell:
    return [(text, DIM) for text, _ in cell]


def clock(ms: float) -> str:
    seconds = max(0, int(ms // 1000))
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}h{minutes:02d}m"
    return f"{minutes}m{secs:02d}s" if minutes else f"{secs}s"


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


def frontmatter_model(agent_type: str) -> str:
    """The `model:` of a cv-kit agent, used when the Agent call named none."""
    name = agent_type.removeprefix("cv-kit:")
    if name == agent_type or not AGENT_NAME.fullmatch(name):
        return ""
    try:
        match = FRONT_MODEL.search((ROOT / "agents" / f"{name}.md").read_text(encoding="utf-8"))
    except OSError:
        return ""
    return match.group(1) if match else ""


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


def activity_text(activity: dict | None) -> str:
    if not activity:
        return ""
    return flat(f"{activity.get('tool', '')} {activity.get('arg', '')}")


def agent_row(agent: dict, now_ms: float, g: dict) -> dict:
    """The cells of one agent. A cell is a list of variants, widest first."""
    agent_type = str(agent.get("type") or "agent")
    label = flat(agent.get("label"))
    model = short_model(str(agent.get("model") or "") or frontmatter_model(agent_type))
    start, end = float(agent["start"]), agent.get("end")
    row = {"name": clip([(agent_type.removeprefix("cv-kit:"), BOLD)], NAME_MAX, g["ell"]),
           "model": [(model, DIM)] if model else [], "meter": effort_meter(str(agent.get("effort") or ""), g),
           "time": [(clock((now_ms if end is None else float(end)) - start), "" if end is None else DIM)],
           "task": [], "now": [], "clock": [], "merged": None}
    if end is None:
        row["icon"] = (g["spin"][int(now_ms // 1000) % len(g["spin"])], RUNNING)
        row["task"] = [[(label, "")]] if label else []
        activity = agent.get("activity")
        if activity and not activity.get("done"):
            row["now"] = [[(activity_text(activity), ACTIVE)]]
            ran = now_ms - number(activity.get("t"), now_ms)
            row["clock"] = [(clock(ran), DIM)] if ran >= TOOL_CLOCK_MS else []
        else:
            row["now"] = [[(g["think"], DIM)]]
        return row
    state, summary = agent.get("outcome"), flat(agent.get("summary"))
    if agent.get("failed") or state == "failed":
        row["icon"], style = (g["failed"], FAILED), FAILED
        text = f"failed: {summary}" if state == "failed" and summary else label
    elif state == "blocked":
        row["icon"], style = (g["blocked"], BLOCKED), BLOCKED
        text = f"blocked: {summary}" if summary else label
    elif agent.get("lost"):
        row["icon"], style, text = (g["lost"], DIM), DIM, label
    else:
        row["icon"], style, text = (g["done"], DONE), DIM, summary or label
    row["merged"] = [[(text, style)]] if text else [[]]
    if style == DIM:
        row["name"] = fade(row["name"])
    return row


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
            "meter": effort_meter(str(effort.get("level") or ""), g), "task": task, "now": now, "clock": [],
            "time": [(short_clock(duration), "")] if has_time else [], "merged": None}


# --- layout ------------------------------------------------------------------------------------------------------


def best(variants: list[Cell], size: int, ell: str) -> Cell:
    """The widest variant that fits `size`, else the narrowest one cut to it."""
    for cell in variants:
        if width(cell) <= size:
            return cell
    return clip(variants[-1], size, ell) if variants else []


def want(rows: list[dict], key: str) -> int:
    return max((width(row[key][0]) for row in rows if row[key]), default=0)


def layout(rows: list[dict], columns: int) -> dict:
    """The widest step whose rows fit `columns` (0 = no limit), as column widths; 0 means the column is left out."""
    name_w = max(width(row["name"]) for row in rows)
    time_w = max(width(row["time"]) for row in rows)
    task_want, now_want = min(TASK_MAX, want(rows, "task")), min(NOW_MAX, want(rows, "now"))
    merged_want = min(TASK_MAX + 2 + NOW_MAX, want(rows, "merged"))
    for clock_on, now_min, task_min, meter_on, model_on in STEPS:
        widths = {"name": name_w, "time": time_w,
                  "model": max(width(row["model"]) for row in rows) if model_on else 0,
                  "meter": max(width(row["meter"]) for row in rows) if meter_on else 0,
                  "clock": max(width(row["clock"]) for row in rows) if clock_on else 0}
        fixed = 2 + name_w + sum(1 + widths[k] for k in ("model", "meter") if widths[k])
        fixed += sum(2 + widths[k] for k in ("clock", "time") if widths[k])
        room = (columns - fixed - 2) if columns else 10 ** 6
        task_w = now_w = 0
        if task_min is None:
            pass
        elif now_min is not None and now_want:
            task_w, now_w = max(task_want, merged_want - 2 - now_want, 0), now_want
            if task_w + 2 + now_w > room:
                now_w = max(min(now_min, now_want), room - 2 - task_w)
            if task_w + 2 + now_w > room:
                task_w = max(min(task_min, task_w), room - 2 - now_w)
            if task_w + 2 + now_w > room:
                continue
        else:
            task_w = min(max(task_want, merged_want), room)
            if task_w < min(task_min, max(task_want, merged_want)):
                continue
        return {**widths, "task": task_w, "now": now_w}
    raise AssertionError("the last step always fits")


def line(row: dict, widths: dict, g: dict) -> Cell:
    icon, style = row["icon"]
    out: Cell = [(icon, style), (" ", "")] + pad(row["name"], widths["name"])
    for key in ("model", "meter"):
        if widths[key]:
            out += [(" ", "")] + pad(clip(row[key], widths[key], g["ell"]), widths[key])
    shown = [key for key in ("task", "now") if widths[key]]
    if shown and row["merged"] is not None:  # a finished row's outcome spans both columns
        span = sum(widths[key] for key in shown) + 2 * (len(shown) - 1)
        out += [("  ", "")] + pad(best(row["merged"], span, g["ell"]), span)
    elif shown:
        for key in shown:
            out += [("  ", "")] + pad(best(row[key], widths[key], g["ell"]), widths[key])
    for key in ("clock", "time"):
        if widths[key]:
            out += [("  ", "")] + pad(row[key], widths[key], right=True)
    while out and not out[-1][0].strip():
        out.pop()
    if out:
        out[-1] = (out[-1][0].rstrip(), out[-1][1])
    return out


def paint(cell: Cell, color: bool) -> str:
    return "".join(f"\x1b[{style}m{text}\x1b[0m" if color and style and text else text for text, style in cell)


def visible(agents: list[dict], prompt, now_ms: float) -> list[dict]:
    # A foreground agent cannot outlive its prompt: one from an earlier prompt was interrupted, and Esc runs no hook.
    running = [a for a in agents if a.get("end") is None
               and (a.get("background") or not prompt or a.get("prompt") in (None, prompt))]
    if prompt:
        done = [a for a in agents if a.get("end") is not None and a.get("prompt") == prompt]
    else:
        done = [a for a in agents if a.get("end") is not None and now_ms - number(a["end"]) <= RECENT_MS]
    return running + done


def render(agents: list[dict], prompt, now_ms: float, columns: int = 0, color: bool = True, main: dict | None = None,
           ascii: bool = False) -> list[str]:
    """One string per row, cut to `columns` (0 = no limit)."""
    g = GLYPHS[ascii]
    built = []
    for agent in visible(agents, prompt, now_ms):
        try:
            built.append(agent_row(agent, now_ms, g))
        except (KeyError, TypeError, ValueError):  # one bad agent loses its row; the others still draw
            continue
    extra = max(0, len(built) - MAX_ROWS)
    built = built[:MAX_ROWS]
    head = main_row(main, g) if isinstance(main, dict) else None
    if head:
        built.insert(0, head)
    if not built:
        return []
    widths = layout(built, columns)
    lines = [paint(clip(line(row, widths, g), columns, g["ell"]) if columns else line(row, widths, g), color)
             for row in built]
    if extra:
        lines.append(paint([(f"+{extra} more", DIM)], color))
    return lines


# --- the command line --------------------------------------------------------------------------------------------


def write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(f"{path.name}.{os.getpid()}")
    part.write_bytes(data)
    os.replace(part, path)


def register() -> None:
    # shortcut: one pointer per user, the last session to start wins; fine while every copy draws the same rows.
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
    for folder in (CACHE / "agents", CACHE / "rows"):  # rows/ is the row memory of cv-kit 0.9.1 and older
        try:
            for path in folder.iterdir():
                try:
                    if path.stat().st_mtime < cutoff:
                        path.unlink()
                except OSError:
                    continue
        except OSError:
            pass


def status_line(raw: str, ascii: bool = False, main: bool = True) -> list[str]:
    try:
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return []
        path = log_path(CACHE / "agents", payload.get("session_id"))
        agents = fold(read_events(path)) if path else []
        columns = os.environ.get("COLUMNS", "")
        return render(agents, payload.get("prompt_id"), time.time() * 1000,
                      columns=int(columns) if columns.isdigit() else 0, color=not os.environ.get("NO_COLOR"),
                      main=payload if main else None, ascii=ascii or bool(os.environ.get("CV_KIT_ASCII")))
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
            log_event(json.loads(raw or "{}"), time.time() * 1000, CACHE / "agents")
        elif "--event" in argv or "--activity" in argv:
            log_event(json.loads(raw), time.time() * 1000, CACHE / "agents", activity="--activity" in argv)
        else:
            write_lines(status_line(raw, ascii="--ascii" in argv, main="--no-main" not in argv))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
