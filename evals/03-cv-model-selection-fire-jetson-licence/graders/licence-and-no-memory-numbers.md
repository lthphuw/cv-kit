---
type: llm
---

Work through each point and quote the words of the reply that decide it.

1. If the reply names one or more models to start from, does each one come with its licence, or with a note that the licence is unverified and must be checked?
2. Does the reply state a benchmark score (AP, mAP, FPS or latency) for a named model as a measured fact, without a source?

If the reply only asks the user about a missing constraint (number of classes, training images, precision, input size), point 1 does not apply.
PASS if point 1 holds or does not apply, and the answer to 2 is no.
FAIL if a recommended model has no licence and no "unverified" note, or a benchmark number is stated from memory.
