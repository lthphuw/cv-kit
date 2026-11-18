"""Add cv-kit's agent rows to the statusLine in a Claude Code settings file, keeping the line already there.

    python3 "$(cat ~/.cache/cv-kit/agent-rows-root)/scripts/install_statusline.py" [--settings PATH] [--refresh N]
    python3 "$(cat ~/.cache/cv-kit/agent-rows-root)/scripts/install_statusline.py" --uninstall

A plugin cannot set `statusLine`, so this writes it for the user (default `~/.claude/settings.json`). With no status
line it adds the rows command. With one, it runs that command first on the same input and the rows after it, so the
user's line still prints when cv-kit is gone. It backs the file up to `<file>.bak-cv-kit` before writing, changes
nothing when the rows are already there, and refuses a file that is not a JSON object. `--uninstall` puts the old line
back. hooks/README.md explains the rows.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROWS = 'python3 "$(cat "$HOME/.cache/cv-kit/agent-rows-root" 2>/dev/null)/hooks/agent_rows.py" 2>/dev/null || true'
PREFIX = "in=$(cat); printf '%s' \"$in\" | { "
MIDDLE = "; }; printf '%s' \"$in\" | "
DEFAULT = Path.home() / ".claude" / "settings.json"


def backup_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.bak-cv-kit")


def read(path: Path) -> dict:
    """The settings as a dict; {} for a missing file. Raises ValueError for anything else."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: not a JSON object")
    return data


def write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    part.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(part, path)


def own_command(command: str) -> str | None:
    """The user's command inside a wrapped one, or None when `command` is not wrapped."""
    if command.startswith(PREFIX) and command.endswith(MIDDLE + ROWS):
        return command[len(PREFIX):-len(MIDDLE + ROWS)]
    return None


def install(path: Path, refresh: int = 1) -> str:
    try:
        data = read(path)
    except json.JSONDecodeError as error:
        raise ValueError(f"{path}: not valid JSON ({error})") from error
    line = data.get("statusLine")
    if line is None:
        data["statusLine"] = {"type": "command", "command": ROWS, "refreshInterval": refresh}
        result = "added"
    elif not isinstance(line, dict) or line.get("type") != "command" or not isinstance(line.get("command"), str):
        raise ValueError(f"{path}: statusLine is not a command; add the rows by hand (hooks/README.md)")
    elif "agent_rows.py" in line["command"]:
        return "already set"
    else:
        old = line.get("refreshInterval")
        data["statusLine"] = {**line, "command": PREFIX + line["command"] + MIDDLE + ROWS,
                              "refreshInterval": min(old, refresh) if isinstance(old, int) and old > 0 else refresh}
        result = "wrapped"
    if path.exists():
        shutil.copyfile(path, backup_path(path))
    write(path, data)
    return result


def uninstall(path: Path) -> str:
    try:
        data = read(path)
    except json.JSONDecodeError as error:
        raise ValueError(f"{path}: not valid JSON ({error})") from error
    line = data.get("statusLine")
    command = line.get("command") if isinstance(line, dict) else None
    if not isinstance(command, str):
        return "not set"
    if command == ROWS:
        del data["statusLine"]
        write(path, data)
        return "removed"
    own = own_command(command)
    if own is None:
        return "not set"
    try:
        saved = read(backup_path(path)).get("statusLine")
    except (OSError, ValueError):
        saved = None
    if isinstance(saved, dict) and saved.get("command") == own:
        data["statusLine"] = saved
    else:  # no backup of that line: keep its other fields, drop the refresh this script set
        data["statusLine"] = {key: value for key, value in line.items() if key != "refreshInterval"} | {"command": own}
    write(path, data)
    return "restored"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--settings", type=Path, default=DEFAULT, help="settings file (default: %(default)s)")
    parser.add_argument("--refresh", type=int, default=1, help="seconds between refreshes (default: 1)")
    parser.add_argument("--uninstall", action="store_true", help="put the old status line back")
    args = parser.parse_args(argv)
    if args.refresh < 1:
        print("--refresh must be 1 or more", file=sys.stderr)
        return 2
    try:
        result = uninstall(args.settings) if args.uninstall else install(args.settings, args.refresh)
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"{result}: {args.settings}")
    if result in ("added", "wrapped"):
        print(f"backup: {backup_path(args.settings)}" if backup_path(args.settings).exists() else "no backup: new file")
    return 0


if __name__ == "__main__":
    sys.exit(main())
