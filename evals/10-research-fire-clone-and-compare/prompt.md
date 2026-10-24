---
description: A request to compare a repository's code with its paper goes to research, which keeps evidence in research/<slug>/.
expected_outcome: research fires; the plan clones the repository at a recorded commit into research/<slug>/ and runs nothing from it without a yes.
tags: [trigger, fire, behaviour]
max_turns: 16
allowed_tools: [Read, Glob, Grep, Skill]
---

The DEIMv2 README claims a COCO AP I do not trust. Pull the repository and the paper, and check whether the loss in the code is what the paper describes.
