"""Offline checks of the trigger eval suite in evals/. The suite itself runs by hand; see evals/README.md."""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
CASES = sorted(p.parent for p in EVALS.glob("*/prompt.md"))
GRADERS = sorted(p for case in CASES for p in (case / "graders").glob("*.md"))

# The documented format: https://code.claude.com/docs/en/plugin-evals.md, checked 2026-10-15 (Claude Code 2.1.300).
PROMPT_KEYS = {"schema_version", "name", "description", "tags", "plugins", "runs", "expected_outcome", "model",
               "max_turns", "timeout_seconds", "allowed_tools", "append_system_prompt", "env"}
READ_ONLY_TOOLS = {"Read", "Glob", "Grep", "NotebookRead", "Skill", "AskUserQuestion", "Agent", "TodoWrite",
                   "TaskCreate", "TaskGet", "TaskList", "TaskUpdate", "TaskStop"}
GRADER_KEYS = {"type", "weight", "arm"}
TYPE_KEYS = {
    "regex": {"pattern", "flags", "match", "target"},
    "tool_used": {"tool", "input_match", "min", "max"},
    "tool_order": {"before", "after"},
    "file_exists": {"path", "exists"},
    "llm": {"criteria", "focus"},
    "baseline": {"baseline_file", "criteria"},
}
ARMS = {"with-only", "both"}
CASE_NAME = re.compile(r"^\d{2}-(?P<subject>[a-z0-9-]+?)-(?P<kind>fire|nofire)-[a-z0-9-]+$")
OFF_TOPIC = "off-topic"
ANY_SKILL = "no-cv-kit-skill"
# Skill names that sit close to cv-kit's own and must never match a cv-kit pattern.
DECOYS = ("deep-research", "brainstorming", "superpowers:brainstorming", "model-selection", "commit",
          "cv-deep-research-v2", "figure", "code-review", "simplify", "review", "refactor", "py-cpp-review-v2")
# Strings each regex grader must and must not find in a final reply.
REGEX_SAMPLES = {
    "no-trailer": (
        ["Co-Authored-By: Claude <noreply@anthropic.com>", "Signed-off-by: A Dev <a@example.com>",
         "🤖 Generated with [Claude Code](https://claude.com/claude-code)"],
        ["refactor: rename load_weights to load_checkpoint", "I left out any Co-Authored-By trailer.",
         "No Signed-off-by line, as the project asks."],
    ),
}


def split(path: Path) -> tuple[dict, str]:
    match = re.match(r"---\n(.*?)\n---\n(.*)\Z", path.read_text(encoding="utf-8"), re.S)
    assert match, f"{path}: no frontmatter"
    front = yaml.safe_load(match.group(1)) or {}
    assert isinstance(front, dict), f"{path}: frontmatter is not a mapping"
    return front, match.group(2).strip()


def plugin_skills() -> dict[str, bool]:
    """Map each skill name to whether the model may invoke it."""
    skills = {}
    for md in sorted(ROOT.glob("skills/*/SKILL.md")):
        front, _ = split(md)
        skills[front["name"]] = not front.get("disable-model-invocation", False)
    return skills


SKILLS = plugin_skills()


def skill_graders() -> list[tuple[Path, str, str]]:
    """Return (grader file, kind, subject) for every grader on the Skill tool."""
    found = []
    for path in GRADERS:
        front, _ = split(path)
        if front.get("type") != "tool_used" or front.get("tool") != "Skill":
            continue
        stem = path.stem
        if stem == ANY_SKILL:
            found.append((path, "not-called", ANY_SKILL))
        elif stem.endswith("-fired"):
            found.append((path, "fired", stem.removesuffix("-fired")))
        elif stem.endswith("-not-called"):
            found.append((path, "not-called", stem.removesuffix("-not-called")))
        else:
            pytest.fail(f"{path}: a Skill grader is named <skill>-fired, <skill>-not-called or {ANY_SKILL}")
    return found


def skill_inputs(name: str) -> list[str]:
    """JSON-encoded Skill tool inputs naming this skill, in the forms a run may produce."""
    out = []
    for value in (name, f"cv-kit:{name}"):
        for args in ({}, {"args": "x"}):
            data = {"skill": value, **args}
            out += [json.dumps(data), json.dumps(data, separators=(",", ":"))]
    return out


def pattern_cases() -> list[dict]:
    """Every regex in the suite with the strings it must and must not match."""
    cases = []
    for path, _, subject in skill_graders():
        front, _ = split(path)
        wanted = set(SKILLS) if subject == ANY_SKILL else {subject}
        samples = [(s, name in wanted) for name in [*SKILLS, *DECOYS] for s in skill_inputs(name)]
        cases.append({"where": str(path.relative_to(ROOT)), "pattern": front["input_match"], "flags": "",
                      "samples": samples})
    for path in GRADERS:
        front, _ = split(path)
        if front.get("type") == "regex":
            hits, misses = REGEX_SAMPLES.get(path.stem, ([], []))
            cases.append({"where": str(path.relative_to(ROOT)), "pattern": front["pattern"],
                          "flags": front.get("flags", ""),
                          "samples": [(s, True) for s in hits] + [(s, False) for s in misses]})
    return cases


def test_suite_has_cases():
    assert len(CASES) >= 14
    others = {p.name for p in EVALS.iterdir() if p.is_dir()} - {c.name for c in CASES} - {"results"}
    assert not others, f"folders in evals/ that are not cases: {sorted(others)}"


