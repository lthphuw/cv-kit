"""Turn on cv-kit's status line in a Claude Code settings file, keeping the status line already there.

    macOS, Linux, Git Bash:  python3 "$(cat ~/.cache/cv-kit/agent-rows-root)/scripts/install_statusline.py"
    Windows PowerShell:      python "$(Get-Content ~/.cache/cv-kit/agent-rows-root)/scripts/install_statusline.py"

    options: [--settings PATH] [--refresh SECONDS] [--ascii | --no-ascii] [--main | --no-main] [--uninstall]

A plugin cannot set `statusLine`, so this writes it for the user (default `~/.claude/settings.json`). It copies
hooks/statusline_launcher.py to `~/.claude/cv-kit/statusline.py` and sets the command to `<python> <launcher>
<config>`, quoted for the shell Claude Code runs it in: sh on macOS and Linux, Git Bash on Windows, PowerShell when
Git Bash is missing. Each settings file has its own config, `statusline-<id>.json`; a status line already there goes
into it, with that shell, and the launcher runs it first. Before cv-kit first writes the settings file it backs it
up to `<file>.bak-cv-kit`; a second run changes nothing; a file that is not a JSON object is refused. The 0.10 shell
forms are migrated. `--uninstall` puts the old line back.
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER_SOURCE = ROOT / "hooks" / "statusline_launcher.py"
HOME = Path.home()
# The 0.10 status line: a shell command that only sh and Git Bash understood.
LEGACY_ROWS = ('python3 "$(cat "$HOME/.cache/cv-kit/agent-rows-root" 2>/dev/null)/hooks/agent_rows.py" '
               '2>/dev/null || true')
LEGACY_PREFIX = "in=$(cat); printf '%s' \"$in\" | { "
LEGACY_MIDDLES = ("\n}; printf '%s' \"$in\" | ", "; }; printf '%s' \"$in\" | ")
POWERSHELL_SPECIAL = set(" '\"$`(){};&@#,|<>")


def backup_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.bak-cv-kit")


def read(path: Path) -> dict:
    """The JSON object in `path`; {} for a missing file. Raises ValueError for anything else."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError(f"{path}: not valid JSON ({error})") from error
    if not isinstance(data, dict):
        raise ValueError(f"{path}: not a JSON object")
    return data


def write(path: Path, data: dict) -> None:
    path = path.resolve()  # write through a symlink (dotfile managers), not over it
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    part.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if path.exists():
        shutil.copymode(path, part)
    os.replace(part, path)


def legacy_own(command: str) -> tuple[bool, str | None]:
    """(is it a 0.10 cv-kit line, the user's own command inside it)."""
    if command == LEGACY_ROWS:
        return True, None
    for middle in LEGACY_MIDDLES:
        if command.startswith(LEGACY_PREFIX) and command.endswith(middle + LEGACY_ROWS):
            return True, command[len(LEGACY_PREFIX):-len(middle + LEGACY_ROWS)]
    return False, None


def is_ours(command: str) -> bool:
    return "cv-kit/statusline.py" in command.replace("\\", "/")


def git_bash(env) -> str | None:
    """Git Bash the way Claude Code finds it on Windows; never WSL's bash.exe."""
    custom = env.get("CLAUDE_CODE_GIT_BASH_PATH")
    if custom and Path(custom).name.lower() in ("bash.exe", "sh.exe", "bash", "sh") and Path(custom).is_file():
        return str(custom)
    roots = []
    git = shutil.which("git")
    if git:
        here = Path(git).resolve()
        roots += [here.parents[1], here.parents[2]] if len(here.parents) > 2 else [here.parents[1]]
    for key in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)"):
        if env.get(key):
            roots.append(Path(env[key]) / "Git")
    if env.get("LOCALAPPDATA"):
        roots.append(Path(env["LOCALAPPDATA"]) / "Programs" / "Git")
    for root in roots:
        for candidate in (root / "bin" / "bash.exe", root / "usr" / "bin" / "bash.exe"):
            if candidate.is_file():
                return str(candidate)
    return None


