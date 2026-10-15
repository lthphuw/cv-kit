# cv-kit research 03: superpowers study and plugin packaging

Date: 2026-10-14. Sources: obra/superpowers cloned shallow at commit `bb92a77` (2026-10-09, v7.0.0) into
`<scratchpad>/sp-clone/repo` (nothing executed; only `claude plugin validate`, a read-only check, was run on it).
Official docs read live from code.claude.com (plugins reference, manifest reference, marketplace reference, components,
skills, sub-agents, hooks, memory, plugin-evals, CLI reference, loading) and agentskills.io/specification.
Local Claude Code used for checks: 2.1.299. A prototype skeleton of cv-kit that passes `claude plugin validate --strict`
is at `<scratchpad>/cvkit-proto` (see Part C).

---------------------------------------------------------------------------------------------------

## Part A. Superpowers v7.0.0

### A1. Repo layout (relevant to Claude Code; the rest is multi-harness packaging)

```
.claude-plugin/plugin.json, marketplace.json     Claude Code manifests
skills/<15 skills>/SKILL.md (+ supporting files) the actual product
hooks/hooks.json, run-hook.cmd, session-start    SessionStart bootstrap (bash, polyglot .cmd wrapper for Windows)
tests/                                           bash/node tests of NON-LLM code (hooks, sync scripts, structure checks)
docs/testing.md, docs/superpowers/ (plans,specs) maintainer docs; evals live in a SEPARATE repo (superpowers-evals)
scripts/bump-version.sh + .version-bump.json     bumps version in 12 manifest files
.codex-plugin .cursor-plugin .devin-plugin .kimi-plugin .antigravity-plugin .hermes-plugin .muse-plugin .opencode .pi .agents gemini-extension.json GEMINI.md index.js package.json
AGENTS.md (= contributor rules), README.md, RELEASE-NOTES.md (109 KB), CODE_OF_CONDUCT.md
```

There is NO `agents/` directory and NO `commands/` directory in v7. History: `agents/code-reviewer.md` existed (release notes
~v3/v4), later removed ("single source of truth": the reviewer persona now lives only as a prompt template,
`skills/requesting-code-review/code-reviewer.md`, dispatched through a `general-purpose` subagent). `commands/brainstorm.md`
etc. were redirect shims, since removed. So superpowers is skills + one hook, nothing else.

### A2. Manifests

`.claude-plugin/plugin.json` (complete file): `name`, `description`, `version` ("7.0.0"), `author{name,email}`, `homepage`,
`repository`, `license`, `keywords[]`. No `skills`/`hooks`/`agents` keys: it relies on default locations.

`.claude-plugin/marketplace.json`: `name` ("superpowers-dev"), `description`, `owner{name,email}`, `plugins[]` with ONE entry
`{name, description, version, source: "./", author}`. The repo is both marketplace and plugin (`source: "./"`).
`claude plugin validate ./repo --strict` on it: passes (exit 0).
Distribution: official marketplace (`/plugin install superpowers@claude-plugins-official`) and the author's own marketplace
repo (`superpowers-marketplace`). So the dev-marketplace in-repo is only for development.

### A3. Skills: how they are written

- Frontmatter is ONLY `name` + `description` (portable across harnesses; matches the agentskills.io subset).
- Description lengths in the repo: 93 to 393 characters (median ~120). Style: `Use when <trigger condition>` (13 of 15).
  Examples: `Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies`;
  `Use when implementing any feature or bugfix, before writing implementation code`. Exceptions: brainstorming v7
  (`"You MUST use this before any creative work..."`, quoted because of the colon-free imperative) and using-superpowers.
- Rule stated in `writing-skills` and enforced in a test: the description is TRIGGER ONLY and never summarises the workflow.
  Reason they give (measured): when the description said "code review between tasks" the model did one review instead of
  following the two-stage flow in the body; the model follows the description as a shortcut. `test-skill-structure.sh` even
  greps the description for banned workflow words (`dispatch`, `then`, `step`).
- Length: 15 skills, 3,828 lines total. Median ~200 lines. Outliers: writing-skills 681, subagent-driven-development 568,
  executing-plans 373, test-driven-development 330. Their own word targets: bootstrap skill <150-200 words, others <500
  words, but real files exceed that. Official limit: keep SKILL.md under 500 lines (two of theirs exceed it).
- Body vocabulary/devices that carry the behaviour: `<HARD-GATE>` blocks, `<EXTREMELY-IMPORTANT>`, "Red Flags" tables
  (`Thought` / `Reality`) listing rationalisations, "Announce at start: I'm using the X skill", Graphviz `dot` flowcharts for
  decisions, "Core principle" one-liners, "When NOT to use" lists, cross-references `superpowers:writing-plans`
  ("REQUIRED SUB-SKILL").
- Supporting files live next to SKILL.md: `*-prompt.md` templates for sub-agents, `scripts/` (task-brief extraction),
  `references/` (per-harness tool-name mapping), examples.
- `using-superpowers` (65 lines, 3.2 KB): the meta-skill. "If there is even a 1% chance a skill applies you MUST invoke it",
  plus a rationalisation table and skill priority (process skills before implementation skills).

### A4. Hooks

