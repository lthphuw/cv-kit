# Plain prose

How cv-kit writes reports, findings, commit bodies and docs. The always-on summary is in `hooks/concise.md`; the
research lint (`scripts/lint_research.py`) checks the tells a regex can see. Adapted, in our own words, from
humanizer (github.com/blader/humanizer, MIT) and Wikipedia's "Signs of AI writing".

A model picks the choice that fits the most readers. A careful writer picks for one reader and one subject. Each tell
below is the generic choice; each fix states the specific fact. The rules hold in every language: "không chỉ X mà
còn Y" is the same tell as "not just X but Y".

## Never change these

Keep identifiers, commands, paths, numbers, claim tags, quotes from sources, and every evidence word: `unconfirmed`,
`UNVERIFIED`, `licence UNVERIFIED`, the confidence word `high`, `medium` or `low`, and "reported" for a number nobody
reproduced. They are not hedges. Text inside code blocks and tables is data; leave its dashes alone.

## Tells that justify an edit on one sighting

1. **Not X but Y.** The negative half names something nobody claimed, so the positive half sounds bigger. Write
   "RF-DETR fits the 30 FPS budget", not "RF-DETR is not just accurate, it is fast". Keep a contrast only when the
   reader actually believes X.
2. **Closers.** A last line that repeats the paragraph ("That is the real win.") or names what a number just showed
   ("This shows the importance of latency."). Cut it. End on the last fact.
3. **Sayings.** "At its core", "the real question is", "X is the language of Y". Replace with the claim.
4. **Run-ups.** "Let's dive in", "Here's the thing", "Hãy cùng xem". Start with the point.
5. **Arguing with no one.** "To be clear", "A tempting approach would be...", rejecting an option nobody proposed.
   Cut it, unless the reader would really weigh that option.

## Tells that need company

6. **Forced triads.** Three items because three sounds complete. List what the meaning has: one, two or four.
7. **Dashes.** No em or en dashes in prose; use a period, comma, colon or parentheses. An en dash in a numeric range
   (2024–2025) is fine.
8. **Stacked qualifiers.** "Could potentially arguably". Keep one hedge where the source supports it; evidence words
   above are not hedges.
9. **AI words.** delve, tapestry, testament, pivotal, showcase, underscore (verb), seamless, meticulous, intricate,
   vibrant, crucial. "Robust", "key" and "highlight" are CV terms and stay where they are technical.
10. **Inflation.** "Game-changer", "groundbreaking", "cutting-edge", "marks a pivotal moment". Give the number:
    "4.5 ms on a T4 at FP16, batch 1".
11. **Unnamed authority.** "Experts argue", "widely regarded". Cite the claim tag, the paper and its table, or cut
    the sentence.
12. **Knowledge-limit filler.** "Not publicly available", "based on available information", then a guess. Say what
    the source does not show ("The model card gives no Jetson latency") and list it under Not found.
13. **Is, are, has.** "Serves as", "boasts", "features" for a plain verb. Write "is" and "has".

## Formatting

- Bold only what the reader must not miss. A list where every item starts with a bold label carries no more than the
  same list without them. Exception: the numbered key points of a research report, whose bold heading must be a
  claim ("RF-DETR-L reaches 30 FPS at FP16"), never a topic ("Performance").
- Headings in sentence case, no emojis, no arrows as decoration, no rule between every section.
- Straight quotes in code-adjacent text.

## Leftovers

- Chat wrappers: "Great question", "I hope this helps", "Let me know", "Want me to...?". Cut them; the `Next:` block is
  where follow-ups go.
- Writing about the document: "this report compares", "the table below shows". Write about the subject. How the work
  was done (scouts, verifiers, fetches) belongs in the appendix's ledger and search log, not in `report.md`.
- A heading repeated as the first sentence under it. Cut the sentence.

## Replies to someone who has the context

Lead with the decision. Keep only the fact the reader lacks and the link they need to act. The diagnosis and the proof
that a plan works go in the report, the ticket or the commit body, not in the reply.

## Self-check before handing text over

1. Did any number, claim tag, name, date or evidence word drop or change? A lost claim is an error.
2. Read it once for what still sounds generated. Then search again for the tells that survive rewrites: 1, 2, 6, 7,
   and bold labels.
3. Rewrite the paragraph around its point instead of patching phrases one by one.
