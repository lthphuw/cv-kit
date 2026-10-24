# Figure guide

Budget, sizing and the questions to ask before drawing a figure.

## Stay in budget

The box and connector counts are a budget, set on the starters. Over budget, a figure reads as a wall. Cut in
this order and stop as soon as the plan fits:

1. Repeated blocks become one box with a count (`Blocks 1-12`), as the low-level starter does.
2. A module's internals become one box; its own low-level figure shows them.
3. Side outputs that do not change the story go: logging, metrics, an EMA copy, hooks.
4. Still over: split into an overview figure and one detail figure per module.

For a high-level or pipeline figure, then ask of each part: can this box go, can these two boxes merge, can this
connector or label go, without losing a fact the reader needs? If yes, cut it. Do not apply this test to
low-level, whole-model or delta figures: their job is the detail.

## Fit the figure to its use

The figure is drawn in viewBox units and scaled to the width it is shown at, so one text size reads very
differently on a docs page, in a paper and on a slide:

    printed size in pt = text size in units x printed width in pt / canvas width in units

For example, body text at 19 on the 1760 canvas printed 240 pt wide is 19 x 240 / 1760 = 2.6 pt.

| Use | Canvas | How to size it |
| --- | --- | --- |
| Docs page or README | 1760 wide, as the starters | Nothing to change: the page shows it near full size. |
| Paper | Narrower than 1760 | Ask for the printed width (LaTeX prints it with `\the\columnwidth` or `\the\textwidth`) and the smallest text the user accepts in print. Canvas width = printed width x 19 / smallest size. |
| Slide | The slide's shape, for example 1760 x 990 for 16:9 | Ask for the slide width in pt and the smallest text; same formula. |

Never shrink text below the computed size to fit more: cut parts instead (see the budget). On a canvas much
narrower than 1760, only a high-level figure fits. Measure the width for every new template; do not assume one.

## Ask before drawing

Ask only the questions whose answer changes the figure, together in one message. If the user does not answer,
use the default in brackets and say so in the final message.

- Use: slide, paper, docs page or README? For a paper or slide, the printed width in pt and the smallest text
  size accepted. [docs page in the repository]
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

In the same message, give the plan: the mode, the canvas, the boxes you will draw, and what you will merge or
leave out to stay in budget. The user corrects a plan faster than a figure.

