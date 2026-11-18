"""cv-kit's status line: hooks log agent events; the status line draws the main session and the agents on one grid."""
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
NOW = 1_800_000_000_000
SPIN = "[◐◓◑◒]"


# --- hook payloads -----------------------------------------------------------------------------------------------


def call(tu: str, kind: str = "cv-kit:engineer", desc: str = "clamp boxes", **extra) -> dict:
    return {"hook_event_name": "PreToolUse", "session_id": SID, "prompt_id": PROMPT, "tool_name": "Agent",
            "tool_use_id": tu, "tool_input": {"subagent_type": kind, "description": desc, "prompt": "...", **extra}}


def link(tu: str, agent: str, status: str = "completed") -> dict:
    return {"hook_event_name": "PostToolUse", "session_id": SID, "tool_name": "Agent", "tool_use_id": tu,
            "tool_input": {}, "tool_response": {"status": status, "agentId": agent}}


def fail(tu: str) -> dict:
    return {"hook_event_name": "PostToolUseFailure", "session_id": SID, "tool_name": "Agent", "tool_use_id": tu,
            "tool_input": {}, "error": "agent crashed"}


def start(agent: str, kind: str = "cv-kit:engineer", prompt: str = PROMPT) -> dict:
    return {"hook_event_name": "SubagentStart", "session_id": SID, "prompt_id": prompt, "agent_id": agent,
            "agent_type": kind}


def stop(agent: str, kind: str = "cv-kit:engineer", message: str = "STATUS: done — 4 tests pass") -> dict:
    return {"hook_event_name": "SubagentStop", "session_id": SID, "agent_id": agent, "agent_type": kind,
            "stop_hook_active": False, "last_assistant_message": message}


def resume() -> dict:
    return {"hook_event_name": "SessionStart", "session_id": SID, "source": "resume"}


def tool(agent: str, name: str, tool_input: dict, tu: str = "t1", event: str = "PreToolUse") -> dict:
    return {"hook_event_name": event, "session_id": SID, "agent_id": agent, "agent_type": "cv-kit:engineer",
            "tool_name": name, "tool_use_id": tu, "tool_input": tool_input}


def logged(folder: Path, *events: tuple[dict, float], activity: tuple[tuple[dict, float], ...] = ()) -> list[dict]:
    for payload, at in events:
        rows.log_event(payload, at, folder)
    for payload, at in activity:
        rows.log_event(payload, at, folder, activity=True)
    return rows.fold(rows.read_events(folder / f"{SID}.jsonl"))


def kinds(folder: Path) -> list[str]:
    return [json.loads(line)["e"] for line in (folder / f"{SID}.jsonl").read_text(encoding="utf-8").splitlines()]


# --- logging -----------------------------------------------------------------------------------------------------


def test_each_event_appends_one_json_line(tmp_path):
    for payload in (call("tu1"), start("a1"), link("tu1", "a1"), stop("a1"), fail("tu1"), resume()):
        rows.log_event(payload, NOW, tmp_path)
    assert kinds(tmp_path) == ["call", "start", "link", "stop", "fail", "reset"]


@pytest.mark.parametrize("payload", [
    {"hook_event_name": "PreToolUse", "session_id": SID, "tool_name": "Bash", "tool_input": {"command": "ls"}},
    {**stop("x"), "agent_type": ""},  # Claude Code's own agents (prompt suggestions, /btw) stop with no type
    {**start("a1"), "session_id": "../escape"},
    {**start("a1"), "session_id": None},
    {"hook_event_name": "Stop", "session_id": SID},
    {**call("tu1"), "tool_name": "Task"},
    {**resume(), "source": "startup"},
])
def test_other_events_write_nothing(tmp_path, payload):
    rows.log_event(payload, NOW, tmp_path)
    assert not list(tmp_path.iterdir())


