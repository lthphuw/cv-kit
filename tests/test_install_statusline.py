"""scripts/install_statusline.py and the launcher it installs, on macOS, Linux and Windows."""
import json
import os
import re
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest

import install_statusline as inst
from install_statusline import install, main, uninstall

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "hooks/statusline_launcher.py"
PY = sys.executable
OWN = [PY, "-c"]  # a stand-in shell that works on every OS: runs the own "command" as Python code
SID, PROMPT = "s-1", "p-1"
PAYLOAD = {"session_id": SID, "prompt_id": PROMPT, "model": {"id": "claude-opus-5-5", "display_name": "Opus"},
           "context_window": {"used_percentage": 32, "context_window_size": 200_000}}


def settings(tmp_path: Path, data: dict | None) -> Path:
    path = tmp_path / "settings.json"
    if data is not None:
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def put(path: Path, **kw) -> str:
    kw = {"home": path.parent / "home", "system": "Linux", "python": "/usr/bin/python3", "env": {}, **kw}
    return install(path, **kw)


def config(path: Path, home: Path | None = None) -> dict:
    return load(inst.config_path(path, home or path.parent / "home"))


def env_for(home: Path, **extra) -> dict:
    return {**os.environ, "HOME": str(home), "USERPROFILE": str(home), "NO_COLOR": "1", **extra}


# --- the settings it writes --------------------------------------------------------------------------------------


def test_no_status_line_gets_the_launcher_alone(tmp_path):
    path = settings(tmp_path, {"model": "opus"})
    assert put(path) == "added"
    launcher, cfg = tmp_path / "home/.claude/cv-kit/statusline.py", inst.config_path(path, tmp_path / "home")
    assert cfg.parent == launcher.parent and cfg.name.startswith("statusline-") and cfg.suffix == ".json"
    assert load(path) == {"model": "opus", "statusLine": {"type": "command",
                                                          "command": f"/usr/bin/python3 {launcher} {cfg}",
                                                          "refreshInterval": 1}}
    assert launcher.read_bytes() == LAUNCHER.read_bytes()
    assert config(path) == {"own": None, "shell": ["/bin/sh", "-c"], "ascii": False, "main": True, "before": None}


def test_a_missing_settings_file_is_created(tmp_path):
    path = settings(tmp_path / "new", None)
    assert put(path, home=tmp_path / "home") == "added" and "statusLine" in load(path)


def test_an_existing_status_line_is_kept_with_its_fields(tmp_path):
    before = {"type": "command", "command": "echo 'mine' # note", "padding": 2}
    path = settings(tmp_path, {"statusLine": before})
    assert put(path) == "wrapped"
    line = load(path)["statusLine"]
    assert line["padding"] == 2 and line["refreshInterval"] == 1 and "statusline.py" in line["command"]
    assert config(path)["own"] == "echo 'mine' # note" and config(path)["before"] == before


def test_a_slower_refresh_of_the_users_own_is_lowered_and_a_faster_one_kept(tmp_path):
    slow = settings(tmp_path, {"statusLine": {"type": "command", "command": "x", "refreshInterval": 30}})
    put(slow)
    assert load(slow)["statusLine"]["refreshInterval"] == 1
    (tmp_path / "b").mkdir()
    fast = settings(tmp_path / "b", {"statusLine": {"type": "command", "command": "x"}})
    put(fast, home=tmp_path / "b/home", refresh=5)
    assert load(fast)["statusLine"]["refreshInterval"] == 5


def test_running_it_twice_changes_nothing_and_a_new_choice_updates(tmp_path):
    path = settings(tmp_path, {"statusLine": {"type": "command", "command": "echo mine"}})
    put(path)
    before = path.read_text(encoding="utf-8")
    assert put(path) == "already set" and path.read_text(encoding="utf-8") == before
    assert put(path, refresh=3, ascii=True) == "updated"
    assert load(path)["statusLine"]["refreshInterval"] == 3 and config(path)["ascii"] is True
    assert config(path)["own"] == "echo mine"  # the user's line survives a re-run


