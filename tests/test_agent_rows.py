"""Agent rows in the status line: hooks log each agent's events, the status line command draws one row per agent."""
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


def call(tu: str, kind: str = "cv-kit:engineer", desc: str = "clamp boxes", **extra) -> dict:
    return {"hook_event_name": "PreToolUse", "session_id": SID, "prompt_id": PROMPT, "tool_name": "Agent",
            "tool_use_id": tu, "tool_input": {"subagent_type": kind, "description": desc, "prompt": "...", **extra}}


def link(tu: str, agent: str) -> dict:
    return {"hook_event_name": "PostToolUse", "session_id": SID, "tool_name": "Agent", "tool_use_id": tu,
            "tool_input": {}, "tool_response": {"status": "async_launched", "agentId": agent}}


def fail(tu: str) -> dict:
    return {"hook_event_name": "PostToolUseFailure", "session_id": SID, "tool_name": "Agent", "tool_use_id": tu,
            "tool_input": {}, "error": "agent crashed"}


def start(agent: str, kind: str = "cv-kit:engineer") -> dict:
    return {"hook_event_name": "SubagentStart", "session_id": SID, "prompt_id": PROMPT, "agent_id": agent,
            "agent_type": kind}


def stop(agent: str, kind: str = "cv-kit:engineer") -> dict:
    return {"hook_event_name": "SubagentStop", "session_id": SID, "agent_id": agent, "agent_type": kind,
            "stop_hook_active": False, "last_assistant_message": "STATUS: done"}


def logged(folder: Path, *events: tuple[dict, float]) -> list[dict]:
    for payload, at in events:
        rows.log_event(payload, at, folder)
    return rows.fold(rows.read_events(folder / f"{SID}.jsonl"))


# --- logging -----------------------------------------------------------------------------------------------------


def test_each_event_appends_one_json_line(tmp_path):
    for payload in (call("tu1"), start("a1"), link("tu1", "a1"), stop("a1"), fail("tu1")):
        rows.log_event(payload, NOW, tmp_path)
    lines = (tmp_path / f"{SID}.jsonl").read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["e"] for line in lines] == ["call", "start", "link", "stop", "fail"]


@pytest.mark.parametrize("payload", [
    {"hook_event_name": "PreToolUse", "session_id": SID, "tool_name": "Bash", "tool_input": {"command": "ls"}},
    {**stop("x"), "agent_type": ""},  # Claude Code's own agents (prompt suggestions, /btw) stop with no type
    {**start("a1"), "session_id": "../escape"},
    {**start("a1"), "session_id": None},
    {"hook_event_name": "Stop", "session_id": SID},
])
def test_other_events_write_nothing(tmp_path, payload):
    rows.log_event(payload, NOW, tmp_path)
    assert not list(tmp_path.iterdir())


def test_a_long_description_is_cut(tmp_path):
    rows.log_event(call("tu1", desc="x" * 1000), NOW, tmp_path)
    assert len(json.loads((tmp_path / f"{SID}.jsonl").read_text(encoding="utf-8"))["desc"]) <= 200


def test_unreadable_lines_are_skipped(tmp_path):
    path = tmp_path / f"{SID}.jsonl"
    path.write_text('{"e": "start", "t": 1, "id": "a1", "type": "Explore"}\nnot json\n[1]\n', encoding="utf-8")
    assert [a["id"] for a in rows.fold(rows.read_events(path))] == ["a1"]


# --- folding events into agents ----------------------------------------------------------------------------------


def test_a_call_and_its_start_make_one_running_agent(tmp_path):
    [agent] = logged(tmp_path, (call("tu1", model="opus", effort="high"), NOW), (start("a1"), NOW + 50))
    assert agent == {"id": "a1", "type": "cv-kit:engineer", "label": "clamp boxes", "model": "opus",
                     "effort": "high", "prompt": PROMPT, "start": NOW + 50, "end": None, "failed": False}


def test_stop_ends_the_agent(tmp_path):
    [agent] = logged(tmp_path, (call("tu1"), NOW), (start("a1"), NOW), (stop("a1"), NOW + 9000))
    assert agent["end"] == NOW + 9000


