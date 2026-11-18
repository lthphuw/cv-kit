"""cv-kit's status line draws one row, for the main session; the built-in agent panel lists the subagents."""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "hooks/agent_rows.py"
sys.path.insert(0, str(ROOT / "hooks"))

import agent_rows as rows  # noqa: E402

SID, PROMPT = "s-1", "p-1"


# --- drawing -----------------------------------------------------------------------------------------------------

MAIN = {"model": {"id": "claude-opus-5-5", "display_name": "Opus"}, "effort": {"level": "high"},
        "context_window": {"used_percentage": 32, "context_window_size": 200_000},
        "cost": {"total_cost_usd": 0.4213, "total_duration_ms": 725_000, "total_lines_added": 156,
                 "total_lines_removed": 23}}
MAIN_ROW = "● main opus ▰▰▰▱▱  ctx ▰▰▰▱▱▱▱▱▱▱ 32% of 200k  $0.42  +156 −23  12m"


def draw(main, columns=0, ascii=False) -> list[str]:
    return rows.render(main, columns=columns, color=False, ascii=ascii)


def test_the_main_row_alone():
    assert draw(MAIN) == [MAIN_ROW]


def test_the_main_row_without_data_is_left_out():
    assert draw({}) == [] and draw(None) == []


def test_the_main_row_handles_missing_and_null_fields():
    line = draw({"model": {"display_name": "Sonnet 5.5"}, "context_window": {"used_percentage": None}})[0]
    assert line == "● main sonnet  ctx —"
    line = draw({**MAIN, "fast_mode": True, "cost": {"total_cost_usd": 123.4, "total_duration_ms": 3_900_000}})
    assert "opus⚡" in line[0] and "$123" in line[0] and line[0].endswith("1h05m") and "+0" not in line[0]


def test_a_nan_cost_or_context_is_left_out():
    line = draw({"model": {"id": "claude-opus-5-5"}, "context_window": {"used_percentage": float("nan")},
                 "cost": {"total_cost_usd": float("nan"), "total_duration_ms": float("nan")}})[0]
    assert "nan" not in line.lower()


@pytest.mark.parametrize("pct, colour", [(32, "32"), (65, "33"), (91, "31")])
def test_the_context_bar_turns_yellow_then_red(pct, colour):
    main = {**MAIN, "context_window": {"used_percentage": pct, "context_window_size": 1_000_000}}
    line = rows.render(main, color=True)[0]
    assert f"\x1b[{colour}m▰" in line and f"{pct}%" in line and "of 1M" in line


def test_a_narrow_terminal_shortens_the_cells_then_drops_the_cost():
    [line] = draw(MAIN, columns=50)
    assert len(line) <= 50 and "ctx ▰▰▱▱▱ 32%" in line and "$0.42" in line and "+156" not in line
    [line] = draw(MAIN, columns=40)
    assert len(line) <= 40 and "ctx ▰▰▱▱▱ 32%" in line and "$0.42" not in line and line.endswith("12m")


def test_the_narrowest_terminal_keeps_icon_name_and_time():
    [line] = draw(MAIN, columns=18)
    assert len(line) <= 18 and line.startswith("● main") and line.endswith("12m")


def test_ascii_glyphs():
    [line] = draw(MAIN, ascii=True)
    assert line.isascii() and line.startswith("* main") and "ctx ###-------" in line


def test_clip_drops_the_padding_before_the_ellipsis():
    assert rows.clip([("ab", ""), ("    ", ""), ("cdef", "")], 7) == [("ab", ""), ("…", "")]


def test_colour_codes_only_when_asked():
    [coloured] = rows.render(MAIN, color=True)
    assert "\x1b[" in coloured and re.sub(r"\x1b\[[0-9;]*m", "", coloured) == MAIN_ROW


# --- the command line --------------------------------------------------------------------------------------------


def run(home: Path, *args: str, stdin: str = "", env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], input=stdin.encode("utf-8"), capture_output=True,
                          timeout=30, env={**os.environ, "HOME": str(home), "USERPROFILE": str(home), "NO_COLOR": "1",
                                           **(env or {})})


