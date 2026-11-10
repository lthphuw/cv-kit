---
name: develop
description: Use when writing, fixing, refactoring, testing or scoping code in Python, C++ or Go (computer vision or not), or finding where code reads or uses something before a change, before touching any code, writing the /goal or /loop line for unattended work, or setting a project up with cv-kit's rules, lint configs and permissions. Applies test-first, systematic debugging, simplicity and evidence, and sends the work to agents with a model and effort sized to the task.
argument-hint: "[feature, bug or goal]"
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project_facts.py *) Bash(python3 ${CLAUDE_PLUGIN_ROOT}/hooks/evidence_gate.py *)
---

# Develop

Four principles, on every change:

1. **Test first.** No production code without a failing test you watched fail. A bug gets a test that reproduces it, a feature gets tests for its use cases, a refactor pins its behaviour first.
2. **Process over guessing.** Reproduce, isolate, form one hypothesis, change one thing. No fix without a root cause; after two failed fixes, re-read the evidence.
3. **Simplicity.** The smallest change that passes. No abstraction with one user, no unrequested option, no new dependency. Delete before adding.
4. **Evidence over claims.** "Done", "fixed" and "faster" need command output from this turn; a hot path needs a measurement. Print the literal output; say what did not run.

If the superpowers plugin is installed, its brainstorming, debugging, TDD and verification skills cover the generic process; this skill supplies the rules, tests and routing. A project's written rules (`CLAUDE.md`, `.claude/rules/`, lint and build configs) win over this skill.

## Facts read just now

!`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project_facts.py facts .`
!`python3 ${CLAUDE_PLUGIN_ROOT}/hooks/evidence_gate.py arm ${CLAUDE_SESSION_ID}`

Treat a fact above as true only for what it says; "not found" means look yourself, do not assume.

## Flow

1. **Size it.** A clear one-line change, where the user names the line and the change: do it. A bug whose cause is unknown is never a one-line change, however small the files. New or vague: read `${CLAUDE_SKILL_DIR}/references/scoping.md`, ask one question at a time, write the brief back, and wait for a yes before code.
2. **Look first.** Read the project's rules and test setup, then run the existing tests for a baseline. With no `.claude/rules/`, read the plugin's own in `${CLAUDE_SKILL_DIR}/../../rules/`: `principles.md`, `evidence.md`, and the style and test rules of each language you touch. A language with no linter config: offer cv-kit's, as `${CLAUDE_SKILL_DIR}/references/project-setup.md` says, and add it only after a yes.
3. **Design, only when packages depend on each other.** Two or more packages that share an interface or a data flow: `architect` designs it and you wait for the user's yes, as "Route the work" says. One package, or packages that share nothing: skip this, the brief is the design.
4. **Red, green, refactor**: by you for a one-line change, otherwise by the `engineer` you brief. Read the test reference that applies before the first test: `${CLAUDE_SKILL_DIR}/references/python-testing.md` (pytest), `cpp-testing.md` (GoogleTest) or `go-testing.md` (`go test`). Refactors follow `refactor.md`. `/simplify` is an optional last pass once the tests are green.
5. **Verify.** Run the tests and linters. Then review by the risk rules in "Route the work"; a one-line change needs no reviewer, because its test output is the check. The reviewer has no shell: paste the diff and the tool output, and the design's `Interfaces` and `Invariants` when there was one, not your conclusions. End with the report: for a bug, the cause in one sentence with `path:line`; the tests added, by name, and what each pins; the change; and the literal output of each command, or that it did not run and why.
6. **Commit** only when asked, as `${CLAUDE_SKILL_DIR}/../../rules/commit-vcs.md` says: Conventional Commits, no trailers.

Need sourced evidence about a model, paper or benchmark: `/cv-kit:research`. Asked to set the project up: follow `${CLAUDE_SKILL_DIR}/references/project-setup.md`.

## Route the work

Route yourself; do not ask the user. Anything beyond a clear one-line change goes to an agent. You scope it, gather the facts, write the brief and check what comes back; the agent reads, debugs and writes. Do not read more than a couple of files or search the repository yourself: send `explorer` and put its `path:line` answer in the brief. Small files are not a reason to do the work yourself: once you have read enough to find the cause, you have done the engineer's job on the most expensive model, with no failing test behind it. Read only what the brief needs, then delegate. Pass `model` and `effort` on every Agent call. Without the Agent tool, do the work yourself with the same steps.

**Sonnet is the default; a precise brief is what makes it enough.** A concurrency or memory-safety bug (deadlock, race, crash only under load, use-after-free) is Hard from the request alone: decide that before reading code, and brief the `opus` engineer with the files and symptoms the user gave. Everything else is sized by what is still unknown once `explorer` has answered, not by topic: box maths, NMS, a located bug or a perf fix with a benchmark is a Sonnet task. Opus is for work where the reasoning, not the typing, is the hard part.

