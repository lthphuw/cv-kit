"""Copy cv-kit's rule files into a project's .claude/rules directory."""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

RULES_DIR = Path(__file__).resolve().parents[1] / "rules"


def copy_new(pairs: list[tuple[Path, str]], project: Path, force: bool = False) -> tuple[list[str], list[str]]:
    """Copy each (source, path relative to project) pair, keeping files that already exist.

    Returns the relative paths copied and kept. Raises ValueError, before writing anything, when a directory on
    the way to a destination is a symlink or resolves outside the project.
    """
    root = project.resolve()
    for _, rel in pairs:
        destination = project / rel
        for parent in [p for p in destination.parents if p != project and project in p.parents]:
            if parent.is_symlink():
                raise ValueError(f"{parent}: refusing to write through a symlink")
        # Backstop for links that is_symlink() does not report.
        if not destination.parent.resolve().is_relative_to(root):
            raise ValueError(f"{destination.parent}: refusing to write through a symlink")
    copied, skipped = [], []
    for source, rel in pairs:
        destination = project / rel
        # is_symlink() also catches dangling links, which exists() reports as absent.
        if destination.is_symlink() or destination.is_dir() or (destination.exists() and not force):
            skipped.append(rel)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        copied.append(rel)
    return copied, skipped


def install(rules_dir: Path, project: Path, force: bool = False) -> tuple[list[str], list[str]]:
    pairs = [(source, f".claude/rules/{source.name}") for source in sorted(rules_dir.glob("*.md"))]
    copied, skipped = copy_new(pairs, project, force)
    return [Path(rel).name for rel in copied], [Path(rel).name for rel in skipped]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--force", action="store_true", help="overwrite files that already exist")
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        print(f"{args.project}: not a directory", file=sys.stderr)
        return 1
    try:
        copied, skipped = install(RULES_DIR, args.project, args.force)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    print(f"copied: {', '.join(copied) or 'none'}")
    print(f"kept existing: {', '.join(skipped) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
