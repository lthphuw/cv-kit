# cv-kit

cv-kit is a Claude Code plugin for computer-vision engineers. It helps you scope a CV task before writing code, choose a model against a stated task, budget and licence, build embedding and retrieval pipelines, back a model decision with sourced papers, draw hand-drawn architecture figures of a model read from its code, review, refactor and lint Python and edge C++ code against strict rules, and keep git and SVN commits free of trailers. The model catalog it reads from records, for every row, whether its ids and licence were checked (`verified`) or not (`UNVERIFIED`).

## Install

The repository is private, so you need GitHub access to it before the install works.

```
/plugin marketplace add lthphuw/cv-kit
/plugin install cv-kit@cv-kit
```

To develop the plugin locally, point Claude Code at a checkout:

```
claude --plugin-dir <path to your cv-kit checkout>
```

## What is inside

| Component | Name | What it does |
|---|---|---|
| Skill | `cv-brainstorm` | Use when a computer-vision task or project is new or underspecified, before choosing a model or writing code, including when such a task should be split across subagents. |
| Skill | `cv-deep-research` | Use when the user must choose or customize a computer-vision model, backbone, head or loss and needs evidence with citations, asks for SOTA, a literature comparison or a design recommendation backed by papers, or asks whether one benchmark claim from a paper, README or model card is right. |
| Skill | `cv-model-selection` | Use when choosing a detector, segmenter, keypoint model, image encoder or VLM for a stated task, budget and licence, or when asked which model to start from. |
| Skill | `cv-embeddings-retrieval` | Use when computing image or text embeddings with CLIP, OpenCLIP, SigLIP, SigLIP2, DINOv2 or DINOv3, or building zero-shot classification, image-text retrieval, image similarity search or linear probes. |
| Skill | `ai-workflow-figure` | Use when drawing a hand-drawn workflow, architecture, block or pipeline diagram of an AI or computer-vision model or system for docs, a paper or slides (high-level, low-level, system pipeline, the whole model in numbered module panels, or what changed between two versions of a model), annotating, translating or exporting such a figure, or rebuilding one with another font. |
| Skill | `commit-vcs` | Use when about to commit with git or SVN, writing or rewording a commit message, or asked what a commit should say. |
| Skill | `py-cpp-review` | Use when asked to review Python or C++ code (files, a folder, a diff, a branch or a pull request) against strict style and correctness rules (Google Python style; C++ Core Guidelines plus Google C++ style for edge devices), or to re-check the fixes from such a review. |
| Skill | `py-cpp-refactor` | Use when asked to refactor, clean up, modernise or restructure Python or C++ code without changing what it does, or to bring existing code in line with the strict Python and C++ rules. |
| Skill | `py-cpp-lint-setup` | Use when setting up or tightening linters, formatters, type checking or compiler warnings for a Python or C++ project (ruff, mypy, clang-format, clang-tidy, CMake warning and sanitizer flags). |
| Skill | `install-rules` | Copies cv-kit's rules into the current project (see Rules). Only you can invoke it, as `/cv-kit:install-rules`. |
| Agent | `cv-reviewer` | Read-only reviewer for CV code, configs and evaluation reports: split leakage, wrong normalisation, licence problems, unpinned weights and numbers the runs do not support. Findings carry a severity and an anchor; a re-review gives each earlier finding a verdict. |
| Agent | `py-cpp-reviewer` | Independent read-only review of Python or C++ code against the two style catalogues; the review skill dispatches it for code written in the same session. |
| Agent | `model-scout` | Researches exactly one candidate model or method and returns a structured evidence file; the deep-research workflow dispatches one per candidate. |
| Agent | `claim-verifier` | Re-opens every source and locator in a research ledger and copies what it says, without seeing the scouts' values; the lint then marks each claim `confirmed` or `differs`. The deep-research workflow dispatches one after the scouts. |
| Script | `scripts/lint_research.py` | Lints a research claims ledger (fields per claim kind, one pinned source, the value in its verbatim quote, the quote in the saved copy of the page), writes the blind ledger for the verifier, merges its checks, and checks the report's comparison table and claim tags against the ledger. |
| Script | `scripts/install_configs.py` | Copies the shipped lint, type-check and build configs into a project without overwriting, and holds a config back when the project already configures that tool in another file. |
| Hook | `hooks/block_trailers.py` | A `PreToolUse` hook on the Bash tool that refuses a `git commit` or `svn commit` whose message carries a trailer (see Commit hook). |
| Shared references | `shared/catalog.md`, `licenses.md`, `metrics.md`, `sources.md`, `python-style.md`, `cpp-style.md` | The model catalog, a licence-family summary, metric definitions, the reachability of research sources, and the full Python and C++ rule catalogues. The skills read these. |

