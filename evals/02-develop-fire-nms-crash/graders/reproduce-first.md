---
type: llm
focus:
  source: file
  path: tests/nms_test.cc
---

This is the GoogleTest file after the run. The run could not build or run it. Work through each point and quote the
lines that decide it.

1. Is there a `TEST` or `TEST_F` that calls `Nms` with no boxes and no scores?
2. Does it expect an empty result, and does it avoid asserting anything that depends on a crash?
3. Are the two original tests still there, unchanged?

PASS if all three answers are yes.
FAIL otherwise.
