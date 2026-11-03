"""Live subagent rows: hooks/agent_status.py rewrites each row from the JSON Claude Code sends on stdin."""
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "hooks/agent_status.py"
NOW_MS = 1_800_000_000_000
ANSI = re.compile(r"\x1b\[[0-9;]*m")
FULL = "◐ engineer (sonnet ▰▰▱▱▱)  writing the failing test  1.2k  4m12s"


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


def rows(tasks, columns=200, color=False, memory=None) -> list[dict]:
    out = load().render({"columns": columns, "tasks": tasks}, NOW_MS, color=color, memory=memory)
    return [json.loads(line) for line in out]


def content(columns=200, color=False, memory=None, **over) -> str:
    return rows([task(**over)], columns, color, memory)[0]["content"]


# --- layout: `icon name (model meter)  label  tokens  time` --------------------------------------------------------

def test_row_is_icon_name_model_group_label_tokens_and_time():
    assert rows([task()]) == [{"id": "t1", "content": FULL}]


@pytest.mark.parametrize("effort, meter", [("low", "▰▱▱▱▱"), ("medium", "▰▰▱▱▱"), ("high", "▰▰▰▱▱"),
                                           ("xhigh", "▰▰▰▰▱"), ("max", "▰▰▰▰▰"), ("HIGH", "▰▰▰▱▱"),
                                           (8000, "≤8k"), (512, "≤512"), ("auto", "auto")])
def test_effort_sits_in_the_model_group(effort, meter):
    assert content(effort=effort).startswith(f"◐ engineer (sonnet {meter})  writing")


@pytest.mark.parametrize("effort", [None, "", True, -5])
def test_without_effort_the_group_holds_the_model_only(effort):
    assert content(effort=effort) == "◐ engineer (sonnet)  writing the failing test  1.2k  4m12s"


def test_without_a_model_the_group_holds_the_meter_only():
    t = task()
    del t["model"]
    assert rows([t])[0]["content"].startswith("◐ engineer (▰▰▱▱▱)  writing")


@pytest.mark.parametrize("status, icon", [("completed", "✓"), ("failed", "✗"), ("killed", "■"), ("pending", "○")])
def test_status_is_an_icon(status, icon):
    assert content(status=status).startswith(f"{icon} engineer (")


@pytest.mark.parametrize("count, shown", [(850, "850"), (1200, "1.2k"), (17_768, "18k"), (1_250_000, "1.2M")])
def test_token_count(count, shown):
    assert content(tokenCount=count).endswith(f"  {shown}  4m12s")


@pytest.mark.parametrize("count", [0, None, "x", True])
def test_rows_without_tokens_drop_the_column(count):
    assert content(tokenCount=count).endswith("writing the failing test  4m12s")


@pytest.mark.parametrize("start, shown", [(NOW_MS - 9_000, "9s"), (NOW_MS - 60_000, "1m00s"),
                                          (NOW_MS - 3_725_000, "1h02m"), (NOW_MS + 5_000, "0s")])
def test_elapsed_formats(start, shown):
    assert content(startTime=start).endswith(f"  1.2k  {shown}")


@pytest.mark.parametrize("fields, name", [({"agentType": "cv-kit:reviewer"}, "reviewer"),
                                          ({"agentType": "Explore"}, "Explore"),
                                          ({"agentType": "", "name": "scout"}, "scout"),
                                          ({"agentType": "", "name": ""}, "agent")])
def test_agent_name(fields, name):
    assert content(**fields).startswith(f"◐ {name} (")


def test_missing_model_effort_tokens_and_label_fall_back():
    t = task(label="", description="clamp_boxes", tokenCount=0)
    del t["model"], t["effort"]
    assert rows([t])[0]["content"] == "◐ engineer  clamp_boxes  4m12s"


def test_finished_rows_have_no_clock_because_the_task_has_no_end_time():
    assert content(status="failed") == "✗ engineer (sonnet ▰▰▱▱▱)  writing the failing test  1.2k"