def test_case_names_follow_the_convention():
    for case in CASES:
        match = CASE_NAME.match(case.name)
        assert match, f"{case.name}: name it NN-<skill or {OFF_TOPIC}>-<fire|nofire>-<slug>"
        assert match["subject"] in SKILLS or match["subject"] == OFF_TOPIC, case.name
        assert not (match["subject"] == OFF_TOPIC and match["kind"] == "fire"), case.name


@pytest.mark.parametrize("case", CASES, ids=lambda p: p.name)
def test_prompt_uses_documented_fields(case):
    front, body = split(case / "prompt.md")
    assert set(front) <= PROMPT_KEYS, f"undocumented keys: {sorted(set(front) - PROMPT_KEYS)}"
    assert body, "the prompt body is empty"
    tools = set(front.get("allowed_tools", []))
    assert "Skill" in tools, "a trigger case needs the Skill tool"
    assert tools <= READ_ONLY_TOOLS, f"tools that need a grant: {sorted(tools - READ_ONLY_TOOLS)}"
    assert isinstance(front.get("max_turns", 10), int) and 1 <= front.get("max_turns", 10) <= 200
    assert isinstance(front.get("tags", []), list)
    assert list((case / "graders").glob("*.md")), "a case without a grader fails to load"


@pytest.mark.parametrize("path", GRADERS, ids=lambda p: f"{p.parent.parent.name}/{p.stem}")
def test_grader_uses_documented_fields(path):
    front, body = split(path)
    kind = front.get("type")
    assert kind in TYPE_KEYS, f"unknown grader type {kind!r}"
    allowed = GRADER_KEYS | TYPE_KEYS[kind]
    assert set(front) <= allowed, f"undocumented keys: {sorted(set(front) - allowed)}"
    assert front.get("arm") in ARMS | {None}
    weight = front.get("weight", 1)
    assert isinstance(weight, (int, float)) and weight > 0
    if kind == "regex":
        assert front.get("pattern"), "a regex grader needs a pattern"
        assert set(front.get("flags", "")) <= {"i", "s"}, "use flags i or s; inline (?i) is not supported"
        match = front.get("match")
        assert match is None or match == "not_contains" or re.fullmatch(r"count:\d+", str(match))
        assert path.stem in REGEX_SAMPLES, "add sample strings for this grader to REGEX_SAMPLES"
    if kind == "llm":
        assert body or front.get("criteria"), "an llm grader needs a rubric"
        assert "PASS" in body and "FAIL" in body, "write the rubric as PASS and FAIL conditions"
    if kind == "tool_used" and front.get("tool") == "Skill":
        assert front.get("input_match"), "a Skill grader must name the skill"
        if front.get("max") == 0:
            assert front.get("min") == 0 and front.get("arm") == "both", "a never-called check needs min 0 and arm both"


def test_skill_graders_are_well_formed():
    for path, kind, subject in skill_graders():
        front, _ = split(path)
        assert subject == ANY_SKILL or subject in SKILLS, f"{path}: no skill named {subject!r}"
        if kind == "fired":
            assert front.get("min", 1) >= 1 and "max" not in front and "arm" not in front, path
        else:
            assert (front.get("min"), front.get("max"), front.get("arm")) == (0, 0, "both"), path


def test_case_name_matches_its_graders():
    by_case: dict[str, set[tuple[str, str]]] = {}
    for path, kind, subject in skill_graders():
        by_case.setdefault(path.parent.parent.name, set()).add((kind, subject))
    for case in CASES:
        match = CASE_NAME.match(case.name)
        found = by_case.get(case.name, set())
        if match["subject"] == OFF_TOPIC:
            assert ("not-called", ANY_SKILL) in found, case.name
        else:
            want = ("fired" if match["kind"] == "fire" else "not-called", match["subject"])
            assert want in found, f"{case.name}: missing grader {want[1]}-{want[0]}"


def test_every_skill_has_a_fire_and_a_no_fire_case():
    seen = {(kind, subject) for _, kind, subject in skill_graders()}
    for skill, model_invocable in SKILLS.items():
        assert ("not-called", skill) in seen, f"{skill}: no case checks that it does not fire"
        if model_invocable:
            assert ("fired", skill) in seen, f"{skill}: no case checks that it fires"
        else:
            assert ("fired", skill) not in seen, f"{skill} is user-invoked only; the model cannot fire it"


def test_patterns_match_only_their_own_skill():
    for case in pattern_cases():
        for sample, want in case["samples"]:
            got = bool(re.search(case["pattern"], sample, re.I if "i" in case["flags"] else 0))
            assert got == want, f"{case['where']}: {sample!r} should {'' if want else 'not '}match"


NODE_CHECK = """
const cases = JSON.parse(require("fs").readFileSync(0, "utf8"));
const bad = [];
for (const c of cases) {
  let re;
  try { re = new RegExp(c.pattern, c.flags); } catch (e) { bad.push(c.where + ": " + e.message); continue; }
  for (const [s, want] of c.samples) {
    if (re.test(s) !== want) bad.push(c.where + ": " + JSON.stringify(s) + (want ? " should match" : " should not match"));
  }
}
process.stdout.write(JSON.stringify(bad));
"""


def test_patterns_behave_the_same_under_node():
    # The eval runner is a JavaScript program, so every pattern must also work as a JavaScript RegExp.
    node = shutil.which("node")
    if node is None:
        if os.environ.get("CI"):
            pytest.fail("node is required in CI to check the eval regexes")
        pytest.skip("node not installed")
    result = subprocess.run([node, "-e", NODE_CHECK], input=json.dumps(pattern_cases()), capture_output=True,
                            text=True, encoding="utf-8", check=False)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == []


def test_results_folder_is_ignored():
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "evals/results/" in lines
