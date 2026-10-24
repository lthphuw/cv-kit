# Review report format

One finding per defect, most severe first:

```
[Critical] CPP-ERR-8 src/infer/engine.cc:88
What: the constructor throws when the engine file is missing; the target builds with -fno-exceptions.
Trigger: Engine("missing.plan") does not compile on the target build; on host it terminates the process.
Fix: private constructor + static Create(path) returning the project's result type (recipe R-CPP-1).
```

- Severity is the catalogue's Critical, Major or Minor, rated for each finding alone, never raised because others
  exist. Say why only when you changed the catalogue's default.
- The anchor is `path:line`, or `absent: <where> — expected <what>; checked <files>` for something missing (a test,
  a status check, a `Close()`).
- Group the Minor findings a tool repairs into one line per tool, for example `ruff check --fix: I001 x5, UP035 x2`.
- For each catalogue section with no findings write what you checked there in one line; do not pad.
- End with `Blocking: <n> Critical, <m> Major` and the tools that did not run. The change is not ready while a
  Critical or Major finding is open.

The catalogues are `${CLAUDE_SKILL_DIR}/../../shared/python-style.md` and
`${CLAUDE_SKILL_DIR}/../../shared/cpp-style.md`; each ends its rules with a "Review order".
