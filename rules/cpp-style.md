---
paths:
  - "**/*.{h,hh,hpp,hxx,cc,cpp,cxx,cu,cuh,inl,ipp}"
---
# C++ (edge devices)

Follow these rules when writing or editing C++. The code is C++20 inference code for edge devices (Jetson, ARM
boards, phones), built with `-fno-exceptions -fno-rtti` and strict warnings as errors. The IDs refer to cv-kit's
full C++ catalogue. Where the project has its own written rule, that rule wins. A "hot path" is a function the
project documents as running every frame under a latency budget, plus everything it calls.

## Errors without exceptions

- Never write `throw`, `try`, `catch`, `dynamic_cast` or `typeid`, and never use `std::exception_ptr` or `std::type_info` (CPP-ERR-16).
- Report failure through the project's one status / result type (`std::expected`, `tl::expected` or `absl::StatusOr`, whichever the project uses), never through `int` codes, `bool` for a multi-cause failure, or `-1` / `nullptr` / NaN sentinels (CPP-ERR-1, CPP-ERR-6).
- Status and result types are `[[nodiscard]]`; so is any query or factory whose only effect is its return value. A deliberate discard is `(void)Call();` with a comment saying why (CPP-ERR-2).
- Return an error you cannot handle to the caller with its original cause and some context; never log it and then report success. Log an error once, in the layer that applies the policy (CPP-ERR-3, CPP-ERR-4, CPP-ERR-5).
- Use the error channel only when the function failed; "no detections", "queue empty" and "no frame yet" are ordinary values (`std::optional`, an empty container) (CPP-ERR-7).
- A type whose setup can fail gets a private constructor that cannot fail plus `static Result<T> Create(...)`. No public `Init()` / `Setup()` and no `is_valid()` on half-built objects (CPP-ERR-8, CPP-ERR-9).
- Destructors never fail. When release can fail (flush, device close, stream sync), add an idempotent `[[nodiscard]] Status Close()` and let the destructor do a best-effort release (CPP-ERR-10).
- Bugs (broken invariants, impossible states) go to the project check macro, which logs and aborts. Outside conditions (bad file, camera timeout, corrupt frame, full queue) return a status. Never abort on outside data; never call `exit`, `std::terminate` or rely on `assert` in library code (CPP-ERR-11, CPP-ERR-13).
- State preconditions in the declaration comment and validate them once where data enters; inner loops do not re-check (CPP-ERR-12).
- Validate sizes from outside data before allocating; where running out of memory must be survivable, use `new (std::nothrow)`, check it and return a status (CPP-ERR-14).
- Never use aborting checks as error handling: no `.at()`, `std::get<T>` on a variant, `optional::value()`, `std::stoi`, `gsl::narrow`. Check at the boundary, then use `[]`, `std::get_if`, `has_value()` and `*`, `std::from_chars` (CPP-ERR-15).
- Avoid downcasts: a virtual function, then `std::variant` with `std::visit`, then an `As...()` query. The last resort is one audited helper per hierarchy that checks a `kind()` tag before `static_cast`, with a NOLINT and reason (CPP-ERR-17, CPP-ERR-18).
- Call third-party code that can throw only through its C API, or through a wrapper library built with `-fexceptions` whose `noexcept` entry points catch everything and return the project status (CPP-ERR-19).
- Read `errno`, `cudaGetLastError()` and similar last-error state on the same thread right after the call, and turn it into a returned status (CPP-ERR-20).
- Every new or changed error return gets a test that forces it (CPP-ERR-21).

## Edge hot paths