STDIN = json.dumps({"session_id": SID, "prompt_id": PROMPT, **MAIN})


def test_the_status_line_is_the_main_row(tmp_path):
    result = run(tmp_path, stdin=STDIN, env={"COLUMNS": "100", "PYTHONIOENCODING": "cp1252"})  # a Windows console
    assert (result.returncode, result.stdout.decode("utf-8").splitlines()) == (0, [MAIN_ROW])


def test_running_subagents_add_no_rows_to_the_status_line(tmp_path):
    folder = tmp_path / ".cache/cv-kit/agents"
    folder.mkdir(parents=True)
    events = [{"e": "start", "t": time.time() * 1000, "id": f"a{i}", "type": "cv-kit:engineer", "p": PROMPT}
              for i in range(9)]  # the log an older version wrote: nine agents running
    (folder / f"{SID}.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    result = run(tmp_path, stdin=STDIN, env={"COLUMNS": "100"})
    assert result.stdout.decode("utf-8").splitlines() == [MAIN_ROW]  # the built-in agent panel lists them


def test_ascii_flag_and_the_old_no_main_flag(tmp_path):
    out = run(tmp_path, "--ascii", "--no-main", stdin=STDIN).stdout.decode()  # --no-main is gone: it is ignored
    assert out.isascii() and out.startswith("* main ") and len(out.splitlines()) == 1


def test_the_status_line_prints_nothing_without_input(tmp_path):
    for stdin in ("", "not json", "[]", "{}"):
        result = run(tmp_path, stdin=stdin)
        assert (result.returncode, result.stdout) == (0, b"")


def test_register_writes_the_plugin_root_and_drops_old_logs(tmp_path):
    folder, legacy = tmp_path / ".cache/cv-kit/agents", tmp_path / ".cache/cv-kit/rows"
    folder.mkdir(parents=True), legacy.mkdir(parents=True)
    old, new, older = folder / "old.jsonl", folder / "new.jsonl", legacy / "s.json"  # left by 0.11 and by 0.9.1
    old.write_text(""), new.write_text(""), older.write_text("{}")
    stale = time.time() - 2 * 86400
    os.utime(old, (stale, stale)), os.utime(older, (stale, stale))
    result = run(tmp_path, "--register", stdin='{"hook_event_name": "SessionStart"}')
    assert (result.returncode, result.stdout) == (0, b"")
    assert (tmp_path / ".cache/cv-kit/agent-rows-root").read_text(encoding="utf-8") == str(ROOT)
    assert not (tmp_path / ".cache/cv-kit/plugin-root").exists()  # 0.9.1 and older write that one
    assert sorted(p.name for p in folder.iterdir()) == ["new.jsonl"] and not older.exists()


def test_register_logs_nothing_at_resume(tmp_path):
    result = run(tmp_path, "--register", stdin=json.dumps({"hook_event_name": "SessionStart", "session_id": SID,
                                                          "source": "resume"}))
    assert (result.returncode, result.stdout) == (0, b"")
    assert not (tmp_path / ".cache/cv-kit/agents").exists()


def test_register_refreshes_an_installed_launcher(tmp_path):
    launcher = tmp_path / ".claude/cv-kit/statusline.py"
    launcher.parent.mkdir(parents=True)
    launcher.write_text("old", encoding="utf-8")
    run(tmp_path, "--register", stdin="{}")
    assert launcher.read_bytes() == (ROOT / "hooks/statusline_launcher.py").read_bytes()
    run(tmp_path / "other", "--register", stdin="{}")
    assert not (tmp_path / "other/.claude/cv-kit/statusline.py").exists()  # never installs one by itself


# --- wiring ------------------------------------------------------------------------------------------------------


def test_hooks_json_runs_agent_rows_only_to_register():
    hooks = json.loads((ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]
    found = [(event, g.get("matcher"), h["args"][1:], h.get("async", False), h["command"], "onFailure" in h)
             for event, groups in hooks.items() for g in groups for h in g["hooks"]
             if "agent_rows.py" in " ".join(h.get("args", []))]
    assert found == [("SessionStart", "startup|resume|clear|compact", ["--register"], False, "python3", False)]
