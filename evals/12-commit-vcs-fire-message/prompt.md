---
description: Asking what a commit should say goes to commit-vcs, and the message carries no trailer.
expected_outcome: commit-vcs fires; the suggested message has no trailer.
tags: [trigger, fire, behaviour]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

What should the commit message say for this change? I renamed load_weights to load_checkpoint and pinned the Hugging Face revision in configs/model.yaml.
