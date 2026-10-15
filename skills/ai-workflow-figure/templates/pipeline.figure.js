// AI system pipeline figure: components, data stores and the flows between them.
// Starter spec: an offline training row and an online serving row, joined by the
// model registry. Build:
//   python3 <skill>/scripts/build_figure.py <this file> <out.html>
// Panels group the phases; store is for data and model artefacts; aux is for
// observation that is not on the request path.
const FIGURE = {
  title: "System name: training and serving pipeline",
  subtitle: "Top row runs offline and publishes a model; bottom row serves requests with it.",
  width: 1760,
  height: 740,
  draw(k) {
    const { card, panel, text, connect, box, left, snowflake, frost, fire } = k;
    const W = 280, H = 120;
    // Five columns at a 340 pitch; the same x positions serve both rows.
    const X = (i) => 60 + i * 340;

    // ---- Offline row: training ----
    panel(40, 110, 1680, 230, "plain", "Offline: training");
    text(64, 146, "Offline: training", 24, true, "start");
    const TOP_OFF = 180;
    const raw = card(X(0), TOP_OFF, W, "store", "Raw data",
      ["image and label files", "versioned snapshot"], { h: H });
    const clean = card(X(1), TOP_OFF, W, "plain", "Validate and clean",
      ["drop corrupt frames", "split by subject"], { h: H });
    const features = card(X(2), TOP_OFF, W, "plain", "Feature build",
      ["face crops, 518 px", "cached as tensors"], { h: H });
    const train = card(X(3), TOP_OFF, W, "trained", "Train",
      ["fine-tune, LoRA r8", "checkpoint per epoch"], { h: H });
    fire(train);
    const registry = card(X(4), TOP_OFF, W, "store", "Model registry",
      ["versioned weights", "config and metrics"], { h: H });
    connect([[raw.right, raw.mid], [clean.left, clean.mid]]);
    connect([[clean.right, clean.mid], [features.left, features.mid]]);
    connect([[features.right, features.mid], [train.left, train.mid]]);
    connect([[train.right, train.mid], [registry.left, registry.mid]]);

    // ---- Online row: serving ----
    panel(40, 380, 1680, 230, "plain", "Online: serving");
    text(64, 416, "Online: serving", 24, true, "start");
    const TOP_ON = 450;
    const request = card(X(0), TOP_ON, W, "plain", "Client request",
      ["image from the app", "one call per check"], { h: H });
    const preprocess = card(X(1), TOP_ON, W, "plain", "Preprocess",
      ["same crop as training", "no augmentation"], { h: H });
    const server = card(X(2), TOP_ON, W, "frozen", "Model server",
      ["registry weights, loaded once", "batch of 1 to 8"], { h: H });
    frost(server);
    const response = card(X(3), TOP_ON, W, "plain", "Response",
      ["label and score", "returned to the caller"], { h: H });
    const monitor = card(X(4), TOP_ON, W, "aux", "Monitoring",
      ["latency and error rate", "sampled requests"], { h: H });
    connect([[request.right, request.mid], [preprocess.left, preprocess.mid]]);
    connect([[preprocess.right, preprocess.mid], [server.left, server.mid]]);
    connect([[server.right, server.mid], [response.left, response.mid]]);
    connect([[response.right, response.mid], [monitor.left, monitor.mid]]);

    // The registry feeds the server: down out of the top row, across the gap, into the server.
    connect([[registry.cx, registry.bottom], [registry.cx, 360],
             [server.cx, 360], [server.cx, server.top]]);

    // ---- Legend ----
    box(60, 660, 40, 26, "store");
    left(112, 678, "store: data or model artefacts", 20);
    box(480, 660, 40, 26, "trained");
    left(532, 678, "trained: learned in this pipeline", 20);
    box(940, 660, 40, 26, "frozen");
    snowflake(1012, 673, 9);
    left(1040, 678, "frozen: deployed weights", 20);
    box(1400, 660, 40, 26, "aux");
    left(1452, 678, "aux: monitoring", 20);
  }
};