def test_a_re_run_keeps_edits_made_after_install(tmp_path):
    path = settings(tmp_path, {"statusLine": {"type": "command", "command": "echo mine"}})
    put(path)
    data = load(path)
    data["statusLine"].update(padding=1, refreshInterval=3)
    path.write_text(json.dumps(data), encoding="utf-8")
    put(path, ascii=True, refresh=None)  # no --refresh given
    assert load(path)["statusLine"]["padding"] == 1 and load(path)["statusLine"]["refreshInterval"] == 3


def test_two_settings_files_keep_their_own_lines(tmp_path):
    (tmp_path / "proj").mkdir()
    user = settings(tmp_path, {"statusLine": {"type": "command", "command": "echo user"}})
    project = settings(tmp_path / "proj", {})
    home = tmp_path / "home"
    put(user, home=home), put(project, home=home)
    assert config(user, home)["own"] == "echo user" and config(project, home)["own"] is None
    assert uninstall(project, home=home) == "removed"
    assert (home / ".claude/cv-kit/statusline.py").is_file()  # the user settings still run it
    assert uninstall(user, home=home) == "restored" and not (home / ".claude/cv-kit").exists()


def test_a_lost_config_falls_back_to_the_backup(tmp_path):
    path = settings(tmp_path, {"statusLine": {"type": "command", "command": "echo mine", "padding": 2}})
    put(path)
    inst.config_path(path, tmp_path / "home").unlink()  # synced settings, but not the config beside the launcher
    assert put(path, refresh=2) == "updated" and config(path)["own"] == "echo mine"
    assert uninstall(path, home=tmp_path / "home") == "restored"
    assert load(path)["statusLine"] == {"type": "command", "command": "echo mine", "padding": 2}


def test_a_re_run_without_flags_keeps_the_earlier_choices(tmp_path):
    path = settings(tmp_path, {})
    put(path, ascii=True, main=False)
    assert put(path) == "already set" and config(path)["ascii"] is True and config(path)["main"] is False
    put(path, ascii=False)
    assert config(path)["ascii"] is False and config(path)["main"] is False


def test_an_explicit_refresh_wins(tmp_path):
    path = settings(tmp_path, {"statusLine": {"type": "command", "command": "x", "refreshInterval": 2}})
    put(path, refresh=5)
    assert load(path)["statusLine"]["refreshInterval"] == 5


def test_a_re_run_finds_the_shell_again(tmp_path, monkeypatch):
    monkeypatch.setattr(inst.shutil, "which", lambda name: None)
    path = settings(tmp_path, {"statusLine": {"type": "command", "command": "echo mine"}})
    win = {"system": "Windows", "python": "C:\\Program Files\\py\\python.exe", "home": tmp_path / "home"}
    put(path, env={}, **win)
    assert load(path)["statusLine"]["command"].startswith("& ")
    bash = tmp_path / "Git/bin/bash.exe"
    bash.parent.mkdir(parents=True), bash.write_text("")
    put(path, env={"CLAUDE_CODE_GIT_BASH_PATH": str(bash)}, **win)  # Git Bash installed since
    assert load(path)["statusLine"]["command"].startswith("'C:/Program Files/py/python.exe'")
    assert config(path)["shell"] == [str(bash), "-c"]


@pytest.mark.parametrize("legacy, own", [
    (inst.LEGACY_ROWS, None),
    ("in=$(cat); printf '%s' \"$in\" | { echo mine\n}; printf '%s' \"$in\" | " + inst.LEGACY_ROWS, "echo mine"),
    ("in=$(cat); printf '%s' \"$in\" | { echo mine; }; printf '%s' \"$in\" | " + inst.LEGACY_ROWS, "echo mine"),
])
def test_a_0_10_status_line_is_migrated(tmp_path, legacy, own):
    path = settings(tmp_path, {"statusLine": {"type": "command", "command": legacy, "refreshInterval": 1}})
    assert put(path) == "migrated"
    assert config(path)["own"] == own and "statusline.py" in load(path)["statusLine"]["command"]
    assert config(path)["before"] == ({"type": "command", "command": own} if own else None)


