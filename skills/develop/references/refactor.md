# Refactor without changing behaviour

A refactor changes structure, not behaviour. The recipes and rule IDs are in the catalogues:

- Python: `${CLAUDE_SKILL_DIR}/../../shared/python-style.md` (section "Refactor recipes", `R-PY-n`)
- C++: `${CLAUDE_SKILL_DIR}/../../shared/cpp-style.md` (section "Refactor recipes", `R-CPP-n`)

1. **Agree on scope.** Files or functions, the goal (rule IDs or a smell), and what must not change: public API and
   ABI, file and wire formats, numeric outputs with their tolerance, log and error text other code parses, and on
   edge targets the latency and memory budget. Changing a public name, signature or ABI needs an explicit yes.
2. **Pin the behaviour first.** Find the tests that cover the code and run them; record command and result. If
   nothing covers it, write characterisation tests before touching it: real inputs, today's outputs, the edge
   cases (empty, one element, largest size, invalid input and its error). Numeric code compares against saved
   outputs with a stated tolerance. For a C++ hot path also record p50 and p99 latency (hardware, precision,
   batch, warm-up) and peak memory. Code that cannot be tested gets the smallest seam that makes it testable, and
   nothing else, as its first step.
3. **Plan small steps.** One recipe and one concern per step. Formatting is a step of its own, never mixed with
   logic. Show the plan; wait for a yes when it has more than a handful of steps.
4. **One step at a time.** Edit, then run tests, linters and (C++) the strict build. If anything fails, undo that
   step only. Never change behaviour and structure in one step.
   - A bug found on the way is reported, not fixed silently; its fix is a separate change with its own test.
   - No new dependency, no abstraction with one user, no speculative extension point.
   - Never weaken or delete a test, and never add `# noqa`, `// NOLINT` or `# type: ignore` to make a tool pass.
     A suppression that is truly needed names the check and the reason, and the user agrees to it.
   - C++ edge code keeps the `-fno-exceptions -fno-rtti` build green; after a step on a per-frame path, measure
     again before saying it is faster or no slower.
5. **Finish.** Report the steps with their recipe and rule IDs, the commands and results, what was left and why,
   and anything whose behaviour may differ, with the evidence that it does not. Offer a review of the result.
