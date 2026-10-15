---
description: A model choice that asks for no papers goes to cv-model-selection, not cv-deep-research, and keeps its licence rules.
expected_outcome: cv-model-selection fires; cv-deep-research does not; every named model carries a licence.
tags: [trigger, fire, behaviour]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Which object detector should I start from for 30 FPS on a Jetson Orin NX? It is for a commercial product, so Apache-2.0 or MIT licences only.