def test_activity_logs_only_tools_a_subagent_calls(tmp_path):
    main_thread = {**tool("x", "Bash", {"command": "ls"}), "agent_id": None}
    for payload in (main_thread, tool("a1", "Bash", {"command": "ls"}),
                    tool("a1", "Bash", {}, event="PostToolUse"), tool("a1", "Bash", {}, event="PostToolUseFailure"),
                    start("a1")):
        rows.log_event(payload, NOW, tmp_path, activity=True)
    assert kinds(tmp_path) == ["tool", "tooldone", "tooldone"]


@pytest.mark.parametrize("name, tool_input, shown", [
    ("Bash", {"command": "pytest -q tests/test_track.py\necho done"}, "Bash pytest -q tests/test_track.py"),
    ("PowerShell", {"command": "Get-ChildItem"}, "PowerShell Get-ChildItem"),
    ("Edit", {"file_path": "/repo/vision/track.py"}, "Edit track.py"),
    ("Read", {"file_path": "C:\\repo\\io\\writer.py"}, "Read writer.py"),
    ("Grep", {"pattern": "def nms"}, "Grep def nms"),
    ("WebFetch", {"url": "https://arxiv.org/abs/2304.07193"}, "WebFetch arxiv.org"),
    ("WebSearch", {"query": "rf-detr licence"}, "WebSearch rf-detr licence"),
    ("mcp__github__get_issue", {"number": 3}, "get_issue"),
    ("TodoWrite", {"todos": []}, "TodoWrite"),
])
def test_activity_names_the_tool_and_its_main_argument(tmp_path, name, tool_input, shown):
    [agent] = logged(tmp_path, (start("a1"), NOW), activity=((tool("a1", name, tool_input), NOW + 10),))
    assert rows.activity_text(agent["activity"]) == shown


def test_a_handback_report_is_the_outcome(tmp_path):
    handback = tool("a1", "SubagentHandback", {"message": "STATUS: blocked — torch not installed\nmore"})
    [agent] = logged(tmp_path, (start("a1"), NOW), activity=((handback, NOW + 10),))
    assert (agent["outcome"], agent["summary"]) == ("blocked", "torch not installed")


def test_a_long_description_is_cut(tmp_path):
    rows.log_event(call("tu1", desc="x" * 1000), NOW, tmp_path)
    assert len(json.loads((tmp_path / f"{SID}.jsonl").read_text(encoding="utf-8"))["desc"]) <= 200


def test_a_long_log_parses_only_its_recent_tool_lines(tmp_path, monkeypatch):
    monkeypatch.setattr(rows, "TOOL_LINES", 5)
    for i in range(20):
        rows.log_event(tool("a1", "Bash", {"command": f"step {i}"}, tu=f"t{i}"), NOW + i, tmp_path, activity=True)
    rows.log_event(start("a1"), NOW - 1, tmp_path)
    events = rows.read_events(tmp_path / f"{SID}.jsonl")
    assert [e["e"] for e in events].count("tool") == 5 and events[-1]["e"] == "start"
    [agent] = rows.fold(events)
    assert agent["activity"]["arg"] == "step 19"


def test_unreadable_lines_are_skipped(tmp_path):
    path = tmp_path / f"{SID}.jsonl"
    path.write_text('{"e": "start", "t": 1, "id": "a1", "type": "Explore"}\nnot json\n[1]\n', encoding="utf-8")
    assert [a["id"] for a in rows.fold(rows.read_events(path))] == ["a1"]


