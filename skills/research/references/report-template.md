Write two files in the research folder: `report.md` (short, what the reader reads) and `appendix.md` (everything else).
Format adapted from the FOCUS method (Lin, Nat. Biotechnol. 2025); the length caps are cv-kit's own.

Cite a claim as `[<candidate-slug>-<n>]`, its id in `claims.json`. A claim whose verdict is not `confirmed` is cited only on a line that also says "unconfirmed". The lint checks both, in `report.md` and in `appendix.md`.

## report.md

```
# <Decision>: <one-line question>
<date>, brief <hash>, cv-kit <version>.

## Overview
3 to 6 sentences, no bullets: the recommendation, the main risk, a confidence word.

## Key points
1. **Heading in sentence case**
1 or 2 sentences with the specific numbers and their [claim-tag].

## Comparison

| Candidate | Value | Metric | Dataset and split | Resolution | Hardware | Version | Licence | Claim |
|---|---|---|---|---|---|---|---|---|

## Next steps
1. Validation experiment: metric and data.

Details, exclusions and sources: [appendix.md](appendix.md).
```

Rules:
- Body outside the table: one screen, at most 400 words. No preamble, no closing remarks, no "this report".
- **Overview.** The confidence word is `high`, `medium` or `low`, as `claim-checks.md` defines it.
- **Key points.** At most 7, numbered `N. **Heading**`. Concrete numbers, not adjectives; a quote supports a point and is not repeated beside it; combine near-duplicates. The stress-test answers go here as one point: does the pick still win without its strongest claim, and which single claim, if wrong, would flip it.
- **Comparison.** `Value` is the claim's value as the source states it; `Claim` holds its tag. Numbers appear only if the dataset, split, resolution and hardware match across rows; otherwise write `not comparable` in `Value`. When two sources give different numbers for one setting (arXiv v1 against v2, a paper against a README), give each its own row.
- **Next steps.** At most 3 experiments that would confirm or kill the recommendation, each with its metric and data.
- With fewer than two comparable candidates, say so in the Overview, do not rank, and let Next steps carry the plan.

## appendix.md

Headings, in this order; omit a heading with nothing under it, except the fourth.

1. **Context and constraints.** Copied from the brief: task, metric, dataset and split, hardware and latency budget, licence constraint.
2. **Considered and excluded.** Each candidate dropped at the shortlist, with its reason (licence, task, no weights, no traceable numbers, stack) and the deciding fact.
3. **Recommended design.** Only if it does not fit in a Key point: what to build or change, and why it beats the alternatives under the constraints.
4. **Not found or not checked.** Every item the scouts could not locate (`not_found`), every source they could not reach (`access_failed`), and every claim whose verdict is `absent` or `unreachable`. Never dropped, even when empty ("none").
5. **Caveats.** The `caveats` that are concerns, per candidate, with their locators.
6. **Claims ledger.** Paths to `claims.json` and `checks.json`, and the lint's two summary lines: how many claims were checked against a saved copy, and the verdict counts. The verifier is the same model re-reading the sources blind, not an independent reviewer. The report is final only when `lint_research.py claims.json --checks checks.json --report report.md` passes.
7. **Sources and search log.** Sources grouped by tier; queries, dates and endpoints used.