def test_a_failed_call_ends_its_agent_as_failed(tmp_path):
    [agent] = logged(tmp_path, (call("tu1"), NOW), (start("a1"), NOW), (fail("tu1"), NOW + 3000))
    assert agent["end"] == NOW + 3000 and agent["failed"]


def test_a_failure_does_not_rewrite_a_finished_agent(tmp_path):
    [agent] = logged(tmp_path, (call("tu1"), NOW), (start("a1"), NOW), (stop("a1"), NOW + 1000),
                     (fail("tu1"), NOW + 3000))
    assert agent["end"] == NOW + 1000 and not agent["failed"]


def test_a_resumed_agent_runs_again(tmp_path):
    [agent] = logged(tmp_path, (call("tu1"), NOW), (start("a1"), NOW), (stop("a1"), NOW + 1000),
                     (start("a1"), NOW + 5000))
    assert agent["start"] == NOW + 5000 and agent["end"] is None


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


def test_a_start_without_a_call_still_shows(tmp_path):
    [agent] = logged(tmp_path, (start("a1", kind="Explore"), NOW))
    assert agent["type"] == "Explore" and agent["label"] == "" and agent["prompt"] == PROMPT


def test_a_call_without_a_type_is_general_purpose(tmp_path):
    payload = call("tu1")
    del payload["tool_input"]["subagent_type"]
    [agent] = logged(tmp_path, (payload, NOW), (start("a1", kind="general-purpose"), NOW))
    assert agent["label"] == "clamp boxes"


# --- drawing rows ------------------------------------------------------------------------------------------------


def agent(**over) -> dict:
    base = {"id": "a1", "type": "cv-kit:engineer", "label": "clamp boxes", "model": "sonnet", "effort": "medium",
            "prompt": PROMPT, "start": NOW - 252_000, "end": None}
    return {**base, **over}


def draw(agents, columns=0, prompt=PROMPT, now=NOW) -> list[str]:
    return rows.render(agents, prompt, now, columns=columns, color=False)


def test_a_running_row():
    assert draw([agent()]) == ["◐ engineer (sonnet ▰▰▱▱▱)  clamp boxes  4m12s"]


def test_the_spinner_turns_with_the_clock():
    frames = {draw([agent()], now=NOW + step * 1000)[0][0] for step in range(4)}
    assert frames == set("◐◓◑◒")


def test_a_finished_row_shows_its_duration():
    assert draw([agent(end=NOW - 200_000)]) == ["✓ engineer (sonnet ▰▰▱▱▱)  clamp boxes  52s"]


def test_a_failed_row_stays_bright():
    assert draw([agent(end=NOW - 200_000, failed=True)]) == ["✗ engineer (sonnet ▰▰▱▱▱)  clamp boxes  52s"]
    coloured = rows.render([agent(end=NOW, failed=True)], PROMPT, NOW, columns=0, color=True)[0]
    assert "\x1b[1;31m✗" in coloured and "\x1b[2mengineer" not in coloured


def test_columns_line_up():
    lines = draw([agent(), agent(id="a2", type="cv-kit:claim-verifier", model="haiku", effort="low",
                                 label="re-read", start=NOW - 5000)])
    assert lines == ["◐ engineer (sonnet ▰▰▱▱▱)       clamp boxes  4m12s",
                     "◐ claim-verifier (haiku ▰▱▱▱▱)  re-read         5s"]


def test_the_model_group_drops_what_is_unknown():
    assert draw([agent(type="Explore", model="", effort="")]) == ["◐ Explore  clamp boxes  4m12s"]
    assert draw([agent(effort="")]) == ["◐ engineer (sonnet)  clamp boxes  4m12s"]
    assert draw([agent(model="claude-opus-5-5")])[0].startswith("◐ engineer (opus ▰▰▱▱▱)")


def test_a_cv_kit_agent_without_a_model_gets_its_frontmatter_model():
    model = rows.frontmatter_model("cv-kit:explorer")
    assert model in {"haiku", "sonnet", "opus"}
    assert draw([agent(type="cv-kit:explorer", model="", effort="")])[0].startswith(f"◐ explorer ({model})")
    assert rows.frontmatter_model("Explore") == "" and rows.frontmatter_model("cv-kit:../x") == ""