def test_appends_from_many_processes_stay_whole(tmp_path):
    code = ("import sys; sys.path.insert(0, sys.argv[1]); import agent_rows as r; from pathlib import Path\n"
            "for i in range(40): r.log_event({'hook_event_name': 'SubagentStart', 'session_id': 's-1', "
            "'agent_id': f'{sys.argv[3]}-{i}', 'agent_type': 'x' * 300}, 1, Path(sys.argv[2]))")
    procs = [subprocess.Popen([sys.executable, "-c", code, str(ROOT / "hooks"), str(tmp_path), str(n)])
             for n in range(6)]
    assert all(p.wait(timeout=60) == 0 for p in procs)
    lines = (tmp_path / f"{SID}.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 240 and all(json.loads(line)["e"] == "start" for line in lines)


# --- STATUS lines ------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("text, expected", [
    ("STATUS: done — 4 tests pass", ("done", "4 tests pass")),
    ("**STATUS: failed** - pytest not found", ("failed", "pytest not found")),
    ("Intro line\nstatus: Blocked: needs a GPU\n", ("blocked", "needs a GPU")),
    ("STATUS: done", ("done", "")),
    ("STATUS: done\n\n## Findings\n- x", ("done", "")),  # the next line is not the summary
    ("All good, nothing to report", None),
    (None, None),
])
def test_status_lines(text, expected):
    assert rows.outcome(text) == expected


# --- folding events into agents ----------------------------------------------------------------------------------


def test_a_call_and_its_start_make_one_running_agent(tmp_path):
    [agent] = logged(tmp_path, (call("tu1", model="opus", effort="high"), NOW), (start("a1"), NOW + 50))
    assert agent == {"id": "a1", "type": "cv-kit:engineer", "label": "clamp boxes", "model": "opus",
                     "effort": "high", "prompt": PROMPT, "start": NOW + 50, "end": None, "failed": False,
                     "lost": False, "background": False, "activity": None, "outcome": None, "summary": ""}


def test_stop_ends_the_agent_with_its_status_line(tmp_path):
    [agent] = logged(tmp_path, (call("tu1"), NOW), (start("a1"), NOW), (stop("a1"), NOW + 9000))
    assert (agent["end"], agent["outcome"], agent["summary"]) == (NOW + 9000, "done", "4 tests pass")


def test_a_failed_call_ends_its_agent_as_failed(tmp_path):
    [agent] = logged(tmp_path, (call("tu1"), NOW), (start("a1"), NOW), (fail("tu1"), NOW + 3000))
    assert agent["end"] == NOW + 3000 and agent["failed"]


def test_a_failure_does_not_rewrite_a_finished_agent(tmp_path):
    [agent] = logged(tmp_path, (call("tu1"), NOW), (start("a1"), NOW), (stop("a1"), NOW + 1000),
                     (fail("tu1"), NOW + 3000))
    assert agent["end"] == NOW + 1000 and not agent["failed"]


def test_a_call_that_failed_before_starting_pairs_with_nothing(tmp_path):
    first = call("tu1", desc="bad call")
    second = {**call("tu2", desc="real"), "prompt_id": "p-2"}
    [agent] = logged(tmp_path, (first, NOW), (fail("tu1"), NOW + 2), (second, NOW + 5),
                     (start("a1", prompt="p-2"), NOW + 11))
    assert (agent["label"], agent["end"], agent["failed"], agent["prompt"]) == ("real", None, False, "p-2")


def test_a_call_that_never_started_does_not_pair_with_a_later_prompt(tmp_path):
    [agent] = logged(tmp_path, (call("tu1", desc="denied"), NOW),
                     ({**call("tu2", desc="real"), "prompt_id": "p-2"}, NOW + 5), (start("a1", prompt="p-2"), NOW + 11))
    assert agent["label"] == "real"


def test_a_session_resume_ends_the_agents_left_running(tmp_path):
    rows.log_event(resume(), NOW, tmp_path)
    agents = logged(tmp_path, (start("a1"), NOW), (start("a2"), NOW), (stop("a2"), NOW + 1000),
                    (resume(), NOW + 5000), (start("a3"), NOW + 6000))
    assert [(a["id"], a["end"], a["lost"]) for a in agents] == [("a1", NOW + 5000, True), ("a2", NOW + 1000, False),
                                                                 ("a3", None, False)]


def test_post_tool_use_at_launch_marks_a_background_agent(tmp_path):
    [agent] = logged(tmp_path, (call("tu1"), NOW), (start("a1"), NOW), (link("tu1", "a1", "async_launched"), NOW))
    assert agent["background"]


