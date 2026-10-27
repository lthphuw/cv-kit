# Commits (git and SVN)

- Subject: imperative, about 50 characters. Optional body, wrapped at 72, saying what changed and why.
- No trailers: no `Co-Authored-By`, `Signed-off-by`, `Generated-by`, "Generated with …", SVN's crediting lines `Patch by:`, `Review by:` or `Found by:`, and no `--signoff` (`-s`) or `--trailer`. Pull-request bodies too.
- Never say who or what reviewed the change, how many rounds ran, or which findings were fixed.
- If the hook blocks a line you were told to add and cannot drop (for example a managed attribution policy), stop and tell the user; do not retry.
- Before committing, show the branch (or SVN working-copy path), the staged files and the full message; wait for approval. One approval covers one commit.
- Git: stage named files, never `git add -A`; never `--no-verify`. SVN: run `svn status` and `svn diff` first; commit only the listed paths, with `-F <file>`.