`hooks/hooks.json` has exactly one hook: `SessionStart`, matcher `startup|clear|compact` (note: not `resume`), a command
hook running `${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd session-start` with `"shell":"bash"`, `"async":false`.
`hooks/session-start` reads `skills/using-superpowers/SKILL.md`, JSON-escapes it with bash parameter substitution, wraps it in
`<EXTREMELY_IMPORTANT>You have superpowers...`, and prints
`{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"..."}}` for Claude Code (different JSON shapes for
Cursor/Copilot/Muse, selected by env vars). Much of the file is workarounds: broken `PATH` at startup
(anthropics/claude-code#43127), bash 5.3 heredoc hang, Windows EPIPE. This is how a plugin gets "always on" instructions:
skills alone only expose a one-line description.

### A5. The four patterns the task asked about

**brainstorming (v7 rewrite, 225 lines).** Not the old "propose 2-3 approaches" flow. Mechanics: (1) decide if the request
already contains everything (then just do it); (2) first message = one line "say so if you'd rather skip questions" + ONE open
question anchored in a concrete moment; (3) one question per message, no menu unless stuck; (4) "play back" 200-300 words per
understood part, marking guesses as guesses; (5) offer recon (look at code/data/web) instead of silently doing it;
(6) "size the work": quick task / small change in chat / project with a written design; (7) written design goes to
`docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`; (8) **builder check**: a fresh subagent with
`builder-check-prompt.md` reads the doc as the person who must build it and returns only the questions it would still have;
the parent sorts them into answered / minor (decide, mark "my call") / theirs (one round to the user); (9) `<HARD-GATE>`: no
building until the user approves; the only exits are "user opted out of questions" and a labelled throwaway spike. Terminal
state: invoke `writing-plans` and no other skill. Optional visual companion (a node server in `scripts/`) is off by default.

**writing-plans (204 lines).** Plan written for "an engineer who has not seen this codebase". Header block: Goal,
Architecture, Tech Stack, Spec path, **Global Constraints** (verbatim values copied from the spec), **Review Focus** (five
failure modes the spec implies but no test covers). File-structure map first, then tasks. Each task: Files
(Create/Modify/Test), **Interfaces** (`Consumes` / `Produces`, because an implementer sees only its own task), checkbox steps
(write failing test, run, implement, run, commit). "Task right-sizing": a task is the smallest unit worth a fresh reviewer's
gate. Saved to `docs/superpowers/plans/`.

**subagent-driven-development (568 lines, the heaviest).** Per task: implementer subagent (template `implementer-prompt.md`,
reads a task-brief FILE produced by `scripts/task-brief`), then a task reviewer (spec compliance + quality,
`task-reviewer-prompt.md`), then fix rounds with a breaker at 5 (rounds 1-3 resume the implementer, 4-5 a stronger fresh one;
`re-review-prompt.md`), then a whole-branch final review. Distinctive ideas: a **ledger** file `progress.md` as the recovery
map after compaction (trust it and `git log` over memory); a pre-flight "conflict scan" table over the plan; **"Rulings, not
stalls"** (the controller decides and logs `Ruling: what, why, cost if wrong`; only four things stop it: destructive op,
security-sensitive action, outside-worktree side effect, plan so broken every path is a guess); explicit **model per
dispatch** (cheap for mechanical, standard for integration, most capable for architecture/final review; omitting `model`
silently inherits the expensive session model); batch same-shape tiny edits into one dispatch; pass artifacts as files, not
pasted text, to protect controller context. A cheaper variant (`using-superpowers/references/claude-code-tools.md`): run the
whole loop inside one mid-tier orchestrator subagent, relying on nested subagents.

**dispatching-parallel-agents (167 lines).** Use for 2+ independent failures/domains with no shared state. Steps: group by
domain; give each agent a focused, self-contained prompt (scope, goal, constraints "do not change other code", expected
return summary); issue ALL Agent calls in ONE response so they run concurrently; then read summaries, check for conflicts,
run the full suite. Anti-use: related failures, need whole-system understanding, shared files/resources. Includes a dot
decision graph and "Common mistakes" (too broad / no context / no constraints / vague output).

### A6. Agents

None shipped (see A1). Sub-agent roles are prompt templates (`implementer-prompt.md`, `task-reviewer-prompt.md`,
`re-review-prompt.md`, `code-reviewer.md`, `builder-check-prompt.md`) that skills paste into a `general-purpose` dispatch.
Advantage: portable across harnesses and parameterisable per call (model, task text). Cost: every dispatch re-sends the
template through the controller's context, no tool restriction, no `@agent-` mention, no `skills:` preload.

### A7. Testing / eval approach

- `writing-skills` = "TDD for documentation": write pressure scenarios, run a subagent WITHOUT the skill (RED, record the exact
  rationalisations), write the skill against those, rerun (GREEN), then close loopholes (REFACTOR). Supporting files:
  `testing-skills-with-subagents.md`, `persuasion-principles.md`, `test-pressure-1..3.md` in systematic-debugging.
- `tests/` (bash/node, no LLM): hook output JSON (`tests/hooks/test-session-start.sh`), version-bump audit, shell lint,
  skill structure (`tests/diagnosing-superpowers/test-skill-structure.sh`: frontmatter present, `name` matches, description
  starts "Use when", <=1024 chars, banned workflow words, body word budget, required headings, every referenced file exists,
  no leaked local paths).