def test_a_start_without_a_time_does_not_break_the_others(tmp_path):
    path = tmp_path / f"{SID}.jsonl"
    path.write_text('{"e": "call", "t": 5, "type": "x"}\n{"e": "start", "id": "A", "type": "x"}\n'
                    '{"e": "start", "t": 9, "id": "B", "type": "x", "p": "p-1"}\n', encoding="utf-8")
    agents = rows.fold(rows.read_events(path))
    assert [a["id"] for a in agents] == ["A", "B"]
    assert re.match(f"{SPIN} x", draw(agents)[0])


def test_an_agent_resumed_under_a_later_prompt_belongs_to_it(tmp_path):
    [agent] = logged(tmp_path, (call("tu1"), NOW), (start("a1"), NOW), (stop("a1"), NOW + 1000),
                     (start("a1", prompt="p-2"), NOW + 5000), (stop("a1", message="no status"), NOW + 9000))
    assert agent["prompt"] == "p-2" and agent["outcome"] is None  # the first run's STATUS is not this run's


def test_parallel_calls_of_one_type_pair_in_order(tmp_path):
    agents = logged(tmp_path, (call("tu1", desc="first"), NOW), (call("tu2", desc="second"), NOW),
                    (start("a1"), NOW + 10), (start("a2"), NOW + 20))
    assert [(a["id"], a["label"]) for a in agents] == [("a1", "first"), ("a2", "second")]


def test_the_agent_id_from_post_tool_use_wins_over_order(tmp_path):
    agents = logged(tmp_path, (call("tu1", desc="first"), NOW), (call("tu2", desc="second"), NOW),
                    (start("a1"), NOW + 10), (start("a2"), NOW + 20), (link("tu2", "agent-a1"), NOW + 30))
    assert [(a["id"], a["label"]) for a in agents] == [("a1", "second"), ("a2", "first")]


def test_a_call_pairs_only_with_its_own_type(tmp_path):
    agents = logged(tmp_path, (call("tu1", kind="cv-kit:explorer", desc="look"), NOW),
                    (call("tu2", desc="build"), NOW), (start("a1"), NOW + 10),
                    (start("a2", kind="cv-kit:explorer"), NOW + 20))
    assert {a["id"]: a["label"] for a in agents} == {"a1": "build", "a2": "look"}


def test_a_call_without_a_type_is_general_purpose(tmp_path):
    payload = call("tu1")
    del payload["tool_input"]["subagent_type"]
    [agent] = logged(tmp_path, (payload, NOW), (start("a1", kind="general-purpose"), NOW))
    assert agent["label"] == "clamp boxes"


def test_the_latest_tool_is_the_activity_and_its_end_means_thinking(tmp_path):
    activity = ((tool("a1", "Read", {"file_path": "a.py"}, tu="t1"), NOW + 10),
                (tool("a1", "Read", {}, tu="t1", event="PostToolUse"), NOW + 20),
                (tool("a1", "Bash", {"command": "pytest"}, tu="t2"), NOW + 30))
    [agent] = logged(tmp_path, (start("a1"), NOW), activity=activity)
    assert agent["activity"] == {"tool": "Bash", "arg": "pytest", "t": NOW + 30, "done": False}
    [agent] = logged(tmp_path, activity=((tool("a1", "Bash", {}, tu="t2", event="PostToolUse"), NOW + 40),))
    assert agent["activity"]["done"]


def test_a_tool_end_logged_before_its_start_still_counts(tmp_path):  # async hooks can land out of order
    activity = ((tool("a1", "Bash", {}, tu="t1", event="PostToolUse"), NOW + 20),
                (tool("a1", "Bash", {"command": "ls"}, tu="t1"), NOW + 10))
    [agent] = logged(tmp_path, (start("a1"), NOW), activity=activity)
    assert agent["activity"]["done"]


def test_tools_of_an_earlier_run_are_not_the_activity_of_a_resumed_one(tmp_path):
    [agent] = logged(tmp_path, (start("a1"), NOW), (stop("a1"), NOW + 100), (start("a1"), NOW + 500),
                     activity=((tool("a1", "Bash", {"command": "ls"}), NOW + 50),))
    assert agent["activity"] is None


