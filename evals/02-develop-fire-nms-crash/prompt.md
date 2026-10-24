---
description: A bug report in C++ goes to develop, which reproduces it with a GoogleTest test before fixing it.
expected_outcome: develop fires; the plan reproduces the crash with a GoogleTest test and looks for the root cause first.
tags: [trigger, fire, behaviour]
max_turns: 16
allowed_tools: [Read, Glob, Grep, Skill]
---

Our NMS function crashes on the Jetson build when there are zero detections. It is in src/post/nms.cc. Can you fix it? We build with CMake.
