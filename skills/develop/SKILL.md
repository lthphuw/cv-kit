---
name: develop
description: Use when writing, fixing, refactoring, testing or scoping code in Python or C++ (computer vision or not), before touching any code. Applies test-first, systematic debugging, simplicity and evidence, and sends the work to agents with a model and effort sized to the task.
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
   build, and for a hot path a measurement. Say what did not run.

If the superpowers plugin is installed, its brainstorming, debugging, TDD and verification skills cover the generic
process; follow them and use this skill for the rules, tests and routing below. A project's own written rule
(`CLAUDE.md`, `.claude/rules/`, lint and build configs) beats anything here.

## Flow

1. **Size it.** A clear one-line change: do it. New or vague: read `${CLAUDE_SKILL_DIR}/references/scoping.md`,
   ask one question at a time, write the brief back, and wait for a yes before code.
2. **Look first.** Read the project's rules and test setup, then run the existing tests for a baseline.
3. **Red, green, refactor.** Python tests use pytest (`${CLAUDE_SKILL_DIR}/references/python-testing.md`), C++ tests
   use GoogleTest (`${CLAUDE_SKILL_DIR}/references/cpp-testing.md`). Read the one that applies before writing the
   first test. Refactors follow `${CLAUDE_SKILL_DIR}/references/refactor.md`.
4. **Verify.** Run the tests and the linters. For anything non-trivial, or code you wrote this session, have the
   `reviewer` agent check it; give it the diff and the tool output, not your conclusions.
5. **Commit** only when asked, through `/cv-kit:commit`.

Need sourced evidence about a model, paper or benchmark: `/cv-kit:research`. Need linters or rules installed in the
project: `/cv-kit:setup`.

## Route the work

Route yourself; do not ask the user. Pick the agent, then pass `model` and `effort` on the Agent call by how hard
the task is (the table is this skill's explicit instruction to set them):

| Task | Agent | Model | Effort |
| --- | --- | --- | --- |
| Find, read or summarise code, logs, docs | `explorer` | `claude-haiku-5-5` | low |
| Ordinary feature, bug fix, test, refactor step | `engineer` | `claude-sonnet-5-5` | medium |
| Unclear bug, cross-module design, concurrency, numerics, performance, security | `engineer` | `claude-opus-5-5` | high |
| Independent review of non-trivial or self-written code | `reviewer` | `claude-opus-5-5` | high |

Escalate one row after a failed attempt (and to `xhigh` on the last row); never resend the same prompt. Run
independent tasks, ones that share no files, in one message so they run in parallel. A brief states the goal, the
constraints, what is ruled out and the exact files; an agent knows nothing else. Check what comes back against the
output you asked for before you merge it. More detail: `${CLAUDE_SKILL_DIR}/references/routing.md`.
