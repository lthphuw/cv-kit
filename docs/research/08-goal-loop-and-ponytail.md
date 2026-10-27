# cv-kit research 08: /goal and /loop blog, ponytail, concise output

Date: 2026-10-27. Asked by: brainstorming for cv-kit, four goals: combine `/goal` and `/loop` with `cv-kit:develop`, always
concise output, concise code in the style of ponytail, all inside this plugin. Nothing executed from any clone. Nothing built yet.

## Sources consulted

| # | Source | How read | Version | Licence | Tier |
|---|---|---|---|---|---|
| S1 | https://www.mindstudio.ai/blog/how-to-use-goal-and-loop-claude-code-autonomous-workflows | WebFetch, summarised by a small model; page text not copied | live 2026-10-27 | not stated in fetch; ideas only, no text copied | T5 (blog; never cited for numbers) |
| S2 | https://github.com/DietrichGebert/ponytail | WebFetch summary of the README page, then local files below | commit `09c434a` (2026-10-18) | MIT, Copyright (c) 2026 DietrichGebert (`<refs>/ponytail/LICENSE`); compatible with cv-kit MIT, keep notice if text is copied | repo (code and prompt) |
| S3 | local clone `<refs>/ponytail`, shallow | read: `skills/ponytail/SKILL.md` (52 lines, whole); `hooks/ponytail-activate.js` lines 1-80 of 201; `hooks/claude-codex-hooks.json`; `plugin.json` | same | as S2 | as S2 |
| S4 | cv-kit files | read: `skills/develop/SKILL.md`, `skills/develop/references/unattended.md`, `rules/principles.md`, `hooks/hooks.json`, `.claude-plugin/plugin.json`; grep for `/goal`, `/loop`, `concise`, `ponytail` | HEAD `add00d7` | MIT (repo) | own code |

## Findings

**1. `/goal` and `/loop` already exist in cv-kit.** `skills/develop/SKILL.md` has an "Unattended runs" section;
`references/unattended.md` has condition templates; README has examples per skill; `tests/test_plugin_contract.py:103` pins
the text. So the integration is extend-or-tune work, not new work.

**2. Blog patterns against cv-kit** (S1 vs S4):

| Pattern in S1 | cv-kit today |
|---|---|
| Measurable goal plus the command that proves it | present (`unattended.md` templates) |
| Cycle cap ("stop after N turns") | present |
| Verification each cycle, literal output for the judge | present (`develop/SKILL.md` unattended section) |
| Blocker handling: stop after failed attempts | partial: "after two failed fixes stop and report" |
| Log unattended output to a file | absent |
| Sentinel file to stop a loop (e.g. `/tmp/stop-loop`) | absent |
| Checkpoint phases in one goal | absent |
| Restrict file access in `.claude/settings.json` | partial (`skills/setup/references/settings.md`) |

**3. Unverified claim in S1.** S1 says `/goal` and `/loop` are custom Markdown commands in `.claude/commands/`. cv-kit's
`unattended.md` says `/goal` is built-in and `/loop` is a bundled skill. Not settled here. Check against Claude Code docs
before relying on either.

**4. Ponytail's mechanism (S2, S3).** A SessionStart hook injects the ruleset into every session. A UserPromptSubmit hook
tracks the mode; a SubagentStart hook covers subagents. Levels: lite, full (default), ultra. A deliberate shortcut is
marked `shortcut: <limit>, <when to upgrade>`. A closing line says what was skipped or unchecked. Decision ladder: 6 numbered
rungs in SKILL.md (the WebFetch summary said seven; the file has six). It overlaps `rules/principles.md` "Simplicity" and
the develop routing.

**5. Conflicts to decide, not resolve here.**
- Ponytail (S3 SKILL.md): "trivial changes need no test". cv-kit (`rules/principles.md`, develop principle 1): no production
  code without a failing test. Default: keep cv-kit's rule; ponytail's lighter test rule applies only where cv-kit allows.
- Ponytail's SKILL.md ends each reply with skipped or unchecked items. cv-kit's develop report already asks for literal
  command output. Compatible if both are kept.

**6. Concise output.** cv-kit has no rule for it today (grep: only a ruff output format and a test match).

## Not checked

- Ponytail's benchmark (self-reported: 53% less code, 45% fewer tokens; 39 tasks, 5 runs). Not re-run; not cited
  for numbers. The `/goal` and `/loop` question is settled in the second pass below.

## Second pass: ponytail hooks, docs, and what was ported

Two read-only subagents read the clone in depth (text only; nothing run). Files read: `hooks/*.js`, `hooks/*.json`,
`plugin.json`; `README.md`, `AGENTS.md`, `INSTALL.md`, `after-install.md`, `.github/copilot-instructions.md`,
`commands/*.toml`, `benchmarks/README.md`, `benchmarks/behavior.yaml`, `benchmarks/behavior.js`,
`benchmarks/correctness.js`, `benchmarks/loc.js`. Commit `09c434a`, MIT.

Claude Code docs read live: https://code.claude.com/docs/en/hooks (SessionStart and SubagentStart accept
`hookSpecificOutput.additionalContext` with `hookEventName` set; SessionStart also accepts plain stdout),
https://code.claude.com/docs/en/commands (`/goal` is a built-in command; `/loop` is a bundled skill),
https://code.claude.com/docs/en/goal.md (the evaluator reads the transcript only and runs no commands; a condition is
at most 4,000 characters; `claude -p "/goal ..."` runs to completion in one invocation).

Ported into `hooks/concise.md` (always on, via `hooks/concise.py`):
- the 6-rung decision ladder, the `shortcut:` comment, the closing skipped/unchecked line, the never-cut list, the
  bug-fix caller grep, "lazy about the solution, never about the change" (ponytail `SKILL.md`).
- the test-first rule stays cv-kit's: ponytail's "trivial changes need no test" is not ported (conflicts with
  `rules/principles.md` rule 1).

Not ported, on purpose:
- `lite`/`ultra` levels, `/ponytail` mode switching, the per-project mode file, `ponytail-config` writes: cv-kit
  wants concise always, at one level.
- `/ponytail-review`, `/ponytail-audit`, `/ponytail-debt`, `/ponytail-gain`, `/ponytail-help`: cv-kit already has
  `review`; the debt ledger and gain scoreboard are not needed yet.
- `ponytail-map.js` (codebase map injected each session): it runs a repo scan at every start; not worth the cost yet.
- anything that edits `~/.claude/settings.json`, copies scripts into the Claude config dir, or installs a statusline.
- the band, webhook and transcript import: out of scope.
- ponytail's benchmark numbers (53% less code, 45% fewer tokens, self-reported): not verified here, not cited.

Blog claim, now settled: `/goal` is built-in and `/loop` is a bundled skill, not custom Markdown commands. The docs also
present them as separate approaches, not chained: a finite task takes `/goal`, a recurring check takes `/loop`.
