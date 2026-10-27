---
paths:
  - "**/*_test.go"
---
# Go tests

Follow these when writing or editing Go tests. The IDs refer to cv-kit's full Go catalogue (`shared/go-style.md`).
The suite is run with the standard `go test`; the test reference is `skills/develop/references/go-testing.md` in the
cv-kit plugin.

- Write the failing test first and watch it fail for the right reason (GO-TEST-1).
- Table-driven cases use `t.Run`. Each subtest runs on its own and is named like an identifier. Print the inputs on
  failure, not a row index (GO-TEST-2, GO-TEST-3, GO-TEST-4).
- Helpers call `t.Helper()` first and take `ctx` before `t` (GO-TEST-7, GO-TEST-8). Never call `t.Fatal`,
  `t.FailNow` or `t.SkipNow` from a goroutine the test started; send the result back (GO-TEST-9).
- Report each mismatch with `t.Error`, and use `t.Fatal` only when later checks would be meaningless (GO-TEST-10).
- Failure messages read `Func(input) = got, want want`, quote strings with `%q`, and compare whole values with a
  deep diff (GO-TEST-11 to GO-TEST-13).
- Never compare error text to decide what happened; use `errors.Is` or `errors.As` (GO-TEST-16).
- Register fake and listener teardown with `t.Cleanup`. Use `t.Context()` on Go 1.24 or newer (GO-TEST-17,
  GO-TEST-18).
- A package that starts goroutines runs a leak check: `goleak.VerifyTestMain(m)`, or an equivalent. Every goleak
  ignore has a comment naming its owner (GO-TEST-26, GO-TEST-28). A clean run is not proof of no leak; test that
  connections close and queues stay bounded (GO-TEST-29).
- Every concurrent component has a shutdown test with its own timeout (GO-TEST-24).
- Run `go test -race ./...` for any change that touches shared state, goroutines or channels. A test must really run
  the concurrent paths, not a sequential stand-in (GO-TEST-30, GO-TEST-31).
- Never `time.Sleep` to wait for another goroutine. Wait on a channel or a `WaitGroup`, or use `testing/synctest` on
  Go 1.25 or newer (GO-TEST-33, GO-TEST-34).
- Each test is independent of the others and restores the global state it changed (GO-TEST-23).
- Keep test-only imports out of production code; do not use `go-cmp` outside tests (GO-TEST-15).
