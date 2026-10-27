# 09 - Go style and concurrency: what cv-kit took, and from where

Date: 2026-10-27. Input for the Go rules: `rules/go-style.md`, `rules/go-concurrency.md`, `rules/go-tests.md`, the full
catalogue `shared/go-style.md`, and the reference `skills/develop/references/go-testing.md`. The folder with clones,
notes and probes is outside this repository (`<refs>/`); it is not published.

## The request, and what it produced

The user asked for Go rules like the Python and C++ ones, based on the Google Go style decisions, and for deeper rules on
goroutines and concurrency, because a Go service that drives a time-attendance terminal must not block, leak
goroutines, or leak memory. The catalogue has 238 rules in 15 areas. The concurrency and device-I/O rules sit in
`GO-CONC` (66 rules) and `GO-EDGE` (15 rules). Each rule carries a source label, and the sources are listed below.

Wiring that a Go project needs: the evidence gate treats `.go` edits as code (`hooks/evidence_gate.py`), so an edit
needs a passing `go test` before the turn ends. `scripts/project_facts.py` reports Go and its tests. The develop skill,
the engineer and reviewer agents, and the setup skill name the Go references. The installer copies every
`rules/*.md`, so the Go rules install with `/cv-kit:setup`; no Go lint config is shipped.

## The resources

| Resource | Where it was read | Revision | Licence | What cv-kit took |
|---|---|---|---|---|
| Google Go Style Guide: `go/guide.md`, `go/decisions.md`, `go/best-practices.md` | `<refs>/google-styleguide` | `2ac1584cd3c9854760f02418ec24687ec1698fb8` (2026-10-21) | CC BY 3.0 for the guides; Apache 2.0 for code samples (`README.md`, "Licensing") | Paraphrased rules for GO-NAME, GO-DOC, GO-IMP, GO-ERR, GO-LANG, GO-VAR, GO-FN, GO-IFACE, GO-STATE, GO-LIB, and the Google parts of GO-CONC and GO-TEST. Attribution: "Google Go Style Guide". |
| Effective Go, `go.dev/doc/effective_go` | `<refs>/golang-website` (`_content/doc/effective_go.html`) | `b8d34bbe2d9e230cc70ce3e4272dc651f494a188` | CC BY 4.0 for site content (`_content/copyright.md`) | Goroutine, channel, semaphore, worker-pool and reply-channel patterns (GO-CONC-10 to GO-CONC-17, GO-CONC-29, GO-RES-11). The examples that leak were corrected, not copied. |
| The Go Memory Model, `go.dev/ref/mem` | `<refs>/golang-go` (`doc/go_mem.html`) | `6c49ac311e5642fa5399b46c736295a9dc4eeec9` | BSD-3-Clause (repository `LICENSE`) | Happens-before and data-race rules (GO-CONC-1, GO-CONC-26, GO-CONC-37 to GO-CONC-44, GO-TEST-34). |
| The Go Programming Language Specification | `<refs>/golang-go` (`doc/go_spec.html`) and Go 1.22.2 (`doc/go_spec.html` in the package) | as above | BSD-3-Clause | Panic, close, send, receive and nil-channel behaviour (GO-CONC-18, GO-CONC-19, GO-CONC-22, GO-CONC-23, GO-CONC-10). |
| Data Race Detector article, `go.dev/doc/articles/race_detector` | `<refs>/golang-website` | `b8d34bbe2d9e230cc70ce3e4272dc651f494a188` | CC BY 4.0 | Race patterns and the overhead of `-race` (GO-CONC-38, GO-CONC-45, GO-TEST-30 to GO-TEST-32, GO-RES-12). |
| Go release notes, `go.dev/doc/go1.21` to `go1.25` | `<refs>/golang-website` (`_content/doc/go1.2x.md`) and `go.dev/doc/go1.22`, `go1.23`, `go1.24`, `go1.25` via WebFetch | as above | CC BY 4.0 | Loop variables (1.22), timer and ticker channels (1.23, gated by the `go` line), `t.Context` (1.24), `testing/synctest` and `WaitGroup.Go` (1.25). |
| Go standard library doc comments and source, Go 1.22.2 | `<refs>/toolchain/root/usr/lib/go-1.22/src` (Ubuntu package `golang-1.22-src`) | 1.22.2-2ubuntu0.5 | BSD-3-Clause | `context`, `sync`, `net`, `net/http`, `time`, `os/signal`, `log`, `os`, `sync/atomic`, `runtime` panic text, `cmd/compile` loop-variable gate. |
| `go vet` analyzers | `go tool vet help` in Go 1.22.2 | 1.22.2 | BSD-3-Clause | The analyzer names in every `vet` Check field. `waitgroup` is Go 1.25 (release notes), so it is not in 1.22. |
| staticcheck checks, `staticcheck.dev/docs/checks/` | WebFetch | read 2026-10-27 | licence not checked: facts only, no text copied | The SA, S and ST codes in Check fields. The ST codes, and ST1000 and ST1003, are non-default. |
| uber-go/guide | `<refs>/uber-go-guide` | `1d60a91aa5e87d443002e23c21903c49489dbde5` | **Apache-2.0** (`LICENSE`); the brief assumed MIT, which was wrong | Paraphrased with attribution: "Uber Go Style Guide, Apache-2.0". Goroutine ownership, defer, mutex, channel size, time and container-copy rules. |
| uber-go/goleak | `<refs>/goleak` | `b656bfda2fbf4f4964e1d9349840a72169224d88` | MIT (`LICENSE`) | Goroutine leak check in tests (GO-TEST-26 to GO-TEST-29). Used as a test-only dependency; the rule accepts an equivalent check. |
| Go Blog, "Go Concurrency Patterns: Pipelines and cancellation", `go.dev/blog/pipelines` | WebFetch | fetched 2026-10-27 | CC BY 4.0 (`go.dev/copyright`); the page carries no notice of its own | Fan-out, fan-in, bounded parallelism, explicit cancellation (GO-CONC-11, GO-CONC-15, GO-CONC-18, GO-CONC-20, GO-CONC-27). |
| Go Blog, "Go Concurrency Patterns: Context", `go.dev/blog/context` | WebFetch | fetched 2026-10-27 | CC BY 4.0 | Derived contexts, cancel functions, context keys (GO-CONC-50, GO-CONC-52). |
| errgroup, `golang.org/x/sync/errgroup` | pkg.go.dev, v0.24.0 | v0.24.0 | BSD-3-Clause | `WithContext`, `Wait`, `SetLimit` (GO-CONC-11, GO-CONC-59 to GO-CONC-61). |
| Dave Cheney, "Never start a goroutine without knowing how it will stop" | WebFetch | 2016 post | CC BY-NC-SA 4.0 (footer) | **Ideas only**; no wording used. The non-commercial and share-alike terms do not fit a MIT plugin. |
| Sameer Ajmani, "Advanced Go Concurrency Patterns" (slides) | WebFetch of `go.dev/talks/2013/advconc.slide` | slides | no licence shown | **Ideas only**: owner goroutines instead of locks, nil channels to disable a case, bounded queues. |

