#!/usr/bin/env bash
# A Python project where letterbox_params takes the scale from the width alone, so portrait images get a scale that
# is too large. The one existing test uses a landscape image.
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
cat > vision/letterbox.py <<'EOF'
"""Letterbox geometry and the mapping of boxes back to the original image."""
import numpy as np


def letterbox_params(height: int, width: int, size: int) -> tuple[float, int, int]:
    """Return (scale, pad_x, pad_y) that fit a height x width image into a size x size square."""
    scale = size / width
    pad_x = (size - round(width * scale)) // 2
    pad_y = (size - round(height * scale)) // 2
    return scale, pad_x, pad_y


def boxes_to_original(boxes: np.ndarray, scale: float, pad_x: int, pad_y: int) -> np.ndarray:
    """Map (N, 4) xyxy boxes from the letterboxed square back to the original image."""
    out = boxes.astype(np.float64)
    out[:, [0, 2]] -= pad_x
    out[:, [1, 3]] -= pad_y
    return out / scale
EOF
cat > tests/test_letterbox.py <<'EOF'
import numpy as np

from vision.letterbox import boxes_to_original, letterbox_params


def test_landscape_box_maps_back():
    scale, pad_x, pad_y = letterbox_params(height=480, width=640, size=320)
    assert (scale, pad_x, pad_y) == (0.5, 0, 40)
    boxes = np.array([[10, 50, 110, 150]], dtype=np.float32)
    assert boxes_to_original(boxes, scale, pad_x, pad_y).tolist() == [[20.0, 20.0, 220.0, 220.0]]
EOF
