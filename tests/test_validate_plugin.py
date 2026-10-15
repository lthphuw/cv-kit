import json
from pathlib import Path

import pytest

from validate_plugin import run_checks

SKILL = "---\nname: demo\ndescription: Use when testing the validator.\n---\n# Demo\n"
CATALOG_HEADER = (
    "| Model | Task | Paper (arXiv) | Repo / HF id | Licence | Typical use | Gotcha | Status |\n"
    "|---|---|---|---|---|---|---|---|\n"
)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def plugin(tmp_path: Path) -> Path:
    write(tmp_path / ".claude-plugin/plugin.json", json.dumps({"name": "cv-kit", "version": "0.1.0"}))
    market = {"name": "cv-kit", "owner": {"name": "x"}, "plugins": [{"name": "cv-kit", "source": "./"}]}
    write(tmp_path / ".claude-plugin/marketplace.json", json.dumps(market))
    write(tmp_path / "skills/demo/SKILL.md", SKILL)
    return tmp_path


def test_valid_plugin_has_no_errors(plugin):
    assert run_checks(plugin) == []


def test_skill_name_must_equal_directory(plugin):
    write(plugin / "skills/demo/SKILL.md", SKILL.replace("name: demo", "name: other"))
    assert any("name 'other'" in e for e in run_checks(plugin))


def test_description_must_start_with_use_when(plugin):
    write(plugin / "skills/demo/SKILL.md", SKILL.replace("Use when testing", "Tests"))
    assert any("Use when" in e for e in run_checks(plugin))


def test_description_over_1024_characters_fails(plugin):
    long_desc = "Use when " + "x" * 1100
    write(plugin / "skills/demo/SKILL.md", f"---\nname: demo\ndescription: {long_desc}\n---\n")
    assert any("1024" in e for e in run_checks(plugin))


def test_unknown_frontmatter_key_fails(plugin):
    write(plugin / "skills/demo/SKILL.md", SKILL.replace("---\n# Demo", "bogus: 1\n---\n# Demo"))
    assert any("bogus" in e for e in run_checks(plugin))


def test_malformed_frontmatter_is_reported_not_raised(plugin):
    write(plugin / "skills/demo/SKILL.md", "no frontmatter here\n")
    errors = run_checks(plugin)
    assert any("SKILL.md" in e and "frontmatter" in e for e in errors)


def test_skill_directory_without_skill_md_fails(plugin):
    (plugin / "skills/empty").mkdir()
    assert any("skills/empty" in e for e in run_checks(plugin))


def test_broken_relative_link_fails(plugin):
    write(plugin / "skills/demo/SKILL.md", SKILL + "\nSee [ref](references/missing.md).\n")
    assert any("missing.md" in e for e in run_checks(plugin))


def test_skill_dir_reference_must_resolve(plugin):
    write(plugin / "shared/catalog.md", "x\n")
    ok = SKILL + "\nRead `${CLAUDE_SKILL_DIR}/../../shared/catalog.md`.\n"
    write(plugin / "skills/demo/SKILL.md", ok)
    assert run_checks(plugin) == []
    write(plugin / "skills/demo/SKILL.md", ok.replace("catalog.md", "nope.md"))
    assert any("nope.md" in e for e in run_checks(plugin))


def test_agent_with_ignored_key_fails(plugin):
    write(plugin / "agents/a.md", "---\nname: a\ndescription: d\npermissionMode: acceptEdits\n---\nbody\n")
    assert any("permissionMode" in e for e in run_checks(plugin))


def test_agent_skills_must_exist(plugin):
    write(plugin / "agents/a.md", "---\nname: a\ndescription: d\nskills:\n  - ghost\n---\nbody\n")
    assert any("ghost" in e for e in run_checks(plugin))


def test_version_in_marketplace_entry_fails(plugin):
    market = {"name": "cv-kit", "owner": {"name": "x"}, "plugins": [{"name": "cv-kit", "source": "./", "version": "1"}]}
    write(plugin / ".claude-plugin/marketplace.json", json.dumps(market))
    assert any("version" in e for e in run_checks(plugin))


