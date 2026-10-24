---
type: llm
focus:
  source: file
  path: src/post/nms.cc
---

This is `src/post/nms.cc` after the run. In the original, `scores[order.front()]` is read before anything checks that
there is a box, so zero detections read past the end of an empty vector. Work through each point and quote the lines
that decide it.

1. When `boxes` is empty, can `Nms` return without reading `order.front()`, `scores[0]` or any element?
2. Does a non-empty input still follow the same path as before (sort by score, score threshold, suppress by IoU)?
3. Is the fix small: no new class, no new dependency, no rewrite of the algorithm?

PASS if all three answers are yes.
FAIL otherwise.