# --- drawing -----------------------------------------------------------------------------------------------------

MAIN = {"model": {"id": "claude-opus-5-5", "display_name": "Opus"}, "effort": {"level": "high"},
        "context_window": {"used_percentage": 32, "context_window_size": 200_000},
        "cost": {"total_cost_usd": 0.4213, "total_duration_ms": 725_000, "total_lines_added": 156,
                 "total_lines_removed": 23}}


def agent(**over) -> dict:
    base = {"id": "a1", "type": "cv-kit:engineer", "label": "clamp boxes", "model": "sonnet", "effort": "medium",
            "prompt": PROMPT, "start": NOW - 252_000, "end": None, "failed": False, "lost": False,
            "background": False, "activity": None, "outcome": None, "summary": ""}
    return {**base, **over}


BASH = {"tool": "Bash", "arg": "pytest -q", "t": NOW - 100_000, "done": False}


def draw(agents, columns=0, prompt=PROMPT, now=NOW, main=None, ascii=False) -> list[str]:
    return rows.render(agents, prompt, now, columns=columns, color=False, main=main, ascii=ascii)


def test_a_running_row_before_its_first_tool():
    assert draw([agent()]) == ["◐ engineer sonnet ▰▰▱▱▱  clamp boxes  thinking…  4m12s"]


def test_a_running_row_shows_its_tool_and_how_long_the_tool_has_run():
    assert draw([agent(activity=BASH)]) == ["◐ engineer sonnet ▰▰▱▱▱  clamp boxes  Bash pytest -q  1m40s  4m12s"]


def test_a_short_tool_shows_no_tool_clock():
    assert draw([agent(activity={**BASH, "t": NOW - 4000})]) == \
        ["◐ engineer sonnet ▰▰▱▱▱  clamp boxes  Bash pytest -q  4m12s"]


def test_a_finished_tool_means_thinking():
    assert draw([agent(activity={**BASH, "done": True})]) == ["◐ engineer sonnet ▰▰▱▱▱  clamp boxes  thinking…  4m12s"]


def test_a_running_row_without_a_task_still_shows_its_tool():
    assert draw([agent(label="", activity=BASH)]) == ["◐ engineer sonnet ▰▰▱▱▱  Bash pytest -q  1m40s  4m12s"]


def test_a_nan_cost_or_context_is_left_out():
    line = draw([], main={"model": {"id": "claude-opus-5-5"}, "context_window": {"used_percentage": float("nan")},
                          "cost": {"total_cost_usd": float("nan"), "total_duration_ms": float("nan")}})[0]
    assert "nan" not in line.lower()


def test_the_spinner_turns_with_the_clock():
    assert {draw([agent()], now=NOW + step * 1000)[0][0] for step in range(4)} == set("◐◓◑◒")


@pytest.mark.parametrize("over, icon, text", [
    ({"outcome": "done", "summary": "4 tests pass"}, "✓", "4 tests pass"),
    ({"outcome": "blocked", "summary": "torch not installed"}, "!", "blocked: torch not installed"),
    ({"outcome": "failed", "summary": "pytest not found"}, "✗", "failed: pytest not found"),
    ({"failed": True}, "✗", "clamp boxes"),
    ({"lost": True}, "■", "clamp boxes"),
    ({}, "✓", "clamp boxes"),  # no STATUS line: the task description
])
def test_a_finished_row_shows_its_outcome_and_duration(over, icon, text):
    assert draw([agent(end=NOW - 200_000, activity=BASH, **over)]) == [f"{icon} engineer sonnet ▰▰▱▱▱  {text}  52s"]


def test_the_main_row_alone():
    assert draw([], main=MAIN) == ["● main opus ▰▰▰▱▱  ctx ▰▰▰▱▱▱▱▱▱▱ 32% of 200k  $0.42  +156 −23  12m"]


