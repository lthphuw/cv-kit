# cv-kit

A Claude Code plugin for computer-vision engineers who write Python, edge C++ and Go.

**One prompt → agents sized to the task → tested code, sourced numbers, strict review, clean commits.**

```
┌──────────┐    ┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────────────┐
│  prompt  │───►│      skill      │───►│        agents        │───►│         result          │
│  plain   │    │ develop  review │    │ explorer   engineer  │    │ green tests + output    │
│  words   │    │ research figure │    │ researcher reviewer  │    │ report, claims checked  │
│          │    │ commit   setup  │    │ claim-verifier       │    │ findings · figure       │
└──────────┘    └─────────────────┘    └──────────────────────┘    └────────────┬────────────┘
     ▲                                                                          │
     └──────────────────────────── Next: prompts to paste ◄─────────────────────┘

hooks, every turn: concise replies · no "done" without a green test · no AI trailers · live rows
```

## Install

```
/plugin marketplace add lthphuw/cv-kit
/plugin install cv-kit@cv-kit
/cv-kit:setup python                  # once per project: python | cpp | both

/plugin marketplace update cv-kit     # update
/reload-plugins
```

Needs Claude Code ≥ 2.1.295 and `python3`. `figure` also needs Python ≥ 3.10 and Chrome or Chromium (`CHROME=` if not
on PATH; not the snap build, it cannot read `/tmp`).

## Skills

Name a skill, or just describe the work: "NMS crashes on empty input" loads `develop`.

| Kind | Name | Example prompt | You get |
|:-----|:-----|:---------------|:--------|
| Skill | `develop` | `NMS in src/post/nms.cc crashes on zero detections` | failing test → fix → literal `ctest` output |
| Skill | `research` | `which detector for 30 FPS on Orin NX, Apache-2.0` | short report, every number re-checked |
| Skill | `review` | `train/val split in data/split.py, any leakage?` | `[Severity] RULE-ID path:line` findings → `Blocking: N Critical, M Major` |
| Skill | `figure` | `low-level figure with tensor shapes for the neck and head` | HTML + PNG (SVG for papers), unconfirmed facts labelled |
| Skill | `commit` | `/cv-kit:commit` | preview → your yes → commit without trailers |
| Skill | `setup` | `/cv-kit:setup cpp` | `.claude/rules/` + lint configs, existing files kept |

## Agents

You never pick an agent: the skill does, sizing model and effort to the task.

| Kind | Name | Model · effort | Job |
|:-----|:-----|:---------------|:----|
| Agent | `explorer` | haiku `▰▱▱▱▱` | find and summarise code, logs, docs · read-only |
| Agent | `engineer` | sonnet `▰▰▱▱▱` · hard: opus `▰▰▰▱▱` | one change, test first |
| Agent | `researcher` | sonnet `▰▰▰▱▱` | sourced evidence for one candidate model |
| Agent | `claim-verifier` | haiku `▰▰▱▱▱` | re-reads each source, blind to the claimed value |
| Agent | `reviewer` | opus `▰▰▰▱▱` · routine: sonnet `▰▰▱▱▱` | read-only review |
| Agent | `lead` | opus `▰▰▰▱▱` | main thread, only delegates |

Effort: `▰▱▱▱▱` low · `▰▰▱▱▱` medium · `▰▰▰▱▱` high · `▰▰▰▰▱` xhigh · `▰▰▰▰▰` max

### Routing by difficulty

```
                               how hard is the task?
          ┌──────────────────────────────┼──────────────────────────────┐
          ▼                              ▼                              ▼
         read                         ordinary                         hard
   find · summarise             feature · fix · test          unclear bug · threads
          │                              │                  numerics · perf · security
          │                              │                              │
          ▼                              ▼                              ▼
   explorer  haiku                engineer  sonnet                engineer  opus
      ▰▱▱▱▱ low                     ▰▰▱▱▱ medium                    ▰▰▰▱▱ high
                                         │                              │
                                         ▼                              ▼
                                  reviewer  sonnet                reviewer  opus
                                    ▰▰▱▱▱ medium                    ▰▰▰▱▱ high

attempt failed? ──► one level up: sonnet ▰▰▱▱▱ ──► opus ▰▰▰▱▱ ──► opus ▰▰▰▰▱ xhigh
                    never the same prompt twice
```

### Lead mode: `claude --agent cv-kit:lead`

```
                            lead · opus ▰▰▰▱▱
                   loads the skill, never edits a file
      ┌──────────────┬──────────────┼───────────────┬───────────────┐
      ▼              ▼              ▼               ▼               ▼
   explorer       engineer      researcher    claim-verifier     reviewer
    reads          edits         evidence       re-checks        reviews
      │              │              │               │               │
      └──────────────┴──────────────┼───────────────┴───────────────┘
                                    ▼
       each result is a claim: lead reruns the named command first
```

