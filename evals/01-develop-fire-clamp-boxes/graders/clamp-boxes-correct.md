---
type: llm
focus:
  source: file
  path: vision/utils.py
---

This is `vision/utils.py` after the run. Work through each point and quote the lines that decide it.

1. Is there a function `clamp_boxes(boxes, width, height)`?
2. Does it clip x1 and x2 into `[0, width]` and y1 and y2 into `[0, height]`?
3. Does it drop the boxes whose width or height is zero or negative after clipping, and return the others in their
   original order?
4. Does it leave the existing `box_area` and `xyxy_to_xywh` unchanged?

PASS if all four answers are yes.
FAIL otherwise.
