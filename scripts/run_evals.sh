#!/usr/bin/env bash
# Run the trigger evals with the grants they need. Extra arguments go to `claude plugin eval` and win over the defaults:
#
#   scripts/run_evals.sh --max-cost-usd 5
#   scripts/run_evals.sh --case '02-*' --runs 1 --keep-temp
#
# Why each flag is here (see evals/README.md, "Run it"):
#   --allow-tools  eval runs remove Bash unless the operator grants it, and a skill's own `allowed-tools` cannot widen
#                  that. develop, review and commit read their project facts with a `!` command; without the grant the
#                  Skill call returns "Permission to use Bash has been denied" and the skill body never loads.
#                  Only the plugin's own scripts are granted, and Bash then runs inside the OS sandbox.
#                  Edit and Write are granted so develop can write its test first; the run's workspace is a temp folder.
#                  No test runner, compiler or network is granted, so no run builds or executes anything.
#   --scaffold     runs each case's fixture.sh, which writes the files the prompt names (cases 01, 02, 21, 22).
#   --judge-model  the six llm rubrics are judged by sonnet; the default haiku flips on the same reply.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

claude plugin eval . \
  --ablation none --judge-model sonnet --no-publish --scaffold \
  --allow-tools Edit Write \
  "Bash(python3 $root/scripts/project_facts.py *)" \
  "Bash(python3 $root/hooks/evidence_gate.py *)" \
  "Bash(python3 $root/scripts/research_workspace.py *)" \
  "Bash(python3 $root/scripts/lint_research.py *)" \
  "$@"
