---
description: A routine bug that a test can reproduce goes to develop, which briefs the engineer agent on sonnet.
expected_outcome: develop fires; an engineer agent is dispatched with model sonnet and a brief with its fields; no agent runs on opus.
tags: [trigger, fire, routing]
max_turns: 20
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Agent]
---

The boxes we map back from the letterboxed input land in the wrong place on portrait images; landscape images are fine. The code is in vision/letterbox.py and we use pytest. Please fix it.
