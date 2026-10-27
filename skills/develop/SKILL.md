---
name: develop
description: Use when writing, fixing, refactoring, testing or scoping code in Python or C++ (computer vision or not), or finding where code reads or uses something before a change, before touching any code, or writing the /goal or /loop line for unattended work. Applies test-first, systematic debugging, simplicity and evidence, and sends the work to agents with a model and effort sized to the task.
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

1. **Size it.** A clear one-line change: do it. New or vague: read `${CLAUDE_SKILL_DIR}/references/scoping.md`, ask one question at a time, write the brief back, and wait for a yes before code.
2. **Look first.** Read the project's rules and test setup, then run the existing tests for a baseline.
3. **Red, green, refactor**: by you for a one-line change, otherwise by the `engineer` you brief. Read the test reference that applies before the first test: `${CLAUDE_SKILL_DIR}/references/python-testing.md` (pytest) or `cpp-testing.md` (GoogleTest). Refactors follow `refactor.md`. `/simplify` is an optional last pass once the tests are green.
4. **Verify.** Run the tests and linters. Then review by the risk rules in "Route the work"; a one-line change needs no reviewer, because its test output is the check. Give the reviewer the diff and the tool output, not your conclusions. End with the report: for a bug, the cause in one sentence with `path:line`; the tests added, by name, and what each pins; the change; and the literal output of each command, or that it did not run and why.
5. **Commit** only when asked, through `/cv-kit:commit`.

Need sourced evidence about a model, paper or benchmark: `/cv-kit:research`. Need linters or rules installed in the project: `/cv-kit:setup`.

## Route the work

Route yourself; do not ask the user. Anything beyond a clear one-line change goes to an agent from this table. You scope it and write the brief; the agent reads or writes; you check what comes back. Judge difficulty from the request before reading code: an unknown-cause bug, or anything with threads, numerics, performance or security, is Hard even if the fix looks small. Do not read more than a couple of files or search the repository yourself; send `explorer` and keep its answer. Pass `model` and `effort` on each Agent call from this table. Without the Agent tool, do the work yourself with the same steps.

| Task | Agent | `model` | `effort` |
| --- | --- | --- | --- |
| Find, read or summarise code, logs, docs | `explorer` | `haiku` | low |
| Ordinary feature, bug fix, test, refactor step | `engineer` | `sonnet` | medium |
| Unclear bug, cross-module design, concurrency, numerics, performance, security | `engineer` | `opus` | high |
| Review of a Hard change, or of anything touching numerics, security or a published number | `reviewer` | `opus` | high |
| Review of a routine change whose tests and linters pass | `reviewer` | `sonnet` | medium |

`model` takes the aliases `haiku`, `sonnet`, `opus` (Haiku 5.5, Sonnet 5.5 and Opus 5.5 on the Anthropic API). Escalate one row after a failed attempt, and to `xhigh` on the last row; never resend the same prompt. Run file-disjoint tasks in one message; give each parallel `engineer` that edits files `isolation: worktree`. A brief states the goal, the constraints, what is ruled out and the exact files. Check what comes back against the output you asked for. Detail: `${CLAUDE_SKILL_DIR}/references/routing.md`.

## Unattended runs (`/goal`, `/loop`)

When the prompt came from `/goal <condition>` or a `/loop`, nobody is there to answer. Take the brief from the condition; if it leaves out something that changes the result, state your assumption and go on. `/goal`'s judge reads only the transcript, so end every turn with the literal output of the check (test summary, exit status, linter result), not a description of it. Never commit or push, and never run code from a cloned repo, unless the condition says so. After two failed fixes, stop and report what the evidence shows.

**Writing the line.** When asked to write a `/goal` or `/loop` line, change no code: write one fenced block for the user to paste, then stop. Use the facts above for the check; "not found" means look yourself.

1. **Pick the mode.** A finite task with a checkable end (fix, feature, migration, backlog): `/goal`. Something to repeat or watch on an interval: `/loop`. Say which, and why, in one line.
2. **Set the end state.** One measurable outcome and the command that proves it. A vague task gets your assumption stated inside the line.
3. **Bound it.** End with `Or stop after N turns` (fix 15, feature 25, research 30), and add `After two failed fixes, stop and report the literal output.`
4. **Constrain it.** Name what must not change: other test files, `no commit`, `no push`, no code run from a clone.
5. **Loops.** Start with `first run test -f .cv-kit-stop and stop if it exists`, so `touch .cv-kit-stop` halts it. A watch-only loop says `change nothing`.
6. **Headless, only if the user will be away.** Give `claude -p "/goal ..." --output-format stream-json --verbose` with a log path outside the repo. Permissions must be set in advance (`/cv-kit:setup`).
7. **Size.** At most 4,000 characters. Keep tests in the foreground: a background run defers the judge.

Output: the block, then `Paste it after /goal or /loop, in auto mode.` Examples: `${CLAUDE_SKILL_DIR}/references/goal-loop-templates.md`.