def status_shell(system: str, env) -> list[str]:
    """The argv prefix Claude Code uses for a status line command on `system`."""
    if system != "Windows":
        return ["/bin/sh", "-c"]
    bash = git_bash(env)
    return [bash, "-c"] if bash else ["powershell.exe", "-NoProfile", "-Command"]


@functools.lru_cache(maxsize=None)
def python3_works(python: str | None = None) -> bool:
    if not python:
        return False
    try:  # the Microsoft Store stub exists on PATH but only prints a hint
        result = subprocess.run([python, "-c", "import sys; print(sys.version_info[0])"], capture_output=True,
                                timeout=20)
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0 and result.stdout.strip() == b"3"


def pick_python(works=python3_works) -> str:
    """`python3` from PATH when it runs (it survives Python upgrades), else the interpreter running this script."""
    found = shutil.which("python3")
    return found if found and works(found) else sys.executable


def command_line(parts: list[str], system: str, shell: list[str]) -> str:
    if system == "Windows":  # Git Bash eats backslashes; PowerShell accepts forward slashes too
        parts = [p.replace("\\", "/") for p in parts]
        if shell[0].startswith("powershell"):
            if not any(set(p) & POWERSHELL_SPECIAL for p in parts):
                return " ".join(parts)
            return "& " + " ".join("'" + p.replace("'", "''") + "'" for p in parts)
    return " ".join(shlex.quote(p) for p in parts)


def config_path(settings: Path, home: Path) -> Path:
    """One config per settings file, so the user and a project can each keep their own line."""
    key = os.path.normcase(str(settings.resolve()))
    return home / ".claude" / "cv-kit" / f"statusline-{hashlib.sha256(key.encode('utf-8')).hexdigest()[:12]}.json"


def write_atomic(path: Path, data: bytes) -> None:
    """The status line runs every second, so it must never read a half-written file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    part.write_bytes(data)
    os.replace(part, path)


def saved_config(cfg: Path, settings: Path) -> dict:
    """This settings file's config. When it is gone (a synced settings file, a copied project), the line in the
    backup taken before cv-kit first wrote the file stands in, so the user's own line is never dropped."""
    try:
        if cfg.is_file():
            return read(cfg)
        line = read(backup_path(settings)).get("statusLine")
    except ValueError:
        return {}
    if not isinstance(line, dict) or not isinstance(line.get("command"), str) or is_ours(line["command"]):
        return {}
    legacy, inner = legacy_own(line["command"])
    if legacy:
        before = {**{k: v for k, v in line.items() if k != "refreshInterval"}, "command": inner} if inner else None
        return {"own": inner, "before": before}
    return {"own": line["command"], "before": line}


def refresh_of(line: dict | None) -> int | None:
    value = (line or {}).get("refreshInterval")
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else None


