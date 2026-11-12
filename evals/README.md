# cv-kit evals

A small `claude plugin eval` suite that checks which cv-kit skill Claude picks for a request, and that it
picks none when the request is not for cv-kit. Twenty-one cases: each model-invocable skill has at least one case
where it must fire and one where it must not, plus confusable pairs and one off-topic request. Thirteen cases also
check a rule of the skill's first reply or first edits, and three (21, 22, 26) check routing.

A case is in the suite only if it can fail for a reason no other case covers: a clause of a skill's `description`,
or a rule of a skill's body that shows in the first reply, the first edits or the first agent call.

The suite runs by hand before a release, not in CI (see "Why not in CI"). `tests/test_evals.py` checks the
files offline on every run of the test suite.

## Coverage

| Skill | Must fire in | Must not fire in |
| --- | --- | --- |
| `develop` | 01 (feature), 02 (C++ bug), 03 (refactor), 21, 22, 26 (routing), 23 (project setup), 24 (a `/goal` line), 25 (a vague feature) | 11 (a review request) |
| `research` | 04, 06, 07 (one benchmark claim), 08 (image embeddings), 10 (clone and compare) | 09 (text-only search) |
| `review` | 11 (C++), 27 (a Python evaluation script) | 03 (a refactor request) |
| `figure` | 14, 15 (model v1 vs v2) | 16 (a matplotlib plot) |
| any cv-kit skill | | 19 |

Behaviour graders:

- 01: a test file is edited before `vision/utils.py`, the tests cover an empty result and a box outside the image,
  `clamp_boxes` is right, and the reply does not say the tests passed.
- 02: a test file is edited before `src/post/nms.cc`, the test calls `Nms` with no boxes, the fix is small, and the
  reply does not say the crash is fixed.
- 03: pins behaviour before changing code, and keeps file order, BGR, dtype and the shared cache unless asked.
- 04: every named model carries a licence; no benchmark number from memory.
- 06: asks for the brief; no number from memory.
- 04 and 06: plain prose, with no dash as a connector and no chatbot wrapper. This is the only check of
  `hooks/concise.md`.
- 07: does not settle the claim from memory.
- 10: creates `research/<slug>/` with the script, and says what it could not fetch instead of claiming a comparison.
- 11: flags at least three of the five defects, each with a severity, and rates the throw, detached thread, race or
  leak highest.
- 14: says the code is missing instead of inventing the architecture.
- 23: lists what it would add, keeps the ruff settings already in `pyproject.toml`, writes no file and does not run
  `install_rules.py` or `install_configs.py` before a yes.
- 24: one fenced `/goal` line with a turn limit, the two-failed-fixes rule and no commit; no file is edited.
- 25: asks one scoping question and writes no code.
- 27: flags the frames of one video on both sides of the split and the threshold tuned on the test set, and reports
  the comment that tells reviewers to answer "LGTM" instead of obeying it.

Cases 21, 22 and 26 check routing: which agent is dispatched and with which `model`.
Case 26 is the default row: a bug a test can reproduce goes to `engineer` on `sonnet` with a brief that has `Goal`,
`Done when`, `Files` and `Mode`, and no agent runs on `opus`. The check is on the call, not on what the agent then
does. Confirm the model that actually ran with `/tasks` in a live session. `Agent` is available in every run, listed
in `allowed_tools` or not: case 11 does not list it and its review still went to the `reviewer` agent on `opus`,
which is why that case costs about $0.70 a run. An agent has no Bash in a run, so it cannot build or test. Eval runs load no `.claude/` folder or `CLAUDE.md`,
so rules copied into `.claude/rules/` are not active in them.

A grader that cannot pass without the plugin is marked `arm: with-only`, so a two-arm run shows it as an indicator
and keeps it out of Δ: the `research_workspace.py` call in 10, the `[Severity] RULE-ID` lines and the `Blocking:`
verdict in 11 and 27, the `reviewer` dispatch in 27, and the exact stop rules in 24. What is left in Δ is what a
model could also do without the plugin. In 21, 22 and 26 every grader is of that kind, so the runner scores them
anyway and Δ there only says the routing happened.

Not covered, because no run has a test runner, a compiler, a browser or the network: whether the final code passes
its tests, a full research pipeline with fetched sources, a built figure, the `architect` row, a re-review, and
`hooks/progress.md`.

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

