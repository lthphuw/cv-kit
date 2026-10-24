---
description: A read-only lookup inside a development task goes to the explorer agent on haiku.
expected_outcome: develop fires; an explorer agent is dispatched with model haiku.
tags: [trigger, fire, routing]
max_turns: 20
allowed_tools: [Read, Glob, Grep, Skill, Agent]
---

Before I change anything: where in this repository is the non-maximum suppression threshold read from the config, and which functions use it? Only find and list; do not change code.
