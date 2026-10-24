---
paths:
  - "**/*_test.{cc,cpp,cxx}"
  - "**/*_tests.{cc,cpp,cxx}"
  - "**/test/**/*.{cc,cpp,cxx,h,hpp}"
  - "**/tests/**/*.{cc,cpp,cxx,h,hpp}"
---
# C++ tests (GoogleTest)

Follow these when writing or editing C++ tests. They come from google/googletest's primer and advanced guide; the full guide is `skills/develop/references/cpp-testing.md` in the cv-kit plugin.

- Write the failing test first and watch it fail. Every new or changed error return gets a test that forces it.
- `TEST(Suite, Name)` for a stand-alone test, `TEST_F(Fixture, Name)` for shared setup. No underscores in suite or test names.
- Prefer `EXPECT_*`; use `ASSERT_*` only when going on is pointless, and never in a helper that returns a value.
- Floats: `EXPECT_NEAR` or `EXPECT_FLOAT_EQ` with a stated tolerance. Value-parameterised tests (`TEST_P`) instead of loops. `GTEST_SKIP()` for a runtime skip; never `DISABLED_` to hide a failure.
- Deterministic: seed random input, no sleeps to wait for threads, no network, no real device behind the test.
- Build with CMake `FetchContent` pinned to a commit, link `GTest::gtest_main`, register with `gtest_discover_tests`, run `ctest --output-on-failure`.
