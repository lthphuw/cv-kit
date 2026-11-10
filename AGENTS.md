# Guide for agents and contributors

How to change cv-kit without breaking the plugin or its prompts.

## What is where

- `skills/*/SKILL.md` and `agents/*.md` are the prompts. Every word is read on each use, so a change that adds words
  must earn them.
- `hooks/concise.md` and `hooks/progress.md` are injected into every session (and `concise.md` into every subagent).
  `tests/test_concise_hook.py` caps them at 2,200 and 1,200 characters.
- `rules/` is copied into a project's `.claude/rules/` by `/cv-kit:setup`; a plugin cannot ship rules directly.
- `shared/` holds the catalogues the prompts point at. `shared/prose.md` is the one source for writing style; the
  regex part of it lives in `PROSE_TELLS` in `scripts/lint_research.py`. Change both together.
- `evals/` holds the trigger and behaviour cases; `evals/README.md` explains the format.

## Rules for changes

- Test first. Change or add the test in `tests/`, watch it fail, then change the prompt or script.
- Keep the README skill table, `evals/README.md` coverage and the files in sync; `scripts/validate_plugin.py` checks
  the README table.
- A new or removed skill needs its fire and no-fire eval cases added or removed; `tests/test_evals.py` checks it.
- A new regex grader needs sample strings in `REGEX_SAMPLES`.
- Credit any project an idea came from in the README's Acknowledgements, with its licence. Write the rule in our own
  words; copy nothing from a non-commercial source.
- Commits follow `rules/commit-vcs.md`.

## Checks before publishing

```
.venv/bin/python scripts/validate_plugin.py
.venv/bin/python -m pytest tests -q
claude plugin validate . --strict
```

Run `scripts/run_evals.sh` before a release; it calls the API and costs money.

## Writing style

Prompts, docs, comments and messages follow `shared/prose.md`. In short:

- Lead with the main point. Use common words, active voice, short sentences.
- Use one term for one thing, and `must` for a requirement.
- Keep exact identifiers, commands, paths, numbers and quotes.
- No em or en dashes in prose, no bold label on every list item, no closing line that repeats the paragraph.
