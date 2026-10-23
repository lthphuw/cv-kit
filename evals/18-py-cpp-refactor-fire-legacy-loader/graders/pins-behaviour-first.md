---
type: llm
---

Work through each point and quote the words of the reply that decide it.

1. Before or together with any rewritten code, does the reply say how the current behaviour will be pinned (tests,
   saved outputs, or a comparison of old and new arrays on real images)?
2. Does the reply keep or explicitly ask about behaviour other scripts may rely on, such as the file order from
   `os.listdir`, the BGR channel order, the float64 dtype, or the shared `cache` default?
3. Does the reply silently change one of those behaviours (for example sorts the files, converts to RGB, changes the
   dtype) while claiming the output is unchanged?

PASS if the answers to 1 and 2 are yes and the answer to 3 is no.
FAIL otherwise.
