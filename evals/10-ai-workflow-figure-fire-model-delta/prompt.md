---
description: A figure of what changed between two model versions goes to ai-workflow-figure.
expected_outcome: ai-workflow-figure fires.
tags: [trigger, fire]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Make a figure that shows what changed between v1 and v2 of our segmentation model: v2 replaced the ResNet-50 encoder with a ViT-S/16 and added an auxiliary edge head.
