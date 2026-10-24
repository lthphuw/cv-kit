# cv-kit trigger evals

A small `claude plugin eval` suite that checks which cv-kit skill Claude picks for a request, and that it
picks none when the request is not for cv-kit. Twenty-two cases: each model-invocable skill has at least one case
where it must fire and one where it must not, plus confusable pairs and two off-topic requests. Eleven cases also
check one rule of the skill's first reply.

The suite runs by hand before a release, not in CI (see "Why not in CI"). `tests/test_evals.py` checks the
files offline on every run of the test suite.

## Coverage

| Skill | Must fire in | Must not fire in |
| --- | --- | --- |
| `develop` | 01 (feature), 02 (C++ bug), 03 (refactor), 21, 22 (routing) | 11 (a review request) |
| `research` | 04, 05, 06, 07 (one benchmark claim), 08 (image embeddings), 10 (clone and compare) | 09 (text-only search) |
| `review` | 11 | 03 (a refactor request) |
| `commit` | 12 | 13 (release notes) |
| `figure` | 14, 15 (model v1 vs v2) | 16 (a matplotlib plot) |
| `setup` | never (user-invoked only) | 17, 18 |
| any cv-kit skill | | 19, 20 |

Behaviour graders: 01 (a failing pytest test comes before the code), 02 (a GoogleTest reproduction and the root
cause come before the fix), 03 (pins behaviour before changing code, and keeps file order, BGR, dtype and the
shared cache unless asked), 04 (every named model carries a licence; no benchmark number from memory), 06 (asks
for the brief; no number from memory), 07 (does not settle the claim from memory), 10 (clones into
`research/<slug>/`, records the commit, runs nothing from the clone), 11 (findings carry a severity and a `CPP-`
rule ID, and the throw, detached thread, race or leak is Critical), 12 (no trailer in the suggested message),
14 (says the code is missing instead of inventing the architecture).

Cases 21 and 22 grant the `Agent` tool and check routing: which agent is dispatched and with which `model`. They
run read-only, so the dispatched agent cannot edit; the check is on the call. Confirm the model that actually ran
with `/tasks` in a live session. Eval runs load no `.claude/` folder or `CLAUDE.md`, so rules installed by `setup`
are not active in them.

## Layout

```
evals/
  NN-<skill or off-topic>-<fire|nofire>-<slug>/
    prompt.md          frontmatter: run limits and tools; body: the request
    graders/
      <skill>-fired.md        tool_used: the Skill tool was called with this skill
      <skill>-not-called.md   tool_used with min 0, max 0, arm both: never called
      no-cv-kit-skill.md      no cv-kit skill was called
      <rule>.md               an llm rubric or a regex on the final reply
  results/             written by each run; git-ignored
```

Every run starts in an empty folder with only `Read`, `Glob`, `Grep` and `Skill`: no web, no Bash, no writes.
The cases therefore measure routing and the first reply, not a full research run or a built figure.

## Run it

From the repository root, with Claude Code 2.1.269 or later:

```
claude plugin eval . --ablation none --model <model to release against> --judge-model sonnet \
  --no-publish --max-cost-usd <ceiling>
```

- `--ablation none` runs only the with-plugin arm. Under the default two-arm mode, `<skill>-fired` graders are
  shown as indicators and left out of the score, so use one arm to measure trigger rates. Add the no-plugin arm
  (`--ablation with-without`) only to see what the plugin adds to the behaviour graders.
- `--model` pins the model under test, so a model rollout is not read as a plugin change.
- `--judge-model sonnet` grades the six `llm` rubrics with a larger judge than the default.
- `--no-publish` keeps the HTML report local. Without it the report is published to claude.ai when the account
  allows it.
- `--max-cost-usd` stops starting new runs once the estimate passes the ceiling (exit 2, partial results). The
  cost of a full run of this suite has not been measured yet; set a low ceiling for the first run.
- Each case runs three times. A case passes only when every grader passes in every run (the default
  `--threshold` is 1.0); read the per-case scores, not only the exit code.
- To try one case once: `claude plugin eval . --case 05-* --runs 1 --ablation none --no-publish`.
- The first run in this directory asks whether to trust it.

## Why not in CI

Every run and every judge call is a real model call billed to the account that runs it, CI would need model
credentials, and scores vary between runs and between models. The offline test (`tests/test_evals.py`) runs in
CI instead: it checks frontmatter keys and grader types against the documented format, that every skill has a
fire and a no-fire case, that each skill pattern matches its own skill and no other, and that every regex
compiles under Node's `RegExp`, which the eval runner uses.

## Adding a case

Name the folder `NN-<skill or off-topic>-<fire|nofire>-<slug>` and give it the matching `<skill>-fired` or
`<skill>-not-called` grader. Write the prompt the way a CV engineer would type it, without naming the skill.
Write an `llm` rubric as numbered points the judge checks against quoted words of the reply, then a PASS and a
FAIL line. A new `regex` grader needs sample strings in `REGEX_SAMPLES` in `tests/test_evals.py`.

## Format source

The case and grader format follows the Claude Code documentation page "Test plugins with evals"
(`https://code.claude.com/docs/en/plugin-evals.md`) and `claude plugin eval --help`, both checked on 2026-10-15
with Claude Code 2.1.300.