def install(path: Path, refresh: int | None = None, ascii: bool | None = None, main: bool | None = None,
            home: Path | None = None, system: str | None = None, python: str | None = None, env=None,
            write_files: bool = True) -> str:
    """Write the status line into `path`.

    None for `refresh`, `ascii` or `main` means no choice was made: a re-run keeps what is set, a new install uses
    1 second, Unicode and the main row. A wrapped line is set to 1 second unless `refresh` says otherwise, since the
    rows' clocks need it; README says to pass `--refresh` for a slow command."""
    home, system = home or HOME, system or platform.system()
    env = os.environ if env is None else env
    data = read(path)
    folder, cfg = home / ".claude" / "cv-kit", config_path(path, home)
    line = data.get("statusLine")
    if line is not None and (not isinstance(line, dict) or line.get("type") != "command"
                             or not isinstance(line.get("command"), str)):
        raise ValueError(f"{path}: statusLine is not a command; set it up by hand (hooks/README.md)")
    shell = status_shell(system, env)  # found again each run: Git Bash may have come or gone
    if line is None:
        own, before, base, result = None, None, {}, "added"
    elif is_ours(line["command"]):
        old = saved_config(cfg, path)
        own, before, base, result = old.get("own"), old.get("before"), line, "updated"  # keep edits made since
        ascii = old.get("ascii", False) if ascii is None else ascii
        main = old.get("main", True) if main is None else main
    else:
        legacy, inner = legacy_own(line["command"])
        if legacy:  # 0.10 set refreshInterval itself, so the user's own value is gone
            base = {k: v for k, v in line.items() if k != "refreshInterval"}
            own, result = inner, "migrated"
            before = {**base, "command": inner} if inner else None
        else:
            own, before, base, result = line["command"], line, line, "wrapped"
    seconds = refresh or (refresh_of(base) if result == "updated" else None) or 1
    config = {"own": own, "shell": shell, "ascii": bool(ascii), "main": main is not False, "before": before}
    launcher = folder / "statusline.py"
    command = command_line([python or pick_python(), str(launcher), str(cfg)], system, shell)
    new_line = {**{k: v for k, v in base.items() if k not in ("type", "command", "refreshInterval")},
                "type": "command", "command": command, "refreshInterval": seconds}
    if result == "updated":
        try:
            unchanged = read(cfg) == config and launcher.read_bytes() == LAUNCHER_SOURCE.read_bytes()
        except (OSError, ValueError):
            unchanged = False
        if unchanged and line == new_line:
            return "already set"
    if write_files:
        write_atomic(launcher, LAUNCHER_SOURCE.read_bytes())
        write_atomic(cfg, (json.dumps(config, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    if line != new_line or not path.exists():
        if path.exists() and result != "updated":  # keep the backup from before cv-kit wrote the file
            shutil.copy2(path, backup_path(path))
        write(path, {**data, "statusLine": new_line})
    return result


def uninstall(path: Path, home: Path | None = None) -> str:
    home = home or HOME
    data = read(path)
    line = data.get("statusLine")
    command = line.get("command") if isinstance(line, dict) else None
    if not isinstance(command, str):
        return "not set"
    folder, cfg = home / ".claude" / "cv-kit", config_path(path, home)
    if is_ours(command):
        before = saved_config(cfg, path).get("before")
    else:
        legacy, inner = legacy_own(command)
        if not legacy:
            return "not set"
        before = {**{k: v for k, v in line.items() if k != "refreshInterval"}, "command": inner} if inner else None
    if isinstance(before, dict):
        data["statusLine"] = before
    else:
        data.pop("statusLine", None)
    write(path, data)
    cfg.unlink(missing_ok=True)
    if not any(folder.glob("statusline-*.json")):  # no other settings file runs the launcher
        shutil.rmtree(folder, ignore_errors=True)
    return "restored" if isinstance(before, dict) else "removed"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--settings", type=Path, help="settings file (default: ~/.claude/settings.json)")
    parser.add_argument("--refresh", type=int, help="seconds between refreshes (default: 1, or what is set)")
    parser.add_argument("--ascii", action=argparse.BooleanOptionalAction,
                        help="draw with ASCII only, for terminals without the glyphs (--no-ascii undoes it)")
    parser.add_argument("--main", action=argparse.BooleanOptionalAction,
                        help="the main session's row (default; --no-main leaves it out)")
    parser.add_argument("--uninstall", action="store_true", help="put the old status line back")
    args = parser.parse_args(argv)
    settings = args.settings or HOME / ".claude" / "settings.json"
    if args.refresh is not None and args.refresh < 1:
        print("--refresh must be 1 or more", file=sys.stderr)
        return 2
    try:
        if args.uninstall:
            result = uninstall(settings, home=HOME)
        else:
            result = install(settings, refresh=args.refresh, ascii=args.ascii, main=args.main, home=HOME)
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"{result}: {settings}")
    if not args.uninstall and not python3_works(shutil.which("python3")):
        print("warning: `python3` does not run here, and cv-kit's hooks need it, so no agent rows will appear. On "
              "Windows, install Python from the Microsoft Store, or copy python.exe to python3.exe in the same folder.",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
