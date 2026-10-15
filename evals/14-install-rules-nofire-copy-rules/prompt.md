---
description: install-rules is user-invoked only, so the model must never call it, even when asked in prose.
expected_outcome: install-rules is never invoked through the Skill tool.
tags: [trigger, nofire]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Install cv-kit's rules into this project's .claude/rules folder.
