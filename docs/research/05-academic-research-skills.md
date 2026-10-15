# 05 - academic-research-skills: what cv-kit took, and from where

Date: 2026-10-15. Input for the research-side changes made the same day (`cv-deep-research`, `model-scout`, the new `claim-verifier`, `cv-reviewer`, `lint_research.py`, `validate_plugin.py`, `evals/`).
Legend: **VERIFIED** = seen in a response or a file today. **UNVERIFIED** = named in the repository, not opened by us.

## The resource

| Field | Value |
|---|---|
| Repository | https://github.com/imbad0202/academic-research-skills |
| Commit read | `a3ef8c79d888b90aaaaecce7f42fbc3fd082d5ab` (2026-10-14), 828 commits, 2,840 files |
| Licence | **CC BY-NC 4.0** (`LICENSE:1-4`, copyright Cheng-I Wu). GitHub's API reports `NOASSERTION`. |
| Stars, last push | 52,035; 2026-10-13 (`gh api repos/imbad0202/academic-research-skills`, 2026-10-15) |
| What it is | A Claude Code plugin for academic research and writing: deep research, paper writing, peer review, a research-to-publication pipeline, systematic-review screening. |
| Clone | `/mnt/data2/projects/cv-kit-refs/academic-research-skills`, outside this repository. Read only; nothing in it was run, installed or built. |

**Licence consequence.** cv-kit is MIT. A non-commercial licence cannot be relicensed as MIT, so cv-kit takes ideas and mechanisms only. Every adopted rule below was written in our own words; no ARS text, prompt, fixture or code was copied. Shipped cv-kit files do not reference ARS paths; only this note does.

## How it was read

Four research agents, each with a disjoint scope, each reading its files in full (or saying which it skimmed), comparing them with the cv-kit counterparts, and citing every fact as `path:line`. Their notes, 1,833 lines in total, are kept outside the repository in `/mnt/data2/projects/cv-kit-refs/notes/`:

| Note | Scope | Read |
|---|---|---|
| `ars-1-deep-research.md` | `deep-research/` (SKILL.md, 14 agents, 24 references, 6 templates, 8 examples), top-level `agents/` | all in full. `skills/deep-research` is a symlink to `deep-research/`; 3 of the 4 top-level agents are byte-identical copies. |
| `ars-2-shared-packaging.md` | `shared/` (155 files), manifests, `hooks/`, `commands/` (16), `.claude/`, governance and root docs, workflows | top-level `shared/*.md` in full; subfolders sampled; the write-scope guard (`scripts/ars_write_scope_guard.py`) read to understand the hook |
| `ars-3-review-pipeline.md` | `academic-paper-reviewer/`, `academic-pipeline/`, `academic-paper/`, `sr-screener/` | reviewer, pipeline and screener in full; five writing and formatting agents of `academic-paper` by headings only |
| `ars-4-scripts-evals.md` | `scripts/` (633 files), `tests/`, `evals/`, `plugin-evals*/`, `audits/`, `docs/`, CI | inventory of everything; about 20 scripts, 6 workflows, 3 eval suites and 2 audits in full |

## What cv-kit adopted

