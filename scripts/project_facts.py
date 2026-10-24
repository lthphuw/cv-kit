"""Print a few facts about the current project for a skill to read; always exits 0.

    project_facts.py facts [dir]

A skill runs this with `!`...`` so Claude starts from the real state (branch, staged files, test setup) instead of
guessing. A fact that cannot be found is reported as not found, never invented.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

MAX_LISTED = 20
PYTEST_FILES = ("pyproject.toml", "pytest.ini", "tox.ini", "setup.cfg", "requirements.txt", "requirements-dev.txt")


def _git(path: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(["git", *args], cwd=path, capture_output=True, text=True, encoding="utf-8",
                                timeout=5, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout if result.returncode == 0 else None


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _capped(items: list[str]) -> str:
    shown = ", ".join(items[:MAX_LISTED])
    return shown + (f" and {len(items) - MAX_LISTED} more" if len(items) > MAX_LISTED else "")


def _git_facts(path: Path) -> list[str]:
    if _git(path, "rev-parse", "--is-inside-work-tree") is None:
        return ["Git: not a repository"]
    branch = (_git(path, "branch", "--show-current") or "").strip() or "detached HEAD"
    changed = [l for l in (_git(path, "status", "--porcelain") or "").splitlines() if l.strip()]
    lines = [f"Git: branch {branch}, " + (f"{len(changed)} changed" if changed else "clean")]
    staged = (_git(path, "diff", "--cached", "--name-only") or "").split()
    if staged:
        lines.append(f"Staged: {_capped(staged)}")
    stat = (_git(path, "diff", "--shortstat", "HEAD") or "").strip()
    if stat:
        lines.append(f"Diff vs HEAD: {stat}")
    subjects = (_git(path, "log", "-5", "--format=%s") or "").splitlines()
    if subjects:
        lines.append("Recent subjects: " + " | ".join(subjects))
    return lines


def _has_files(path: Path, patterns: tuple[str, ...]) -> bool:
    for pattern in patterns:
        if any(True for _ in path.glob(pattern)):
            return True
    return False


def _project_facts(path: Path) -> list[str]:
    python = (path / "pyproject.toml").exists() or (path / "setup.py").exists() or _has_files(path, ("*.py", "*/*.py"))
    cpp = (path / "CMakeLists.txt").exists() or _has_files(path, ("*.cc", "*.cpp", "src/*.cc", "src/*.cpp"))
    languages = [name for name, present in (("Python", python), ("C++", cpp)) if present]
    lines = ["Languages: " + (", ".join(languages) if languages else "none detected")]
    if python:
        pytest = (path / "conftest.py").exists() or (path / "tests" / "conftest.py").exists() or any(
            re.search(r"pytest", _read(path / name)) for name in PYTEST_FILES)
        lines.append("Python tests: pytest configured" if pytest else "Python tests: no pytest configuration found")
    if cpp:
        cmake = "\n".join(_read(p) for p in [path / "CMakeLists.txt", *path.glob("*/CMakeLists.txt")])
        gtest = re.search(r"googletest|GTest|gtest", cmake) is not None
        ctest = re.search(r"enable_testing|include\(CTest\)", cmake) is not None
        parts = [name for name, present in (("GoogleTest referenced", gtest), ("ctest enabled", ctest)) if present]
        lines.append("C++ tests: " + (", ".join(parts) if parts else "no GoogleTest or ctest found"))
    rules = path / ".claude" / "rules"
    count = len(list(rules.glob("*.md"))) if rules.is_dir() else 0
    lines.append(f"Project rules: {count} file{'s' if count != 1 else ''} in .claude/rules" if count
                 else "Project rules: not installed (run /cv-kit:setup)")
    return lines


def collect(path: Path) -> list[str]:
    return _git_facts(path) + _project_facts(path)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args[:1] != ["facts"]:
        return 0
    path = Path(args[1]) if len(args) > 1 else Path.cwd()
    if path.is_dir():
        print("\n".join(collect(path)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
