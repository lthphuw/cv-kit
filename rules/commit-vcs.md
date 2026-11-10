# Commits (git and SVN)

Messages follow Conventional Commits 1.0.0 (conventionalcommits.org), in git and in SVN. A project's own convention
(a commitlint config, `CONTRIBUTING.md`, the style of its recent log) wins over this file.

```
<type>(<scope>)!: <description>

<body>

<footers>
```

- **Type**, one of: `feat` a new feature, `fix` a bug fix, `docs` documentation only, `style` formatting with no code
  change, `refactor` code change with no behaviour change, `perf` faster or smaller, `test` tests only, `build` build
  system or dependencies, `ci` CI configuration, `chore` tooling and housekeeping, `revert` undoes an earlier commit.
- **Scope**, optional: the package, module or folder the change touches, lowercase, one word (`fix(nms): ...`,
  `feat(tracker): ...`). Leave it out when the change spans the repository.
- **Description**: imperative mood ("add", not "added" or "adds"), lowercase first word, no trailing period. The
  whole header is at most 72 characters; aim for 50. It says what the commit does to the code, not what you did.
- **Breaking change**: `!` before the colon, and a `BREAKING CHANGE: <what breaks and how to migrate>` footer, for any
  change to a public API, a config key, a CLI flag, a file format or a model's input or output.
- **Body**, optional: after one blank line, wrapped at 72. Why the change was needed and what behaviour changed; the
  diff already shows how. Plain prose: no "This commit", no dashes as connectors, no bold labels, no closing line.
- **Footers**, optional: `BREAKING CHANGE: ...`, `Refs: #123`, `Closes #123`. Nothing else.
- **Revert**: `revert: <header of the reverted commit>`, body `This reverts commit <sha>.`

Examples:

```
fix(nms): return no boxes for zero detections

torchvision's batched_nms raised on an empty tensor when the detector
found nothing in a frame, which stopped the video loop.

Refs: #41
```

```
feat(export)!: write ONNX with dynamic batch

BREAKING CHANGE: export_onnx() no longer takes batch_size; pass
dynamic_batch=False to keep a fixed batch of 1.
```

One logical change per commit: the tests go with the code they test, a refactor goes in its own commit before the
behaviour change, and unrelated formatting stays out.

- No trailers: no `Co-Authored-By`, `Signed-off-by`, `Generated-by`, "Generated with …", SVN's crediting lines `Patch by:`, `Review by:` or `Found by:`, and no `--signoff` (`-s`) or `--trailer`. Pull-request bodies too.
- Never say who or what reviewed the change, how many rounds ran, or which findings were fixed.
- If the hook blocks a line you were told to add and cannot drop (for example a managed attribution policy), stop and tell the user; do not retry.
- Commit only when the user asks. Git: stage named files, never `git add -A`; never `--no-verify`; never amend, rebase or force-push a commit that is already pushed unless asked. SVN: run `svn status` and `svn diff` first; commit only the listed paths, with `-F <file>`.
