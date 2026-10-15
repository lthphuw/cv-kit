// High-level model figure: the blocks and the data that flows between them.
// Starter spec. Copy it, rename the file, change the content, then build:
//   python3 <skill>/scripts/build_figure.py <this file> <out.html>
// Keep 4 to 7 boxes, one or two short lines each, and no tensor layouts.
const FIGURE = {
  title: "Model name: high-level workflow",
  subtitle: "Read left to right: the input is encoded, adapted, scored, then turned into probabilities.",
  width: 1760,
  height: 640,
  draw(k) {
    const { card, connect, box, left, snowflake, flame, frost, fire } = k;
    const W = 280, GAP = 75, TOP = 150, H = 130;
    const x = (i) => 40 + i * (W + GAP);

    const input = card(x(0), TOP, W, "plain", "Input", ["face image, RGB", "resized to 224 px"], { h: H });
    const encoder = card(x(1), TOP, W, "frozen", "Encoder",
      ["pretrained, not updated", "image to 768-d vector"], { h: H });
    const adapter = card(x(2), TOP, W, "trained", "Adapter",
      ["learned in training", "zero-init residual"], { h: H });
    const head = card(x(3), TOP, W, "trained", "Head",
      ["linear layer", "one logit per class"], { h: H });
    const output = card(x(4), TOP, W, "plain", "Output", ["class probabilities"], { h: H });
    frost(encoder);
    fire(adapter);
    fire(head);

    // The loss exists only during training, so it hangs off the head with a dashed box.
    const loss = card(x(3), 360, W, "dashed", "Loss", ["cross-entropy on the logits"], { h: 96 });

    connect([[input.right, input.mid], [encoder.left, encoder.mid]]);
    connect([[encoder.right, encoder.mid], [adapter.left, adapter.mid]]);
    connect([[adapter.right, adapter.mid], [head.left, head.mid]]);
    connect([[head.right, head.mid], [output.left, output.mid]]);
    connect([[head.cx, head.bottom], [loss.cx, loss.top]]);

    // Legend: the same kinds and icons as the figure body.
    box(40, 490, 40, 26, "frozen");
    snowflake(112, 503, 9);
    left(140, 508, "frozen: pretrained weights, never updated", 20);
    box(560, 490, 40, 26, "trained");
    flame(632, 503, 0.7);
    left(660, 508, "trained: learned weights, kept at export", 20);
    box(1080, 490, 40, 26, "dashed");
    left(1132, 508, "training only: dropped at export", 20);
  }
};