def test_a_migration_keeps_the_users_other_fields(tmp_path):
    legacy = "in=$(cat); printf '%s' \"$in\" | { echo mine\n}; printf '%s' \"$in\" | " + inst.LEGACY_ROWS
    path = settings(tmp_path, {"statusLine": {"type": "command", "command": legacy, "padding": 2,
                                              "refreshInterval": 1}})
    put(path)
    assert load(path)["statusLine"]["padding"] == 2
    uninstall(path, home=tmp_path / "home")
    assert load(path)["statusLine"] == {"type": "command", "command": "echo mine", "padding": 2}


def test_it_backs_up_the_file_before_writing(tmp_path):
    path = settings(tmp_path, {"statusLine": {"type": "command", "command": "echo mine"}})
    original = path.read_text(encoding="utf-8")
    put(path)
    assert (tmp_path / "settings.json.bak-cv-kit").read_text(encoding="utf-8") == original


def test_other_keys_and_unicode_survive(tmp_path):
    data = {"model": "opus", "hooks": {"Stop": []}, "theme": "đậm", "statusLine": {"type": "command", "command": "x"}}
    path = settings(tmp_path, data)
    put(path)
    after = load(path)
    assert {k: after[k] for k in ("model", "hooks", "theme")} == {k: data[k] for k in ("model", "hooks", "theme")}
    assert "đậm" in path.read_text(encoding="utf-8")


@pytest.mark.parametrize("text", ["{not json", "[1, 2]"])
def test_a_broken_settings_file_is_left_alone(tmp_path, text):
    path = tmp_path / "settings.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError):
        put(path)
    assert path.read_text(encoding="utf-8") == text and not (tmp_path / "settings.json.bak-cv-kit").exists()
    assert not (tmp_path / "home").exists()


def test_a_status_line_that_is_not_a_command_is_left_alone(tmp_path):
    with pytest.raises(ValueError):
        put(settings(tmp_path, {"statusLine": {"type": "static", "text": "hi"}}))


@pytest.mark.skipif(os.name == "nt", reason="symlinks need extra rights on Windows")
def test_a_symlinked_settings_file_stays_a_link_and_keeps_its_mode(tmp_path):
    real = settings(tmp_path, {"model": "opus"})
    real.chmod(0o600)
    link = tmp_path / "linked.json"
    link.symlink_to(real)
    put(link)
    assert link.is_symlink() and "statusLine" in load(real)
    assert stat.S_IMODE(real.stat().st_mode) == 0o600


# --- the command per platform ------------------------------------------------------------------------------------


def test_a_path_with_spaces_is_quoted_for_sh(tmp_path):
    path = settings(tmp_path, {})
    put(path, home=tmp_path / "my home", python="/opt/my python/bin/python3")
    command = load(path)["statusLine"]["command"]
    cfg = inst.config_path(path, tmp_path / "my home")
    assert command == f"'/opt/my python/bin/python3' '{tmp_path / 'my home'}/.claude/cv-kit/statusline.py' '{cfg}'"


def test_windows_with_git_bash(tmp_path):
    bash = tmp_path / "Git/bin/bash.exe"
    bash.parent.mkdir(parents=True)
    bash.write_text("")
    path = settings(tmp_path, {"statusLine": {"type": "command", "command": "echo mine"}})
    put(path, system="Windows", python="C:\\Users\\Ann Lee\\py\\python.exe", home=Path("C:/Users/Ann Lee"),
        env={"CLAUDE_CODE_GIT_BASH_PATH": str(bash)}, write_files=False)
    cfg = inst.config_path(path, Path("C:/Users/Ann Lee")).name
    assert load(path)["statusLine"]["command"] == \
        f"'C:/Users/Ann Lee/py/python.exe' 'C:/Users/Ann Lee/.claude/cv-kit/statusline.py' " \
        f"'C:/Users/Ann Lee/.claude/cv-kit/{cfg}'"


