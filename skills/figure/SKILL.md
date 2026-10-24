---
name: figure
description: Use when drawing a hand-drawn workflow, architecture, block or pipeline diagram of an AI or computer-vision model or system for docs, a paper or slides (high-level, low-level, system pipeline, the whole model in numbered module panels, or what changed between two versions of a model), annotating, translating or exporting such a figure, or rebuilding one with another font.
---

# Figure

A figure is one spec file (`<name>.figure.js`) built into one self-contained HTML file in the rough.js hand-drawn
style. The kit draws the boxes, arrows and icons and checks the layout; the spec says what to draw and where. Every
shape, count, name and hyperparameter is read from the code or config it describes in this session, never from
memory; a fact you cannot confirm is left out or labelled `UNVERIFIED`, and listed in the final message.

Needs Python 3.10 or later and, for the check, Chrome or Chromium (`google-chrome`, `chromium`, or `CHROME` set to
the binary; a snap Chromium cannot read `/tmp` or hidden folders, so use a visible folder under home). The default
font is bundled, so a build works offline.

## Choose the mode

| Mode | Shows | Boxes | Connectors (max) | Starter |
| --- | --- | --- | --- | --- |
| High-level model | Blocks and the data between them | 4 to 7 | 8 | `high-level.figure.js` |
| Low-level model | Modules, tensor shapes, skip and fusion paths, losses | 10 to 20 | 24 | `low-level.figure.js` |
| System pipeline | Services, stores, queues, phases | 8 to 16 | 20 | `pipeline.figure.js` |
| Whole model or system | Every component in numbered module panels | 6 to 10 panels, 40 to 80 boxes | 30 | `whole-model.figure.js` |
| Model delta | What changed between two versions: before, numbered changes, after | up to 8 parts per side | 10 per side | `delta.figure.js` |

With no mode named, use high-level for "the model" and pipeline for "the system". Use delta only when asked what
changed between two versions; a change of hyperparameters alone is a table, not a figure. Name the mode in the final
message. Over budget a figure reads as a wall: merge repeated blocks into one box with a count, fold a module's
internals into one box, drop side outputs, then split into an overview and one detail figure per module.

## Workflow

1. **Ask and plan.** Before drawing, read `${CLAUDE_SKILL_DIR}/references/guide.md`: ask only the questions whose
   answer changes the figure, in one message, with defaults; give the mode, canvas, boxes, and what you merge or leave
   out.
2. **Read the facts** from the model code and configs; note the file each shape, count and name comes from.
3. **Start from the starter.** Copy it from `${CLAUDE_SKILL_DIR}/templates/` to the output folder as
   `<name>.figure.js`, keep `FIGURE` and `draw(k)`, and put the sources and build command in the header comment. For
   a whole-model, notes or translated edition read `${CLAUDE_SKILL_DIR}/references/house-style.md`; every helper,
   kind, icon and font is in `${CLAUDE_SKILL_DIR}/references/kit.md`.
4. **Build and check.**

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/build_figure.py" <dir>/<name>.figure.js <dir>/<name>.html
   python3 "${CLAUDE_SKILL_DIR}/scripts/check_figure.py" <dir>/<name>.html --png <scratch>/<name>.png
   ```

   The check prints every layout issue and exits 1 on one; fix each in the spec, rebuild and recheck. For a paper or
   slide add `--bare`, `--scale 2` and `--svg <dir>/<name>.svg`. Fixes for each message are in
   `${CLAUDE_SKILL_DIR}/references/troubleshooting.md`.
5. **Look at the PNG** with the Read tool for what the checker cannot see: an arrow pointing the wrong way, an icon
   too small or on text, a label the code does not support. Fix, rebuild and look again.
6. **Report** the mode, the HTML and PNG paths, the defaults used and any unconfirmed fact, plus "Merged: ..." and
   "Left out: ...", and alt text for the PNG. Commit only after the user approves, through `/cv-kit:commit`.

## Constraints

- Never edit files under `${CLAUDE_SKILL_DIR}/` from a user project; a figure that needs a new helper defines it in
  its own `draw()`.
- Do not commit cached fonts or scratch PNGs, and do not restyle a committed figure unasked; build the new one beside it.
- State the licence of any font other than the bundled Patrick Hand (OFL); Stay With Me is personal use only.
- Deliver exactly the figures asked for. To publish icons or figures to a design library the user runs `/design-sync`.
