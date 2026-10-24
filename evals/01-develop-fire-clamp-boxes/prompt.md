---
description: A small feature request in a Python project goes to develop, which starts from a failing pytest test.
expected_outcome: develop fires; the plan writes a failing pytest test before the implementation.
tags: [trigger, fire, behaviour]
max_turns: 16
allowed_tools: [Read, Glob, Grep, Skill]
---

Add a function `clamp_boxes(boxes, width, height)` to our `vision/utils.py` that clips xyxy boxes to the image and drops boxes that end up empty. We use pytest.
