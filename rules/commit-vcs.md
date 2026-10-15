# Commits (git and SVN)

- A commit message is a subject line plus an optional body. The subject is imperative and about 50 characters. The body is wrapped at 72 and explains what changed and why.
- No trailers of any kind: no `Co-Authored-By`, `Signed-off-by`, `Generated-by`, "Generated with …", SVN's crediting lines `Patch by:`, `Review by:` and `Found by:`, and no `--signoff` (`-s`) or `--trailer` flags. The same applies to pull-request bodies.
- If the hook blocks a line you were instructed to add and cannot drop (for example a managed attribution policy), stop and tell the user; do not retry.
- A message never says who or what reviewed the change, how many review rounds ran, or which findings were fixed.
- Before committing, show the user the branch (or SVN working-copy path), the staged files, and the full message. Wait for approval. Approval for one commit does not cover the next.
- Git: stage named files, not `git add -A`. Never use `--no-verify`.
- SVN: run `svn status` and `svn diff` first, commit only the listed paths, and pass the message with `-F <file>`.
