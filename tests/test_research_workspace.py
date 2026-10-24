"""The research workspace script: folders for evidence, and repositories cloned at a recorded revision."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import research_workspace as rw  # noqa: E402


def git(cwd: Path, *args: str) -> str:
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@example.com", "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
           "HOME": str(cwd)}
    return subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def upstream(tmp_path: Path) -> tuple[Path, str]:
    """A local repository with two commits; returns its path and the first commit."""
    repo = tmp_path / "upstream" / "demo-model"
    repo.mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main")
    (repo / "README.md").write_text("one\n")
    git(repo, "add", "README.md")
    git(repo, "commit", "-q", "-m", "one")
    first = git(repo, "rev-parse", "HEAD")
    (repo / "README.md").write_text("two\n")
    git(repo, "commit", "-q", "-am", "two")
    return repo, first


class TestInit:
    def test_creates_the_folders(self, tmp_path):
        folder = rw.init(tmp_path / "research", "small-objects")
        assert [p.name for p in sorted(folder.iterdir())] == ["evidence", "repos", "sources"]

    def test_keeps_clones_out_of_version_control(self, tmp_path):
        rw.init(tmp_path / "research", "small-objects")
        assert (tmp_path / "research" / ".gitignore").read_text().splitlines() == ["*/repos/"]

    def test_is_idempotent(self, tmp_path):
        rw.init(tmp_path / "research", "small-objects")
        (tmp_path / "research" / "small-objects" / "evidence" / "keep.txt").write_text("x")
        rw.init(tmp_path / "research", "small-objects")
        assert (tmp_path / "research" / "small-objects" / "evidence" / "keep.txt").exists()

    @pytest.mark.parametrize("slug", ["", "Upper", "a b", "../escape", "a/b", "-lead", "x" * 61])
    def test_rejects_a_bad_slug(self, tmp_path, slug):
        with pytest.raises(ValueError, match="slug"):
            rw.init(tmp_path / "research", slug)


class TestClone:
    def test_clones_and_records_the_revision(self, tmp_path, upstream):
        repo, _ = upstream
        rw.init(tmp_path / "research", "topic")
        entry = rw.clone(tmp_path / "research", "topic", str(repo))
        assert entry["sha"] == git(repo, "rev-parse", "HEAD")
        assert (tmp_path / "research" / "topic" / "repos" / "demo-model" / "README.md").read_text() == "two\n"
        recorded = json.loads((tmp_path / "research" / "topic" / "evidence" / "repos.json").read_text())
        assert [r["sha"] for r in recorded] == [entry["sha"]]

    def test_checks_out_a_commit(self, tmp_path, upstream):
        repo, first = upstream
        rw.init(tmp_path / "research", "topic")
        entry = rw.clone(tmp_path / "research", "topic", str(repo), ref=first)
        assert entry["sha"] == first
        assert (tmp_path / "research" / "topic" / "repos" / "demo-model" / "README.md").read_text() == "one\n"

    def test_a_second_clone_reuses_the_folder(self, tmp_path, upstream):
        repo, _ = upstream
        rw.init(tmp_path / "research", "topic")
        rw.clone(tmp_path / "research", "topic", str(repo))
        rw.clone(tmp_path / "research", "topic", str(repo))
        recorded = json.loads((tmp_path / "research" / "topic" / "evidence" / "repos.json").read_text())
        assert len(recorded) == 1

    def test_never_runs_a_hook_from_the_clone(self, tmp_path, upstream):
        repo, _ = upstream
        marker = tmp_path / "ran"
        hook = repo / ".git" / "hooks" / "post-checkout"
        hook.write_text(f"#!/bin/sh\ntouch {marker}\n")
        hook.chmod(0o755)
        rw.init(tmp_path / "research", "topic")
        rw.clone(tmp_path / "research", "topic", str(repo))
        assert not marker.exists()

    @pytest.mark.parametrize("url", ["--upload-pack=touch x", "ext::sh -c touch% x", ""])
    def test_rejects_a_dangerous_url(self, tmp_path, url):
        rw.init(tmp_path / "research", "topic")
        with pytest.raises(ValueError, match="url"):
            rw.clone(tmp_path / "research", "topic", url)

    def test_needs_an_initialised_workspace(self, tmp_path, upstream):
        repo, _ = upstream
        with pytest.raises(FileNotFoundError):
            rw.clone(tmp_path / "research", "topic", str(repo))