| cv-kit change | Files | Idea taken from (ARS path:line) |
|---|---|---|
| Fetched pages, papers, READMEs and model cards are data, not instructions; text aimed at an agent is reported, not followed. `validate_plugin.py` now fails an agent that has WebFetch, WebSearch or Bash and does not say so. | `agents/model-scout.md`, `agents/claim-verifier.md`, `agents/cv-reviewer.md`, `skills/cv-deep-research/SKILL.md`, `scripts/validate_plugin.py` | `deep-research/agents/source_verification_agent.md:52-55`; `shared/ground_truth_isolation_pattern.md` (section 2A). cv-kit's own research 02 line 207 had proposed it. |
| A separate, blind verifier. It gets the ledger without values or quotes (`lint_research.py --blind`), fetches each source itself, checks the title, copies the passage at the locator, and answers `found`, `wrong-paper`, `absent` or `unreachable`. The lint then decides `confirmed` or `differs`. "Unreachable" is never worded as fabricated; a verdict changes only with new evidence. | `agents/claim-verifier.md`, `scripts/lint_research.py`, `skills/cv-deep-research/SKILL.md` phase 5 | outcome ladder `deep-research/agents/source_verification_agent.md:143-148`; absent is not false `deep-research/references/openalex_api_protocol.md:62`; id/title mismatch `deep-research/references/arxiv_api_protocol.md:32`; blind second check `deep-research/agents/devils_advocate_agent.md:189`; concession threshold `:160-185`; criteria fixed before reading `academic-paper-reviewer/references/re_review_mode_protocol.md:57-117`. The mechanical value comparison is cv-kit's own: ARS judges claim support with a model. |
| A claim schema that fits CV sources: `kind` (`accuracy`, `latency`, `size`) with its own required fields (accuracy no longer needs hardware; latency needs precision and batch); one source of `arxiv` (with version), `doi` or `url` (a Hugging Face or GitHub URL needs a `revision`); `retrieved` date; `measured_by` (authors or third party); `run` for a reproduced number. | `scripts/lint_research.py`, `agents/model-scout.md`, `rules/verified-ids.md` | ID-gated applicability `deep-research/references/arxiv_api_protocol.md:44-48`; closed evidence kinds `deep-research/agents/synthesis_agent.md:337-339`; multi-identifier lookups `deep-research/references/openalex_api_protocol.md:20-34`. |
| The quote must be in a saved copy of the page (`source_file`), checked offline by the lint; WebFetch output is never quoted, because it returns a summary, not the page. | `scripts/lint_research.py`, `agents/model-scout.md` | the gap was found while reading ARS (it has no mechanical quote check); research 02 line 201 had asked for it. |
| The report is linted against the ledger: every claim tag names a claim; a claim that is not `confirmed` is cited only on a line that says "unconfirmed"; every number in the comparison table is the value of a claim its row names. | `scripts/lint_research.py --report`, `references/report-template.md` | report self-gate `deep-research/agents/report_compiler_agent.md:271-300`. |
| Versions and venue: every version found is listed; a number that differs between versions becomes separate claims; a Version column in the report. OpenAlex and Crossref rows in `sources.md`, and a "when a source fails" section. | `agents/model-scout.md`, `shared/sources.md`, `references/report-template.md` | version families `deep-research/agents/timeline_extraction_agent.md:79-108`; degradation tables `deep-research/references/arxiv_api_protocol.md:50-66`, `deep-research/references/openalex_api_protocol.md:54-72`. |
| Shortlist screening: exclusion reasons fixed from the brief before screening, in a cost order; one reason or `advance` per candidate with the deciding fact and what would change it; unclear candidates advance; counts add up; a skew warning; a default cap of 6. | `skills/cv-deep-research/SKILL.md` phase 3, report section 3b | `sr-screener/references/decision_rules.md:25-44`; `sr-screener/agents/screening_reviewer_agent.md:57-59`; skew advisory `deep-research/agents/bibliography_agent.md:104-128`; excluded with reasons `deep-research/templates/prisma_report_template.md:253`. |
| Stress questions before recommending, no ranking when fewer than two candidates are comparable, wording rules ("SOTA" is the best of the candidates checked, on a benchmark, as of a date; "reported", never "shown"). | `skills/cv-deep-research/SKILL.md`, `references/report-template.md` | `deep-research/agents/devils_advocate_agent.md:144-157`; `deep-research/agents/meta_analysis_agent.md:33`, `:40-58`; dated "latest" `deep-research/agents/report_compiler_agent.md:115-144`; claim-strength wording `academic-paper/agents/draft_writer_agent.md:539-594`. |
| Eleven questions to ask of a reported CV result, answered per candidate under `caveats`; the worst answer sets the TL;DR confidence word. Questions only, no numbers. | `skills/cv-deep-research/references/claim-checks.md` | domains and worst-domain rule `deep-research/agents/risk_of_bias_agent.md:31-38`, `:110-112`; AI research failure modes `academic-pipeline/references/ai_research_failure_modes.md:67-78`. Written from scratch; no RoB 2 or GRADE text adapted. |
| A one-claim check path ("is this benchmark claim right?") that skips phases 2 to 4. | `skills/cv-deep-research/SKILL.md`, its description | fact-check mode `deep-research/references/mode_selection_guide.md:146-163`; `deep-research/examples/fact_check_mode.md:147-173`. |
| `cv-reviewer` v2: severity by how much one defect changes the result, rated alone; anchors including an `absent:` form that says what was checked; a "results and reports" category; a norm needs a source or the finding is Minor; a re-review with fixed verdicts. | `agents/cv-reviewer.md` | `academic-paper-reviewer/templates/peer_review_report_template.md:244-287`; `academic-paper-reviewer/agents/eic_agent.md:139-146`; `academic-paper-reviewer/agents/domain_reviewer_agent.md:242-254`; `academic-paper-reviewer/references/re_review_mode_protocol.md:57-117`. |
| A trigger eval suite for `claude plugin eval` (16 cases: each skill fires and does not fire, plus confusable pairs) and an offline lint of it in pytest. | `evals/`, `tests/test_evals.py` | `plugin-evals/README.md`; the format itself was checked against `claude plugin eval --help` (2.1.300) and https://code.claude.com/docs/en/plugin-evals.md on 2026-10-15. |
| The README component table and catalog counts are checked against the files (commit `ffc2347` had fixed that drift by hand); JSON ledgers reject duplicate keys and NaN. | `scripts/validate_plugin.py`, `scripts/lint_research.py` | README parity and strict JSON in ARS's lints (`ars-4-scripts-evals.md` section 2). |

