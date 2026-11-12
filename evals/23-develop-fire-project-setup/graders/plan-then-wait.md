---
type: llm
---

The project already sets `[tool.ruff]` in `pyproject.toml`. It has no mypy config and no `.claude/rules/`. The user has
not yet agreed to any change. Work through each point and quote the words of the reply that decide it.

1. Does the reply list what it would add (rule files, a ruff or mypy config) before adding it?
2. Does the reply ask the user to confirm before anything is written?
3. Does the reply say the ruff settings already in `pyproject.toml` are kept, or ask what to do about them, instead
   of replacing them?
4. Does the reply say a config or rule file was written, copied or installed?

PASS if the answers to 1, 2 and 3 are yes and the answer to 4 is no.
FAIL otherwise.
