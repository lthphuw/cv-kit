---
paths:
  - "**/*.{py,pyi}"
---
# Python

Follow these rules when writing or editing Python. The IDs refer to cv-kit's full Python catalogue. Target
Python 3.10 or later. Where the project has its own written rule, that rule wins.

## Errors and assert

- Use `assert` only in tests. Validate arguments, shapes, dtypes and ranges with `raise ValueError(...)` or `TypeError(...)` (PY-ERR-1).
- Never write a bare `except:`. Catch `Exception` only to re-raise, or at a thread, worker or per-sample boundary that logs the traceback and counts the failure (PY-ERR-2).
- Never swallow an error silently; use `contextlib.suppress(SpecificError)` when ignoring it is right (PY-ERR-3).
- Keep `try` bodies to the lines that can raise, put the success path in `else:`, and catch the narrowest types (PY-ERR-4, PY-ERR-5).
- Translate with `raise NewError(...) from err`; re-raise with a bare `raise` (PY-ERR-6).
- Raise the fitting built-in or a project `...Error` subclass, never `Exception` itself (PY-ERR-7, PY-ERR-8).
- No `return`, `break` or `continue` in `finally` (PY-ERR-9). No `sys.exit()` outside a script's `main()` (PY-ERR-11).

## Resources and files

- Release every resource with `with` or `try`/`finally`: files, sockets, pools, subprocesses, h5py/LMDB handles, `cv2.VideoCapture`/`VideoWriter` (`finally: cap.release()`), matplotlib figures made in loops (PY-RES-1).
- Never rely on `__del__` or garbage collection for cleanup; a class that owns a resource is a context manager with `close()` (PY-RES-2, PY-RES-3).
- A generator that holds a resource must release it when the consumer stops early (`contextlib.closing` or `@contextmanager`) (PY-RES-4).
- Open text files with `encoding="utf-8"` and the least mode needed; CSV with `newline=""` (PY-RES-5). Use `pathlib.Path` for paths (PY-RES-6).
- Write checkpoints and indexes to a temp file in the same directory, then `os.replace` it (PY-RES-7).
- Never load outside data with `pickle`, `torch.load` without `weights_only=True`, `yaml.load` or `np.load(allow_pickle=True)`; use `yaml.safe_load`, `json`, `ast.literal_eval` (PY-RES-9).
- Run commands as `subprocess.run([...], check=True, timeout=...)`, never `shell=True` or `os.system` (PY-RES-10). Give every blocking call a timeout (PY-RES-11). Use `tempfile` for temporary files (PY-RES-12).

## State, defaults and module level

- No mutable module-level state in library code (caches, registries, `global`); if unavoidable, make it `_private`, reach it through functions, and remember each worker process has its own copy (PY-STATE-1).
- Constants are immutable and `CAPS_WITH_UNDER` (PY-STATE-2).
- Never use a mutable default (`[]`, `{}`, `np.zeros(3)`, a tensor); default to `None` and build it in the body (PY-STATE-3). No defaults computed at import time (`time.time()`, env vars) (PY-STATE-4).
- Per-instance state goes in `__init__` or `field(default_factory=...)`, never a mutable class attribute (PY-STATE-5).
- Importing a module must do no work: no model loading, file or camera opening, CUDA init, argument parsing, `logging.basicConfig`, seeding or `print` at module level (PY-STATE-6).
- Scripts put their work in `main()` under `if __name__ == "__main__":`, which multiprocessing and `DataLoader` workers require (PY-STATE-7).
- Library code never changes process-wide settings: `os.chdir`, `os.environ`, `sys.path`, warning filters, `torch.backends.cudnn.*`, thread counts (PY-STATE-8).

## Imports

- Import modules, not names: `from torch.utils import data`, then `data.DataLoader`; only `typing`, `collections.abc` and `typing_extensions` names may be imported directly (PY-IMP-1).
- Aliases only `np`, `pd`, `plt`, `tf`, `F` (torch.nn.functional); write `from torch import nn` (PY-IMP-2).
- No relative imports, no `sys.path` edits, no star imports (PY-IMP-3, PY-IMP-4, PY-IMP-5).
- Imports at the top, one per line; a function-local import only for a heavy optional dependency, with a reason (PY-IMP-6, PY-IMP-7).
- No `try: import` at module level; type-only imports go in `if TYPE_CHECKING:` (PY-IMP-11). Keep `__init__.py` free of work (PY-IMP-13).

