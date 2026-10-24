---
description: A hard, unclear bug goes to develop, which dispatches the engineer agent on opus.
expected_outcome: develop fires; an engineer agent is dispatched with model opus.
tags: [trigger, fire, routing]
max_turns: 20
allowed_tools: [Read, Glob, Grep, Skill, Agent]
---

Our C++ frame pipeline deadlocks about once an hour on the Jetson, only with two cameras, and we do not know why. The grabber, the queue and the inference thread are in src/pipeline/. Please find and fix it.
