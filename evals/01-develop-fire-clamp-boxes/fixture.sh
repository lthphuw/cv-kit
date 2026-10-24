#!/usr/bin/env bash
# A small Python project: vision/utils.py exists, pytest is configured, and clamp_boxes is missing.
set -euo pipefail
mkdir -p vision tests
cat > pyproject.toml <<'EOF'
[project]
name = "vision"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["numpy"]

[tool.pytest.ini_options]
testpaths = ["tests"]
EOF
touch vision/__init__.py
cat > vision/utils.py <<'EOF'
"""Box helpers. Boxes are float arrays of shape (N, 4) in xyxy pixel coordinates."""
import numpy as np


def box_area(boxes: np.ndarray) -> np.ndarray:
    """Return the area of each box; a box with x2 <= x1 or y2 <= y1 has area 0."""
    width = np.clip(boxes[:, 2] - boxes[:, 0], 0, None)
    height = np.clip(boxes[:, 3] - boxes[:, 1], 0, None)
    return width * height


def xyxy_to_xywh(boxes: np.ndarray) -> np.ndarray:
    """Convert xyxy boxes to (x, y, width, height)."""
    out = boxes.copy()
    out[:, 2] = boxes[:, 2] - boxes[:, 0]
    out[:, 3] = boxes[:, 3] - boxes[:, 1]
    return out
EOF
cat > tests/test_utils.py <<'EOF'
import numpy as np

from vision.utils import box_area, xyxy_to_xywh


def test_box_area():
    boxes = np.array([[0, 0, 2, 3], [5, 5, 4, 4]], dtype=float)
    assert box_area(boxes).tolist() == [6.0, 0.0]


def test_xyxy_to_xywh():
    boxes = np.array([[1, 2, 4, 6]], dtype=float)
    assert xyxy_to_xywh(boxes).tolist() == [[1.0, 2.0, 3.0, 4.0]]
EOF