def test_finished_rows_of_earlier_prompts_are_hidden_but_running_ones_stay():
    agents = [agent(id="old-done", prompt="p-0", end=NOW - 1000), agent(id="old-running", prompt="p-0", label="bg"),
              agent(id="new-done", label="now", end=NOW - 1000)]
    assert [line.split("  ")[1] for line in draw(agents)] == ["bg", "now"]


def test_without_a_prompt_id_finished_rows_show_for_a_minute():
    agents = [agent(id="a", label="recent", end=NOW - 30_000), agent(id="b", label="stale", end=NOW - 90_000)]
    assert [line.split("  ")[1] for line in draw(agents, prompt=None)] == ["recent"]


def test_running_rows_come_first_and_the_rest_is_counted():
    agents = [agent(id=f"d{i}", label=f"done{i}", end=NOW) for i in range(3)]
    agents += [agent(id=f"r{i}", label=f"run{i}") for i in range(rows.MAX_ROWS)]
    lines = draw(agents)
    assert len(lines) == rows.MAX_ROWS + 1 and lines[0].split("  ")[1] == "run0"
    assert lines[-1] == "+3 more"


def test_a_narrow_terminal_cuts_the_label_then_the_group():
    assert draw([agent(label="writing the failing test for clamp")], columns=48) == \
        ["◐ engineer (sonnet ▰▰▱▱▱)  writing the f…  4m12s"]
    narrow = draw([agent(label="writing the failing test")], columns=26)[0]
    assert narrow.startswith("◐ engineer  ") and len(narrow) <= 26


def test_control_characters_in_a_label_are_flattened():
    assert draw([agent(label="a\nb\x1b[31mc")])[0] == "◐ engineer (sonnet ▰▰▱▱▱)  a b [31mc  4m12s"


def test_colour_codes_only_when_asked():
    plain = draw([agent()])
    coloured = rows.render([agent()], PROMPT, NOW, columns=0, color=True)
    assert "\x1b[" in coloured[0] and re.sub(r"\x1b\[[0-9;]*m", "", coloured[0]) == plain[0]


def test_no_agents_draw_nothing():
    assert draw([]) == []


# --- the command line --------------------------------------------------------------------------------------------


def run(home: Path, *args: str, stdin: str = "", env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], input=stdin, capture_output=True, text=True,
                          timeout=20, env={**os.environ, "HOME": str(home), "NO_COLOR": "1", **(env or {})})


def hook(home: Path, payload: dict) -> subprocess.CompletedProcess:
    return run(home, "--event", stdin=json.dumps(payload))


def test_hooks_then_status_line(tmp_path):
    for payload in (call("tu1", model="sonnet", effort="high"), start("a1")):
        assert hook(tmp_path, payload).stdout == ""
    result = run(tmp_path, stdin=json.dumps({"session_id": SID, "prompt_id": PROMPT}), env={"COLUMNS": "80"})
    assert result.returncode == 0
    assert re.fullmatch(r"[◐◓◑◒] engineer \(sonnet ▰▰▰▱▱\)  clamp boxes  \d+s\n", result.stdout)


def test_the_hook_never_fails(tmp_path):
    home = tmp_path / "file"
    home.write_text("not a folder")
    for stdin in ("not json", json.dumps(start("a1"))):
        result = run(home, "--event", stdin=stdin)
        assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


def test_the_status_line_prints_nothing_without_agents_or_input(tmp_path):
    for stdin in ("", "not json", json.dumps({"session_id": SID}), json.dumps({"session_id": "../x"})):
        result = run(tmp_path, stdin=stdin)
        assert (result.returncode, result.stdout) == (0, "")


def test_register_writes_the_plugin_root_and_drops_old_logs(tmp_path):
    folder = tmp_path / ".cache/cv-kit/agents"
    folder.mkdir(parents=True)
    old, new = folder / "old.jsonl", folder / "new.jsonl"
    old.write_text(""), new.write_text("")
    stale = time.time() - 2 * 86400
    os.utime(old, (stale, stale))
    result = run(tmp_path, "--register", stdin='{"hook_event_name": "SessionStart"}')
    assert (result.returncode, result.stdout) == (0, "")
    assert (tmp_path / ".cache/cv-kit/agent-rows-root").read_text(encoding="utf-8") == str(ROOT)
    assert not (tmp_path / ".cache/cv-kit/plugin-root").exists()  # 0.9.1 and older write that one
    assert sorted(p.name for p in folder.iterdir()) == ["new.jsonl"]


