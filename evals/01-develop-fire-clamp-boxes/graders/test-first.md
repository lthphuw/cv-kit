---
type: llm
focus:
  source: file
  path: tests/test_utils.py
---

This is the test file after the run. The run could not run pytest. Work through each point and quote the lines that
decide it.

1. Are there pytest tests for `clamp_boxes` (imported from `vision.utils`)?
2. Does one of them check a box that lies fully outside the image, and expect it to be dropped?
3. Does one of them check a box that ends up with zero width or zero height after clipping, and expect it to be
   dropped?
4. Does one of them check a box partly outside the image, and expect it to be clipped to the image edge?

PASS if the answers to 1, 2 and 3 are yes and the expected values in the tests are right for clipping to
`[0, width]` and `[0, height]`.
FAIL otherwise.
