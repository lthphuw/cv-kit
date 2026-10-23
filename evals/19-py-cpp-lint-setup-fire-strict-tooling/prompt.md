---
description: Asking to set up strict linters and warnings for a Python plus CMake C++ repo goes to py-cpp-lint-setup.
expected_outcome: py-cpp-lint-setup fires.
tags: [trigger, fire]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Our repo has the Python training code and a CMake C++ inference app for the edge box. Nothing enforces style yet. Set up strict linting, formatting, type checks and compiler warnings for both.
