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

Behaviour graders: 01 (a test file is edited before `vision/utils.py`, and the tests cover an empty result and a box
outside the image), 02 (a test file is edited before `src/post/nms.cc`, and the reply names the cause it read), 03 (pins behaviour before changing code, and keeps file order, BGR, dtype and the
shared cache unless asked), 04 (every named model carries a licence; no benchmark number from memory), 06 (asks
for the brief; no number from memory), 07 (does not settle the claim from memory), 10 (clones into
`research/<slug>/`, records the commit, runs nothing from the clone), 11 (findings carry a severity and a `CPP-`
rule ID, and the throw, detached thread, race or leak is Critical), 12 (no trailer in the suggested message),
14 (says the code is missing instead of inventing the architecture).

Cases 21 and 22 grant the `Agent` tool and check routing: which agent is dispatched and with which `model`. The
check is on the call, not on what the agent then does. Confirm the model that actually ran
with `/tasks` in a live session. Eval runs load no `.claude/` folder or `CLAUDE.md`, so rules installed by `setup`
are not active in them.

## Layout

```
evals/
  NN-<skill or off-topic>-<fire|nofire>-<slug>/
    prompt.md          frontmatter: run limits and tools; body: the request
    case.yaml          only when the prompt names files: points at fixture.sh
    fixture.sh         writes those files into the empty workspace (runs with --scaffold)
    graders/
      <skill>-fired.md        tool_used: the Skill tool was called with this skill
      <skill>-not-called.md   tool_used with min 0, max 0, arm both: never called
      no-cv-kit-skill.md      no cv-kit skill was called
      <rule>.md               an llm rubric on the final reply, or a regex on the final reply or the trace
  results/             written by each run; git-ignored
```

Every run starts in a temporary folder with no `.claude/` and no `CLAUDE.md`. Cases whose prompt names files
(01, 02, 21, 22) get them from `fixture.sh`; case 14 stays empty on purpose, because its reply must say the code is
missing. The tools are `Read`, `Glob`, `Grep`, `Skill` and, in 21 and 22, `Agent`, plus what `scripts/run_evals.sh`
grants: `Edit` and `Write` in the run's folder, and `Bash` for the plugin's own four scripts only. No run has a test
runner, a compiler, a browser or the network, so nothing is built or executed and no research is fetched. The cases
measure routing and what the first reply and the first edits do.

## Run it

From the repository root, with Claude Code 2.1.310 or later:

```
scripts/run_evals.sh --model <model to release against> --max-cost-usd <ceiling>
```

Do not run a bare `claude plugin eval`. An eval run removes `Bash` unless the operator grants it, and a skill's own
`allowed-tools` cannot widen that. `develop`, `review` and `commit` read project facts with a `!` command, so without
the grant their `Skill` call returns `Permission to use Bash has been denied` and the skill body never loads. The
`<skill>-fired` grader still passes, and every behaviour grader then measures the model alone. The first full run of
this suite (2026-10-24, bare command) showed exactly that: the `develop` and `review` behaviour cases 02, 03, 11 and
21 scored the same with and without the plugin.

What the script sets, and why:

- `--allow-tools "Bash(python3 <repo>/scripts/project_facts.py *)" ...` grants only the four scripts the skills call,
  and `Edit Write` so `develop` can write its test first. Bash then runs in Claude Code's OS sandbox.
- `--scaffold` runs each `fixture.sh`. Without it, cases 01, 02, 21 and 22 start empty and the model correctly says
  the file is not there.
- `--judge-model sonnet` judges the six `llm` rubrics. The default haiku gave unanimous FAIL on a correct reply
  (04) and split votes on the same reply (14).
- `--ablation none` runs only the with-plugin arm. Under the default two-arm mode, `<skill>-fired` graders are shown
  as indicators and left out of the score. Add `--ablation with-without` to see what the plugin adds to the behaviour
  graders: Δ near zero on a case whose `-fired` indicator passes means the skill loaded but changed nothing, or did
  not load.
- `--no-publish` keeps the HTML report local.

Further flags pass through and win over the defaults. `--max-cost-usd` stops starting new runs once the estimate
passes the ceiling (exit 2, partial results). The first two-arm run (132 runs) cost $15.21; the cost of each run is
in `evals/results/<time>/aggregate-result.json`.

- Each case runs three times. A case passes only when every grader passes in every run (the default `--threshold`
  is 1.0); read the per-case scores, not only the exit code.
- To try one case once: `scripts/run_evals.sh --case '05-*' --runs 1`.
- To read what a run did, add `--keep-temp` and open the `trace.jsonl` it prints. A `Skill` result with
  `is_error: true` is a skill that did not load.
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
