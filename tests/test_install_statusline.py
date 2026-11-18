"""scripts/install_statusline.py adds the agent rows to a user's statusLine, keeping the line they already have."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from install_statusline import ROWS, install, main, uninstall

ROOT = Path(__file__).resolve().parents[1]


def settings(tmp_path: Path, data: dict | None) -> Path:
    path = tmp_path / "settings.json"
    if data is not None:
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_no_status_line_gets_the_rows_alone(tmp_path):
    path = settings(tmp_path, {"model": "opus"})
    assert install(path) == "added"
    assert load(path) == {"model": "opus", "statusLine": {"type": "command", "command": ROWS, "refreshInterval": 1}}


def test_a_missing_settings_file_is_created(tmp_path):
    path = settings(tmp_path / "new", None)
    assert install(path) == "added" and load(path)["statusLine"]["command"] == ROWS


def test_an_existing_status_line_is_kept_and_runs_first(tmp_path):
    path = settings(tmp_path, {"statusLine": {"type": "command", "command": "echo 'mine'", "padding": 2}})
    assert install(path) == "wrapped"
    line = load(path)["statusLine"]
    assert line["padding"] == 2 and line["refreshInterval"] == 1
    assert line["command"] == "in=$(cat); printf '%s' \"$in\" | { echo 'mine'\n}; printf '%s' \"$in\" | " + ROWS


def test_a_slower_refresh_of_the_users_own_is_lowered_and_a_faster_one_kept(tmp_path):
    slow = settings(tmp_path, {"statusLine": {"type": "command", "command": "x", "refreshInterval": 30}})
    install(slow)
    assert load(slow)["statusLine"]["refreshInterval"] == 1
    install(slow := settings(tmp_path, {"statusLine": {"type": "command", "command": "x"}}), refresh=5)
    assert load(slow)["statusLine"]["refreshInterval"] == 5


@pytest.mark.parametrize("own", ["echo mine # my line", "echo mine &", "echo mine;"])
def test_a_command_ending_in_a_comment_or_ampersand_still_runs(tmp_path, own):
    path = settings(tmp_path, {"statusLine": {"type": "command", "command": own}})
    install(path)
    command = load(path)["statusLine"]["command"]
    result = subprocess.run(["sh", "-c", command + "; wait"], input="{}", capture_output=True, text=True, timeout=20,
                            env={**os.environ, "HOME": str(tmp_path)})
    assert (result.returncode, result.stdout) == (0, "mine\n")


def test_a_symlinked_settings_file_stays_a_link_and_keeps_its_mode(tmp_path):
    real = settings(tmp_path, {"model": "opus"})
    real.chmod(0o600)
    link = tmp_path / "linked.json"
    link.symlink_to(real)
    install(link)
    assert link.is_symlink() and load(real)["statusLine"]["command"] == ROWS
    assert real.stat().st_mode & 0o777 == 0o600


def test_running_it_twice_changes_nothing(tmp_path):
    path = settings(tmp_path, {"statusLine": {"type": "command", "command": "echo mine"}})
    install(path)
    before = path.read_text(encoding="utf-8")
    assert install(path) == "already set" and path.read_text(encoding="utf-8") == before


def test_it_backs_up_the_file_before_writing(tmp_path):
    path = settings(tmp_path, {"statusLine": {"type": "command", "command": "echo mine"}})
    original = path.read_text(encoding="utf-8")
    install(path)
    assert (tmp_path / "settings.json.bak-cv-kit").read_text(encoding="utf-8") == original


def test_other_keys_and_unicode_survive(tmp_path):
    data = {"model": "opus", "hooks": {"Stop": []}, "theme": "đậm", "statusLine": {"type": "command", "command": "x"}}
    path = settings(tmp_path, data)
    install(path)
    after = load(path)
    assert {k: after[k] for k in ("model", "hooks", "theme")} == {k: data[k] for k in ("model", "hooks", "theme")}
    assert "đậm" in path.read_text(encoding="utf-8")


@pytest.mark.parametrize("text", ["{not json", "[1, 2]"])
def test_a_broken_settings_file_is_left_alone(tmp_path, text):
    path = tmp_path / "settings.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError):
        install(path)
    assert path.read_text(encoding="utf-8") == text and not (tmp_path / "settings.json.bak-cv-kit").exists()


def test_a_status_line_that_is_not_a_command_is_left_alone(tmp_path):
    path = settings(tmp_path, {"statusLine": {"type": "static", "text": "hi"}})
    with pytest.raises(ValueError):
        install(path)


def test_uninstall_restores_the_users_own_line(tmp_path):
    original = {"type": "command", "command": "echo 'mine'", "padding": 2, "refreshInterval": 30}
    path = settings(tmp_path, {"model": "opus", "statusLine": original})
    install(path)
    assert uninstall(path) == "restored"
    assert load(path) == {"model": "opus", "statusLine": original}


def test_uninstall_without_the_backup_drops_the_refresh_it_added(tmp_path):
    path = settings(tmp_path, {"statusLine": {"type": "command", "command": "echo mine"}})
    install(path)
    (tmp_path / "settings.json.bak-cv-kit").unlink()
    uninstall(path)
    assert load(path)["statusLine"] == {"type": "command", "command": "echo mine"}


def test_uninstall_removes_a_rows_only_line(tmp_path):
    path = settings(tmp_path, {"model": "opus"})
    install(path)
    assert uninstall(path) == "removed" and load(path) == {"model": "opus"}


def test_uninstall_leaves_a_foreign_line_alone(tmp_path):
    path = settings(tmp_path, {"statusLine": {"type": "command", "command": "echo mine"}})
    before = path.read_text(encoding="utf-8")
    assert uninstall(path) == "not set" and path.read_text(encoding="utf-8") == before


def test_the_written_command_keeps_your_line_and_draws_rows(tmp_path):
    path = settings(tmp_path, {"statusLine": {"type": "command", "command": "read -r x; echo mine"}})
    install(path)
    home = tmp_path / "home"
    env = {**os.environ, "HOME": str(home), "NO_COLOR": "1"}
    subprocess.run([sys.executable, str(ROOT / "hooks/agent_rows.py"), "--register"], env=env, check=True)
    start = {"hook_event_name": "SubagentStart", "session_id": "s-1", "prompt_id": "p-1", "agent_id": "a1",
             "agent_type": "Explore"}
    subprocess.run([sys.executable, str(ROOT / "hooks/agent_rows.py"), "--event"], input=json.dumps(start), text=True,
                   env=env, check=True)
    result = subprocess.run(["sh", "-c", load(path)["statusLine"]["command"]], text=True, capture_output=True,
                            input='{"session_id": "s-1", "prompt_id": "p-1"}\n', env=env, timeout=20)
    assert result.returncode == 0
    assert result.stdout.splitlines()[0] == "mine" and re.match("[◐◓◑◒] Explore", result.stdout.splitlines()[1])


def test_the_rows_command_matches_the_documented_one():
    text = (ROOT / "hooks/README.md").read_text(encoding="utf-8")
    [block] = [json.loads(b) for b in re.findall(r"```json\n(.*?)```", text, re.S) if '"statusLine"' in b]
    assert block["statusLine"]["command"] == ROWS


def test_cli(tmp_path, capsys):
    path = settings(tmp_path, {})
    assert main(["--settings", str(path)]) == 0
    assert "added" in capsys.readouterr().out
    assert main(["--settings", str(path), "--uninstall"]) == 0
    assert main(["--settings", str(tmp_path / "x.json"), "--refresh", "0"]) == 2
    (tmp_path / "bad.json").write_text("{", encoding="utf-8")
    assert main(["--settings", str(tmp_path / "bad.json")]) == 1


def test_the_readme_gives_the_command():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert 'python3 "$(cat ~/.cache/cv-kit/agent-rows-root)/scripts/install_statusline.py"' in text
