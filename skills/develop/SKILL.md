---
name: develop
description: Use when writing, fixing, refactoring, testing or scoping code in Python or C++ (computer vision or not), or finding where code reads or uses something before a change, before touching any code. Applies test-first, systematic debugging, simplicity and evidence, and sends the work to agents with a model and effort sized to the task.
argument-hint: "[feature, bug or goal]"
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project_facts.py *) Bash(python3 ${CLAUDE_PLUGIN_ROOT}/hooks/evidence_gate.py *)
---

# Develop

Four principles, applied on every change:

1. **Test first.** No production code without a failing test you watched fail. A bug gets a test that reproduces
   it, a feature gets tests for its use cases, a refactor gets its behaviour pinned first.
2. **Process over guessing.** Reproduce, isolate, form one hypothesis, test it, change one thing. No fix without a
   root cause; after two failed fixes, stop and re-read the evidence.
3. **Simplicity.** The smallest change that passes. No abstraction with one user, no option nobody asked for, no
   new dependency. Delete before adding.
4. **Evidence over claims.** "Done", "fixed" and "faster" need command output from this turn: tests, linters,
   build, and for a hot path a measurement. Print the literal output; say what did not run.

If the superpowers plugin is installed, its brainstorming, debugging, TDD and verification skills cover the generic
process; follow them and use this skill for the rules, tests and routing below. A project's own written rule
(`CLAUDE.md`, `.claude/rules/`, lint and build configs) beats anything here.

## Facts read just now

!`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project_facts.py facts .`
!`python3 ${CLAUDE_PLUGIN_ROOT}/hooks/evidence_gate.py arm ${CLAUDE_SESSION_ID}`

Treat a fact above as true only for what it says; "not found" means look yourself, do not assume.

## Flow

1. **Size it.** A clear one-line change: do it. New or vague: read `${CLAUDE_SKILL_DIR}/references/scoping.md`,
   ask one question at a time, write the brief back, and wait for a yes before code.
2. **Look first.** Read the project's rules and test setup, then run the existing tests for a baseline.
3. **Red, green, refactor**, done by you for a one-line change and otherwise by the `engineer` you brief (see "Route
   the work"). Python tests use pytest (`${CLAUDE_SKILL_DIR}/references/python-testing.md`), C++ tests
   use GoogleTest (`${CLAUDE_SKILL_DIR}/references/cpp-testing.md`). Read the one that applies before writing the
   first test. Refactors follow `${CLAUDE_SKILL_DIR}/references/refactor.md`; `/simplify` is a good last pass on the
   changed code once the tests are green.
4. **Verify.** Run the tests and the linters. For anything non-trivial, or code you wrote this session, have the
   `reviewer` agent check it; give it the diff and the tool output, not your conclusions. End with a report: for a
   bug the cause in one sentence with `path:line`; the tests added, by name, and what each pins; the change; and the
   literal output of each command, or that it did not run and why.
5. **Commit** only when asked, through `/cv-kit:commit`.

Need sourced evidence about a model, paper or benchmark: `/cv-kit:research`. Need linters or rules installed in the
project: `/cv-kit:setup`.

## Route the work

Route yourself; do not ask the user. A clear one-line change you make yourself (step 1 above). Anything larger goes to
an agent from this table: you scope it, write the brief and check what comes back; the agent reads or writes. Judge
the difficulty from the request, before you read the code: a bug whose cause is unknown, or anything with threads,
numerics, performance or security, is a Hard row even if the fix then turns out to be two lines. Do not read more than
a couple of files, or search the repository, to answer a question yourself; send `explorer` and keep its answer, not
the files, in your context. Pick the agent, then pass `model` and `effort` on the Agent call by how hard the task is
(this table is the instruction to set them). Without the Agent tool, do the work yourself and keep the same steps.
`model` takes the aliases `haiku`, `sonnet`, `opus`; they resolve to Haiku 5.5, Sonnet 5.5 and Opus 5.5 on the
Anthropic API.

| Task | Agent | `model` | `effort` |
| --- | --- | --- | --- |
| Find, read or summarise code, logs, docs | `explorer` | `haiku` | low |
| Ordinary feature, bug fix, test, refactor step | `engineer` | `sonnet` | medium |
| Unclear bug, cross-module design, concurrency, numerics, performance, security | `engineer` | `opus` | high |
| Independent review of non-trivial or self-written code | `reviewer` | `opus` | high |

Escalate one row after a failed attempt (and to `xhigh` on the last row); never resend the same prompt. Run
independent tasks, ones that share no files, in one message so they run in parallel; give each `engineer` that
edits files in parallel `isolation: worktree`. A brief states the goal, the constraints, what is ruled out and the
exact files; an agent knows nothing else. Check what comes back against the output you asked for before you merge it.
More detail: `${CLAUDE_SKILL_DIR}/references/routing.md`.

## Unattended runs (`/goal`, `/loop`)

When the prompt came from `/goal <condition>` or a `/loop`, nobody is there to answer. Take the brief from the
condition and do not ask; if it leaves out something that changes the result, state your assumption and go on.
`/goal`'s judge reads only the transcript, so end every turn with the literal output of the check (test summary,
exit status, linter result), not a description of it. Never commit or push, and never run code from a cloned repo,
unless the condition says so. After two failed fixes stop and report what the evidence shows. Condition templates
are in `${CLAUDE_SKILL_DIR}/references/unattended.md`.
