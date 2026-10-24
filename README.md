# cv-kit

A Claude Code plugin for engineers who write Python and edge C++ and do computer-vision R&D. Four principles drive
it: test first, process over guessing, simplicity, and evidence over claims. Six skills are the entry points; Claude
routes the work to agents on its own, with a model (Haiku 5.5, Sonnet 5.5 or Opus 5.5) and an effort level sized to
how hard the task is.

## Install

```
/plugin marketplace add lthphuw/cv-kit
/plugin install cv-kit@cv-kit
```

Updates arrive when the plugin `version` changes: turn on auto-update in `/plugin` > Marketplaces > cv-kit, or run
`/plugin marketplace update cv-kit`. To develop locally: `claude --plugin-dir <path to your checkout>`.

## What is inside

| Component | Name | What it does |
|---|---|---|
| Skill | `develop` | Any code change, scoped and routed: test first (pytest for Python, GoogleTest for C++), systematic debugging, behaviour-preserving refactors, and agent, model and effort chosen by difficulty. |
| Skill | `research` | R&D with evidence: model selection, embeddings and retrieval, paper and benchmark comparison, claim checks. Sources and cloned repositories go in `research/<slug>/`. |
| Skill | `review` | Independent review of Python or C++ against the strict catalogues, plus CV leakage and reproducibility checks; findings carry a rule ID and a severity. |
| Skill | `commit` | Git and SVN commit messages without trailers, previewed before committing. |
| Skill | `figure` | Hand-drawn architecture and pipeline figures read from a model's code; exports SVG and PNG. |
| Skill | `setup` | Copies the rules and the strict lint and build configs into a project; run it as `/cv-kit:setup`. |
| Agent | `explorer` | Haiku 5.5, low effort: finds and summarises code, logs and docs, read-only. |
| Agent | `engineer` | Sonnet 5.5, medium effort: makes one change test first. |
| Agent | `researcher` | Sonnet 5.5, high effort: researches one candidate and returns sourced claims. |
| Agent | `claim-verifier` | Haiku 5.5, medium effort: re-checks every claim without seeing the researchers' values. |
| Agent | `reviewer` | Opus 5.5, high effort: read-only review of code, configs and reports. |
| Hook | `hooks/block_trailers.py` | Refuses a `git commit` or `svn commit` whose message carries a trailer (details and known gaps: `hooks/README.md`). |

Each agent's frontmatter holds its default model and effort. The `develop` skill raises or lowers them per call:
Opus 5.5 with high effort for an unclear bug, concurrency, numerics, performance or security work, and one step up
after a failed attempt.

The model catalog (`shared/catalog.md`) has 64 rows. 38 are marked `verified` and 26 are marked `UNVERIFIED`;
treat an `UNVERIFIED` row as a lead to check.

## Python and C++ rules

`shared/python-style.md` (255 rules, Google Python style plus CV/ML rules) and `shared/cpp-style.md` (394 rules for
C++20 on edge devices: C++ Core Guidelines for semantics, Google C++ style for naming and layout, built without
exceptions or RTTI, allocation-free per-frame paths). Every rule has an ID, a severity, a check and a source.

## Rules

`rules/` holds seven short rules: working principles, evidence (verified ids, licences, pinned revisions, the research
folder), commits, Python style, C++ style, Python tests (pytest) and C++ tests (GoogleTest). A plugin cannot load rules,
so `/cv-kit:setup` copies them to your project's `.claude/rules/`; it never overwrites a file. The style and test rules
load only when Claude reads or edits a matching file. The test rules follow roboflow/rf-detr (`AGENTS.md`,
`CONTRIBUTING.md`) and google/googletest.

## Requirements

- `figure`: Python 3.10+ and Chrome or Chromium (set `CHROME` if it is not on PATH).
- The `setup` lint configs were tested with ruff 0.17.2, mypy 2.4.0, clang-format 23.1.3, clang-tidy 23.1.3,
  CMake 4.4 and GCC 13.3.
- The commit hook needs `python3` on PATH.

## Development

```
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python scripts/validate_plugin.py
.venv/bin/python -m pytest tests -q
claude plugin validate . --strict
```

CI (`.github/workflows/validate.yml`) also validates `.claude-plugin/plugin.json`, `skills` and `agents`, and installs
the lint tools so `tests/test_lint_configs.py` runs them. `evals/` is a trigger eval suite, run by hand before a
release (`evals/README.md`).

## Licence

MIT (`LICENSE`). The models in the catalog have their own licences; check them before use.

The style catalogues paraphrase the Google Python and C++ Style Guides (© Google, CC BY 3.0); they take ideas, not
text, from the C++ Core Guidelines, and pitfalls from methylDragon's coding notes (BSD-2-Clause). The figure skill
bundles rough.js 4.6.6 (MIT) and the Patrick Hand font (SIL OFL 1.1).