def test_windows_without_git_bash_uses_powershell_quoting(tmp_path, monkeypatch):
    monkeypatch.setattr(inst.shutil, "which", lambda name: None)
    path = settings(tmp_path, {})
    cfg = inst.config_path(path, Path("C:/Users/ann")).name
    put(path, system="Windows", python="C:\\Program Files\\Python312\\python.exe", home=Path("C:/Users/ann"), env={},
        write_files=False)
    assert load(path)["statusLine"]["command"] == \
        "& 'C:/Program Files/Python312/python.exe' 'C:/Users/ann/.claude/cv-kit/statusline.py' " \
        f"'C:/Users/ann/.claude/cv-kit/{cfg}'"
    put(path, system="Windows", python="C:\\Python312\\python.exe", home=Path("C:/Users/ann"), env={},
        write_files=False)
    assert load(path)["statusLine"]["command"] == \
        f"C:/Python312/python.exe C:/Users/ann/.claude/cv-kit/statusline.py C:/Users/ann/.claude/cv-kit/{cfg}"


def test_the_own_command_runs_in_the_shell_claude_code_would_use(tmp_path, monkeypatch):
    monkeypatch.setattr(inst.shutil, "which", lambda name: None)
    assert inst.status_shell("Linux", {}) == ["/bin/sh", "-c"] and inst.status_shell("Darwin", {}) == ["/bin/sh", "-c"]
    assert inst.status_shell("Windows", {}) == ["powershell.exe", "-NoProfile", "-Command"]
    git = tmp_path / "Git/cmd/git.exe"
    (tmp_path / "Git/bin").mkdir(parents=True), git.parent.mkdir(parents=True)
    git.write_text(""), (tmp_path / "Git/bin/bash.exe").write_text("")
    monkeypatch.setattr(inst.shutil, "which", lambda name: str(git) if name == "git" else None)
    assert inst.status_shell("Windows", {}) == [str(tmp_path / "Git/bin/bash.exe"), "-c"]
    wsl = tmp_path / "System32/bash.exe"  # WSL's bash.exe is not Git Bash and must not be picked
    wsl.parent.mkdir(), wsl.write_text("")
    assert inst.status_shell("Windows", {"CLAUDE_CODE_GIT_BASH_PATH": str(tmp_path / "nope/bash.exe")}) == \
        [str(tmp_path / "Git/bin/bash.exe"), "-c"]


def test_python3_is_preferred_but_a_broken_one_is_skipped(monkeypatch):
    monkeypatch.setattr(inst.shutil, "which", lambda name: "/usr/bin/python3" if name == "python3" else None)
    assert inst.pick_python(works=lambda p: True) == "/usr/bin/python3"
    assert inst.pick_python(works=lambda p: False) == sys.executable  # e.g. the Microsoft Store stub


# --- uninstall ---------------------------------------------------------------------------------------------------


def test_uninstall_restores_the_users_own_line_and_removes_the_launcher(tmp_path):
    original = {"type": "command", "command": "echo 'mine'", "padding": 2, "refreshInterval": 30}
    path = settings(tmp_path, {"model": "opus", "statusLine": original})
    put(path)
    assert uninstall(path, home=tmp_path / "home") == "restored"
    assert load(path) == {"model": "opus", "statusLine": original}
    assert not (tmp_path / "home/.claude/cv-kit").exists()


def test_uninstall_removes_a_rows_only_line(tmp_path):
    path = settings(tmp_path, {"model": "opus"})
    put(path)
    assert uninstall(path, home=tmp_path / "home") == "removed" and load(path) == {"model": "opus"}


@pytest.mark.parametrize("legacy, expected", [
    (inst.LEGACY_ROWS, None),
    ("in=$(cat); printf '%s' \"$in\" | { echo mine\n}; printf '%s' \"$in\" | " + inst.LEGACY_ROWS,
     {"type": "command", "command": "echo mine"}),
])
def test_uninstall_undoes_a_0_10_line(tmp_path, legacy, expected):
    path = settings(tmp_path, {"statusLine": {"type": "command", "command": legacy, "refreshInterval": 1}})
    uninstall(path, home=tmp_path / "home")
    assert load(path).get("statusLine") == expected


def test_uninstall_leaves_a_foreign_line_alone(tmp_path):
    path = settings(tmp_path, {"statusLine": {"type": "command", "command": "echo mine"}})
    before = path.read_text(encoding="utf-8")
    assert uninstall(path, home=tmp_path / "home") == "not set" and path.read_text(encoding="utf-8") == before


# --- the launcher ------------------------------------------------------------------------------------------------


