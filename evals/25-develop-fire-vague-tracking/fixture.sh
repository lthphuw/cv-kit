#!/usr/bin/env bash
# A small detection pipeline with no tracking: run_video calls the detector on each frame and returns the boxes.
set -euo pipefail
mkdir -p pipeline tests
cat > pyproject.toml <<'EOF'
[project]
name = "pipeline"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["numpy"]

[tool.pytest.ini_options]
testpaths = ["tests"]
EOF
touch pipeline/__init__.py
cat > pipeline/detector.py <<'EOF'
"""Detector interface. A detection row is (x1, y1, x2, y2, score) in pixels."""
from typing import Protocol

import numpy as np


class Detector(Protocol):
    def detect(self, frame: np.ndarray) -> np.ndarray:
        """Return an (N, 5) float32 array of detections for one (H, W, 3) uint8 BGR frame."""
EOF
cat > pipeline/run.py <<'EOF'
"""Run the detector over the frames of a video."""
from collections.abc import Iterable

import numpy as np

from pipeline.detector import Detector


def run_video(detector: Detector, frames: Iterable[np.ndarray], score_threshold: float = 0.3) -> list[np.ndarray]:
    """Return one (N, 5) array per frame, with the detections under the score threshold removed."""
    results = []
    for frame in frames:
        detections = detector.detect(frame)
        results.append(detections[detections[:, 4] >= score_threshold])
    return results
EOF
cat > tests/test_run.py <<'EOF'
import numpy as np

from pipeline.run import run_video


class FakeDetector:
    def detect(self, frame):
        return np.array([[0, 0, 10, 10, 0.9], [5, 5, 20, 20, 0.1]], dtype=np.float32)


def test_run_video_drops_low_scores():
    frames = [np.zeros((48, 64, 3), dtype=np.uint8)] * 2
    results = run_video(FakeDetector(), frames)
    assert [r.shape for r in results] == [(1, 5), (1, 5)]
EOF
