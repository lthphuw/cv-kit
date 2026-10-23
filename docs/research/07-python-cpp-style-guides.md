# 07 - Python and C++ style guides: what cv-kit took, and from where

Date: 2026-10-23. Input for the Python and C++ rules (`rules/python-style.md`, `rules/cpp-style.md`), their full
`<refs>` is the author's working folder outside this repository (clones, notes, probes); it is not published.
catalogues (`shared/python-style.md`, `shared/cpp-style.md`), the skills `py-cpp-review`, `py-cpp-refactor` and
`py-cpp-lint-setup`, the agent `py-cpp-reviewer`, `scripts/install_configs.py` and the shipped lint and build configs.

## The resources

| Resource | Revision read | Licence | What cv-kit may do with it |
|---|---|---|---|
| Google Python Style Guide, `pyguide.md` (+ `pylintrc`) in https://github.com/google/styleguide | `2ac1584cd3c9854760f02418ec24687ec1698fb8` (2026-10-21, branch `gh-pages`) | CC BY 3.0 for the guides, Apache 2.0 for code samples (`README.md:82-89`, `LICENSE`) | Paraphrase with attribution. The catalogues carry the attribution line. |
| Google C++ Style Guide, `cppguide.html` in the same repository | same commit | same | same |
| C++ Core Guidelines, `CppCoreGuidelines.md` in https://github.com/isocpp/CppCoreGuidelines (https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) | `33bcd015997f0d8e0fa0202eb66254a16f59ad8f` (2026-08-06) | Standard C++ Foundation licence: derivative works "for your personal or internal business use only" (`LICENSE:3-6`). The Markdown calls it "MIT-style" (`CppCoreGuidelines.md:12`); the `LICENSE` file is the binding text. | **Ideas only.** cv-kit is MIT and distributed, so no rule text, reason or example was copied; rules citing `CG` are cv-kit's own wording, cited by rule ID. |
| methylDragon coding notes, `Python 3/` (5 files) and `C++/` (9 files + `Bonus Notes/BONUS C++ - Headers.md`) in https://github.com/methylDragon/coding-notes | `b9dcabff04e0a29160728aeaaad18f1364067493` (2022-06-30) | BSD-2-Clause (`LICENSE`). The notes also quote third-party text (a Stack Overflow answer, Python docs, a dbader.org snippet) and link images from other sites whose licences differ; none of that was used. | Pitfalls and refactor idioms only; paraphrased. |

The user named the Google guides and the methylDragon notes in the request, and proposed the Core Guidelines
mid-task. The user then chose (in chat, 2026-10-23): combine the Core Guidelines (semantics, safety) with Google
(naming, layout, headers, feature bans); edge C++ is built without exceptions and RTTI and returns errors as values.

Clones: `<refs>/{google-styleguide,CppCoreGuidelines,coding-notes}`, outside this
repository. Read only; nothing in them was run, installed or built.

## How they were read

Eleven reader agents, disjoint scopes, each reading every line of its scope in chunks and citing `path:line`; then
four synthesis agents and one merge agent. All notes are outside the repository in
`<refs>/notes/`.

| Note | Scope | Size |
|---|---|---|
| `style-1-google-pyguide.md` | `pyguide.md` 1-4097, `pylintrc` | 944 lines, 375 tagged rules |
| `style-2-google-cpp-a.md` | `cppguide.html` 1-1864 (Background to Google-Specific Magic) | 631 lines, 223 rules |
| `style-3-google-cpp-b.md` | `cppguide.html` 1865-3801 (Other C++ Features, Inclusive Language) | 545 lines, 191 rules |
| `style-4-google-cpp-c.md` | `cppguide.html` 3802-5398 (Naming, Comments, Formatting, Exceptions to the Rules) | 1165 lines, 224 rules |
| `style-5-methyldragon-python.md` | the five Python files, 4545 lines | 692 lines, 354 items |
| `style-6-methyldragon-cpp.md` | the ten C++ files, 7475 lines | 1014 lines, 498 items |
| `style-7-cppcg-a.md` | CG 1-4295: In, P, I, F | 270 lines, 74 rules |
| `style-8-cppcg-b.md` | CG 4296-9413: C, Enum | 348 lines, 108 rules |
| `style-9-cppcg-c.md` | CG 9414-14288: R, ES, Per | 282 lines, 109 rules |
| `style-10-cppcg-d.md` | CG 14289-17129: CP, E, Con | 295 lines, 60 rules |
| `style-11-cppcg-e.md` | CG 17130-22163 (T, CPL, SF, SL, A, NR, Pro, GSL, NL), Appendix B 22268-22312, Appendix D 22886-22898 | 450 lines, 167 entries |
| `style-decisions.md` | the decisions above, given to every synthesis agent | |

