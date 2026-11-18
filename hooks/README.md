# Commit hook

`block_trailers.py` runs before each Bash command. If the command is a `git commit` or an `svn commit` / `svn ci`, it denies the command when:

- the command text, or a message file named with `-F` / `--file` that exists when the hook runs, contains a trailer line such as `Co-Authored-By:`, `Signed-off-by:`, `Generated-by:`, `Claude-Session:`, `Acked-by:`, `Reviewed-by:` or similar;
- the text contains "Generated with" or the robot emoji;
- a git commit passes `--signoff`, `-s` or `--trailer`.

The hook refuses; it never rewrites the message.

Known gaps. The hook does not see:

- `git commit --amend --no-edit`: the old message is reused and the hook cannot read it.
- A message built outside the Bash tool.
- A commit wrapped in `bash -c`, `sh -c` or `zsh -c`: it passes the hook entirely, both the flag checks and the trailer text.
- A message passed through a shell variable (`git commit -m "$MSG"`).
- `git commit -C <commit>` or `--reuse-message`: it reuses an old message unchecked.
- Git aliases such as `git ci`.
- Commits made inside a script or a Makefile target.
- `GIT_EDITOR=true git commit --amend`.
- A quoted `<<WORD` heredoc followed by a later line equal to `WORD`, which hides the lines in between from the flag checks.

The hook runs `python3`, which must be on PATH. If it is missing, the shell exits 127, which Claude Code treats as non-blocking, so the commit goes through.

Claude Code treats any non-blocking hook failure (an exit code other than 0 or 2) as a pass. The trailer hook sets
`"onFailure": "block"`, so a crash, a timeout or invalid output refuses the command instead (Claude Code 2.1.295 or
later; earlier versions do not know the field). It is still a guard, not a guarantee: an installed mod can approve a
call that a `PreToolUse` hook blocked, unless managed settings or a Team or Enterprise login apply.

## Switching off Claude Code's own attribution

The hook and `rules/commit-vcs.md` stop a trailer in a message the agent writes. Claude Code can also add its own attribution to commits and pull requests. A plugin cannot set that in its own `settings.json`. Set it yourself in your user, project or local settings:

```json
{
  "attribution": false
}
```

- `"attribution": false` hides all attribution. It needs Claude Code 2.1.281 or later; earlier versions reject it and skip the whole settings file that holds it.
- The object form `{"commit": "", "pr": "", "sessionUrl": false}` is documented as the form for a settings file that earlier versions also read. The documentation gives no version for it.
- `attribution.sessionUrl` is a separate switch. It controls the `Claude-Session` trailer and the PR session link in cloud and Remote Control sessions, so blanking `commit` does not turn it off.
- `includeCoAuthoredBy` is deprecated since Claude Code v2.0.62. It is ignored once `attribution.commit` or `attribution.pr` is set.
- Managed settings can override your own rules. Claude Code tells Claude that your CLAUDE.md or memory instructions about attribution take precedence, unless the line is set in managed settings. If an administrator set `attribution` there, a rule in your project or in this plugin may not win.

## Concise mode

`concise.py` listens to `SessionStart` (startup, resume, clear, compact) and `SubagentStart`. It adds `concise.md` as
context, so replies and code stay short in every session and every subagent; at `SessionStart` it also adds
`progress.md` (see below). It only adds context: it never blocks, and any error means the session starts without it. The rules are adapted from ponytail (MIT, copyright (c) 2026
DietrichGebert): the decision ladder, the `shortcut:` comment and the never-cut list. To change the rules, edit
`concise.md`; to switch them off, remove the two entries from `hooks.json`.

## Evidence gate

`evidence_gate.py` listens to `PostToolUse`, `PostToolUseFailure`, `Stop` and `SubagentStop` (only for
`cv-kit:engineer`). It does nothing until the `develop` skill arms it for the session. Once armed it keeps a ledger
under `~/.cache/cv-kit/gate/` (set `CV_KIT_GATE_DIR` to move it, delete it any time):

- An edit to a code file (`.py`, `.go`, `.cc`, `.cpp`, `.h`, `.hpp`, `.cu`, `CMakeLists.txt` and similar) makes any earlier
  green test run stale. Docs and data files do not count.
- A Bash command counts as a green run only if it is a test command (`pytest`, `ctest`, `tox`, `make test`,
  `go test`, `cargo test`, a `*_test` binary) that exited 0 and whose exit status is trustworthy: not piped
  (unless `pipefail` is set), not followed by `|| true`, and not followed by another `;` command.
