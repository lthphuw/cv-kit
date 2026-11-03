# cv-kit research 10: progress without asking, and suggested next prompts

Date: 2026-11-03. Asked by: the lead, two approved features. (1) The user sees progress without asking "how is it going?":
live subagent rows, and event summaries. (2) After a finished task, the reply ends with copy-pasteable next prompts.
Nothing was run in Claude Code itself: the pages below are the only evidence for how the settings behave.

## Sources consulted

| # | Source | How read | Read on | Licence | Used for |
|---|---|---|---|---|---|
| S1 | https://code.claude.com/docs/en/statusline (section "Subagent status lines" and "Task fields") | WebFetch, then the saved page text read around the section | 2026-11-03 | not stated on the page; facts only, no text copied | `subagentStatusLine` shape (`type: command`, `command`), stdin (`columns`, `tasks[]` with `id`, `name`, `agentType`, `status`, `description`, `label`, `startTime`, `model`, `effort`, `tokenCount`, ...), stdout (`{"id","content"}` per row; no id keeps the default; empty content hides), gates (`disableAllHooks`, `allowManagedHooksOnly`), `agentType` needs Claude Code 2.1.293 |
| S2 | https://code.claude.com/docs/en/settings-reference.md (entry `subagentStatusLine`, and "Status line and file suggestion gates") | `curl` piped to `grep`, nothing saved | 2026-11-03 | as S1 | Type is an object with `type: "command"` and a `command` string; scope is any file; unset by default; the trust gate (untrusted folder turns it off) |
| S3 | https://code.claude.com/docs/en/plugins/components (section "Default settings", "Reference plugin paths") | WebFetch | 2026-11-03 | as S1 | A plugin's root `settings.json` takes effect for `agent` and `subagentStatusLine` only; user settings override plugin defaults; two plugins setting one key: the later one wins; `${CLAUDE_PLUGIN_ROOT}` is substituted in skill, command and agent content, hook and monitor commands, MCP and LSP configuration |
| S4 | https://code.claude.com/docs/en/plugins/manifest-reference.md (sections "settings", "Environment variables", "Where each variable resolves") | `curl` piped to `sed` and `grep` | 2026-11-03 | as S1 | Table of fields where `${...}` resolves: hook commands, monitor commands, MCP and LSP servers, skill, command and agent content. `settings.json` is not in the table |

Other: `docs/research/08-goal-loop-and-ponytail.md` (the concise rules this extends); the repository's own `hooks/`, `agents/`
and `skills/develop/` files.

## Findings

1. **Live rows are possible from a plugin** (S1, S3): `settings.json` at the plugin root may set `subagentStatusLine`. The
   command runs once per refresh tick; stdin is one JSON object; each stdout line rewrites one row.
2. **Checked live (Claude Code 2.1.317, 2026-11-03): `${CLAUDE_PLUGIN_ROOT}` is empty in `subagentStatusLine`.**
   A logging command printed `lit= env=`: neither substituted nor in the environment. The command runs in a shell
   with the project folder as cwd and no plugin variable. So `agent_status.py --register` runs at `SessionStart`
   (where the variable resolves) and writes the plugin root to `~/.cache/cv-kit/plugin-root`; the command reads it.
   The logged payloads: `startTime` is epoch ms and the command runs about every 5 s, so the row also shows
   `tokenCount`, which moves between ticks. After the fix the rows rendered as `explorer · haiku · 0s · running · …`.
3. **No end time in the task fields** (S1), so a finished task's elapsed time cannot be shown; the script shows the clock
   only for `running` rows.
4. **Plugins cannot steer the grey prompt suggestions** (S3: only `agent` and `subagentStatusLine` are honoured), so
   the suggested prompts are a `Next:` block in the reply, written by the model under a rule in `hooks/progress.md`.
5. **Decided against: a timer-based heartbeat.** Progress blocks come from events (a background agent finishing), the
   live rows cover the time between events.

## What was built

`settings.json`, `hooks/agent_status.py` (stdlib, never fails, `now` is injectable in `render`), `tests/test_agent_status.py`;
the STATUS line in `hooks/concise.md` (every session and subagent), the Progress, Summarization and Next blocks in
`hooks/progress.md` (added at `SessionStart` only, so subagents carry none of it), and a section in `hooks/README.md`.
At review the rules were taken out of `agents/*.md`, `skills/develop` and `agents/lead.md`, where they repeated the
hook, and the elapsed time was dropped from the Progress header: the main thread has no clock, the live rows show it.
