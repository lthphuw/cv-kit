# cv-kit

A Claude Code plugin for engineers who write Python and edge C++ and do computer-vision R&D.

---

## Install

```
/plugin marketplace add lthphuw/cv-kit
/plugin install cv-kit@cv-kit
```

Then, once per project:

```
/cv-kit:setup
```

Update:

```
/plugin marketplace update cv-kit
```

---

## Usage & Workflows

Choose the right scenario, skill, and automation mode (Interactive, Goal-driven, or Continuous Loop).

### 1. Test-Driven Development & Code Changes
* **Skill:** `/cv-kit:develop`
* **Use Case:** Writing new features, fixing bugs, refactoring, or optimizing performance with test-first guarantees.

* **Interactive Prompt:**
  ```
  /cv-kit:develop add clamp_boxes(boxes, width, height) to vision/utils.py
  ```
  *Claude reads project rules, writes a failing test, implements minimum passing code, and runs full test suites.*

* **Autonomous Goal (`/goal`):**
  ```
  /goal follow /cv-kit:develop. NMS handles zero detections: a new GoogleTest test
    fails first, then ctest --test-dir build --output-on-failure exits 0.
    Do not commit. Or stop after 20 turns.
  ```

* **Continuous Monitoring (`/loop`):**
  ```
  /loop 10m run pytest -q and ctest; if either fails, find the root cause
    with /cv-kit:develop and stop to report it
  ```

<details>
<summary>More development prompts</summary>

---

* **Fix crashes:**
  ```
  /cv-kit:develop NMS in src/post/nms.cc crashes on zero detections
  ```

* **Root cause analysis:**
  ```
  /cv-kit:develop loss goes NaN after epoch 3, only with AMP
  ```

* **Refactoring:**
  ```
  /cv-kit:develop refactor this loader, it must return the same arrays
  ```

* **Dependency migration:**
  ```
  /cv-kit:develop migrate dataset loader from PIL to cv2, outputs must not change
  ```

* **Benchmarking:**
  ```
  /cv-kit:develop make preprocessing faster; measure p50 and p99 before and after
  ```

* **Read-only exploration:**
  ```
  Where is the NMS threshold read from config, and which functions use it? Only look.
  ```

</details>

---

### 2. Evidence-Backed R&D & Model Benchmarking
* **Skill:** `/cv-kit:research`
* **Use Case:** Model selection, verifying paper claims, checking licenses, or reproducing results with cited sources.

* **Interactive Prompt:**
  ```
  /cv-kit:research which detector for 30 FPS on a Jetson Orin NX, Apache-2.0 only
  ```
  *Claude builds a research brief, presents a shortlist for approval, clones repos, verifies claims independently, and writes `research/<slug>/report.md`.*

* **Autonomous Goal (`/goal`):**
  ```
  /goal follow /cv-kit:research. Compare DINOv2 and SigLIP2 as frozen backbones for ADE20K,
    verify mIoU claims from paper tables, produce research/backbones/report.md
  ```

<details>
<summary>More research prompts</summary>

---

* **Paper comparisons:**
  ```
  /cv-kit:research compare DINOv2 and SigLIP2 as frozen backbones for ADE20K, numbers from papers' tables
  ```

* **Pipeline evaluation:**
  ```
  /cv-kit:research image search over 200k product photos with SigLIP2, what do I need and how do I evaluate it?
  ```

* **Fact-checking claims:**
  ```
  /cv-kit:research the DEIMv2 README claims a COCO AP I do not trust
  ```

* **Code vs. Paper check:**
  ```
  /cv-kit:research does the loss in the repo match the paper? clone it and read
  ```

* **License audit:**
  ```
  /cv-kit:research can we use this model in a commercial product? check the licence and the weights
  ```

* **Reproduction:**
  ```
  /cv-kit:research reproduce the AP in the README in a throwaway environment
  ```

</details>

---

### 3. Code Review & Quality Gates
* **Skill:** `/cv-kit:review`
* **Use Case:** Independent, read-only checks against style catalogues (Python/C++) and CV-specific rules.

