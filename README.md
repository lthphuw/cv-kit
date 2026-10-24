# cv-kit

A Claude Code plugin for engineers who write Python and edge C++ and do computer-vision R&D. Four principles drive
it: test first, process over guessing, simplicity, evidence over claims. Six skills are the entry points; Claude
routes the work to agents on its own, with a model (Haiku, Sonnet or Opus 5.5) and effort sized to the task.

## Install

```
/plugin marketplace add lthphuw/cv-kit
/plugin install cv-kit@cv-kit
```

Then, once per project, run `/cv-kit:setup`. It copies the rules and strict lint configs into the project, and offers
`permissions.ask` rules so an unattended run still asks before it commits. It never overwrites a file you have.

Update with `/plugin marketplace update cv-kit` (or turn on auto-update in `/plugin`). To work on the plugin itself:
`claude --plugin-dir <path to your checkout>`.

## Use it

Describe the task in plain words and Claude picks the skill, or call one as `/cv-kit:<skill> <request>`. Name the
files, the metric or the constraint when you have them; the skill asks only for what is still missing.

### Common situations

| You want to | Say |
|---|---|
| Add a feature | `/cv-kit:develop add clamp_boxes(boxes, width, height) to vision/utils.py` |
| Fix a crash or a flaky bug | `/cv-kit:develop NMS in src/post/nms.cc crashes on zero detections` |
| Find a root cause, not a patch | `/cv-kit:develop loss goes NaN after epoch 3, only with AMP` |
| Clean up code without changing it | `/cv-kit:develop refactor this loader, it must return the same arrays` |
| Start something vague | `/cv-kit:develop we want to count pallets from CCTV, where do we start?` |
| Pick a model for a budget and licence | `/cv-kit:research which detector for 30 FPS on a Jetson Orin NX, Apache-2.0 only` |
| Check a number in a README or paper | `/cv-kit:research the DEIMv2 README claims a COCO AP I do not trust` |
| Compare code with its paper | `/cv-kit:research does the loss in the repo match the paper? clone it and read` |
| Review before merging | `/cv-kit:review the diff against main` |
| Check a split or a report | `/cv-kit:review train/val split in data/split.py, any leakage?` |
| Commit or write a message | `/cv-kit:commit` |
| Draw the architecture | `/cv-kit:figure our detector, from src/detector/model.py` |
| Prepare a new project | `/cv-kit:setup` |
| Run until a check passes | `/goal follow /cv-kit:develop. ... ctest exits 0 ... Do not commit. Or stop after 20 turns.` |
| Repeat a job on a schedule | `/loop 30m /cv-kit:review the diff against main, report only new Critical findings` |
| Route everything through one agent | `claude --agent cv-kit:lead` |
| Review in CI or a script | `claude -p "/cv-kit:review the diff against origin/main"` |

### `develop`: any code change, test first

It reads the project's rules and test setup, runs the existing tests for a baseline, writes a failing test (pytest,
GoogleTest), then the least code that passes, then shows the test and linter output. It picks `explorer`, `engineer`
or `reviewer` for each piece and sets their model and effort by difficulty.

```
/cv-kit:develop add tests for src/post/nms.cc before we touch it          # pins today's behaviour first
/cv-kit:develop migrate the dataset loader from PIL to cv2, outputs must not change
/cv-kit:develop make the preprocessing faster; measure p50 and p99 before and after
/cv-kit:develop split the work on these three modules into independent packages and run them in parallel
Where is the NMS threshold read from the config, and which functions use it? Only look.   # explorer, Haiku
```

### `research`: R&D with evidence

It writes a brief, shortlists candidates and waits for your yes, then reads papers, model cards and repos cloned at a
recorded commit into `research/<slug>/`. Every number in the answer cites a saved source; a claim it could not confirm
is listed as not found. It runs nothing from a clone unless you say yes.

```
/cv-kit:research compare DINOv2 and SigLIP2 as frozen backbones for ADE20K, numbers from the papers' tables
/cv-kit:research image search over 200k product photos with SigLIP2, what do I need and how do I evaluate it?
/cv-kit:research what is SOTA for small-object detection on VisDrone, with sources and the date
/cv-kit:research can we use this model in a commercial product? check the licence and the weights
/cv-kit:research reproduce the AP in the README in a throwaway environment     # asks first, labels it reproduced
```

### `review`: independent review

It runs the linters you have, then a `reviewer` agent (Opus) reads the change against the Python and C++ catalogues
and the CV checks. You get findings with a severity, rule ID and `path:line`, the smallest fix, and a verdict such as
`Blocking: 1 Critical, 2 Major`. It changes nothing until you say so.

```
/cv-kit:review src/camera/frame_grabber.cc, we build with -fno-exceptions
/cv-kit:review PR 142
/cv-kit:review does the mAP in report.md follow from the runs in runs/?
/cv-kit:review check the fixes for the findings you gave me earlier        # one verdict per old finding
```

For correctness and security bugs in a pull request, `/code-review` and `/security-review` are good companions.

### `commit`: commits without trailers

It shows the branch, the staged files and the full message, and commits only after your yes. A message never carries
`Co-Authored-By`, `Signed-off-by` or "Generated with"; the hook refuses one that does. Works for git and SVN.