- Mark every hot path with a declaration comment starting `Hot path:` that names its rate and budget (CPP-EDGE-1).
- In a hot path, allocate nothing in steady state: no `new`, `make_unique`, `make_shared`, container growth past reserved capacity, `std::string` building, `std::to_string`, `std::stringstream`, large-capture `std::function`, or a new `cv::Mat` per frame (CPP-EDGE-2).
- Size per-frame buffers at init (in `Create()`) from config and model shapes, keep them as members, and reuse them; outputs go into caller-owned, reused buffers (CPP-EDGE-3).
- Give every container that grows with input (detections, tracks, caches, logs) a fixed capacity and an overflow policy; no cache without eviction (CPP-EDGE-4).
- No blocking calls in a hot path: file or socket I/O, `printf` / `std::cout`, synchronous logging, `sleep_for`, `cudaDeviceSynchronize`. Logging reachable from a hot path is rate-limited and non-blocking (CPP-EDGE-5, CPP-EDGE-6).
- Write `'\n'`, never `std::endl` (CPP-EDGE-7).
- Never hold a lock across inference or any long step; under the lock only swap a pointer, index or slot (CPP-EDGE-8).
- Connect pipeline stages with bounded queues or fixed slot pools with a documented full-queue policy (drop and count for live video) (CPP-EDGE-9).
- A frame buffer has one owning stage at a time and moves by handle; small metadata is passed by value; concurrent readers get `const` views (CPP-EDGE-10).
- Create all threads at start-up from configuration, never per frame or per request (CPP-EDGE-11). Own each thread as a `std::jthread` member that is stopped and joined; never `detach()` (CPP-EDGE-12).
- Wait on a condition variable, semaphore or `poll()` with a predicate and a `steady_clock` timeout; never spin with `yield()` or short sleeps (CPP-EDGE-13).
- Measure latency, timeouts and rates with `std::chrono::steady_clock`; `system_clock` only for wall-clock stamps; never `high_resolution_clock` (CPP-EDGE-14).
- Keep float code in float: `0.5f` literals, `float` overloads, no promotion to `double` (CPP-EDGE-15).
- Never add `-ffast-math`, `-Ofast` or `-march=native` to shipped builds (CPP-EDGE-16, CPP-EDGE-32).
- Check model outputs and sensor data for NaN / Inf at the stage boundary (CPP-EDGE-18). Quantise and dequantise through named functions that state scale, zero point, rounding and saturation (CPP-EDGE-20).
- Pin the layout of structs written to files, sent over the wire or shared with device code with `static_assert` on `sizeof`, `alignof` and trivial copyability; decode binary formats field by field with explicit byte order (CPP-EDGE-21, CPP-EDGE-23).
- Allocate SIMD, DMA and vendor buffers with the alignment they need (`alignas`, an aligned allocator) and check it at the boundary (CPP-EDGE-22).
- Pass images and tensors as a view type carrying element type, shape, stride, layout and colour order, never `T*` plus sizes (CPP-EDGE-24).
- Keep SIMD intrinsics, `__restrict__`, `__attribute__`, `__builtin_*`, `#pragma`, inline assembly and platform `#if` inside the project's portability directory, each with a scalar fallback (CPP-EDGE-25).
- Check every CUDA, TensorRT, ONNX Runtime, OpenCV, V4L2 and EGL call that can fail through the project helper that turns it into a status with the call name and vendor code; check `cudaGetLastError()` after each kernel launch (CPP-EDGE-26).
- Make every host-device copy an explicit call on a named non-blocking stream; read device results only after a sync or event on that stream, and never reuse a buffer that queued work may still touch (CPP-EDGE-27, CPP-EDGE-28).
- Never keep device or driver handles (CUDA memory, streams, TensorRT engines, camera fds) in static or global storage (CPP-EDGE-29).

## Ownership and lifetime