The synthesis drafts are in `<refs>/drafts/` (`python-style.md`, `cpp-a.md` semantics,
`cpp-b.md` Google layer, `cpp-c.md` edge, errors and build); the merge produced `shared/cpp-style.md`.

## What the sources gave, and what cv-kit added

- **Google Python** is the base of the Python catalogue: every normative line is either a rule or listed under
  "Not adopted" there (for example pytype, which cv-kit replaces with mypy, `generator_stop`, and the guide's own
  2-space examples, which contradict its 4-space rule at `pyguide.md:1801`).
- **Google C++** gives naming, formatting, comments, header and include rules, scoping, static and global
  variables, and the feature bans (`<ratio>`, `<cfenv>`, `<filesystem>`, standard-library user-defined literals,
  C++23 features; the guide targets C++20, `cppguide.html:146`).
- **Core Guidelines** give resources and ownership (R), parameter passing and functions (F), classes (C),
  expressions and arithmetic (ES), concurrency (CP), templates (T) and performance (Per). Every E rule was
  translated into the no-exceptions policy or listed as not adopted (E.2, E.3, E.14, E.15, E.18, E.31 assume
  exceptions; C.147 and Type.2 assume RTTI).
- **methylDragon** supplied pitfalls; several of its own examples are wrong (a header guard written with `#ifdef`,
  an atomic flag used to skip a condition-variable lock, which loses wakeups, `system_clock` deadlines, a Python
  mutable-default memo dict, bare `except:`). The catalogues use them as things to catch, never as advice.
- **cv-kit's own rules**: the CV/ML Python rules (explicit RNGs, documented array shape, layout, dtype and colour
  order, inference mode, device syncs in loops) and the edge C++ rules (per-frame hot paths without allocation,
  blocking I/O or long locks, bounded queues, joined threads, checked CUDA / TensorRT / ONNX Runtime calls,
  numerics without `-ffast-math`, alignment and type punning). Rules that rest on experience rather than a source
  say `(experience)`.

## Tools: what was verified, with which versions

All in a scratch virtualenv outside the repository (`<refs>/lint-venv`, from PyPI):
ruff 0.17.2, mypy 2.4.0, clang-format 23.1.3, clang-tidy 23.1.3, cmake 4.4.4, ninja; GCC 13.3 from the system.

- Every ruff code cited in the Python catalogue was checked with `ruff rule`, and against the resolved set the
  shipped `ruff.toml` enables (599 codes). Every clang-tidy check cited in the C++ catalogue exists in 23.1.3; a
  check is cited as enforcing a rule only if the shipped `.clang-tidy` enables it. `clang-tidy --verify-config`
  reports unknown option names, so the shipped option keys are known to be real.
- `tests/test_lint_configs.py` runs the shipped configs on good and bad samples with the real tools, and builds a
  CMake project with `cv_kit_strict()` under ASan and UBSan. CI installs the pinned versions.
- Facts measured with probes (g++ 13.3, x86-64) that the C++ rules rely on: under `-fno-exceptions` a failed
  `new`, `vector::reserve`, `.at()`, `std::get` on the wrong alternative, `optional::value()`, and a failed
  `std::thread` creation all abort; `new (std::nothrow)` returns null; `std::vector` growth copies elements whose
  move constructor is not `noexcept` even with exceptions off; `_GLIBCXX_ASSERTIONS` turns an out-of-range
  `operator[]` into an abort; `-O2 -ffast-math` folds `std::isnan` to false and linking with it flushes subnormals
  process-wide; plain `-Wcast-align` is silent on x86-64 while `-Wcast-align=strict` fires; clang-tidy's noexcept
  checks stay silent when the compile command has `-fno-exceptions` (so the shipped `.clang-tidy` adds
  `-fexceptions` to its own arguments); clang-tidy over a GCC `compile_commands.json` fails on GCC-only warning
  flags without `-Wno-unknown-warning-option`; TSan in GCC 13 fails at start-up on Linux kernel 7.0 unless run under
  `setarch -R`.
- Config defects found and fixed before shipping: the naming options rejected every Google header guard
  (`UPPER_CASE` with a trailing `_`) and static members named `name_`; `readability-uppercase-literal-suffix`
  demanded `1.0F`; `cppcoreguidelines-pro-bounds-avoid-unchecked-container-access` and
  `-constant-array-index` flag every `v[i]` and suggest `.at()` / `gsl::at`, which abort without exceptions (both
  disabled); ruff's `TD003` rejects Google's `TODO(b/123)` form and `TRY003` fights the required interpolated error
  messages (both ignored).

## Not verified

AArch64 and armv7 behaviour (no cross compiler was installed), a full Clang build of the CMake module, libc++
hardening, TensorRT, OpenCV and V4L2 specifics (headers not installed), and numpy or torch types under mypy.