def test_columns_line_up_across_rows():
    out = rows([task(id="a", agentType="cv-kit:claim-verifier", model="claude-haiku-5-5", effort="low",
                     tokenCount=850, label="re-check claims"),
                task(id="b", status="completed", label="add iou")])
    assert [r["content"] for r in out] == [
        "◐ claim-verifier (haiku ▰▱▱▱▱)  re-check claims   850  4m12s",
        "✓ engineer (sonnet ▰▰▱▱▱)       add iou          1.2k",
    ]


def test_a_long_agent_name_is_cut_so_it_cannot_push_the_other_columns_away():
    assert content(agentType="x" * 40).startswith("◐ " + "x" * 15 + "… (sonnet ")


def test_a_long_label_stops_at_48_columns_so_tokens_and_time_stay_close():
    assert content(label="x" * 100) == "◐ engineer (sonnet ▰▰▱▱▱)  " + "x" * 47 + "…  1.2k  4m12s"


# --- responsive: narrower rows drop parts in a fixed order ---------------------------------------------------------

@pytest.mark.parametrize("columns, want", [
    (64, FULL),
    (60, "◐ engineer (sonnet ▰▰▱▱▱)  writing the failing…  1.2k  4m12s"),  # the label shrinks first
    (55, "◐ engineer (sonnet ▰▰▱▱▱)  writing the failing…   4m12s"),       # then the tokens go
    (50, "◐ engineer (sonnet)  writing the failing t…  4m12s"),            # then the effort meter
    (34, "◐ engineer  writing the fa…  4m12s"),                            # then the model group
    (26, "◐ engineer  writin…  4m12s"),                                    # the label shrinks again
    (20, "◐ engineer  4m12s"),                                             # then goes
])
def test_narrow_rows_drop_parts_in_order(columns, want):
    assert content(columns=columns) == want


@pytest.mark.parametrize("color", [False, True])
def test_never_wider_than_the_row(color):
    for columns in range(8, 80):
        plain = ANSI.sub("", content(columns=columns, color=color, label="x" * 300))
        assert len(plain) <= columns, columns


def test_wide_characters_count_twice():
    plain = content(columns=40, label="検出" * 50)
    width = sum(2 if "　" <= ch <= "鿿" else 1 for ch in plain)
    assert width <= 40 and "…" in plain


def test_label_is_one_line_without_control_characters():
    text = content(label="a\nb\x1b[31m  c")
    assert "  a b [31m c  " in text and "\n" not in text and "\x1b" not in text


# --- animation: one frame per refresh tick ------------------------------------------------------------------------

def test_spinner_turns_a_quarter_each_tick_the_token_count_grows():
    memory = {}
    seen = [content(memory=memory, tokenCount=n)[0] for n in (1200, 1200, 1300, 1400, 1500, 1600)]
    assert seen == ["◐", "◐", "◓", "◑", "◒", "◐"]


def test_a_running_agent_whose_tokens_stood_still_for_three_ticks_shows_a_hollow_dot():
    assert content(tokenSamples=[900, 1200, 1200, 1200, 1200]).startswith("○ engineer")
    assert content(tokenSamples=[1200, 1200, 1200]).startswith("◐ engineer")  # too few ticks to tell
    assert content(color=True, tokenSamples=[1200] * 4).startswith("\x1b[2;33m○\x1b[0m")


@pytest.mark.parametrize("status, sgr", [("completed", "32"), ("failed", "31"), ("killed", "90")])
def test_a_finished_icon_flashes_then_turns_bold_then_settles(status, sgr):
    memory = {}
    content(memory=memory)
    icons = [ANSI.findall(content(color=True, memory=memory, status=status))[0] for _ in range(3)]
    assert icons == [f"\x1b[1;7;{sgr}m", f"\x1b[1;{sgr}m", f"\x1b[{sgr}m"]


def label_is_dim(text: str) -> bool:
    return "\x1b[2mwriting the failing test" in text


