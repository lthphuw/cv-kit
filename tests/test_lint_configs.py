"""Run the shipped lint and build configs with the real tools: bad code must fail, good code must pass.

CI installs the pinned tools (see .github/workflows/validate.yml). Locally a test skips when its tool is missing.
"""
import os
import re
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "skills/setup/assets"

GOOD_PY = '''\
"""Crop helpers for detector inputs."""

import logging

import numpy as np
import numpy.typing as npt

_LOGGER = logging.getLogger(__name__)


def center_crop(
    image: npt.NDArray[np.uint8], size: int
) -> npt.NDArray[np.uint8]:
    """Crops the center of an image.

    Args:
        image: Array of shape (H, W, C), RGB, uint8.
        size: Side of the square crop in pixels.

    Returns:
        A view of shape (size, size, C) into `image`.

    Raises:
        ValueError: If `size` is not positive or larger than the image.
    """
    height, width = image.shape[:2]
    if not 0 < size <= min(height, width):
        msg = f"size must be in (0, {min(height, width)}], got {size=}"
        raise ValueError(msg)
    top = (height - size) // 2
    left = (width - size) // 2
    _LOGGER.debug("crop at top=%d left=%d", top, left)
    return image[top : top + size, left : left + size]
'''

BAD_PY = '''\
import os, sys
from .x import y
import numpy as np

def load(paths, cache={}):
    try:
        f = open(paths[0])
        data = f.read()
    except:
        pass
    assert data
    print("loaded " + paths[0])
    np.random.seed(0)
    if data == None:
        return
    # TODO: fix later
    return data
'''
BAD_PY_CODES = {"E401", "TID252", "B006", "SIM115", "E722", "S101", "T201", "NPY002", "E711", "ANN001"}

GOOD_CC = """\
#include <cstdint>
#include <vector>

namespace {

constexpr int kChannels = 3;

class Frame {
 public:
  explicit Frame(int width) : width_(width) {}

  [[nodiscard]] int width() const { return width_; }

 private:
  int width_;
};

[[nodiscard]] std::int64_t SumPixels(const std::vector<std::int32_t>& pixels) {
  std::int64_t total = 0;
  for (const std::int32_t value : pixels) {
    total += value;
  }
  return total * kChannels;
}

}  // namespace

int main() {
  const Frame frame(4);
  const std::vector<std::int32_t> pixels(4, 1);
  return SumPixels(pixels) == 12 && frame.width() == 4 ? 0 : 1;
}
"""

BAD_CC = """\
#include <vector>
using namespace std;

int global_counter = 0;
const int max_size = 64;

class detector {
 public:
  detector(int n) : n(n) {}
  int n;
};

int run(vector<int> v) {
  int total = 0;
  for (int i = 0; i < v.size(); i++) total += v[i];
  float f = (float)total;
  try { throw 1; } catch (...) {}
  return static_cast<int>(f * 0.5);
}
"""
BAD_CC_TIDY = {"google-build-using-namespace", "cppcoreguidelines-avoid-non-const-global-variables",
               "readability-identifier-naming", "google-explicit-constructor", "google-readability-casting",
               "readability-braces-around-statements"}
BAD_CC_GCC = {"-Werror=sign-compare", "-Werror=old-style-cast", "-Werror=double-promotion",
              "exception handling disabled"}


def tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        if os.environ.get("CI"):
            pytest.fail(f"{name} is required in CI to check the shipped configs")
        pytest.skip(f"{name} not installed")
    return path


def run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", check=False)


@pytest.fixture
def py_project(tmp_path: Path) -> Path:
    for name in ("ruff.toml", "mypy.ini"):
        shutil.copyfile(ASSETS / "python" / name, tmp_path / name)
    (tmp_path / "good.py").write_text(GOOD_PY, encoding="utf-8")
    (tmp_path / "bad.py").write_text(BAD_PY, encoding="utf-8")
    return tmp_path


@pytest.fixture
def cc_project(tmp_path: Path) -> Path:
    shutil.copytree(ASSETS / "cpp", tmp_path, dirs_exist_ok=True)
    (tmp_path / "good.cc").write_text(GOOD_CC, encoding="utf-8")
    (tmp_path / "bad.cc").write_text(BAD_CC, encoding="utf-8")
    return tmp_path


def test_ruff_passes_good_code(py_project):
    ruff = tool("ruff")
    result = run([ruff, "check", "--no-cache", "good.py"], py_project)
    assert result.returncode == 0, result.stdout + result.stderr
    result = run([ruff, "format", "--no-cache", "--check", "good.py"], py_project)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "warning" not in result.stderr.lower(), result.stderr


def test_ruff_flags_bad_code(py_project):
    result = run([tool("ruff"), "check", "--no-cache", "--output-format", "concise", "bad.py"], py_project)
    found = set(re.findall(r"\b([A-Z]+\d+)\b", result.stdout))
    assert result.returncode == 1
    assert BAD_PY_CODES <= found, f"missing: {sorted(BAD_PY_CODES - found)}"


def test_mypy_is_strict(py_project):
    mypy = tool("mypy")
    (py_project / "untyped.py").write_text("def f(x):\n    return x\n", encoding="utf-8")
    result = run([mypy, "--config-file", "mypy.ini", "--no-incremental", "untyped.py"], py_project)
    assert result.returncode == 1 and "no-untyped-def" in result.stdout, result.stdout + result.stderr