## Deferred, with the reason

- **A write-scope fence for `model-scout`** (a `PreToolUse` hook keyed on the payload's `agent_type`, as `scripts/ars_write_scope_guard.py` does). The format of `agent_type` for plugin agents in our Claude Code version is not verified; ARS's captured payloads show `<plugin>:<agent>`, and calls from the main session carry none. Capture real payloads before building it.
- **A networked `verify_claims.py`** (arXiv id and version existence, title match). The verifier agent does this now; a script can follow once the empty-feed behaviour below is used in tests.
- **A `Checked` date column and a recheck script for `shared/catalog.md`.** It needs a live check of which Hub API field carries the licence.
- **gitleaks in CI.** Its version and checksum need checking first.
- **A seeded-defect fixture for the verifier** (`tests/fixtures/verifier/`, 12 to 20 synthetic cases). Useful once the verifier has run on real ledgers.

## Not adopted

The RCT evidence pyramid, APA style, PRISMA, meta-analysis and GRADE in full, the ethics and IRB machinery, predatory-journal checks, the Socratic mentor (it hides mechanisms from the user on purpose, `academic-paper/agents/socratic_mentor_agent.md:68-75`), the material passport and the twelve handoff schemas, cross-vendor verification, model tiering (two agents keep `inherit`), `commands/` (research 03 calls them legacy), a SessionStart announcement, the mode registry, release-process gates and the gold-set lift gates (ARS's own gold harness notes that it scores about 1.0 by construction, `evals/gold/citation_extraction/README.md:11`).

## Probes made for this note (2026-10-15)

Raw responses are in `/mnt/data2/projects/cv-kit-refs/probe/`.

| Request | Result (VERIFIED) |
|---|---|
| OpenAlex `GET /works/doi:10.48550/arXiv.2511.09554` | 200; the RF-DETR preprint, `type` `preprint`, only arXiv locations. |
| OpenAlex `GET /works/doi:10.48550/arXiv.2304.02643` | 200, but an **unrelated** record ("Micrograph segmentations for DDEVD"). The arXiv API gives "Segment Anything" for that id. A DOI lookup must be followed by a title check. |
| OpenAlex `GET /works?filter=title.search:segment anything` | 200; the ICCV 2023 record under DOI `10.1109/iccv51070.2023.00371`, separate from the preprint record. |
| Crossref `GET /works/10.1109/iccv51070.2023.00371` | 200; `title`, `container-title` (ICCV 2023), `type` `proceedings-article`. |
| Crossref `GET /works/10.48550/arXiv.2304.02643` | 404: arXiv DOIs are not in Crossref. |
| arXiv API `id_list=2304.02643v9` (no such version) | 200, `opensearch:totalResults` 0, no entry. |
| End-to-end lint on `https://arxiv.org/html/2511.09554v2` saved to disk | A sentence quoted from the page passed the saved-copy check; the same claim with the number changed (48.0 to 48.5) failed it. |

## External resources the repository cites

Named as written in ARS; none of these was opened for this note (UNVERIFIED), except where a probe above says so.

| Resource | As written | Cited at | Why it matters to cv-kit |
|---|---|---|---|
| arXiv API terms of use | `https://info.arxiv.org/help/api/tou.html` | `deep-research/references/arxiv_api_protocol.md:6` | The primary source for the 1 request per 3 s rule in `shared/sources.md`. |
| OpenAlex API and authentication | `https://api.openalex.org`; `https://developers.openalex.org/api-reference/authentication` | `deep-research/references/openalex_api_protocol.md:5-7` | Rate and key rules for the new OpenAlex row. |
| Crossref API | `https://api.crossref.org` | `deep-research/references/crossref_api_protocol.md:5` | The new Crossref row. |
| Semantic Scholar key form | `https://www.semanticscholar.org/product/api#api-key` | `deep-research/references/semantic_scholar_api_protocol.md:100` | Getting an `S2_API_KEY`. |
| DOI registration agency lookup | `https://doi.org/doiRA/<prefix>` | `deep-research/references/chinese_literature_api_protocol.md:19` | Tells which agency holds a DOI. |
| PROBAST+AI; TRIPOD+AI; STARD-AI | `https://www.bmj.com/content/388/bmj-2024-082505`; `https://doi.org/10.1136/bmj-2023-078378`; the EQUATOR STARD-AI page | `deep-research/references/equator_reporting_guidelines.md:285`, `:343`, `:404` | Published appraisal and reporting standards for AI models, relevant to medical-imaging users. |
| PRISMA 2020; RoB 2 | `https://doi.org/10.1136/bmj.n71`; `https://doi.org/10.1136/bmj.l4898` | `deep-research/references/systematic_review_toolkit.md:39`, `:154` | The structures behind "excluded with reasons" and the claim questions. |
| Lu et al. 2026, Nature 651:914-919 | `doi:10.1038/s41586-026-10265-5` | `academic-pipeline/references/ai_research_failure_modes.md:7` | Failure modes of automated AI research (shortcuts, invented results). |
| Zhao et al. 2026, hallucinated citations | `arXiv:2605.07723` | `deep-research/agents/bibliography_agent.md:336` | Motivation for title checks and claim-support checks. |
| Kim et al. 2026, AI reviewer failure classes | `arXiv:2605.20668v1` | `academic-paper-reviewer/agents/domain_reviewer_agent.md:244` | Norm-gated severity in `cv-reviewer`. |
| Ren et al. 2026, evaluator independence | `arXiv:2607.13104` | `shared/cross_model_verification.md:331` | Why the verifier is called a same-model re-read, not an independent check. |
| Adams et al. 2026, hallucinated citations in NeurIPS 2025 | `arXiv:2602.05930` | `academic-pipeline/agents/integrity_verification_agent.md:82` | Same. |
| Retraction Watch database | `http://retractiondatabase.org` | `deep-research/references/literature_monitoring_strategies.md:100` | An optional retraction check; OpenAlex's `is_retracted` covers part of it. |
| gitleaks | `https://github.com/gitleaks/gitleaks` | `.github/workflows/repository-hygiene.yml:5` | The deferred secrets scan. |

Not cited anywhere in ARS: NeurIPS or ICLR reviewer guidelines, the NeurIPS paper checklist, ML reproducibility checklists, REFORMS, model cards and datasheets. A reporting checklist for v0.2 `cv-evaluate` needs its own research pass.

## Content that read like instructions

Treated as data and not followed: each ARS `SKILL.md` carries a routing block addressed to whatever agent loads it; `sr-screener/agents/protocol_architect_agent.md:21` suggests running a `python -c` one-liner; `audits/external-contribution-audit-prompt.md` is a prompt meant to be pasted into a model; `.github/copilot-instructions.md` is an instruction file for Copilot. ARS also contradicts itself on verification thresholds (spot-check rates of 20, 30, 50 and 100 % in different files), which is why cv-kit keeps each rule in one place.