@pytest.mark.parametrize("status, fades", [("completed", True), ("killed", True), ("failed", False)])
def test_done_and_killed_rows_fade_after_the_flash_but_failed_rows_stay_bright(status, fades):
    memory = {}
    content(memory=memory)
    shown = [label_is_dim(content(color=True, memory=memory, status=status)) for _ in range(3)]
    assert shown == [False, False, fades]


def test_a_task_first_seen_finished_does_not_flash():
    text = content(color=True, memory={}, status="completed")
    assert text.startswith("\x1b[32m✓\x1b[0m") and label_is_dim(text)


def test_memory_keeps_only_the_rows_on_screen_and_survives_junk():
    memory = {"gone": ["running", 5, 1, 2], "t1": "junk"}
    assert content(memory=memory).startswith("◐ ")
    assert set(memory) == {"t1"}


# --- colour and bad input -----------------------------------------------------------------------------------------

def test_color_tints_the_row_and_strips_back_to_the_plain_text():
    tinted = rows([task(), task(id="t2", status="completed")], color=True)
    plain = rows([task(), task(id="t2", status="completed")], color=False)
    assert all("\x1b[" in r["content"] for r in tinted)
    assert [ANSI.sub("", r["content"]) for r in tinted] == [r["content"] for r in plain]


def test_rows_without_an_id_keep_the_default_and_bad_rows_do_not_hide_good_ones():
    out = rows([{"agentType": "x"}, "junk", task(id="ok"), task(id="bad", startTime="soon")])
    assert [r["id"] for r in out] == ["ok", "bad"] and out[1]["content"].startswith("◐ engineer")


# --- command line -------------------------------------------------------------------------------------------------

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


def tick(home: Path, session, tokens: int) -> str:
    payload = {"columns": 120, "tasks": [task(tokenCount=tokens)]}
    if session is not None:
        payload["session_id"] = session
    result = run(json.dumps(payload), HOME=str(home), NO_COLOR="1")
    return json.loads(result.stdout)["content"]


def test_cli_remembers_each_session_so_the_spinner_turns_between_runs(tmp_path):
    assert tick(tmp_path, "s-1", 1200)[0] == "◐"
    assert tick(tmp_path, "s-1", 1300)[0] == "◓"
    assert tick(tmp_path, "s-2", 1400)[0] == "◐"  # another session starts its own spinner
    assert sorted(p.name for p in (tmp_path / ".cache/cv-kit/rows").iterdir()) == ["s-1.json", "s-2.json"]


@pytest.mark.parametrize("session", [None, "", "../escape", "a/b"])
def test_cli_without_a_safe_session_id_renders_but_writes_nothing(tmp_path, session):
    assert tick(tmp_path, session, 1200).startswith("◐ engineer")
    assert not (tmp_path / ".cache").exists()


def test_cli_ignores_an_unreadable_memory_file(tmp_path):
    folder = tmp_path / ".cache/cv-kit/rows"
    folder.mkdir(parents=True)
    (folder / "s-1.json").write_text("{not json")
    assert tick(tmp_path, "s-1", 1200).startswith("◐ engineer")


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


def test_register_drops_row_memory_older_than_a_day(tmp_path):
    folder = tmp_path / ".cache/cv-kit/rows"
    folder.mkdir(parents=True)
    old, new = folder / "old.json", folder / "new.json"
    old.write_text("{}"), new.write_text("{}")
    stale = time.time() - 2 * 86400
    os.utime(old, (stale, stale))
    register(tmp_path)
    assert sorted(p.name for p in folder.iterdir()) == ["new.json"]


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
    assert json.loads(result.stdout)["content"].startswith("◐ engineer (sonnet)  x  ")


def test_hooks_json_registers_the_pointer_at_session_start():
    hooks = json.loads((ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]
    args = [" ".join(h.get("args", [])) for g in hooks["SessionStart"] for h in g["hooks"]]
    assert any("agent_status.py" in a and "--register" in a for a in args)
