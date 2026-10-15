---
description: A backbone comparison that asks for paper tables and citations goes to cv-deep-research.
expected_outcome: cv-deep-research fires; cv-model-selection does not.
tags: [trigger, fire]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Compare DINOv2 and SigLIP2 as frozen backbones for a semantic segmentation head on ADE20K. I need the numbers from the papers' own tables, with citations, before we commit to one.
