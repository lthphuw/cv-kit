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
while others run, the main thread prints a `Progress (2/3 done):` block, with no clock, since Claude Code's agent panel
shows the time. A finished task ends with `Summarization:` (at most 5 bullets) and `Next:` (at most 3 prompts to copy, such as
`/cv-kit:review the diff against main`). A plugin cannot steer Claude Code's own grey prompt suggestions, so `Next:`
is plain text in the reply. There is no timer-based heartbeat: the blocks appear on events, and the agent panel covers
the time in between.

## The status line

The status line is one row for the main session:

```
● main           opus   ▰▰▰▱▱  ctx ▰▰▰▱▱▱▱▱▱▱ 32% of 200k  $0.42  +156 −23         12m
```

The columns are icon, name, model, effort meter (`low` `▰▱▱▱▱` to `max` `▰▰▰▰▰`), context, cost and session time.
Claude Code's own agent panel lists each subagent (task, time, tokens) below the status line, so cv-kit draws no
agent rows. Versions up to 0.11 did, with hooks that logged agent events; those hooks are gone.

- **main**: the session's model (`⚡` in fast mode) and effort; the context used, green below 50%, yellow to 80%,
  red above; the cost, the lines changed, and how long the session has run.

When the terminal is narrow, parts go in this order: the lines changed, the context window size, the cost, the effort
meter, the model, the context. The cells shorten instead of cutting (`ctx 32%`, `$0.42`). `NO_COLOR=1` turns the
colours off.

At `SessionStart`, `agent_rows.py --register` writes the plugin root to `~/.cache/cv-kit/agent-rows-root`, refreshes
an installed launcher, and deletes the agent logs and row memory that older versions left in `~/.cache/cv-kit`, once
they are a day old.

### Turning it on, on macOS, Linux and Windows

A plugin cannot set `statusLine`, so `scripts/install_statusline.py` writes it (README, Install). It copies
`statusline_launcher.py` to `~/.claude/cv-kit/statusline.py` and sets the command to `<python> <launcher> <config>`,
with no shell syntax, so it runs the same in sh, Git Bash and PowerShell. Paths are written with forward slashes, and quoted
for the shell Claude Code uses: sh on macOS and Linux, Git Bash on Windows, PowerShell (with `&`) when Git Bash is
missing. The Python is `python3` from PATH when it runs, else the one that ran the installer.

Each settings file gets its own config, `~/.claude/cv-kit/statusline-<id>.json`, so your user settings and a
project's can each keep their own line. A status line you already have goes there with the shell it runs in, found
again on every run of the installer (Git Bash may have come or gone). On each refresh the launcher runs it first
with the same input, keeps its output when it exits 0 within 10 seconds, and then adds the row. A command that runs
longer is killed (its whole process tree on Windows, where a child still holding the output would stall the
refresh), and when Claude Code cancels a refresh the launcher takes your command with it. The launcher always exits
0 and prints UTF-8, since Claude Code blanks the whole status line when the command fails: a missing cv-kit or a
broken config never costs you your own line.

A re-run keeps edits you made to the line since (`padding`, a `refreshInterval` you set) and your earlier `--ascii`,
unless you pass a new one. A config written with the old `--no-main` is rewritten without it, and until then the
launcher ignores it: the main row always shows. If the config is gone (a settings file synced without it), the backup
taken before cv-kit first wrote the file gives your line back. `--uninstall` puts the old line back, and removes the
launcher once no settings file uses it. The 0.10 shell form is migrated on the next run, keeping your other fields.

Options: `--refresh N` (default 1 second; your own command then runs that often too), `--ascii` for a terminal
without the glyphs (`#` and `-` for the bars; `--no-ascii` undoes it), `--settings PATH` for another file.

Known gaps:

- cv-kit's hooks run `python3`. On Windows the python.org installer makes only `python.exe`, so the installer warns
  when `python3` does not run: install Python from the Microsoft Store, or copy `python.exe` to `python3.exe`.
- The main row needs one session start with cv-kit 0.11 or later enabled, so the pointer file exists. The last session
  to start wins.
- Hooks are off in an untrusted folder and under `disableAllHooks`, and then the pointer file is not written and the
  main row does not appear.
