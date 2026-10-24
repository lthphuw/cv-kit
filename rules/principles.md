# Working principles

- **Test first.** No production code without a failing test you watched fail: a bug gets a test that reproduces it, a feature gets tests for its use cases, a refactor gets its behaviour pinned first. Python tests use pytest, C++ tests use GoogleTest.
- **Process over guessing.** Reproduce, isolate, form one hypothesis, change one thing. No fix without a root cause; after two failed fixes, stop and re-read the evidence.
- **Simplicity.** The smallest change that passes. No abstraction with one user, no unrequested option, no new dependency. Delete before adding.
- **Evidence over claims.** Do not say "done", "fixed", "passing" or "faster" without command output from this turn. Say what did not run.
- A project's own written rule beats these. For non-trivial work use `/cv-kit:develop`, which routes to agents sized to the task.
