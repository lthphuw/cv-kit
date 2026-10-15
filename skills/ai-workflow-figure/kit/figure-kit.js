// Hand-drawn figure kit, shared by every figure. A figure spec calls these helpers
// and never writes SVG itself, so strokes, arrows, icons and checks stay uniform.
// Needs rough.js loaded first; rc is rough.svg(svg).
function createFigureKit(svg, rc) {
  const NS = "http://www.w3.org/2000/svg";
  const INK = "#2b2b2b";
  const KIND = {
    plain: { fill: "#fffdf8", stroke: INK },
    frozen: { fill: "#d5e4fb", stroke: "#2f5fa8" },
    trained: { fill: "#fde0b8", stroke: "#9a5300" },
    aux: { fill: "#e6d8f7", stroke: "#5f3c9c" },
    store: { fill: "#dcefe0", stroke: "#2e6b3e" },
    dashed: { fill: "none", stroke: "#6b6b6b" },
    // An annotation, not a component: it explains the part its pointer reaches.
    note: { fill: "#ffec8b", stroke: "#b8860b" }
  };
  // A note's pointer: the note's colour and a dash, so it never reads as a tensor.
  const POINTER = { stroke: "#b8860b", dash: [7, 6] };
  const NOTE_SIZE = 20;
  const NOTE_LINE = 25;
  const NOTE_PAD = 14;
  // Baseline-to-baseline distance of body lines, in viewBox units.
  const LINE = 26;
  const CORNER = 14;
  const ARROW_LEN = 14;
  const ARROW_HALF = 7;
  const STORE_LID = 24;
  // A connector may run along a box edge; the crossing check ignores this much of it.
  const EDGE_TOLERANCE = 2;
  // Text closer than this to its box edge counts as overflowing.
  const TEXT_MARGIN = 4;
  // The ink band of a line, in em above and below the baseline. getBBox() reports
  // the full font box (about 1.3 em tall), which would flag neighbouring lines that
  // look clear, so the checks use the band the letters occupy instead.
  // finish() raises the band to the measured ink of a line whose letters reach further.
  const INK_ASCENT = 0.75;
  const INK_DESCENT = 0.25;

  // Park-Miller generator: fixed seeds give the same strokes on every build.
  let seed = 11;
  function nextSeed() {
    seed = (seed * 16807) % 2147483647;
    return seed;
  }

  // Kept so finish() can check the layout once the font has loaded.
  const shapes = [];
  const texts = [];
  const connectors = [];

  // A missing argument or a misspelt field (b.middle) is NaN by the time it is drawn, and NaN
  // compares false, so every layout check would pass it. Stop the drawing with its name instead.
  function requireNumbers(what, values) {
    if (!values.every(Number.isFinite)) {
      throw new Error(what + " needs numbers, got " + JSON.stringify(values.map(String)));
    }
  }

  // style is optional: {fill, stroke} overrides the kind's colours, e.g. a module tint.
  function makeBox(x, y, w, h, kind, name, container, style) {
    const k = KIND[kind];
    if (!k) {
      throw new Error("unknown box kind: " + JSON.stringify(kind));
    }
    requireNumbers("box " + JSON.stringify(name || "") + " (x, y, w, h)", [x, y, w, h]);
    const fill = style && style.fill ? style.fill : k.fill;
    const stroke = style && style.stroke ? style.stroke : k.stroke;
    const opts = { roughness: 1.2, bowing: 1, strokeWidth: 2.4, seed: nextSeed(),
                   fill, fillStyle: "solid", stroke };
    if (kind === "dashed") { opts.strokeLineDash = [10, 8]; }
    svg.appendChild(rc.rectangle(x, y, w, h, opts));
    if (kind === "store") {
      svg.appendChild(rc.ellipse(x + w / 2, y, w, STORE_LID,
        { stroke: k.stroke, strokeWidth: 2.4, roughness: 1, seed: nextSeed() }));
    }
    const b = { x, y, w, h, left: x, right: x + w, top: y, bottom: y + h,
                mid: y + h / 2, cx: x + w / 2,
                name: name || "box at " + x + "," + y, container };
    shapes.push(b);
    return b;
  }

  // A box holds text; connectors must route around it.
  function box(x, y, w, h, kind, name, style) {
    return makeBox(x, y, w, h, kind, name, false, style);
  }
  // A panel groups boxes; connectors may cross it. A panel's fill hides everything drawn
  // before it, so draw panels before the boxes and connectors inside them.
  function panel(x, y, w, h, kind, name, style) {
    return makeBox(x, y, w, h, kind, name, true, style);
  }

  function text(x, y, str, size, bold, anchor) {
    requireNumbers("text " + JSON.stringify(str) + " (x, y, size)", [x, y, size]);
    const t = document.createElementNS(NS, "text");
    t.setAttribute("x", x);
    t.setAttribute("y", y);
    t.setAttribute("font-size", size);
    if (anchor) { t.setAttribute("text-anchor", anchor); }
    if (bold) { t.setAttribute("font-weight", "700"); }
    t.textContent = str;
    svg.appendChild(t);
    texts.push({ el: t, x, y, size, str });
  }
  function label(x, y, str, size, bold) { text(x, y, str, size, bold, "middle"); }
  function left(x, y, str, size) { text(x, y, str, size, false, null); }

  // Titled box with centred lines (a line is a string or {text, bold}); card and cbox differ only
  // in the metrics m: title and first-line baselines below the top, base height, pitch, sizes.
  function titledBox(x, top, w, kind, title, lines, m) {
    const h = m.h || m.base + m.pitch * lines.length;
    const b = box(x, top, w, h, kind, title, m.style);
    label(b.cx, top + m.titleY, title, m.titleSize, true);
    lines.forEach((line, i) => {
      const item = typeof line === "string" ? { text: line, bold: false } : line;
      label(b.cx, top + m.firstY + i * m.pitch, item.text, m.bodySize, item.bold);
    });
    return b;
  }

  // Titled box; its height follows the body lines unless opts.h is set.
  // opts.bodySize and opts.lineHeight raise the body text for dense figures; the defaults are 19 and 26.
  function card(x, top, w, kind, title, lines, opts) {
    const o = opts || {};
    const pitch = o.lineHeight || LINE;
    return titledBox(x, top, w, kind, title, lines, { h: o.h, style: o.style, titleY: 40, firstY: 70,
      base: 64, pitch, titleSize: o.titleSize || 24, bodySize: o.bodySize || 19 });
  }

  // Small box: bold title over one line.
  function sub(x, top, w, h, kind, title, line, titleSize, lineSize) {
    const b = box(x, top, w, h, kind, title);
    label(b.cx, top + h * 0.42, title, titleSize, true);
    label(b.cx, top + h * 0.78, line, lineSize);
    return b;
  }

  // Box with one centred line.
  function tag(x, top, w, h, kind, str, size, bold) {
    const b = box(x, top, w, h, kind, str);
    label(b.cx, b.mid + size * 0.35, str, size, bold);
    return b;
  }

  // Annotation: left-aligned lines on a note-coloured box, height from the lines.
  // Pair it with pointer() from its edge to the part it explains.
  function note(x, top, w, lines) {
    const h = 15 + NOTE_LINE * lines.length;
    const b = box(x, top, w, h, "note", "note: " + lines[0]);
    lines.forEach((line, i) => {
      left(x + NOTE_PAD, top + 27 + i * NOTE_LINE, line, NOTE_SIZE);
    });
    return b;
  }

  // ---- House style (references/house-style.md): whole-model figures use these four ----

  // Titled box, height from its lines: 31 to the title baseline, one pitch per line, 16 below.
  // o: ts title size (23), bs body size (21), lh line pitch (26), h fixed height, style {fill, stroke}.
  function cbox(x, top, w, kind, title, lines, o) {
    const opt = o || {};
    const pitch = opt.lh || LINE;
    return titledBox(x, top, w, kind, title, lines, { h: opt.h, style: opt.style, titleY: 31,
      firstY: 31 + pitch, base: 31 + 16, pitch, titleSize: opt.ts || 23, bodySize: opt.bs || 21 });
  }

  // Module panel: number badge, icon, title at 26 bold, one subtitle line at 21 (y + 74).
  // A null number draws the icon in the badge's place (strips and summary panels). Draw it
  // before its contents; contents start at y + 86 to 92.
  function module(x, y, w, h, kind, number, title, iconName, tint, subtitle) {
    const p = panel(x, y, w, h, kind, "panel " + title, { fill: tint });
    let titleX = x + 62;
    if (number) {
      box(x + 14, y + 14, 38, 38, "plain", "badge " + number);
      label(x + 33, y + 41, number, 24, true);
      titleX = x + 112;
      icon(iconName, x + 82, y + 33, 0.8);
    } else {
      icon(iconName, x + 32, y + 33, 0.8);
    }
    text(titleX, y + 43, title, 26, true, null);
    if (subtitle) {
      text(x + 20, y + 74, subtitle, 21, false, null);
    }
    return p;
  }

  // Kind marks at a fixed corner offset: a snowflake on a frozen box, a flame on a trained one.
  function frost(b) { snowflake(b.right - 22, b.top + 22, 9); }
  function fire(b) { flame(b.right - 18, b.top + 22, 0.55); }

  // Frozen parts carry a snowflake, trained parts a flame (model figures).
  // Each of the six arm ends forks outward, so no end reads as an arrow head.
  function snowflake(cx, cy, r) {
    const col = "#2f5fa8";
    for (let a = 0; a < 3; a++) {
      const th = a * Math.PI / 3;
      const dx = r * Math.cos(th), dy = r * Math.sin(th);
      svg.appendChild(rc.line(cx - dx, cy - dy, cx + dx, cy + dy,
        { stroke: col, strokeWidth: 2, roughness: 0.5, seed: nextSeed() }));
      for (const [px, py, outward] of [[cx + dx, cy + dy, th], [cx - dx, cy - dy, th + Math.PI]]) {
        for (const d of [-1, 1]) {
          const ang = outward + d * Math.PI / 4;
          svg.appendChild(rc.line(px, py, px + 0.4 * r * Math.cos(ang), py + 0.4 * r * Math.sin(ang),
            { stroke: col, strokeWidth: 2, roughness: 0.5, seed: nextSeed() }));
        }
      }
    }
  }
  function flame(cx, cy, s) {
    const p = (x, y) => (cx + x * s).toFixed(1) + " " + (cy + y * s).toFixed(1);
    const outer = `M ${p(0, -15)} C ${p(8, -7)} ${p(11, 3)} ${p(7, 11)} C ${p(4, 15)} ${p(-4, 15)} ${p(-7, 11)} C ${p(-11, 3)} ${p(-8, -7)} ${p(0, -15)} Z`;
    svg.appendChild(rc.path(outer, { fill: "#f08a24", fillStyle: "solid", stroke: "#9a5300",
      strokeWidth: 1.8, roughness: 0.6, seed: nextSeed() }));
    const inner = `M ${p(0, -3)} C ${p(3, 2)} ${p(4, 7)} ${p(0, 9)} C ${p(-3, 7)} ${p(-3, 2)} ${p(0, -3)} Z`;
    svg.appendChild(rc.path(inner, { fill: "#ffd27a", fillStyle: "solid", stroke: "#9a5300",
      strokeWidth: 1.2, roughness: 0.4, seed: nextSeed() }));
  }

  // One connector style for the whole figure: rounded right-angle runs, filled head.
  function roundedPath(points) {
    let d = "M " + points[0][0] + " " + points[0][1];
    for (let i = 1; i < points.length - 1; i++) {
      const [px, py] = points[i - 1];
      const [cx, cy] = points[i];
      const [nx, ny] = points[i + 1];
      const v1x = cx - px, v1y = cy - py, v2x = nx - cx, v2y = ny - cy;
      const l1 = Math.hypot(v1x, v1y), l2 = Math.hypot(v2x, v2y);
      const r = Math.min(CORNER, l1 / 2, l2 / 2);
      d += " L " + (cx - v1x / l1 * r) + " " + (cy - v1y / l1 * r);
      d += " Q " + cx + " " + cy + " " + (cx + v2x / l2 * r) + " " + (cy + v2y / l2 * r);
    }
    const last = points[points.length - 1];
    return d + " L " + last[0] + " " + last[1];
  }
  function arrowHead(x1, y1, x2, y2, color) {
    const a = Math.atan2(y2 - y1, x2 - x1);
    const bx = x2 - ARROW_LEN * Math.cos(a), by = y2 - ARROW_LEN * Math.sin(a);
    svg.appendChild(rc.polygon(
      [[x2, y2], [bx + ARROW_HALF * Math.sin(a), by - ARROW_HALF * Math.cos(a)],
       [bx - ARROW_HALF * Math.sin(a), by + ARROW_HALF * Math.cos(a)]],
      { fill: color, fillStyle: "solid", stroke: color, roughness: 0.4, seed: nextSeed() }));
  }
  // One run with a head at its end; the layout check treats every run alike.
  // A repeated point (a lane between two boxes at the same height) would give a zero-length
  // segment and a 0/0 corner, so repeats are dropped first.
  function run(points, open, stroke, dash) {
    points.forEach((p, i) => requireNumbers("connector point " + i, p));
    points = points.filter((p, i) => i === 0 || p[0] !== points[i - 1][0] || p[1] !== points[i - 1][1]);
    if (points.length < 2) {
      throw new Error("a connector needs two distinct points");
    }
    connectors.push(points);
    const opts = { roughness: 0.5, bowing: 0.3, strokeWidth: 2.4, stroke, seed: nextSeed() };
    if (dash) { opts.strokeLineDash = dash; }
    svg.appendChild(rc.path(roundedPath(points), opts));
    if (!open) {
      const [x1, y1] = points[points.length - 2];
      const [x2, y2] = points[points.length - 1];
      arrowHead(x1, y1, x2, y2, stroke);
    }
  }
  // Points are [x, y] pairs of an orthogonal run; open = no arrow head.
  function connect(points, open) { run(points, open, INK, null); }
  // From a note's edge to the part it explains, in the note's colour and dashed.
  function pointer(points) { run(points, false, POINTER.stroke, POINTER.dash); }

  // Smallest shape whose area holds the point; the text it anchors belongs to it.
  function ownerAt(x, y) {
    let owner = null;
    for (const s of shapes) {
      const inside = x >= s.left && x <= s.right && y >= s.top && y <= s.bottom;
      if (inside && (!owner || s.w * s.h < owner.w * owner.h)) { owner = s; }
    }
    return owner;
  }
  function overlap(a, b) {
    return a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
  }
  function segmentBounds(p, q) {
    return { left: Math.min(p[0], q[0]), right: Math.max(p[0], q[0]),
             top: Math.min(p[1], q[1]), bottom: Math.max(p[1], q[1]) };
  }
  function crossesBox(seg, s) {
    return seg.left <= s.right - EDGE_TOLERANCE && seg.right >= s.left + EDGE_TOLERANCE &&
           seg.top <= s.bottom - EDGE_TOLERANCE && seg.bottom >= s.top + EDGE_TOLERANCE;
  }

  // Measures the drawn text, so call it once the font has loaded. Writes the
  // report into the page as JSON, for scripts/check_figure.py to read.
  // drawError is what FIGURE.draw() threw, if anything; it is reported as the first issue.
  function finish(fontLoaded, drawError) {
    const issues = [];
    if (drawError) { issues.push("draw() stopped: " + drawError); }
    if (!fontLoaded) { issues.push("font not loaded: text fell back to a system font"); }
    // Two bands per line: the fixed one, and the fixed one stretched to the line's own ink, since
    // stacked accents (Vietnamese capitals reach about 1 em), a tall apostrophe and descenders
    // can pass it. Box, canvas and connector checks use the stretched band.
    const ink = document.createElement("canvas").getContext("2d");
    const lines = texts.map((t) => {
      const r = t.el.getBBox();
      const style = getComputedStyle(t.el);
      const font = `${style.fontWeight} ${t.size}px ${style.fontFamily}`;
      ink.font = font;
      const m = ink.measureText(t.str);
      const fixed = { left: r.x, right: r.x + r.width,
                      top: t.y - INK_ASCENT * t.size, bottom: t.y + INK_DESCENT * t.size };
      const band = { left: fixed.left, right: fixed.right,
                     top: Math.min(fixed.top, t.y - m.actualBoundingBoxAscent),
                     bottom: Math.max(fixed.bottom, t.y + m.actualBoundingBoxDescent) };
      return { fixed, band, font, glyphs: null };
    });
    const bounds = lines.map((l) => l.band);
    // Ink box of each letter, measured on demand: a tall mark in one line clashes with a
    // descender in the next only where the two letters meet.
    function glyphs(i) {
      const l = lines[i], t = texts[i];
      if (!l.glyphs) {
        ink.font = l.font;
        l.glyphs = [];
        let prefix = "";
        for (const ch of Array.from(t.str)) {
          const x = l.fixed.left + ink.measureText(prefix).width;
          prefix += ch;
          if (!ch.trim()) { continue; }
          const m = ink.measureText(ch);
          l.glyphs.push({ left: x - m.actualBoundingBoxLeft, right: x + m.actualBoundingBoxRight,
                          top: t.y - m.actualBoundingBoxAscent, bottom: t.y + m.actualBoundingBoxDescent });
        }
      }
      return l.glyphs;
    }
    function textsClash(i, j) {
      if (overlap(lines[i].fixed, lines[j].fixed)) { return true; }
      return overlap(bounds[i], bounds[j]) && glyphs(i).some((a) => glyphs(j).some((b) => overlap(a, b)));
    }
    texts.forEach((t, i) => {
      const owner = ownerAt(t.x, t.y);
      if (!owner) { return; }
      const r = bounds[i];
      const outside = r.left < owner.left + TEXT_MARGIN || r.right > owner.right - TEXT_MARGIN ||
                      r.top < owner.top + TEXT_MARGIN || r.bottom > owner.bottom - TEXT_MARGIN;
      if (outside) {
        issues.push(`text leaves "${owner.name}": ${JSON.stringify(t.str)}`);
      }
    });
    for (let i = 0; i < texts.length; i++) {
      for (let j = i + 1; j < texts.length; j++) {
        if (textsClash(i, j)) {
          issues.push(`text overlaps text: ${JSON.stringify(texts[i].str)} and ${JSON.stringify(texts[j].str)}`);
        }
      }
    }
    for (const points of connectors) {
      for (let i = 1; i < points.length; i++) {
        const seg = segmentBounds(points[i - 1], points[i]);
        for (const s of shapes) {
          if (!s.container && crossesBox(seg, s)) {
            issues.push(`connector crosses "${s.name}"`);
          }
        }
        // A line drawn over letters makes them unreadable, inside a panel or in a gutter.
        texts.forEach((t, j) => {
          if (overlap(seg, bounds[j])) {
            issues.push(`connector runs through text ${JSON.stringify(t.str)}`);
          }
        });
      }
    }
    // Anything past the viewBox is cropped from the figure.
    const view = svg.viewBox.baseVal;
    if (view && view.width > 0) {
      const off = (r) => r.left < 0 || r.top < 0 || r.right > view.width || r.bottom > view.height;
      shapes.filter(off).forEach((s) => issues.push(`"${s.name}" leaves the canvas`));
      texts.forEach((t, i) => {
        if (off(bounds[i])) { issues.push(`text leaves the canvas: ${JSON.stringify(t.str)}`); }
      });
      if (connectors.some((points) => points.some(([x, y]) => off({ left: x, right: x, top: y, bottom: y })))) {
        issues.push("a connector leaves the canvas");
      }
    }
    // The content height (not the viewport's) lets check_figure.py size a screenshot that
    // holds the whole figure and nothing below it.
    const pageHeight = Math.ceil(document.body.getBoundingClientRect().height);
    const report = { shapes: shapes.length, texts: texts.length, connectors: connectors.length,
                     pageHeight, issues: [...new Set(issues)] };
    svg.setAttribute("data-layout", report.issues.length === 0 ? "ok" : "issues");
    const node = document.createElement("script");
    node.type = "application/json";
    node.id = "layout-report";
    node.textContent = JSON.stringify(report);
    document.body.appendChild(node);
  }

  // Hand-drawn icons: each is drawn in a 40-unit square centred on (cx, cy), scaled by s.
  // Local coordinates run from -20 to 20 with y down. Strokes use the figure ink unless color is given.
  const ICON_ROUGH = 0.6;
  const ICON_STROKE = 2;
  const ICON_SUN = "#ffd27a";
  const ICON_FILL = "#fde0b8";
  function iconPen(cx, cy, s, color) {
    const at = (x, y) => [cx + x * s, cy + y * s];
    const opts = (fill) => ({ stroke: color, strokeWidth: ICON_STROKE, roughness: ICON_ROUGH,
                              seed: nextSeed(), fill: fill || "none", fillStyle: "solid" });
    return {
      cx, cy, s, color, at,
      line(x1, y1, x2, y2) {
        const a = at(x1, y1), b = at(x2, y2);
        svg.appendChild(rc.line(a[0], a[1], b[0], b[1], opts()));
      },
      rect(x, y, w, h, fill) {
        const a = at(x, y);
        svg.appendChild(rc.rectangle(a[0], a[1], w * s, h * s, opts(fill)));
      },
      dashedRect(x, y, w, h) {
        const a = at(x, y);
        svg.appendChild(rc.rectangle(a[0], a[1], w * s, h * s,
          { ...opts(), strokeLineDash: [4, 3] }));
      },
      circle(x, y, r, fill) {
        const a = at(x, y);
        svg.appendChild(rc.circle(a[0], a[1], 2 * r * s, opts(fill)));
      },
      poly(points, fill) {
        svg.appendChild(rc.polygon(points.map(([x, y]) => at(x, y)), opts(fill)));
      },
      path(d, fill) {
        svg.appendChild(rc.path(d, opts(fill)));
      },
      head(x1, y1, x2, y2) {
        const tip = at(x2, y2), a = Math.atan2(y2 - y1, x2 - x1), len = 7 * s, half = 3.5 * s;
        const bx = tip[0] - len * Math.cos(a), by = tip[1] - len * Math.sin(a);
        svg.appendChild(rc.polygon([tip, [bx + half * Math.sin(a), by - half * Math.cos(a)],
          [bx - half * Math.sin(a), by + half * Math.cos(a)]], opts(color)));
      },
    };
  }
  const ICON_DRAW = {
    // Input photo: frame, mountain, sun.
    image(g) {
      g.rect(-18, -14, 36, 28);
      g.poly([[-14, 10], [-4, -2], [4, 6], [9, 0], [14, 10]]);
      g.circle(8, -6, 3, ICON_SUN);
    },
    // Patch tokens: a 4 x 4 grid of cells.
    grid(g) {
      for (let r = 0; r < 4; r++) {
        for (let c = 0; c < 4; c++) { g.rect(-12 + c * 8, -12 + r * 8, 6, 6); }
      }
    },
    // Windowed attention: four separate windows.
    window(g) {
      g.rect(-16, -16, 14, 14, ICON_FILL);
      g.rect(2, -16, 14, 14, ICON_FILL);
      g.rect(-16, 2, 14, 14, ICON_FILL);
      g.rect(2, 2, 14, 14, ICON_FILL);
    },
    // Global attention: one circle that covers everything.
    global(g) {
      g.circle(0, 0, 16);
      g.line(-16, 0, 16, 0);
      g.line(0, -16, 0, 16);
    },
    // Attention: three nodes that all connect.
    attention(g) {
      g.circle(-14, -10, 5);
      g.circle(14, -10, 5);
      g.circle(0, 12, 5);
      g.line(-9, -10, 9, -10);
      g.line(-11, -6, -2, 8);
      g.line(11, -6, 2, 8);
    },
    // LayerNorm: bars normalised around a mean line.
    norm(g) {
      g.rect(-14, -2, 6, 16, ICON_FILL);
      g.rect(-4, -10, 6, 24, ICON_FILL);
      g.rect(6, -6, 6, 20, ICON_FILL);
      g.line(-18, 0, 18, 0);
    },
    // MLP: 2, 3 and 1 nodes in three layers.
    mlp(g) {
      for (const y of [-8, 8]) { g.circle(-12, y, 3, ICON_FILL); }
      for (const y of [-12, 0, 12]) { g.circle(0, y, 3, ICON_FILL); }
      g.circle(12, 0, 3, ICON_FILL);
      for (const y of [-8, 8]) {
        for (const y2 of [-12, 0, 12]) { g.line(-12, y, 0, y2); }
      }
      for (const y of [-12, 0, 12]) { g.line(0, y, 12, 0); }
    },
    // Convolution kernel: a 3 x 3 grid.
    conv(g) {
      for (let r = 0; r < 3; r++) {
        for (let c = 0; c < 3; c++) { g.rect(-14 + c * 10, -14 + r * 10, 8, 8); }
      }
    },
    // Concat: two inputs merge into one run with a head.
    merge(g) {
      g.line(-16, -16, 0, -4);
      g.line(16, -16, 0, -4);
      g.line(0, -4, 0, 10);
      g.head(0, 4, 0, 16);
    },
    // Memory or layers: three stacked sheets.
    stack(g) {
      g.rect(-16, -16, 32, 9, ICON_FILL);
      g.rect(-16, -4, 32, 9, ICON_FILL);
      g.rect(-16, 8, 32, 9, ICON_FILL);
    },
    // Matching target: concentric rings.
    target(g) {
      g.circle(0, 0, 16);
      g.circle(0, 0, 10);
      g.circle(0, 0, 4, ICON_SUN);
    },
    // Bounding box: a rectangle with corner handles.
    box(g) {
      g.rect(-14, -10, 28, 22);
      g.rect(-17, -13, 6, 6, ICON_SUN);
      g.rect(11, -13, 6, 6, ICON_SUN);
      g.rect(-17, 9, 6, 6, ICON_SUN);
      g.rect(11, 9, 6, 6, ICON_SUN);
    },
    // Query: a point that drives into the decoder.
    query(g) {
      g.circle(-14, 0, 4, ICON_SUN);
      g.line(-9, 0, 9, 0);
      g.head(-9, 0, 14, 0);
    },
    // Loss curve: axes and a falling curve.
    loss(g) {
      g.line(-16, 16, 16, 16);
      g.line(-16, 16, -16, -16);
      g.path(`M ${g.at(-12, -8).join(" ")} C ${g.at(-4, -8).join(" ")} ${g.at(-2, 10).join(" ")} ${g.at(12, 10).join(" ")}`);
    },
    // Repeated layers: three offset cards.
    cascade(g) {
      g.rect(-16, -16, 24, 18, ICON_FILL);
      g.rect(-10, -10, 24, 18, ICON_FILL);
      g.rect(-4, -4, 24, 18, ICON_FILL);
    },
    // Kind icons: the same marks the boxes carry, so a legend can use the icon set.
    // trained and frozen reuse flame() and snowflake(); plain and dashed are drawn here.
    trained(g) { flame(g.cx, g.cy, g.s); },
    frozen(g) { snowflake(g.cx, g.cy, 18 * g.s); },
    plain(g) {
      g.rect(-16, -16, 32, 32);
      g.line(-10, -6, 10, -6);
      g.line(-10, 0, 10, 0);
      g.line(-10, 6, 4, 6);
    },
    dashed(g) { g.dashedRect(-16, -16, 32, 32); },
  };
  const ICON_NAMES = Object.keys(ICON_DRAW);
  // Draws a named icon; color defaults to the figure ink.
  function icon(name, cx, cy, s, color) {
    const draw = ICON_DRAW[name];
    if (!draw) {
      throw new Error("unknown icon: " + JSON.stringify(name));
    }
    draw(iconPen(cx, cy, s || 1, color || INK));
  }

  return { box, panel, card, sub, tag, note, text, label, left, snowflake, flame, connect, pointer,
           cbox, module, frost, fire, finish, icon, ICON_NAMES };
}