def home_with_rows(tmp_path: Path, cfg: dict | None, pointer: bool = True) -> Path:
    home = tmp_path / "home"
    (home / ".claude/cv-kit").mkdir(parents=True)
    if cfg is not None:
        (home / ".claude/cv-kit/statusline.json").write_text(json.dumps(cfg), encoding="utf-8")
    if pointer:
        (home / ".cache/cv-kit").mkdir(parents=True)
        (home / ".cache/cv-kit/agent-rows-root").write_text(str(ROOT), encoding="utf-8")
    start = {"hook_event_name": "SubagentStart", "session_id": SID, "prompt_id": PROMPT, "agent_id": "a1",
             "agent_type": "Explore"}
    subprocess.run([PY, str(ROOT / "hooks/agent_rows.py"), "--event"], input=json.dumps(start).encode(),
                   env=env_for(home), check=True, timeout=30)
    return home


def launch(home: Path, stdin: str = json.dumps(PAYLOAD), *args: str, **extra) -> subprocess.CompletedProcess:
    args = args or (str(home / ".claude/cv-kit/statusline.json"),)  # the config the test wrote
    return subprocess.run([PY, str(LAUNCHER), *args], input=stdin.encode("utf-8"), capture_output=True, timeout=30,
                          env=env_for(home, **extra))


MINE = "import sys, json; print('mine', json.load(sys.stdin)['session_id'])"


def test_launcher_prints_the_users_line_then_the_rows(tmp_path):
    home = home_with_rows(tmp_path, {"own": MINE, "shell": OWN, "ascii": False, "main": True})
    result = launch(home, PYTHONIOENCODING="cp1252")
    lines = result.stdout.decode("utf-8").splitlines()
    assert result.returncode == 0 and lines[0] == f"mine {SID}"
    assert lines[1].startswith("● main") and re.match("[◐◓◑◒] Explore", lines[2])


def test_launcher_without_config_prints_the_rows(tmp_path):
    lines = launch(home_with_rows(tmp_path, None)).stdout.decode("utf-8").splitlines()
    assert lines[0].startswith("● main") and len(lines) == 2


def test_launcher_honours_ascii_and_no_main(tmp_path):
    out = launch(home_with_rows(tmp_path, {"own": None, "shell": OWN, "ascii": True, "main": False})).stdout.decode()
    assert out.isascii() and re.match(r"[|/\\-] Explore", out)


def test_launcher_keeps_the_users_line_when_cv_kit_is_gone(tmp_path):
    home = home_with_rows(tmp_path, {"own": MINE, "shell": OWN}, pointer=False)
    result = launch(home)
    assert (result.returncode, result.stdout.decode().splitlines()) == (0, [f"mine {SID}"])
    (home / ".cache/cv-kit").mkdir(parents=True, exist_ok=True)
    (home / ".cache/cv-kit/agent-rows-root").write_text(str(tmp_path / "deleted"), encoding="utf-8")
    assert launch(home).stdout.decode().splitlines() == [f"mine {SID}"]


def test_launcher_drops_a_failing_or_slow_own_line_and_still_draws_rows(tmp_path):
    home = home_with_rows(tmp_path, {"own": "import sys; print('x'); sys.exit(3)", "shell": OWN})
    lines = launch(home).stdout.decode("utf-8").splitlines()
    assert lines[0].startswith("● main")  # Claude Code shows a failing command as nothing, so the launcher does too
    slow = ("import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)']); "
            "time.sleep(30)")  # a grandchild that keeps stdout open
    (home / ".claude/cv-kit/statusline.json").write_text(json.dumps({"own": slow, "shell": OWN, "timeout": 1}),
                                                          encoding="utf-8")
    begun = time.monotonic()
    result = launch(home)
    assert result.returncode == 0 and result.stdout.decode("utf-8").startswith("● main")
    assert time.monotonic() - begun < 10


def test_launcher_reads_the_config_it_is_given(tmp_path):
    home = home_with_rows(tmp_path, {"own": "print('default')", "shell": OWN})
    other = home / ".claude/cv-kit/statusline-abc.json"
    other.write_text(json.dumps({"own": "print('other')", "shell": OWN, "main": False}), encoding="utf-8")
    lines = launch(home, json.dumps(PAYLOAD), str(other)).stdout.decode("utf-8").splitlines()
    assert lines[0] == "other" and re.match("[◐◓◑◒] Explore", lines[1])