Not used: the obsolete `golang/blog` repository (its README says the content moved to `golang/website`).

## How they were read

Seven reader agents worked in parallel, each on a disjoint scope, and each wrote a candidate note outside the repository.
The notes list every candidate with its source line range, its strength and its severity.

| Note | Scope | Candidates |
|---|---|---|
| `go-g1-guide-naming-errors.md` | `guide.md`; `decisions.md` 1 to 1240 | 56 |
| `go-g2-language.md` | `decisions.md` 1235 to 2600 | 48 |
| `go-g3-libraries-tests.md` | `decisions.md` 2600 to 3883 | 31 |
| `go-g4-best-practices-a.md` | `best-practices.md` 1 to 2000 | 55 |
| `go-g5-best-practices-b.md` | `best-practices.md` 2000 to 3992 | 33 |
| `go-c1-language-concurrency.md` | Memory Model, Spec, Effective Go, race article, release notes, `context`, `sync`, `net/http`, `time` | 61 |
| `go-c2-community-tools.md` | uber-go/guide, goleak, Go blog, staticcheck, errgroup, vet | 60 |

The candidate notes overlapped. The catalogue merges them, keeps the strongest supported strength, and drops items that
were Google-internal or tool-only (listed under "Not adopted" in the catalogue). The Google readers flagged analyzer and
staticcheck names from memory; those names were checked afterwards (below).

## What was verified, and how

- **Analyzer names.** `go tool vet help` in Go 1.22.2 lists `copylocks`, `lostcancel`, `composites`,
  `testinggoroutine`, `loopclosure`, `printf`, `errorsas`, `atomic`, `unmarshal` and `httpresponse`. It does not list
  `shadow` or `nilness`, so the catalogue says the shadow check is not in the default `go vet`.
- **Staticcheck codes.** All codes in the catalogue were checked on the checks page (2026-10-27). The page marks ST1000,
  ST1003, ST1016 and ST1020 to ST1022 as non-default.
- **Compiler behaviour.** `cmd/compile/internal/noder/writer.go` (`distinctVars`, Go 1.22.2) gates the per-iteration
  loop variables on the file's Go version. The rule uses the `go` line in `go.mod`.