def test_clang_tidy_config_is_valid(cc_project):
    result = run([tool("clang-tidy"), "--verify-config"], cc_project)
    assert result.returncode == 0 and "No config errors detected" in result.stdout, result.stdout + result.stderr
    assert "warning" not in (result.stdout + result.stderr).lower()


def test_clang_tidy_passes_good_and_flags_bad_code(cc_project):
    tidy = tool("clang-tidy")
    good = run([tidy, "good.cc", "--", "-std=c++20", "-fno-exceptions", "-fno-rtti"], cc_project)
    assert good.returncode == 0, good.stdout
    bad = run([tidy, "bad.cc", "--", "-std=c++20"], cc_project)
    found = set(re.findall(r"\[([a-z0-9.-]+)(?:,[^\]]*)?\]", bad.stdout))
    found |= {name for group in re.findall(r"\[([^\]]+)\]", bad.stdout) for name in group.split(",")}
    assert BAD_CC_TIDY <= found, f"missing: {sorted(BAD_CC_TIDY - found)}"


def test_clang_format_keeps_good_code(cc_project):
    result = run([tool("clang-format"), "--dry-run", "--Werror", "good.cc"], cc_project)
    assert result.returncode == 0, result.stderr


def test_clang_format_adds_braces(cc_project):
    (cc_project / "loop.cc").write_text("void F(int n) {\n  for (int i = 0; i < n; ++i) G(i);\n}\n", encoding="utf-8")
    result = run([tool("clang-format"), "loop.cc"], cc_project)
    assert "{\n    G(i);\n  }" in result.stdout, result.stdout


def test_cmake_module_builds_good_code_and_rejects_bad_code(cc_project):
    cmake = tool("cmake")
    tool("g++")
    (cc_project / "CMakeLists.txt").write_text(textwrap.dedent("""\
        cmake_minimum_required(VERSION 3.20)
        project(probe CXX)
        include(cmake/cv_kit_strict.cmake)
        add_executable(good good.cc)
        cv_kit_strict(good)
        add_executable(bad bad.cc)
        cv_kit_strict(bad)
        """), encoding="utf-8")
    env = {**os.environ, "CXX": "g++"}
    configure = subprocess.run([cmake, "-S", ".", "-B", "build", "-DCMAKE_BUILD_TYPE=Debug"], cwd=cc_project,
                               capture_output=True, text=True, env=env, check=False)
    assert configure.returncode == 0, configure.stdout + configure.stderr
    good = run([cmake, "--build", "build", "--target", "good"], cc_project)
    assert good.returncode == 0, good.stdout + good.stderr
    assert subprocess.run([str(next((cc_project / "build").glob("good*")))], check=False).returncode == 0
    bad = run([cmake, "--build", "build", "--target", "bad"], cc_project)
    output = bad.stdout + bad.stderr
    assert bad.returncode != 0
    missing = {flag for flag in BAD_CC_GCC if flag not in output}
    assert not missing, f"missing: {sorted(missing)}\n{output}"


GUARDED_H = """\
#ifndef DEMO_SCALE_H_
#define DEMO_SCALE_H_

namespace demo {

[[nodiscard]] float Scale(float value);

}  // namespace demo

#endif  // DEMO_SCALE_H_
"""

GUARDED_CC = """\
#include "demo/scale.h"

namespace demo {

float Scale(float value) { return value * 0.5f; }

}  // namespace demo
"""

STATIC_AND_MOVE_CC = """\
#include <map>
#include <string>
#include <utility>

namespace {

std::map<std::string, int> registry;

class Buffer {
 public:
  Buffer() = default;
  Buffer(const Buffer&) = default;
  Buffer& operator=(const Buffer&) = default;
  Buffer(Buffer&& other) : name_(std::move(other.name_)) {}
  Buffer& operator=(Buffer&&) = default;
  ~Buffer() = default;

 private:
  std::string name_;
};

}  // namespace

int main() { return static_cast<int>(registry.size()); }
"""


def test_clang_tidy_accepts_google_guards_and_float_suffix(cc_project):
    (cc_project / "demo").mkdir()
    (cc_project / "demo/scale.h").write_text(GUARDED_H, encoding="utf-8")
    (cc_project / "scale.cc").write_text(GUARDED_CC, encoding="utf-8")
    result = run([tool("clang-tidy"), "scale.cc", "--", "-std=c++20", "-I.", "-fno-exceptions", "-fno-rtti"],
                 cc_project)
    assert result.returncode == 0, result.stdout


def test_clang_tidy_flags_dynamic_globals_and_throwing_moves_under_no_exceptions(cc_project):
    (cc_project / "bad2.cc").write_text(STATIC_AND_MOVE_CC, encoding="utf-8")
    result = run([tool("clang-tidy"), "bad2.cc", "--", "-std=c++20", "-fno-exceptions", "-fno-rtti"], cc_project)
    for check in ("clang-diagnostic-exit-time-destructors", "clang-diagnostic-global-constructors",
                  "performance-noexcept-move-constructor"):
        assert check in result.stdout, f"{check} did not fire:\n{result.stdout}"
