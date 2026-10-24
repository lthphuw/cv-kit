# Layout rules and common mistakes

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
| `connectors N apart, lanes need 30` | Move one lane; if both leave one box, start them at the same point (a bus) |
| `connector runs along the edge of "..."` | Move the lane into the gutter, clear of the box's stroke |
| `connector segment ... is diagonal` | Add a corner point so every segment is horizontal or vertical |
| `text leaves "..."` | Shorten the label, or widen or heighten the box |
| `text runs into "..."` | Move the label into the open gutter, or shorten it |
| `text overlaps text` | Move one line by a full pitch (26 at size 19 to 21), or shorten it |
| `"..." crosses the edge of "..."` | Raise the panel height, or move the box inside the panel or clear of it |
| `panel "..." hides ...` | Draw the panel before its contents |
| `font not loaded` | Check the `--font` file and family; the bundled default always loads |
| `... leaves the canvas` | Raise `FIGURE.height` (last strip bottom plus about 40) or move the part in |
| `draw() stopped: ReferenceError: card is not defined` | Destructure every helper `draw()` uses from `k` |
| `draw() stopped: ... needs numbers` | A size argument is missing, or a field name is misspelt (`b.middle`) |
| Body text too small on a dense figure | `cbox` (21) or `card` with `bodySize` 21 to 23; labels 20 or more |
| A symbol shows in a fallback font | Write it in ASCII; check the font's coverage in `references/kit.md` |
| Figure rebuilt with another font than before | Pass `--font` explicitly, as the spec header says |
| Several figures delivered when one was asked | Deliver exactly the figures asked for |

