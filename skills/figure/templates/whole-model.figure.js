// Whole-model figure in the house style: numbered module panels on a two-column grid,
// losses inside the panel they train, full-width strips at the bottom. The rules are in the
// skill's references/house-style.md; cbox, module, frost and fire come from the kit.
// Header to keep in a real spec: where every fact was read (files), how each count was
// derived, and the build command:
//   python3 <skill>/scripts/build_figure.py <this file> <out.html>
const FIGURE = {
  title: "model_name: one line on what the model does",
  subtitle: "Whole model with its training parts. Follow the numbers: 1 input, 2 to 4 the main side, 5 the side reader, 6 the combiner. Dashed: training only.",
  width: 1760,
  height: 1710,
  draw(k) {
    const { box, sub, tag, label, left, snowflake, flame, connect, cbox, module, frost, fire } = k;

    // One light tint per module, distinct from the kind colours.
    const TINT = {
      input: "#f2efe7",
      main: "#fff3c4",
      headA: "#e4eefb",
      headB: "#e3f4e6",
      side: "#dff2ef",
      combiner: "#fde9e7",
      summary: "#f7f1e3",
      strip: "#fbf8f0"
    };

    // ---- Grid: main column x 40-1120, side column x 1180-1720, gaps of 40 between panels ----
    const X0 = 40, X1 = 1720, SX1 = 1120, RX0 = 1180, GAP = 40;
    // Lanes, 30 apart: the left margin for the main side, two in the 60-unit gutter between columns.
    const LANE_MAIN = 20, LANE_HEAD_B = 1135, LANE_SIDE = 1165;
    // A loss box says what it compares, against which tensor, at which grid, and its weight.
    const LOSS = ["what it compares, against which tensor", "at which grid; weight w"];

    // ---- Legend, two rows ----
    snowflake(56, 44, 12);
    left(80, 51, "FROZEN: pretrained, never updated", 21);
    flame(470, 44, 0.9);
    left(494, 51, "TRAINED: learned weights", 21);
    box(40, 80, 40, 26, "dashed", "legend training only");
    left(92, 100, "TRAINING ONLY: dropped at export", 21);
    box(470, 76, 34, 34, "plain", "legend badge");
    label(487, 100, "n", 22, true);
    left(522, 100, "module n, in forward order; arrows carry tensors", 21);

    // ---- 1 Input, full width ----
    const P1 = 125, H1 = 200;
    module(X0, P1, X1 - X0, H1, "plain", "1", "Input", "image", TINT.input);
    const source = sub(60, P1 + 66, 500, 80, "plain", "image (B, 3, H, W)", "what enters the model", 23, 21);
    const prepared = sub(1220, P1 + 66, 480, 80, "plain", "prepared input (B, C, S, S)",
      "resized and normalised", 23, 21);

    // ---- 2 Main reader, main column ----
    const P2 = P1 + H1 + GAP, H2 = 300;
    module(X0, P2, SX1 - X0, H2, "plain", "2", "Main reader: backbone at S px", "attention",
      TINT.main, "one line: weights, input size, token count");
    const trunk = sub(60, P2 + 92, 1040, 80, "frozen", "trunk: N blocks, frozen",
      "T tokens = CLS + G x G patches", 23, 21);
    frost(trunk);
    const lora = sub(60, P2 + 186, 1040, 80, "trained", "LoRA rank r on every block",
      "which weights; which stage it learns in", 23, 21);
    fire(lora);

    // ---- 3 and 4: a row of head panels sharing one height ----
    const R = P2 + H2 + GAP, R_H = 406;
    const PA = { x: 40, w: 520 }, PB = { x: 600, w: 520 };
    module(PA.x, R, PA.w, R_H, "plain", "3", "Head A", "target", TINT.headA, "what it reads");
    const inA = { x: PA.x + 15, w: PA.w - 30 };
    const scoreA = cbox(inA.x, R + 90, inA.w, "plain", "scoring", ["the operation, with shapes", "-> (B, K)"]);
    const zA = tag(inA.x, scoreA.bottom + 16, inA.w, 50, "plain", "z_a (B,)", 21, true);
    cbox(inA.x, zA.bottom + 24, inA.w, "dashed", "loss on z_a", LOSS);

    module(PB.x, R, PB.w, R_H, "plain", "4", "Head B", "grid", TINT.headB, "what it reads");
    const inB = { x: PB.x + 15, w: PB.w - 30 };
    const scoreB = cbox(inB.x, R + 90, inB.w, "plain", "per-patch scores",
      ["the operation, with shapes", "-> (B, P)"]);
    const zB = tag(inB.x, scoreB.bottom + 16, inB.w, 50, "plain", "z_b (B,)", 21, true);
    cbox(inB.x, zB.bottom + 24, inB.w, "dashed", "loss on z_b", LOSS);

    // ---- 5 Side reader, side column, level with the main reader ----
    const P5 = P2, H5 = H2 + GAP + R_H;
    module(RX0, P5, X1 - RX0, H5, "plain", "5", "Side reader", "grid", TINT.side, "what it reads");
    const in5 = { x: RX0 + 20, w: X1 - RX0 - 40 };
    // Read top to bottom like a head panel: operation, pooling, score, loss; then the training-only
    // part, which fills the column down to the head row's bottom.
    const trunkSide = sub(in5.x, P5 + 92, in5.w, 80, "frozen", "trunk, frozen", "tokens and shapes", 23, 21);
    frost(trunkSide);
    const poolSide = cbox(in5.x, trunkSide.bottom + 14, in5.w, "plain", "pooling",
      ["CLS token or mean of patches -> (B, D)"]);
    const headSide = sub(in5.x, poolSide.bottom + 14, in5.w, 80, "trained", "head: linear D -> 1",
      "-> z_c (B,)", 23, 21);
    fire(headSide);
    const lossSide = cbox(in5.x, headSide.bottom + 24, in5.w, "dashed", "loss on z_c", LOSS);
    const auxSide = cbox(in5.x, lossSide.bottom + 24, in5.w, "dashed", "auxiliary head, training only",
      ["what it reads, what it predicts", "dropped at export"]);
    fire(auxSide);
    cbox(in5.x, auxSide.bottom + 24, in5.w, "dashed", "auxiliary loss", LOSS);

    // ---- 6 Combiner, main column; the summary panel beside it ends at the same bottom ----
    const P6 = R + R_H + GAP, H6 = 270;
    module(X0, P6, SX1 - X0, H6, "plain", "6", "Combiner", "merge", TINT.combiner,
      "learned weights on the detached head scores");
    const formula = cbox(60, P6 + 90, 1040, "trained", "fused score z (B,)",
      ["z = w_a z_a + w_b z_b + w_c z_c + c"], { bs: 22, lh: 28 });
    fire(formula);
    const logits = tag(60, formula.bottom + 30, 1040, 50, "plain", "logits (B, 2)", 22, true);

    const PS = P5 + H5 + GAP, HS = P6 + H6 - PS;
    module(RX0, PS, X1 - RX0, HS, "plain", null, "Export", "box", TINT.summary, "what deploys");
    const slim = cbox(in5.x, PS + 86, in5.w, "plain", "slim build", ["what is merged, baked, dropped"]);
    cbox(in5.x, slim.bottom + 14, in5.w, "plain", "parameters", ["trained counts, from the shapes"]);

    // ---- Full-width strip: four equal cards ----
    const SC = P6 + H6 + GAP, HSC = 210;
    module(X0, SC, X1 - X0, HSC, "plain", null, "Training schedule", "cascade", TINT.strip);
    const CARD_W = (X1 - X0 - 40 - 3 * 20) / 4;
    ["stage 1", "stage 2", "stage 3", "optimizer and run"].forEach((title, i) => {
      cbox(X0 + 20 + i * (CARD_W + 20), SC + 60, CARD_W, "plain", title,
        ["share of the run", "what learns", "what is still"]);
    });

    // ---- Connectors: straight drops inside a column, lanes for anything that changes column ----
    connect([[source.right, source.mid], [prepared.left, prepared.mid]]);
    const busY = P1 + H1 - 20;
    // Enter a panel right of its title and subtitle, never through them or the badge.
    const MAIN_IN = 900;
    connect([[prepared.cx, prepared.bottom], [prepared.cx, busY], [MAIN_IN, busY], [MAIN_IN, trunk.top]]);
    connect([[prepared.right - 40, prepared.bottom], [prepared.right - 40, trunkSide.top]]);
    // Straight drops into each head, right of the head panel's title and subtitle.
    connect([[scoreA.right - 25, lora.bottom], [scoreA.right - 25, scoreA.top]]);
    connect([[scoreB.right - 25, lora.bottom], [scoreB.right - 25, scoreB.top]]);
    connect([[scoreA.cx, scoreA.bottom], [zA.cx, zA.top]]);
    connect([[scoreB.cx, scoreB.bottom], [zB.cx, zB.top]]);
    connect([[trunkSide.cx, trunkSide.bottom], [poolSide.cx, poolSide.top]]);
    connect([[poolSide.cx, poolSide.bottom], [headSide.cx, headSide.top]]);
    connect([[zA.left, zA.mid], [LANE_MAIN, zA.mid], [LANE_MAIN, formula.mid], [formula.left, formula.mid]]);
    // Each score through its own lane, entering the combiner 30 apart.
    connect([[zB.right, zB.mid], [LANE_HEAD_B, zB.mid], [LANE_HEAD_B, formula.mid - 15],
             [formula.right, formula.mid - 15]]);
    connect([[headSide.left, headSide.mid], [LANE_SIDE, headSide.mid], [LANE_SIDE, formula.mid + 15],
             [formula.right, formula.mid + 15]]);
    connect([[formula.cx, formula.bottom], [logits.cx, logits.top]]);
  }
};
