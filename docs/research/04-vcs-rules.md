# cv-kit research 04: commit rules for git and Subversion

Date: 2026-10-14. Nothing was installed, no repo was modified, no `git commit` / `svn commit` was run. The three scripts in section C4 were exercised on synthetic input only (details in C6).

## 0. Recommendations in one screen

1. **Ship the rule as ONE skill (`commit-messages`) with two reference files (`git.md`, `svn.md`), not as three rule files.** A plugin has no `rules/` component, and the plugin docs say that a `CLAUDE.md` at the plugin root "isn't loaded as context ... put them in a skill" (plugins-reference, "Standard layout"). "No trailers" is one sentence, identical for both VCSs, so it lives once in `SKILL.md`; the references only point to it.
2. **Rules alone are not enough, so layer four defences:** (a) the skill; (b) the `attribution` settings that switch the harness trailer off (a plugin cannot set them, see B5); (c) a `PreToolUse` hook that refuses a bad `git commit` / `svn commit` before it runs; (d) a VCS-side hook (git `commit-msg`, SVN `pre-commit`) as the last gate.
3. **Do not make Conventional Commits the default.** Its footer syntax is the git trailer syntax, which collides with "no trailers of any kind". Follow the repo's existing title style; plain imperative title otherwise.
4. **Refuse, do not rewrite.** The hooks deny with a reason and never strip a trailer silently (`updatedInput` could rewrite the command, but then the user sees a message the agent did not write).
5. **Two things that are easy to miss:** `attribution.sessionUrl` (a `Claude-Session` trailer in cloud / Remote Control sessions, a separate switch), and SVN's own crediting lines (`Patch by:`, `Review by:` in Subversion's community guide), which are trailers in all but name.

---

## A. What the existing rf-detr rules contain, and what is reusable

Read (read-only): `.claude/rules/git.md`, `.claude/rules/pr.md`, `.claude/skills/preparing-rfdetr-pr/SKILL.md`, a grep of the other five skills for commit and preview handling, `.claude/settings.json` (only `enabledPlugins`), `.claude/settings.local.json` (no attribution key), `~/.claude/settings.json` (no `attribution` / `includeCoAuthoredBy` key), and the author's saved preferences.

**Current protection is rule-only.** No settings key and no hook enforces "no trailers". The rule works because project instructions take precedence over the harness default: the session that produced this research received a system reminder asking for a `Co-Authored-By:` line, and the rule won. The official docs back that mechanism, with one exception (managed settings, B5).

| Source | Part | Verdict for cv-kit |
|---|---|---|
| git.md "Before every commit" | Show a preview and wait for an explicit ok; approval covers one commit only | **Generic.** Keep. |
| | Preview contents: branch, `git diff --cached --stat`, full message in a code block | **Generic.** Keep. SVN analogue: repository URL and working-copy path, `svn status` plus the explicit target list, the message. |
| | "First run `verifying-rfdetr-changes`, then `reviewing-rfdetr-changes`"; the line `Review: <n> fixed, <m> open` | **rf-detr-specific** (names its own skills). Generic kernel: report verification (commands with real result lines, and what was not verified) in the preview, never in the message. Keep the kernel, drop the names. |
| | Merge commits exempt from the preview | **rf-detr-specific** (its push flow). Drop. |
| git.md "No trailers" | List of banned trailers; `--signoff` / `--trailer` banned; message = subject + optional body | **Generic, reusable almost verbatim.** Extend with SVN's equivalents. |
| | Message never says who or what reviewed the change, how many rounds, which findings were fixed | **Generic.** Keep (user preference). The review result goes in the preview. |
| git.md "Before every push" | `git fetch upstream` + `git merge upstream/develop`, merge not rebase | **rf-detr-specific** (fork layout, branch names). Generic kernel to keep as a user preference: sync with the base branch before pushing, stop on conflict, confirm the push, never force-push. |
| git.md "PR branches that maintainers have touched" | a named maintainer; `git merge origin/<branch>` before any edit | **rf-detr-specific.** Kernel (optional): if others push to the branch, fetch and merge before editing. |
| git.md "Outward-facing steps belong to the user" | Claude never opens PRs or posts comments; drafts in `.temp/<topic>/` | The policy is **generic as a default** (user preference); the `.temp/` path is **specific**. |
| git.md "Hooks" | Never `--no-verify`; `SKIP=mypy` exception | `--no-verify` ban **generic**; `SKIP=mypy` **specific**. |
| pr.md | Section order Summary / Changes / Verification / Known follow-ups / Performance; Performance needs hardware, command, repetitions, before/after table | **Generic and valuable for CV.** Belongs to a separate `pr-description` skill, outside this task. |
| | "Never": trailers, unbacked claims, numbers not measured in this session, mentions of own review | **Generic.** The "no unmeasured number" rule belongs in the commit rule too. |
| | `.github/PULL_REQUEST_TEMPLATE.md`, `.temp/<topic>/pr-body.md`, `Closes #N`, #1024 | **rf-detr-specific.** |
| preparing-rfdetr-pr | `type(scope): imperative summary` with the rf-detr scope list | The *shape* is a repo convention, not universal; the **scopes are specific**. |
| | Body "says what was broken, what the change does, and why this approach and not the obvious alternative" (example `repeat` vs `tile`) | **Generic.** Best sentence in the set; reused as the body rule. |
| | CHANGELOG, `pre-commit run --all-files`, fork/upstream, Copilot, `action_required` | **rf-detr-specific.** |
| Saved preferences | The author's own feedback on earlier commits | Evidence for why each rule exists. Not shipped. |

