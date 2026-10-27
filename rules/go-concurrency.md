---
paths:
  - "**/*.go"
---
# Go concurrency and device I/O

Follow these rules when writing or editing Go that starts goroutines, uses channels, locks, contexts or timers, or talks
to a device. The IDs refer to cv-kit's full Go catalogue (`shared/go-style.md`). Three failures matter most on a device
service: a goroutine that never ends, a call that blocks forever, and a buffer or map that grows without a bound. The
race detector finds races that run; these rules prevent the rest.

## Goroutine lifetime and ownership

- Every goroutine has a stop signal (a cancelled context, a closed input channel, or bounded work), and its owner
  waits for it before returning or shutting down (GO-CONC-1, GO-CONC-3).
- No bare `go f(item)` per item with no stop signal and no completion tracking (GO-CONC-2).
- A type that owns goroutines has one `Close`, `Stop` or `Shutdown` that signals them and waits (GO-CONC-4). Start
  goroutines from `main` or a constructor, never from `init()` (GO-CONC-5).
- Signal completion with `defer` as the first statement (`defer wg.Done()`, `defer close(done)`) (GO-CONC-6).
- Call `wg.Add` before the `go` statement, never inside the new goroutine. Do not reuse a `WaitGroup` early, and never
  copy one (GO-CONC-7, GO-CONC-9). On Go 1.25 or newer, `wg.Go(f)` does both (GO-CONC-8).
- Each long-lived goroutine recovers its own panic, logs it with the device or job identity, and then stops or restarts
  only that unit of work. An unrecovered panic ends the whole program (GO-CONC-10).

## Bounding work and memory

- Bound the goroutines. Take a slot, or hand work to a fixed pool, before the `go` statement; `errgroup.SetLimit` does
  this for a group (GO-CONC-11). Release a slot with `defer` (GO-CONC-12). Give a pool an explicit shutdown
  (GO-CONC-13).
- Each device runs in its own goroutine or bounded pool, with its own context and bounded queue (GO-CONC-14).
- Every queue or channel has a stated capacity and a stated full-queue policy. No unbounded slice as a queue
  (GO-CONC-15). A channel buffer is zero or one unless its size is justified (GO-CONC-16).
- A reply that the caller may no longer wait for goes into a buffer of one, or is sent under a `select` on the
  caller's context (GO-CONC-17).
- Every map, slice or cache that grows with device input has a cap and an eviction or reject policy (GO-EDGE-3).

## Channels and select

- Every blocking send or receive in a long-lived goroutine sits in a `select` with `ctx.Done()` or a stop channel
  (GO-CONC-18).
- Only the owner of the send side closes a channel, once. Never send or close after a close: it is a panic (GO-CONC-19,
  GO-CONC-20).
- A `for` loop that receives from a channel it does not own also selects on its own stop signal (GO-CONC-21).
- Leave a loop on a closed channel with the two-value receive or `range`. A receive from a closed channel returns the
  zero value at once (GO-CONC-22).
- Make every channel with `make` before use. A nil channel blocks forever (GO-CONC-23).
- A `select` loop that must stop on shutdown returns or uses a labelled `break`. A bare `break` inside `select` leaves
  only the `select` (GO-CONC-24).
- Never spin: no empty `for {}`, and no `select` with an empty `default` inside a loop (GO-CONC-25).
- Hand data between goroutines over a channel, and protect state that stays in one place with a mutex (GO-CONC-29).

## Locks and shared state

- Take each lock with `defer mu.Unlock()` on the next line (GO-CONC-32). Make the mutex a named field, not an embedded
  one (GO-CONC-33). Never copy a value that holds a lock (GO-CONC-34).
- Never hold a lock across device or network I/O, a channel operation, `time.Sleep`, or a callback. Copy what you need,
  unlock, then do the slow part (GO-CONC-35). A locked method returns a copy of a map or slice, never the original
  (GO-CONC-36).
- A map shared between goroutines has one guard. Every variable that two goroutines touch with a write is protected by a
  lock, a channel, or an atomic (GO-CONC-37, GO-CONC-38).
- Use typed atomics (`atomic.Bool`, `atomic.Int64`), and never mix atomic and plain access to one variable
  (GO-CONC-39). On 32-bit targets, align 64-bit values used with raw atomics (GO-CONC-40).
- Do not poll a plain variable to wait for a goroutine. Wait on a `WaitGroup`, a channel or a lock (GO-CONC-44).
  Declare a result such as `err` inside the goroutine that uses it (GO-CONC-45).

## Context, cancellation and shutdown

- A function that blocks, does I/O, or waits on a device takes `ctx` first, honours cancellation, and returns
  `ctx.Err()` (GO-CONC-46). Pass the caller's context down. Never replace it with `context.Background()` midway
  (GO-CONC-47).
- Never store a context in a struct field, and never define a custom context type (GO-CONC-48, GO-CONC-49).
- Call the cancel function on every path, with `defer cancel()` on the next line (GO-CONC-50).
- Every loop that can block observes `ctx.Done()` on each iteration (GO-CONC-55). Never sleep in a loop that must stop
  (GO-CONC-65).
- Shut down in order: stop new work, cancel the root context, wait with a bounded timeout, then close connections and
  files (GO-CONC-56). `main` gets its root context from `signal.NotifyContext`, and a `signal.Notify` channel is
  buffered (GO-CONC-57, GO-CONC-58).
- Work that must outlive its caller is detached on purpose, with its own timeout and owner (GO-CONC-53).

## Device I/O and time

- Every network or serial read and write has a deadline, or is cancelled by closing the connection when its context
  ends (GO-EDGE-1). A blocking device call never runs in the goroutine that handles shutdown or commands (GO-CONC-62).
  A call that cannot take a context runs in its own goroutine, reports on a buffered channel, and the caller waits in a
  `select` with a timeout (GO-CONC-63).
- Every retry loop has a limit or a context, and waits between attempts (GO-EDGE-2). Validate a length from a frame
  before it sizes an allocation (GO-EDGE-4).
- Durations are `time.Duration`. Measure elapsed time with the monotonic clock. Timestamps to devices are RFC 3339
  with a zone (GO-EDGE-5, GO-EDGE-6, GO-EDGE-8).
- Use `time.NewTicker` with `defer ticker.Stop()`. Do not call `time.After` or `time.Tick` in a hot loop in a module
  older than Go 1.23 (GO-EDGE-13, GO-EDGE-14). Check the `go` line before writing timer drains (GO-EDGE-11).
- An `http.Server` shuts down with `Shutdown(ctx)` under a deadline (GO-EDGE-15).
- No `defer` in an endless loop; move the loop body into a function (GO-CONC-64).
