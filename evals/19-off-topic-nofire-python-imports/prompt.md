---
description: A plain Python question triggers no cv-kit skill.
expected_outcome: No cv-kit skill fires.
tags: [trigger, nofire]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Which imports are unused here?

import os
import sys
import json

print(json.dumps({"ok": True}))
