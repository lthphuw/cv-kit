---
name: cv-deep-research
description: Use when the user must choose or customize a computer-vision model, backbone, head or loss and needs evidence with citations, or asks for SOTA, a literature comparison or a design recommendation backed by papers.
---

# Sourced deep research for CV model decisions

Every number in the final report must trace to a paper table. Aggregator sites nominate candidates; they are never the citation.

Read `${CLAUDE_SKILL_DIR}/../../shared/sources.md` (what is reachable and how) and `${CLAUDE_SKILL_DIR}/../../shared/licenses.md` first.

## Phases
1. **Frame.** Write the brief: task, metric, dataset and split, hardware and latency budget, licence constraint, and what is being customized. Ask the user for anything missing, one question at a time. Save it as `brief.md` in a working folder.
2. **Scout.** Sweep the sources in `sources.md` (arXiv, Hugging Face Papers, CVF, GitHub code search, `paperswithcode.co` for leads). Output a candidate list with one line each.
3. **Shortlist.** Show the user the list and wait for approval of the candidates to read in depth. Stop here; do not start the expensive phase unapproved.
4. **Deep-read.** Dispatch one `model-scout` agent per approved candidate, in parallel, with the brief, the candidate and an output path. Tell each what is already ruled out.
5. **Cross-check.** Merge the claims into `claims.json`: one JSON array formed by concatenating every scout file's `claims` array. Carry each scout file's `not_found` list into report section 7. Run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/lint_research.py" claims.json`, then dispatch a separate verifier agent that re-opens each cited locator and confirms the quote. Remove or relabel any claim it cannot confirm as `unverified`.
6. **Synthesise.** Fill `${CLAUDE_SKILL_DIR}/references/report-template.md`. Compare numbers only when dataset, split, resolution and hardware match; otherwise say they are not comparable. List what was not found.
7. **Hand off.** If the `rnd-notebook` skill is installed, offer to record the decision there; otherwise save `report.md` and `claims.json` in the working folder.

## Rules
- Each claim carries value, metric, dataset and split, resolution, hardware, arXiv id with version, locator and a verbatim quote, plus a label: `reported`, `reproduced` or `unverified`.
- Never state a benchmark number from memory.
- A claim you could not confirm is listed under "not found", not dropped.
- State the licence of every candidate in the comparison.
