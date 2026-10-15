# cv-kit design

Date: 2026-10-14. Status: draft for review. Repo: `lthphuw/cv-kit` (MIT, private).

## 1. Purpose

`cv-kit` is a Claude Code plugin that gives a computer-vision engineer a tested set of skills, agents, hooks and rules:
choosing a model, preparing data, finetuning, evaluating, exporting, and researching how to customize a model, with
commit rules for git and SVN. Success means:

1. `/plugin marketplace add lthphuw/cv-kit` then `/plugin install cv-kit@cv-kit` works on a clean machine.
2. `claude plugin validate --strict` passes on the manifest, `skills/` and `agents/`.
3. Every model id, licence and number in the shipped catalog is verified against a live source or labelled `UNVERIFIED`.
4. A `git commit` or `svn commit` carrying a trailer is blocked by a hook, not only discouraged by prose.

Non-goals: no training framework, no model weights, no multi-harness manifests (Claude Code only), no duplicate of
superpowers' generic workflow skills.

## 2. Constraints that shape the design

Verified against the official docs on 2026-10-14 (see `docs/research/03-packaging.md`):

- A plugin cannot ship `.claude/rules` or `CLAUDE.md`; a root `CLAUDE.md` is ignored and `validate` warns about it.
  Rules therefore reach the user through a copy step (`install-rules`) and through hooks.
- Plugin agents ignore `permissionMode`, `hooks` and `mcpServers`. Read-only behaviour is enforced by a `tools` allowlist.
- Skill `description` plus `when_to_use` is capped at 1,536 characters; we keep `description` under 1,024 and start it
  with "Use when". It states the trigger, never a summary of the workflow.
- Skills are namespaced `/cv-kit:<skill>`; `SKILL.md` bodies stay under 500 lines, with critical instructions first
  (after compaction only the first 5,000 tokens survive).
- The version lives only in `plugin.json`.
- `claude plugin validate` on the repo root checks only `marketplace.json`, so CI validates each component path itself.

Papers with Code was shut down and now redirects to Hugging Face trending papers. `paperswithcode.co` is a third-party
site with benchmark pages (for example `/task/object-detection`, `/benchmark/coco-val2017`) but no stated operator, no API
and no provenance. It is a discovery source only (section 5).

## 3. Architecture

```
.claude-plugin/plugin.json, marketplace.json
skills/<name>/SKILL.md            + references/ and scripts/ where the skill needs them
agents/model-scout.md, cv-reviewer.md
hooks/hooks.json, block_trailers.py       PreToolUse on Bash
rules/*.md                                source files copied by install-rules; never auto-loaded
shared/                                   catalog.md, licenses.md, metrics.md, sources.md (data-formats.md arrives in v0.2)
scripts/validate_plugin.py, lint_research.py
docs/research/, docs/superpowers/specs/
.github/workflows/validate.yml
README.md
```

Skills read `shared/` through `${CLAUDE_SKILL_DIR}/../../shared/`. Marketplace installs copy the plugin directory, so
nothing may reference files outside it.

## 4. Skills

Names carry the `cv-` prefix where the bare name would be ambiguous; they are not prefixed with `cv-kit-`.

| Skill | Release | Triggers when |
|---|---|---|
| `cv-brainstorm` | v0.1 | a CV task is new or underspecified. Asks one question at a time about task, data, latency, licence, hardware, then splits the work into independent work packages for subagents |
| `cv-deep-research` | v0.1 | the user must pick or customize a model, backbone, head or loss and needs sourced evidence (section 5) |
| `cv-model-selection` | v0.1 | choosing a detector, segmenter, encoder or VLM for a stated task, budget and licence |
| `cv-embeddings-retrieval` | v0.1 | using CLIP, SigLIP/SigLIP2, DINOv2/v3 or similar for embeddings, zero-shot, retrieval or linear probes |
| `commit-vcs` | v0.1 | committing in git or SVN (section 6) |
| `install-rules` | v0.1 | user-invoked only (`disable-model-invocation: true`); copies `rules/*.md` into the project's `.claude/rules/` |
| `cv-dataset-prep`, `cv-auto-label`, `cv-finetune-detector`, `cv-evaluate`, `cv-export-deploy`, `cv-vlm-usage`, `cv-video-tracking`, `cv-depth-3d-pose-ocr` | v0.2 | one per engineer workflow, not per model |

