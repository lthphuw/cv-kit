# 11 - FOCUS-style short reports: what cv-kit took, and from where

Date: 2026-11-03. Input for the research skill's report format: `skills/research/references/report-template.md`,
`skills/research/SKILL.md` (steps 6 and 7), and the report checks in `scripts/lint_research.py`. Nothing was executed from
any downloaded file; the one file read is data.

## The request

The old `report.md` had nine sections and was too long to read; readers skipped it. The user approved a short report in a
format adapted from the FOCUS summarisation method, with the rest moved to `appendix.md`, and only the Overview printed
in chat.

## The resources

| # | Resource | Where it was read | Revision | Licence | What cv-kit took |
|---|---|---|---|---|---|
| S1 | https://github.com/stephenturner/skill-focus, `SKILL.md` | `curl` of https://raw.githubusercontent.com/stephenturner/skill-focus/main/SKILL.md, saved to `/tmp/focus-dl/SKILL.md` (outside the repository), read whole (5,942 bytes), 2026-11-03. A WebFetch summary was tried first and was not used, because it summarises. | commit `84e521dcf0a44786500cce60bac6ddf00c63b3e8` (2026-03-26) | **MIT**, Copyright (c) 2026 Stephen D. Turner (repository `LICENSE`, read through https://raw.githubusercontent.com/stephenturner/skill-focus/main/LICENSE; GitHub API reports `MIT`) | The format only, in our own words: an Overview of 3 to 6 sentences with no bullets; numbered key points `N. **Heading in sentence case**` with a body of concrete specifics; quotes support a point and do not repeat it; no meta-discourse; combine near-duplicates. No text copied. |
| S2 | https://github.com/stephenturner/skill-focus, `README.md` | `curl` of https://raw.githubusercontent.com/stephenturner/skill-focus/main/README.md, first 40 lines, 2026-11-03 | same | MIT (as S1) | Confirms the credit and the method's description. |
| S3 | GitHub API, `gh api repos/stephenturner/skill-focus` and `.../commits/main` | 2026-11-03 | same | n/a | Commit hash and date, licence identifier (`MIT`). |
| S4 | Lin, Nat. Biotechnol. 43, 2070-2075 (2025), https://doi.org/10.1038/s41587-025-02947-8 | **Not opened.** Its title and citation come from S1 and S2. | n/a | not checked | Credit only. cv-kit makes no claim about what the paper says beyond what S1 and S2 state. |

Credit in the shipped template: "Format adapted from the FOCUS method (Lin, Nat. Biotechnol. 2025)". The cv-kit licence is
MIT, the same as S1, so adapting the format is compatible, and no S1 wording was copied.

## What was changed, and why

| FOCUS | cv-kit report | Reason |
|---|---|---|
| Overview paragraph, 3 to 6 sentences, no bullets | `## Overview`, same, with the recommendation, the main risk and a confidence word | The reader needs the decision first. The lint rejects a missing Overview and any bullet in it. |
| Numbered key points with specifics | `## Key points`, at most 7, one or two sentences each, each with its `[claim-tag]` | Specifics are what a claim check can verify. The stress-test answers are one point here, not a section. |
| Section structure mirrors the source | Fixed sections: Overview, Key points, Comparison, Next steps | The source is our own evidence, not a document with its own structure. |
| Citation markers removed in step 2 | Claim tags kept | The tags are what the lint uses to tie each number to a checked claim. |
| Quotes embedded in italics | Not used in `report.md`; quotes stay in `claims.json` | A verbatim quote is the evidence for a claim, and it lives in the ledger. |
| Step 1 extraction, then step 2 cleanup, only step 2 shown | One pass; the ledger and scout files play the part of step 1 | The scouts already extracted every claim. |

## The deviation: brevity over exhaustiveness

FOCUS's first principle is "exhaustiveness over brevity": list all 30 insights if there are 30. cv-kit takes the opposite
for `report.md`, because the readers of a decision report do not read long reports. The caps are cv-kit's own and were not
tested against readers:

- at most 7 key points; at most 400 words outside the table; at most 3 next steps;
- the lint enforces the 7-item cap and a 400-word cap (counting every non-table line of `report.md`, headings included).

Exhaustiveness moved to `appendix.md`, not away: considered and excluded, recommended-design detail, caveats per
candidate, not found and not checked (`not_found`, `access_failed`, `absent`, `unreachable`; never dropped), the claims
ledger summary, and the sources and search log. The same claim-tag rules apply there: the lint checks `appendix.md` when
it sits next to the report.

## What was verified, and how

- **Lint behaviour.** `tests/test_lint_research.py` covers each new check: the table is found under `## Comparison`
  (case-insensitive) and still under the old `## 3.` heading; the Overview is required and bullet-free; Key points at most
  7; the 400-word cap, with table rows not counted; and the claim-tag check applied to `appendix.md`.
- **Old reports.** A report with `## 3.` and no `## Comparison` keeps the table and tag checks and skips the Overview,
  Key points and length checks.

## Not verified

- **The 400-word cap (raised from 350 at review: 7 key points, a 6-sentence Overview and 3 next steps did not fit) and the 7-point cap are not evidence-based.** They are a judgement about "about one screen". Tune
  them after reading a few real reports.
- **The 3-to-6-sentence Overview rule is not linted**; sentence counting is unreliable around numbers such as `54.7`.
  Only "no bullet lines" is checked.
- **No end-to-end run of the research skill with the new template** was made; evals 04 to 08 test only that the skill
  fires and that replies keep licences and avoid unsourced numbers, and none of their graders refers to the report format.
- **The Lin (2025) paper was not read** (S4).
