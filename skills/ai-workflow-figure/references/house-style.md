# House style for whole-model figures

Read this before drawing a whole-model figure or an annotated (notes) edition. The style was set on a
production model figure the owner approved on 2026-10-15 as more balanced than earlier figures, with clear
labels and icons that work. `templates/whole-model.figure.js` carries its grid and rhythm; the kit provides its
helpers (`module`, `cbox`, `frost`, `fire`). Keep every rule below.

## Grid

- The canvas is 1760 wide.
- The main column runs x 40 to 1120; the side column runs x 1180 to 1720.
- The 60-unit gutter between the columns holds the side lanes. The left margin (x 20) holds the main side's lane.
- Name these numbers once at the top of `draw()` (`X0, X1, SX1, RX0, LANE_*`) and use the names everywhere after.
- A full-width panel spans `X0` to `X1`.

## Vertical rhythm

- Leave 40 units between panels.
- Compute each panel's top from the one above (`P2 = P1 + H1 + 40`), never as a literal.
- Panels in one row share one height (`R_H`).
- A side-column panel ends level with the main-column panel beside it (`HS = P8 + H8 - PS`), so the two columns
  close on one line.
- Size each panel to its contents. An empty band at the bottom of a panel unbalances the row; fill the column or
  shorten the panel.
- Set the figure height to the last strip's bottom plus about 40.

## Module panels

- Use `module(x, y, w, h, kind, number, title, iconName, tint, subtitle)`.
- It draws a 38-unit number badge at (x + 14, y + 14), the icon beside it at scale 0.8, the title at 26 bold, and
  one subtitle line at 21 (at y + 74) that says what the module reads.
- Content starts at y + 86 to 92.
- Number the panels in forward order. Strips and summary panels (schedule, data, export) pass `null` as the
  number: they carry an icon and no badge.
- A module that exists only in training is a `dashed` panel.

## Icons

- The hand-drawn kit icons are part of the look: one per panel title, at scale 0.8, between the badge and the
  title.
- Choose the icon by what the module does:

  | module | icon |
  | --- | --- |
  | input or data | `image` |
  | transformer reader, attention trunk | `attention` |
  | patch or tile reader, per-patch head | `grid` |
  | convolutional stage | `conv` |
  | scoring head against prototypes | `target` |
  | anchor bank, stacked prototypes, memory | `stack` |
  | auxiliary or query heads, decoder queries | `query` |
  | fusion or combiner | `merge` |
  | detection output, export or slim build | `box` |
  | schedule or stages | `cascade` |
  | camera or video input | `camera`, `video` |
  | text encoder, prompt or captions | `text` |
  | embedding or projection head | `embed` |
  | segmentation head | `mask` |
  | pose or keypoint head | `keypoints` |
  | depth head, 3D lifting | `depth` |
  | tracker, association | `track` |
  | crop, resize, region of interest | `crop` |
  | serving, accelerator | `gpu` |

- When no icon fits, use the nearest one and say so in the final message, or add an icon to the kit in the
  cv-kit repository. Never give one icon two meanings in one figure.

- Frozen boxes get the snowflake and boxes with learned weights get the flame. Place them with `frost(b)` and
  `fire(b)`, which use a fixed corner offset, never by hand.
- No emoji or font glyphs.

## Boxes

- `cbox` is a titled box: title at 23 bold, 31 below its top; body lines at 21 with a pitch of 26; 16 below the
  last line; the height follows the lines.
- `sub` is the 80-high box with a title and one line (sizes 23 and 21).
- `tag` is a 50-high box. Use it bold for a head's output, as in `z_patch (B,)`.
- Inset children 15 from the edge of a narrow panel and 20 from a wide one.
- Stack boxes with gaps of 14 to 16, and leave 24 before the first loss box.

## Head panels read top to bottom

The order is: the operation with its shapes, then the pooling, then the bold score tag, then the head's own dashed
loss boxes. A loss sits inside the panel whose part it trains, never in a separate losses band, so no arrow runs to
the bottom of the figure.

