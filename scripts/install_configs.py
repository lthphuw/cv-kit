"""Copy cv-kit's strict lint, type-check and build configs into a project."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from install_rules import copy_new

ASSETS = Path(__file__).resolve().parents[1] / "skills" / "setup" / "assets"
FILES = {
    "python": ["ruff.toml", "mypy.ini"],
    "cpp": [".clang-format", ".clang-tidy", "cmake/cv_kit_strict.cmake"],
}
# Another file that already configures the same tool. Copying ours next to it would override it (ruff.toml beats
# [tool.ruff], mypy.ini beats every other mypy file) or be ignored (.ruff.toml beats ruff.toml), so keep it.
OTHER_CONFIGS = {
    "ruff.toml": [(".ruff.toml", None), ("pyproject.toml", r"^\[tool\.ruff[\].]")],
    "mypy.ini": [(".mypy.ini", None), ("pyproject.toml", r"^\[tool\.mypy[\].]"), ("setup.cfg", r"^\[mypy[\]-]")],
    ".clang-format": [("_clang-format", None)],
    ".clang-tidy": [("_clang-tidy", None)],
}


def other_config(project: Path, rel: str) -> str | None:
    """Name the file that already configures the tool `rel` is for, if any."""
    for name, section in OTHER_CONFIGS.get(rel, []):
        path = project / name
        if not path.is_file():
            continue
        if section is None or re.search(section, path.read_text(encoding="utf-8", errors="replace"), re.M):
            return name
    return None


def install(project: Path, langs: list[str], force: bool = False) -> tuple[list[str], list[str], dict[str, str]]:
    """Return the files copied, the files kept because they exist, and the files held back by another config."""
    held: dict[str, str] = {}
    pairs = []
    for lang in langs:
        for rel in FILES[lang]:
            owner = other_config(project, rel)
            if owner is not None:
                held[rel] = owner
            else:
                pairs.append((ASSETS / lang / rel, rel))
    copied, skipped = copy_new(pairs, project, force)
    return copied, skipped, held


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--lang", action="append", choices=sorted(FILES), required=True,
                        help="python or cpp; repeat for both")
    parser.add_argument("--force", action="store_true", help="overwrite files with the same name")
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        print(f"{args.project}: not a directory", file=sys.stderr)
        return 1
    try:
        copied, skipped, held = install(args.project, sorted(set(args.lang)), args.force)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    print(f"copied: {', '.join(copied) or 'none'}")
    print(f"kept existing: {', '.join(skipped) or 'none'}")
    for rel, owner in held.items():
        print(f"not copied: {rel} (the project configures this tool in {owner}; merge by hand)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
