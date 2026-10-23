# Commit hook

`block_trailers.py` runs before each Bash command. If the command is a `git commit` or an `svn commit` / `svn ci`, it denies the command when:

- the command text, or a message file named with `-F` / `--file` that exists when the hook runs, contains a trailer line such as `Co-Authored-By:`, `Signed-off-by:`, `Generated-by:`, `Claude-Session:`, `Acked-by:`, `Reviewed-by:` or similar;
- the text contains "Generated with" or the robot emoji;
- a git commit passes `--signoff`, `-s` or `--trailer`.

The hook refuses; it never rewrites the message.

Known gaps. The hook does not see:

- `git commit --amend --no-edit`: the old message is reused and the hook cannot read it.
- A message built outside the Bash tool.
- A commit wrapped in `bash -c`, `sh -c` or `zsh -c`: it passes the hook entirely, both the flag checks and the trailer text.
- A message passed through a shell variable (`git commit -m "$MSG"`).
- `git commit -C <commit>` or `--reuse-message`: it reuses an old message unchecked.
- Git aliases such as `git ci`.
- Commits made inside a script or a Makefile target.
- `GIT_EDITOR=true git commit --amend`.
- A quoted `<<WORD` heredoc followed by a later line equal to `WORD`, which hides the lines in between from the flag checks.

The hook runs `python3`, which must be on PATH. If it is missing, the shell exits 127, which Claude Code treats as non-blocking, so the commit goes through.

Claude Code also treats any non-blocking hook failure (an exit code other than 0 or 2) as a pass, so the hook is a guard, not a guarantee.

## Switching off Claude Code's own attribution

The hook and the `commit-vcs` skill stop a trailer in a message the agent writes. Claude Code can also add its own attribution to commits and pull requests. A plugin cannot set that: the plugin documentation says only `agent` and `subagentStatusLine` take effect in a plugin's settings. Set it yourself in your user, project or local settings:

```json
{
  "attribution": false
}
```

- `"attribution": false` hides all attribution. It needs Claude Code 2.1.281 or later; earlier versions reject it and skip the whole settings file that holds it.
- The object form `{"commit": "", "pr": "", "sessionUrl": false}` is documented as the form for a settings file that earlier versions also read. The documentation gives no version for it.
- `attribution.sessionUrl` is a separate switch. It controls the `Claude-Session` trailer and the PR session link in cloud and Remote Control sessions, so blanking `commit` does not turn it off.
- `includeCoAuthoredBy` is deprecated since Claude Code v2.0.62. It is ignored once `attribution.commit` or `attribution.pr` is set.
- Managed settings can override your own rules. Claude Code tells Claude that your CLAUDE.md or memory instructions about attribution take precedence, unless the line is set in managed settings. If an administrator set `attribution` there, a rule in your project or in this plugin may not win.
