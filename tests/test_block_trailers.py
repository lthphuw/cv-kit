import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "block_trailers.py"
TRAILER = "Co-Authored-By: Someone <someone@example.com>"


def run_hook(command: str, cwd: Path, tool: str = "Bash") -> subprocess.CompletedProcess:
    payload = {"tool_name": tool, "tool_input": {"command": command}, "cwd": str(cwd)}
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), capture_output=True, text=True)


@pytest.mark.parametrize(
    "command",
    [
        'git commit -m "fix(loader): handle empty masks"',
        "git status",
        'git add . && git commit -m "ok"',
        'svn commit -m "fix: tidy paths"',
        f'echo "{TRAILER}"',
        'git commit -m "Add anchors generated with k-means"',
        'git commit -m "fix: x" && git status -s',
        "git commit -m x; git show -s HEAD",
        "git commit -m x && git push -s",
        "git commit -F - <<'EOF'\nfix: don't reject -s\n\nrefuse --trailer text\nEOF",
        "git commit -m x && git commit -m y",
        "git commit -m x && git status -s",
        "git commit -F - <<'EOF'\nfix: document git commit -s\n\nbody mentions git commit --signoff\nEOF",
        'git commit -m "a << b"',
        "echo 1 << 2",
        "git commit -F - <<-EOF\n\tfix: document git commit -s\n\tEOF",
    ],
)
def test_clean_commands_are_allowed(command, tmp_path):
    assert run_hook(command, tmp_path).returncode == 0


@pytest.mark.parametrize(
    "command",
    [
        f'git commit -m "fix\n\n{TRAILER}"',
        f'git commit -m "fix" -m "{TRAILER}"',
        f"git commit -F - <<'EOF'\nfix\n\n{TRAILER}\nEOF",
        'git commit -m "$(cat <<\'EOF\'\nfix\n\nSigned-off-by: A <a@b.c>\nEOF\n)"',
        'git commit -m "fix\n\nGenerated with Claude Code"',
        'git commit -m "fix 🤖"',
        'git commit -m "Generated with Claude Code"',
        'git commit -m "fix" -m "  Generated with Claude Code"',
        "git commit -m $'fix\\n\\nGenerated with Claude Code'",
        'git commit --signoff -m "fix"',
        'git commit -s -m "fix"',
        'git commit -sm "fix"',
        'git commit --trailer "Reviewed-by: A" -m "fix"',
        f'svn commit -m "fix\n\n{TRAILER}"',
        f'svn ci -m "fix" -m "{TRAILER}"',
        'svn commit -m "fix\n\nPatch by: A"',
        'git commit -m "fix\n\nClaude-Session: https://example.com/s"',
        'git commit -m "fix\n\nSigned-off-by: A"',
        'git commit -m "fix\n\nCo-Authored-By: A"',
        'git commit -m "fix\n\nGenerated-by: A"',
        'git commit -m "fix\n\nAcked-by: A"',
        'git commit -m "fix\n\nReviewed-by: A"',
        'git commit -m "fix\n\nTested-by: A"',
        'git commit -m "fix\n\nReported-by: A"',
        'git commit -m "fix\n\nSuggested-by: A"',
        'git commit -m "fix\n\nHelped-by: A"',
        'git commit -m "fix\n\nReview by: A"',
        'git commit -m "fix\n\nFound by: A"',
        'git commit -m "fix\n\nPatch by: A"',
        "git commit --trailer foo -m x",
        "git commit --trailer=foo -m x",
        f"git commit -m $'fix\\n\\n{TRAILER}'",
        f'printf "fix\\n\\n{TRAILER}" | git commit -F -',
        f'echo -e "fix\\n\\n{TRAILER}" | git commit -F -',
        "git commit -m x && git commit -s -m y",
        'git commit -m "x"; git commit --signoff -m y',
        "git commit -m x&&git commit -s -m y",
        "git commit -m x && git -C y commit -s",
        'git commit -m "a << b"\ngit commit -s -m y',
        'git commit -m "feat: a << b"\ngit commit --amend -s',
        'echo "<<EOF"\ngit commit -s -m y',
        "n=$((1 << k))\ngit commit -s -m y",
        "cat <<'EOF'\nx\nEOF\ngit commit -s -m y",
    ],
)
def test_trailers_are_denied(command, tmp_path):
    result = run_hook(command, tmp_path)
    assert result.returncode == 2
    assert "Commit blocked" in result.stderr


def test_message_file_content_is_scanned(tmp_path):
    (tmp_path / "msg.txt").write_text(f"fix\n\n{TRAILER}\n", encoding="utf-8")
    for command in (
        "svn commit -F msg.txt",
        "git commit --file=msg.txt",
        "svn commit -m x && svn commit -F msg.txt",
        "git commit -m x && git commit --file=msg.txt",
        'git commit -m "feat: a << b"\ngit commit -F msg.txt',
    ):
        result = run_hook(command, tmp_path)
        assert result.returncode == 2
        assert "Commit blocked" in result.stderr


def test_clean_message_file_is_allowed(tmp_path):
    (tmp_path / "msg.txt").write_text("fix: tidy paths\n\nExplain why.\n", encoding="utf-8")
    assert run_hook("svn commit -F msg.txt", tmp_path).returncode == 0


def test_non_bash_tools_are_ignored(tmp_path):
    assert run_hook(f'git commit -m "{TRAILER}"', tmp_path, tool="Write").returncode == 0


def test_invalid_json_fails_open(tmp_path):
    result = subprocess.run([sys.executable, str(HOOK)], input="not json", capture_output=True, text=True)
    assert result.returncode == 0


@pytest.mark.parametrize(
    "payload",
    [
        "{}",
        '{"tool_name": "Bash"}',
        "null",
        "[]",
        '{"tool_name": "Bash", "tool_input": null}',
        '{"tool_name": "Bash", "tool_input": {"command": null}}',
        '{"tool_name": "Bash", "tool_input": {"command": "svn commit -F missing.txt"}, "cwd": null}',
    ],
)
def test_malformed_payloads_fail_open(payload, tmp_path):
    result = subprocess.run(
        [sys.executable, str(HOOK)], input=payload, capture_output=True, text=True, cwd=tmp_path
    )
    assert result.returncode == 0
    assert "Traceback" not in result.stderr


def test_deny_message_tells_claude_to_stop_when_the_line_cannot_be_dropped(tmp_path):
    result = run_hook(f'git commit -m "fix\n\n{TRAILER}"', tmp_path)
    assert "stop and tell the user; do not retry" in result.stderr
