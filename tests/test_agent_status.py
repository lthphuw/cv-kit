"""Live subagent rows: hooks/agent_status.py rewrites each row from the JSON Claude Code sends on stdin."""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "hooks/agent_status.py"
NOW_MS = 1_800_000_000_000


def load():
    spec = importlib.util.spec_from_file_location("agent_status", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def task(**over) -> dict:
    base = {"id": "t1", "type": "local_agent", "agentType": "cv-kit:engineer", "status": "running",
            "description": "clamp_boxes", "label": "writing the failing test", "startTime": NOW_MS - 252_000,
            "model": "claude-sonnet-5-5", "tokenCount": 1200}
    return {**base, **over}


def rows(tasks, columns=200) -> list[dict]:
    module = load()
    out = module.render({"columns": columns, "tasks": tasks}, NOW_MS)
    return [json.loads(line) for line in out]


def test_row_shows_name_model_elapsed_tokens_status_and_label():
    # Claude Code refreshes about every 5 s; the token count shows the agent is still working between ticks.
    want = "engineer · sonnet · 4m12s · 1.2k tok · running · writing the failing test"
    assert rows([task()]) == [{"id": "t1", "content": want}]


@pytest.mark.parametrize("count, shown", [(850, "850 tok"), (17_768, "17.8k tok"), (0, None), (None, None), ("x", None)])
def test_token_count(count, shown):
    content = rows([task(tokenCount=count)])[0]["content"]
    assert (f" · {shown} · " in content) if shown else ("tok" not in content)


@pytest.mark.parametrize("start, shown", [(NOW_MS - 9_000, "9s"), (NOW_MS - 60_000, "1m00s"),
                                          (NOW_MS - 3_725_000, "1h02m"), (NOW_MS + 5_000, "0s")])
def test_elapsed_formats(start, shown):
    assert f" · {shown} · " in rows([task(startTime=start)])[0]["content"]


@pytest.mark.parametrize("fields, name", [({"agentType": "cv-kit:reviewer"}, "reviewer"),
                                          ({"agentType": "Explore"}, "Explore"),
                                          ({"agentType": "", "name": "scout"}, "scout"),
                                          ({"agentType": "", "name": ""}, "agent")])
def test_agent_name(fields, name):
    assert rows([task(**fields)])[0]["content"].startswith(f"{name} · ")


def test_missing_model_and_label_fall_back():
    t = task(label="", description="clamp_boxes", tokenCount=0)
    del t["model"]
    assert rows([t])[0]["content"] == "engineer · 4m12s · running · clamp_boxes"


def test_finished_rows_have_no_clock_because_the_task_has_no_end_time():
    assert rows([task(status="failed")])[0]["content"] == "engineer · sonnet · 1.2k tok · failed · writing the failing test"


def test_truncates_to_columns():
    content = rows([task(label="x" * 300)], columns=40)[0]["content"]
    assert len(content) == 40 and content.endswith("…")


def test_label_is_one_line_without_control_characters():
    content = rows([task(label="a\nb\x1b[31m  c")])[0]["content"]
    assert content.endswith("· a b [31m c") and "\n" not in content and "\x1b" not in content


def test_rows_without_an_id_keep_the_default_and_bad_rows_do_not_hide_good_ones():
    out = rows([{"agentType": "x"}, "junk", task(id="ok"), task(id="bad", startTime="soon")])
    assert [r["id"] for r in out] == ["ok", "bad"] and "running" in out[1]["content"]


def run(stdin: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT)], input=stdin, capture_output=True, text=True, timeout=20)


def test_cli_prints_one_json_line_per_task():
    result = run(json.dumps({"columns": 120, "tasks": [task(id="a"), task(id="b", agentType="cv-kit:explorer")]}))
    assert result.returncode == 0
    ids = [json.loads(line)["id"] for line in result.stdout.splitlines()]
    assert ids == ["a", "b"]


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
                            cwd=tmp_path, env={**os.environ, "HOME": str(tmp_path)})
    assert json.loads(result.stdout)["content"].startswith("engineer · sonnet · ")


def test_hooks_json_registers_the_pointer_at_session_start():
    hooks = json.loads((ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]
    args = [" ".join(h.get("args", [])) for g in hooks["SessionStart"] for h in g["hooks"]]
    assert any("agent_status.py" in a and "--register" in a for a in args)
