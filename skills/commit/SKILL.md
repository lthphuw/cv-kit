---
name: commit
description: Use when about to commit, amend or push with git or SVN, writing or rewording a commit message or a pull-request description, or asked what a commit should say. Commits carry no trailers and are previewed before they are made.
argument-hint: "[what changed, or leave empty]"
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project_facts.py *)
---

# Commit with git or SVN

Facts read just now:

!`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project_facts.py facts .`

Detect the VCS first: `git rev-parse --is-inside-work-tree` succeeding means git (it also works in worktrees and subdirectories), and `svn info` succeeding means SVN. Do not look for a `.git` directory, because `.git` can be a file.

## The message
- Subject line, then an optional body. Nothing else.
- Subject: imperative, about 50 characters, no trailing period. Body: wrapped at 72, says what changed and why.
- No trailers: no `Co-Authored-By`, `Signed-off-by`, `Generated-by`, "Generated with …", SVN's crediting lines `Patch by:`, `Review by:` and `Found by:`, and no `--signoff` (`-s`) or `--trailer`. The cv-kit hook blocks these commits, so write it clean the first time.
- If the hook blocks a line you were instructed to add and cannot drop (for example a managed attribution policy), stop and tell the user; do not retry.
- Never mention who or what reviewed the change, review rounds, or findings.

## Before committing: preview, then wait
Show the user: the branch (SVN: the working-copy path), the staged or listed files, and the full message in a code block. Stop. Commit only after an explicit yes. A yes covers that commit only.

## git
1. `git status` and `git diff --cached` to see exactly what is staged.
2. Stage named files. Do not use `git add -A`.
3. `git commit -m "<subject>" -m "<body>"`. Never `--no-verify`.
4. `git commit --amend --no-edit` reuses the old message, which the hook cannot inspect: read that message first.

## SVN
1. `svn status` and `svn diff` to see what will go in; add new files with `svn add`.
2. Write the message to a file and commit only the listed paths: `svn commit -F msg.txt <paths>`.
3. If the commit is rejected by a server hook, read the reason, fix the message, and commit again.
