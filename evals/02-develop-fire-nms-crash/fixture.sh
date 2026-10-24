#!/usr/bin/env bash
# A small C++ project: NMS reads the best score before it checks that there is one, so zero detections crash it.
set -euo pipefail
mkdir -p src/post tests
cat > CMakeLists.txt <<'EOF'
cmake_minimum_required(VERSION 3.20)
project(detector LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)

add_library(post src/post/nms.cc)
target_include_directories(post PUBLIC src)

include(FetchContent)
FetchContent_Declare(googletest URL https://github.com/google/googletest/archive/refs/tags/v1.15.2.zip)
FetchContent_MakeAvailable(googletest)

enable_testing()
add_executable(nms_test tests/nms_test.cc)
target_link_libraries(nms_test PRIVATE post GTest::gtest_main)
include(GoogleTest)
gtest_discover_tests(nms_test)
EOF
cat > src/post/nms.h <<'EOF'
#pragma once
#include <vector>

struct Box {
  float x1, y1, x2, y2;
};

// Returns the indices of the boxes to keep, highest score first.
std::vector<int> Nms(const std::vector<Box>& boxes, const std::vector<float>& scores, float iou_threshold,
                     float score_threshold);
EOF
cat > src/post/nms.cc <<'EOF'
#include "post/nms.h"

#include <algorithm>
#include <numeric>

namespace {

float Iou(const Box& a, const Box& b) {
  const float w = std::max(0.0f, std::min(a.x2, b.x2) - std::max(a.x1, b.x1));
  const float h = std::max(0.0f, std::min(a.y2, b.y2) - std::max(a.y1, b.y1));
  const float inter = w * h;
  const float area_a = (a.x2 - a.x1) * (a.y2 - a.y1);
  const float area_b = (b.x2 - b.x1) * (b.y2 - b.y1);
  return inter / (area_a + area_b - inter);
}

}  // namespace

std::vector<int> Nms(const std::vector<Box>& boxes, const std::vector<float>& scores, float iou_threshold,
                     float score_threshold) {
  std::vector<int> order(boxes.size());
  std::iota(order.begin(), order.end(), 0);
  std::sort(order.begin(), order.end(), [&](int a, int b) { return scores[a] > scores[b]; });

  // Nothing can pass if even the best score is under the threshold.
  if (scores[order.front()] < score_threshold) return {};

  std::vector<int> keep;
  std::vector<bool> suppressed(boxes.size(), false);
  for (int i : order) {
    if (suppressed[i] || scores[i] < score_threshold) continue;
    keep.push_back(i);
    for (int j : order) {
      if (!suppressed[j] && j != i && Iou(boxes[i], boxes[j]) > iou_threshold) suppressed[j] = true;
    }
  }
  return keep;
}
EOF
cat > tests/nms_test.cc <<'EOF'
#include "post/nms.h"

#include <gtest/gtest.h>

TEST(Nms, KeepsTheBetterOfTwoOverlappingBoxes) {
  std::vector<Box> boxes = {{0, 0, 10, 10}, {1, 1, 10, 10}};
  std::vector<float> scores = {0.6f, 0.9f};
  EXPECT_EQ(Nms(boxes, scores, 0.5f, 0.1f), std::vector<int>({1}));
}

TEST(Nms, KeepsDisjointBoxes) {
  std::vector<Box> boxes = {{0, 0, 5, 5}, {20, 20, 30, 30}};
  std::vector<float> scores = {0.7f, 0.8f};
  EXPECT_EQ(Nms(boxes, scores, 0.5f, 0.1f), std::vector<int>({1, 0}));
}
EOF