v0.2 is deferred because its engineering gotchas have not been verified in this research pass, and the project's rule is
not to ship unverified content. The reference skill `senior-computer-vision` (davila7/claude-code-templates) turned out to
be template boilerplate with no CV content, so only its layout is reused: `SKILL.md`, `references/`, `scripts/`.

`install-rules` copies without overwriting existing files unless the user confirms, and never edits `CLAUDE.md`.

## 5. Deep research (`cv-deep-research`)

Adapted from Weizhena/Deep-Research-skills, whose weaknesses for ML work are: no per-claim provenance, a validator that
checks field names rather than values, one entity-card schema that compares benchmark numbers across mismatched dataset,
resolution and hardware, no source ranking, and web search as the only channel.

Phases: Frame, Scout, Shortlist, Deep-read, Cross-check, Synthesise, Hand-off.

- **Frame:** task, metric, dataset and split, latency and hardware budget, licence constraint, what is being customized.
- **Scout:** sweep the sources below for candidates. Aggregator sites only nominate candidates.
- **Shortlist:** the user approves the candidate list before the expensive phase.
- **Deep-read:** one `model-scout` subagent per candidate, in parallel, each writing a structured file.
- **Cross-check:** a separate verifier subagent re-opens every cited locator.
- **Synthesise:** comparison table normalised by dataset, split, resolution and hardware; recommended design; risks;
  ablation plan. Items not found are listed rather than dropped.
- **Hand-off:** writes to the project's R&D notebook if the `rnd-notebook` skill is installed; otherwise a markdown file.

Source tiers: T1 camera-ready proceedings (CVF Open Access, ECVA, accepted OpenReview); T2 arXiv paper (latest version)
with an official repository (RF100-VL paper and repository); T3 Hugging Face model cards and benchmark spaces; T4
aggregators, discovery only (`paperswithcode.co`, HF trending papers, alphaXiv, Semantic Scholar, GitHub code search, the
MTEB/MIEB and Open VLM boards, COCO/LVIS/ADE20K/ImageNet sites); T5 blogs and social posts, never cited for numbers. The
tier column in `shared/sources.md` is cv-kit's own assignment from these definitions, not a rating taken from the research.

Access, as probed on 2026-10-14: arXiv API, HF Papers JSON, CVF and ECVA work without a key; Semantic Scholar needs a key
(HTTP 429 otherwise); OpenReview blocks plain curl, use `openreview-py` or a browser; GitHub code search works through
`gh` at 10 requests per minute; COCO leaderboards are stale (2015 to 2017).

Anti-hallucination protocol: every number carries value, metric, dataset and split, resolution, hardware, arXiv id with
version, table or section locator, and a verbatim quote, plus a label `reported`, `reproduced` or `unverified`.
`scripts/lint_research.py` rejects a report with a missing field, a malformed arXiv id, or a number absent from its quote.

## 6. Version-control rules

Generic rules distilled from the user's rf-detr `git.md` and `pr.md`; repo-specific parts (upstream/develop merge
flow, `.temp/` drafts, named maintainers) are left out.

- A commit message is a subject line plus an optional body that states the change and its reason. Git: imperative subject,
  50/72 wrapping. SVN: `svn commit -F <file>` with the same shape.
- No trailers of any kind: `Co-Authored-By`, `Signed-off-by`, `Generated-by`, "Generated with …", `--signoff`, `--trailer`.
- A message never says who or what reviewed the change, how many review rounds ran, or which findings were fixed.
- Show a preview (branch, staged files, full message) and wait for approval before committing; approval does not carry to
  the next commit. Never use `--no-verify`.