## Flows

### `/cv-kit:develop`

```
/cv-kit:develop add iou(a, b) and clamp(box, w, h) to vision/
  │
  ├─ 1 SIZE ──── one-liner? ─┬─ yes ─► do it inline, then 4
  │                          └─ no ──► one question at a time ─► brief ─► your yes
  │
  ├─ 2 LOOK ──── project rules · test setup · baseline test run          explorer
  │
  ├─ 3 BUILD ─── ┌─────┐    ┌───────┐    ┌──────────┐                    engineer × N
  │              │ red │───►│ green │───►│ refactor │                    in parallel,
  │              └─────┘    └───────┘    └──────────┘                    one per file set
  │
  ├─ 4 VERIFY ── tests + linters ─► review by risk                       reviewer
  │
  └─ 5 REPORT ── cause at path:line · tests by name · literal command output
```

### `/cv-kit:research`

```
/cv-kit:research which detector for 30 FPS on a Jetson Orin NX, Apache-2.0 only
  │
  ├─ 1 FRAME ──────── brief.md: task · metric · split · hardware · latency · licence
  ├─ 2 SCOUT ──────── arXiv · HF Papers · CVF · GitHub ─► one line per candidate
  ├─ 3 SHORTLIST ──── cut by licence ─► task ─► weights ─► traceable numbers ─► stack
  │                   ─► your yes (≤ 6 go on)
  ├─ 4 DEEP-READ ──── researcher   researcher   researcher               one per candidate,
  │                    model A      model B      model C                 in parallel
  ├─ 5 CROSS-CHECK ── claim-verifier re-reads every source without seeing the claimed value
  └─ 6 REPORT ─────── research/<slug>/report.md     overview · ≤ 7 points · table · ≤ 3 next steps
                      research/<slug>/appendix.md   exclusions · caveats · claims ledger · sources

one claim to check? ─► steps 4–5 only ─► confirmed | partly right | contradicted | not found
```

### `/cv-kit:review`

```
/cv-kit:review the diff against main
  │
  ├─ 1 SCOPE ──── paths · uncommitted diff · branch vs base · pull request
  ├─ 2 TOOLS ──── ruff · mypy · clang-format · clang-tidy · build · tests   (only those installed)
  ├─ 3 REVIEW ─── reviewer opus ▰▰▰▱▱   xhigh for concurrency, memory safety, published numbers
  │               large diff ─► one reviewer per directory, in parallel
  ├─ 4 REPORT ─── [Critical] CPP-ERR-8 src/infer/engine.cc:88 ─► What · Trigger · Fix
  │               Blocking: 1 Critical, 0 Major
  └─ 5 FIX ────── only after your yes: mechanical directly, structural through develop

in CI: claude -p "/cv-kit:review the diff against origin/main"
```

### `/cv-kit:figure` and `/cv-kit:commit`

```
figure   read code + configs ─► ask what changes the figure ─► HTML ─► PNG ─► look at it ─► report
         modes: high-level · low-level · pipeline · whole model · delta between two versions

commit   branch + files + message ─► STOP ─► your yes ─► git / svn commit
                                                              ▲
                                      block_trailers.py ──────┘  refuses AI trailers
```

## What you see

```
while agents run: one live row each, refreshed about every 5 s

  ● engineer  sonnet  ▰▰▱▱▱  1m42s  18k  Add iou with tests
  │ │         │       │      │      │    └─ task
  │ │         │       │      │      └─ tokens
  │ │         │       │      └─ elapsed (running rows only)
  │ │         │       └─ effort
  │ │         └─ model
  │ └─ agent
  └─ ● running   ✓ done   ✗ failed   ■ killed      (finished rows fade)

when one finishes                      at the end
  ● Progress (1/2 done):                 ● Summarization:
    - engineer#1 iou: 5 tests pass         - iou in vision/utils.py, tests in tests/test_iou.py
    - engineer#2 clamp: running            - pytest -q: 9 passed
                                           - Nothing is committed.
                                           Next:
                                           - /cv-kit:review the diff against main
                                           - /cv-kit:commit
```

`research` prints only its Overview, the report path and `Next:`.

## Autonomous runs

`/goal <condition>` runs until a judge model says it holds; `/loop [interval] <prompt>` repeats. Use auto mode.

