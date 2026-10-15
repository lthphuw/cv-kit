---
description: Checking one benchmark claim goes to cv-deep-research, which does not settle it from memory.
expected_outcome: cv-deep-research fires and neither confirms nor refutes the figures without the paper.
tags: [trigger, fire, behaviour]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

A blog post says RF-DETR gets 54.7 AP on COCO val2017 at 4.5 ms on a T4. Is that claim right? Check it against the paper before I put it in our design doc.
