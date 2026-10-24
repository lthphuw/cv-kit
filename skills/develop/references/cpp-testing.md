# C++ tests: GoogleTest, test first

GoogleTest (`google/googletest`) is the default for every C++ project. The rules follow its `docs/primer.md`,
`docs/advanced.md` and `docs/quickstart-cmake.md`, read at commit `cd8e73f` (release line 1.18.0). It needs C++17 or later.

## The loop

Write the test, build, watch it fail for the right reason, write the least code that passes, then refactor with the
tests green. A bug gets a test that reproduces it first. Every new or changed error return gets a test that forces
it (CPP-ERR-21 in the style catalogue). Pin behaviour before a refactor (`refactor.md`).

## Writing tests

- `TEST(SuiteName, TestName)` for a stand-alone test, `TEST_F(FixtureName, TestName)` when tests share setup.
  A fixture derives from `::testing::Test`, builds state in the constructor or `SetUp()`, and cleans up in
  `TearDown()`. Suite and test names contain no underscores (GoogleTest reserves them); the suite names the unit, the test the behaviour.
- Prefer `EXPECT_*`: a failure is reported and the test goes on. Use `ASSERT_*` only when going on makes no sense
  (a null pointer or empty result you are about to read); it returns from the current function, so it cannot sit
  in a helper that returns a value, and it skips cleanup after it.
- Stream context into an assertion (`EXPECT_EQ(a[i], b[i]) << "index " << i`) instead of looping silently.
- Floating point: `EXPECT_NEAR(x, y, tol)` or `EXPECT_FLOAT_EQ`, never `==`; state the tolerance.
- Runtime skip: `GTEST_SKIP() << "reason"`. Do not use `DISABLED_` to hide a failing test.
- Value-parameterised tests (`TEST_P`, `INSTANTIATE_TEST_SUITE_P`) replace loops over cases.
- Test code in strict edge projects is built without exceptions: use `EXPECT_DEATH` for a check macro that aborts,
  and assert on the returned status for every error path. Keep sanitizer builds (`CV_KIT_SANITIZE`, `CV_KIT_TSAN`)
  in the loop for code with memory or threads.
- A test is deterministic: seed any random input, use no sleeps to wait for threads, no network, no real camera or
  accelerator. Fake the device behind the project's interface.

## CMake

```cmake
include(FetchContent)
FetchContent_Declare(googletest
  URL https://github.com/google/googletest/archive/<full commit sha>.zip)   # pin a commit, not a branch
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

enable_testing()
add_executable(foo_test foo_test.cc)
target_link_libraries(foo_test PRIVATE foo GTest::gtest_main)
include(GoogleTest)
gtest_discover_tests(foo_test)
```

Run with `cmake -S . -B build && cmake --build build && ctest --test-dir build --output-on-failure`. Give the
test target the project's warning flags.
