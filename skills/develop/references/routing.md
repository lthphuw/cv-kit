# Routing: agent, model, effort

Pick by the cost of being wrong, not by the size of the diff. Models are `claude-haiku-5-5`, `claude-sonnet-5-5`
and `claude-opus-5-5`; each agent's frontmatter holds its default, and a `model` or `effort` on the Agent call wins.

## Difficulty

| Level | Signs | Start with |
| --- | --- | --- |
| Trivial | One file, known location, no behaviour change, read-only | haiku, low |
| Routine | Clear spec, one module, a test can pin it | sonnet, medium |
| Hard | Root cause unknown, several modules, shared state or threads, numeric tolerance, latency budget, memory safety, security, a public API or ABI | opus, high |
| Stuck | Two attempts failed, or the evidence contradicts itself | opus, xhigh |

A task is Hard when any one sign holds. When unsure, take the higher level: a wrong cheap run costs a second run.

## Rules

- One concern per agent. A plan with a test, a fix and a review is three calls, in order.
- Independent means: no shared files and no output used as another's input. Only those run in parallel.
- The reviewer never sees the author's reasoning or findings first; it gets the diff, the test output and the rules.
- Read-only work (`explorer`, `reviewer`) cannot edit; only `engineer` writes code, and it follows the red, green,
  refactor loop in the tests references.
- A returned result is a claim. Rerun the test or command it names before you rely on it.
