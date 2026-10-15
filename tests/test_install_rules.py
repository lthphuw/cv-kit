from pathlib import Path

import pytest

from install_rules import install, main


def make_rules(tmp_path: Path) -> Path:
    rules = tmp_path / "rules"
    rules.mkdir()
    (rules / "a.md").write_text("rule a\n", encoding="utf-8")
    (rules / "b.md").write_text("rule b\n", encoding="utf-8")
    return rules


def test_copies_rules_into_claude_rules(tmp_path):
    project = tmp_path / "proj"
    project.mkdir()
    copied, skipped = install(make_rules(tmp_path), project)
    assert (copied, skipped) == (["a.md", "b.md"], [])
    assert (project / ".claude/rules/a.md").read_text(encoding="utf-8") == "rule a\n"


def test_existing_file_is_kept_without_force(tmp_path):
    project = tmp_path / "proj"
    (project / ".claude/rules").mkdir(parents=True)
    (project / ".claude/rules/a.md").write_text("mine\n", encoding="utf-8")
    copied, skipped = install(make_rules(tmp_path), project)
    assert (copied, skipped) == (["b.md"], ["a.md"])
    assert (project / ".claude/rules/a.md").read_text(encoding="utf-8") == "mine\n"


def test_force_overwrites(tmp_path):
    project = tmp_path / "proj"
    (project / ".claude/rules").mkdir(parents=True)
    (project / ".claude/rules/a.md").write_text("mine\n", encoding="utf-8")
    copied, skipped = install(make_rules(tmp_path), project, force=True)
    assert skipped == []
    assert (project / ".claude/rules/a.md").read_text(encoding="utf-8") == "rule a\n"


def test_missing_project_is_an_error(tmp_path, capsys):
    assert main([str(tmp_path / "nope")]) == 1
    assert "not a directory" in capsys.readouterr().err


@pytest.mark.parametrize("force", [False, True])
def test_dangling_symlink_destination_is_skipped_not_followed(tmp_path, force):
    project = tmp_path / "proj"
    (project / ".claude/rules").mkdir(parents=True)
    outside = tmp_path / "outside.md"
    (project / ".claude/rules/a.md").symlink_to(outside)
    copied, skipped = install(make_rules(tmp_path), project, force=force)
    assert not outside.exists()
    assert (copied, skipped) == (["b.md"], ["a.md"])


def test_live_symlink_destination_is_not_overwritten_with_force(tmp_path):
    project = tmp_path / "proj"
    (project / ".claude/rules").mkdir(parents=True)
    outside = tmp_path / "outside.md"
    outside.write_text("keep me\n", encoding="utf-8")
    (project / ".claude/rules/a.md").symlink_to(outside)
    copied, skipped = install(make_rules(tmp_path), project, force=True)
    assert outside.read_text(encoding="utf-8") == "keep me\n"
    assert (copied, skipped) == (["b.md"], ["a.md"])


@pytest.mark.parametrize("link", [".claude", ".claude/rules"])
def test_symlinked_rules_path_is_refused_and_writes_nothing_outside(tmp_path, link):
    project = tmp_path / "proj"
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (project / link).parent.mkdir(parents=True)
    (project / link).symlink_to(elsewhere, target_is_directory=True)
    with pytest.raises(ValueError, match="refusing to write through a symlink"):
        install(make_rules(tmp_path), project)
    assert list(elsewhere.iterdir()) == []


def test_symlinked_rules_directory_inside_project_is_refused(tmp_path):
    project = tmp_path / "proj"
    docs = project / "docs"
    docs.mkdir(parents=True)
    (project / ".claude").mkdir()
    (project / ".claude/rules").symlink_to(docs, target_is_directory=True)
    with pytest.raises(ValueError, match="refusing to write through a symlink"):
        install(make_rules(tmp_path), project)
    assert list(docs.iterdir()) == []


def test_target_resolving_outside_project_is_refused_when_no_link_is_reported(tmp_path, monkeypatch):
    # Simulates a link that is_symlink() does not report (for example a Windows junction).
    monkeypatch.setattr(Path, "is_symlink", lambda self: False)
    project = tmp_path / "proj"
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    project.mkdir()
    (project / ".claude").symlink_to(elsewhere, target_is_directory=True)
    with pytest.raises(ValueError, match="refusing to write through a symlink"):
        install(make_rules(tmp_path), project)
    assert list(elsewhere.iterdir()) == []


def test_symlinked_rules_directory_makes_main_exit_one(tmp_path, capsys):
    project = tmp_path / "proj"
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (project / ".claude").mkdir(parents=True)
    (project / ".claude/rules").symlink_to(elsewhere, target_is_directory=True)
    assert main([str(project)]) == 1
    assert "refusing to write through a symlink" in capsys.readouterr().err
    assert list(elsewhere.iterdir()) == []


def test_directory_at_destination_is_skipped_with_force(tmp_path):
    project = tmp_path / "proj"
    (project / ".claude/rules/a.md").mkdir(parents=True)
    copied, skipped = install(make_rules(tmp_path), project, force=True)
    assert (copied, skipped) == (["b.md"], ["a.md"])
    assert (project / ".claude/rules/a.md").is_dir()