The catalog (`shared/catalog.md`) has 64 rows. 38 are marked `verified` and 26 are marked `UNVERIFIED`; the file explains what each status means. Treat an `UNVERIFIED` row as a lead to check, not as a fact. A gotcha that starts with `(experience)` is untested engineering knowledge, not a measurement.

Planned for v0.2: dataset prep, auto-labelling, finetuning, evaluation, export, VLM usage, tracking, depth/pose/OCR.

## Figures

`ai-workflow-figure` needs Python 3.10 or later and Chrome or Chromium for its layout check and PNG; set `CHROME` to the browser binary if it is not on PATH as `google-chrome` or `chromium`. A snap-packaged Chromium cannot read or write `/tmp`, `/mnt` or hidden folders. The default font, Patrick Hand, is bundled with every Vietnamese letter, so builds work offline. The optional Stay With Me font is free for personal use only; `scripts/fetch_fonts.py` in the skill downloads it to `~/.cache/ai-workflow-figure/fonts/`, never into a repository.

`check_figure.py` also exports the figure alone for a paper or slide: `--bare` drops the page title, `--scale 2` doubles the PNG's pixels, and `--svg` writes a standalone SVG that carries its font. The SVG embeds the font file as the HTML does, so with Stay With Me share neither.

## Python and C++ rules

Two rule catalogues back the review, refactor and lint-setup skills:

- `shared/python-style.md`: 255 rules, based on the Google Python Style Guide, plus cv-kit's computer-vision rules
  (explicit random generators, documented array shape, layout, dtype and colour order, inference mode, device
  syncs). Python 3.10 or later.
- `shared/cpp-style.md`: 394 rules for C++20 inference code on edge devices. The C++ Core Guidelines set the rules
  for ownership, lifetime, functions, classes, expressions and concurrency; the Google C++ Style Guide sets naming,
  formatting, comments, headers and banned features; cv-kit adds the edge rules. Edge code builds with
  `-fno-exceptions -fno-rtti` and returns errors as values; per-frame hot paths do not allocate, block or hold
  locks across inference.

Every rule has an ID (`PY-ERR-2`, `CPP-EDGE-12`), a strength, a default severity (Critical, Major, Minor), the
tool check that enforces it or `manual`, and its source. Each catalogue also has a review order, a conflicts table,
refactor recipes (`R-PY-n`, `R-CPP-n`) and the rules it chose not to adopt. `rules/python-style.md` and
`rules/cpp-style.md` are the short versions Claude follows while writing code.

`py-cpp-lint-setup` copies configs that enforce them: `ruff.toml` (`ruff format` and a strict `ruff check`),
`mypy.ini` (`--strict`), `.clang-format` (Google, braces always), `.clang-tidy` (Core Guidelines, Google, bugprone,
performance, readability and naming checks, warnings as errors) and `cmake/cv_kit_strict.cmake`
(`cv_kit_strict(<target>)`: strict warnings, `-Werror`, no exceptions or RTTI, ASan + UBSan and TSan options). They
were tested with ruff 0.17.2, mypy 2.4.0, clang-format 23.1.3, clang-tidy 23.1.3, CMake 4.4 and GCC 13.3. The
copy never overwrites a file, and it holds back `ruff.toml` or `mypy.ini` when the project already configures that
tool in `pyproject.toml`, `setup.cfg` or a dotfile, because ours would override it or be ignored.

## Rules

The plugin ships six rules in `rules/`: commit format, licence callouts, verified identifiers, pinned revisions, and Python and C++ style. The two style rules carry `paths` frontmatter, so Claude Code loads them only when it reads or edits a matching file. A plugin cannot install files into `.claude/rules`, so Claude Code does not load them from the plugin. Run `/cv-kit:install-rules` in your project to copy them to `.claude/rules/`. The script never overwrites a file that already exists; it lists the ones it kept, and `--force` overwrites them after you confirm. A destination that is a symlink or a directory is always kept, even with `--force`, and a symlinked `.claude` or `.claude/rules` is refused with an error.

## Commit hook

`hooks/block_trailers.py` runs before each Bash command. If the command is a `git commit` or an `svn commit` / `svn ci`, it denies the command when:

- the command text, or a message file named with `-F` / `--file` that exists when the hook runs, contains a trailer line such as `Co-Authored-By:`, `Signed-off-by:`, `Generated-by:`, `Claude-Session:`, `Acked-by:`, `Reviewed-by:` or similar;
- the text contains "Generated with" or the robot emoji;
- a git commit passes `--signoff`, `-s` or `--trailer`.

