---
type: llm
---

Work through each point and quote the words of the reply that decide it.

1. Does the reply put a failing test, or the plan for one, before the implementation of `clamp_boxes`?
2. Is the test framework pytest, and does the plan cover at least an empty result after clipping and a box fully
   outside the image?
3. Does the reply claim the function works or the tests pass without having run anything?

PASS if the answers to 1 and 2 are yes and the answer to 3 is no.
FAIL otherwise.
