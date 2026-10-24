#!/usr/bin/env bash
# A C++ detector project where the NMS threshold is read from configs/det.yaml in one place and used in two.
set -euo pipefail
mkdir -p configs src/config src/post src/detector
cat > configs/det.yaml <<'EOF'
model:
  input_size: 640
postprocess:
  nms_iou_threshold: 0.45
  score_threshold: 0.25
EOF
cat > src/config/config.h <<'EOF'
#pragma once
#include <string>

struct PostprocessConfig {
  float nms_iou_threshold = 0.5f;
  float score_threshold = 0.3f;
};

PostprocessConfig LoadPostprocessConfig(const std::string& path);
EOF
cat > src/config/config.cc <<'EOF'
#include "config/config.h"

#include <yaml-cpp/yaml.h>

PostprocessConfig LoadPostprocessConfig(const std::string& path) {
  PostprocessConfig cfg;
  const YAML::Node root = YAML::LoadFile(path);
  const YAML::Node post = root["postprocess"];
  if (post["nms_iou_threshold"]) cfg.nms_iou_threshold = post["nms_iou_threshold"].as<float>();
  if (post["score_threshold"]) cfg.score_threshold = post["score_threshold"].as<float>();
  return cfg;
}
EOF
cat > src/post/nms.h <<'EOF'
#pragma once
#include <vector>

struct Box {
  float x1, y1, x2, y2;
};

std::vector<int> Nms(const std::vector<Box>& boxes, const std::vector<float>& scores, float iou_threshold);
EOF
cat > src/post/nms.cc <<'EOF'
#include "post/nms.h"

std::vector<int> Nms(const std::vector<Box>& boxes, const std::vector<float>& scores, float iou_threshold) {
  (void)boxes;
  (void)scores;
  (void)iou_threshold;
  return {};
}
EOF
cat > src/detector/detector.h <<'EOF'
#pragma once
#include <vector>

#include "config/config.h"
#include "post/nms.h"

class Detector {
 public:
  explicit Detector(const std::string& config_path) : cfg_(LoadPostprocessConfig(config_path)) {}
  std::vector<int> Postprocess(const std::vector<Box>& boxes, const std::vector<float>& scores) const;

 private:
  PostprocessConfig cfg_;
};
EOF
cat > src/detector/detector.cc <<'EOF'
#include "detector/detector.h"

std::vector<int> Detector::Postprocess(const std::vector<Box>& boxes, const std::vector<float>& scores) const {
  return Nms(boxes, scores, cfg_.nms_iou_threshold);
}
EOF
cat > src/detector/benchmark.cc <<'EOF'
#include "detector/detector.h"

int main() {
  Detector detector("configs/det.yaml");
  PostprocessConfig cfg = LoadPostprocessConfig("configs/det.yaml");
  std::vector<Box> boxes(100, Box{0, 0, 10, 10});
  std::vector<float> scores(100, cfg.score_threshold);
  detector.Postprocess(boxes, scores);
  return Nms(boxes, scores, cfg.nms_iou_threshold).empty() ? 0 : 1;
}
EOF
