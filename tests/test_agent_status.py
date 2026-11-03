"""Live subagent rows: hooks/agent_status.py rewrites each row from the JSON Claude Code sends on stdin."""
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "hooks/agent_status.py"
NOW_MS = 1_800_000_000_000
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def load():
    spec = importlib.util.spec_from_file_location("agent_status", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def task(**over) -> dict:
    base = {"id": "t1", "type": "local_agent", "agentType": "cv-kit:engineer", "status": "running",
            "description": "clamp_boxes", "label": "writing the failing test", "startTime": NOW_MS - 252_000,
            "model": "claude-sonnet-5-5", "effort": "medium", "tokenCount": 1200}
    return {**base, **over}


def rows(tasks, columns=200, color=False) -> list[dict]:
    out = load().render({"columns": columns, "tasks": tasks}, NOW_MS, color=color)
    return [json.loads(line) for line in out]


def content(columns=200, **over) -> str:
    return rows([task(**over)], columns)[0]["content"]


def test_row_shows_icon_name_model_effort_elapsed_tokens_and_label():
    want = "● engineer  sonnet  ▰▰▱▱▱  4m12s  1.2k  writing the failing test"
    assert rows([task()]) == [{"id": "t1", "content": want}]


@pytest.mark.parametrize("effort, meter", [("low", "▰▱▱▱▱"), ("medium", "▰▰▱▱▱"), ("high", "▰▰▰▱▱"),
                                           ("xhigh", "▰▰▰▰▱"), ("max", "▰▰▰▰▰"), ("HIGH", "▰▰▰▱▱"),
                                           (8000, "≤8k"), (512, "≤512"), ("auto", "auto")])
def test_effort_is_a_five_step_meter_or_the_budget(effort, meter):
    assert f"  {meter}  " in content(effort=effort)


@pytest.mark.parametrize("effort", [None, "", True, -5])
def test_rows_without_effort_drop_the_column(effort):
    assert content(effort=effort) == "● engineer  sonnet  4m12s  1.2k  writing the failing test"


@pytest.mark.parametrize("status, icon", [("running", "●"), ("completed", "✓"), ("failed", "✗"),
                                          ("killed", "■"), ("pending", "○")])
def test_status_is_an_icon(status, icon):
    assert content(status=status).startswith(f"{icon} engineer  ")


@pytest.mark.parametrize("count, shown", [(850, "850"), (1200, "1.2k"), (17_768, "18k"), (1_250_000, "1.2M")])
def test_token_count(count, shown):
    assert f"  {shown}  writing" in content(tokenCount=count)


@pytest.mark.parametrize("count", [0, None, "x", True])
def test_rows_without_tokens_drop_the_column(count):
    assert content(tokenCount=count).endswith("  4m12s  writing the failing test")


@pytest.mark.parametrize("start, shown", [(NOW_MS - 9_000, "9s"), (NOW_MS - 60_000, "1m00s"),
                                          (NOW_MS - 3_725_000, "1h02m"), (NOW_MS + 5_000, "0s")])
def test_elapsed_formats(start, shown):
    assert f"  {shown}  1.2k" in content(startTime=start)


@pytest.mark.parametrize("fields, name", [({"agentType": "cv-kit:reviewer"}, "reviewer"),
                                          ({"agentType": "Explore"}, "Explore"),
                                          ({"agentType": "", "name": "scout"}, "scout"),
                                          ({"agentType": "", "name": ""}, "agent")])
def test_agent_name(fields, name):
    assert content(**fields).startswith(f"● {name}  ")


def test_missing_model_effort_tokens_and_label_fall_back():
    t = task(label="", description="clamp_boxes", tokenCount=0)
    del t["model"], t["effort"]
    assert rows([t])[0]["content"] == "● engineer  4m12s  clamp_boxes"


def test_finished_rows_have_no_clock_because_the_task_has_no_end_time():
    assert content(status="failed") == "✗ engineer  sonnet  ▰▰▱▱▱  1.2k  writing the failing test"


def test_columns_line_up_across_rows():
    out = rows([task(id="a", agentType="cv-kit:claim-verifier", model="claude-haiku-5-5", effort="low",
                     tokenCount=850, label="re-check claims"),
                task(id="b", status="completed", label="add iou")])
    assert [r["content"] for r in out] == [
        "● claim-verifier  haiku   ▰▱▱▱▱  4m12s   850  re-check claims",
        "✓ engineer        sonnet  ▰▰▱▱▱         1.2k  add iou",
    ]


def test_a_long_agent_name_is_cut_so_it_cannot_push_the_other_columns_away():
    assert content(agentType="x" * 40).startswith("● " + "x" * 15 + "…  sonnet  ")


@pytest.mark.parametrize("color", [False, True])
def test_truncates_to_the_visible_width(color):
    text = rows([task(label="x" * 300)], columns=40, color=color)[0]["content"]
    plain = ANSI.sub("", text)
    assert len(plain) == 40 and plain.endswith("…")


def test_wide_characters_count_twice():
    plain = content(columns=40, label="検出" * 50)
    width = sum(2 if "　" <= ch <= "鿿" else 1 for ch in plain)
    assert width <= 40 and plain.endswith("…")


def test_label_is_one_line_without_control_characters():
    text = content(label="a\nb\x1b[31m  c")
    assert text.endswith("  a b [31m c") and "\n" not in text and "\x1b" not in text


def test_color_tints_the_row_and_strips_back_to_the_plain_text():
    tinted = rows([task(), task(id="t2", status="completed")], color=True)
    plain = rows([task(), task(id="t2", status="completed")], color=False)
    assert all("\x1b[" in r["content"] for r in tinted)
    assert [ANSI.sub("", r["content"]) for r in tinted] == [r["content"] for r in plain]


def test_rows_without_an_id_keep_the_default_and_bad_rows_do_not_hide_good_ones():
    out = rows([{"agentType": "x"}, "junk", task(id="ok"), task(id="bad", startTime="soon")])
    assert [r["id"] for r in out] == ["ok", "bad"] and out[1]["content"].startswith("● engineer")


def run(stdin: str, **env) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT)], input=stdin, capture_output=True, text=True, timeout=20,
                          env={**os.environ, **env})