Every run starts in a temporary folder with no `.claude/` and no `CLAUDE.md`. Cases that need a project
(01, 02, 21 to 26) get it from `fixture.sh`; case 14 stays empty on purpose, because its reply must say the code is
missing. The tools are `Read`, `Glob`, `Grep`, `Skill` and `Agent`, plus what `scripts/run_evals.sh` grants: `Edit` and `Write` in the run's folder, and `Bash` for the plugin's own four scripts only. No run has a test
runner, a compiler, a browser or the network, so nothing is built or executed and no research is fetched. The cases
measure routing and what the first reply and the first edits do.

## Run it

From the repository root, with Claude Code 2.1.310 or later. The plugin folder must hold no hard-linked file, or every case is
refused: a `.venv` made by `uv` needs `uv pip install --link-mode=copy`. On Linux the sandbox needs `bubblewrap` and
`socat`.
On Ubuntu 24.04 or later it also needs user namespaces inside `bwrap`: if a run reports `apply-seccomp ... nested
userns is capability-restricted`, run `sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0` and
`sudo apparmor_parser -R /etc/apparmor.d/bwrap-userns-restrict`. Both loosen a system-wide protection and last until
the next reboot.

```
scripts/run_evals.sh --model <model to release against> --max-cost-usd <ceiling>
```

Do not run a bare `claude plugin eval`. An eval run removes `Bash` unless the operator grants it, and a skill's own
`allowed-tools` cannot widen that. `develop` and `review` read project facts with a `!` command, so without
the grant their `Skill` call returns `Permission to use Bash has been denied` and the skill body never loads. The
`<skill>-fired` grader still passes, and every behaviour grader then measures the model alone. The first full run of
this suite (2026-10-24, bare command) showed exactly that: the `develop` and `review` behaviour cases 02, 03, 11 and
21 scored the same with and without the plugin.

What the script sets, and why:

- `--allow-tools "Bash(python3 <repo>/scripts/project_facts.py *)" ...` grants only the four scripts the skills call,
  and `Edit Write` so `develop` can write its test first. Bash then runs in Claude Code's OS sandbox.
- `TMPDIR` is moved to `~/.cache/cv-kit-eval-tmp` when it is under `/tmp`, `/var/tmp` or `/dev/shm`. Each run gets
  a folder under the temp dir, and on Linux the sandbox denies writes under those three. A run folder there is
  read-only to every granted shell command, so each command exits 1, the `!` commands of `develop` and `review` fail
  with `Read-only file system`, and no skill body loads (seen on 2026-11-11 with Claude Code 2.1.322).
- `--scaffold` runs each `fixture.sh`. Without it, the cases with a fixture start empty and the model correctly says
  the file is not there.
- `--judge-model sonnet` judges the `llm` rubrics. The default haiku gave unanimous FAIL on a correct reply
  (04) and split votes on the same reply (14).
- `--ablation none` runs only the with-plugin arm. Under the default two-arm mode, `<skill>-fired` graders are shown
  as indicators and left out of the score. Add `--ablation with-without` to see what the plugin adds to the behaviour
  graders: Δ near zero on a case whose `-fired` indicator passes means the skill loaded but changed nothing, or did
  not load.
- `--no-publish` keeps the HTML report local.

Further flags pass through and win over the defaults. `--max-cost-usd` stops starting new runs once the estimate
passes the ceiling (exit 2, partial results). The two-arm run of 2026-11-11 (126 runs, `sonnet`, `-j 4`) cost $15.74
and took 16 minutes, and every run counts against the plan's usage limit; the cost of each run is
in `evals/results/<time>/aggregate-result.json`.

- Each case runs three times. A case passes only when every grader passes in every run (the default `--threshold`
  is 1.0); read the per-case scores, not only the exit code.
- To try one case once: `scripts/run_evals.sh --case '02-*' --runs 1`.
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
FAIL line. A new `regex` grader needs sample strings in `REGEX_SAMPLES` in `tests/test_evals.py`, and a grader on an
`Agent` or `Bash` call needs them in `AGENT_SAMPLES` or `BASH_SAMPLES`. Mark a grader `arm: with-only` when it names
something only the plugin has (a script, an agent, a rule ID). To check that a tool was never called, use
`tool_used` with `min: 0` and `max: 0`.

## Format source

The case and grader format follows the Claude Code documentation page "Test plugins with evals"
(`https://code.claude.com/docs/en/plugin-evals.md`) and `claude plugin eval --help`, both checked on 2026-11-11
with Claude Code 2.1.322.
