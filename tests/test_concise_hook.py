"""Always-on concise rules: hooks/concise.py adds hooks/concise.md as context at session start and subagent start."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "hooks/concise.py"
RULES = (ROOT / "hooks/concise.md").read_text(encoding="utf-8").strip()


def run(stdin: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT)], input=stdin, capture_output=True, text=True, timeout=20)


@pytest.mark.parametrize("event", ["SessionStart", "SubagentStart"])
def test_adds_the_rules_as_context_for_each_event(event):
    result = run(json.dumps({"hook_event_name": event, "session_id": "t"}))
    assert result.returncode == 0
    out = json.loads(result.stdout)["hookSpecificOutput"]
    assert out == {"hookEventName": event, "additionalContext": RULES}


@pytest.mark.parametrize("stdin", ["", "not json", "[]", json.dumps({"hook_event_name": "PreToolUse"})])
def test_fails_open_without_output(stdin):
    result = run(stdin)
    assert result.returncode == 0 and result.stdout == ""


def test_rules_stay_under_the_context_cap_and_budget():
    # Claude Code saves a context string over 10,000 characters to a file and shows Claude only a preview.
    assert len(RULES) <= 3000


def test_concision_never_cuts_safety_or_the_test_rule():
    lowered = RULES.lower()
    for keyword in ("validation", "security", "data loss", "accessibility", "failing test", "shortcut:"):
        assert keyword in lowered, keyword


def test_hooks_json_registers_both_events():
    hooks = json.loads((ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]
    session = hooks["SessionStart"][0]
    assert session["matcher"] == "startup|resume|clear|compact"
    assert any("concise.py" in " ".join(h["args"]) for h in session["hooks"])
    assert any("concise.py" in " ".join(h["args"]) for g in hooks["SubagentStart"] for h in g["hooks"])
