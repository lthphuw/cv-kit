# Set up strict lint and build checks

cv-kit ships configs that enforce its Python and C++ rules. They were tested with ruff 0.17.2, mypy 2.4.0, clang-format 23.1.3, clang-tidy 23.1.3, CMake 4.4 and GCC 13.

| Language | File | What it does |
|---|---|---|
| Python | `ruff.toml` | `ruff format` (80 columns, 4 spaces) and a strict `ruff check` selection with Google docstrings |
| Python | `mypy.ini` | `mypy --strict` |
| C++ | `.clang-format` | Google style, braces always, `int* p`, includes regrouped |
| C++ | `.clang-tidy` | Core Guidelines, Google, bugprone, performance, readability and naming checks, warnings as errors |
| C++ | `cmake/cv_kit_strict.cmake` | `cv_kit_strict(<target>)`: C++20, strict warnings, `-Werror`, `-fno-exceptions -fno-rtti`, `_GLIBCXX_ASSERTIONS` in Debug, `CV_KIT_SANITIZE` and `CV_KIT_TSAN` options |

The rules behind them are in `${CLAUDE_SKILL_DIR}/../../shared/python-style.md` and `${CLAUDE_SKILL_DIR}/../../shared/cpp-style.md`.

1. **Look first.** Find which languages the project has, its build system, and its existing configs: `pyproject.toml` (`[tool.ruff]`, `[tool.mypy]`), `setup.cfg`, `.ruff.toml`, `.clang-format`, `.clang-tidy`, `CMakeLists.txt`, pre-commit and CI files.
2. **Show the plan and wait.** List the files you will add and the ones that already exist. Adding config changes what every later run reports, so wait for an explicit yes.
3. **Copy.** Run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/install_configs.py" "$PWD" --lang python --lang cpp` (one `--lang` per language present). The script never overwrites a file; it lists the ones it kept. It also holds back `ruff.toml` or `mypy.ini` when the project already configures that tool in another file, because ours would silently override or be ignored by it. For a kept or held-back file, show the user the differences from ours and offer a merge; edit their file only after a yes. Re-run with `--force` only after the user confirms; it overwrites same-named files and still never writes through a symlink.
4. **Wire it in, with a yes for each edit.**
   - CMake: `include(cmake/cv_kit_strict.cmake)` and `cv_kit_strict(<target>)` for each target, and `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON` so clang-tidy can run. Another build system gets the same flags, listed in the CPP-BUILD section of the C++ catalogue.
   - `.clang-format`: replace `PROJECT_ROOT` with the directory the project's own includes start with, and add the third-party libraries it includes with angle brackets to the first `IncludeCategories` regex.
   - `.clang-tidy`: the project-specific settings (macro prefix, allowed logging and check macros, the project's result types in `bugprone-unused-return-value.CheckedReturnTypes`, per-directory files for a portability layer or device code) are listed under "Per-project settings" in the C++ catalogue; propose the values, set them after a yes.
   - Pin the tool versions in the project's dev requirements, pre-commit or CI (`ruff==0.17.2`, `mypy==2.4.0`, `clang-format==23.1.3`, `clang-tidy==23.1.3` are the tested ones).
   - Code that cannot build without exceptions (a library that throws) stays in a separate target without `cv_kit_strict`, behind a boundary that converts errors; do not drop the flag for the whole project.
5. **First run.** Run the tools and report counts per code or check, not every line. Do not mass-fix. Offer the order: a formatting-only pass as its own commit, then `ruff check --fix` safe fixes, then the rest with `/cv-kit:develop`. For a large legacy codebase, offer to turn the strict checks on per directory instead of adding suppressions.
6. **Rules for writing code.** The matching rules for Claude are installed by this skill's rules step, which copies `python-style.md` and `cpp-style.md` into `.claude/rules/`; mention it if they are not there.