def test_launcher_still_draws_with_a_0_10_agent_rows(tmp_path):
    old_root = tmp_path / "old"
    (old_root / "hooks").mkdir(parents=True)
    (old_root / "hooks/agent_rows.py").write_text("def status_line(raw):\n    return ['old rows']\n", encoding="utf-8")
    home = home_with_rows(tmp_path, None)
    (home / ".cache/cv-kit/agent-rows-root").write_text(str(old_root), encoding="utf-8")
    assert launch(home).stdout.decode().splitlines() == ["old rows"]


@pytest.mark.skipif(os.name == "nt", reason="POSIX signals")
def test_launcher_stopped_by_claude_code_takes_the_users_command_with_it(tmp_path):
    pid_file = tmp_path / "child.pid"
    own = f"import os, time; open({str(pid_file)!r}, 'w').write(str(os.getpid())); time.sleep(30)"
    home = home_with_rows(tmp_path, {"own": own, "shell": OWN})
    proc = subprocess.Popen([PY, str(LAUNCHER), str(home / ".claude/cv-kit/statusline.json")],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, env=env_for(home))
    proc.stdin.write(json.dumps(PAYLOAD).encode()), proc.stdin.close()
    deadline = time.monotonic() + 20
    while not pid_file.exists() or not pid_file.read_text():
        assert time.monotonic() < deadline
        time.sleep(0.05)
    proc.terminate()  # Claude Code cancels an in-flight status line
    proc.wait(timeout=10)
    child = int(pid_file.read_text())
    time.sleep(0.3)
    with pytest.raises(ProcessLookupError):
        os.kill(child, 0)


def test_launcher_never_fails(tmp_path):
    home = home_with_rows(tmp_path, None)
    (home / ".claude/cv-kit/statusline.json").write_text("{broken", encoding="utf-8")
    for stdin in ("", "not json", "[]"):
        result = launch(home, stdin=stdin)
        assert result.returncode == 0 and result.stderr == b""


def test_installed_command_end_to_end(tmp_path):
    """Install for this machine, then run the written command the way Claude Code would."""
    home = home_with_rows(tmp_path, None)
    path = settings(tmp_path, {"statusLine": {"type": "command", "command": "echo mine"}})
    system = {"nt": "Windows"}.get(os.name, "Linux")
    shell = inst.status_shell(system, os.environ)
    install(path, home=home, system=system, python=PY, env=os.environ)
    command = load(path)["statusLine"]["command"]
    result = subprocess.run([*shell, command], input=json.dumps(PAYLOAD).encode(), capture_output=True, timeout=60,
                            env=env_for(home))
    lines = result.stdout.decode("utf-8").splitlines()
    assert result.returncode == 0 and lines[0] == "mine" and lines[1].startswith("● main")


# --- the command line and docs -----------------------------------------------------------------------------------


def test_cli(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(inst, "python3_works", lambda python=None: True)
    home = tmp_path / "home"
    monkeypatch.setattr(inst, "HOME", home)
    path = settings(tmp_path, {})
    assert main(["--settings", str(path)]) == 0
    assert "added" in capsys.readouterr().out
    assert main(["--settings", str(path), "--uninstall"]) == 0
    assert main(["--settings", str(tmp_path / "x.json"), "--refresh", "0"]) == 2
    (tmp_path / "bad.json").write_text("{", encoding="utf-8")
    assert main(["--settings", str(tmp_path / "bad.json")]) == 1


def test_cli_warns_when_the_hooks_cannot_run(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(inst, "python3_works", lambda python=None: False)
    monkeypatch.setattr(inst, "HOME", tmp_path / "home")
    assert main(["--settings", str(settings(tmp_path, {}))]) == 0
    assert "python3" in capsys.readouterr().err


def test_the_readme_gives_the_command_for_each_shell():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert 'python3 "$(cat ~/.cache/cv-kit/agent-rows-root)/scripts/install_statusline.py"' in text
    assert 'python "$(Get-Content ~/.cache/cv-kit/agent-rows-root)/scripts/install_statusline.py"' in text
