# cv-kit

A Claude Code plugin for computer-vision engineers who write Python, edge C++ and Go: people who train, evaluate or
deploy vision models and write the loaders, post-processing and on-device inference around them. You type one prompt;
cv-kit routes it to agents sized to the task. Code lands test first with the literal test output. Model and paper
numbers come from saved sources, never memory. Reviews hunt for leakage and preprocessing mismatch. Figures are read
from the code, and commits carry no AI trailers.

## Contents

- [Quick start](#quick-start)
- [How a prompt is routed](#how-a-prompt-is-routed)
- [Autonomous runs](#autonomous-runs)
- [Configuration](#configuration)
- [Limitations](#limitations)
- [Reference and development](#reference-and-development)
- [Licence](#licence)

## Quick start

Needs Claude Code 2.1.295 or later with `python3` on PATH (the eval suite needs 2.1.310). The `figure` skill also needs
Python 3.10+ and Chrome or Chromium (`CHROME` if not on PATH; a snap Chromium cannot read `/tmp` or hidden folders).

```
/plugin marketplace add lthphuw/cv-kit        # install
/plugin install cv-kit@cv-kit

/plugin marketplace update cv-kit             # update to the latest release
/reload-plugins

/cv-kit:setup python                          # once per project: rules + lint configs (python, cpp, or both)
```

Then ask for work in plain words or with a skill name:

```
/cv-kit:develop add clamp_boxes(boxes, width, height) to vision/utils.py
```

## How a prompt is routed

You do not pick agents. A skill fires from its name or from plain words ("NMS crashes on empty input" loads
`develop`, "which detector for a Jetson" loads `research`), sizes the task and dispatches agents with a model and
effort to match. While agents run, each one has a live row under the prompt; when one finishes, the main thread prints
a `Progress` block without being asked; a finished task ends with `Summarization:` and `Next:` prompts to paste.

### `/cv-kit:develop`

```
you ─► /cv-kit:develop add iou(a, b) and clamp(box, w, h) to vision/
         │
         ├─ size it: clear one-liner → done inline │ new or vague → one question at a time, brief, your yes
         ├─ look first: project rules, test setup, baseline test run        (explorer · haiku · low)
         ├─ red → green → refactor, file-disjoint tasks in parallel         (engineer · sonnet · medium)
         │     unclear bug, numerics, threads, perf, security → engineer · opus · high
         ├─ verify: tests + linters; review by risk                         (reviewer · sonnet or opus)
         └─ report: cause with path:line, tests by name, literal command output

live rows while it runs:
  engineer · sonnet · 1m42s · 18.4k tok · running · Add iou with tests
  engineer · sonnet · 1m40s · 16.9k tok · running · Add clamp with tests

● Progress (1/2 done):
  - cengineer#1 iou: 5 tests pass
  - engineer#2 clamp: running

● I didn't review the code itself, only the test results.
  Summarization:
  - iou(a, b) is in vision/utils.py and reuses the existing area; tests in tests/test_iou.py.
  - clamp(box, w, h) is in the new vision/clamp.py, with tests in tests/test_clamp.py.
  - pytest -q: 9 passed, including the existing test_utils.py.
  - Nothing is committed.
  Next:
  - /cv-kit:review the diff against main
  - /cv-kit:commit
```

### `/cv-kit:research`

```
you ─► /cv-kit:research which detector for 30 FPS on a Jetson Orin NX, Apache-2.0 only
         │
         ├─ frame: brief.md (task, metric, split, hardware, latency, licence); asks for what is missing
         ├─ scout: arXiv, HF Papers, CVF, GitHub → one line per candidate; "which models do you expect?"
         ├─ shortlist: excluded by licence, task, weights, traceable numbers, stack → you approve (≤ 6 advance)
         ├─ deep-read, one per candidate, in parallel                       (researcher · sonnet · high)
         ├─ cross-check, blind to the scouts' values                        (claim-verifier · haiku · medium)
         └─ research/<slug>/report.md   Overview · ≤ 7 key points · Comparison · ≤ 3 next steps (≤ 400 words)
            research/<slug>/appendix.md exclusions, not found, caveats, claims ledger, sources

chat shows only:
  Overview: 3–6 sentences, the pick, the main risk, confidence medium.
  Report: research/jetson-detector/report.md
  Next:
  - /cv-kit:develop the first next step in research/jetson-detector/report.md
```

A single claim ("the DEIMv2 README claims a COCO AP I do not trust") skips the pipeline and answers `confirmed`,
`partly right`, `contradicted` or `not found`, with the corrected sentence.

### `claude --agent cv-kit:lead`

Starts a session whose main thread only delegates: it loads the skill for the work and sends every read, edit, piece
of evidence and review to an agent, then reruns the commands they name before trusting them.

| Task | Agent | `model` | `effort` |
|:-----|:------|:--------|:---------|
| Find, read, summarise code, logs, docs | `explorer` | `haiku` | low |
| Ordinary feature, bug fix, test, refactor step | `engineer` | `sonnet` | medium |
| Unclear bug, cross-module, concurrency, numerics, performance, security | `engineer` | `opus` | high |
| Evidence for one candidate model | `researcher` | `sonnet` | high |
| Blind re-check of the claims | `claim-verifier` | `haiku` | medium |
| Review of a Hard change, numerics, security, a published number | `reviewer` | `opus` | high |
| Review of a routine change whose tests and linters pass | `reviewer` | `sonnet` | medium |

A failed attempt escalates one row (the last to `xhigh`); the same prompt is never resent.

### Every skill and agent

| Kind | Name | Prompt → what you get |
|:-----|:-----|:----------------------|
| Skill | `develop` | `NMS in src/post/nms.cc crashes on zero detections` → a GoogleTest that reproduces it, the guard, `ctest` output. `refactor this loader, same arrays` → behaviour pinned in tests first. |
| Skill | `research` | `which detector for 30 FPS on Orin NX, Apache-2.0` → short report with checked claims. `CLIP or SigLIP embeddings for retrieval` → normalisation and indexing from sources. |
| Skill | `review` | `train/val split in data/split.py, any leakage?` → findings with rule ID and `path:line`, ending `Blocking: N Critical, M Major`. In CI: `claude -p "/cv-kit:review the diff against origin/main"`. |
| Skill | `figure` | `low-level figure with tensor shapes for the neck and head` → spec, HTML, PNG (SVG for papers); facts it cannot confirm are labelled. |
| Skill | `commit` | `/cv-kit:commit` → branch, staged files and message shown; commits after your yes, no trailers. |
| Skill | `setup` | `/cv-kit:setup cpp` → `.claude/rules/` and lint configs; existing files kept. |
| Agent | `explorer` | Haiku, low: finds and summarises code, read-only. |
| Agent | `engineer` | Sonnet, medium: one change, test first. |
| Agent | `researcher` | Sonnet, high: one candidate, sourced claims in JSON. |
| Agent | `claim-verifier` | Haiku, medium: re-reads each claim's source without seeing the claimed value. |
| Agent | `reviewer` | Opus, high: read-only review of code, configs and reports. |
| Agent | `lead` | Opus, high: the delegating main thread above. |

Hooks: `concise.py` (short replies, the `STATUS` line in every agent report, the Progress, Summarization and Next
blocks in the main thread), `evidence_gate.py` (holds a turn after a code edit until a test passes),
`block_trailers.py` (refuses a commit message with a trailer). Status line: `agent_status.py` (the live rows).

## Autonomous runs

`/goal <condition>` keeps working until a model judging the transcript says the condition holds; `/loop [interval]
<prompt>` repeats a prompt. Name the skill, the command that proves the result, what must not change, and a turn limit.
Run them in auto mode.

```
/goal follow /cv-kit:develop ... Or stop after 25 turns.
  │
  turn 1    develop: brief from the condition, baseline tests
  turn 2-n  engineer(s): failing test → fix → green           Progress blocks as agents finish
  turn n+1  reviewer: Blocking: 0 Critical, 0 Major
  turn n+2  commit: preview → your yes (permissions.ask prompts even in auto mode)
  turn n+3  git push / gh pr create                           only if the condition says so
  end       the judge reads the literal test output → goal met, or it stops at the turn limit
```

End to end, from change to pull request:

```
/goal follow /cv-kit:develop. clamp_boxes in vision/utils.py clips xyxy boxes and drops empty ones; a new pytest test failed first, then `pytest -q` exits 0 and `ruff check .` is clean. Then /cv-kit:review the diff against main until it ends with `Blocking: 0 Critical, 0 Major`. Then /cv-kit:commit, push the branch and open a PR with `gh pr create`. Print each output. Or stop after 25 turns.
```

Fix only, nothing committed:

```
/goal follow /cv-kit:develop. NMS in src/post/nms.cc handles zero detections: a new GoogleTest test fails first, then `ctest --test-dir build --output-on-failure` exits 0 with no other test changed. Print the ctest summary. Do not commit. Or stop after 20 turns.
```

Watch a branch; `touch .cv-kit-stop` halts it:

```
/loop 15m first run `test -f .cv-kit-stop` and stop if it exists; otherwise /cv-kit:review the diff against main, report only new Critical or Major findings, change nothing
```

- Without "commit" or "push" in the condition, an unattended run never commits or pushes. With it, `/cv-kit:commit`
  still shows its preview, and the `permissions.ask` rules that `/cv-kit:setup` offers for `git commit`, `git push` and
  `gh pr create` still prompt you.
- After two failed fixes the run stops and reports the evidence.
- `/cv-kit:develop write the /goal line for the NMS crash` drafts a line without touching code. More templates:
  `skills/develop/references/goal-loop-templates.md`. Headless: `claude -p "/goal ..." --output-format stream-json
  --verbose > /tmp/run.log`, with permissions set in advance.
- cv-kit does not train models, ship a benchmark harness or measure hardware: you run those, and it writes and checks
  the code and reports around them.

## Configuration

- **Rules and lint.** `/cv-kit:setup` copies `rules/*.md` into `.claude/rules/` and the ruff, mypy, clang-format,
  clang-tidy and CMake files into the project (Go needs no lint config). It never overwrites a file, never edits
  `CLAUDE.md`, and merges commit-guard permissions into `.claude/settings.json` only after your yes. Refresh from a clone
  with `python3 scripts/install_rules.py <project> --force`. Lint configs are tested with ruff 0.17.2, mypy 2.4.0,
  clang-format and clang-tidy 23.1.3, CMake 4.4, GCC 13.3.
- **Models.** Agents use the aliases `haiku`, `sonnet` and `opus`; pin a version with a full model ID in an agent's
  `model` field.
- **Hooks.** In `hooks/hooks.json`. Remove the two `concise.py` entries to switch off the concise rules and the
  Progress, Summarization and Next blocks. The evidence gate's ledger is in `~/.cache/cv-kit/gate/` (`CV_KIT_GATE_DIR`
  moves it). Details: `hooks/README.md`.
- **Live rows.** The plugin's `settings.json` sets `subagentStatusLine`; one in your own settings wins.

## Limitations

- **The evidence gate is a nudge.** It cannot tell that the right tests ran.
- **The commit hook has known gaps** (for example `git commit --amend --no-edit`, commits inside `bash -c`). See
  `hooks/README.md`.
- **Live rows need a SessionStart hook.** `${CLAUDE_PLUGIN_ROOT}` is empty in a plugin's `subagentStatusLine` (checked
  on Claude Code 2.1.317), so a SessionStart hook writes the plugin path to `~/.cache/cv-kit/plugin-root` for the status
  line to read. Without it the default rows show. The rows are off in an untrusted folder and under `disableAllHooks`.
- **Progress, Summarization and Next are model-written.** They follow rules, not code; a model can skip one.
- **Models and licences change.** Catalogue rows marked `UNVERIFIED` are unchecked; re-check licences at release.
- **No benchmark harness, training loop or dataset tools.** Measured numbers come from your runs.
- **Costs.** `lead` and `reviewer` run on Opus; `develop` sends routine reviews to Sonnet. The eval suite calls the API
  and is run by hand.

## Reference and development

- **References:** `shared/catalog.md` (models), `shared/metrics.md` (metrics, latency protocol), `shared/licenses.md`,
  `shared/sources.md`, the style catalogues `shared/python-style.md`, `shared/cpp-style.md`, `shared/go-style.md`,
  `hooks/README.md`, `evals/README.md`. Design notes with their sources and licences: `docs/research/`.
- **Develop:**

  ```
  python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
  .venv/bin/python scripts/validate_plugin.py
  .venv/bin/python -m pytest tests -q
  claude plugin validate . --strict
  ```

  CI (`.github/workflows/validate.yml`) runs the same checks and renders the figure templates. Before a pull request,
  run the four commands, write a failing test before a plugin change (`rules/principles.md`), keep skill descriptions
  under the validator's 8000-character total starting with "Use when", and run `scripts/run_evals.sh` before a release.

## Licence

MIT. See `LICENSE`.

Catalogued models have their own licences; check them before use. The style catalogues paraphrase the Google Python
and C++ Style Guides (CC BY 3.0), take ideas from the C++ Core Guidelines, and pitfalls from methylDragon's coding notes
(BSD-2-Clause). The Go catalogue draws on the Go documentation (BSD-3-Clause; CC BY 4.0 for the site pages) and the
uber-go guide (Apache-2.0), and uses goleak (MIT) as a test-only check. The figure skill bundles rough.js 4.6.6 (MIT)
and the Patrick Hand font (SIL OFL 1.1). The research report format is adapted from FOCUS (skill-focus, MIT).