## Labels that read on their own

- A data box's title names the tensor and its shape: `region map (B, 2, 518, 518)`.
- Its body has at most two lines: what the values mean (`1 attack pixel, 0 bona fide, -1 unknown`) and how it lines
  up with other tensors (`ch 0 under the face view, ch 1 under the tile`).
- A loss box says four things: what it compares, against which tensor or channel, at which grid, and its weight.
- A head's subtitle says what it reads.

## Connectors

- Within a column, use straight drops.
- Anything that changes column goes through a named lane, one lane per connector, at least 30 units apart.
- An arrow enters a panel right of its title and subtitle, never through the badge, the title or the subtitle.
- A fan-out from one box runs along a bus at one fixed y.
- Head scores leave for the combiner each through its own lane.

## Legend and header

- The legend sits in two rows at the top (baselines near y 51 and y 100). It lists every kind the figure uses, plus
  the number badge.
- The figure subtitle gives the reading order by numbers and says what dashed means.
- The spec's header comment lists the files every fact was read from, how each count was derived, and the build
  command.

## Notes (annotated edition)

- A note explains why a part is the way it is; the part's own box still says what it is. Every claim in a note is
  read from the code or the method write-up, like any label.
- Draw it with `note(x, top, w, lines)` and join it to its part with `pointer(points)`, from the note's edge to the
  part's edge. One note, one part.
- Put a note under its part, 28 below it (the pointer's room), as wide as the part, where no data arrow leaves that
  part downward. Otherwise put it beside the part, level with it.
- Never put a note on a data path: route connectors around notes as around boxes.
- An annotated figure needs room: widen the canvas to 2000 (main column x 40 to 1260, side column x 1320 to 1960)
  and grow each panel by its notes.
- Build the annotated edition beside the plain one (`<name>.notes.figure.js` or `<name>.vi.figure.js`); the plain
  figure stays as it is.

## Delta figures

`templates/delta.figure.js` shows what changed between two versions of one model. The layout follows the
architecture-delta type of cathrynlavery/diagram-design (MIT): before, the numbered changes, after.

- Before sits at x 40 to 700, the changes at 740 to 1020, after at 1060 to 1720. Parts read top to bottom.
- Both sides are drawn from one `PARTS` list, so a part has the same place and the same name on both sides. A
  part that exists on one side only leaves its slot empty on the other.
- The change list is computed from `PARTS` and `EDGES`, never typed: only after is ADDED, only before is
  REMOVED, a different kind or different lines is CHANGED, different inputs is REWIRED. An added or removed part
  between two kept parts is its own change, not a rewire of its neighbours.
- A CHANGED part carries a short `change` line (`fine-tuned -> frozen`); the figure stops with an error without it.
- Each changed part carries a mark in its top-left corner: `+` added, `-` removed, `~` changed or rewired, with
  the number of its line in the change list. Never mark a removed part with a dashed outline: dashed means
  training only.
- Kind colours keep their meaning on both sides.
- A setting that changed without changing a part (learning rate, epochs) goes in the settings card.
- Read each side's facts from its own revision, and name both revisions in the header and the panel subtitles.
- Budget: 8 parts and 10 connectors per side. Over it, make one delta figure per module.

## Translated edition

- Titles, keywords, tensor names, shapes and formulas stay English; subtitles, body explanations and notes are
  translated.
- Set `lang` on `FIGURE` (for example `lang: "vi"`), so the page declares its language.
- The default font covers every Vietnamese letter. For another script, check the font has its glyphs: the checker
  reports a font that did not load, not a single glyph that fell back.

## Bottom strips

- These are full-width panels of four equal cards: `(X1 - X0 - 40 - 3 * 20) / 4` wide, 20 apart.
- The training schedule strip holds one card per stage (its share of the run, its step range, what learns, what is
  still), plus one card for the optimizer and the run.
- The training data strip holds the synthesis, augmentation and label or region rules.
- Cards in one strip share one height.