def test_the_main_row_and_the_agents_share_one_grid():
    lines = draw([agent(activity=BASH), agent(id="a2", type="cv-kit:claim-verifier", model="haiku", effort="low",
                                              label="re-read", start=NOW - 5000),
                  agent(id="a3", end=NOW - 1000, outcome="done", summary="frames at pipeline.py:57")], main=MAIN)
    assert lines[0].startswith("● main           opus   ▰▰▰▱▱  ctx ▰▰▰▱▱▱▱▱▱▱ 32% of 200k  $0.42  +156 −23")
    assert lines[1].startswith("◐ engineer       sonnet ▰▰▱▱▱  " + "clamp boxes".ljust(26) + "  Bash pytest -q")
    assert lines[2].startswith("◐ claim-verifier haiku  ▰▱▱▱▱  " + "re-read".ljust(26) + "  thinking…")
    assert lines[3].startswith("✓ engineer       sonnet ▰▰▱▱▱  frames at pipeline.py:57")
    assert len({len(line) for line in lines}) == 1  # the clocks end on one edge
    assert lines[1].endswith("1m40s  4m12s") and lines[0].endswith("  12m") and lines[3].endswith("  4m11s")


def test_the_main_row_without_data_is_left_out():
    assert draw([agent()], main={}) == draw([agent()])
    assert draw([], main=None) == []


def test_the_main_row_handles_missing_and_null_fields():
    line = draw([], main={"model": {"display_name": "Sonnet 5.5"}, "context_window": {"used_percentage": None}})[0]
    assert line == "● main sonnet  ctx —"
    line = draw([], main={**MAIN, "fast_mode": True, "cost": {"total_cost_usd": 123.4, "total_duration_ms": 3_900_000}})
    assert "opus⚡" in line[0] and "$123" in line[0] and line[0].endswith("1h05m") and "+0" not in line[0]


@pytest.mark.parametrize("pct, colour", [(32, "32"), (65, "33"), (91, "31")])
def test_the_context_bar_turns_yellow_then_red(pct, colour):
    main = {**MAIN, "context_window": {"used_percentage": pct, "context_window_size": 1_000_000}}
    line = rows.render([], PROMPT, NOW, color=True, main=main)[0]
    assert f"\x1b[{colour}m▰" in line and f"{pct}%" in line and "of 1M" in line


def test_a_narrow_terminal_drops_the_tool_clock_then_shrinks_the_columns():
    lines = draw([agent(activity=BASH)], columns=60, main=MAIN)
    assert all(len(line) <= 60 for line in lines)
    assert "ctx ▰▰▱▱▱ 32%" in lines[0] and "$0.42" in lines[0] and "+156" not in lines[0]
    assert "Bash pyte…" in lines[1] and "1m40s" not in lines[1] and lines[1].endswith("4m12s")


def test_a_narrower_terminal_drops_the_activity_then_the_meter():
    lines = draw([agent(activity=BASH)], columns=40, main=MAIN)
    assert all(len(line) <= 40 for line in lines)
    assert "Bash" not in lines[1] and "$0.42" not in lines[0] and "▰▰▱▱▱" not in lines[1]
    assert lines[1].startswith("◐ engineer sonnet  clamp boxes")


def test_the_narrowest_terminal_keeps_icon_name_and_clock():
    lines = draw([agent(activity=BASH)], columns=18, main=MAIN)
    assert all(len(line) <= 18 for line in lines)
    assert lines[1].startswith("◐ engineer") and lines[1].endswith("4m12s")


def test_ascii_glyphs():
    lines = draw([agent(activity=BASH), agent(id="a2", end=NOW, outcome="done", summary="ok")], main=MAIN, ascii=True)
    assert all(line.isascii() for line in lines)
    assert lines[0].startswith("* main") and "ctx ###-------" in lines[0]
    assert re.match(r"[|/\\-] engineer", lines[1]) and lines[2].startswith("+ engineer")


