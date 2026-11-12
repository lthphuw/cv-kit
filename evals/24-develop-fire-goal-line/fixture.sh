#!/usr/bin/env bash
# A small Python project: vision/preprocess.py has a plain resize, pytest is configured, and letterbox is missing.
set -euo pipefail
mkdir -p vision tests
cat > pyproject.toml <<'EOF'
[project]
name = "vision"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["numpy", "opencv-python-headless"]

[tool.pytest.ini_options]
testpaths = ["tests"]
EOF
touch vision/__init__.py
cat > vision/preprocess.py <<'EOF'
"""Image preprocessing. Images are uint8 arrays of shape (H, W, 3) in BGR order."""
import cv2
import numpy as np


def resize(image: np.ndarray, size: int) -> np.ndarray:
    """Resize to size x size without keeping the aspect ratio."""
    return cv2.resize(image, (size, size), interpolation=cv2.INTER_LINEAR)
EOF
cat > tests/test_preprocess.py <<'EOF'
import numpy as np

from vision.preprocess import resize


def test_resize_returns_a_square_image():
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    assert resize(image, 320).shape == (320, 320, 3)
EOF