## Functions and classes

- Bind loop variables in closures made in a loop (`functools.partial`, `lambda x, i=i: ...`) (PY-FN-2).
- Never mutate a container while iterating over it (PY-FN-9). Use `zip(..., strict=True)` for paired data (PY-FN-10).
- Never iterate a generator, `map` or file twice; materialise with `list()` if needed (PY-FN-11).
- Never mutate a caller's list, dict, array or tensor unless the name and docstring say so (PY-FN-21).
- Never drop a returned value (`s.strip()`, `arr.astype(...)`, `t.to(device)`) or keep the `None` of `xs.sort()` (PY-FN-28).
- Never build nested lists with `[[0] * w] * h` or `[obj] * n` (PY-FN-29).
- Make boolean and option parameters keyword-only, and avoid swappable positional pairs like `h, w` (PY-FN-18, PY-FN-19).
- Decorator wrappers use `@functools.wraps`, forward `*args, **kwargs` and return the result; decorators do no work at decoration time (PY-FN-13, PY-FN-14).
- Stay within 5 parameters, 12 branches, 6 returns, 50 statements per function (PY-FN-16). No quadratic patterns on growing data (`list.pop(0)`, `in list` in a loop) (PY-FN-25).
- Use `functools.cache`/`lru_cache(maxsize=N)`, never on methods, never on arrays or tensors (PY-FN-27).
- Comprehensions have at most one `for` and one `if`; no lambdas bound to names (PY-FN-4, PY-FN-6).
- No `@staticmethod` (use a module function); `@classmethod` only for named constructors (PY-CLS-1, PY-CLS-2).
- Properties are cheap and side-effect free; no pass-through getters or setters; setters raise on bad values instead of clamping (PY-CLS-3, PY-CLS-4, PY-CLS-8).
- Configs and records are `@dataclass(frozen=True)` or `typing.NamedTuple` (PY-CLS-9, PY-CLS-10).
- No metaclasses, `eval`/`exec`, monkey-patching or `getattr` dispatch (PY-CLS-11).
- Call `super().__init__()` first, before any attribute (required for `nn.Module`) (PY-CLS-12). Mark overrides with `@override` (PY-CLS-13).
- Define `__hash__` with `__eq__`; return `NotImplemented` for unsupported operands (PY-CLS-14). Single `_private`, never `__mangled` (PY-CLS-15).

## Types

- Annotate every parameter and return in library code, `-> None` on `__init__` included; the code passes `mypy --strict` (PY-TYPE-1, PY-TYPE-2).
- Avoid `Any` where a real type, `TypeVar` or `Protocol` works (PY-TYPE-3).
- Write `X | None`, `list[int]`, `collections.abc.Sequence[T]`; never `Optional`, `typing.List` or implicit `= None` (PY-TYPE-4, PY-TYPE-5, PY-TYPE-6).

## Truthiness, None and comparisons

- Compare with `is None`; when `0`, `0.0` or `""` is legal, never write `x = x or default` (PY-BOOL-1, PY-BOOL-2).
- Never use an array or tensor in a boolean context; test `is None`, `.size`, `.numel()`, `.any()` (PY-BOOL-5).
- `is` only for `None`, sentinels and enums; never for numbers or strings (PY-BOOL-7).
- `isinstance`, not `type(x) == T`; remember `bool` is an `int` (PY-BOOL-8).
- Write range checks so NaN fails: `if not 0.0 <= p <= 1.0: raise ...` (PY-BOOL-9).
- Guard empty inputs to `max`, `min`, `all`, `np.mean` when empty is an error (PY-BOOL-15).

## Strings and logging

- f-strings in ordinary code; no `+` chains; no `+=` string building in loops (use `"".join`) (PY-STR-1, PY-STR-3, PY-STR-4).
- Never rely on implicit concatenation inside lists or calls: `["cat" "dog"]` is one item (PY-STR-7).
- Library code logs through `logger = logging.getLogger(__name__)`; no `print`, no root-logger calls, no logging configuration (PY-STR-9, PY-STR-10, PY-STR-13).
- Log with a `%`-pattern and arguments: `logger.info("read %d frames", n)`, never f-strings; use `logger.exception` in handlers (PY-STR-11, PY-STR-12).
- Error messages state the exact failed condition and the value, `f"expected (H, W, 3), got {img.shape}"` (PY-STR-14).
- Handle suffixes with `pathlib` or `removesuffix`, never `rstrip(".png")` (PY-STR-15). Parse CSV with `csv`, not `split(",")` (PY-STR-16).