def test_finished_rows_of_earlier_prompts_are_hidden_but_running_background_ones_stay():
    agents = [agent(id="old-done", prompt="p-0", end=NOW - 1000),
              agent(id="old-running", prompt="p-0", label="bg", background=True),
              agent(id="new-done", label="now", end=NOW - 1000)]
    assert [line.split("  ")[1] for line in draw(agents)] == ["bg", "now"]


def test_a_foreground_agent_of_an_earlier_prompt_counts_as_interrupted():
    agents = [agent(id="fg", prompt="p-0", label="fg"), agent(id="bg", prompt="p-0", label="bg", background=True)]
    assert [line.split("  ")[1] for line in draw(agents)] == ["bg"]


def test_without_a_prompt_id_finished_rows_show_for_a_minute():
    agents = [agent(id="a", label="recent", end=NOW - 30_000), agent(id="b", label="stale", end=NOW - 90_000)]
    assert [line.split("  ")[1] for line in draw(agents, prompt=None)] == ["recent"]


def test_running_rows_come_first_and_the_rest_is_counted():
    agents = [agent(id=f"d{i}", label=f"done{i}", end=NOW) for i in range(3)]
    agents += [agent(id=f"r{i}", label=f"run{i}") for i in range(rows.MAX_ROWS)]
    lines = draw(agents, main=MAIN)
    assert len(lines) == rows.MAX_ROWS + 2 and lines[1].split("  ")[1] == "run0" and lines[-1] == "+3 more"


def test_a_cv_kit_agent_without_a_model_gets_its_frontmatter_model():
    model = rows.frontmatter_model("cv-kit:explorer")
    assert model in {"haiku", "sonnet", "opus"}
    assert draw([agent(type="cv-kit:explorer", model="", effort="")])[0].startswith(f"◐ explorer {model}  ")
    assert rows.frontmatter_model("Explore") == "" and rows.frontmatter_model("cv-kit:../x") == ""


def test_control_characters_are_flattened():
    assert "a b [31mc" in draw([agent(label="a\nb\x1b[31mc")])[0]


def test_clip_drops_the_padding_before_the_ellipsis():
    assert rows.clip([("ab", ""), ("    ", ""), ("cdef", "")], 7) == [("ab", ""), ("…", "")]


def test_colour_codes_only_when_asked():
    coloured = rows.render([agent(activity=BASH)], PROMPT, NOW, color=True, main=MAIN)
    assert all("\x1b[" in line for line in coloured)
    assert [re.sub(r"\x1b\[[0-9;]*m", "", line) for line in coloured] == draw([agent(activity=BASH)], main=MAIN)


# --- the command line --------------------------------------------------------------------------------------------


def run(home: Path, *args: str, stdin: str = "", env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], input=stdin.encode("utf-8"), capture_output=True,
                          timeout=30, env={**os.environ, "HOME": str(home), "USERPROFILE": str(home), "NO_COLOR": "1",
                                           **(env or {})})


def hook(home: Path, payload: dict, flag: str = "--event") -> subprocess.CompletedProcess:
    return run(home, flag, stdin=json.dumps(payload))


def test_hooks_then_status_line(tmp_path):
    for payload in (call("tu1", model="sonnet", effort="high"), start("a1")):
        assert hook(tmp_path, payload).stdout == b""
    hook(tmp_path, tool("a1", "Bash", {"command": "pytest -q"}), "--activity")
    result = run(tmp_path, stdin=json.dumps({"session_id": SID, "prompt_id": PROMPT, **MAIN}),
                 env={"COLUMNS": "100", "PYTHONIOENCODING": "cp1252"})  # a Windows console's default encoding
    lines = result.stdout.decode("utf-8").splitlines()
    assert result.returncode == 0 and lines[0].startswith("● main ")
    assert re.fullmatch(rf"{SPIN} engineer sonnet ▰▰▰▱▱  clamp boxes +Bash pytest -q +\d+s", lines[1])


