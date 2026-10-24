"""project_facts.py prints live facts for a skill to read; it must never fail and never guess."""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import project_facts as pf  # noqa: E402

ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@example.com", "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"}


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, env={**ENV, "HOME": str(cwd)}, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q", "-b", "main")
    (tmp_path / "a.py").write_text("x = 1\n")
    git(tmp_path, "add", "a.py")
    git(tmp_path, "commit", "-q", "-m", "feat: add a")
    return tmp_path


def facts(path: Path) -> str:
    return "\n".join(pf.collect(path))


class TestGit:
    def test_outside_a_repository(self, tmp_path):
        assert "Git: not a repository" in facts(tmp_path)

    def test_branch_and_clean_tree(self, repo):
        assert "Git: branch main, clean" in facts(repo)

    def test_counts_changed_and_staged_files(self, repo):
        (repo / "a.py").write_text("x = 2\n")
        (repo / "b.py").write_text("y = 1\n")
        git(repo, "add", "b.py")
        text = facts(repo)
        assert "2 changed" in text
        assert "Staged: b.py" in text

    def test_recent_subjects(self, repo):
        assert "feat: add a" in facts(repo)

    def test_shortstat_against_head(self, repo):
        (repo / "a.py").write_text("x = 2\ny = 3\n")
        assert "Diff vs HEAD: 1 file changed" in facts(repo)

    def test_a_long_staged_list_is_capped(self, repo):
        for i in range(40):
            (repo / f"f{i}.py").write_text("")
        git(repo, "add", ".")
        line = next(l for l in pf.collect(repo) if l.startswith("Staged:"))
        assert "and 20 more" in line


class TestProject:
    def test_python_with_pytest(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\naddopts = '-q'\n")
        text = facts(tmp_path)
        assert "Languages: Python" in text
        assert "Python tests: pytest configured" in text

    def test_python_without_a_test_setup_says_so(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n")
        assert "Python tests: no pytest configuration found" in facts(tmp_path)

    def test_conftest_counts_as_pytest(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n")
        (tmp_path / "conftest.py").write_text("")
        assert "Python tests: pytest configured" in facts(tmp_path)

    def test_cpp_with_googletest_and_ctest(self, tmp_path):
        (tmp_path / "CMakeLists.txt").write_text("enable_testing()\nFetchContent_Declare(googletest URL x)\n")
        text = facts(tmp_path)
        assert "Languages: C++" in text
        assert "C++ tests: GoogleTest referenced, ctest enabled" in text

    def test_cpp_without_tests_says_so(self, tmp_path):
        (tmp_path / "CMakeLists.txt").write_text("project(x)\n")
        assert "C++ tests: no GoogleTest or ctest found" in facts(tmp_path)

    def test_nothing_detected_is_stated_not_guessed(self, tmp_path):
        assert "Languages: none detected" in facts(tmp_path)

    def test_rules_installed_or_not(self, tmp_path):
        assert "Project rules: not installed" in facts(tmp_path)
        (tmp_path / ".claude" / "rules").mkdir(parents=True)
        (tmp_path / ".claude" / "rules" / "principles.md").write_text("x")
        assert "Project rules: 1 file in .claude/rules" in facts(tmp_path)


class TestCommandLine:
    def run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(ROOT / "scripts/project_facts.py"), *args], capture_output=True,
                              text=True, check=False)

    def test_prints_facts_and_exits_zero(self, repo):
        result = self.run("facts", str(repo))
        assert result.returncode == 0
        assert "Git: branch main" in result.stdout

    @pytest.mark.parametrize("args", [[], ["facts"], ["facts", "/no/such/dir"], ["nonsense"]])
    def test_never_fails_a_skill(self, args):
        result = self.run(*args)
        assert result.returncode == 0
        assert result.stderr == ""
