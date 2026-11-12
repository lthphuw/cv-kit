# Set up a project

Use this when the user asks to set cv-kit up in a project, or when a step needs a linter config or test runner the
project lacks. Each step changes what every later run reports, so show the plan first and wait for a yes; the request to set the project up is not that yes. The scripts
never overwrite a file that exists.

1. **Rules.** A plugin cannot ship `.claude/rules`, so `develop` reads them from `${CLAUDE_SKILL_DIR}/../../rules/`.
   To make them load in every session, `develop` or not, run
   `python3 "${CLAUDE_SKILL_DIR}/../../scripts/install_rules.py" "$PWD"`. It copies `rules/*.md` into
   `.claude/rules/` and lists the files it kept; ask before re-running with `--force`. A destination that is a symlink
   or a directory is always kept, and a symlinked `.claude` or `.claude/rules` is refused. Do not edit `CLAUDE.md`.
2. **Lint and build configs.** Follow `${CLAUDE_SKILL_DIR}/references/lint-setup.md`, once per language the project
   has (look first: `pyproject.toml`, `CMakeLists.txt`, existing `.clang-*`, pre-commit and CI).
3. **Permissions for unattended runs.** Offer `${CLAUDE_SKILL_DIR}/references/settings.md`, show the JSON, and merge
   it into `.claude/settings.json` only after a yes.
4. **Tests.** Check the project runs its tests the way this skill expects: `pytest` for Python, `go test` for Go,
   GoogleTest through CMake `FetchContent` pinned to a commit for C++ (`cpp-testing.md`). Offer what is missing; do
   not add it unasked.
5. **Report** what was copied, what was kept and why, and the one command that runs each tool.
