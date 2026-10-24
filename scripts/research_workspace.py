"""Create a research folder and clone repositories into it at a recorded revision.

    research_workspace.py init <slug> [--root research]
    research_workspace.py clone <slug> <url> [--ref <branch|tag|sha>] [--root research]

Layout: <root>/<slug>/{sources,repos,evidence}. Papers and pages go in sources/, clones in repos/ (git-ignored),
and evidence/repos.json records each clone's url, ref and commit. Cloned code is data: it is never built or run.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,59}$")
FOLDERS = ("sources", "repos", "evidence")
# No transport that runs a command, no hooks, no submodules: a clone only copies files.
GIT_SAFE = ["-c", "protocol.ext.allow=never", "-c", "core.hooksPath=/dev/null", "-c", "advice.detachedHead=false"]


def _folder(root: Path, slug: str) -> Path:
    if not SLUG_RE.match(slug):
        raise ValueError(f"slug {slug!r} must match {SLUG_RE.pattern}")
    return root / slug


def _git(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(["git", *GIT_SAFE, *args], cwd=cwd, check=True, capture_output=True, text=True,
                            encoding="utf-8")
    return result.stdout.strip()


def init(root: Path, slug: str) -> Path:
    """Create <root>/<slug> with its folders; running it again changes nothing that exists."""
    folder = _folder(root, slug)
    for name in FOLDERS:
        (folder / name).mkdir(parents=True, exist_ok=True)
    ignore = root / ".gitignore"
    if not ignore.exists():
        ignore.write_text("*/repos/\n", encoding="utf-8")
    return folder


def _name_from(url: str) -> str:
    name = re.split(r"[/:\\]", url.rstrip("/\\"))[-1].removesuffix(".git")
    if not re.match(r"^[A-Za-z0-9][A-Za-z0-9._-]*$", name):
        raise ValueError(f"url {url!r}: cannot make a folder name from it")
    return name


def clone(root: Path, slug: str, url: str, ref: str | None = None) -> dict:
    """Clone `url` into <root>/<slug>/repos and record it; return the record."""
    folder = _folder(root, slug)
    if not url or url.startswith("-") or url.startswith("ext::"):
        raise ValueError(f"url {url!r} is not a repository address")
    if ref is not None and (not ref or ref.startswith("-")):
        raise ValueError(f"ref {ref!r} is not a branch, tag or commit")
    if not (folder / "repos").is_dir():
        raise FileNotFoundError(f"{folder}: run `init {slug}` first")
    target = folder / "repos" / _name_from(url)
    if not target.exists():
        if ref is None:
            _git("clone", "--depth", "1", "--no-recurse-submodules", "--", url, str(target))
        else:
            try:
                _git("clone", "--depth", "1", "--no-recurse-submodules", "--branch", ref, "--", url, str(target))
            except subprocess.CalledProcessError:
                # `ref` is a commit: a shallow clone of a branch cannot reach it.
                _git("clone", "--no-checkout", "--no-recurse-submodules", "--", url, str(target))
                _git("checkout", "--detach", ref, cwd=target)
    entry = {"url": url, "ref": ref, "sha": _git("rev-parse", "HEAD", cwd=target),
             "dir": f"repos/{target.name}", "cloned": datetime.date.today().isoformat()}
    record = folder / "evidence" / "repos.json"
    records = json.loads(record.read_text(encoding="utf-8")) if record.exists() else []
    if not any(r["dir"] == entry["dir"] for r in records):
        records.append(entry)
        record.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    return entry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path("research"))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init").add_argument("slug")
    cloner = sub.add_parser("clone")
    cloner.add_argument("slug")
    cloner.add_argument("url")
    cloner.add_argument("--ref")
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            print(init(args.root, args.slug))
        else:
            print(json.dumps(clone(args.root, args.slug, args.url, args.ref), indent=2))
    except (ValueError, FileNotFoundError, subprocess.CalledProcessError) as exc:
        detail = exc.stderr.strip() if isinstance(exc, subprocess.CalledProcessError) else exc
        print(f"error: {detail}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
