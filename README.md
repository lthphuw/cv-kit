# cv-kit

A Claude Code plugin for computer-vision engineers: scope a CV task, choose a model by task, budget and licence,
build embedding and retrieval pipelines, back a decision with sourced papers, draw hand-drawn architecture
figures, review, refactor and lint Python and edge C++ against strict rules, and keep commits free of trailers.

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
| Skill | `cv-brainstorm` | Scopes a new or underspecified CV task before any model or code. |
| Skill | `cv-model-selection` | Picks a detector, segmenter, keypoint model, encoder or VLM for a stated task, budget and licence. |
| Skill | `cv-deep-research` | Sourced comparison of models, backbones, heads or losses; checks a single benchmark claim. |
| Skill | `cv-embeddings-retrieval` | CLIP, SigLIP and DINO embeddings, zero-shot classification, retrieval, linear probes. |
| Skill | `ai-workflow-figure` | Hand-drawn architecture and pipeline figures read from a model's code; exports SVG and PNG. |
| Skill | `py-cpp-review` | Reviews Python or C++ against the strict catalogues; findings carry a rule ID and a severity. |
| Skill | `py-cpp-refactor` | Behaviour-preserving refactors: pin behaviour with tests, then small steps. |
| Skill | `py-cpp-lint-setup` | Installs ruff, mypy, clang-format, clang-tidy and a strict CMake module. |
| Skill | `commit-vcs` | Git and SVN commit messages without trailers, previewed before committing. |
| Skill | `install-rules` | Copies the rules below into a project; run it as `/cv-kit:install-rules`. |
| Agent | `py-cpp-reviewer` | Independent read-only Python and C++ review. |
| Agent | `cv-reviewer` | Read-only review of CV code, configs and reports: leakage, preprocessing, licences, unsupported numbers. |
| Agent | `model-scout` | Researches one candidate model for the deep-research workflow. |
| Agent | `claim-verifier` | Re-checks every claim in a research ledger without seeing the scouts' values. |
| Hook | `hooks/block_trailers.py` | Refuses a `git commit` or `svn commit` whose message carries a trailer (details and known gaps: `hooks/README.md`). |

The model catalog (`shared/catalog.md`) has 64 rows. 38 are marked `verified` and 26 are marked `UNVERIFIED`;
treat an `UNVERIFIED` row as a lead to check.

## Python and C++ rules

`shared/python-style.md` (255 rules, Google Python style plus CV/ML rules) and `shared/cpp-style.md` (394 rules for
C++20 on edge devices: C++ Core Guidelines for semantics, Google C++ style for naming and layout, built without
exceptions or RTTI, allocation-free per-frame paths). Every rule has an ID, a severity, a check and a source.

## Rules

`rules/` holds six short rules: commits, licence callouts, verified identifiers, pinned revisions, and Python and C++
style. A plugin cannot load rules, so `/cv-kit:install-rules` copies them to your project's `.claude/rules/`; it never
overwrites a file. The two style rules load only when Claude reads or edits a matching file.

## Requirements

- `ai-workflow-figure`: Python 3.10+ and Chrome or Chromium (set `CHROME` if it is not on PATH).
- `py-cpp-lint-setup` configs were tested with ruff 0.17.2, mypy 2.4.0, clang-format 23.1.3, clang-tidy 23.1.3,
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