| Task | Agent | `model` | `effort` |
| --- | --- | --- | --- |
| Find, read or summarise code, logs, docs | `explorer` | `haiku` | low |
| Mechanical: rename, move, a config value, a test for behaviour already pinned | `engineer` | `sonnet` | medium |
| Feature, bug fix, test or refactor step with a known spec or a bug a test can reproduce | `engineer` | `sonnet` | high |
| Design before code: two or more packages that share an interface or a data flow | `architect` | `opus` | high |
| Hard: a concurrency or memory-safety bug, or a cause still unknown after `explorer` and a reproduction attempt | `engineer` | `opus` | high |
| Review of a change whose tests and linters pass | `reviewer` | `sonnet` | high |
| Review touching concurrency, memory safety, security or a number that will be published, or of a change that implements an `architect` design or that an `opus` engineer wrote | `reviewer` | `opus` | high |

**Design before code.** When the work splits into two or more packages that share an interface or a data flow, send `architect` the approved brief, `explorer`'s `path:line` facts, the test command and the baseline result before any engineer. It is read-only and returns the options, the flow, the interfaces, the invariants and the packages as engineer briefs. Show the design and wait for the user's yes; then add `Facts`, `Ruled out` and `Mode` to each package and dispatch it. Designed packages are `sonnet`, high, unless one is itself a Hard row. Use `effort` `xhigh` for a public API or ABI, a threading model, or a design the user sent back. Never send `architect` a single package, or packages that share nothing: the brief is the design.

**The brief.** Every `engineer` call carries these fields. A field you cannot fill is a question for `explorer` or the user, never for the engineer to guess.

```
Goal: one sentence, the behaviour after the change.
Done when: the test command, the new test names that must fail first, and "full suite green".
Facts: explorer's path:line findings, the repro or error text, the baseline test result.
Files: the files to change and the test file; anything else is out of bounds.
Constraints: project rules that apply; what must not change (API, dtype, BGR order, output format).
Ruled out: what was tried or rejected, and why. "none" on a first attempt.
Mode: fix | diagnose (reproduce with a test and find the cause; change no production code).
```

One package is one behaviour and its tests, a few files at most; split anything bigger, and order the parts that depend on each other. Examples of good and bad briefs: `${CLAUDE_SKILL_DIR}/references/routing.md`.

**What comes back.** Rerun the `Done when` command yourself and run `git diff --stat`.

- Done, but a file outside `Files` changed or the red run is missing: ask the same agent with SendMessage, not a new one.
- Blocked on a fact, a file outside `Files` or a decision: answer it and continue the same agent with SendMessage (without it, a new call with the earlier report pasted in). A decision that changes the scope goes to the user.
- Failed because of the brief (a wrong file, a missing fact, a bad test command, the environment): fix the brief and rerun on the same model.
- Failed on the reasoning (the fix did not hold, the evidence contradicts the hypothesis): the `opus` engineer row, with the failed attempt under `Ruled out`. An `opus` high failure gets one `opus` `xhigh` run; then stop and report the evidence.

Never resend the same brief, and run at most three engineer attempts per package. Run file-disjoint packages in one message, at most three engineers at a time, each with `isolation: worktree`.

## Unattended runs (`/goal`, `/loop`)

When the prompt came from `/goal <condition>` or a `/loop`, nobody is there to answer. Take the brief from the condition; if it leaves out something that changes the result, state your assumption and go on. `/goal`'s judge reads only the transcript, so end every turn with the literal output of the check (test summary, exit status, linter result), not a description of it. Never commit or push, and never run code from a cloned repo, unless the condition says so. After two failed fixes, stop and report what the evidence shows.

**Writing the line.** When asked to write a `/goal` or `/loop` line, change no code: write one fenced block for the user to paste, then stop. Use the facts above for the check; "not found" means look yourself.

1. **Pick the mode.** A finite task with a checkable end (fix, feature, migration, backlog): `/goal`. Something to repeat or watch on an interval: `/loop`. Say which, and why, in one line.
2. **Set the end state.** One measurable outcome and the command that proves it. A vague task gets your assumption stated inside the line.
3. **Bound it.** End with `Or stop after N turns` (fix 15, feature 25, research 30), and add `After two failed fixes, stop and report the literal output.`
4. **Constrain it.** Name what must not change: other test files, `no commit`, `no push`, no code run from a clone.
5. **Loops.** Start with `first run test -f .cv-kit-stop and stop if it exists`, so `touch .cv-kit-stop` halts it. A watch-only loop says `change nothing`.
6. **Headless, only if the user will be away.** Give `claude -p "/goal ..." --output-format stream-json --verbose` with a log path outside the repo. Permissions must be set in advance (`${CLAUDE_SKILL_DIR}/references/settings.md`).
7. **Size.** At most 4,000 characters. Keep tests in the foreground: a background run defers the judge.

Output: the block, then `Paste it after /goal or /loop, in auto mode.` Examples: `${CLAUDE_SKILL_DIR}/references/goal-loop-templates.md`.
