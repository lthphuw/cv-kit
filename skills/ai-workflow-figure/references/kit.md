# Figure kit reference

The spec format, the helpers, the kinds, icons, fonts, and what the layout check covers. All coordinates are in
viewBox units.

## Spec format

```js
const FIGURE = {
  title: "...", subtitle: "...", width: 1760, height: 640,
  lang: "en",  // optional; "vi" for a Vietnamese edition
  draw(k) {
    const { card, connect, box, left, snowflake, flame } = k;
    const a = card(40, 150, 280, "plain", "Input", ["face image", "resized to 224 px"]);
    const b = card(395, 150, 280, "frozen", "Encoder", ["pretrained"], { h: 130 });
    connect([[a.right, a.mid], [b.left, b.mid]]);
  }
};
```

Destructure every helper `draw()` uses. Whatever stops `draw()` (a helper used but not destructured, an unknown
kind or icon, a missing size argument, a misspelt field that gives NaN) is the first issue the check reports, as
`draw() stopped: <error>`. Size arguments have no defaults.

Every box helper returns `{ x, y, w, h, left, right, top, bottom, mid, cx }`; route connectors from these
fields, not from literals.

## Helpers

- `box(x, y, w, h, kind, name, style)`: a plain box. Connectors must route around it. `style` is optional
  `{ fill, stroke }` to override the kind's colours.
- `panel(x, y, w, h, kind, name, style)`: a box that holds other boxes. Connectors may cross it. Its fill hides
  everything drawn before it, so draw it first.
- `card(x, top, w, kind, title, lines, opts)`: titled box, height from the lines (26 units per line) unless `opts.h`
  is set. Title at 24 (`opts.titleSize`), body at 19 (`opts.bodySize`), pitch 26 (`opts.lineHeight`). A line is a
  string or `{ text, bold }`. Used by the high-level, low-level and pipeline starters.
- `sub(x, top, w, h, kind, title, line, titleSize, lineSize)`: a bold title over one line.
- `tag(x, top, w, h, kind, str, size, bold)`: one centred line.
- `label(x, y, str, size, bold)`, `left(x, y, str, size)`, `text(x, y, str, size, bold, anchor)`: text at a
  baseline. `label` centres, `left` starts at x.
- `connect(points, open)`: orthogonal run through `[x, y]` points, with rounded corners and an arrow head at the
  end. `open` true omits the head. A repeated point is dropped, so a lane between two boxes at the same height
  needs no special case.
- `note(x, top, w, lines)`: an annotation, left-aligned lines at 20 on the note colour; height 15 + 25 per line.
  `pointer(points)`: a run like `connect`, dashed in the note colour, from the note to the part it explains. The
  layout check treats them like a box and a connector.
- `snowflake(cx, cy, r)`, `flame(cx, cy, s)`: the marks for frozen and trained parts.
- `icon(name, cx, cy, s, color)`: a named hand-drawn icon, 40 units square at scale `s`. `ICON_NAMES` lists the
  names.

House-style helpers (see `house-style.md`):

- `cbox(x, top, w, kind, title, lines, o)`: titled box; title 23 bold at top + 31, body 21 at a pitch of 26, 16
  below the last line. `o`: `ts`, `bs`, `lh`, `h`, `style`.
- `module(x, y, w, h, kind, number, title, iconName, tint, subtitle)`: a module panel with badge, icon, title and
  subtitle. `number` null draws no badge.
- `frost(b)`, `fire(b)`: the snowflake or flame at a fixed corner of box `b`.

A figure that needs a helper the kit lacks defines it inside its own `draw()`, built from the helpers above.

## Kinds

| Kind | Look | Meaning |
| --- | --- | --- |
| `plain` | White | Inputs, outputs, logic with no weights of its own |
| `frozen` | Blue, snowflake | Pretrained weights, never updated |
| `trained` | Orange, flame | Learned weights, kept at export |
| `aux` | Purple | Text side or monitoring, off the main path |
| `store` | Green, cylinder lid | Data or model artefacts |
| `dashed` | Grey dashed | Training only, or optional and dropped at export |
| `note` | Yellow, gold border | An annotation, not a component; see `note()` and `pointer()` |

## Icons and colour