- Every resource (memory, fd, `FILE*`, `mmap`, socket, lock, CUDA buffer or stream, TensorRT object, V4L2 buffer) is owned by an object whose destructor releases it, so every early `return` releases it; no paired acquire/release calls and no `goto cleanup` (CPP-RES-1).
- Wrap each vendor or OS handle type in one small move-only owner (or `std::unique_ptr` with a stateless deleter); raw handles and `extern "C"` calls stay inside the wrapper's `.cc` (CPP-RES-2).
- A raw pointer or reference never owns. No naked `new` / `delete`, no `malloc` / `free` for C++ objects; use `std::make_unique`, containers and matching deleters (CPP-RES-3, CPP-RES-4, CPP-RES-6, CPP-RES-7).
- Exclusive ownership is `std::unique_ptr` (or a value); use `std::shared_ptr` only for genuinely shared ownership, say why, and prefer `shared_ptr<const T>`. Break cycles with `std::weak_ptr` (CPP-RES-8, CPP-RES-9, CPP-RES-11).
- Take a smart pointer as a parameter only to transfer or share ownership; a function that only uses the object takes `T&`, `const T&` or `T*` (CPP-RES-12).
- Before passing `*p` from a smart pointer that another thread or the callee could reset, copy it into a local (CPP-RES-13).
- No large objects or variable-length arrays on worker-thread stacks, and no recursion driven by image data (CPP-RES-15).
- Never keep a pointer, reference, iterator, `span` or view across an operation that may reallocate or erase the container, or into a frame buffer that is recycled (CPP-RES-19).
- Never return or store a pointer, reference, `span`, `string_view` or `cv::Mat` header that refers to a local, a temporary or a by-value parameter (CPP-FN-13).
- A lambda that outlives the scope (queued, stored, registered as a callback) captures by value or by move, never by reference, raw pointer or bare `this` (CPP-FN-27).
- Declare members in dependency order: what others use during construction or destruction comes first, and a thread member comes after the state it reads (CPP-CLS-8).
- A move leaves the source handle empty (`nullptr`, `-1`) so its destructor releases nothing (CPP-CLS-15).

## Concurrency

- No mutable function-local `static` and no mutable globals or static members for program state; per-stream state lives in an object the caller owns (CPP-CONC-1).
- Every object written by one thread and read by another is a `std::atomic` or guarded by the same mutex at every access, and the pairing is annotated (`GUARDED_BY`) (CPP-CONC-2, CPP-CONC-9).
- Lock only through a named RAII guard (`std::scoped_lock lock(mu_);`); never call `lock()` / `unlock()` by hand; lock several mutexes in one `std::scoped_lock` (CPP-CONC-3, CPP-CONC-4, CPP-CONC-5).
- Hold a lock only around the shared-state access; never call callbacks, virtual functions, I/O or logging under it, and do not use `std::recursive_mutex` (CPP-CONC-6, CPP-CONC-7).
- Wait on a condition variable only with a predicate that includes a stop flag, and change that state under the same mutex before notifying (CPP-CONC-8).
- Everything a thread uses outlives it (CPP-CONC-10). Never use `volatile` for communication between threads (CPP-CONC-11).
- Use the default `seq_cst` order on atomics unless a comment names the paired operation and an ARM stress test exists; a check-then-act on several values needs a lock or one read-modify-write (CPP-CONC-12, CPP-CONC-13).
- One-time initialisation is a function-local static or `std::call_once`, never hand-rolled double-checked locking (CPP-CONC-15).
- No `std::async`, `std::promise` or `std::packaged_task`; submit to the project work queue, and let errors cross threads as result values (CPP-CONC-16).
- Coroutines only through an approved library: no reference parameters, no captures, no lock held across `co_await`, never on a hot path (CPP-CONC-17).
- A signal handler only sets a lock-free atomic flag (CPP-CONC-18). Test threaded changes under TSan (CPP-CONC-19).

## Expressions and types

