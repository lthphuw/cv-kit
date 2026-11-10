---
description: A request to set a Python project up with strict lint and the house rules goes to develop, which shows the plan before writing any config.
expected_outcome: develop fires; no config file is written before the user says yes.
tags: [trigger, fire]
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---

Set this repo up the cv-kit way: strict ruff and mypy, and the rules for Python style and tests. Don't overwrite anything I already have.
