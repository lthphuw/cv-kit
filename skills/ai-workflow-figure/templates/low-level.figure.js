// Low-level model figure: modules, tensor shapes and the connections between them.
// Starter spec in a three-column layout: input left, the encoder panel in the middle, the head right.
// Build:
//   python3 <skill>/scripts/build_figure.py <this file> <out.html>
// Put every tensor shape in a label, mark frozen and trained parts, and route each
// connector through a gutter (x 390-500 and 1040-1180) so it never crosses a box.
const FIGURE = {
  title: "Model name: low-level workflow",
  subtitle: "Read top to bottom: tokens flow through the frozen encoder, the trained adapters, and the head that gives the logits.",
  width: 1760,
  height: 680,
  draw(k) {
    const { card, sub, tag, panel, label, box, left, connect, snowflake, flame, frost, fire } = k;
    const LANE_EMBED = 460, LANE_BUS = 1100;
    const MID_CX = 770;

    // ---- Left column: input and patch embedding ----
    const input = card(60, 120, 330, "plain", "Input image", [
      "RGB, resized to 224 px",
      "tensor (B, 3, 224, 224)"
    ]);
    const embed = card(60, 280, 330, "plain", "Patch embedding", [
      "16 x 16 patches, linear 768",
      "tokens (B, 197, 768) with CLS"
    ]);
    connect([[input.cx, input.bottom], [embed.cx, embed.top]]);

    // ---- Middle: the encoder, a panel that connectors may cross ----
    panel(500, 120, 540, 300, "plain", "Encoder");
    label(MID_CX, 160, "Encoder: ViT-B/16, 12 blocks", 24, true);
    const trunk = sub(520, 180, 500, 72, "frozen", "Blocks 1-12",
      "frozen, (B, 197, 768) in and out", 22, 17);
    frost(trunk);
    const lora = tag(520, 266, 500, 44, "trained", "LoRA r8 on qkv and proj (trains)", 18, false);
    fire(lora);
    const out = sub(520, 324, 500, 72, "plain", "Token output",
      "(B, 197, 768): CLS + 196 patches", 22, 17);
    connect([[trunk.cx, trunk.bottom], [lora.cx, lora.top]]);
    connect([[lora.cx, lora.bottom], [out.cx, out.top]]);
    connect([[embed.right, embed.mid], [LANE_EMBED, embed.mid],
             [LANE_EMBED, trunk.mid], [trunk.left, trunk.mid]]);

    // ---- Right column: pooling and head, then logits and the training loss ----
    const pool = card(1180, 120, 540, "trained", "Pooling and head", [
      "CLS token -> LayerNorm -> linear 768 -> 2",
      "zero-init, trains in every stage"
    ]);
    fire(pool);
    const logits = tag(1180, 300, 540, 56, "plain", "logits (B, 2)", 21, true);
    const loss = card(1180, 420, 540, "dashed", "Training loss", ["cross-entropy on the logits"],
      { h: 100 });
    connect([[out.right, out.mid], [LANE_BUS, out.mid], [LANE_BUS, pool.mid], [pool.left, pool.mid]]);
    connect([[pool.cx, pool.bottom], [logits.cx, logits.top]]);
    connect([[logits.cx, logits.bottom], [loss.cx, loss.top]]);

    // ---- Legend ----
    box(60, 600, 40, 26, "frozen");
    snowflake(132, 613, 9);
    left(160, 618, "frozen: pretrained weights, never updated", 20);
    box(560, 600, 40, 26, "trained");
    flame(632, 613, 0.7);
    left(660, 618, "trained: learned weights, kept at export", 20);
    box(1080, 600, 40, 26, "dashed");
    left(1132, 618, "training only: dropped at export", 20);
  }
};