- Initialise every variable where it is declared, in the narrowest scope; compute branch-dependent values in a helper or an immediately invoked lambda so they can be `const` (CPP-EXPR-1, CPP-EXPR-2, CPP-EXPR-12).
- Do not shadow names (CPP-EXPR-4). Use `std::array` / `std::vector`, never C arrays, `new[]` or variable-length arrays (CPP-EXPR-8).
- No C-style casts; use `static_cast`, and `reinterpret_cast` only at hardware or driver boundaries (CPP-EXPR-17, CPP-EXPR-18).
- Never read an object as another type through `reinterpret_cast`, `void*` or a union; copy bits with `std::bit_cast` or `std::memcpy`. Read a `std::variant` with `std::get_if` or `std::visit` (CPP-EXPR-19, CPP-CLS-49).
- No implicit narrowing: convert with `static_cast` after a range check; convert float to integer only with an explicit rounding (`std::lround`) after a range and NaN check (CPP-EXPR-20, CPP-EXPR-21).
- Integer types by role: `int` for small counts, `int64_t` or `ptrdiff_t` for sizes and indices, exact-width `<cstdint>` types for tensors, pixels and file formats; no `long`, `short` or `unsigned` for "non-negative"; never plain `char` for pixel data (CPP-EXPR-22, CPP-EXPR-23, CPP-EXPR-27).
- Never mix signed and unsigned in comparisons (`std::ssize`, `std::cmp_less`); widen before multiplying sizes and check products of untrusted dimensions; guarantee divisors are non-zero (CPP-EXPR-24, CPP-EXPR-25, CPP-EXPR-26).
- No `long double` (CPP-EXPR-28). No unsequenced modifications (`v[i] = i++`) (CPP-EXPR-29).
- Write `nullptr`, never `0` or `NULL` (CPP-EXPR-32). Test a nullable pointer before dereferencing it (CPP-EXPR-35).
- No raw pointer arithmetic outside one audited view type or kernel; check bounds once at the API boundary, then index (CPP-EXPR-36, CPP-EXPR-38).
- `std::move` only to hand a named object to a new owner; never on a `const` object, a returned local or a forwarding reference; never use an object after moving from it (CPP-EXPR-39, CPP-FN-16).
- A `switch` on an `enum class` lists every enumerator and has no `default`; end each case with `break` / `return` or `[[fallthrough]];` (CPP-EXPR-42, CPP-EXPR-43).
- Name unexplained literals (input sizes, mean/std, thresholds) as `constexpr` constants (CPP-EXPR-15). Use `auto` only when the type is obvious or noise (CPP-EXPR-9).

## Functions and classes

- Keep functions short and single-purpose (CPP-FN-1). Type parameters precisely: no `void*`, no runs of `bool` flags (use an `enum class` or an options struct), units in the type (`std::chrono::milliseconds`) (CPP-FN-4).
- Never put same-typed order-sensitive parameters side by side (width/height, src/dst); pass a `Size`, `Rect` or `Point` (CPP-FN-5).
- Pass cheap inputs (scalars, `std::span`, `std::string_view`) by value, other inputs by `const T&`, in-out by `T&`, sinks by value plus `std::move`. Never take `std::string`, `std::vector` or `cv::Mat` by value just to read it (CPP-FN-7, CPP-FN-8).
- A maybe-absent parameter is `T*` or `std::optional`; a required one is a reference (CPP-FN-10).
- Return results by value, several as a named struct, not `std::pair` / `std::tuple`; out-parameters only for caller-owned buffers reused across frames (CPP-FN-11, CPP-FN-12).
- Pass sequences as `std::span<const T>` / `std::span<T>`, text as `std::string_view`, never pointer plus count (CPP-FN-35, CPP-LIB-16).
- No C varargs; the `printf` family only inside one audited formatting helper (CPP-FN-21). No default arguments on virtual functions (CPP-FN-23). No deduced `auto` return types on public header functions (CPP-FN-25).
- `struct` only for passive data with no invariant; a `class` keeps all data private (CPP-CLS-1, CPP-CLS-3).
- Follow the rule of zero; a class with a private section states copy/move intent publicly (`= default` / `= delete`); once any special member is declared, declare all five (CPP-CLS-9, CPP-CLS-10, CPP-CLS-11).
- Moves and `swap` are `noexcept`, otherwise `std::vector` copies on growth (CPP-CLS-14). Types that own frames, tensors or model buffers are move-only, with an explicit `Clone()` if needed (CPP-CLS-27).
- A constructor initialises every member; constant defaults go on the member declaration (CPP-CLS-18, CPP-CLS-19). No `const` or reference data members in copyable or movable types (CPP-CLS-7).
- Mark one-argument constructors and conversion operators `explicit` (CPP-CLS-23). Never call a virtual function from a constructor or destructor (CPP-CLS-24).
- Base destructors are public virtual or protected non-virtual; overrides say `override` or `final`, not `virtual`; polymorphic bases delete copy and move to prevent slicing (CPP-CLS-29, CPP-CLS-30, CPP-CLS-33).
- Never `memset` / `memcpy` an object that is not trivially copyable; put `static_assert(std::is_trivially_copyable_v<T>)` next to byte copies (CPP-CLS-25).
- Use `enum class`; give enumerators explicit values when they must match class indices or file formats (CPP-CLS-45, CPP-CLS-46).

