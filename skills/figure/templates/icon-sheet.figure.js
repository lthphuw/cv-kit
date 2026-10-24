// Icon sheet: every icon the kit draws, with its name, for review before a figure uses them.
// Build the same way as a figure:
//   python3 <skill>/scripts/build_figure.py <this file> <out.html>
// Names come from the kit (k.ICON_NAMES), so a new icon in the kit appears here with no edit.
// The height fits 30 icons in 5 columns; raise it by 190 for each extra row of five.
const FIGURE = {
  title: "Icon set: hand-drawn, one style",
  subtitle: "Each icon is drawn by the kit in a 40-unit square. Figures refer to icons by these names.",
  width: 1800,
  height: 1280,
  draw(k) {
    const { box, icon, label, ICON_NAMES } = k;
    ICON_NAMES.forEach((name, i) => {
      const x = 40 + (i % 5) * 350;
      const y = 120 + Math.floor(i / 5) * 190;
      box(x, y, 310, 170, "plain", name);
      icon(name, x + 155, y + 72, 2.2);
      label(x + 155, y + 152, name, 22, true);
    });
  }
};
