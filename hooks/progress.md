Main thread only, without being asked, in the user's language (labels may be translated):
- A background agent finishes while others still run: print this block at once, one line per agent, status as a
  word, no icons, no other prose.
  Not at launch, and not when the last one finishes: Summarization covers that.
```
Progress (2/3 done):
- engineer#1 clamp_boxes: done, 4 tests pass
- engineer#2 NMS crash: running
- engineer#3 loader: failed twice, escalating to opus
```
- A finished task, not a plain answer, puts the skipped-or-risk line first, then `Summarization:`
  (at most 5 bullets, each a result and its evidence), then `Next:` (at most 3 copy-pasteable prompts from the
  context) as the very last block. Flow: develop green, `/cv-kit:review`; review with 0 blocking, `/cv-kit:commit`;
  research done, `/cv-kit:develop` on its next steps; a failure, the prompt that fixes it.
  Never suggest a commit while tests are red or blocking findings are open.
