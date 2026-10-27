"""Keep replies and code short in every session and subagent: adds hooks/concise.md as context.

Listens to SessionStart (startup, resume, clear, compact) and SubagentStart (see hooks/hooks.json). Standard library
only. It never blocks: any error means no context and the session starts as usual.

The rules are adapted from ponytail (MIT, copyright (c) 2026 DietrichGebert; the 6-rung ladder, the shortcut comment
and the never-cut list). Its lite and ultra levels, mode switching and config writes are not ported.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

EVENTS = {"SessionStart", "SubagentStart"}
RULES = Path(__file__).with_name("concise.md")


def main() -> int:
    try:
        event = json.load(sys.stdin).get("hook_event_name")
        if event not in EVENTS:
            return 0
        text = RULES.read_text(encoding="utf-8").strip()
    except (OSError, ValueError, AttributeError):
        return 0
    json.dump({"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