- When a turn ends with a stale edit, the gate blocks once with a reason. It does not block again for the same edit,
  does not block when `stop_hook_active` is set or a background task is running, and any error lets the turn end.
  Claude Code also stops after eight consecutive Stop blocks.

It is a nudge toward "evidence over claims", not a proof: it cannot tell that the right tests ran. A request for only
a failing test (the red step) is answered by saying so.

## Progress and next prompts

`concise.md` tells every subagent to start its report with `STATUS: done|blocked|failed — <15 words max>`.
`progress.md` is added at `SessionStart` only, so subagents pay no tokens for it: when a background agent finishes
while others run, the main thread prints a `Progress (2/3 done):` block, with no clock, since the agent rows show the
time. A finished task ends with `Summarization:` (at most 5 bullets) and `Next:` (at most 3 prompts to copy, such as
`/cv-kit:review the diff against main`). A plugin cannot steer Claude Code's own grey prompt suggestions, so `Next:`
is plain text in the reply. There is no timer-based heartbeat: the blocks appear on events, and the agent rows cover
the time in between.

## Agent rows in the status line

Since Claude Code 2.1.323 a plugin cannot restyle the subagent rows under the prompt, and a status line command gets
no subagent data. So the hooks collect it and your status line draws it, one row per agent:

```
◓ engineer (sonnet ▰▰▰▱▱)  tracker core: failing test, then code  27s
✓ explorer (haiku ▰▱▱▱▱)   where frames reach the writer          17s
```

Icon, agent, model and effort meter (`low` `▰▱▱▱▱` to `max` `▰▰▰▰▰`), the task description, and the time: elapsed
while it runs, the duration once done. `◐◓◑◒` turns on each refresh while the agent runs, `✓` is done, `✗` is a
failed Agent call, `■` is an agent left running when the session was quit and resumed; done rows fade, failed rows
stay bright. A foreground agent from an earlier prompt is not shown: it was interrupted, and Esc runs no hook. Running rows come first, then the rows that finished
under your current prompt; past 6 rows a `+N more` line counts the rest. The model is the one the Agent call named,
else the `model:` of a cv-kit agent. A narrow terminal cuts the description first, then the effort meter, then the
model. `NO_COLOR=1` turns the colours off.

`agent_rows.py --event` runs on `PreToolUse`, `PostToolUse` and `PostToolUseFailure` of the Agent tool and on
`SubagentStart` and `SubagentStop`, and appends one line per event to `~/.cache/cv-kit/agents/<session_id>.jsonl`.
The Agent call gives the type, description, model and effort; the start and stop give the clock. A call pairs with
the next start of its type under the same prompt, and the `agentId` that `PostToolUse` returns corrects the pair
when two agents of one type start together; a call that failed or was refused before it started pairs with nothing. At `SessionStart`, `agent_rows.py --register` writes the plugin root to
`~/.cache/cv-kit/agent-rows-root`, which the status line command reads, and deletes logs older than a day.

A plugin cannot set `statusLine`. `scripts/install_statusline.py` writes it for you (README, Install): it keeps a
status line you already have, backs the file up, does nothing on a second run, and `--uninstall` puts the old line
back. By hand, add this to `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 \"$(cat \"$HOME/.cache/cv-kit/agent-rows-root\" 2>/dev/null)/hooks/agent_rows.py\" 2>/dev/null || true",
    "refreshInterval": 1
  }
}
```

`refreshInterval` keeps the clocks moving while the main thread waits on background agents; the script reads one
small file, so once a second is cheap. If you already have a status line, keep it: put its command in place of
`YOUR_COMMAND` and use the result as `command` (escape the quotes and the newline for JSON; the newline lets a
command that ends in `#` or `&` still parse). Both get the same input, your line
prints first, and it still prints when cv-kit is not there: `|| true` matters, since a status line that exits
non-zero goes blank. Your command then also runs every second.

```sh
in=$(cat); printf '%s' "$in" | { YOUR_COMMAND
}; printf '%s' "$in" | python3 "$(cat "$HOME/.cache/cv-kit/agent-rows-root" 2>/dev/null)/hooks/agent_rows.py" 2>/dev/null || true
```

Known gaps:

- The rows need one session start with cv-kit 0.10 or later enabled, so the pointer file exists. The last session
  to start wins.
- A background agent stopped from `/tasks` may keep a running row until the session is resumed: no hook reports
  the stop.
- Hooks are off in an untrusted folder and under `disableAllHooks`, and then no rows appear.
- Run `install_statusline.py --uninstall` before you uninstall cv-kit. If you forget, your own line still prints
  and the rows part prints nothing.
