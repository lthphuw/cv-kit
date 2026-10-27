# Routing: agent, model, effort

Pick by the cost of being wrong, not by the size of the diff. Models are the aliases `haiku`, `sonnet` and `opus`
(Haiku 5.5, Sonnet 5.5 and Opus 5.5 on the Anthropic API; the Agent tool's per-call `model` rejects a full model id).
Each agent's frontmatter holds its default, and a `model` or `effort` on the Agent call wins. To pin a version,
edit the agent's `model` to a full id; the environment variable `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` overrides
every agent's `model`, so unset it if routing seems ignored.

## Difficulty

| Level | Signs | Start with |
| --- | --- | --- |
| Trivial | One file, known location, no behaviour change, read-only | `haiku`, low |
| Routine | Clear spec, one module, a test can pin it | `sonnet`, medium |
| Hard | Root cause unknown, several modules, shared state or threads, numeric tolerance, latency budget, memory safety, security, a public API or ABI | `opus`, high |
| Stuck | Two attempts failed, or the evidence contradicts itself | `opus`, xhigh |

A task is Hard when any one sign holds. When unsure, take the higher level: a wrong cheap run costs a second run.

Review follows the same levels. A Hard change, or one touching numerics, security or a published number, gets `reviewer`
at `opus`, high. A Routine change whose tests and linters pass gets `reviewer` at `sonnet`, medium. A one-line change
gets no reviewer; its test output is the check.

## Rules

- One concern per agent. A plan with a test, a fix and a review is three calls, in order.
- Independent means: no shared files and no output used as another's input. Only those run in parallel.
- The reviewer never sees the author's reasoning or findings first; it gets the diff, the test output and the rules.
- Read-only work (`explorer`, `reviewer`) cannot edit; only `engineer` writes code, and it follows the red, green,
  refactor loop in the tests references.
- Do not use `max` effort for routine escalation; the docs warn it overthinks.
- To see which model ran, open the subagent in `/tasks`, or press Ctrl+O to show the model on each message.
- A returned result is a claim. Rerun the test or command it names before you rely on it.