```
/goal follow /cv-kit:develop … Or stop after 25 turns.
  │
  ├─ turn 1      develop: brief from the condition, baseline tests
  ├─ turn 2..n   engineer: failing test ─► fix ─► green        Progress per agent
  ├─ turn n+1    reviewer: Blocking: 0 Critical, 0 Major
  ├─ turn n+2    commit: preview ─► your yes                    only if the condition says commit
  ├─ turn n+3    git push · gh pr create                        only if it says push
  └─ end         judge reads the literal test output ─► met, or stop at the turn limit
```

Change → pull request:

```
/goal follow /cv-kit:develop. clamp_boxes in vision/utils.py clips xyxy boxes and drops empty ones; a new pytest test failed first, then `pytest -q` exits 0 and `ruff check .` is clean. Then /cv-kit:review the diff against main until it ends with `Blocking: 0 Critical, 0 Major`. Then /cv-kit:commit, push the branch and open a PR with `gh pr create`. Print each output. Or stop after 25 turns.
```

Watch a branch, change nothing:

```
/loop 15m first run `test -f .cv-kit-stop` and stop if it exists; otherwise /cv-kit:review the diff against main, report only new Critical or Major findings, change nothing
```

| Guard | Effect |
|:------|:-------|
| no "commit" / "push" in the condition | never commits or pushes |
| `/cv-kit:commit` | still shows its preview |
| `permissions.ask` from `/cv-kit:setup` | `git commit`, `git push`, `gh pr create` still prompt, even in auto mode |
| two failed fixes | stops and reports the evidence |
| `touch .cv-kit-stop` | halts the loop above |

Draft one: `/cv-kit:develop write the /goal line for the NMS crash`. Templates:
`skills/develop/references/goal-loop-templates.md`.

## Hooks

```
SessionStart          PreToolUse: Bash       PostToolUse: edit, Bash      Stop
──────┬─────────────────────┬──────────────────────────┬─────────────────────┬──────────►
      ▼                     ▼                          ▼                     ▼
concise.py            block_trailers.py        evidence_gate.py        evidence_gate.py
short replies,        refuses a commit         code edit ─► stale      stale? hold the
STATUS / Progress /   with an AI trailer       green test ─► fresh     turn, once
Next blocks
agent_status.py
live rows
```

Details and known gaps: `hooks/README.md`.

## Configuration

| What | Where | How |
|:-----|:------|:----|
| Rules, lint configs | `/cv-kit:setup` | never overwrites; refresh: `python3 scripts/install_rules.py <project> --force` |
| Models | `model:` in `agents/*.md` | aliases `haiku` `sonnet` `opus`, or a full model ID to pin |
| Concise mode, Progress, Next | `hooks/hooks.json` | remove the two `concise.py` entries to turn off |
| Evidence ledger | `~/.cache/cv-kit/gate/` | move with `CV_KIT_GATE_DIR` |
| Live rows | plugin `settings.json` | your own `subagentStatusLine` wins; `NO_COLOR=1` drops colour |

Lint configs tested with ruff 0.17.2, mypy 2.4.0, clang-format and clang-tidy 23.1.3, CMake 4.4, GCC 13.3.

## Limitations

- Evidence gate: a nudge, it cannot tell the right tests ran.
- Commit hook: gaps such as `--amend --no-edit` and `bash -c` (`hooks/README.md`).
- Live rows: need the SessionStart hook (`${CLAUDE_PLUGIN_ROOT}` is empty in `subagentStatusLine`, Claude Code
  2.1.317); off in untrusted folders and under `disableAllHooks`.
- Progress, Summarization, Next: model-written, one can be skipped.
- Catalogue rows marked `UNVERIFIED` are unchecked; licences change.
- No training, benchmark harness or hardware measurement: you run those.
- Cost: `lead` and `reviewer` run on Opus; the eval suite calls the API (run by hand).

## Development

```
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python scripts/validate_plugin.py
.venv/bin/python -m pytest tests -q
claude plugin validate . --strict
```

CI runs the same. Change the plugin test first; run `scripts/run_evals.sh` before a release. Reference material:
`shared/`, `hooks/README.md`, `evals/README.md`, `docs/research/`.

## Licence

MIT, see `LICENSE`. Catalogued models carry their own licences; check them before use.

- Style catalogues: paraphrase the Google Python and C++ Style Guides (CC BY 3.0), ideas from the C++ Core Guidelines,
  pitfalls from methylDragon's coding notes (BSD-2-Clause).
- Go catalogue: the Go documentation (BSD-3-Clause; CC BY 4.0 for site pages), uber-go guide (Apache-2.0), goleak
  (MIT, test only).
- `figure` bundles rough.js 4.6.6 (MIT) and the Patrick Hand font (SIL OFL 1.1).
- The research report format is adapted from FOCUS (skill-focus, MIT); concise mode from ponytail (MIT).