# --- wiring and docs ---------------------------------------------------------------------------------------------


def handlers(event: str) -> list[tuple[str | None, dict]]:
    hooks = json.loads((ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]
    return [(g.get("matcher"), h) for g in hooks.get(event, []) for h in g["hooks"]]


@pytest.mark.parametrize("event, matcher, flag", [("SessionStart", "startup|resume|clear|compact", "--register"),
                                                  ("PreToolUse", "Agent", "--event"),
                                                  ("PostToolUse", "Agent", "--event"),
                                                  ("PostToolUseFailure", "Agent", "--event"),
                                                  ("SubagentStart", None, "--event"),
                                                  ("SubagentStop", None, "--event")])
def test_hooks_json_wires_the_logger(event, matcher, flag):
    found = [(m, h) for m, h in handlers(event) if "agent_rows.py" in " ".join(h.get("args", []))]
    assert [(m, h["args"][-1]) for m, h in found] == [(matcher, flag)]
    assert all(h["command"] == "python3" and "onFailure" not in h for _, h in found)


def settings_snippet() -> dict:
    text = (ROOT / "hooks/README.md").read_text(encoding="utf-8")
    blocks = [json.loads(b) for b in re.findall(r"```json\n(.*?)```", text, re.S) if '"statusLine"' in b]
    assert len(blocks) == 1
    return blocks[0]["statusLine"]


def test_the_documented_setting_draws_rows_after_register(tmp_path):
    line = settings_snippet()
    assert line["type"] == "command" and line["refreshInterval"] >= 1
    run(tmp_path, "--register")
    hook(tmp_path, start("a1", kind="Explore"))
    stdin = json.dumps({"session_id": SID, "prompt_id": PROMPT})
    result = subprocess.run(["sh", "-c", line["command"]], input=stdin, capture_output=True, text=True, timeout=20,
                            cwd=tmp_path, env={**os.environ, "HOME": str(tmp_path), "NO_COLOR": "1"})
    assert re.match("[◐◓◑◒] Explore", result.stdout)


def own_line_snippet() -> str:
    text = (ROOT / "hooks/README.md").read_text(encoding="utf-8")
    [block] = [b for b in re.findall(r"```sh\n(.*?)```", text, re.S) if "YOUR_COMMAND" in b]
    return block.strip()


@pytest.mark.parametrize("registered", [True, False])
def test_the_documented_own_line_form_keeps_your_line(tmp_path, registered):
    if registered:
        run(tmp_path, "--register")
    hook(tmp_path, start("a1", kind="Explore"))
    command = own_line_snippet().replace("YOUR_COMMAND", "read -r x; echo mine")
    result = subprocess.run(["sh", "-c", command], input=json.dumps({"session_id": SID, "prompt_id": PROMPT}) + "\n",
                            capture_output=True, text=True, timeout=20, cwd=tmp_path,
                            env={**os.environ, "HOME": str(tmp_path), "NO_COLOR": "1"})
    lines = result.stdout.splitlines()
    assert result.returncode == 0  # a status line that exits non-zero goes blank, your line with it
    assert lines[0] == "mine"
    assert (len(lines) == 2 and re.match("[◐◓◑◒] Explore", lines[1])) if registered else lines == ["mine"]


def test_the_documented_setting_exits_0_before_any_register(tmp_path):
    result = subprocess.run(["sh", "-c", settings_snippet()["command"]], input="{}", capture_output=True, text=True,
                            timeout=20, cwd=tmp_path, env={**os.environ, "HOME": str(tmp_path)})
    assert (result.returncode, result.stdout) == (0, "")


def test_the_documented_setting_refreshes_every_second():
    assert settings_snippet()["refreshInterval"] == 1


def test_the_readme_points_to_the_setting():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "agent_rows.py" in text and "statusLine" in text
