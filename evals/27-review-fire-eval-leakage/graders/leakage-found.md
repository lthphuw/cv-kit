---
type: llm
---

The code has these defects. (a) It shuffles frames, not videos, so frames of one video land in both train and test.
(b) It picks the threshold that gives the best F1 on the test set and prints that F1 as the test result. (c) It
shuffles with the unseeded global `random` over an unsorted `glob`, so the split changes from run to run. (d) It runs
the model without `eval()` or `inference_mode`.
Work through each point and quote the words of the reply that decide it.

1. Does the reply flag (a)?
2. Does the reply flag (b)?
3. Is (a) or (b) given the most severe rating the reply uses (Critical, blocker or the like), or said to make the
   printed F1 invalid?
4. Does the reply rewrite the script in full without being asked, instead of reporting findings?

PASS if the answers to 1, 2 and 3 are yes and the answer to 4 is no.
FAIL otherwise.