def test_ascii_flag_and_no_main_flag(tmp_path):
    hook(tmp_path, start("a1", kind="Explore"))
    stdin = json.dumps({"session_id": SID, "prompt_id": PROMPT, **MAIN})
    out = run(tmp_path, "--ascii", "--no-main", stdin=stdin).stdout.decode()
    assert out.isascii() and re.match(r"[|/\\-] Explore", out)


def test_the_hook_never_fails(tmp_path):
    home = tmp_path / "file"
    home.write_text("not a folder")
    for flag in ("--event", "--activity"):
        for stdin in ("not json", json.dumps(start("a1")), json.dumps(tool("a1", "Bash", {}))):
            result = run(home, flag, stdin=stdin)
            assert (result.returncode, result.stdout, result.stderr) == (0, b"", b"")


def test_the_status_line_prints_nothing_without_agents_or_input(tmp_path):
    for stdin in ("", "not json", json.dumps({"session_id": SID}), json.dumps({"session_id": "../x"})):
        result = run(tmp_path, stdin=stdin)
        assert (result.returncode, result.stdout) == (0, b"")


def test_register_writes_the_plugin_root_and_drops_old_logs(tmp_path):
    folder, legacy = tmp_path / ".cache/cv-kit/agents", tmp_path / ".cache/cv-kit/rows"
    folder.mkdir(parents=True), legacy.mkdir(parents=True)
    old, new, older = folder / "old.jsonl", folder / "new.jsonl", legacy / "s.json"  # rows/ is 0.9.1's memory
    old.write_text(""), new.write_text(""), older.write_text("{}")
    stale = time.time() - 2 * 86400
    os.utime(old, (stale, stale)), os.utime(older, (stale, stale))
    result = run(tmp_path, "--register", stdin='{"hook_event_name": "SessionStart"}')
    assert (result.returncode, result.stdout) == (0, b"")
    assert (tmp_path / ".cache/cv-kit/agent-rows-root").read_text(encoding="utf-8") == str(ROOT)
    assert not (tmp_path / ".cache/cv-kit/plugin-root").exists()  # 0.9.1 and older write that one
    assert sorted(p.name for p in folder.iterdir()) == ["new.jsonl"] and not older.exists()


def test_register_at_resume_logs_the_reset(tmp_path):
    run(tmp_path, "--register", stdin=json.dumps(resume()))
    assert kinds(tmp_path / ".cache/cv-kit/agents") == ["reset"]


def test_register_refreshes_an_installed_launcher(tmp_path):
    launcher = tmp_path / ".claude/cv-kit/statusline.py"
    launcher.parent.mkdir(parents=True)
    launcher.write_text("old", encoding="utf-8")
    run(tmp_path, "--register", stdin="{}")
    assert launcher.read_bytes() == (ROOT / "hooks/statusline_launcher.py").read_bytes()
    run(tmp_path / "other", "--register", stdin="{}")
    assert not (tmp_path / "other/.claude/cv-kit/statusline.py").exists()  # never installs one by itself


# --- wiring ------------------------------------------------------------------------------------------------------


def handlers(event: str) -> list[tuple[str | None, dict]]:
    hooks = json.loads((ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]
    return [(g.get("matcher"), h) for g in hooks.get(event, []) for h in g["hooks"]]


@pytest.mark.parametrize("event, wired", [
    ("SessionStart", [("startup|resume|clear|compact", "--register", False)]),
    ("PreToolUse", [("Agent", "--event", False), (None, "--activity", True)]),
    ("PostToolUse", [("Agent", "--event", False), (None, "--activity", True)]),
    ("PostToolUseFailure", [("Agent", "--event", False), (None, "--activity", True)]),
    ("SubagentStart", [(None, "--event", False)]),
    ("SubagentStop", [(None, "--event", False)]),
])
def test_hooks_json_wires_the_logger(event, wired):
    found = [(m, h) for m, h in handlers(event) if "agent_rows.py" in " ".join(h.get("args", []))]
    assert [(m, h["args"][-1], h.get("async", False)) for m, h in found] == wired
    assert all(h["command"] == "python3" and "onFailure" not in h for _, h in found)