- **Probes** (Go 1.22.2, outside the repository, in `<refs>/samples/`):
  - `loop121`: a goroutine captures a loop variable in a `go 1.21` module, and prints `[3 3 3]`.
  - `loop122`: the same program in a `go 1.22` module prints `[0 1 2]`. This confirms GO-LANG-9.
  - `bad`: `go vet` reports `copylocks` for a mutex passed by value and `lostcancel` for a discarded cancel function.
    This confirms GO-CONC-34 and GO-CONC-50.
  - `runtime` (`go test -race`, six tests, all pass): a nil-map write panics; a send on a closed channel panics; a second
    `close` panics; a bare `break` inside `select` leaves only the `select`; a labelled `break` exits the loop; a nil
    channel is never ready. This confirms GO-VAR-3, GO-CONC-19, GO-CONC-24 and GO-CONC-23.
- **Spec on panics.** The "Handling panics" section says that a panic which is not recovered on the goroutine's stack
  terminates the program. This settles the open question in the reader notes: one goroutine's unrecovered panic ends
  the whole service. It is why GO-CONC-10 requires each long-lived goroutine to recover at its own top.
- **Release notes.** The `go1.23` timer rule (the new behaviour applies only when the main module's `go` line is 1.23.0
  or later; `len` and `cap` of a timer channel are 0) was confirmed with WebFetch.
- **Standard library.** The stdlib facts used (the context does not wait; a zero `Client.Timeout` means none; the body
  must be read to EOF and closed for reuse; `Ticker.Stop` does not close the channel; `os.Exit` skips deferred calls;
  `log.Fatal` calls `os.Exit(1)`) were read in the Go 1.22.2 source.
- **Test suite.** `tests/test_go_rules.py` checks that the catalogue is well formed, that IDs are unique and numbered
  without gaps, that every entry has its fields and a valid severity, and that every ID the summaries and the reference
  cite exists.

## Not verified

- **No Go toolchain newer than 1.22.2 was run.** Behaviour from Go 1.23 to 1.25 (timer channels, `WaitGroup.Go`,
  `testing/synctest`, `T.Context`) rests on the release notes and the stdlib documentation, not on a run. The
  signatures of `WaitGroup.Go` and `synctest` were not read from source; check them on pkg.go.dev for the project's
  version before writing code against them.
- **The Go code in the rules was not compiled.** The catalogue quotes API names and short phrases only; the probes above
  are the only Go code that was built and run.
- **Staticcheck's licence was not checked.** The codes and titles are facts; no text was copied.
- **The go.dev blog pages were read through WebFetch summaries**, not raw text. The rules use only the general patterns
  they describe. Re-read the pages before quoting them.
- **Serial-port timeouts** depend on the driver. GO-EDGE-1 says "a deadline, or close on cancel", and does not name a
  driver API.
- **golangci-lint** and **errcheck** were not run, and no rule depends on them. `go vet` and staticcheck are the named
  checks.

## Attribution for the shipped rules

The rule files and the catalogue paraphrase these sources, with the attribution given in the catalogue's Sources table:
Google Go Style Guide (CC BY 3.0), Effective Go and the Go race article and release notes (CC BY 4.0), the Go Memory Model
and the Go specification and standard library (BSD-3-Clause), the uber-go/guide (Apache-2.0), goleak (MIT), errgroup
(BSD-3-Clause), and the Go Blog context and pipelines posts (CC BY 4.0). Nothing from Dave Cheney's post or the Ajmani
slides is reproduced.

## Reading list for going deeper

These are the references the user asked for on goroutines and concurrency. Read them in this order.

1. Effective Go, "Concurrency" (`go.dev/doc/effective_go`): goroutines, channels, and the "share memory by communicating"
   idea.
2. Go Blog, "Go Concurrency Patterns: Pipelines and cancellation" (`go.dev/blog/pipelines`): cancellation through a
   done channel, and bounded parallelism.
3. Go Blog, "Go Concurrency Patterns: Context" (`go.dev/blog/context`): contexts, deadlines and cancel functions.
4. The Go Memory Model (`go.dev/ref/mem`): what a data race is, and why an unsynchronised flag is not enough.
5. The Data Race Detector (`go.dev/doc/articles/race_detector`): how to run `-race`, and what it cannot see.
6. uber-go/guide (`github.com/uber-go/guide`): the goroutine, mutex, channel and time rules this catalogue borrows.
7. goleak (`github.com/uber-go/goleak`): how to make a test fail on a leaked goroutine.
8. The errgroup package (`pkg.go.dev/golang.org/x/sync/errgroup`): first error, cancellation, and `SetLimit`.
9. Go 1.25 release notes (`go.dev/doc/go1.25`): `WaitGroup.Go`, `testing/synctest`, and the `waitgroup` vet analyzer.

Not read for this note (add them when you want them): Bryan Mills, "Rethinking Classical Concurrency Patterns" (a talk,
cited in the Google decisions guide); Dave Cheney's "Never start a goroutine without knowing how it will stop"
(read for ideas only, because of its licence).