```
/cv-kit:commit
What should the commit message say? I renamed load_weights to load_checkpoint and pinned the revision.
Reword my last commit message
Write the pull request description for this branch
```

### `figure`: hand-drawn architecture figures

It asks only what changes the figure (use, mode, font), reads every shape and count from your code, builds one HTML
file, checks the layout in Chrome and exports PNG or SVG. It tells you what it merged or left out.

```
/cv-kit:figure high-level figure of the detector for the docs page
/cv-kit:figure low-level figure with tensor shapes for the neck and head
/cv-kit:figure the whole model in numbered module panels
/cv-kit:figure what changed between v1 and v2, before and after
/cv-kit:figure the serving pipeline, offline and online phases
/cv-kit:figure same figure for a two-column paper, 240 pt wide, labels in Vietnamese
```

### `setup`: install into a project (you run it)

```
/cv-kit:setup                  # rules, lint configs, commit guard, test check
/cv-kit:setup python           # only the Python side
/cv-kit:setup cpp              # only the C++ side
/cv-kit:setup only the commit guard settings
```

It shows what it will add and waits for your yes. It never overwrites a file you have, and writes
`.claude/settings.json` only after you agree.

### Unattended runs and parallel work

```
/goal follow /cv-kit:develop. NMS handles zero detections: a new GoogleTest test fails first, then `ctest --test-dir build --output-on-failure` exits 0, no other test changes. Print the ctest summary. Do not commit. Or stop after 20 turns.
/goal follow /cv-kit:review. Review the diff against main; end with `Blocking: N Critical, M Major`; change no file. Or stop after 10 turns.
/loop 10m run pytest -q and ctest; if either fails, find the root cause with /cv-kit:develop and stop to report it
```

Name the command that proves the goal and ask for its output, since the judge reads only the transcript. More
conditions: `skills/develop/references/unattended.md`.

## What is inside

| Component | Name | What it does |
|---|---|---|
| Skill | `develop` | Any code change, test first, with agent, model and effort chosen by difficulty. |
| Skill | `research` | Evidence-backed R&D: model choice, embeddings, paper and claim checks. |
| Skill | `review` | Independent review against the strict catalogues and CV reproducibility checks. |
| Skill | `commit` | Git and SVN commits without trailers, previewed before committing. |
| Skill | `figure` | Hand-drawn architecture and pipeline figures read from code. |
| Skill | `setup` | Copies rules and lint configs into a project; manual only (`/cv-kit:setup`). |
| Agent | `explorer` | Haiku, low: finds and summarises code, read-only. |
| Agent | `engineer` | Sonnet, medium: one change, test first. |
| Agent | `researcher` | Sonnet, high: researches one candidate, returns sourced claims. |
| Agent | `claim-verifier` | Haiku, medium: re-checks claims without seeing the values. |
| Agent | `reviewer` | Opus, high: read-only review of code, configs and reports. |
| Agent | `lead` | Opus, high: optional orchestrator that only delegates. |
| Hook | `hooks/block_trailers.py` | Refuses a commit message with a trailer (`hooks/README.md`). |
| Hook | `hooks/evidence_gate.py` | After `develop` arms it, blocks a turn once if code changed and no test has passed. |

Models are named by alias, so they follow the newest version your provider offers (5.5 on the Anthropic API, older on
Bedrock, Foundry and Claude Platform on AWS). To pin one, put a full model id in the agent's `model`.

**Rules and catalogues.** `rules/` holds seven short rules (principles, evidence, commits, Python and C++ style,
pytest and GoogleTest tests) that `/cv-kit:setup` installs; the style and test rules load only for matching files.
`shared/python-style.md` (255 rules) and `shared/cpp-style.md` (394 rules, C++20 on edge devices) are the catalogues
that `review` cites. The model catalog (`shared/catalog.md`) has 64 rows. 38 are marked `verified` and 26 are marked
`UNVERIFIED`; treat an `UNVERIFIED` row as a lead to check.

## Requirements

- Claude Code 2.1.295 or later (per-call `effort` needs 2.1.292, the hooks' `onFailure` 2.1.295). `python3` on PATH.
- `figure`: Python 3.10+ and Chrome or Chromium (set `CHROME` if it is not on PATH).
- The `setup` lint configs were tested with ruff 0.17.2, mypy 2.4.0, clang-format 23.1.3, clang-tidy 23.1.3, CMake 4.4
  and GCC 13.3.

## Development

```
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python scripts/validate_plugin.py
.venv/bin/python -m pytest tests -q
claude plugin validate . --strict
```

CI (`.github/workflows/validate.yml`) also validates `plugin.json`, `skills` and `agents`. `evals/` is a trigger and
routing eval suite, run by hand before a release (`evals/README.md`).

## Licence

MIT (`LICENSE`). The models in the catalog have their own licences; check them before use.

The style catalogues paraphrase the Google Python and C++ Style Guides (© Google, CC BY 3.0); they take ideas, not
text, from the C++ Core Guidelines, and pitfalls from methylDragon's coding notes (BSD-2-Clause). The figure skill
bundles rough.js 4.6.6 (MIT) and the Patrick Hand font (SIL OFL 1.1).
