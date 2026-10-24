# Unattended runs: /goal and /loop

`/goal` is a built-in command, and `/loop` is a bundled skill that ends a stack of skills, so neither is stacked
with a cv-kit skill in one message. Name the skill in the condition or prompt, or run the skill first and set the goal
afterwards.

## /goal: work until a check passes

A model judges the condition after every turn from the transcript alone; it does not run commands or read files. So
a good condition has one measurable end state, the command that proves it, constraints, and a turn limit (up to
4,000 characters). Run it in auto mode to avoid per-tool prompts. Examples:

```
/goal follow /cv-kit:develop. clamp_boxes in vision/utils.py clips xyxy boxes and drops empty ones; a new pytest test for it failed first, then `pytest -q` exits 0 and `ruff check .` is clean; no other test file changes. Print both outputs. Do not commit. Or stop after 15 turns.

/goal follow /cv-kit:develop. NMS in src/post/nms.cc handles zero detections: a new GoogleTest test fails first, then `ctest --test-dir build --output-on-failure` exits 0 with no other test changed. Print the ctest summary. Do not commit. Or stop after 20 turns.

/goal follow /cv-kit:review. Review the diff against main; end with the line `Blocking: N Critical, M Major` and every finding carrying a rule ID and a path:line. Change no file. Or stop after 10 turns.

/goal follow /cv-kit:research. research/small-objects/report.md exists, its claims.json passes `lint_research.py --checks checks.json --report report.md`, and every number cites a saved source. Run nothing from a clone. Or stop after 30 turns.
```

Keep tests in the foreground: a background run defers the judge's check.

## /loop: repeat on a schedule

`/loop [interval] [prompt]` re-runs a prompt while the session stays open; with no interval Claude paces itself and
can end the loop. It runs skills the model may invoke, so `/cv-kit:setup` (manual only) arrives as plain text.

```
/loop 30m /cv-kit:review the diff against main, report only new Critical or Major findings
/loop 10m run `pytest -q` and `ctest --test-dir build`; if either fails, find the root cause with /cv-kit:develop and stop to report it
```

A loop that only watches should say so ("report, change nothing"); a loop that edits files needs a clean tree or a
git checkpoint first, because rewind does not restore a subagent's edits.
