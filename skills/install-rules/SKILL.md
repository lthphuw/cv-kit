---
name: install-rules
description: Use when the user asks to install cv-kit's rules (commit format, licence callouts, verified ids, pinned revisions) into the current project.
disable-model-invocation: true
---

# Install cv-kit rules

Plugins cannot ship `.claude/rules`, so this skill copies them into the project.

1. Run: `python3 "${CLAUDE_SKILL_DIR}/../../scripts/install_rules.py" "$PWD"`
2. The script never overwrites a file that already exists and lists the ones it kept. If any were kept, show the user the list and ask before re-running with `--force`. A destination that is a symlink or a directory is always kept, even with `--force`, and a symlinked `.claude` or `.claude/rules` is refused with an error.
3. Report which files were copied. Do not edit `CLAUDE.md`.

The commit rule is enforced separately by the plugin's PreToolUse hook; the copied rule files carry the rest.