The hook refuses; it never rewrites the message.

Known gaps. The hook does not see:

- `git commit --amend --no-edit`: the old message is reused and the hook cannot read it.
- A message built outside the Bash tool.
- A commit wrapped in `bash -c`, `sh -c` or `zsh -c`: it passes the hook entirely, both the flag checks and the trailer text.
- A message passed through a shell variable (`git commit -m "$MSG"`).
- `git commit -C <commit>` or `--reuse-message`: it reuses an old message unchecked.
- Git aliases such as `git ci`.
- Commits made inside a script or a Makefile target.
- `GIT_EDITOR=true git commit --amend`.
- A quoted `<<WORD` heredoc followed by a later line equal to `WORD`, which hides the lines in between from the flag checks.

The hook runs `python3`, which must be on PATH. If it is missing, the shell exits 127, which Claude Code treats as non-blocking, so the commit goes through.

Claude Code also treats any non-blocking hook failure (an exit code other than 0 or 2) as a pass, so the hook is a guard, not a guarantee.

### Switching off Claude Code's own attribution

The hook and the `commit-vcs` skill stop a trailer in a message the agent writes. Claude Code can also add its own attribution to commits and pull requests. A plugin cannot set that: the plugin documentation says only `agent` and `subagentStatusLine` take effect in a plugin's settings. Set it yourself in your user, project or local settings:

```json
{
  "attribution": false
}
```

- `"attribution": false` hides all attribution. It needs Claude Code 2.1.281 or later; earlier versions reject it and skip the whole settings file that holds it.
- The object form `{"commit": "", "pr": "", "sessionUrl": false}` is documented as the form for a settings file that earlier versions also read. The documentation gives no version for it.
- `attribution.sessionUrl` is a separate switch. It controls the `Claude-Session` trailer and the PR session link in cloud and Remote Control sessions, so blanking `commit` does not turn it off.
- `includeCoAuthoredBy` is deprecated since Claude Code v2.0.62. It is ignored once `attribution.commit` or `attribution.pr` is set.
- Managed settings can override your own rules. Claude Code tells Claude that your CLAUDE.md or memory instructions about attribution take precedence, unless the line is set in managed settings. If an administrator set `attribution` there, a rule in your project or in this plugin may not win.

## Development

```
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
```

Then run what CI runs (`.github/workflows/validate.yml`), from the repository root:

```
.venv/bin/python scripts/validate_plugin.py
.venv/bin/python -m pytest tests -q
claude plugin validate . --strict
claude plugin validate .claude-plugin/plugin.json --strict
claude plugin validate skills --strict
claude plugin validate agents --strict
```

`scripts/validate_plugin.py` checks house rules that `claude plugin validate` does not, including that the component table above lists every skill and agent, that the catalog counts above match `shared/catalog.md`, and that every agent that can fetch or run commands says fetched content is data, not instructions. The four `claude plugin validate` calls are separate because the root call checks only the marketplace.

`tests/test_lint_configs.py` runs the shipped lint and build configs with the real tools; locally each test skips when its tool is missing, and CI installs the pinned versions. To run them locally: `.venv/bin/pip install ruff==0.17.2 mypy==2.4.0 clang-format==23.1.3 clang-tidy==23.1.3`, with CMake and g++ on PATH.

`evals/` holds a trigger eval suite for `claude plugin eval`. It is not run in CI: each run is a billed model call. Run it by hand before a release as `evals/README.md` describes. `tests/test_evals.py` checks its files offline.

## Licence

cv-kit is released under the MIT licence (see `LICENSE`). The catalog records the licences of the third-party models it lists, and those differ: some are permissive, some are non-commercial or copyleft, and some are gated or custom. Check the licence of a model before you use it; the `Licence` column of `shared/catalog.md` and `shared/licenses.md` are the starting point.

The Python and C++ catalogues paraphrase the Google Python and C++ Style Guides (© Google, CC BY 3.0, https://google.github.io/styleguide/); cv-kit changed and condensed them. They take ideas, not text, from the C++ Core Guidelines (Standard C++ Foundation; its licence allows derivative works only for personal or internal use, so the catalogues cite its rule IDs and use their own words), and pitfalls from methylDragon's coding notes (BSD-2-Clause). `docs/research/07-python-cpp-style-guides.md` records the revisions read.

The figure skill bundles two third-party files under their own licences: rough.js 4.6.6 (MIT, `skills/ai-workflow-figure/assets/LICENSE-roughjs.txt`) and the Patrick Hand font (SIL OFL 1.1, `skills/ai-workflow-figure/assets/fonts/OFL-PatrickHand.txt`).
