# <Decision>: <one-line question>
Date, brief hash, cv-kit version, tool versions.

Cite a claim as `[<candidate-slug>-<n>]`, its id in `claims.json`. A claim whose verdict is not `confirmed` is cited only on a line that also says "unconfirmed". The lint checks both.

## 1. TL;DR
Recommendation in three sentences, with the main risk and a confidence word (`high`, `medium` or `low`, as `claim-checks.md` defines it).

## 2. Context and constraints
Copied from the brief: task, metric, dataset and split, hardware and latency budget, licence constraint.

## 3. Candidate comparison
One row per candidate and setting, with these columns:

| Candidate | Value | Metric | Dataset and split | Resolution | Hardware | Version | Licence | Claim |
|---|---|---|---|---|---|---|---|---|

`Value` is the claim's value as the source states it; `Claim` holds its tag. Numbers appear only if the dataset, split, resolution and hardware match across rows; otherwise write `not comparable` in `Value`. When two sources give different numbers for one setting (arXiv v1 against v2, a paper against a README), give each its own row.

### 3b. Considered and excluded
Each candidate dropped at the shortlist, with its reason (licence, task, no weights, no traceable numbers, stack) and the deciding fact.

## 4. Recommended design
What to build or change, and why this beats the alternatives under the constraints.

## 5. Risks and unknowns
- Stress tests, answered before recommending: Does the pick still win without its strongest claim? Does it still win on the other benchmarks in the ledger? Which single claim, if wrong, would change the pick?
- The `caveats` that are concerns, per candidate, with their locators.

## 6. Ablation and validation plan
Smallest experiments that would confirm or kill the recommendation, with the metric and the data they use.

## 7. Not found or not checked
Every item the scouts could not locate (`not_found`), every source they could not reach (`access_failed`), and every claim whose verdict is `absent` or `unreachable`.

## 8. Claims ledger
Paths to `claims.json` and `checks.json`, and the lint's two summary lines: how many claims were checked against a saved copy, and the verdict counts. The verifier is the same model re-reading the sources blind, not an independent reviewer. The report is final only when `lint_research.py claims.json --checks checks.json --report report.md` passes.

## 9. Sources and search log
Sources grouped by tier; queries, dates and endpoints used.
