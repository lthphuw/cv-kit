---
name: setup
description: Use when the user asks to install cv-kit into a project, to copy its rules (commits, evidence, principles, Python and C++ style and tests) into `.claude/rules/` and add the strict lint and build configs (ruff, mypy, clang-format, clang-tidy, CMake warning flags). Run as /cv-kit:setup.
disable-model-invocation: true
argument-hint: "[python, cpp or both]"
---

# Set up cv-kit in a project

A plugin cannot ship `.claude/rules` or tool configs, so this skill copies them. Both steps change what every later
run reports, so show the plan first and wait for a yes. Neither step overwrites a file that exists.

1. **Rules.** Follow `${CLAUDE_SKILL_DIR}/references/install-rules.md`. It copies `rules/*.md` into
   `.claude/rules/` and never edits `CLAUDE.md`.
2. **Lint and build configs.** Follow `${CLAUDE_SKILL_DIR}/references/lint-setup.md`, once per language the project
   has (look first: `pyproject.toml`, `CMakeLists.txt`, existing `.clang-*`, pre-commit and CI).
3. **Commit guard.** Offer the settings in `${CLAUDE_SKILL_DIR}/references/settings.md`, show the JSON, and merge it
   into `.claude/settings.json` only after a yes.
4. **Tests.** Check the project can run its tests the way `/cv-kit:develop` expects: `pytest` for Python,
   GoogleTest through CMake `FetchContent` pinned to a commit for C++
   (`${CLAUDE_SKILL_DIR}/../develop/references/cpp-testing.md`). Offer to add what is missing; do not add it unasked.
5. **Report** what was copied, what was kept and why, and the one command to run each tool.
