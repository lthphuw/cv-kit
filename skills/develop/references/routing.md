# Routing: agent, model, effort, brief

Pick by what is still unknown, not by the topic or the size of the diff. Models are the aliases `haiku`, `sonnet` and
`opus` (Haiku 5.5, Sonnet 5.5 and Opus 5.5 on the Anthropic API; the Agent tool's per-call `model` rejects a full
model id). Each agent's frontmatter holds its default (`engineer` and `reviewer`: `sonnet`, high), and a `model` or
`effort` on the Agent call wins. To pin a version, edit the agent's `model` to a full id; the environment variable
`CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` overrides every agent's `model`, so unset it if routing seems ignored.

## Difficulty

| Level | Signs | Run with |
| --- | --- | --- |
| Lookup | Read-only: where is X, who calls Y, what does this log say | `explorer`, `haiku`, low |
| Mechanical | No behaviour change, or a test for behaviour already pinned | `engineer`, `sonnet`, medium |
| Routine (the default) | The spec is known or the bug reproduces in a test; box maths, NMS, a loader, a located bug, a perf fix with a benchmark | `engineer`, `sonnet`, high |
| Hard | A concurrency or memory-safety bug; a cause still unknown after `explorer` and a reproduction attempt; a design across modules; a public API or ABI | `engineer`, `opus`, high |
| Stuck | An `opus` high attempt failed on the reasoning | `engineer`, `opus`, xhigh, once; then report |

Size after `explorer` has answered: a quick look often turns "some bug in the pipeline" into a located one, which is
Routine. A topic alone (numerics, performance, CV) does not make a task Hard; an unknown does. Most failed Sonnet runs
are failed briefs, so the first answer to a failure is a better brief, not a bigger model.

Review follows the same split: `reviewer` on `sonnet`, high, by default; on `opus`, high, when the change touches
concurrency, memory safety, security or a number that will be published. A one-line change gets no reviewer; its
test output is the check.

## A good brief

A brief is the only context the engineer has. It is good when the engineer never has to search for where to start
and can tell, without asking, when it is done.

Bad:

```
Fix the IoU bug in the tracker, the tests are failing.
```

Good:

```
Goal: iou() returns 0.0 for boxes that do not overlap; today two negative sides multiply into a positive area.
Done when: pytest tests/test_boxes.py -q; test_iou_disjoint and test_iou_touching_edge fail first; full suite green (pytest -q).
Facts: tracker/boxes.py:41 computes the overlap w and h without clamping them at 0 (explorer).
       Repro: iou([0,0,1,1], [2,2,3,3]) returns 1.0. Baseline: 212 passed.
Files: tracker/boxes.py, tests/test_boxes.py.
Constraints: boxes stay xyxy float32; no new dependency; project rule .claude/rules/python-style.md.
Ruled out: none.
Mode: fix
```

A diagnose brief keeps the same fields with `Mode: diagnose`; `Done when` is then "a failing test that reproduces it
and the cause with `path:line`". Use it to split a Hard bug: `opus` finds the cause, a `sonnet` engineer writes the
fix from the diagnosis.

## Handling what comes back

| Came back | Do |
| --- | --- |
| Done, checks pass | Rerun `Done when` yourself, `git diff --stat`; then review by risk |
| Done, a gap (file outside `Files`, no red run, a missing field) | SendMessage the same agent for the gap |
| Blocked, `Need:` a fact or file | Get it (explorer or you), SendMessage the same agent |
| Blocked, `Need:` a decision that changes scope | Ask the user |
| Failed, brief problem (wrong file, missing fact, bad command, environment) | Fix the brief, same model |
| Failed, reasoning (fix did not hold, evidence contradicts) | One level up, the attempt under `Ruled out` |

Continuing an agent with SendMessage keeps what it has read and costs far less than a fresh call. Without it, start
a new call with the earlier report pasted into `Facts`. At most three engineer attempts per package.

## Rules

- One concern per agent. A plan with a test, a fix and a review is three calls, in order.
- One package is one behaviour and its tests, a few files at most. Split bigger work; keep dependent parts in order.
- Independent means: no shared files and no output used as another's input. Only those run in parallel, at most
  three engineers at a time, each with `isolation: worktree`.
- The reviewer never sees the author's reasoning or findings first; it gets the diff, the test output and the rules.
- Read-only work (`explorer`, `reviewer`) cannot edit; only `engineer` writes code, and it follows the red, green,
  refactor loop in the tests references.
- Do not use `max` effort; the docs warn it overthinks.
- To see which model ran, open the subagent in `/tasks`, or press Ctrl+O to show the model on each message.
- A returned result is a claim. Rerun the test or command it names before you rely on it.
