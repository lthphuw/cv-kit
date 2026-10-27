# cv-kit

A Claude Code plugin for computer-vision engineers who write Python and edge C++. It turns an engineering question into
a tested change, a sourced model comparison, a review or a figure, and keeps the evidence in the repository.

- **Who it is for:** engineers who train, evaluate or deploy vision models, and write the code around them: data
  loaders, post-processing, and C++ inference on Jetson, ARM boards or phones.
- **What it solves:**
  - Code changes land with a failing test first, and the literal test output.
  - Model, paper and benchmark claims are checked against saved sources, not memory; licences are stated, or marked unverified.
  - Reviews look for what breaks CV results: train/validation leakage, preprocessing mismatch, numbers the runs do not support.
  - Architecture figures are drawn from the code, not from memory.
  - Commits carry no AI trailers, and each is previewed before it is made.

## Contents

- [Quick start](#quick-start)
- [Skills and example tasks](#skills-and-example-tasks)
- [Goals and example projects](#goals-and-example-projects)
- [Install and requirements](#install-and-requirements)
- [Configuration](#configuration)
- [Limitations](#limitations)
- [Reference and development](#reference-and-development)
- [Licence](#licence)

## Quick start

Install the plugin in Claude Code:

```
/plugin marketplace add lthphuw/cv-kit
/plugin install cv-kit@cv-kit
```

Once per project, copy the rules and lint configs (`python`, `cpp`, or omit for both):

```
/cv-kit:setup python
```

Then ask for a change:

```
/cv-kit:develop add clamp_boxes(boxes, width, height) to vision/utils.py
```

Deliverable: a test that fails first, the least code that passes it, and the output of the test run.

## Skills and example tasks

| Skill | Use it for | Deliverable |
|:------|:-----------|:------------|
| `/cv-kit:develop` | Features, bug fixes, refactors, benchmark code | Failing test, minimal fix, command output |
| `/cv-kit:research` | Choosing, comparing or checking a model, paper number or licence | `research/<slug>/report.md` with saved sources and checked claims |
| `/cv-kit:review` | Review of code, a diff, a pipeline or a report | Findings with rule IDs and `path:line`, and `Blocking: N Critical, M Major` |
| `/cv-kit:figure` | Architecture, pipeline and model diagrams for docs or papers | Figure spec, self-contained HTML, PNG (and SVG for papers) |
| `/cv-kit:commit` | Git or SVN commit messages | Preview of branch, files and message; commit only after your yes |
| `/cv-kit:setup` | Installing rules and lint configs into a project | Files in `.claude/rules/` and lint configs; existing files kept |

### Examples

- **Fix a crash:** `/cv-kit:develop NMS in src/post/nms.cc crashes on zero detections`
  gives a GoogleTest that reproduces the crash, the guard, and the `ctest` output.
- **Refactor with a fixed contract:** `/cv-kit:develop refactor this loader, it must return the same arrays`
  pins the current behaviour in tests first, then changes the code.
- **Pick a model:** `/cv-kit:research which detector for 30 FPS on a Jetson Orin NX, Apache-2.0 only`
  builds a brief, asks you to approve a shortlist, saves sources, and has a second agent re-read each claim.
- **Check a claim:** `/cv-kit:research the DEIMv2 README claims a COCO AP I do not trust`
  answers `confirmed`, `partly right`, `contradicted` or `not found`, with the corrected sentence.
- **Review for leakage:** `/cv-kit:review train/val split in data/split.py, any leakage?`
  returns findings with the rule ID, the file and line, and what triggers each.
- **Review in CI:** `claude -p "/cv-kit:review the diff against origin/main"`
- **Draw a figure:** `/cv-kit:figure low-level figure with tensor shapes for the neck and head`
  reads the shapes from the code and labels any fact it cannot confirm.
- **Commit:** `/cv-kit:commit` shows the message and the staged files, and commits after your yes.

### Autonomous runs

`/goal` keeps working until a condition holds; `/loop` repeats a prompt on an interval. Name the command that proves
the result and a turn limit in the condition. Example:

```
/goal follow /cv-kit:develop. NMS handles zero detections: a new GoogleTest test fails first, then
  ctest --test-dir build --output-on-failure exits 0. Do not commit. Or stop after 20 turns.
```

Ask `/cv-kit:develop write the /goal line for the NMS crash` to draft one without changing code. More templates:
`skills/develop/references/goal-loop-templates.md`.

### What is inside

| Component | Name | What it does |
|:----------|:-----|:-------------|
| Skill | `develop` | Code changes, test first, with agent/model/effort chosen by difficulty |
| Skill | `research` | Evidence-backed R&D: model choice, paper and claim checks |
| Skill | `review` | Independent review against strict catalogues and CV checks |
| Skill | `commit` | Git/SVN commits without trailers, previewed before committing |
| Skill | `figure` | Hand-drawn architecture and pipeline figures read from code |
| Skill | `setup` | Copies rules and lint configs into a project |
| Agent | `explorer` | Haiku, low effort — finds and summarises code, read-only |
| Agent | `engineer` | Sonnet, medium effort — one change, test first |
| Agent | `researcher` | Sonnet, high effort — researches one candidate, returns sourced claims |
| Agent | `claim-verifier` | Haiku, medium effort — re-checks claims without seeing original values |
| Agent | `reviewer` | Opus, high effort — read-only review of code, configs, and reports |
| Agent | `lead` | Opus, high effort — optional orchestrator that only delegates (`claude --agent cv-kit:lead`) |
| Hook | `block_trailers.py` | Refuses a commit message with a trailer |
| Hook | `evidence_gate.py` | Blocks a turn if code changed but no test passed |
| Hook | `concise.py` | Keeps replies and code short in every session and subagent (rules adapted from ponytail, MIT) |

---

## Goals and example projects

**Goal.** Take a computer-vision engineer from an engineering question to a tested, reproducible implementation, with
every number traced to its source. cv-kit provides the skills, agents, rules, hooks and checks. It does not train
models, ship benchmark harnesses or measure hardware. You run those; cv-kit writes and checks the code and reports
around them.

The projects below are illustrative. Each row separates what the plugin does today from what you provide.

| Example project | cv-kit supports today | You provide |
|:----------------|:----------------------|:------------|
| **Face detector for a Raspberry Pi 3B+** | `research` gathers candidates from papers, model cards and repositories, checks licences and cites each number. `review` checks that reported numbers match their runs and split. | The candidates and the face dataset with its split. The catalogue has no face-detector rows yet, so the first step adds sources. On-device latency and memory, measured with the protocol in `shared/metrics.md`. |
| **Face quality assessment** (blur, exposure, pose, occlusion) | `research` compares quality-assessment approaches. `develop` writes the filter and its tests. `review` flags thresholds tuned on the test set. | Labelled images from your cameras, and the threshold study. No quality models are catalogued. |
| **Edge deployment and quantisation** | `develop` writes inference code in Python and C++ (the C++ rules assume `-fno-exceptions`). `review` checks style and build flags. `research` compares runtimes and formats from sources. | The target device, the build, and the measured latency, precision and batch for each variant. |
| **Robustness and regression tests** | `develop` writes regression tests for a pipeline. `review` looks for preprocessing mismatch and leakage. | Test images and their conditions: lighting, blur, occlusion, camera. |
| **R&D decision report** | `research` runs the pipeline: scouts, researchers, claim check, `report.md`. Numbers are compared only when dataset, split, resolution and hardware match. | The decision the report supports, and the experiments it calls for. |

## Install and requirements

- **Claude Code** 2.1.295 or later, with `python3` on PATH. The eval suite needs 2.1.310 or later.
- **figure skill:** Python 3.10 or later, and Chrome or Chromium (set `CHROME` if it is not on PATH). A snap Chromium
  cannot read `/tmp` or hidden folders; use a visible folder under your home.
- **Lint configs tested with:** ruff 0.17.2, mypy 2.4.0, clang-format 23.1.3, clang-tidy 23.1.3, CMake 4.4, GCC 13.3.
- **Update:** `/plugin marketplace update cv-kit`

## Configuration

- **Project rules and lint.** `/cv-kit:setup` copies `rules/*.md` into `.claude/rules/` and the ruff, mypy, clang-format,
  clang-tidy and CMake files into the project. It never overwrites an existing file and never edits `CLAUDE.md`. It
  offers commit-guard permissions and merges them into `.claude/settings.json` only after your yes.
- **Refresh rules.** From a clone of this repo, `python3 scripts/install_rules.py <project> --force` overwrites the copied rules.
- **Models.** Agents use the aliases `haiku`, `sonnet` and `opus`. To pin a version, set a full model ID in an agent's
  `model` field (`agents/*.md`).
- **Hooks.** Defined in `hooks/hooks.json`. To switch off the concise rules, remove the two `concise.py` entries. The
  evidence gate keeps its ledger in `~/.cache/cv-kit/gate/`; set `CV_KIT_GATE_DIR` to move it. See `hooks/README.md`.

## Limitations

- **The evidence gate is a nudge.** It holds a turn after a code edit until a test command passes. It cannot tell that
  the right tests ran.
- **The commit hook has known gaps** (for example `git commit --amend --no-edit` and commits wrapped in `bash -c`).
  It is a guard, not a guarantee. See `hooks/README.md`.
- **Models and licences change.** Catalogue rows marked `UNVERIFIED` have not been checked. Re-check licences at release.
- **No benchmark harness, training loop or dataset tools.** Measured numbers come from your runs.
- **Costs.** `lead` runs on Opus, and `reviewer` defaults to Opus; `develop` sends routine reviews to Sonnet. The eval
  suite calls the API and is run by hand.

## Reference and development

- **Maintained references in this repo:** `shared/catalog.md` (models), `shared/metrics.md` (metric definitions and the
  latency protocol), `shared/licenses.md`, `shared/sources.md`, the style catalogues `shared/python-style.md` and
  `shared/cpp-style.md`, `hooks/README.md`, and `evals/README.md`.
- **Design research notes:** `docs/research/` records the sources consulted, their licences and what was adopted.
- **Set up for development:**

  ```
  python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
  .venv/bin/python scripts/validate_plugin.py
  .venv/bin/python -m pytest tests -q
  claude plugin validate . --strict
  ```

- **CI** (`.github/workflows/validate.yml`) runs the same checks, installs the lint-config versions above, and renders
  the figure templates.
- **Contributing:** run the four commands above before a pull request. Write a failing test before a plugin change, as
  `rules/principles.md` requires. Keep skill descriptions under the 8000-character total the validator allows, and start
  each with "Use when".
  Run the trigger evals with `scripts/run_evals.sh` before a release (see `evals/README.md`).

---

## Licence

MIT. See `LICENSE`.

The models in the catalogue have their own licences; check them before use. The style catalogues paraphrase the Google
Python and C++ Style Guides (CC BY 3.0), take ideas from the C++ Core Guidelines, and pitfalls from methylDragon's coding
notes (BSD-2-Clause). The figure skill bundles rough.js 4.6.6 (MIT) and the Patrick Hand font (SIL OFL 1.1).