def test_cli_prints_one_json_line_per_task():
    result = run(json.dumps({"columns": 120, "tasks": [task(id="a"), task(id="b", agentType="cv-kit:explorer")]}))
    assert result.returncode == 0
    ids = [json.loads(line)["id"] for line in result.stdout.splitlines()]
    assert ids == ["a", "b"]


@pytest.mark.parametrize("no_color, tinted", [("", True), ("1", False)])
def test_cli_honours_no_color(no_color, tinted):
    result = run(json.dumps({"columns": 120, "tasks": [task()]}), NO_COLOR=no_color)
    assert ("\x1b[" in json.loads(result.stdout)["content"]) is tinted


@pytest.mark.parametrize("stdin", ["", "not json", "[]", "null", json.dumps({"tasks": "x"}), json.dumps({"tasks": [1]})])
def test_never_crashes_and_prints_nothing_on_bad_input(stdin):
    result = run(stdin)
    assert result.returncode == 0 and result.stdout == "" and result.stderr == ""


def test_settings_json_registers_it_and_nothing_else():
    settings = json.loads((ROOT / "settings.json").read_text(encoding="utf-8"))
    assert set(settings) == {"subagentStatusLine"}  # only `agent` and `subagentStatusLine` take effect in a plugin
    line = settings["subagentStatusLine"]
    assert line["type"] == "command" and "hooks/agent_status.py" in line["command"]
    # Claude Code leaves ${CLAUDE_PLUGIN_ROOT} empty here (seen on 2.1.317), so the path comes from the pointer file.
    assert "CLAUDE_PLUGIN_ROOT" not in line["command"]
    assert ".cache/cv-kit/plugin-root" in line["command"]


def register(home: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), "--register"], input='{"hook_event_name": "SessionStart"}',
                          capture_output=True, text=True, timeout=20, env={**os.environ, "HOME": str(home)})


def test_register_writes_the_plugin_root_and_prints_nothing(tmp_path):
    result = register(tmp_path)
    assert result.returncode == 0 and result.stdout == ""
    assert (tmp_path / ".cache/cv-kit/plugin-root").read_text(encoding="utf-8") == str(ROOT)


def test_register_never_fails_when_the_cache_cannot_be_written(tmp_path):
    home = tmp_path / "file"
    home.write_text("not a folder")
    result = register(home)
    assert result.returncode == 0 and result.stdout == "" and result.stderr == ""


def test_the_settings_command_renders_rows_after_register(tmp_path):
    register(tmp_path)
    command = json.loads((ROOT / "settings.json").read_text(encoding="utf-8"))["subagentStatusLine"]["command"]
    payload = json.dumps({"columns": 80, "tasks": [{"id": "t1", "agentType": "cv-kit:engineer", "status": "running",
                                                    "label": "x", "startTime": 0, "model": "claude-sonnet-5-5"}]})
    result = subprocess.run(["sh", "-c", command], input=payload, capture_output=True, text=True, timeout=20,
                            cwd=tmp_path, env={**os.environ, "HOME": str(tmp_path), "NO_COLOR": "1"})
    assert json.loads(result.stdout)["content"].startswith("● engineer  sonnet  ")


def test_hooks_json_registers_the_pointer_at_session_start():
    hooks = json.loads((ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]
    args = [" ".join(h.get("args", [])) for g in hooks["SessionStart"] for h in g["hooks"]]
    assert any("agent_status.py" in a and "--register" in a for a in args)
