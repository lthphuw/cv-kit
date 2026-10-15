---
name: ai-workflow-figure
description: Use when drawing a hand-drawn workflow, architecture or pipeline figure of an AI or computer-vision model or system (high-level, low-level, system pipeline, or the whole model in numbered module panels), annotating or translating such a figure, or rebuilding one with another font.
---

# AI workflow figure

A figure is one spec file (`<name>.figure.js`) built into one self-contained HTML file in the rough.js
hand-drawn style. The kit draws the boxes, arrows and icons and checks the layout; the spec only says what to
draw and where. Every shape, count, name and hyperparameter in a figure is read from the code or config it
describes in this session, never written from memory.

The scripts need Python 3.10 or later. The check needs Chrome or Chromium; if it is not on PATH as
`google-chrome` or `chromium`, set `CHROME` to its binary. A snap-packaged Chromium cannot read or write `/tmp`,
`/mnt` or hidden folders, so with it keep the figure and the PNG in a visible folder under the home directory.
The default font is bundled, so a build works offline.

## Choose the mode

| Mode | Shows | Boxes | Text per box | Starter |
| --- | --- | --- | --- | --- |
| High-level model | Blocks and the data between them | 4 to 7 | 1 or 2 short lines, no tensor layouts | `high-level.figure.js` |
| Low-level model | Modules, tensor shapes, skip and fusion paths, losses | 10 to 20 | Shapes in every label | `low-level.figure.js` |
| System pipeline | Services, stores, queues, phases (offline, online) | 8 to 16 | Role and key facts | `pipeline.figure.js` |
| Whole model or system | Every component of one model in numbered module panels, losses in their panels | 6 to 10 panels, 40 to 80 boxes | Body 21 to 23, titles 23 to 26, tints and icons | `whole-model.figure.js` |

When the request does not name a mode, use high-level for "the model" and pipeline for "the system". In C4
terms, high-level is the context or container view, low-level the component view, pipeline the container view
of a whole system. Name the mode you chose in the final message.

## Ask before drawing

Ask only the questions whose answer changes the figure, together in one message. If the user does not answer,
use the default in brackets and say so in the final message.

- Use: slide, paper, docs page or README? [docs page in the repository]
- Mode and scope: which mode, which variant or configuration? [the mode the request names, else the table]
- Parts: inference only, or training and losses too? Optional branches, such as a segmentation head?
  [inference only, no optional branches]
- Language: English labels, or another language? Vietnamese works with the default font. [English]
- Notes: annotate parts with notes that point at them, in which language? [no notes]
- Font: Patrick Hand (bundled, SIL OFL, fine for commercial use) or another? Stay With Me is personal use only.
  [Patrick Hand]
- Colour: module tints, a brand palette? [kind colours; tints only in a whole-model figure]
- Output: where do the spec and HTML go, is a PNG to be kept, and is a commit wanted? [spec and HTML beside the
  model's docs, else `docs/figures/`; PNG in a scratch folder outside the repository; no commit]
- Handoff: review only, or publish icons and figures to a Claude Design library? [review only]

## Workflow

1. **Read the facts.** Open the model code, configs and method write-up the figure describes. Note the file each
   shape, count and name comes from, and how each derived number (parameters, tokens, FLOPs) was computed.
   A fact you cannot confirm is left out or labelled `UNVERIFIED`, and listed in the final message.
2. **Start from the starter.** Copy the starter for the mode from `${CLAUDE_SKILL_DIR}/templates/` to the output
   folder as `<name>.figure.js` and edit the copy. Keep `FIGURE` and its `draw(k)` signature. Put the sources from
   step 1 and the build command in the header comment. For a whole-model figure, a notes edition or a translated
   edition, read `${CLAUDE_SKILL_DIR}/references/house-style.md` first. For every helper, kind, icon and font, see
   `${CLAUDE_SKILL_DIR}/references/kit.md`.
3. **Build.**

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/build_figure.py" <dir>/<name>.figure.js <dir>/<name>.html
   ```

4. **Check and render.** The check prints every layout issue and exits 1 if there is one; `--png` also writes a
   screenshot as tall as the page, issues or not.

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/check_figure.py" <dir>/<name>.html --png /tmp/figures/<name>.png
   ```

   Fix every issue in the spec, then build and check again.
5. **Look at the PNG** (open it with the Read tool). Look for what the checker cannot see: two connectors on one
   lane, an arrow head pointing the wrong way, a panel that hides boxes, an icon too small to read, a crowded or
   empty band, a label that says something the code does not. Fix each one, rebuild and look again before
   reporting.
6. **Report** the mode, the HTML and PNG paths, the defaults you used and any fact you could not confirm.
   Commit only after the user approves the figure, and then through the `commit-vcs` skill.

To publish approved icons or figures to a Claude Design library, the user runs `/design-sync`; this skill does
not call the DesignSync tool itself.

## Layout rules for every mode

- Connectors run in the gutters between columns, one lane per connector, lanes at least 30 apart.
- A connector that leaves a container goes through the container's edge and its gutter, never through a child.
- Prefer one clear lane per connector to a long snake route. When a tensor is used far from where it was made,
  repeat a small box labelled "same tensor" and say so in a note.
- Draw each panel before the boxes and connectors inside it: a panel's fill hides everything drawn earlier.
- Text sits inside its box. Card titles at 24 and body at 19 by default; in a whole-model figure, body 21 to 23
  and titles 23 to 26, because 19 is hard to read there.
- A two-line box at size 19 needs a height of at least 56.
- Each label has one meaning and one position. A label on a connector goes in the open gutter beside it, never on
  a box edge or across the line.
- Mark frozen parts with the snowflake and trained parts with the flame; dashed means training only. The legend
  lists every kind the figure uses.
- Number module panels in forward order (1 input, 2 encoder, ...), so the reader follows the numbers before the
  arrows.
- Labels use ASCII for symbols: `->`, `<=`, `sigma`, `x`. No emoji, and no font glyphs used as icons.

## Common mistakes

| Mistake | Fix |
| --- | --- |
| A shape or number written from memory | Read it from the code or config, and cite the file in the header |
| `connector crosses "..."` | Add a lane in the gutter and route through it |
| `connector runs through text` | Move the label into the open gutter, or move the lane |
| `text leaves "..."` | Shorten the label, or widen or heighten the box |
| `... leaves the canvas` | Raise `FIGURE.height` (last strip bottom plus about 40) or move the part in |
| `draw() stopped: ReferenceError: card is not defined` | Destructure every helper `draw()` uses from `k` |
| `draw() stopped: ... needs numbers` | A size argument is missing, or a field name is misspelt (`b.middle`) |
| Module panel hides the boxes inside it | Draw the panel before its contents |
| Body text too small on a dense figure | `cbox` (21) or `card` with `bodySize` 21 to 23; labels 20 or more |
| A symbol shows in a fallback font | Write it in ASCII; check the font's coverage in `references/kit.md` |
| Figure rebuilt with another font than before | Pass `--font` explicitly, as the spec header says |
| Several figures delivered when one was asked | Deliver exactly the figures asked for |

## Constraints

- Never edit files under `${CLAUDE_SKILL_DIR}/` from a user project: the plugin copy is replaced on every update.
  A figure that needs a new helper defines it in its own `draw()`; a kit change goes to the cv-kit repository
  (see "Changing the kit" in `references/kit.md`).
- Do not commit fonts from the cache, and do not commit scratch PNGs.
- Do not change a committed figure to suit a new style without asking. Build the new version beside it first.
- State the licence of a font other than the default when you use it; Stay With Me is personal use only.
