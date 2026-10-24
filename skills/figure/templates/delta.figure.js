// Model delta figure: what changed between two versions of one model (baseline and ours, v1 and v2).
// Starter spec: before on the left, the numbered changes in the middle, after on the right.
// Both sides are drawn from one parts list, so a part keeps its place and its name on both sides,
// and the change list is worked out from the same data: it cannot miss a change or invent one.
// Read each side's facts from its own revision and name both here, for example:
//   before: <repo>@<rev>, <config file>
//   after:  <repo>@<rev>, <config file>
// Build:
//   python3 <skill>/scripts/build_figure.py <this file> <out.html>
// Keep at most 8 parts and 10 connectors per side. A setting that changed without changing a part
// (learning rate, epochs) goes in SETTINGS, not in the parts list.
const FIGURE = {
  title: "Model name: what changed from the baseline to ours",
  subtitle: "Left the baseline, right ours. A mark such as ~1 on a part is line 1 of the changes in the middle.",
  width: 1760,
  height: 980,
  draw(k) {
    const { panel, card, tag, label, left, box, connect, snowflake, flame, frost, fire } = k;
    // Columns: before x 40 to 700, changes 740 to 1020, after 1060 to 1720.
    const SIDE_W = 660, MID_X = 740, MID_W = 280, TOP = 100, PANEL_H = 840;
    const SIDES = { before: 40, after: 1060 };
    // Parts sit in one column, 100 in from the panel edge; lanes for a skipped part run on the right.
    const PART_IN = 100, PART_W = 460, PART_H = 90, PITCH = 124, FIRST = TOP + 100;
    const LANES = [600, 630];

    // One entry per part, top to bottom. before or after is null when the part exists on one side
    // only. A part whose kind or lines differ needs a short `change` line for the list.
    const PARTS = [
      { id: "input", name: "Input",
        before: { kind: "plain", lines: ["RGB, 224 px"] }, after: { kind: "plain", lines: ["RGB, 224 px"] } },
      { id: "encoder", name: "Encoder", change: "fine-tuned -> frozen",
        before: { kind: "trained", lines: ["ViT-B/16, all weights tuned"] },
        after: { kind: "frozen", lines: ["ViT-B/16, not updated"] } },
      { id: "adapter", name: "Adapter", before: null, after: { kind: "trained", lines: ["LoRA r8 on qkv"] } },
      { id: "pool", name: "Pooling", change: "mean -> CLS token",
        before: { kind: "plain", lines: ["mean of patch tokens"] }, after: { kind: "plain", lines: ["CLS token"] } },
      { id: "dropout", name: "Dropout", before: { kind: "plain", lines: ["p 0.1 before the head"] }, after: null },
      { id: "head", name: "Head", change: "1000 -> 2 classes",
        before: { kind: "trained", lines: ["linear 768 -> 1000"] }, after: { kind: "trained", lines: ["linear 768 -> 2"] } },
    ];
    // Connectors of each side, as [from, to] part ids, each from a part above to one below.
    const EDGES = {
      before: [["input", "encoder"], ["encoder", "pool"], ["pool", "dropout"], ["dropout", "head"]],
      after: [["input", "encoder"], ["encoder", "adapter"], ["adapter", "pool"], ["pool", "head"]],
    };
    const SETTINGS = ["lr 1e-3 -> 1e-4", "epochs 30 -> 10"];

    // ---- The change list, worked out from PARTS and EDGES ----
    const byId = Object.fromEntries(PARTS.map((p) => [p.id, p]));
    const common = new Set(PARTS.filter((p) => p.before && p.after).map((p) => p.id));
    // A part's inputs, seen through parts that exist on one side only: an added or removed part
    // between two kept parts is its own change, not a rewire of the parts around it.
    function inputs(side, id, seen) {
      const found = new Set();
      for (const [from, to] of EDGES[side]) {
        if (to !== id || seen.has(from)) { continue; }
        seen.add(from);
        if (common.has(from)) { found.add(from); } else { inputs(side, from, seen).forEach((x) => found.add(x)); }
      }
      return [...found].sort();
    }
    // A rewire is told as the inputs a part gained (+) and lost (-).
    function rewire(was, now) {
      const gained = now.filter((id) => !was.includes(id)).map((id) => "+ " + byId[id].name);
      const lost = was.filter((id) => !now.includes(id)).map((id) => "- " + byId[id].name);
      return "inputs " + [...gained, ...lost].join(", ");
    }
    const changes = [];
    for (const p of PARTS) {
      const b = p.before, a = p.after;
      if (!b) {
        changes.push({ id: p.id, mark: "+", word: "ADDED", detail: p.change || a.lines[0] });
      } else if (!a) {
        changes.push({ id: p.id, mark: "-", word: "REMOVED", detail: p.change || b.lines[0] });
      } else if (b.kind !== a.kind || JSON.stringify(b.lines) !== JSON.stringify(a.lines)) {
        if (!p.change) { throw new Error(`part "${p.name}" changed: give it a change line`); }
        changes.push({ id: p.id, mark: "~", word: "CHANGED", detail: p.change });
      }
      if (b && a) {
        const was = inputs("before", p.id, new Set()), now = inputs("after", p.id, new Set());
        if (was.join() !== now.join()) {
          changes.push({ id: p.id, mark: "~", word: "REWIRED", detail: rewire(was, now) });
        }
      }
    }
    changes.forEach((c, i) => { c.n = i + 1; });

    // ---- The two sides: one layout, so a part sits at the same place on both ----
    function drawSide(side, title, source) {
      const ox = SIDES[side];
      panel(ox, TOP, SIDE_W, PANEL_H, "plain", side);
      label(ox + SIDE_W / 2, TOP + 44, title, 26, true);
      label(ox + SIDE_W / 2, TOP + 74, source, 19);
      const drawn = {};
      PARTS.forEach((p, i) => {
        const part = p[side];
        if (!part) { return; }
        const b = card(ox + PART_IN, FIRST + i * PITCH, PART_W, part.kind, p.name, part.lines, { h: PART_H });
        if (part.kind === "frozen") { frost(b); }
        if (part.kind === "trained") { fire(b); }
        // An added part exists only after and a removed part only before, so each side shows its own marks.
        const marks = changes.filter((c) => c.id === p.id);
        if (marks.length) {
          const text = marks.map((c) => c.mark + c.n).join(" ");
          tag(b.x + 10, b.y + 10, 20 + 16 * text.length, 34, "plain", text, 20, true);
        }
        drawn[p.id] = { b, slot: i };
      });
      let lane = 0;
      for (const [from, to] of EDGES[side]) {
        const a = drawn[from].b, z = drawn[to].b;
        const between = PARTS.slice(drawn[from].slot + 1, drawn[to].slot).some((p) => p[side]);
        if (!between) {
          connect([[a.cx, a.bottom], [z.cx, z.top]]);
        } else {
          // A part in between: go round it through a lane on the right.
          const x = ox + LANES[lane++];
          connect([[a.right, a.mid], [x, a.mid], [x, z.mid], [z.right, z.mid]]);
        }
      }
    }
    drawSide("before", "Before: baseline", "baseline config, rev a1b2c3d");
    drawSide("after", "After: ours", "our config, rev d4e5f6a");

    // ---- The numbered changes, then the settings that changed ----
    panel(MID_X, TOP, MID_W, PANEL_H, "plain", "changes");
    label(MID_X + MID_W / 2, TOP + 44, "Changes", 26, true);
    let y = FIRST;
    for (const c of changes) {
      card(MID_X + 15, y, MID_W - 30, "plain", `${c.mark}${c.n} ${c.word} ${byId[c.id].name}`, [c.detail],
        { h: 86, titleSize: 21 });
      y += 98;
    }
    if (SETTINGS.length) {
      card(MID_X + 15, y + 12, MID_W - 30, "plain", "Settings", SETTINGS, { titleSize: 21 });
    }

    // ---- Legend, above the panels ----
    box(40, 30, 40, 26, "frozen");
    snowflake(112, 43, 9);
    left(140, 48, "frozen: not updated", 20);
    box(440, 30, 40, 26, "trained");
    flame(512, 43, 0.7);
    left(540, 48, "trained: learned weights", 20);
    left(880, 48, "Marks: + added, - removed, ~ changed or rewired; the number is the line in Changes", 20);
  }
};
