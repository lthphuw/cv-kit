"""Cross-file promises of the shipped plugin: model aliases, hooks, agent fields, skill wiring."""
import json
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILLS = sorted(p.parent.name for p in ROOT.glob("skills/*/SKILL.md"))
AGENTS = sorted(p.stem for p in ROOT.glob("agents/*.md"))
FULL_MODEL_ID = re.compile(r"claude-(?:haiku|sonnet|opus|fable)-\d")
ALIASES = {"haiku", "sonnet", "opus"}


def front(path: Path) -> dict:
    return yaml.safe_load(re.match(r"---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.S).group(1))


def hooks() -> dict:
    return json.loads((ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]


class TestModelAliases:
    """The Agent tool takes `haiku`, `sonnet`, `opus` or `fable` per call and rejects a full model id."""

    @pytest.mark.parametrize("path", sorted(ROOT.glob("skills/**/*.md")), ids=lambda p: str(p.relative_to(ROOT)))
    def test_skills_never_tell_claude_to_pass_a_full_model_id(self, path):
        assert not FULL_MODEL_ID.search(path.read_text(encoding="utf-8")), path

    @pytest.mark.parametrize("agent", AGENTS)
    def test_agents_name_their_model_by_alias(self, agent):
        assert front(ROOT / f"agents/{agent}.md")["model"] in ALIASES

    def test_the_routing_table_names_all_three_aliases(self):
        text = (ROOT / "skills/develop/SKILL.md").read_text(encoding="utf-8")
        for alias in ALIASES:
            assert f"`{alias}`" in text


def routing_rows() -> list[tuple[str, str, str]]:
    """(agent, model, effort) for each row of the routing table in develop."""
    text = (ROOT / "skills/develop/SKILL.md").read_text(encoding="utf-8")
    table = text.split("## Route the work", 1)[1]
    return re.findall(r"^\|[^|]*\| `([a-z-]+)` \| `([a-z]+)` \| (\w+) \|$", table, re.M)


class TestRouting:
    """Sonnet at high does most of the work; Opus is kept for the few rows where the reasoning is the hard part."""

    @pytest.mark.parametrize("agent", ["engineer", "reviewer"])
    def test_workers_default_to_sonnet_high(self, agent):
        fm = front(ROOT / f"agents/{agent}.md")
        assert (fm["model"], fm["effort"]) == ("sonnet", "high")

    def test_opus_is_the_exception_in_the_table(self):
        rows = routing_rows()
        opus = [r for r in rows if r[1] == "opus"]
        assert len(rows) >= 6 and len(opus) <= 3
        assert ("engineer", "sonnet", "high") in rows and ("reviewer", "sonnet", "high") in rows

    def test_a_design_goes_to_the_architect_not_to_an_opus_engineer(self):
        """One agent designs and returns the packages; the engineers that build them stay on Sonnet."""
        text = (ROOT / "skills/develop/SKILL.md").read_text(encoding="utf-8")
        table = text.split("## Route the work", 1)[1]
        assert ("architect", "opus", "high") in routing_rows()
        hard = next(line for line in table.splitlines() if "`engineer` | `opus`" in line)
        assert "design" not in hard.lower() and "public API" not in hard
        design = next(p for p in text.split("\n\n") if p.startswith("**Design before code.**"))
        assert "wait for the user's yes" in design and "`xhigh`" in design
        assert "share an interface or a data flow" in design and "share nothing" in design
        scoping = (ROOT / "skills/develop/references/scoping.md").read_text(encoding="utf-8")
        assert "`architect`" in scoping

    def test_a_designed_or_opus_written_change_is_reviewed_on_opus(self):
        row = next(r for r in (ROOT / "skills/develop/SKILL.md").read_text(encoding="utf-8").splitlines()
                   if "`reviewer` | `opus`" in r)
        assert "`architect`" in row and "`opus` engineer" in row

    def test_the_brief_has_every_field(self):
        text = (ROOT / "skills/develop/SKILL.md").read_text(encoding="utf-8")
        for field in ("Goal:", "Done when:", "Facts:", "Files:", "Constraints:", "Ruled out:", "Mode:"):
            assert field in text, field

    def test_a_failed_attempt_is_rebriefed_before_it_is_escalated(self):
        text = (ROOT / "skills/develop/SKILL.md").read_text(encoding="utf-8")
        assert "same model" in text and "SendMessage" in text and "at most three" in text

    def test_the_main_thread_delegates_even_when_the_files_are_small(self):
        """Eval 21: the main thread read seven small files, found the deadlock and fixed it without an agent."""
        text = (ROOT / "skills/develop/SKILL.md").read_text(encoding="utf-8")
        assert "names the line and the change" in text
        assert "never a one-line change" in text
        assert "Small files are not a reason" in text
        assert "before reading code" in text

    def test_the_engineer_stays_inside_its_brief(self):
        text = (ROOT / "agents/engineer.md").read_text(encoding="utf-8")
        assert "outside `Files`" in text and "diagnose" in text

    def test_review_defaults_to_sonnet(self):
        text = (ROOT / "skills/review/SKILL.md").read_text(encoding="utf-8")
        assert "`model` `sonnet`, `effort` `high`" in text

    def test_the_reviewer_is_handed_the_diff_because_it_has_no_shell(self):
        assert "Bash" not in front(ROOT / "agents/reviewer.md")["tools"]
        assert "no shell" in (ROOT / "agents/reviewer.md").read_text(encoding="utf-8")
        review = (ROOT / "skills/review/SKILL.md").read_text(encoding="utf-8")
        assert "paste the diff" in review and "`go vet`" in review


class TestHooks:
    def handlers(self, event: str):
        return [(g.get("matcher"), h) for g in hooks().get(event, []) for h in g["hooks"]]

    def test_the_trailer_hook_blocks_when_it_fails(self):
        trailer = [h for _, h in self.handlers("PreToolUse") if "block_trailers.py" in " ".join(h.get("args", []))]
        assert trailer and all(h.get("onFailure") == "block" for h in trailer)

    @pytest.mark.parametrize("event, matcher", [("PostToolUse", "Bash"), ("PostToolUse", "Edit|Write|MultiEdit"),
                                                ("PostToolUseFailure", "Bash"), ("Stop", None),
                                                ("SubagentStop", "^cv-kit:engineer$")])
    def test_the_gate_listens_to_its_events(self, event, matcher):
        found = [m for m, h in self.handlers(event) if "evidence_gate.py" in " ".join(h.get("args", []))]
        assert matcher in found

    def test_the_gate_uses_exec_form_and_never_blocks_on_its_own_failure(self):
        for event in ("PostToolUse", "PostToolUseFailure", "Stop", "SubagentStop"):
            for _, h in self.handlers(event):
                if "evidence_gate.py" in " ".join(h.get("args", [])):
                    assert h["command"] == "python3" and "onFailure" not in h


class TestAgents:
    def test_the_roster_has_no_agent_whose_job_a_skill_already_does(self):
        """`lead` repeated the routing in `develop`; the main thread routes from the skill instead."""
        assert AGENTS == ["architect", "claim-verifier", "engineer", "explorer", "researcher", "reviewer"]

    @pytest.mark.parametrize("agent", ["explorer", "claim-verifier", "researcher", "architect"])
    def test_runaway_guard(self, agent):
        assert isinstance(front(ROOT / f"agents/{agent}.md").get("maxTurns"), int)

    def test_the_blind_verifier_starts_without_project_instructions(self):
        assert front(ROOT / "agents/claim-verifier.md").get("omitClaudeMd") is True

    def test_the_architect_designs_and_cannot_edit(self):
        fm = front(ROOT / "agents/architect.md")
        assert fm["tools"] == "Read, Grep, Glob" and (fm["model"], fm["effort"]) == ("opus", "high")
        text = (ROOT / "agents/architect.md").read_text(encoding="utf-8")
        for section in ("`Options`", "`Flow`", "`Interfaces`", "`Invariants`", "`Packages`", "`Risks`", "`Decisions`"):
            assert section in text, section
        for field in ("`Goal`", "`Done when`", "`Files`", "`Constraints`", "`Depends on`"):
            assert field in text, field

    def test_one_verifier_per_candidate(self):
        """One verifier for six candidates ran out of turns; each checks its own candidate's claims."""
        assert "one per candidate" in front(ROOT / "agents/claim-verifier.md")["description"].lower()
        text = (ROOT / "skills/research/SKILL.md").read_text(encoding="utf-8")
        assert "--candidate" in (ROOT / "agents/claim-verifier.md").read_text(encoding="utf-8")
        assert "checks-<candidate>.json" in text and "--checks checks-*.json" in text

    @pytest.mark.parametrize("path", ["agents/reviewer.md", "skills/develop/SKILL.md", "skills/review/SKILL.md"])
    def test_descriptions_name_go(self, path):
        assert "Go" in front(ROOT / path)["description"], path


class TestSkills:
    @pytest.mark.parametrize("skill", SKILLS)
    def test_argument_hint(self, skill):
        assert front(ROOT / f"skills/{skill}/SKILL.md").get("argument-hint")

    @pytest.mark.parametrize("skill", ["develop", "review", "commit"])
    def test_live_facts_are_injected_and_pre_approved(self, skill):
        path = ROOT / f"skills/{skill}/SKILL.md"
        body, fm = path.read_text(encoding="utf-8"), front(path)
        assert "!`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project_facts.py facts" in body
        assert "project_facts.py" in str(fm["allowed-tools"])

    def test_develop_arms_the_gate_with_the_session_id(self):
        path = ROOT / "skills/develop/SKILL.md"
        assert "evidence_gate.py arm ${CLAUDE_SESSION_ID}`" in path.read_text(encoding="utf-8")
        assert "evidence_gate.py" in str(front(path)["allowed-tools"])

    def test_every_injected_script_exists(self):
        for path in ROOT.glob("skills/*/SKILL.md"):
            for rel in re.findall(r"!`python3 \$\{CLAUDE_PLUGIN_ROOT\}/(\S+)", path.read_text(encoding="utf-8")):
                assert (ROOT / rel).is_file(), f"{path}: {rel}"

    def test_develop_says_how_to_run_unattended(self):
        text = (ROOT / "skills/develop/SKILL.md").read_text(encoding="utf-8")
        assert "/goal" in text and "/loop" in text

    def test_develop_writes_goal_loop_and_headless_lines(self):
        text = (ROOT / "skills/develop/SKILL.md").read_text(encoding="utf-8")
        for needle in ("/goal", "/loop", "claude -p", "4,000", ".cv-kit-stop", "Or stop after", "change no code"):
            assert needle in text, needle

    def test_setup_offers_the_commit_guard_settings(self):
        text = (ROOT / "skills/setup/references/settings.md").read_text(encoding="utf-8")
        for needle in ("permissions", "ask", "Bash(git commit *)", "Bash(git push *)", "attribution"):
            assert needle in text

    def test_review_complements_the_built_in_reviews(self):
        text = (ROOT / "skills/review/SKILL.md").read_text(encoding="utf-8")
        assert "/code-review" in text and "/security-review" in text


class TestDocs:
    def test_the_eval_readme_does_not_claim_agents_cannot_run(self):
        assert "cannot start an agent" not in (ROOT / "evals/README.md").read_text(encoding="utf-8")

    def test_the_hook_readme_says_the_hook_is_not_absolute(self):
        text = (ROOT / "hooks/README.md").read_text(encoding="utf-8")
        assert "onFailure" in text and "mod" in text.lower()