**Gaps that cv-kit should close:** no SVN at all; no title-length or mood rule in `git.md`; no guidance on passing a multi-line message safely; no handling of `--amend` or force-push beyond the push rule; nothing mechanical (no hook, no settings key); `Closes #N` is allowed in PR bodies and nothing says whether an issue footer may appear in a commit (cv-kit's answer: only inside a sentence).

---

## B. Research

Fetched today (2026-10-14): Claude Code docs `settings-reference`, `settings`, `hooks`, `plugins-reference` (code.claude.com/docs/en/...); git-scm.com `git-interpret-trailers` and `githooks`; git.git `Documentation/SubmittingPatches`; conventionalcommits.org v1.0.0; svnbook 1.7 pages `svn.ref.svn.c.commit`, `svn.reposadmin.create`, `svn.ref.reposhooks.pre-commit`, `svn.ref.reposhooks.start-commit`, `svn.advanced.locking`; Subversion community guide `conventions.html`. A statement not backed by a fetched page is marked **(knowledge)**. Note that the WebFetch tool summarises pages with a small model, so quotes are as reported by it, not byte-verified.

### B1. Git message conventions

- **Title.** `SubmittingPatches`: first line "a short description"; "50 characters is the soft limit"; no full stop; an area prefix is conventional (`doc: ...`). The **72-column body wrap is not in that document** (checked: absent); it is the Pro Git / Tim Pope / Chris Beams convention **(knowledge)**. cv-kit: title 50 soft and 72 hard, body wrapped at 72.
- **Mood.** `SubmittingPatches`: "Describe your changes in imperative mood", "as if you are giving orders to the codebase"; the status quo is written in the present tense.
- **Body = the why.** "The goal of your log message is to convey the _why_ behind your change to help future developers." Structure: the problem (what is wrong without the change), why this solution is better, alternatives considered and discarded.
- **Conventional Commits 1.0.0, trade-offs.**
  - For: machine-readable `type(scope)!:`, changelog and semver tooling, uniform `git log --oneline`.
  - Against, for this plugin: (1) footers follow "a convention similar to git trailer format" (`Token: value` or `Token #value`) and `BREAKING CHANGE:` is a footer, so the spec asks for trailers; (2) the prefix spends 10 to 20 of the 50 title characters; (3) scope lists drift per repo; (4) squash-merge workflows (rf-detr's maintainer squash) make per-commit types redundant; (5) CV and research repos (notebooks, configs, checkpoints) rarely have a consumer for the types.
  - Decision: do not impose it. If the repo already uses it (`git log -20 --format=%s`), keep the prefix, but express a breaking change with `!` plus a sentence in the description, never a `BREAKING CHANGE:` footer.
- **One logical change per commit; no generated artefacts.** For CV repos, review `git diff --cached --stat` for `*.pt`, `*.pth`, `*.onnx`, `*.engine`, datasets, `.env`; they belong in LFS / DVC / a bucket **(knowledge)**.
- **What a trailer is** (git-interpret-trailers): "A trailer block is a group of one or more lines that (i) is all trailers, or (ii) contains at least one Git-generated or user-configured trailer and consists of at least 25% trailers", "by definition at the end of the commit message", preceded by a blank line. `git interpret-trailers --only-trailers --only-input --unfold < msg` prints what git treats as trailers; that is the cleanest machine check and is used in the git hook. `Closes #12` is not recognised by git as a trailer (no colon) but is a footer in Conventional Commits' definition; cv-kit bans it as a standalone line anyway.
- **Ways a trailer gets added:** `git commit -s` / `--signoff`, `git commit --trailer`, `git interpret-trailers --in-place`, `trailer.*` config, `format.signOff` (format-patch only; checked in `git help -c` locally that `commit.signoff` does not exist), and a git alias such as `ci = commit -s` (check `git config --get-regexp '^alias\.'`).

### B2. Git hooks as a gate (githooks)

- `commit-msg`: one argument, the message file; "Exiting with a non-zero status causes the command to abort"; may edit the file in place; "can be bypassed with the `--no-verify` option".
- `prepare-commit-msg`: runs before the editor, args (file, source, sha); not suppressed by `--no-verify`; non-zero exit aborts. It could strip trailers, but silent stripping is rejected (rec. 4). Not used.
- Hooks without the executable bit are ignored. The directory is `$GIT_DIR/hooks` unless `core.hooksPath` is set; `core.hooksPath` replaces the default directory, so it conflicts with the `pre-commit` framework (rf-detr uses it). With that framework, use its `commit-msg` stage:

```yaml
# .pre-commit-config.yaml   (then: pre-commit install --hook-type commit-msg)
- repo: local
  hooks:
    - id: cvkit-commit-msg
      name: commit message has no trailers
      language: script
      entry: .githooks/commit-msg      # the script from C4.1; it receives the message file
      stages: [commit-msg]
```

Because `--no-verify` skips `commit-msg`, the `PreToolUse` hook bans `--no-verify` / `-n` on `git commit`.

### B3. Subversion

- **Commit syntax** (svnbook `svn commit`): `-m / --message` inline, `-F / --file` from a file. With neither, svn opens an editor (a hang for an agent); quitting without saving prompts abort / commit with no message / edit again. `--force-log` is needed only when the `-F` file is versioned ("Log message file is a versioned file; use '--force-log' to override"), so write the message file outside the working copy and delete it afterwards. Also listed: `--encoding`, `--with-revprop`, `--changelist`, `--depth`, `--no-unlock`, `--editor-cmd` (the page gives no description for several of these; `--encoding UTF-8` for non-ASCII text is **(knowledge)**).
- **svn:log.** The log message is the revision property `svn:log`. It can be edited afterwards only with `svn propset|propedit --revprop -r N svn:log` and only if the repository has a `pre-revprop-change` hook that allows it; by default repositories refuse **(knowledge)**. Consequence: an unwanted trailer in a committed SVN message is effectively permanent, so the check before the commit matters more than on git, where `--amend` is local.
- **No trailer concept in the client.** `svn` has no `--signoff` or `--trailer`. Trailer-like text comes from three places: the agent writing it, harness attribution text (aimed at "git commits and pull requests", but an agent can carry the habit over), and project convention. The Subversion community guide's `Patch by:`, `Suggested by:`, `Found by:`, `Review by:`, `Tested by:` lines at the start of a line are trailers in all but name; cv-kit bans them unless the user asks for one in that repo.
- **Which commands write a log message:** `svn commit|ci`, `svn import`, and the URL forms of `svn copy|move|delete|mkdir|propset|propedit|propdel -m`. The `PreToolUse` hook covers all of them.
- **Hooks (svnbook).**
  - `pre-commit`: "run just before a commit transaction is promoted to a new revision"; arguments are the repository path and the transaction name; "If the pre-commit hook program returns a nonzero exit value, the commit is aborted, the commit transaction is removed, and anything printed to stderr is marshalled back to the client." Lock tokens arrive on stdin. The message is read with `svnlook log -t TXN REPOS` **(knowledge; the page fetched does not name svnlook)**.
  - `start-commit`: arguments are repository path, user, client capabilities; it runs before the transaction exists, so it cannot see the message. Unusable for this check.
  - Hooks run with an **empty environment** (no `PATH`), as the user that owns the server process; on Windows the name needs an executable extension (`.bat`, `.exe`). The book advises validating and rejecting in `pre-commit` rather than modifying the transaction.
  - A server-side hook needs repository admin access. A client cannot install one, so the client-side defence is the `PreToolUse` hook plus the skill; offer the server hook to the repo admin as an optional artefact.
- **svn:needs-lock** (svnbook `locking`): the property makes a file read-only in the working copy; `svn lock` makes it writable; "this property is a communication tool that works independently from the locking system". A successful commit releases the locks on the mentioned paths ("all of the repository locks that were mentioned are released") unless `--no-unlock`. The client sends the lock tokens it finds, and the server also requires the committer to authenticate as the lock owner. Agent rules: never `chmod +w` a needs-lock file to get around it; take a lock (`svn lock -m "<reason>" <path>`) only when the user asked, because it blocks other people; name the locks that the commit will release in the preview; `--no-unlock` only on request; if someone else holds the lock, stop and report.
- **Atomic multi-file commits.** A Subversion commit is one atomic transaction that becomes one revision, all or nothing **(knowledge: svnbook ch. 1; the `svn commit` page fetched does not use the word)**. So one commit is one logical change: pass explicit targets (or `--changelist`) instead of a bare `svn commit` that sweeps every local modification; run `svn status` and `svn diff` first; handle `?` (unversioned) and `!` (missing) entries on purpose with `svn add` / `svn rm`, because a forgotten `svn add` leaves a revision that is broken for everyone else.
- **Log message conventions** (community guide): first line "indicating the general nature of the change", detail in a paragraph, full sentences, not fragments; `issue #N` in the text while still summarising the change; on a branch start with `On the 'name' branch:`; per-file `* path (symbol): description` entries. Those file lists are ASF house style; use them only if the repo's last 20 messages do (`svn log -l 20`). Default: same title + description shape as git.

### B4. Enforcing "no trailer"

Layers, strongest first:

1. **VCS hook** (git `commit-msg` or SVN `pre-commit`): the agent cannot argue with it. Git's can be skipped with `--no-verify`; an SVN client cannot skip a server hook.
2. **Claude Code `PreToolUse` hook on `Bash`** (hooks docs): the event JSON arrives on stdin with `tool_name` and `tool_input.command` (plus `cwd`, `tool_use_id`, ...). To block, either exit 2 with a message on stderr ("Claude receives the stderr as the error"), or exit 0 and print `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"..."}}`; the deny reason is shown to Claude; do not mix the two styles in one hook. Decisions: `allow | deny | ask | defer`, precedence `deny > defer > ask > allow`. `updatedInput` replaces the whole input object (not used). Matcher `"Bash"` is an exact tool name; lists such as `Edit|Write` work. An `if` field in permission-rule syntax (`"if": "Bash(git commit *)"`) can pre-filter, but takes exactly one rule per handler and is documented as best-effort, so the script filters itself. **Fail-open warning (docs):** any exit code other than 0 or 2 is a non-blocking error and the call proceeds; a timed-out command hook does not block unless `"onFailure": "block"` is set (v2.1.295 or later). A crash in the hook therefore lets the commit through, and the VCS hook is the backstop.
3. **Settings and instructions** (B5).
4. **The skill** (C1).

What the `PreToolUse` hook cannot see: commits made inside a script or Makefile target, git aliases (`git ci`), GUI clients, `git commit --amend -C HEAD` / `--reuse-message` (reuses an old message unchecked), `git notes`, `git stash -m`, messages passed through a variable (`-m "$MSG"`). It reads `-F file` content only if the file exists when the hook runs. State these limits; do not claim completeness.

An optional mode (`CVKIT_COMMIT_CONFIRM=1`) makes the hook answer `permissionDecision: "ask"` for a clean commit, so the user gets a prompt showing the command and message: a mechanical version of "preview and wait". **Unverified:** whether `ask` still prompts in bypass or auto permission modes; treat as best-effort.

### B5. Overriding the harness attribution (verified in the official settings reference today)

| Key | Facts |
|---|---|
| `attribution` | Object `{ "commit": string, "pr": string, "sessionUrl": boolean }`, **or `false`** to hide all attribution. `false` needs **Claude Code v2.1.281+**; earlier versions "reject it and skip the whole user, project, or local settings file that holds it". Scope: any file (user, project, local, managed). |
| `attribution.commit` | Text, including any trailers, added to commits. Default: `Co-Authored-By: <model name> <noreply@anthropic.com>` (just `Claude` or `Claude Code` when the model is not recognised). An empty string hides it. |
| `attribution.pr` | PR description text. Default: `🤖 Generated with [Claude Code](https://claude.com/claude-code)`. Empty string hides it. |
| `attribution.sessionUrl` | Default `true`. Adds a **`Claude-Session` trailer** to commits (and a link in PR descriptions) when committing from a cloud or Remote Control session. `false` omits it. A separate switch: blanking `commit` does not turn it off. |
| `includeCoAuthoredBy` | **Deprecated since v2.0.62** in favour of `attribution`. `false` is still honoured in old files but ignored once `attribution.commit` or `attribution.pr` is set. |
| `includeGitInstructions` | `false` removes the built-in commit and PR instructions from the Bash tool description **and** the git status snapshot (branch, `git status`, recent commits) from context. Per-session override: env var `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS` (takes precedence). Useful when a plugin's skills own the whole git workflow; the cost is losing the snapshot. Do not recommend it by default. |

Precedence from the docs: managed > `--settings` > project local > shared project > user. Quote: "Claude Code tells Claude that your own instructions about attribution, such as a CLAUDE.md or memory rule, take precedence over these commit and PR lines, unless the line is set in managed settings." So a rule in the skill works unless an admin set `attribution` in managed settings. In that case the hook denies the commit and the agent must tell the user instead of looping; the skill says so.

**A plugin cannot set `attribution`.** `plugin.json` has a `settings` field and a plugin-root `settings.json`, but "only `agent` and `subagentStatusLine` take effect; other keys are dropped at load". So cv-kit must (1) document the settings change in its README (C5), (2) optionally ship a `setup` skill that proposes the JSON and writes it to the user's settings only after the user agrees, and (3) rely on the skill and the hook meanwhile.

### B6. How the plugin ships the pieces (plugins-reference)

- Hooks: `hooks/hooks.json`, wrapped in a top-level `"hooks"` key with the event map inside; scripts referenced through `${CLAUDE_PLUGIN_ROOT}` (resolves in `command` and `args`; double-quote it in shell form). The variable is not exported to commands the agent runs through the Bash tool, so scripts must be invoked by the hook, not by skill text.
- Skills: `skills/<name>/SKILL.md`; extra files such as `references/*.md` sit beside it and are read on demand.
- `claude plugin validate ./cv-kit` checks the manifest and paths; run it in CI.
- Names starting with `claude-`, `anthropic-` or reading as Anthropic's own are rejected or warned by the validator. `cv-kit` is fine.

---

## C. Drafts, ready to drop in

### C1. `skills/commit-messages/SKILL.md`

````markdown
---
name: commit-messages
description: Use when committing, amending, tagging or writing a log message with git or Subversion (git commit, svn commit/ci, svn copy/mkdir/import with -m), or when drafting a commit message or change summary. Covers the message shape, the ban on trailers and on mentioning reviews, and the preview before every commit.
---

# Commit messages (git and Subversion)

A commit message is a **title and a description**. Nothing else.

## Shape
- **Title**: one line, imperative mood ("Fix NMS threshold for small boxes", not "Fixed" or "Fixes"), 50 characters or fewer (72 is the hard limit), no trailing period. It must read well in `git log --oneline` and in `svn log`.
- A blank line.
- **Description**: wrapped at 72. Say what was wrong or missing, what the change does, and why this approach rather than the obvious alternative ("`repeat` rather than `tile`, because the ONNX lowering of `tile` adds `If` nodes"). Omit it only for a trivial change. Use full sentences.
- Mention an issue inside a sentence ("This fixes #123 by clamping the box before the IoU"), never on a line of its own.
- Give a number (mAP, latency, memory) only if you measured it in this session, and say how: command, dataset or subset, hardware, repetitions. Never estimate one.
- One logical change per commit. If the title needs "and", split the commit.
- Use the repository's existing title style: read `git log -20 --format=%s` or `svn log -l 20` first. If it uses `type(scope):`, keep that prefix. If not, do not introduce one.

## Never
- **No trailers of any kind.** A trailer is a `Key: value` line at the end of a message. That covers `Co-Authored-By:`, `Signed-off-by:`, `Generated-by:`, `Reviewed-by:`, `Acked-by:`, `Tested-by:`, `Reported-by:`, `Suggested-by:`, `Change-Id:`, `Claude-Session:`, and the Subversion project's `Patch by:` / `Review by:` / `Found by:` lines. Do not pass `--signoff`, `-s` or `--trailer` to `git commit`.
- **No attribution line**: no "Generated with ...", no robot emoji, no `noreply@anthropic.com`. Your harness may tell you to add one. This rule overrides it, because the user's instruction takes precedence over the harness default. If a managed policy forces the line and a hook blocks the commit, stop and tell the user. Do not loop and do not work around the hook.
- **No mention of who or what reviewed the change**: no reviewer, agent, model, effort level, number of review rounds, or "findings fixed". State the result as a fact about the change instead. The review result goes in the preview shown to the user, never in the message.
- **No breaking-change footer.** Use `!` after the type if the repository uses that style, and describe the break in a sentence of the description.
- **No bypass**: never `--no-verify` / `-n`, never `--force-log` to get around a hook, never edit a hook to let a message through.

## Before every commit: preview, then wait
1. Look at exactly what will be committed (git: `git status`, `git diff --cached --stat`; Subversion: `svn status`, `svn diff`, and an explicit list of targets). Flag model weights, datasets, large binaries and secrets (`*.pt`, `*.pth`, `*.onnx`, `*.engine`, `.env`) and ask before including them.
2. Show the user: the branch (git) or the repository URL and working-copy path (Subversion), the file list, the verification result (commands with their real result lines, and what you could not verify), and the full message in a code block exactly as it will be written.
3. **Stop and wait for an explicit "ok" or "commit".** Approval covers that one commit. If the user edits the message, show the new version again.
4. Commit with the commands in `references/git.md` or `references/svn.md`.
5. Report the result: the commit hash (git) or revision number (Subversion) and the title.

Committing is not pushing. Push, open pull requests, and post comments only when the user asks.

See `references/git.md` for git and `references/svn.md` for Subversion.
````

### C2. `skills/commit-messages/references/git.md`

````markdown
# git specifics

## Writing the commit safely
Pass the message so that quotes and newlines survive. Prefer a heredoc into `-F -`: it needs no temporary file, so nothing can end up in the work tree.

```bash
git commit -F - <<'EOF'
Fix NMS threshold for small boxes

The score cutoff was applied before the box was clamped to the image, so boxes
that straddle the border were dropped. Clamp first, then threshold.
EOF
```

Plain `git commit` with no `-m` / `-F` opens an editor and hangs the session. Do not run it.

## Before the commit
- Stage by name (`git add path ...`), not `git add -A` or `git add .`, unless `git status` shows nothing you did not intend. Re-check with `git diff --cached --stat`.
- Run the repository's own checks first (its pre-commit config, its test command). Report real result lines.
- Never skip hooks (`--no-verify`, `-n`). If a hook rejects the message, fix the message. If a hook rejects the code, fix the code.
- No `-s` / `--signoff`, no `--trailer`. Look for a git alias that adds one (`git config --get-regexp '^alias\.'`, for example `ci = commit -s`) and for `trailer.*` settings; if you find one, tell the user instead of overriding it silently.

## Amending, rewriting, publishing
- `git commit --amend`, `git rebase`, `git reset --hard` and force-push rewrite history. Do them only when the user asks, and never on a commit that is already pushed unless the user explicitly says so.
- `git commit --amend --no-edit` and `git commit -C <commit>` keep an old message. Read it first (`git log -1 --format=%B`); if it contains a trailer, tell the user.
- Before a push the user has approved: fetch the base branch and merge or rebase as the user prefers, stop and ask on any conflict, rerun the checks if new commits came in, and confirm the push.

## Checking a message you already wrote
`git interpret-trailers --only-trailers --only-input --unfold < message.txt` must print nothing.
````

### C3. `skills/commit-messages/references/svn.md`

````markdown
# Subversion specifics

Subversion has no trailers, no `--signoff`, and no client-side commit hooks. The only mechanical gate is a server-side `pre-commit` hook, if the repository has one, so the care below is your job.

## Writing the commit
Write the message to a file **outside the working copy**, commit with `-F`, then delete it. A message file inside the working copy would be versioned (svn then demands `--force-log`) or show up as `?` in `svn status`.

```bash
msg=$(mktemp)
cat > "$msg" <<'EOF'
Fix NMS threshold for small boxes

The score cutoff was applied before the box was clamped to the image, so boxes
that straddle the border were dropped. Clamp first, then threshold.
EOF
svn commit --encoding UTF-8 -F "$msg" path/one.py path/two.py
rm -f "$msg"
```

Never run `svn commit` without `-m` or `-F`: it opens an editor and hangs the session. Do not use `--force-log` to get past a refusal.

## Before the commit
- Run `svn status`, then `svn diff`. A Subversion commit is one atomic revision, so it must contain exactly one logical change, and all of it:
  - `?` (unversioned) files that belong to the change need `svn add`; files that do not belong must not be passed as targets.
  - `!` (missing) files need `svn rm` if the deletion is intended; otherwise stop and report.
  - `C` (conflicted) paths block the commit; stop and report.
- Name the targets explicitly, or use `--changelist`. A bare `svn commit` commits every local modification in the working copy, including unrelated half-finished work.
- Run `svn update` first only when the user wants the commit based on the latest revision. If it reports conflicts, resolve nothing yourself; stop and report.
- Show the user `svn info --show-item url`, the `svn status` lines for the targets, and the message in the preview.

## Locks and `svn:needs-lock`
- A file with `svn:needs-lock` is read-only until locked. Never `chmod +w` it, and never delete and recreate it, to get around that.
- Take a lock (`svn lock -m "<reason>" path`) only when the user asked for it, because it blocks everyone else. If someone else holds the lock, stop and report who and why (`svn info path`).
- A successful commit releases every lock on the committed paths. Say in the preview which locks will be released. Use `--no-unlock` only when the user asks.

## The message
- Same shape as git: title, blank line, description. Subversion does not enforce it, but short `svn log` views show only the first line.
- Do not write `Patch by:`, `Review by:`, `Reviewed by:`, `Found by:`, `Suggested by:` or `Tested by:` lines, even though the Subversion project's own guide uses them. They are trailers. If a repository's convention requires one, tell the user and let them add it.
- Mention issues inside a sentence ("This fixes issue #123 by ..."), as the Subversion guide asks for `issue #N` in the text.
- If the last 20 messages (`svn log -l 20`) use a file-list style (`* path (symbol): description`), follow it for the description. That style is allowed because it is not a trailer.

## Other commands that write a log message
`svn import`, and the URL forms of `svn copy`, `move`, `delete`, `mkdir`, `propset` and `propedit` with `-m` / `-F`, commit straight to the repository with no working-copy review. Treat each one as a commit: preview and wait first, same message rules.

## After the commit, and mistakes
- Report the revision number and `svn log -l 1 -v`.
- A committed log message is the revision property `svn:log`. Changing it (`svn propedit --revprop -r N svn:log`) works only if the repository's `pre-revprop-change` hook allows it. Do it only when the user asks. Otherwise a trailer that slipped in stays in the history, which is why the message is checked before the commit.
````

### C4. Hook scripts (text only; nothing installed)

#### C4.1 `hooks/git/commit-msg` (POSIX sh)

```sh
#!/bin/sh
# cv-kit commit-msg hook. Install as .git/hooks/commit-msg (or via core.hooksPath).
# Refuses: trailers, attribution lines, mentions of who/what reviewed the change,
# and a malformed title. Never edits the message. $1 = path of the message file.
msg_file=$1
tmp=$(mktemp) || exit 1
trap 'rm -f "$tmp"' EXIT HUP INT TERM
grep -v '^#' "$msg_file" > "$tmp"          # comment lines are not part of the message

fail() { printf 'commit-msg: %s\n' "$1" >&2; exit 1; }

# 1. Trailers, by git's own definition (last paragraph of key: value lines).
trailers=$(git interpret-trailers --only-trailers --only-input --unfold < "$tmp")
[ -z "$trailers" ] || fail "trailers are not allowed; remove: $(printf '%s' "$trailers" | head -n 1)"

# 2. Trailer-shaped or attribution lines anywhere, and reviewer mentions.
trailer_re='^[[:space:]]*(co-authored-by|signed-off-by|generated-by|reviewed-by|acked-by|tested-by|reported-by|suggested-by|helped-by|mentored-by|claude-session|change-id|patch by|review by|reviewed by|found by|suggested by|tested by)[[:space:]]*:'
footer_re='^[[:space:]]*(closes|fixes|resolves|refs?)[[:space:]]+#[0-9]+[[:space:]]*$'
attrib_re='generated (with|by) \[?(claude|ai|an? llm)|noreply@anthropic\.com|🤖'
review_re='reviewed[- ]by|review(er)? agent|[0-9a-z]+ review (round|pass)|(claude|opus|sonnet|haiku|gpt|gemini|copilot)[^.]{0,30}review'
grep -Eiq "$trailer_re" "$tmp" && fail "trailer-style line found (Co-Authored-By, Signed-off-by, Reviewed-by, ...)"
grep -Eiq "$footer_re"  "$tmp" && fail "issue footer line; mention the issue inside a sentence of the description instead"
grep -Eiq "$attrib_re"  "$tmp" && fail "attribution line found; a message is a title and a description only"
grep -Eiq "$review_re"  "$tmp" && fail "do not say who or what reviewed the change; state the facts about the change instead"

# 3. Shape of the title (skipped for merges, reverts and autosquash commits).
title=$(sed -n '1p' "$tmp")
case $title in Merge\ *|Revert\ *|fixup!*|squash!*|amend!*) exit 0 ;; esac
[ -n "$title" ] || fail "empty title"
[ "$(sed -n '2p' "$tmp")" = "" ] || fail "line 2 must be blank (title, blank line, description)"
n=$(printf '%s' "$title" | wc -m | tr -d ' ')
[ "$n" -le 72 ] || fail "title is $n characters; keep it to 50 (hard limit 72)"
[ "$n" -le 50 ] || printf 'commit-msg: warning: title is %s characters (soft limit 50)\n' "$n" >&2
exit 0
```

#### C4.2 `hooks/svn/pre-commit` (server side, POSIX sh)

```sh
#!/bin/sh
# cv-kit Subversion pre-commit hook, server side: <repo>/hooks/pre-commit (chmod +x).
# $1 = repository path, $2 = transaction name. Non-zero exit aborts the commit and
# stderr goes back to the client. Subversion runs hooks with an EMPTY environment,
# so every path is absolute.
REPOS=$1
TXN=$2
SVNLOOK=${SVNLOOK:-/usr/bin/svnlook}      # adjust: /usr/local/bin, /opt/homebrew/bin, ...
PATH=/bin:/usr/bin; export PATH

msg=$("$SVNLOOK" log -t "$TXN" "$REPOS") || { echo "pre-commit: cannot read the log message" >&2; exit 1; }
fail() { printf 'pre-commit: %s\n' "$1" >&2; exit 1; }

[ -n "$(printf '%s' "$msg" | tr -d '[:space:]')" ] || fail "empty log message"

trailer_re='^[[:space:]]*(co-authored-by|signed-off-by|generated-by|reviewed-by|acked-by|tested-by|reported-by|suggested-by|helped-by|mentored-by|claude-session|change-id|patch by|review by|reviewed by|found by|suggested by|tested by)[[:space:]]*:'
footer_re='^[[:space:]]*(closes|fixes|resolves|refs?)[[:space:]]+#[0-9]+[[:space:]]*$'
attrib_re='generated (with|by) \[?(claude|ai|an? llm)|noreply@anthropic\.com|🤖'
review_re='reviewed[- ]by|review(er)? agent|[0-9a-z]+ review (round|pass)|(claude|opus|sonnet|haiku|gpt|gemini|copilot)[^.]{0,30}review'
printf '%s\n' "$msg" | grep -Eiq "$trailer_re" && fail "trailer-style line found (Co-Authored-By, Patch by, Reviewed-by, ...)"
printf '%s\n' "$msg" | grep -Eiq "$footer_re"  && fail "issue footer line; mention the issue inside a sentence of the description instead"
printf '%s\n' "$msg" | grep -Eiq "$attrib_re"  && fail "attribution line found; a log message is a title and a description only"
printf '%s\n' "$msg" | grep -Eiq "$review_re"  && fail "do not say who or what reviewed the change; state the facts instead"

# Subversion has no trailer concept, so catch the shape: a last paragraph that is
# only `Key: value` lines, after at least one other paragraph.
printf '%s\n' "$msg" | awk '
  /^[[:space:]]*$/ { if (cur) { last = cur; allkv = kv; paras++ } cur = 0; kv = 1; next }
  { cur++; if ($0 !~ /^[A-Za-z][A-Za-z0-9-]*:[[:space:]]/) kv = 0 }
  END { if (cur) { last = cur; allkv = kv; paras++ }
        exit (paras >= 2 && allkv) ? 0 : 1 }' && fail "last paragraph looks like trailers (only 'Key: value' lines); write it as a sentence"

title=$(printf '%s\n' "$msg" | sed -n '1p')
n=$(printf '%s' "$title" | wc -m | tr -d ' ')
[ "$n" -le 72 ] || fail "title is $n characters; keep it to 50 (hard limit 72)"
exit 0
```

Install on the server (repository admin): copy to `<repo>/hooks/pre-commit`, `chmod +x`, adjust `SVNLOOK`. Do not add a `pre-revprop-change` hook: without one Subversion refuses all revision-property edits, which keeps `svn:log` immutable.

#### C4.3 `hooks/pretooluse-no-trailers.py` (Claude Code `PreToolUse`, matcher `Bash`)

```python
#!/usr/bin/env python3
"""cv-kit PreToolUse hook for the Bash tool: block `git commit` / `svn commit`
whose message carries trailers, attribution or reviewer mentions.

Reads the hook event as JSON on stdin and prints a deny decision as JSON.
Exit 0 with no output means "no opinion". It parses the command with shlex, which
is good enough for what an agent writes, not a shell. A command it cannot parse
falls back to scanning the raw text. Set CVKIT_COMMIT_CONFIRM=1 to also turn every
clean commit into a user prompt that shows the message (permissionDecision "ask").
"""
import json
import os
import re
import shlex
import sys

TRAILER = re.compile(
    r"(?:^|[\s'\"])(co-authored-by|signed-off-by|generated-by|reviewed-by|acked-by|tested-by|"
    r"reported-by|suggested-by|helped-by|mentored-by|claude-session|change-id|"
    r"patch by|review by|reviewed by|found by|suggested by|tested by)\s*:",
    re.I | re.M,
)
FOOTER = re.compile(r"(?:^|[\s'\"])(closes|fixes|resolves|refs?)\s+#\d+\s*(?:['\"]|$)", re.I | re.M)
ATTRIB = re.compile(r"generated (with|by) \[?(claude|ai|an? llm)|noreply@anthropic\.com|\U0001F916", re.I)
REVIEW = re.compile(
    r"reviewed[- ]by|review(er)? agent|[0-9a-z]+ review (round|pass)|"
    r"(claude|opus|sonnet|haiku|gpt|gemini|copilot)[^.\n]{0,30}review",
    re.I,
)
SVN_COMMITS = {"commit", "ci", "import"}
# these commit straight to a URL when given one, with the log message from -m / -F
SVN_URL_WRITES = {"copy", "cp", "move", "mv", "rename", "ren", "delete", "del", "remove", "rm", "mkdir",
                  "propset", "ps", "propedit", "pe", "propdel", "pd"}
SEPARATORS = {"&&", "||", ";", "|", "&", ";;", "\n"}
GIT_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env"}
GIT_MESSAGE_SOURCES = {"-m", "-F", "-C", "-c", "--message", "--file", "--reuse-message",
                       "--reedit-message", "--no-edit", "--fixup", "--squash"}


def deny(reason: str) -> None:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


def split_logical_lines(cmd: str) -> str:
    """Turn newlines outside quotes into `;` so each line is its own command."""
    out, quote = [], None
    for ch in cmd:
        if quote:
            quote = None if ch == quote else quote
            out.append(ch)
        elif ch in "'\"":
            quote = ch
            out.append(ch)
        else:
            out.append(" ; " if ch == "\n" else ch)
    return "".join(out)


def tokenize(cmd: str) -> list[str]:
    lex = shlex.shlex(split_logical_lines(cmd), posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    return list(lex)


def find_commits(tokens: list[str]):
    """Yield (tool, subcommand, args) for each command that records a log message."""
    i = 0
    while i < len(tokens):
        tool = os.path.basename(tokens[i])
        if tool not in ("git", "svn"):
            i += 1
            continue
        j = i + 1
        while tool == "git" and j < len(tokens) and tokens[j].startswith("-"):
            j += 2 if tokens[j] in GIT_OPTS_WITH_VALUE else 1
        sub = tokens[j] if j < len(tokens) else ""
        if (tool == "git" and sub in {"commit", "merge", "tag"}) or (
                tool == "svn" and sub in SVN_COMMITS | SVN_URL_WRITES):
            k = j + 1
            while k < len(tokens) and tokens[k] not in SEPARATORS:
                k += 1
            yield tool, sub, tokens[j + 1:k]
            i = k
        else:
            i = j + 1


def git_flags(args: list[str]):
    """Return (set of flags seen, has_message_source) for `git commit` arguments."""
    flags, has_msg, it = set(), False, iter(args)
    for a in it:
        if a.startswith("--"):
            name = a.split("=", 1)[0]
            flags.add(name)
            has_msg |= name in GIT_MESSAGE_SOURCES
            if name in {"--message", "--file", "--reuse-message", "--reedit-message", "--fixup",
                        "--squash", "--trailer", "--author", "--date", "--template"} and "=" not in a:
                next(it, None)
        elif a.startswith("-") and len(a) > 1:
            for pos, ch in enumerate(a[1:], 1):
                if ch in "mFCct":                       # takes an argument: rest of cluster or next token
                    flags.add("-" + ch)
                    has_msg |= ch in "mFCc"
                    if pos == len(a) - 1:
                        next(it, None)
                    break
                flags.add("-" + ch)
    return flags, has_msg


def svn_msg_source(args: list[str]) -> bool:
    return any(a in ("-m", "-F", "--message", "--file") or a.startswith(("--message=", "--file=", "-m", "-F"))
               for a in args)


def file_args(args: list[str]):
    """Yield the values of -F / --file."""
    it = iter(args)
    for a in it:
        if a in ("-F", "--file"):
            yield next(it, "")
        elif a.startswith("--file="):
            yield a.split("=", 1)[1]
        elif a.startswith("-F") and len(a) > 2:
            yield a[2:]


def main() -> None:
    event = json.load(sys.stdin)
    if event.get("tool_name") != "Bash":
        return
    cmd = (event.get("tool_input") or {}).get("command", "")
    if not re.search(r"\b(git|svn)\b", cmd):
        return
    cwd = event.get("cwd") or os.getcwd()

    try:
        commits = list(find_commits(tokenize(cmd)))
    except ValueError:                                   # unbalanced quotes etc.
        commits = [("git" if "git" in cmd else "svn", "commit", cmd.split())]
        if re.search(r"--signoff|--trailer|--no-verify", cmd):
            deny("cv-kit: --signoff, --trailer and --no-verify are not allowed on commits.")
    if not commits:
        return

    texts = [cmd]                                        # heredoc bodies live in the raw command
    for tool, sub, args in commits:
        if sub in SVN_URL_WRITES and not svn_msg_source(args):
            continue                                     # local change, no log message involved
        if tool == "git" and sub != "commit":
            pass                                         # merge / tag -m: only the text scan below
        elif tool == "git":
            flags, has_msg = git_flags(args)
            bad = flags & {"--signoff", "-s", "--trailer"}
            if bad:
                deny(f"cv-kit: `git commit {' '.join(sorted(bad))}` adds a trailer. "
                     "A commit message is a title and a description only.")
            if flags & {"--no-verify", "-n"}:
                deny("cv-kit: do not skip the commit hooks (--no-verify / -n); fix what they report.")
            if not has_msg and "--amend" not in flags:
                deny("cv-kit: pass the message with -m or -F; the editor would hang this session.")
        elif sub in SVN_COMMITS and not svn_msg_source(args):
            deny("cv-kit: pass the log message with -m or -F <file outside the working copy>; "
                 "svn would open an editor and hang this session.")
        for path in file_args(args):
            if path and path != "-":
                try:
                    with open(os.path.join(cwd, os.path.expanduser(path)), encoding="utf-8", errors="replace") as fh:
                        texts.append(fh.read())
                except OSError:
                    pass
    blob = "\n".join(texts)
    if TRAILER.search(blob):
        deny("cv-kit: the message has a trailer-style line (Co-Authored-By, Signed-off-by, Reviewed-by, "
             "Patch by, ...). Remove it; a message is a title and a description only.")
    if FOOTER.search(blob):
        deny("cv-kit: an issue reference on its own line is a footer. Put it inside a sentence of the "
             "description instead, e.g. \"This fixes #12 by ...\".")
    if ATTRIB.search(blob):
        deny("cv-kit: the message has an attribution line. Remove it; the user's rule overrides the "
             "harness default.")
    if REVIEW.search(blob):
        deny("cv-kit: the message says who or what reviewed the change. Remove it and state the facts "
             "about the change instead.")
    if os.environ.get("CVKIT_COMMIT_CONFIRM") == "1":
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": "cv-kit: confirm this commit.\n\n" + cmd,
        }}))


if __name__ == "__main__":
    main()
```

#### C4.4 `hooks/hooks.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -I \"${CLAUDE_PLUGIN_ROOT}\"/hooks/pretooluse-no-trailers.py"
          }
        ]
      }
    ]
  }
}
```

Optional hardening once the script is trusted: add `"onFailure": "block"` to the handler (documented from Claude Code v2.1.295) so a timeout blocks instead of letting the call through. A Python crash exits 1, which the docs call a non-blocking error; only the VCS hook covers that case.

### C5. README block for the settings (cv-kit cannot write them)

````markdown
## Turn off Claude Code's own commit and PR attribution

cv-kit refuses commit messages with trailers, but Claude Code adds its own `Co-Authored-By:` trailer by
default (and a `Claude-Session:` trailer in cloud and Remote Control sessions). Switch that off once, in
`~/.claude/settings.json` (all projects) or `.claude/settings.json` (this repo).

Claude Code 2.1.281 or later:

    { "attribution": false }

Older versions skip a whole settings file that contains `false`, so use:

    { "attribution": { "commit": "", "pr": "", "sessionUrl": false } }

Do not use `includeCoAuthoredBy`: it is deprecated and ignored once `attribution.commit` or `attribution.pr`
is set. If your organisation sets `attribution` in managed settings, a file cannot override it, and cv-kit's
hook will block the commit with an explanation.
````

### C6. What was tested, and what was not

Tested (scratch directory only; no commit made, no VCS state touched):
- `pretooluse-no-trailers.py`: 40 synthetic hook events fed on stdin (`python3 -I`, Python 3.13.3). Cases: plain and chained commits, `git -C` / `git -c` prefixes, newline-separated commands, `-sm` / `-am` clusters, `--signoff`, `--trailer`, `--no-verify`, `-n`, no-message commit, `--amend --no-edit`, heredoc `-m "$(cat <<'EOF' ...)"` with an apostrophe in the body, `-F -` heredoc, `-F file` (trailer in the file; clean file), `Closes #12` as a footer versus "which fixes #12" in prose, review-round phrases versus "Document how to use Claude Code hooks", `svn commit|ci` with and without a message, `svn mkdir|copy -m` on URLs, `svn rm` on a local path, `git merge -m`, `git tag -m`, unbalanced quotes (falls back to a text scan), non-Bash tool events. All 40 gave the expected allow or deny. `CVKIT_COMMIT_CONFIRM=1` returns an `ask` decision.
- `git-commit-msg`, run directly on 14 message files (git 2.54.0 for `interpret-trailers`): clean, `Signed-off-by`, `Co-Authored-By`, robot-emoji line, reviewer-agent phrase, missing blank line 2, 80-char and 55-char titles, merge title, `#` comment lines, `Closes #12`, `Ticket: CV-12`, prose issue reference. All as expected.
- `svn-pre-commit`, run with a stub `svnlook`: clean, empty, single line, `Patch by:`, trailing `Key: value` paragraph, a mixed last paragraph that must pass, long title, attribution line, `Fixes #9` line. All as expected.
- `sh -n` syntax check of both shell scripts passed.

Not tested or unverified:
- This machine has no `svn`, `svnlook`, `svnadmin` or `shellcheck`. The SVN hook ran against a stub, not a real repository, and the `svnlook log -t` usage comes from knowledge, not the fetched page.
- The scripts were not run inside a live Claude Code session (plugin hook registration, `${CLAUDE_PLUGIN_ROOT}` expansion, how the deny reason is displayed).
- Minimum git version for `interpret-trailers --only-input` was not checked (only 2.54.0 here).
- `ask` behaviour under bypass or auto permission modes is unknown.
- The reviewer-mention regexes have false positives by design; for example a commit titled "Address Copilot review comments" is denied. The cost is one rewritten message. The PreToolUse hook matches an explicit list of trailer keys, not a general `Key: value` pattern; the git hook uses git's own trailer definition and the SVN hook a last-paragraph heuristic.
- Windows: the shell scripts need a POSIX shell (Git Bash); the Python hook is portable but untested there.
- shlex is not a shell parser: process substitution, `eval`, a message held in a variable, and commits made by a script the agent runs are not inspected.
