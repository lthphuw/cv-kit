---
description: A behaviour-preserving clean-up request goes to py-cpp-refactor, which pins behaviour before editing.
expected_outcome: py-cpp-refactor fires; py-cpp-review does not; the reply plans tests before changes.
tags: [trigger, fire, behaviour]
max_turns: 16
allowed_tools: [Read, Glob, Grep, Skill]
---

Clean up this loader so it follows our Python style, but it must keep returning exactly the same arrays, other scripts depend on it.

```python
import os, cv2, numpy as np
def load(dir, size=(224,224), cache={}):
    out = []
    for f in os.listdir(dir):
        if f.endswith(".jpg") == True:
            img = cv2.imread(dir + "/" + f)
            img = cv2.resize(img, size)
            out.append(img / 255.)
    cache[dir] = out
    return np.array(out)
```