## Headers, naming, layout

- Files are `.h` / `.cc` (a project already on `.hpp` / `.cpp` keeps them); guard headers with `#ifndef PROJECT_PATH_FILE_H_`, never `#pragma once` (CPP-HDR-1, CPP-HDR-5, CPP-HDR-6).
- Include what you use, as quoted paths from the source root; never forward-declare `std`, `cv` or other third-party entities (CPP-HDR-7, CPP-HDR-10, CPP-HDR-13).
- Define in headers only ODR-safe things, and only short (about 10 lines) or template / `constexpr` bodies (CPP-HDR-14, CPP-HDR-16).
- All code lives in the project namespace; no `using namespace` anywhere; nothing added to `std`; `.cc`-local helpers go in an unnamed namespace, not `static` (CPP-HDR-17, CPP-HDR-18, CPP-HDR-21, CPP-HDR-24).
- Objects with static storage are trivially destructible and constant-initialised (`constexpr`, `constinit`, `constexpr std::string_view`, `constexpr std::array`); namespace-scope `thread_local` is `constinit` (CPP-HDR-29, CPP-HDR-30, CPP-HDR-33).
- C++20 only, no C++23 features beyond the chosen error type (CPP-LIB-1). No user-defined literal suffixes (`10ms`, `"x"s`) (CPP-LIB-4).
- No `<iostream>` in device libraries; use the project logger (CPP-LIB-9). No macros where `constexpr`, an enum or a function works (CPP-LIB-10). Platform `#if` only in the portability layer (CPP-LIB-13).
- `std::vector<float> v(n, 0.0f)` makes `n` elements; braces always mean an element list (CPP-LIB-15). No `strcpy`, `sprintf`, `atoi`; use `std::from_chars` (CPP-LIB-17). No `setjmp` / `longjmp` (CPP-LIB-19).
- Names: types and functions `PascalCase`; variables and parameters `snake_case`; class members `name_`, struct members `name`; constants and enumerators `kName`; namespaces `snake_case`; macros `PROJECT_UPPER_CASE`; cheap accessors `size()`, `set_size()` (CPP-NAME-4 to CPP-NAME-15).
- No reserved identifiers (anything with `__`, or `_` plus a capital letter) (CPP-NAME-16).
- Document every image or tensor parameter's shape, layout (NCHW/NHWC), element type, value range and colour order (RGB/BGR), and each shared class's thread-safety (CPP-DOC-8, CPP-DOC-4).
- Write TODOs as `// TODO(<issue or name>): <what>` (CPP-DOC-16).
- Suppress a finding only on its line, with a reason: `// NOLINT(check-name): reason`, naming every check name clang-tidy prints, or `// cv-kit: allow[CPP-XXX-n]: reason` for a rule no tool checks (CPP-DOC-18).

Formatting is clang-format's job (Google style, 80 columns, `int* p`, braces always); do not hand-format against
it. The full C++ catalogue, with checks and severities, and code review are in the cv-kit plugin's `py-cpp-review` skill.
