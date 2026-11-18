#!/usr/bin/env python3
"""Draw one status line row per subagent: `◐ engineer (sonnet ▰▰▱▱▱)  clamp boxes  4m12s`.

Claude Code sends a status line command no subagent data, so the plugin's hooks collect it (hooks/hooks.json):

- `--event` runs on PreToolUse, PostToolUse and PostToolUseFailure of the Agent tool, SubagentStart and SubagentStop.
  It appends one JSON line per event to `~/.cache/cv-kit/agents/<session_id>.jsonl`. An append of one short line is
  atomic, so agents that start together do not overwrite each other. The Agent call gives the type, description, model and effort; the
  start and stop give the agent id and the clock. A call pairs with the next start of its type under the same
  prompt, and the `agentId` in PostToolUse corrects the pair when two calls of one type ran together. A failed call
  ends its agent as failed.
- `--register` runs at SessionStart: it writes this plugin's root to `~/.cache/cv-kit/agent-rows-root`, so the
  user's `statusLine` command can find this script, and deletes logs older than a day. cv-kit 0.9.1 and older wrote
  `plugin-root` to a root without this script, so the name differs. On a resume it logs a reset: agents still
  marked running died with the old process and show `■`.
- With no flag, it is the status line: stdin is the status line JSON, stdout one row per agent. Running agents show
  first, then the agents that finished under the current prompt; past `MAX_ROWS` a `+N more` line counts the rest.
  A foreground agent from an earlier prompt was interrupted (Esc runs no hook), so it is not shown.

A plugin cannot set `statusLine`, so the user adds it (hooks/README.md). Standard library only; any error prints
nothing and exits 0, so a hook never blocks and the status line stays as it was.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path.home() / ".cache" / "cv-kit"
MODELS = ("haiku", "sonnet", "opus", "fable")
LEVELS = ("low", "medium", "high", "xhigh", "max")
LEVEL_COLORS = ("32", "36", "33", "38;5;208", "31")  # green, cyan, yellow, orange, red
SPINNER = "◐◓◑◒"
DIM, BOLD, RUNNING, DONE, FAILED = "2", "1", "1;33", "32", "1;31"
MAX_ROWS = 6
RECENT_MS = 60_000  # without a prompt id, a finished row shows this long
NAME_MAX, LABEL_MAX, DESC_MAX = 16, 48, 200
LOG_TTL = 86400  # seconds
# Widest first, the first that fits wins: (model, effort meter, fewest label columns; None = no label).
STEPS = ((True, True, 12), (True, False, 12), (False, False, 6), (False, False, None))
CONTROL = re.compile(r"[\x00-\x1f\x7f]+")
SESSION = re.compile(r"[A-Za-z0-9_-]{1,128}")
AGENT_NAME = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
FRONT_MODEL = re.compile(r"^model:\s*(\S+)\s*$", re.M)

Cell = list[tuple[str, str]]  # (text, SGR code); "" = plain


# --- the log -----------------------------------------------------------------------------------------------------


def log_path(folder: Path, session) -> Path | None:
    return folder / f"{session}.jsonl" if isinstance(session, str) and SESSION.fullmatch(session) else None


def short_id(value) -> str:
    return str(value or "").removeprefix("agent-")


def event_line(payload: dict, now_ms: float) -> dict | None:
    """The log line for one hook payload, or None when the event is not about a subagent."""
    name, prompt = payload.get("hook_event_name"), payload.get("prompt_id")
    if name in ("PreToolUse", "PostToolUse", "PostToolUseFailure") and payload.get("tool_name") == "Agent":
        tool_input = payload.get("tool_input") or {}
        if name == "PreToolUse":
            return {"e": "call", "t": now_ms, "tu": payload.get("tool_use_id"),
                    "type": str(tool_input.get("subagent_type") or "general-purpose"),
                    "desc": str(tool_input.get("description") or "")[:DESC_MAX],
                    "model": str(tool_input.get("model") or ""), "effort": str(tool_input.get("effort") or ""),
                    "p": prompt}
        if name == "PostToolUseFailure":
            return {"e": "fail", "t": now_ms, "tu": payload.get("tool_use_id")}
        response = payload.get("tool_response")
        agent = response.get("agentId") if isinstance(response, dict) else None
        if not agent:
            return None
        return {"e": "link", "t": now_ms, "tu": payload.get("tool_use_id"), "id": short_id(agent),
                "bg": response.get("status") == "async_launched"}  # PostToolUse at launch: a background agent
    if name in ("SubagentStart", "SubagentStop") and payload.get("agent_type") and payload.get("agent_id"):
        line = {"e": "start" if name == "SubagentStart" else "stop", "t": now_ms,
                "id": short_id(payload["agent_id"]), "type": str(payload["agent_type"])}
        return {**line, "p": prompt} if name == "SubagentStart" else line
    if name == "SessionStart" and payload.get("source") == "resume":  # a new process: no agent kept running
        return {"e": "reset", "t": now_ms}
    return None


def log_event(payload: dict, now_ms: float, folder: Path) -> None:
    path = log_path(folder, payload.get("session_id"))
    line = event_line(payload, now_ms)
    if path is None or line is None:
        return
    folder.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as out:  # one write of one line: O_APPEND keeps it whole
        out.write(json.dumps(line, ensure_ascii=False) + "\n")


def read_events(path: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    events = []
    for raw in text.splitlines():
        try:
            event = json.loads(raw)
        except ValueError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def fold(events: list[dict]) -> list[dict]:
    """One dict per agent, in the order they first started."""
    agents: dict[str, dict] = {}
    first: dict[str, tuple[float, object]] = {}  # agent id -> time and prompt of its first start
    calls: list[dict] = []
    links: dict[str, str] = {}  # tool_use_id -> agent id
    background: set[str] = set()
    failures: dict[str, float] = {}  # tool_use_id -> time
    for event in events:
        kind, agent_id, at = event.get("e"), event.get("id"), event.get("t")
        if kind == "call":
            calls.append(event)
        elif kind == "link" and event.get("tu") and agent_id:
            links[event["tu"]] = agent_id
            if event.get("bg"):
                background.add(agent_id)
        elif kind == "fail" and event.get("tu"):
            failures[event["tu"]] = at if isinstance(at, (int, float)) else 0
        elif kind == "start" and agent_id:
            first.setdefault(agent_id, (at if isinstance(at, (int, float)) else 0, event.get("p")))
            agent = agents.setdefault(agent_id, {"id": agent_id, "type": event.get("type", ""), "label": "",
                                                 "model": "", "effort": "", "prompt": None, "start": at,
                                                 "end": None, "failed": False, "lost": False, "background": False})
            # a resumed agent runs again, under the prompt that resumed it
            agent.update(start=at, end=None, lost=False, prompt=event.get("p") or agent["prompt"])
        elif kind == "stop" and agent_id in agents:
            agents[agent_id]["end"] = at
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
                    and (call.get("t") or 0) <= started):
                paired[agent_id], call["used"] = call, True
                break
    for agent_id, agent in agents.items():
        call = paired.get(agent_id, {})
        agent.update(label=call.get("desc", ""), model=call.get("model", ""), effort=call.get("effort", ""),
                     background=agent_id in background, prompt=agent["prompt"] or call.get("p"))
        if agent["end"] is None and call.get("tu") in failures:
            agent["end"], agent["failed"] = failures[call["tu"]], True
    return list(agents.values())


# --- drawing -----------------------------------------------------------------------------------------------------


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
                out.append((kept, style))
                while out and not out[-1][0].strip():  # no padding left before the ellipsis
                    out.pop()
                if out:
                    out[-1] = (out[-1][0].rstrip(), out[-1][1])
                return out + [("…", "")]
            kept += ch
            used += char_width(ch)
        out.append((kept, style))
    return out


def pad(cell: Cell, size: int, right: bool = False) -> Cell:
    space = [(" " * max(0, size - width(cell)), "")]
    return space + cell if right else cell + space


def clock(ms: float) -> str:
    seconds = max(0, int(ms // 1000))
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}h{minutes:02d}m"
    return f"{minutes}m{secs:02d}s" if minutes else f"{secs}s"


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


def effort_meter(effort: str) -> Cell:
    level = effort.strip().lower()
    if not level:
        return []
    if level not in LEVELS:
        return [(level[:6], "")]
    filled = LEVELS.index(level) + 1
    return [("▰" * filled, LEVEL_COLORS[filled - 1]), ("▱" * (len(LEVELS) - filled), DIM)]


def cells(agent: dict, now_ms: float) -> dict[str, Cell]:
    agent_type = str(agent.get("type") or "agent")
    name = agent_type.removeprefix("cv-kit:")
    label = re.sub(r" +", " ", CONTROL.sub(" ", str(agent.get("label") or ""))).strip()
    model = short_model(str(agent.get("model") or "") or frontmatter_model(agent_type))
    start, end = float(agent["start"]), agent.get("end")
    if end is None:
        icon = (SPINNER[int(now_ms // 1000) % len(SPINNER)], RUNNING)
    else:
        icon = ("✗", FAILED) if agent.get("failed") else ("■", DIM) if agent.get("lost") else ("✓", DONE)
    row = {"icon": [icon], "name": clip([(name, BOLD)], NAME_MAX), "model": [(model, "")] if model else [],
           "meter": effort_meter(str(agent.get("effort") or "")), "label": [(label, "")] if label else [],
           "time": [(clock((now_ms if end is None else float(end)) - start), "")]}
    if end is not None and not agent.get("failed"):  # finished rows fade; running and failed ones stand out
        row.update({key: [(text, DIM) for text, _ in row[key]] for key in ("name", "model", "label", "time")})
    return row


def head(row: dict[str, Cell], model: bool, meter: bool) -> Cell:
    group = row["model"] if model else []
    if model and meter and row["meter"]:
        group = group + ([(" ", "")] if group else []) + row["meter"]
    return row["name"] + ([(" (", DIM)] + group + [(")", DIM)] if group else [])


def layout(rows: list[dict[str, Cell]], columns: int) -> tuple[tuple[bool, bool], dict[str, int]]:
    label_max = min(LABEL_MAX, max(width(row["label"]) for row in rows))
    time_w = max(width(row["time"]) for row in rows)
    for model, meter, label_min in STEPS:
        head_w = max(width(head(row, model, meter)) for row in rows)
        room = columns - (2 + head_w + 2 + time_w) - 2 if columns else label_max
        if label_min is not None and label_max and room < min(label_min, label_max):
            continue
        label_w = min(label_max, room) if label_min is not None else 0
        return (model, meter), {"head": head_w, "label": max(0, label_w), "time": time_w}
    raise AssertionError("the last step always fits")


def line(row: dict[str, Cell], step: tuple[bool, bool], widths: dict[str, int]) -> Cell:
    out = row["icon"] + [(" ", "")] + pad(head(row, *step), widths["head"])
    if widths["label"]:
        out += [("  ", "")] + pad(clip(row["label"], widths["label"]), widths["label"])
    return out + [("  ", "")] + pad(row["time"], widths["time"], right=True)


def paint(cell: Cell, color: bool) -> str:
    return "".join(f"\x1b[{style}m{text}\x1b[0m" if color and style and text else text for text, style in cell)


def visible(agents: list[dict], prompt, now_ms: float) -> list[dict]:
    # A foreground agent cannot outlive its prompt: one from an earlier prompt was interrupted, and Esc runs no hook.
    running = [a for a in agents if a.get("end") is None
               and (a.get("background") or not prompt or a.get("prompt") in (None, prompt))]
    if prompt:
        done = [a for a in agents if a.get("end") is not None and a.get("prompt") == prompt]
    else:
        done = [a for a in agents if a.get("end") is not None and now_ms - float(a["end"]) <= RECENT_MS]
    return running + done


def render(agents: list[dict], prompt, now_ms: float, columns: int = 0, color: bool = True) -> list[str]:
    """One string per row, cut to `columns` (0 = no limit)."""
    shown = []
    for agent in visible(agents, prompt, now_ms):
        try:
            shown.append(cells(agent, now_ms))
        except (KeyError, TypeError, ValueError):  # one bad agent loses its row; the others still draw
            continue
    if not shown:
        return []
    extra = len(shown) - MAX_ROWS
    shown = shown[:MAX_ROWS]
    step, widths = layout(shown, columns)
    lines = []
    for row in shown:
        cell = line(row, step, widths)
        while cell and not cell[-1][0].strip():
            cell.pop()
        lines.append(paint(clip(cell, columns) if columns else cell, color))
    if extra > 0:
        lines.append(paint([(f"+{extra} more", DIM)], color))
    return lines


# --- the command line --------------------------------------------------------------------------------------------


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(f"{path.name}.{os.getpid()}")
    part.write_text(text, encoding="utf-8")
    os.replace(part, path)


def register() -> None:
    # shortcut: one pointer per user, the last session to start wins; fine while every copy draws the same rows.
    try:
        write_atomic(CACHE / "agent-rows-root", str(ROOT))
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


def status_line(raw: str) -> list[str]:
    try:
        payload = json.loads(raw)
        path = log_path(CACHE / "agents", payload.get("session_id"))
        if path is None:
            return []
        columns = os.environ.get("COLUMNS", "")
        return render(fold(read_events(path)), payload.get("prompt_id"), time.time() * 1000,
                      columns=int(columns) if columns.isdigit() else 0, color=not os.environ.get("NO_COLOR"))
    except Exception:
        return []


def main(argv: list[str]) -> int:
    try:
        if "--register" in argv:
            register()
            log_event(json.loads(sys.stdin.read() or "{}"), time.time() * 1000, CACHE / "agents")
        elif "--event" in argv:
            log_event(json.loads(sys.stdin.read()), time.time() * 1000, CACHE / "agents")
        else:
            out = status_line(sys.stdin.read())
            if out:
                print("\n".join(out))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