def test_hook_command_path_must_exist(plugin):
    hooks = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
        {"type": "command", "command": "python3", "args": ["${CLAUDE_PLUGIN_ROOT}/hooks/missing.py"]}]}]}}
    write(plugin / "hooks/hooks.json", json.dumps(hooks))
    assert any("missing.py" in e for e in run_checks(plugin))


def test_hooks_json_needs_top_level_hooks_key(plugin):
    write(plugin / "hooks/hooks.json", json.dumps({"PreToolUse": []}))
    assert any("top-level" in e for e in run_checks(plugin))


def test_catalog_verified_row_needs_valid_arxiv(plugin):
    write(plugin / "shared/catalog.md", CATALOG_HEADER + "| M | t | not-an-id | r | MIT | u | g | verified |\n")
    assert any("arXiv" in e for e in run_checks(plugin))


def test_catalog_unverified_row_may_have_free_text_paper(plugin):
    write(plugin / "shared/catalog.md", CATALOG_HEADER + "| M | t | unknown | r | MIT | u | g | UNVERIFIED |\n")
    assert run_checks(plugin) == []


def test_catalog_status_must_be_known(plugin):
    write(plugin / "shared/catalog.md", CATALOG_HEADER + "| M | t | 2103.00020 | r | MIT | u | g | maybe |\n")
    assert any("Status" in e for e in run_checks(plugin))


def test_local_path_leak_fails(plugin):
    write(plugin / "skills/demo/SKILL.md", SKILL + "\nOpen /Users/someone/file.\n")
    assert any("local path" in e for e in run_checks(plugin))


def test_rule_file_over_200_lines_fails(plugin):
    write(plugin / "rules/long.md", "line\n" * 201)
    assert any("long.md" in e for e in run_checks(plugin))


def test_empty_plugin_manifest_still_needs_version(plugin):
    write(plugin / ".claude-plugin/plugin.json", "{}")
    assert any("version is required" in e for e in run_checks(plugin))


def test_non_object_plugin_manifest_is_reported_not_raised(plugin):
    write(plugin / ".claude-plugin/plugin.json", "[]")
    assert any("expected a JSON object" in e for e in run_checks(plugin))


def test_non_object_marketplace_entry_is_reported_not_raised(plugin):
    market = {"name": "cv-kit", "owner": {"name": "x"}, "plugins": ["cv-kit"]}
    write(plugin / ".claude-plugin/marketplace.json", json.dumps(market))
    assert any("not a JSON object" in e for e in run_checks(plugin))


def test_marketplace_plugins_must_be_a_list(plugin):
    market = {"name": "cv-kit", "owner": {"name": "x"}, "plugins": 5}
    write(plugin / ".claude-plugin/marketplace.json", json.dumps(market))
    assert any("must be a list" in e for e in run_checks(plugin))


def test_non_object_hook_group_is_reported_not_raised(plugin):
    write(plugin / "hooks/hooks.json", json.dumps({"hooks": {"PreToolUse": ["oops"]}}))
    assert any("not a JSON object" in e for e in run_checks(plugin))


def test_non_object_hook_handler_is_reported_not_raised(plugin):
    write(plugin / "hooks/hooks.json", json.dumps({"hooks": {"PreToolUse": [{"hooks": ["oops"]}]}}))
    assert any("not a JSON object" in e for e in run_checks(plugin))


def test_hooks_value_must_be_object(plugin):
    write(plugin / "hooks/hooks.json", json.dumps({"hooks": []}))
    assert any("must be a JSON object" in e for e in run_checks(plugin))


def test_hook_bare_command_path_must_exist(plugin):
    hooks = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
        {"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/x.sh"}]}]}}
    write(plugin / "hooks/hooks.json", json.dumps(hooks))
    assert any("x.sh" in e for e in run_checks(plugin))


def test_hook_interpreter_command_path_must_exist(plugin):
    hooks = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
        {"type": "command", "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/x.py"}]}]}}
    write(plugin / "hooks/hooks.json", json.dumps(hooks))
    assert any("x.py" in e for e in run_checks(plugin))


def test_hook_interpreter_command_with_existing_file_passes(plugin):
    hooks = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
        {"type": "command", "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/x.py"}]}]}}
    write(plugin / "hooks/x.py", "")
    write(plugin / "hooks/hooks.json", json.dumps(hooks))
    assert run_checks(plugin) == []