- `tests/claude-code/*.sh` and `tests/explicit-skill-requests/`: real `claude -p` sessions that assert skill triggering and
  token usage (`analyze-token-usage.py`); slow, not for PR CI.
- Behaviour evals live in a different repo (`prime-radiant-inc/superpowers-evals`, "Quorum": drives real CLIs in tmux with an
  LLM actor/verifier, 3-30+ min per scenario, nightly/on-demand, not on every PR).
- Contribution policy (AGENTS.md): 94% PR rejection; zero third-party dependencies; **domain-specific skills do not belong in
  core** (so a CV plugin is correctly a separate plugin); "compliance" rewrites to match Anthropic's skill guidance are
  rejected without eval evidence (their tuned wording diverges deliberately from Anthropic's docs).

### A8. Patterns worth copying for cv-kit

1. Frontmatter = `name` + `description` only; description = trigger conditions only, starts "Use when", under ~250 chars,
   never describes the steps. Add a structure test for it (A7).
2. A short always-on bootstrap skill injected via `SessionStart` (matcher `startup|clear|compact`, add `resume`), well under
   the 10,000-char cap, containing the skill-priority rule and a Red Flags table. Keep it <=60 lines.
3. Brainstorming adapted to CV: one open question at a time; play-back; "size the work"; HARD-GATE before any training or
   data work; a "builder check" sub-agent that reads the design as the ML engineer who must run it and lists what is still
   ambiguous (task definition, label schema, split policy, metric and IoU thresholds, latency budget and target hardware,
   baseline to beat, compute budget).
4. Plan header with **Global Constraints** (dataset version/hash, class list, split seeds, metric definition, target device,
   framework versions) copied verbatim, and `Interfaces: Consumes/Produces` between tasks (e.g. `splits.json` ->
   `train.py` -> `ckpt.pt` -> `eval.json`). This fits ML pipelines unusually well because tasks communicate through artifacts.
5. Sub-agent decomposition rules from dispatching-parallel-agents: parallel only for independent domains and disjoint output
   paths; one response, many Agent calls; each prompt has scope, goal, constraints, expected return; the parent reconciles.
   For CV: dataset audit, label-format check, baseline run, augmentation review, export-parity check are naturally parallel;
   training runs sharing one GPU are NOT (document GPU as the shared-state resource).
6. From SDD: task brief as a file, ledger file for resume after compaction (`experiments/ledger.md`), explicit model per
   dispatch, "Rulings, not stalls", and an independent reviewer that sees the diff and results but not the author's reasoning.
7. "Verification before completion": no metric claim without the command, seed, dataset hash and the printed number.
8. Pressure-scenario tests for skills (writing-skills method) plus a cheap structural test run on every PR.

### A9. Patterns to avoid (bloat)

- Multi-harness surface: 10 plugin dirs, a 12-file version-bump script, Windows polyglot `.cmd`, per-harness tool maps,
  porting guide. cv-kit targets Claude Code only; skip all of it.
- 500-700 line skills (writing-skills 681, SDD 568, executing-plans 373) with Graphviz sources and long prose; they exceed
  Anthropic's 500-line guidance and re-enter context at every use. Keep each SKILL.md <=150 lines; push templates to side files.
- SDD's machinery (5-round breaker, ledger protocol, conflict-scan table, model-tier matrix) is justified for long code-change
  plans, overkill for experiments; copy only the ledger and per-dispatch model idea.
- Two execution skills for the same plan (executing-plans and SDD) plus finishing/worktree/receiving-review skills: generic
  software workflow already covered by superpowers itself. Do not duplicate; declare it a companion (recommend, do not copy).
- Persuasion-heavy shouting (`EXTREMELY-IMPORTANT`, "1% chance you MUST") inflates tokens and can trigger prompt-injection
  defences; official hook docs advise factual statements over imperative system-style text. Use sparingly, one HARD-GATE per
  process skill.
- Hook portability code (PATH-less startup, heredoc, EPIPE) is bash-specific hardening; for cv-kit use exec form
  (`command` + `args`) and a tiny script, or plain-text stdout.
- A 109 KB RELEASE-NOTES.md and in-repo marketing; use a short CHANGELOG.
- Eval lab in a separate repo with tmux harnesses: replace with the built-in `claude plugin eval` (B6).

---------------------------------------------------------------------------------------------------

## Part B. Official Claude Code packaging (verified live, 2026-10-14)

### B1. Plugin layout and `plugin.json`

- Manifest is OPTIONAL; without it components are discovered in default locations. Write one for metadata. Path:
  `.claude-plugin/plugin.json`. Only `plugin.json` (and `marketplace.json`) go inside `.claude-plugin/`; everything else
  (`skills/`, `agents/`, `hooks/`, ...) sits at the plugin root.
- Required: only `name` (kebab-case; no spaces, `@`, `:`; must not start with `claude-`, `anthropic-`, `cc-plugin-` or equal
  `claude`, `anthropic`, etc.: error from `claude plugin validate`). `cv-kit` is fine.
- Fields: `$schema`, `name`, `displayName`, `version` (not semver-checked; setting it PINS the version: users get updates only
  when you change it), `description`, `author{name,email,url}`, `homepage` (must be a valid URL or the plugin fails to load),
  `repository`, `license` (SPDX), `keywords`, `metadata`, directory-listing fields (`icon`, `documentationUrl`, `supportUrl`,
  `privacyPolicyUrl`, `termsOfServiceUrl`), `defaultEnabled`, `dependencies`, `settings` (only `agent` and `subagentStatusLine`
  take effect), `userConfig`, `channels`, component keys `skills`, `commands`, `agents`, `hooks`, `mcpServers`, `lspServers`,
  `outputStyles`, `workflows`, and `experimental.{themes,monitors,evals}`.
- Component keys: all paths start with `./`, stay inside the plugin root. `skills` ADDS to the default `skills/` scan;
  `commands`, `agents`, `outputStyles` REPLACE their default dir; `hooks`/`mcpServers`/`lspServers` MERGE with the default file.
  `agents` entries must be `.md` files, not directories, when set explicitly.
- Unknown top-level keys are stripped (warning in validate); unknown keys inside `userConfig`/`channels`/`lspServers`/`monitors`
  are errors.
- Standard layout table: `skills/`, `commands/` (legacy; "prefer skills/ for new plugins"), `agents/`, `hooks/hooks.json`,
  `.mcp.json`, `.lsp.json`, `output-styles/`, `workflows/`, `themes/`, `monitors/monitors.json`, `bin/` (put on PATH), `settings.json`.
- Env vars: `${CLAUDE_PLUGIN_ROOT}` (changes every version; read-only code), `${CLAUDE_PLUGIN_DATA}` (persistent across updates),
  `${CLAUDE_PROJECT_DIR}`. Not available to commands Claude runs via the Bash tool, only in hook/MCP/LSP processes and
  substituted inline in skill/agent Markdown bodies.
- Marketplace-installed plugins are COPIED to `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`; files outside the
  plugin directory are not copied, so no `../shared` references.

### B2. `marketplace.json`

- Location `.claude-plugin/marketplace.json` at the repo root. Required: `name`, `owner{name}` (`email`,`url` optional), `plugins[]`.
  Recommended: `description`. Optional: `version`, `metadata.{description,version,pluginRoot}`, `forceRemoveDeletedPlugins`,
  `allowCrossMarketplaceDependenciesOn`, `renames`, `$schema`.
- Plugin entry required: `name`, `source`. Optional: `description`, `version`, `category`, `tags`, `strict` (default true),
  `relevance`, `dependencies`, `defaultEnabled`, `displayName`, plus any plugin.json field. Source forms: relative path starting
  with `./` (`"./"` or `"."` = repo root), `github{repo,ref,sha}`, `url`, `git-subdir{url,path,ref,sha}`, `npm`, `archive`, `command`.
- Name rules: letters, digits, `.`, `_`, `-`, start alphanumeric; reserved list includes `claude-code-marketplace`,
  `claude-plugins-official`, `anthropic-*`, `agent-skills`, `inline`, `builtin`, `skills-dir`, `synced`, `github`, `npm`, ...;
  names starting `claudeai-` reserved. `cv-kit` is allowed for both marketplace and plugin.
- Version precedence: `plugin.json` version > marketplace entry version > git SHA (12 chars). If both are set and differ,
  validate warns and plugin.json wins. Recommendation: set version in ONE place (plugin.json).
- Single-repo "marketplace + plugin" (`source: "./"`) is valid; this is what superpowers does. Alternative: keep plugin in
  `plugins/cv-kit/` and marketplace at root (needed only if you plan several plugins).

### B3. Skills (`skills/<name>/SKILL.md`)

Frontmatter fields (all optional; `description` recommended): `name` (defaults to dir name), `description`, `when_to_use`
(appended to description in the listing), `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`,
`allowed-tools`, `disallowed-tools`, `model`, `effort` (`low|medium|high|xhigh|max`), `context: fork` + `agent` + `background`
(run the skill inside a sub-agent), `hooks`, `paths` (glob list: auto-load only when matching files are in play),
`shell`, `metadata`, `license`, `compatibility`.
- Limits: `description` + `when_to_use` combined text is capped at 1,536 chars in the listing (setting
  `skillListingMaxDescChars`); whole listing budget = 1% of the context window (`skillListingBudgetFraction`); when it overflows,
  least-used skills lose their descriptions first. agentskills.io spec (portable subset): `name` <=64 chars, `[a-z0-9-]`, no
  leading/trailing/double hyphen, must equal the directory name; `description` <=1024 chars. SKILL.md body <500 lines
  (<5000 tokens recommended). After compaction each invoked skill keeps only its first 5,000 tokens (25,000 shared), so put
  critical instructions first.
- Portability caveat: claude.ai uploads / Skills API accept ONLY `name, description, license, compatibility, metadata,
  allowed-tools`; other keys (e.g. `argument-hint`, `paths`) are a hard error there. cv-kit targeting Claude Code only may use them.
- Namespacing: `skills/review/SKILL.md` in plugin `my-plugin` is `/my-plugin:review`; frontmatter `name` replaces the last
  segment only. So `cv-kit` + `name: auditing-image-datasets` -> `/cv-kit:auditing-image-datasets`. Do not prefix names with
  `cv-kit-` yourself (since v2.1.246 a name already starting with the prefix is not doubled, but it is still redundant).
  Skill tool calls and the model-facing list use `cv-kit:<name>`.
- `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PLUGIN_ROOT}` substitute in plugin skills. Dynamic injection with `` !`cmd` `` exists
  (non-zero exit aborts the skill; avoid in a CV plugin that must run on machines without GPUs).
- `claude plugin validate <skills dir>` checks SKILL.md frontmatter parse (v2.1.233+).

### B4. Agents (`agents/*.md`)

- Required frontmatter: `name` (<=256 chars, no `:`, not starting `-`), `description`. Supported in PLUGIN agents: `name`,
  `description`, `model` (`sonnet|opus|haiku|fable|inherit|<full id>`), `effort`, `maxTurns`, `tools`, `disallowedTools`,
  `skills` (full content of listed skills injected at startup, up to 32), `memory`, `background`, `omitClaudeMd`, `isolation`
  (`worktree` only), `color`, `experimental.cacheTtl`. IGNORED for plugin agents: `permissionMode`, `hooks`, `mcpServers`,
  `initialPrompt` (security). Unparseable frontmatter -> agent loads with all fields ignored and description "Agent from X plugin".
- Namespacing: `cv-kit:dataset-auditor`; subfolders add segments (`agents/review/x.md` -> `cv-kit:review:x`). Invoke with
  `@agent-cv-kit:dataset-auditor` or `claude --agent cv-kit:dataset-auditor`. Plugin agents have the LOWEST precedence.
- Delegation: Claude matches `description`; phrases like "use proactively" encourage it. Keep descriptions short (warning
  above 15,000 tokens of combined agent descriptions).
- Sub-agents may spawn sub-agents up to 3 layers (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`); 20 concurrent
  (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`); background sub-agents run concurrently; results return into the parent context.
- Preloading via `skills:` does not work for skills with `disable-model-invocation: true`.
- Plugin `settings.json` may set `"agent": "<plugin agent>"` to run that agent as the MAIN thread (user's own setting overrides).

### B5. Hooks, rules, namespacing, install

- Hooks: `hooks/hooks.json` with top-level `"hooks"` wrapper (a file without the wrapper fails to load). Events incl.
  `SessionStart` (matchers `startup|resume|clear|compact|fork`), only `command` and `mcp_tool` handlers on SessionStart.
  Context injection: JSON `hookSpecificOutput.additionalContext` OR plain stdout on exit 0; each capped at 10,000 chars (overflow
  goes to a file with a 2,000-char preview). Docs recommend exec form (`"command":"node","args":["${CLAUDE_PLUGIN_ROOT}/..."]`)
  over shell form (quoting). Docs advise phrasing injected context as facts, not system-style commands.
- **Can plugins ship rules? No.** Neither `.claude/rules/*.md` nor `CLAUDE.md` is a plugin component. A `CLAUDE.md` at the plugin
  root "isn't loaded as project context" and `claude plugin validate` warns about it. Docs: "To include instructions in a plugin,
  write them as a skill"; "If a rule must hold every time ... add it as a hook." Options for cv-kit, in order of preference:
  1. Skills with `paths:` globs (e.g. `**/*.ipynb`, `**/train*.py`, `**/configs/**/*.yaml`) = path-scoped rules that auto-load
     when those files are touched (behaves like `.claude/rules/*.md` with `paths:`).
  2. A short always-on bootstrap injected by a `SessionStart` hook (<10,000 chars; keep ~2-3 KB).
  3. A user-invoked skill `/cv-kit:install-rules` (`disable-model-invocation: true`) that COPIES `rules/*.md` from
     `${CLAUDE_SKILL_DIR}/../../rules` into the project's `.claude/rules/` (or appends an `@import` to project CLAUDE.md). Project
     files are then owned by the user and loaded natively (CLAUDE.md <200 lines advised; imports max 4 hops).
  4. Hard invariants (never `git add` datasets/checkpoints, never run `rm -rf` on data dirs) as PreToolUse hooks.
  5. `settings.json` `{"agent": "..."}` to make a CV persona the main agent (heavy-handed, user can override; use only if wanted).
- Install (user): in a session `/plugin marketplace add lthphuw/cv-kit` then `/plugin install cv-kit@cv-kit`; shell:
  `claude plugin marketplace add lthphuw/cv-kit` and `claude plugin install cv-kit@cv-kit [--scope user|project|local]`;
  one step (v2.1.292+): `claude plugin install cv-kit --marketplace lthphuw/cv-kit`. Pin a ref: `lthphuw/cv-kit#v0.1.0`.
  Share with a team: `claude plugin marketplace add lthphuw/cv-kit --scope project` (writes `.claude/settings.json`).
  Local dev: `claude --plugin-dir ./cv-kit`, then `/reload-plugins`; or add a local directory marketplace
  (`claude plugin marketplace add ./cv-kit`), whose edits load in place at the next session without a version bump.
- Updates: third-party marketplaces have auto-update OFF by default; users run `/plugin marketplace update` / `claude plugin
  update`. With `version` set in plugin.json, nothing updates until you bump it. Omit `version` (git SHA versioning) if you want
  every push to be an update, set it if you want deliberate releases.
- Validation: `claude plugin validate <path> [--strict] [--json]`; exit 0/1/2; `--strict` turns warnings into failures.

### B6. Evals: `claude plugin eval` (new vs superpowers)

Requires Claude Code >= 2.1.269, git >= 2.31. Suite lives in `evals/` at the plugin root: `evals/<case>/prompt.md` (frontmatter:
`runs` default 3, `max_turns` 10, `timeout_seconds` 300, `allowed_tools`, `tags`, `model`, `env EVAL_*`) plus
`graders/<name>.md` (types include regex over reply, `tool_used: Skill` to assert a skill fired, `llm` rubric judged by a second
model, file-based). Each case runs with the plugin and (default) without it; report shows `WITH`, `W/OUT`, delta; CI recipe:
`claude plugin eval . --trust-plugin --json results.json --threshold 0.8 --model <m> --judge-model <m> --no-publish
--max-cost-usd 20` (exit 0 pass / 1 fail / 2 partial). `claude plugin eval init` scaffolds cases interactively. Real model
calls: costs money, non-deterministic, run nightly/manual, not per PR. Docs list "early access / currently unavailable"
messages, so check `claude plugin eval --help` on the CI image before relying on it. This replaces superpowers' external tmux
eval lab for the "does the skill trigger" question. `skill-creator` plugin offers a separate `evals/evals.json` flow.

### B7. Differences from superpowers' usage (things to NOT copy blindly)

| Topic | Superpowers | Official docs / recommendation |
|---|---|---|
| `agents/` | none (prompt templates) | `agents/*.md` is first-class: `@agent-` mention, tool allowlist, `model`, `skills:` preload. cv-kit should use real agents for fixed roles |
| marketplace entry `version` | duplicated in plugin.json and marketplace.json (12-file bump script) | plugin.json wins; keep version in one place or omit |
| `description` cap | 1024 (agentskills.io) | Claude Code: 1,536 for description + when_to_use; 1024 is the portable choice |
| hook command | polyglot `run-hook.cmd` with `"shell":"bash"`, `"async":false` | docs show exec form `command` + `args`; I could not confirm `async` as a documented SessionStart field (superpowers' file passes validate, but unknown keys inside hook handlers may be ignored silently) |
| SessionStart matcher | `startup|clear|compact` | docs list also `resume` and `fork`; add `resume` unless context persists across resume (it does not re-fire otherwise) |
| skill name prefix | none; flat namespace | automatic `plugin:skill` namespacing; do not prefix names |
| frontmatter | name + description only | Claude Code supports `paths`, `when_to_use`, `context: fork`, `disable-model-invocation`, `argument-hint`; these are Claude-Code-only |
| shipping instructions | one big bootstrap skill via hook | rules are not a component; use `paths:` skills + small hook (B5) |
| Evals | external repo, tmux | built-in `claude plugin eval` |
| marketplace name | `superpowers-dev` | any non-reserved name; matching the plugin name (`cv-kit@cv-kit`) is fine |
| `validate` on repo root | n/a | observed on 2.1.299: running it on the repo root validated ONLY `marketplace.json` (`contents: []`). CI must call it separately on `.claude-plugin/plugin.json`, `skills/`, `agents/` |

---------------------------------------------------------------------------------------------------

## Part C. Proposed cv-kit

### C1. Repo tree (directories and files only)

```
cv-kit/
├── .claude-plugin/
│   ├── plugin.json                 Manifest: name cv-kit, version, author, license, keywords (single version source)
│   └── marketplace.json            Marketplace "cv-kit" with one entry, source "./"
├── skills/                         One dir per skill; every dir holds SKILL.md (<=150 lines), optional side files
│   ├── using-cv-kit/SKILL.md                    Bootstrap: skill-priority rule + red flags; also injected by the hook (<=60 lines)
│   ├── brainstorming-cv-work/                   Frame a CV task before work: task, labels, split, metric, latency, baseline
│   │   ├── SKILL.md
│   │   └── builder-check-prompt.md              Sub-agent prompt: "read this design as the ML engineer who must run it"
│   ├── planning-cv-experiments/                 Turn an approved design into a plan with Global Constraints + artifact interfaces
│   │   ├── SKILL.md
│   │   └── plan-template.md
│   ├── decomposing-cv-work/                     Decide what runs in parallel sub-agents vs sequentially (GPU = shared state)
│   │   ├── SKILL.md
│   │   └── dispatch-brief-template.md
│   ├── auditing-image-datasets/SKILL.md         Label errors, duplicates, leakage across splits, class balance, corrupt images
│   ├── converting-annotation-formats/SKILL.md   COCO/YOLO/VOC/segmentation-mask conventions, bbox origin and normalisation traps
│   ├── designing-augmentations/SKILL.md         Geometry-vs-label consistency, photometric limits, validation stays un-augmented
│   ├── splitting-cv-data/SKILL.md               Split by scene/video/patient, never by frame; seeds and hashes
│   ├── choosing-cv-metrics/SKILL.md             mAP definitions, IoU thresholds, per-class and small-object breakdown, calibration
│   ├── debugging-training-runs/SKILL.md         Overfit one batch, NaN loss, LR/scale mismatch, label shift, data-loader bugs
│   ├── evaluating-models-honestly/SKILL.md      No test-set tuning, confidence intervals, seed variance, ablations
│   ├── exporting-and-benchmarking-models/SKILL.md  ONNX/TensorRT/CoreML parity checks, warm-up, latency percentiles, batch size
│   ├── verifying-cv-claims/SKILL.md             No metric claim without command, seed, data hash, printed number
│   ├── recording-experiments/SKILL.md           Ledger/notebook format for runs and failed attempts (links to rnd-notebook if installed)
│   └── installing-cv-rules/SKILL.md             User-invoked only (disable-model-invocation): copy rules/ into project .claude/rules/
├── agents/                         Real sub-agents with fixed roles and tool allowlists (flat; names unique)
│   ├── dataset-auditor.md          Read-only audit of a dataset path; returns a findings table
│   ├── experiment-runner.md        Runs one training/eval command in a worktree, returns metrics + artifact paths only
│   ├── eval-reviewer.md            Independent reviewer: leakage, metric definition, seed variance (sees results, not author reasoning)
│   ├── export-validator.md         Numerical parity and latency check of an exported model
│   └── builder-check.md            Reads a design doc as the implementer; returns only blocking questions
├── hooks/
│   ├── hooks.json                  SessionStart (startup|resume|clear|compact) injecting the bootstrap; optional PreToolUse guards
│   └── session-start               Prints skills/using-cv-kit/SKILL.md as plain stdout or additionalContext (<10,000 chars)
├── rules/                          SOURCE files only (not auto-loaded by Claude Code), copied by installing-cv-rules
│   ├── data-hygiene.md             Never commit datasets/checkpoints; fixed seeds; record dataset hash
│   ├── experiment-reporting.md     How results are reported (metric, split, seed, n runs)
│   └── python-cv-style.md          Tensor shape comments, device handling, determinism flags
├── evals/                          `claude plugin eval` cases (nightly/manual)
│   ├── brainstorming-triggers/     prompt.md + graders/ (skill-fired.md, criteria.md)
│   ├── dataset-audit-triggers/
│   └── no-metric-without-evidence/
├── scripts/
│   ├── validate_plugin.py          Frontmatter/name/description/size/link checker (C2); stdlib + PyYAML
│   └── run_claude_validate.sh      Calls `claude plugin validate --strict` on manifest, marketplace, skills/, agents/
├── tests/
│   ├── test_validate_plugin.py     Unit tests for the validator using bad/good fixtures
│   ├── test_session_start.sh       Hook prints valid JSON/plain text, under 10,000 chars
│   └── fixtures/                   Minimal invalid skills (bad name, long description, missing file link)
├── docs/
│   ├── authoring-skills.md         House style (trigger-only descriptions, size budgets, red-flags table)
│   └── superpowers-companion.md    What cv-kit expects from / adds to superpowers (no duplication)
├── .github/
│   ├── workflows/validate.yml      Runs scripts + claude validate on every PR
│   ├── workflows/evals.yml         workflow_dispatch / nightly `claude plugin eval` with cost ceiling
│   └── PULL_REQUEST_TEMPLATE.md
├── README.md  CHANGELOG.md  LICENSE  CONTRIBUTING.md  .gitignore (evals/results/)
```

Notes on choices: no `commands/` (superseded by skills); no per-harness dirs; `rules/` is deliberately outside any scanned
directory; if multiple plugins are planned later, move to `plugins/cv-kit/` and keep `marketplace.json` at the root.
Skill names are verb-first gerunds (superpowers' own advice) and not prefixed with `cv-` except where meaning needs it.
Prototype of the manifests + one skill + one agent + hook, validated: `<scratchpad>/cvkit-proto`.

### C2. Validation approach

Two layers, both cheap and deterministic, run on every PR and locally via pre-commit.

Layer 1: the official validator (needs the `claude` CLI; install `@anthropic-ai/claude-code` in CI), because it knows the real
loader rules. Observed on 2.1.299 the repo-root call only checks the marketplace, so call it four times:
```bash
claude plugin validate .                              --strict   # marketplace.json
claude plugin validate .claude-plugin/plugin.json     --strict   # plugin manifest
claude plugin validate skills                         --strict   # every SKILL.md frontmatter parses
claude plugin validate agents                         --strict   # every agent file
```
(All four returned `Validation passed` on the prototype; `--json` gives machine-readable output.)

Layer 2: `scripts/validate_plugin.py` for rules the official validator does not enforce (house style and portability).
Checks, each a separate failing message with file path:
1. `SKILL.md` exists in every `skills/*/`; frontmatter starts at line 1, parses as YAML, is a mapping.
2. `name`: present, `^[a-z0-9]+(-[a-z0-9]+)*$`, <=64, equals directory name, unique across `skills/` AND not equal to any agent name.
3. `description`: present, non-empty, <=1024 chars (portable cap; hard fail), warn above 300; must start with `Use when`
   (configurable); must not contain workflow words (`then`, `first`, `step`, `dispatch`) as in superpowers' test;
   `description + when_to_use` <=1536.
4. Allowed frontmatter keys whitelist (`name, description, when_to_use, disable-model-invocation, user-invocable, paths,
   allowed-tools, argument-hint, model, effort, context, agent, license, compatibility, metadata`); unknown key = error
   (Claude Code silently ignores typos, so this catches them).
5. Size: SKILL.md <=150 lines (warn) and <=500 (fail); total description characters across all skills <= budget (e.g. 8,000,
   about 1% of a small context window) so the listing never truncates; the bootstrap body <= 60 lines and the hook payload <10,000 chars.
6. Links: every relative Markdown link and backticked `*.md`/`scripts/*` path inside a SKILL.md resolves to an existing file
   inside the skill dir (superpowers' test does the same), and nothing references `..` outside the plugin root (files outside are
   not copied on install).
7. Agents: frontmatter has `name`+`description`, `name` has no `:` and unique, `model` in the allowed set, `tools` entries are
   known tool names, and none of the ignored keys (`permissionMode`, `hooks`, `mcpServers`, `initialPrompt`) appear (they would
   be silently dropped for plugin agents). Every skill listed in `skills:` exists and lacks `disable-model-invocation: true`.
8. `plugin.json`/`marketplace.json`: valid JSON; plugin names equal between the two; `version` present only in plugin.json
   (warn if also in marketplace entry); no reserved prefix; `hooks/hooks.json` has the top-level `"hooks"` key and every
   `command` path exists.
9. Rules: each file in `rules/` <=200 lines; `paths:` frontmatter globs valid.
10. No secrets/local paths (`/Users/`, `C:\`) in shipped files (superpowers' leak scan).

Minimal core of the script (illustrative; pin `pyyaml`):
```python
import re, sys, pathlib, yaml
ROOT = pathlib.Path(__file__).resolve().parents[1]
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
def frontmatter(p):
    t = p.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", t, re.S)
    if not m: raise ValueError("no frontmatter at line 1")
    d = yaml.safe_load(m.group(1))
    if not isinstance(d, dict): raise ValueError("frontmatter is not a mapping")
    return d, t
errs, names = [], {}
for md in sorted(ROOT.glob("skills/*/SKILL.md")):
    try: fm, text = frontmatter(md)
    except Exception as e: errs.append(f"{md}: {e}"); continue
    n, d = fm.get("name"), str(fm.get("description", ""))
    if n != md.parent.name or not NAME.match(str(n)) or len(str(n)) > 64: errs.append(f"{md}: bad name {n!r}")
    if n in names: errs.append(f"{md}: duplicate name also in {names[n]}")
    names[n] = md
    if not d or len(d) > 1024: errs.append(f"{md}: description empty or >1024 ({len(d)})")
    if not d.startswith("Use when"): errs.append(f"{md}: description must start with 'Use when'")
    if text.count("\n") > 500: errs.append(f"{md}: >500 lines")
sys.exit("\n".join(errs) if errs else 0)
```
CI (`.github/workflows/validate.yml`): checkout, setup-python, `pip install pyyaml pytest`, `npm i -g @anthropic-ai/claude-code`,
run the four `claude plugin validate` calls, `python scripts/validate_plugin.py`, `pytest tests`. Also add the same as a
`pre-commit` local hook. Behavioural layer: `claude plugin eval . --trust-plugin --threshold 0.8 --max-cost-usd N` on
`workflow_dispatch`/nightly only, with `tool_used: Skill` graders asserting trigger-on-natural-phrasing and the no-plugin
baseline delta; plus a short pressure-scenario checklist (writing-skills RED/GREEN) kept in `docs/authoring-skills.md`.

### C3. README outline

1. Title + one-line pitch + badges (license, CI validate).
2. What you get (table: skills / agents / rules / hooks, with counts) and who it is for (CV engineers; detection,
   segmentation, classification, keypoints; training, evaluation, export).
3. Install: `/plugin marketplace add lthphuw/cv-kit`, `/plugin install cv-kit@cv-kit`; shell equivalents; project-scope install for teams;
   update (`/plugin marketplace update`, `/reload-plugins`); uninstall; minimum Claude Code version.
4. Quick start: three prompts that show brainstorming, parallel decomposition, and verification (with expected behaviour).
5. How it works: bootstrap hook, skill triggering, namespacing (`/cv-kit:<skill>`, `cv-kit:<agent>`), `paths:`-scoped skills.
6. Workflow diagram: brainstorm -> design (builder check) -> plan (Global Constraints, interfaces) -> decompose -> sub-agents
   -> review -> verify claims -> record. One short paragraph per stage, link to the skill.
7. Skill catalogue (table: name, when it triggers, size) and agent catalogue (role, tools, model).
8. Rules: why they are not auto-loaded (plugins cannot ship rules), how `/cv-kit:install-rules` installs them, how to edit.
9. Works with superpowers: what to install alongside (TDD, debugging, git worktrees), what cv-kit overrides, priority order.
10. Configuration and cost notes: models used by agents, concurrency limit (20 sub-agents), GPU contention, no network calls.
11. Contributing: house style (trigger-only descriptions, size budgets), `scripts/validate_plugin.py`, running evals (cost warning).
12. Troubleshooting: skill not triggering (`/doctor`, `--debug`, listing budget), plugin not loading (`claude plugin validate`),
    stale cache after update.
13. License, changelog link, acknowledgements (superpowers, agentskills.io).

---------------------------------------------------------------------------------------------------

## Caveats and unverified items

- `claude plugin eval` is documented as GA in these docs but the page lists "early access" and "unavailable" server-side
  messages; not run here (it spends model credits). Verify before building CI on it.
- Whether the `async` key in a hook handler is documented was not confirmed (docs pages read in part: hooks reference read
  to ~100 KB of 270 KB; skills page tail and sub-agents tail beyond 100 KB not fully read).
- `.claude/rules` inside a plugin: absence is inferred from the standard-layout table and the explicit statements that
  CLAUDE.md is not loaded and instructions belong in skills; I did not find a sentence that says "rules are unsupported" verbatim.
- Superpowers statistics (line counts, description lengths) were measured on commit `bb92a77` only.
- Prototype validation used local Claude Code 2.1.299; behaviour of older versions may differ (several checks are version-gated).