Enforcement: `hooks/block_trailers.py`, a PreToolUse hook on the Bash tool, denies `git commit` and `svn commit` whose
message (from `-m`, `-F`, or a heredoc) contains a trailer line or a `--signoff`/`--trailer` flag, and returns the reason
so the agent rewrites the message. The banned lines include SVN's crediting lines (`Patch by:`, `Review by:`, `Found by:`).
A PreToolUse hook fails open on any exit code other than 0 or 2, so it is a guard, not a guarantee.

A plugin cannot set Claude Code's `attribution` setting (only `agent` and `subagentStatusLine` take effect), so the README
tells users to set `"attribution": false` (Claude Code 2.1.281 or later; older versions take
`{"commit": "", "pr": "", "sessionUrl": false}`). `attribution.sessionUrl` is a separate switch that adds a `Claude-Session`
trailer in cloud and Remote Control sessions. `includeCoAuthoredBy` is deprecated. Managed settings override the user's own
rules; if a managed policy forces a line and the hook blocks the commit, the agent tells the user instead of looping.
Server-side backstops (a git `commit-msg` hook, an SVN `pre-commit` hook) are drafted in `docs/research/04-vcs-rules.md`
and are not shipped in v0.1.

## 7. Installed rules (`install-rules`)

`commit-vcs.md` (section 6), `licence-callout.md` (state the licence of any model recommended, and warn on AGPL, GPL,
CC-BY-NC and gated Meta licences), `verified-ids.md` (never write a model id, arXiv id or licence that was not checked;
mark `UNVERIFIED`), `pinned-revisions.md` (pin HF revisions and package versions in generated code).

## 8. Agents

- `model-scout`: tools Read, Grep, WebFetch, WebSearch, Bash and Write; researches one candidate and writes the
  structured evidence file. One instance per candidate. Write is limited to the given output path and Bash to
  read-only `gh` and `curl` calls by instruction, not by the tool list, so it is not a hard sandbox.
- `cv-reviewer`: read-only reviewer of CV code and configs for leakage between splits, wrong normalisation, licence
  violations and unpinned weights.

## 9. Catalog and known open items

`shared/catalog.md` covers detectors, segmentation, encoders (CLIP, OpenCLIP, SigLIP/SigLIP2, DINOv2/v3), VLMs, depth,
tracking and OCR, with task, paper, repository or HF id, licence and typical use. Each id was matched to its arXiv title
or HF card during research; anything not fetched is `UNVERIFIED`.

Licence traps recorded: DEIMv2 is non-commercial; Depth Anything V2 Small is Apache-2.0 but Base and Large are
CC-BY-NC; YOLO11, YOLOv10, YOLOv12 and YOLO26 are AGPL; YOLO-World is GPL.

Open items, left as `UNVERIFIED` in the catalog until someone resolves them:

1. rf-detr's AGENTS.md calls XLarge/2XLarge PML 1.0, while the HF tag on `Roboflow/rf-detr-seg-xxlarge` says Apache-2.0.
2. Commercial terms of DINOv3 and SAM 3 (gated, custom Meta licences) are not fully parsed.
3. EasyOCR, docTR, Surya, the Qwen3.5 to 3.8 papers and the existence of SigLIP 3 were not checked.

## 10. Validation and testing

`scripts/validate_plugin.py` checks: valid frontmatter, `name` equals directory name, names unique, `description` under 1,024
characters and starting with "Use when", `SKILL.md` under 500 lines, every `${CLAUDE_SKILL_DIR}` path resolves, no
`CLAUDE.md` at the plugin root, version only in `plugin.json`. CI runs it, then `claude plugin validate --strict` separately
on `.claude-plugin/plugin.json`, `skills/` and `agents/`. The hook has its own test cases: a clean message passes; each
trailer form fails, for both git and svn. `claude plugin eval` is deferred: not in v0.1.
