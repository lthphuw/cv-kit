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

# The documented format: https://code.claude.com/docs/en/plugin-evals.md, checked 2026-11-11 (Claude Code 2.1.322).
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
# Skill names from other plugins that sit close to cv-kit's own and must never match a cv-kit pattern.
DECOYS = ("deep-research", "superpowers:brainstorming", "superpowers:requesting-code-review",
          "superpowers:test-driven-development", "commit-commands:commit", "code-review", "simplify",
          "figma:figure", "other:review", "develop-v2", "research-notes", "reviewer", "setup-env", "recommit")
# Strings each regex grader must and must not find in a final reply.
REGEX_SAMPLES = {
    "plain-prose": (
        ["RF-DETR is the pick — the latency is open.", "YOLO11 – AGPL-3.0, so it is out.", "I hope this helps!",
         "Great question! First the brief.", "Let's dive into the candidates.", "Here's the thing: no latency.",
         "Want me to search arXiv now?"],
        ["| YOLO11 | — | AGPL-3.0 |", "Papers from 2024–2025 only.", "Which dataset and split? I assumed COCO val2017.",
         "Next:\n- /cv-kit:research small objects on VisDrone", "Let me check the model card first."],
    ),
    "tests-written": (
        ['{"type":"tool_use","name":"Edit","input":{"file_path":"/w/tests/test_utils.py","old_string":"a"}}',
         '{"type":"tool_use","name":"Edit","input":{"replace_all":false,"file_path":"/w/tests/test_utils.py"}}',
         '{"type":"tool_use","name":"Write","input":{"file_path":"/w/tests/nms_test.cc","content":"x"}}'],
        ['{"type":"tool_use","name":"Edit","input":{"file_path":"/w/vision/utils.py","old_string":"a"}}',
         '{"type":"tool_use","name":"Read","input":{"file_path":"/w/tests/test_utils.py"}}'],
    ),
    "test-before-code": (
        # the production file is edited with no edit of a test before it: the grader fails the run
        ['{"name":"Read","input":{"file_path":"/w/tests/test_utils.py"}}\n'
         '{"name":"Edit","input":{"file_path":"/w/vision/utils.py"}}\n'
         '{"name":"Edit","input":{"file_path":"/w/tests/test_utils.py"}}',
         '{"name":"Edit","input":{"replace_all":false,"file_path":"/w/vision/utils.py","old_string":"a"}}\n'
         '{"name":"Edit","input":{"replace_all":false,"file_path":"/w/tests/test_utils.py"}}',
         '{"name":"Write","input":{"file_path":"/w/vision/utils.py"}}'],
        # a test is edited first, or the production file is never edited: the grader passes the run
        ['{"name":"Edit","input":{"file_path":"/w/tests/test_utils.py"}}\n'
         '{"name":"Edit","input":{"file_path":"/w/vision/utils.py"}}',
         '{"name":"Edit","input":{"replace_all":false,"file_path":"/w/tests/test_utils.py"}}\n'
         '{"name":"Edit","input":{"replace_all":false,"file_path":"/w/vision/utils.py"}}',
         '{"name":"Read","input":{"file_path":"/w/vision/utils.py"}}\n'
         '{"name":"Edit","input":{"file_path":"/w/tests/test_utils.py"}}'],
    ),
    "test-before-fix": (
        ['{"name":"Edit","input":{"file_path":"/w/src/post/nms.cc"}}\n'
         '{"name":"Edit","input":{"file_path":"/w/tests/nms_test.cc"}}',
         '{"name":"Edit","input":{"replace_all":false,"file_path":"/w/src/post/nms.cc"}}'],
        ['{"name":"Edit","input":{"file_path":"/w/tests/nms_test.cc"}}\n'
         '{"name":"Edit","input":{"file_path":"/w/src/post/nms.cc"}}',
         '{"name":"Read","input":{"file_path":"/w/src/post/nms.cc"}}'],
    ),
    "report-format": (
        ["[Critical] CPP-ERR-8 snippet:5\nWhat: it throws.\n\nBlocking: 2 Critical, 1 Major",
         "**[Major] PY-ML-1** snippet:9\nWhat: unseeded shuffle.\n\n**Blocking:** 0 Critical, 1 Major",
         "[Critical] no rule snippet:3\nWhat: frames of one video on both sides.\nBlocking: 1 Critical, 0 Major"],
        ["Critical: the constructor throws (line 5).\nBlocking: 1 Critical, 0 Major",
         "[Critical] CPP-ERR-8 snippet:5\nWhat: it throws.\nVerdict: do not merge.",
         "Blocking: 1 Critical, 0 Major\n\n[Critical] CPP-ERR-8 snippet:5"],
    ),
    "goal-line-bounded": (
        ["```\n/goal follow /cv-kit:develop. letterbox is added. Or stop after 25 turns.\n```",
         "`/goal`, because the task has an end.\n```\nletterbox exists; `pytest -q` exits 0. or stop after 15 turns\n```"],
        ["/goal add letterbox. Or stop after 25 turns.", "```\n/goal add letterbox until pytest passes\n```",
         "```\n/goal add letterbox\n```\nIt will stop after a while."],
    ),
    "goal-line-guards": (
        ["Do not commit. Or stop after 25 turns. After two failed fixes, stop and report the literal output.",
         "After two failed fixes, stop.\nno commit, no push"],
        ["Do not commit. Or stop after 25 turns.", "After two failed fixes, stop and report.",
         "Commit when green. After two failed fixes, stop."],
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
            flags = (re.I if "i" in case["flags"] else 0) | (re.S if "s" in case["flags"] else 0)
            got = bool(re.search(case["pattern"], sample, flags))
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


AGENT_SAMPLES = {
    "engineer-on-opus": (
        ['{"description":"x","subagent_type":"cv-kit:engineer","model":"opus","prompt":"p"}',
         '{"model":"opus","subagent_type":"engineer","prompt":"p"}'],
        ['{"subagent_type":"cv-kit:engineer","model":"sonnet"}', '{"subagent_type":"cv-kit:explorer","model":"opus"}',
         '{"subagent_type":"cv-kit:engineer","prompt":"use opus"}'],
    ),
    "explorer-on-haiku": (
        ['{"subagent_type":"cv-kit:explorer","model":"haiku","prompt":"p"}', '{"model":"haiku","subagent_type":"explorer"}'],
        ['{"subagent_type":"cv-kit:explorer","model":"opus"}', '{"subagent_type":"cv-kit:engineer","model":"haiku"}'],
    ),
    "engineer-on-sonnet": (
        ['{"description":"x","subagent_type":"cv-kit:engineer","model":"sonnet","effort":"high","prompt":"p"}',
         '{"model":"sonnet","subagent_type":"engineer","prompt":"p"}'],
        ['{"subagent_type":"cv-kit:engineer","model":"opus"}', '{"subagent_type":"cv-kit:explorer","model":"sonnet"}',
         '{"subagent_type":"cv-kit:engineer","prompt":"use sonnet"}'],
    ),
    "no-opus-agent": (
        ['{"subagent_type":"cv-kit:engineer","model":"opus","prompt":"p"}', '{"model": "opus","subagent_type":"reviewer"}'],
        ['{"subagent_type":"cv-kit:engineer","model":"sonnet","prompt":"opus is not needed"}',
         '{"subagent_type":"cv-kit:explorer","model":"haiku"}'],
    ),
    "brief-has-fields": (
        ['{"subagent_type":"cv-kit:engineer","model":"sonnet","prompt":"Goal: g\\nDone when: d\\nFacts: f\\nFiles: a.py'
         '\\nConstraints: c\\nRuled out: none\\nMode: fix"}',
         '{"prompt":"Goal: g\\nDone when: d\\nFiles: a.py\\nMode: diagnose","subagent_type":"engineer"}'],
        ['{"subagent_type":"cv-kit:engineer","model":"sonnet","prompt":"Fix the box bug in vision/letterbox.py"}',
         '{"subagent_type":"cv-kit:engineer","prompt":"Goal: g\\nFiles: a.py\\nMode: fix"}',
         '{"subagent_type":"cv-kit:explorer","prompt":"Goal: g\\nDone when: d\\nFiles: a.py\\nMode: fix"}'],
    ),
    "reviewer-dispatched": (
        ['{"description":"x","subagent_type":"cv-kit:reviewer","model":"sonnet","prompt":"p"}',
         '{"model":"opus","subagent_type":"reviewer"}'],
        ['{"subagent_type":"cv-kit:engineer","prompt":"then call the reviewer"}', '{"subagent_type":"code-reviewer"}'],
    ),
}


@pytest.mark.parametrize("name", sorted(AGENT_SAMPLES))
def test_agent_routing_graders_match_only_the_right_call(name):
    path = next(p for p in GRADERS if p.stem == name)
    front, _ = split(path)
    assert front["type"] == "tool_used" and front["tool"] == "Agent"
    hits, misses = AGENT_SAMPLES[name]
    for sample in hits:
        assert re.search(front["input_match"], sample), sample
    for sample in misses:
        assert not re.search(front["input_match"], sample), sample


FIXTURE_CASES = sorted(p for p in CASES if (p / "fixture.sh").exists())
# Cases whose prompt names a file on purpose: the run starts in an empty folder and the reply must say it is missing.
EMPTY_ON_PURPOSE = {"14-figure-fire-detector-docs"}
# Cases whose prompt mentions a path only as part of what the user describes; nothing has to read it.
PATH_ONLY_DESCRIBED: set[str] = set()
PATH_IN_PROMPT = re.compile(r"(?<![\w/.])((?:[\w.-]+/)+[\w.-]+\.(?:py|cc|cpp|h|hpp|yaml|yml|txt|toml))\b")


def test_fixture_cases_have_a_case_yaml_that_names_the_script():
    for case in FIXTURE_CASES:
        data = yaml.safe_load((case / "case.yaml").read_text(encoding="utf-8"))
        assert data["schema_version"] == "1.1" and data["name"] == case.name, case.name
        assert data["context"]["scaffold_script"] == "fixture.sh", case.name
    for case in CASES:
        has_yaml = (case / "case.yaml").exists()
        assert has_yaml == (case / "fixture.sh").exists(), f"{case.name}: case.yaml and fixture.sh go together"


@pytest.mark.parametrize("case", CASES, ids=lambda p: p.name)
def test_every_file_the_prompt_names_exists_after_the_fixture(case, tmp_path):
    _, body = split(case / "prompt.md")
    named = sorted(set(PATH_IN_PROMPT.findall(body)))
    if case.name in EMPTY_ON_PURPOSE:
        assert not (case / "fixture.sh").exists(), "an empty-on-purpose case must not seed files"
        return
    if not named or case.name in PATH_ONLY_DESCRIBED:
        return
    assert (case / "fixture.sh").exists(), f"{case.name}: the prompt names {named} but nothing creates them"
    done = subprocess.run(["bash", str(case / "fixture.sh")], cwd=tmp_path, capture_output=True, text=True,
                          check=False)
    assert done.returncode == 0, done.stderr
    missing = [p for p in named if not (tmp_path / p).exists()]
    assert not missing, f"{case.name}: the fixture does not create {missing}"


def test_run_script_grants_what_the_skills_need():
    script = (ROOT / "scripts" / "run_evals.sh").read_text(encoding="utf-8")
    assert "--scaffold" in script and "--allow-tools" in script
    for skill in ROOT.glob("skills/*/SKILL.md"):
        front, body = split(skill)
        for token in re.findall(r"Bash\(python3 \$\{CLAUDE_PLUGIN_ROOT\}/([\w/.]+) \*\)", str(front.get("allowed-tools", ""))):
            assert f"$root/{token} *" in script, f"{skill.parent.name} allows {token}; run_evals.sh does not grant it"


def test_run_script_keeps_the_run_folders_out_of_the_shared_temp_dirs():
    # On Linux the eval sandbox denies writes under /tmp, /var/tmp and /dev/shm. A run folder made there is read-only
    # to every granted shell command, each command exits 1, and the skills' `!` commands fail, so no skill body loads.
    script = (ROOT / "scripts" / "run_evals.sh").read_text(encoding="utf-8")
    assert "export TMPDIR=" in script
    for shared in ("/tmp", "/var/tmp", "/dev/shm"):
        assert f"{shared}|{shared}/*" in script, f"run_evals.sh does not move TMPDIR out of {shared}"


BASH_SAMPLES = {
    "no-install-run": (
        ['{"command":"S=/p/scripts; python3 $S/install_rules.py \\"$PWD\\"; python3 $S/install_configs.py \\"$PWD\\" --lang python"}',
         '{"command":"python3 /p/scripts/install_configs.py . --lang python --force"}'],
        ['{"command":"cat pyproject.toml; ls tests vision"}', '{"command":"python3 /p/scripts/project_facts.py facts ."}',
         '{"command":"ls /p/scripts"}'],
    ),
    "workspace-created": (
        ['{"command":"python3 /p/scripts/research_workspace.py init deimv2-loss-check && ls"}',
         '{"command":"python3 \\"/p/scripts/research_workspace.py\\" init deimv2-loss-check"}',
         '{"command":"python3 /p/scripts/research_workspace.py clone deimv2 https://github.com/a/b --ref main"}',
         # seen on 2026-11-11: the script path goes into a variable first
         '{"command":"S=/p/scripts/research_workspace.py; python3 $S init deimv2-loss-check && python3 $S clone x u"}'],
        ['{"command":"ls research"}', '{"command":"python3 /p/scripts/lint_research.py research/x"}',
         '{"command":"python3 /p/scripts/research_workspace.py --help"}'],
    ),
}


@pytest.mark.parametrize("name", sorted(BASH_SAMPLES))
def test_bash_graders_match_only_the_right_call(name):
    path = next(p for p in GRADERS if p.stem == name)
    front, _ = split(path)
    assert front["type"] == "tool_used" and front["tool"] == "Bash"
    hits, misses = BASH_SAMPLES[name]
    for sample in hits:
        assert re.search(front["input_match"], sample), sample
    for sample in misses:
        assert not re.search(front["input_match"], sample), sample


def test_samples_and_exemptions_name_things_that_exist():
    # A sample set or an exemption that outlives its grader or case checks nothing.
    stems = {p.stem for p in GRADERS}
    for name in [*REGEX_SAMPLES, *AGENT_SAMPLES, *BASH_SAMPLES]:
        assert name in stems, f"samples for {name!r}, but no grader has that name"
    names = {c.name for c in CASES}
    for name in EMPTY_ON_PURPOSE | PATH_ONLY_DESCRIBED:
        assert name in names, f"{name!r} is exempt from the fixture check, but no case has that name"


def test_a_never_called_tool_grader_sets_min_and_max():
    for path in GRADERS:
        front, _ = split(path)
        if front.get("type") == "tool_used" and front.get("max") == 0:
            assert front.get("min") == 0, f"{path}: min defaults to 1, so max 0 alone can never pass"
