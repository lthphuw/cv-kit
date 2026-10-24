#!/usr/bin/env bash
# A C++ frame pipeline: the grabber takes the pool lock then the queue lock, the inference thread takes them in the
# opposite order, and a buffer pool shared by two cameras makes the two paths meet.
set -euo pipefail
mkdir -p src/pipeline tests
cat > CMakeLists.txt <<'EOF'
cmake_minimum_required(VERSION 3.20)
project(pipeline LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
find_package(Threads REQUIRED)
add_executable(pipeline src/pipeline/main.cc src/pipeline/grabber.cc src/pipeline/inference.cc)
target_link_libraries(pipeline PRIVATE Threads::Threads)
EOF
cat > src/pipeline/buffer_pool.h <<'EOF'
#pragma once
#include <cstdint>
#include <mutex>
#include <vector>

// Fixed set of frame buffers shared by every camera.
class BufferPool {
 public:
  explicit BufferPool(int count) {
    for (int i = 0; i < count; ++i) free_.push_back(new uint8_t[1920 * 1080 * 3]);
  }
  // The caller must hold mutex().
  uint8_t* AcquireLocked() {
    if (free_.empty()) return nullptr;
    uint8_t* buffer = free_.back();
    free_.pop_back();
    return buffer;
  }
  void Release(uint8_t* buffer) {
    std::lock_guard<std::mutex> lock(mu_);
    free_.push_back(buffer);
  }
  std::mutex& mutex() { return mu_; }

 private:
  std::mutex mu_;
  std::vector<uint8_t*> free_;
};
EOF
cat > src/pipeline/frame_queue.h <<'EOF'
#pragma once
#include <condition_variable>
#include <cstdint>
#include <deque>
#include <mutex>

class FrameQueue {
 public:
  void Push(uint8_t* frame) {
    std::lock_guard<std::mutex> lock(mu_);
    frames_.push_back(frame);
    ready_.notify_one();
  }
  // Blocks until a frame is available.
  uint8_t* Pop() {
    std::unique_lock<std::mutex> lock(mu_);
    ready_.wait(lock, [this] { return !frames_.empty(); });
    uint8_t* frame = frames_.front();
    frames_.pop_front();
    return frame;
  }
  std::mutex& mutex() { return mu_; }

 private:
  std::mutex mu_;
  std::condition_variable ready_;
  std::deque<uint8_t*> frames_;
};
EOF
cat > src/pipeline/grabber.h <<'EOF'
#pragma once
#include "pipeline/buffer_pool.h"
#include "pipeline/frame_queue.h"

void RunGrabber(int camera_id, BufferPool& pool, FrameQueue& queue);
EOF
cat > src/pipeline/grabber.cc <<'EOF'
#include "pipeline/grabber.h"

#include <chrono>
#include <thread>

void RunGrabber(int camera_id, BufferPool& pool, FrameQueue& queue) {
  (void)camera_id;
  for (;;) {
    {
      // Hold the pool lock while handing the frame to the queue so the buffer cannot be taken by another camera.
      std::lock_guard<std::mutex> pool_lock(pool.mutex());
      uint8_t* buffer = pool.AcquireLocked();
      if (buffer != nullptr) queue.Push(buffer);
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(33));
  }
}
EOF
cat > src/pipeline/inference.h <<'EOF'
#pragma once
#include "pipeline/buffer_pool.h"
#include "pipeline/frame_queue.h"

void RunInference(BufferPool& pool, FrameQueue& queue);
EOF
cat > src/pipeline/inference.cc <<'EOF'
#include "pipeline/inference.h"

void RunInference(BufferPool& pool, FrameQueue& queue) {
  for (;;) {
    uint8_t* frame = queue.Pop();
    // Run the detector on `frame` here, then give the buffer back.
    std::lock_guard<std::mutex> queue_lock(queue.mutex());
    pool.Release(frame);
  }
}
EOF
cat > src/pipeline/main.cc <<'EOF'
#include <thread>

#include "pipeline/buffer_pool.h"
#include "pipeline/frame_queue.h"
#include "pipeline/grabber.h"
#include "pipeline/inference.h"

int main() {
  BufferPool pool(8);
  FrameQueue queue;
  std::thread cam0(RunGrabber, 0, std::ref(pool), std::ref(queue));
  std::thread cam1(RunGrabber, 1, std::ref(pool), std::ref(queue));
  std::thread infer(RunInference, std::ref(pool), std::ref(queue));
  cam0.join();
  cam1.join();
  infer.join();
}
EOF