* **Interactive Prompt:**
  ```
  /cv-kit:review the diff against main
  ```

* **CI / Non-Interactive CLI:**
  ```
  claude -p "/cv-kit:review the diff against origin/main"
  ```

* **Autonomous Goal (`/goal`):**
  ```
  /goal follow /cv-kit:review. Review the diff against main;
    end with Blocking: N Critical, M Major; change no file. Or stop after 10 turns.
  ```

<details>
<summary>More review prompts</summary>

---

* **File review with constraints:**
  ```
  /cv-kit:review src/camera/frame_grabber.cc, we build with -fno-exceptions
  ```

* **PR review:**
  ```
  /cv-kit:review PR 142
  ```

* **Data integrity check:**
  ```
  /cv-kit:review train/val split in data/split.py, any leakage?
  ```

* **Validate report metrics:**
  ```
  /cv-kit:review does the mAP in report.md follow from the runs in runs/?
  ```

* **Verify fixes:**
  ```
  /cv-kit:review check the fixes for the findings you gave me earlier
  ```

</details>

---

### 4. Architecture Diagrams & Visuals
* **Skill:** `/cv-kit:figure`
* **Use Case:** Generating hand-drawn pipeline/architecture diagrams from actual codebase structure.

* **Interactive Prompt:**
  ```
  /cv-kit:figure high-level figure of the detector for the docs page
  ```

<details>
<summary>More figure prompts</summary>

---

* **Low-level tensor shapes:**
  ```
  /cv-kit:figure low-level figure with tensor shapes for the neck and head
  ```

* **Numbered panels:**
  ```
  /cv-kit:figure the whole model in numbered module panels
  ```

* **Before/After diff:**
  ```
  /cv-kit:figure what changed between v1 and v2, before and after
  ```

* **Paper constraints:**
  ```
  /cv-kit:figure same figure for a two-column paper, 240 pt wide, labels in Vietnamese
  ```

</details>

---

### 5. Version Control & Clean Commits
* **Skill:** `/cv-kit:commit`
* **Use Case:** Creating rule-compliant commit messages (Git/SVN) with preview gates and trailer enforcement.

* **Interactive Prompt:**
  ```
  /cv-kit:commit
  ```

---

### 6. Orchestration & Project Setup
* **Project Setup:**
  ```
  /cv-kit:setup            # Full setup
  /cv-kit:setup python     # Python rules only
  /cv-kit:setup cpp        # C++ rules only
  ```

* **Master Orchestrator Agent (`lead`):**
  ```
  claude --agent cv-kit:lead
  ```
  *Routes complex, multi-step engineering tasks through a top-level delegation agent.*

---

## What is inside

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
| Agent | `lead` | Opus, high effort — optional orchestrator that only delegates |
| Hook | `block_trailers.py` | Refuses a commit message with a trailer |
| Hook | `evidence_gate.py` | Blocks a turn if code changed but no test passed |

Models use aliases and follow the newest version your provider offers. To pin one, set a full model ID in the agent's `model` field.

---

## Requirements

- **Claude Code** 2.1.295 or later. `python3` on PATH.
- **figure skill:** Python 3.10+ and Chrome or Chromium (set `CHROME` if not on PATH).
- **Lint configs tested with:** ruff 0.17.2, mypy 2.4.0, clang-format 23.1.3, clang-tidy 23.1.3, CMake 4.4, GCC 13.3.

---

## Development

```
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python scripts/validate_plugin.py
.venv/bin/python -m pytest tests -q
claude plugin validate . --strict
```

CI (`.github/workflows/validate.yml`) validates `plugin.json`, `skills`, and `agents`. The `evals/` directory is a trigger-and-routing eval suite, run by hand before a release.

---

## Licence

MIT. See `LICENSE`.

The models in the catalogue have their own licences — check them before use. The style catalogues paraphrase the Google Python and C++ Style Guides (CC BY 3.0), take ideas from the C++ Core Guidelines, and pitfalls from methylDragon's coding notes (BSD-2-Clause). The figure skill bundles rough.js 4.6.6 (MIT) and the Patrick Hand font (SIL OFL 1.1).