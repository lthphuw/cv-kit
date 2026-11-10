"""Always-on concise rules: hooks/concise.py adds hooks/concise.md at session and subagent start, and hooks/progress.md
(the main thread's Progress, Summarization and Next blocks) at session start only."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "hooks/concise.py"
RULES = (ROOT / "hooks/concise.md").read_text(encoding="utf-8").strip()
PROGRESS = (ROOT / "hooks/progress.md").read_text(encoding="utf-8").strip()


def run(stdin: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT)], input=stdin, capture_output=True, text=True, timeout=20)


@pytest.mark.parametrize(("event", "context"), [("SessionStart", RULES + "\n\n" + PROGRESS), ("SubagentStart", RULES)])
def test_adds_the_rules_as_context_for_each_event(event, context):
    result = run(json.dumps({"hook_event_name": event, "session_id": "t"}))
    assert result.returncode == 0
    out = json.loads(result.stdout)["hookSpecificOutput"]
    assert out == {"hookEventName": event, "additionalContext": context}


@pytest.mark.parametrize("stdin", ["", "not json", "[]", json.dumps({"hook_event_name": "PreToolUse"})])
def test_fails_open_without_output(stdin):
    result = run(stdin)
    assert result.returncode == 0 and result.stdout == ""


def test_rules_stay_under_the_context_cap_and_budget():
    # Claude Code saves a context string over 10,000 characters to a file and shows Claude only a preview.
    assert len(RULES) <= 2200 and len(PROGRESS) <= 1200


def test_concision_never_cuts_safety_or_the_test_rule():
    lowered = RULES.lower()
    for keyword in ("validation", "security", "data loss", "accessibility", "failing test", "shortcut:"):
        assert keyword in lowered, keyword


def test_prose_rules_reach_every_reply_and_subagent():
    # The tells of shared/prose.md a model makes most, in any language, plus decision-first replies.
    for needle in ("in any language", "not X but Y", "run-up", "I hope this helps", "em or en dashes",
                   "sentence-case", "decision first"):
        assert needle in RULES, needle


def test_hooks_json_registers_both_events():
    hooks = json.loads((ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]
    session = hooks["SessionStart"][0]
    assert session["matcher"] == "startup|resume|clear|compact"
    assert any("concise.py" in " ".join(h["args"]) for h in session["hooks"])
    assert any("concise.py" in " ".join(h["args"]) for g in hooks["SubagentStart"] for h in g["hooks"])


class TestProgressAndNextPrompts:
    """Subagents get only the STATUS line; the main thread alone gets the blocks, so subagents pay no tokens for them."""

    def test_subagents_get_the_status_line_and_no_block(self):
        assert "STATUS: done|blocked|failed — <15 words max>" in RULES
        for block in ("Progress (", "Summarization:", "Next:"):
            assert block not in RULES, block

    def test_main_thread_blocks_in_their_exact_shape(self):
        for shape in ("Progress (2/3 done):", "- engineer#1 clamp_boxes: done", "- engineer#2 NMS crash: running",
                      "- engineer#3 loader: failed",
                      "Summarization:", "at most 5 bullets", "Next:", "at most 3", "/cv-kit:review",
                      "commit the change", "/cv-kit:develop"):
            assert shape in PROGRESS, shape

    def test_no_status_icons(self):
        assert not any(icon in PROGRESS for icon in ("✅", "⏳", "❌", "✓", "✗")), "the user asked for plain words"
        assert "no icons" in PROGRESS

    def test_progress_asks_for_no_clock_the_main_thread_cannot_read(self):
        assert "·" not in PROGRESS.split("Progress (", 1)[1].split("\n", 1)[0]

    def test_progress_only_between_agents_and_next_is_last(self):
        assert "Not at launch, and not when the last one finishes" in PROGRESS
        assert "as the very last block" in PROGRESS

    def test_a_commit_is_never_suggested_over_red_tests_or_open_findings(self):
        assert "Never suggest a commit while tests are red or blocking findings are open" in PROGRESS

    def test_no_timer_heartbeat(self):
        assert "heartbeat" not in PROGRESS.lower() and "every minute" not in PROGRESS.lower()

    @pytest.mark.parametrize("path", ["agents/engineer.md", "agents/explorer.md", "agents/researcher.md",
                                      "agents/claim-verifier.md", "agents/reviewer.md", "agents/architect.md",
                                      "skills/develop/SKILL.md", "skills/develop/references/routing.md"])
    def test_the_hook_owns_the_rules_once(self, path):
        text = (ROOT / path).read_text(encoding="utf-8")
        assert "STATUS:" not in text and "Summarization" not in text, path
