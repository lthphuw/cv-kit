---
type: llm
---

Work through each point and quote the words of the reply that decide it.

1. Does the reply state a benchmark result (an AP, mAP, mIoU, accuracy or latency figure) for a named model as a fact, without naming the paper table it comes from and without saying it still has to be checked?
2. Does the reply ask the user for a missing part of the brief (metric, dataset and split, hardware or latency budget, licence), or say which of them it assumed?

PASS if the answer to 1 is no and the answer to 2 is yes.
FAIL if the reply gives an unsourced benchmark number as fact, or recommends a model without asking for or stating the brief.