## Threads and processes

- Never rely on atomic built-ins; guard shared state with `with lock:` (PY-CONC-1).
- Pass data between threads with a bounded `queue.Queue`; use `Event`/`Condition`, not sleep-polling (PY-CONC-2, PY-CONC-3).
- Catch and log exceptions at the top of each thread; join threads; read every future's result (PY-CONC-4, PY-CONC-5).
- Never fork after CUDA init (use `spawn`); send only picklable objects; pass paths or shared memory, not big arrays, through queues; drain a queue before `join()` (PY-CONC-6 to PY-CONC-9).

## Computer vision and ML

- Use explicit generators (`np.random.default_rng(seed)`, `torch.Generator`); never `np.random.seed` or `torch.manual_seed` in library code (PY-ML-1). Seed `DataLoader` workers and log the seed (PY-ML-2).
- Sort file listings and class names before assigning indices; zero-pad frame numbers (PY-ML-3).
- Docstrings of array functions state shape with named dims, layout (NCHW/HWC), dtype, value range, colour order (RGB/BGR) and box format (PY-ML-4). Annotate with `NDArray[...]` / `torch.Tensor` (PY-ML-5).
- Validate array shape and dtype once at the public boundary (PY-ML-6).
- No per-pixel Python loops where NumPy, PyTorch or OpenCV can vectorise; never grow arrays with `np.append`/`torch.cat` in a loop (PY-ML-7, PY-ML-8, PY-ML-9).
- Convert `uint8` to a wider dtype before arithmetic and clip back (PY-ML-10). Use `//` for sizes and indices (PY-ML-11).
- Copy (`.copy()`, `.clone()`) before writing to a view you do not own; make arrays contiguous before OpenCV (PY-ML-12).
- Inference: `model.eval()` and `with torch.inference_mode():`; restore `train()` after evaluation in a training loop (PY-ML-13).
- No `.item()`, `.cpu()`, `.numpy()` or printing of CUDA tensors per batch without need; never keep `loss` tensors in lists (PY-ML-14, PY-ML-15, PY-ML-16).
- Take `device` as a parameter; never hard-code `.cuda()` (PY-ML-17).
- Convert BGR to RGB explicitly at one documented boundary; check `cv2.imread` for `None` and `cap.read()` for `ok` (PY-ML-18, PY-ML-19).
- Datasets open heavy handles lazily per worker and stay picklable (PY-ML-20).
- Compare floats with `isclose`/`allclose` and a stated tolerance, never `==` (PY-ML-21).
- Time with `time.perf_counter()` and `torch.cuda.synchronize()`; call `model(x)`, not `model.forward(x)` (PY-ML-23, PY-ML-25).

## Docs, names, tests

- Google docstrings (`Args:`, `Returns:`/`Yields:`, `Raises:`) for every public function, class and module, saying what it does and its side effects (PY-DOC-4 to PY-DOC-8).
- TODOs read `# TODO(<issue reference>): <what and when>` (PY-DOC-20).
- `lower_with_under` for functions and variables, `CapWords` for classes, `CAPS` for constants; no built-in shadowing (`id`, `type`, `input`, `max`) (PY-NAME-1, PY-NAME-8).
- Suppress a check only on its line with the code and a reason: `# noqa: B008  # reason`, `# type: ignore[code]  # reason`, or `# cv-kit: allow[PY-CLS-1]  # reason` (PY-LINT-2, PY-LINT-3).
- Add tests with every behaviour change; tests use pytest `assert`, fixed seeds, no network or GPU, and tolerance comparisons (PY-TEST-1, PY-TEST-6, PY-TEST-7).

Layout is `ruff format`'s job (80 columns, 4 spaces, double quotes); do not hand-format against it. The
complete catalogue, with checks and severities, and code review are in the cv-kit plugin's `review` skill (`/cv-kit:review`).
