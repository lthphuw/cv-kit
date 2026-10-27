# Go tests: go test, test first

`go test` is the runner for every Go module. Take the project's existing layout, build tags and CI commands first. The
rules this follows are in `rules/go-tests.md` and the catalogue `shared/go-style.md`.

## The loop

- **Bug fix:** write a test that reproduces the bug and watch it fail for the right reason. Make the minimal fix. Run the
  package, then the module.
- **New feature:** write tests for the use cases, the edge cases and the invalid input, including a device that stops
  answering. Implement. Refactor with the tests green.
- **Refactor:** pin the current behaviour first (`refactor.md`).

## Writing tests

- Table-driven cases use `t.Run`. Each subtest runs on its own, so `go test -run 'TestName/case'` runs one case. Name
  subtests like identifiers, and print the inputs on failure.
- A helper that takes `*testing.T` calls `t.Helper()` first and takes `ctx` before `t`. Register teardown with
  `t.Cleanup` in the helper that creates the resource. Use `t.Context()` on Go 1.24 or newer.
- Failure messages read `Func(input) = got, want want`. Compare whole values with `cmp.Diff` in tests only.
- Never call `t.Fatal`, `t.FailNow` or `t.SkipNow` from a goroutine the test started. Send the result back and fail in
  the test goroutine.
- Concurrent code: a package that starts goroutines gets `TestMain` with `goleak.VerifyTestMain(m)`, or an equivalent
  check; each component gets a shutdown test with its own timeout. Do not `time.Sleep` to wait for a goroutine; wait on
  a channel or a `sync.WaitGroup`. On Go 1.25 or newer, `testing/synctest` makes timer tests fast and stable.

## Commands

```
go test ./path/to/pkg -run 'TestName/case' -v   # one case
go test ./... -count=1                          # whole module, no test cache
go test -race ./...                             # before a commit that touches shared state or goroutines
go test -timeout 120s ./...                     # bound a hung test
go vet ./...                                    # static checks
gofmt -l .                                      # must print nothing
```

Use the command the project's CI runs when it differs. Pin the Go version in `go.mod`. The race detector needs cgo and
a C compiler, so run `-race` on the build host, not on the device.
