---
paths:
  - "**/*.go"
---
# Go

Follow these rules when writing or editing Go. The IDs refer to cv-kit's full Go catalogue (`shared/go-style.md`). The
code runs as a long-lived service that drives hardware, so a leaked goroutine or an unbounded buffer is a field
failure. Target Go 1.22 or later, and check the `go` line in `go.mod` before relying on a newer behaviour. Where the
project has its own written rule, that rule wins. Concurrency and device I/O: `rules/go-concurrency.md`. Tests:
`rules/go-tests.md`.

## Tooling and names

- Every file is `gofmt` output, and `go vet ./...` is clean. Never suppress a `copylocks`, `lostcancel` or `printf`
  finding. A suppression names the check and gives its reason on the same line (GO-TOOL-1, GO-TOOL-2, GO-TOOL-4).
- MixedCaps names with no underscores. Constants have no `k` prefix and no ALL_CAPS. Initialisms keep one case: `URL`,
  `ID`, `db` (GO-NAME-1, GO-NAME-2, GO-NAME-8).
- Package names are short and lowercase. Never `util`, `common`, `helper` or `misc` (GO-NAME-4, GO-NAME-5).
- Receivers are one or two letters, the same on every method, never `this` or `self` (GO-NAME-7).
- Every exported name has a doc comment that is a full sentence starting with its name. A package has one package
  comment (GO-DOC-1, GO-DOC-2).
- Document any cleanup the caller must do, thread-safety when it is not obvious, and the shutdown contract of a
  long-lived type (GO-DOC-4, GO-DOC-5).

## Imports and packages

- Rename an import only to resolve a collision. Group standard library, then other modules, then side-effect imports
  (GO-IMP-1, GO-IMP-2).
- No blank (`_`) or dot imports outside `main`, tests and `embed` (GO-IMP-3, GO-IMP-4).

## Errors and failure

- Failure is an `error`, returned last. Never signal failure with `-1`, `""` or `nil`, and never return a value beside a
  non-nil error unless the function documents it (GO-ERR-1, GO-ERR-2, GO-ERR-9).
- Exported functions return `error`, never a concrete error type. A function that takes a context returns an error
  (GO-ERR-3, GO-ERR-4). Error strings start lowercase and end without punctuation (GO-ERR-5).
- Never discard an error with `_` unless it is handled, returned, or justified in a comment (GO-ERR-6, GO-ERR-7).
- Log an error or return it, never both (GO-ERR-8). Handle the error first and return; no `else` after a return
  (GO-ERR-10).
- Errors that callers must tell apart have an identity; tests assert the identity, not the text. Test wrapped errors
  with `errors.Is` or `errors.As`. Wrap with `%w` only when callers should inspect the cause (GO-ERR-11, GO-ERR-12,
  GO-ERR-15).
- At the hardware boundary, translate driver errors into the service's own errors: offline, timeout, rejected
  (GO-ERR-16).
- Library code never panics or exits on a per-device or transient failure. Panic only for a broken invariant in
  this code (GO-ERR-17, GO-ERR-18). `Must...` helpers never take runtime input (GO-ERR-19).
- A repeating device failure is logged once per change of state, or rate-limited (GO-ERR-24). Never log personal or
  biometric data (GO-ERR-25).
- `log.Fatal`, `log.Panic` and `os.Exit` appear only in `main`, because they skip deferred cleanup (GO-ERR-26).

## Language, values and functions

- A method that changes its receiver has a pointer receiver. Never copy a value whose methods are on its pointer
  (GO-LANG-1, GO-LANG-2). Name the fields of a literal of a struct from another package (GO-LANG-6).
- Never end a `switch` clause with an unlabelled `break` (GO-LANG-8).
- A goroutine or closure captures a loop variable only in a file whose Go version is 1.22 or newer. Otherwise pass a
  copy as an argument (GO-LANG-9).
- Use `any` in new code, `%q` for strings in messages, and generics only for a real need (GO-LANG-11 to GO-LANG-13).
- `var s []T` for an empty local slice. Never make callers tell a nil slice from an empty one (GO-VAR-1, GO-VAR-2).
- Initialise every map with `make` or a literal before its first write (GO-VAR-3).
- Never use `:=` in an inner block to shadow a variable that the code after the block must see, such as a `ctx` that
  carries a deadline (GO-VAR-5).
- Name a result only when two share a type, a caller must act on one, or a deferred call changes it. Naked returns only
  in small functions (GO-FN-1, GO-FN-2). Many optional inputs go in an options struct; a context never does
  (GO-FN-3, GO-FN-4).
- Accept interfaces and return concrete types. Add an interface only for a real need, keep it small, and define it in
  the consuming package (GO-IFACE-1 to GO-IFACE-4).
- No behaviour-controlling package-level state, and no lazily built client singletons (GO-STATE-1). No I/O, failing work
  or goroutine starts in `init()` (GO-STATE-3).

## Resources and memory

- Release every resource with `defer` on the line after acquiring it: file, connection, port, lock, timer, ticker, cancel
  function, response body (GO-RES-1). Check the acquiring call's error before deferring its close (GO-RES-2). Check the
  error from `Close` on a writer (GO-RES-3).
- Close every HTTP response body and read it to EOF (GO-RES-4). Build one `http.Client` per process (GO-RES-5).
- Never `http.Get`, `http.Post` or `http.DefaultClient` for devices or remote services. Set `Timeout`, or give every
  request a deadline (GO-RES-6). Set the timeouts on every `http.Server` (GO-RES-7).
- A goroutine that outlives a handler never uses `r.Context()` (GO-RES-8).
- Copy a small slice out of a large buffer that you keep (GO-RES-9). Put pointers into a `sync.Pool` (GO-RES-10).
- A function that hands the caller something to release names it and says the caller must call it (GO-RES-13).
- No binary built with `-race` ships as the service (GO-RES-12).
