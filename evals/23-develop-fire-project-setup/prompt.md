---
description: A request to set a Python project up with strict lint and the house rules goes to develop, which shows the plan and writes nothing before a yes.
expected_outcome: develop fires; the reply lists what it would add, keeps the existing ruff settings, and no file is written.
tags: [trigger, fire, behaviour]
max_turns: 14
allowed_tools: [Read, Glob, Grep, Skill]
---

Set this repo up the cv-kit way: strict ruff and mypy, and the rules for Python style and tests. Don't overwrite anything I already have.