- Icons are drawn with the same rough.js settings as the boxes (roughness 0.6, stroke 2), so they match the figure.
  Names: `window`, `global`, `attention`, `grid`, `image`, `norm`, `mlp`, `conv`, `merge`, `stack`, `target`,
  `box`, `query`, `loss`, `cascade`, plus the kind marks `trained`, `frozen`, `plain`, `dashed`. Build
  `templates/icon-sheet.figure.js` to see them all.
- Use `s` 0.5 for marks inside a box, 0.8 to 1.0 for panel titles.
- Photos are drawn as the `image` icon. The kit does not embed real images.
- Module colour is a tint on the panel background, passed as `{ fill }` in the style argument. The kind keeps its
  meaning: trained stays orange, dashed stays training-only. Example tints, one per module, all light enough for
  black text: `#e4eefb` blue, `#e3f4e6` green, `#efe7fb` purple, `#fff3c4` yellow, `#dff2ef` teal. Keep tints
  distinct from the kind colours.

## Fonts

| `--font` | Licence | Notes |
| --- | --- | --- |
| `patrick-hand` (default) | SIL OFL 1.1, commercial use allowed | Bundled full face: ASCII and every Vietnamese letter. No arrows, `σ` or `α`. |
| `patrick-hand-vi` | same | Alias of `patrick-hand`, kept for older build commands. |
| `stay-with-me` | Free for personal use only | Run `scripts/fetch_fonts.py` once; it saves the font and its terms to `~/.cache/ai-workflow-figure/fonts/`. ASCII only (221 glyphs): no Vietnamese, few symbols. Commercial or promotional use needs a licence from its author. |
| a font file | the file's own | `--font path/to/font.otf --font-family "Family Name"`; .otf, .ttf, .woff or .woff2. |

- Write `->`, `<=`, `sigma` in labels, not `→`, `≤`, `σ`: a missing glyph falls back to another face.
- Bold is synthesised from the regular face.
- Pass `--font` explicitly in a spec's build command when the figure does not use the default.

## What the layout check covers

`check_figure.py` waits for the font, then reports:

- text that leaves the box it sits in (the smallest box or panel that holds its anchor point);
- text that overlaps other text: lines whose ink bands meet (0.75 em above, 0.25 em below the baseline; the full
  font box is about 1.3 em tall and would flag lines that look clear), or two letters whose own ink meets, such
  as a Vietnamese capital with stacked marks (about 1 em tall) under a `g`;
- a connector through the interior of a box (not a panel);
- a connector through text, in a panel or in a gutter;
- a box, text or connector point outside the canvas (`width` x `height`);
- the font not loaded (the figure would use a fallback face);
- an error that stopped `draw()`.

Text bands for the box, canvas and connector checks are the fixed band stretched to the line's own ink.

It does not cover: connector-on-connector overlap, lanes closer than 30, a panel hiding boxes drawn before it,
arrow head direction, icons, a single glyph that fell back to another font, or whether the figure reads well. Look
at the PNG for those.

## Style references

- rough.js (MIT, [rough-stuff/rough](https://github.com/rough-stuff/rough)): `roughness` 0 is a perfect shape;
  `bowing` curves the strokes; `fillStyle` is one of hachure (default), solid, zigzag, cross-hatch, dots, dashed,
  zigzag-line. The kit uses solid fills and fixed seeds, so every build gives the same strokes. It is pinned at
  4.6.6 (`https://cdn.jsdelivr.net/npm/roughjs@4.6.6/bundled/rough.js`): a newer rough.js changes every stroke.
- Excalidraw is the source of the look: each element has `roughness` 0, 1 or 2 (Architect, Artist, Cartoonist),
  `fillStyle` hachure, cross-hatch or solid, and a `seed`. Its default font is Excalifont; check the licence file
  in the font's repository before bundling it.

Not in the kit: hachure fills, roughness presets and real images. Adding the first two changes the look of
existing figures, so each is a separate decision.

## Changing the kit

The kit is shared by every figure, and the plugin copy is replaced on each update, so change it only in the
cv-kit repository. A change must be additive: build every template before and after it and compare the `<svg>`
of each page (dump it with headless Chrome `--dump-dom`). Identical SVG means existing figures are unchanged.
Draw order fixes the rough.js seeds, so a helper that draws in a different order changes every stroke after it.
`tests/test_ai_workflow_figure.py` builds and checks every template.

`check_figure.py` keeps Chrome's sandbox on, except as root (Chrome will not start with it) or when `CI` is set.
