---
description: A request for a /goal line goes to develop, which writes one bounded line to paste and changes no code.
expected_outcome: develop fires; the reply holds one fenced /goal line with a turn limit and its stop rules; no file is edited.
tags: [trigger, fire, behaviour]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

I am leaving for the night. Write me a /goal line so Claude adds a `letterbox(image, size)` function to vision/preprocess.py, test first, and stops on its own. Tests run with `pytest -q`.
