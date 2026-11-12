#!/usr/bin/env bash
# A Python project that already configures ruff in pyproject.toml, with no mypy config and no .claude/rules.
set -euo pipefail
mkdir -p vision tests
cat > pyproject.toml <<'EOF'
[project]
name = "vision"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["numpy"]

[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F"]

[tool.pytest.ini_options]
testpaths = ["tests"]
EOF
touch vision/__init__.py
cat > vision/boxes.py <<'EOF'
"""Box helpers. Boxes are float arrays of shape (N, 4) in xyxy pixel coordinates."""
import numpy as np


def box_area(boxes: np.ndarray) -> np.ndarray:
    """Return the area of each box; a box with x2 <= x1 or y2 <= y1 has area 0."""
    width = np.clip(boxes[:, 2] - boxes[:, 0], 0, None)
    height = np.clip(boxes[:, 3] - boxes[:, 1], 0, None)
    return width * height
EOF
cat > tests/test_boxes.py <<'EOF'
import numpy as np

from vision.boxes import box_area


def test_box_area():
    boxes = np.array([[0, 0, 2, 3], [5, 5, 4, 4]], dtype=float)
    assert box_area(boxes).tolist() == [6.0, 0.0]
EOF
