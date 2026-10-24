---
description: A review request for edge C++ code goes to review, and the first reply cites rule IDs with severities.
expected_outcome: review fires; develop does not; findings carry a severity and a CPP- rule ID.
tags: [trigger, fire, behaviour]
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill]
---

Can you review this before I merge it? It is the frame grabber for our Jetson Orin build (we compile with -fno-exceptions).

```cpp
class FrameGrabber {
 public:
  FrameGrabber(std::string device) {
    fd = open(device.c_str(), O_RDWR);
    if (fd < 0) throw std::runtime_error("cannot open " + device);
  }
  void Start() {
    std::thread([this] { Loop(); }).detach();
  }
 private:
  void Loop() {
    while (running) {
      auto* frame = new uint8_t[1920 * 1080 * 3];
      Read(frame);
      queue.push_back(frame);
    }
  }
  int fd;
  bool running = true;
  std::vector<uint8_t*> queue;
};
```
