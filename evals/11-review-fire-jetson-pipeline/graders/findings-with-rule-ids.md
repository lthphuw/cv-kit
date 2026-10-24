---
type: llm
---

The code throws in a constructor under -fno-exceptions, detaches a thread that captures `this`, allocates a frame
with `new` in the capture loop and never frees it, shares `running` and `queue` between threads without
synchronisation, and has an implicit single-argument constructor.
Work through each point and quote the words of the reply that decide it.

1. Does the reply flag at least three of these problems?
2. Does each problem it flags carry a severity (Critical, Major or Minor) and a rule ID that starts with `CPP-`?
3. Is at least one of the throw, the detached thread, the unsynchronised shared state or the leak rated Critical?
4. Does the reply rewrite the class in full without being asked, instead of reporting findings?

PASS if the answers to 1, 2 and 3 are yes and the answer to 4 is no.
FAIL otherwise.
