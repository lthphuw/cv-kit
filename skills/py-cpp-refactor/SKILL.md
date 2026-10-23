---
name: py-cpp-refactor
description: Use when asked to refactor, clean up, modernise or restructure Python or C++ code without changing what it does, or to bring existing code in line with the strict Python and C++ rules (Google Python style; C++ Core Guidelines plus Google C++ style for edge devices).
---

# Refactor Python and C++ without changing behaviour

A refactor changes structure, not behaviour. The target rules and the recipes are in the catalogues; every step names the recipe it applies and the rule IDs it fixes.

- Python: `${CLAUDE_SKILL_DIR}/../../shared/python-style.md` (section "Refactor recipes", `R-PY-n`)
- C++: `${CLAUDE_SKILL_DIR}/../../shared/cpp-style.md` (section "Refactor recipes", `R-CPP-n`)

## 1. Agree on scope
State the files or functions, the goal (which rule IDs or which smell), and what must not change: the public API and ABI, file and wire formats, numeric outputs (with the tolerance), log and error text other code parses, and on edge targets the latency and memory budget. Changing a public name, signature or ABI needs an explicit yes. Read the project's own rules first (`CLAUDE.md`, `.claude/rules/`, lint and build configs); they win over the catalogue.

## 2. Pin the behaviour first
Find the tests that cover the code and run them; record the command and the result. If nothing covers it, write characterisation tests before touching the code: real inputs, the outputs the code gives today, and the edge cases (empty input, one element, the largest size, invalid input and its error). For numeric code, compare against saved outputs with a stated tolerance. For a C++ hot path, also record latency (p50 and p99, hardware, precision, batch, warm-up) and peak memory if the refactor could change them. If the code cannot be tested as it is, the first step is the smallest seam that makes it testable, and nothing else.

## 3. Plan in small steps
List the steps before editing. Each step applies one recipe and one concern. Formatting (`ruff format`, `clang-format`) is a step of its own, first or last, never mixed with logic. Show the plan; for more than a handful of steps, wait for a yes.

## 4. One step at a time
For each step: edit, then run the tests, the linters and (C++) the strict build. If anything fails, undo that step only and rethink it. Never change behaviour and structure in the same step.
- A bug found on the way is not fixed silently: report it and ask. Its fix is a separate change with its own test.
- No new dependency, no new abstraction with a single user, no speculative extension point.
- Never weaken or delete a test, and never add a suppression (`# noqa`, `// NOLINT`, `# type: ignore`) to make a tool pass. A suppression that is truly needed names the check and the reason, and the user agrees to it.
- C++ edge code: keep `-fno-exceptions -fno-rtti` builds green; after a step that touches a per-frame path, re-measure before saying it is faster or no slower.

## 5. Finish
Report: the steps done with their recipe and rule IDs, the test and tool commands with their results, what was left undone and why, and anything whose behaviour may differ (with the evidence that it does not). Offer the `py-cpp-review` skill on the result. Commit only when asked, with the `commit-vcs` skill.
