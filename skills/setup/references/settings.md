# Guard settings for commits

Two settings keep commits under the rules when Claude runs unattended. A plugin cannot set them (only `agent` and
`subagentStatusLine` take effect in a plugin's `settings.json`), so offer them to the user, show the exact JSON, and
merge it into the project's `.claude/settings.json` only after a yes. Keep every key the file already has.

```json
{
  "permissions": {
    "ask": ["Bash(git commit *)", "Bash(git push *)", "Bash(gh pr create *)"]
  },
  "attribution": { "commit": "", "pr": "" }
}
```

- `permissions.ask` rules are checked before auto mode's classifier and always prompt, even under `/goal` in auto
  mode, so a commit or push still needs the user's yes. The hook in `hooks/README.md` also reads `git -C <dir>
  commit`, which an `ask` rule on its own does not match.
- `attribution` empty stops Claude Code adding its own `Co-Authored-By` trailer and pull-request footer, which the
  plugin's hook would otherwise refuse. Managed settings can override it.
- Auto mode also drops broad allow rules such as `Bash(*)`. For an unattended run, narrow ones keep working:
  `Bash(pytest *)`, `Bash(ctest *)`, `Bash(ruff *)`, `Bash(mypy *)`, `Bash(clang-tidy *)`, `Bash(git status *)`,
  `Bash(git diff *)`, `Bash(git log *)`. Offer these too, as an `allow` list, and say they run without a prompt.
