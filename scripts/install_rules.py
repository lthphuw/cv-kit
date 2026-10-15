"""Copy cv-kit's rule files into a project's .claude/rules directory."""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

RULES_DIR = Path(__file__).resolve().parents[1] / "rules"


def install(rules_dir: Path, project: Path, force: bool = False) -> tuple[list[str], list[str]]:
    target = project / ".claude" / "rules"
    for link in (project / ".claude", target):
        if link.is_symlink():
            raise ValueError(f"{link}: refusing to write through a symlink")
    # Backstop for links that is_symlink() does not report.
    if not target.resolve().is_relative_to(project.resolve()):
        raise ValueError(f"{target}: refusing to write through a symlink")
    target.mkdir(parents=True, exist_ok=True)
    copied, skipped = [], []
    for source in sorted(rules_dir.glob("*.md")):
        destination = target / source.name
        # is_symlink() also catches dangling links, which exists() reports as absent.
        if destination.is_symlink() or destination.is_dir() or (destination.exists() and not force):
            skipped.append(source.name)
            continue
        shutil.copyfile(source, destination)
        copied.append(source.name)
    return copied, skipped


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
