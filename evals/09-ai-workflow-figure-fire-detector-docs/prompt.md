---
description: An architecture figure of a model goes to ai-workflow-figure, which reads facts from code and invents none.
expected_outcome: ai-workflow-figure fires and says the code is missing instead of inventing the architecture.
tags: [trigger, fire, behaviour]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Draw a hand-drawn architecture figure of our detector for the docs page. The model code is in src/detector/model.py and the config is configs/det.yaml.
