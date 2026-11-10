// cv-kit overview: who does what in /cv-kit:develop and /cv-kit:research.
// Sources: skills/develop/SKILL.md (flow and routing table), skills/research/SKILL.md (pipeline),
// agents/*.md (model, effort and tools of each agent). Build:
//   python3 skills/figure/scripts/build_figure.py docs/figures/cv-kit-overview.figure.js docs/figures/cv-kit-overview.html
//   python3 skills/figure/scripts/check_figure.py docs/figures/cv-kit-overview.html --png docs/assets/overview.png --bare
// Blue boxes are read-only agents, the yellow box is the only agent that edits code, white boxes are
// the main thread, green boxes are what you get.
const FIGURE = {
  title: "cv-kit: one prompt, agents sized to the task",
  subtitle: "The skill scopes the work on the main thread and hands each step to the cheapest agent that can do it.",
  width: 1760,
  height: 630,
  draw(k) {
    const { card, panel, text, connect, box, left } = k;
    const W = 250, H = 120;
    const X = (i) => 50 + i * 283;
    const READ = { fill: "#e4eefb" }, EDIT = { fill: "#fff3c4" };
    const chain = (boxes) => boxes.slice(1).forEach((b, i) =>
      connect([[boxes[i].right, boxes[i].mid], [b.left, b.mid]]));

    // ---- /cv-kit:develop ----
    panel(30, 30, 1700, 230, "plain", "develop");
    text(54, 66, "/cv-kit:develop", 24, true, "start");
    const T1 = 100;
    chain([
      card(X(0), T1, W, "plain", "Brief", ["scope, one question", "at a time, your yes"], { h: H }),
      card(X(1), T1, W, "plain", "explorer", ["haiku, low", "facts with path:line"], { h: H, style: READ }),
      card(X(2), T1, W, "plain", "architect", ["opus, high: only when", "packages share an interface"], { h: H, style: READ }),
      card(X(3), T1, W, "plain", "engineer x N", ["sonnet, high", "red, green, refactor"], { h: H, style: EDIT }),
      card(X(4), T1, W, "plain", "reviewer", ["sonnet, opus if risky", "findings with rule IDs"], { h: H, style: READ }),
      card(X(5), T1, W, "store", "Report", ["cause, tests by name,", "literal command output"], { h: H }),
    ]);

    // ---- /cv-kit:research ----
    panel(30, 300, 1700, 230, "plain", "research");
    text(54, 336, "/cv-kit:research", 24, true, "start");
    const T2 = 370;
    chain([
      card(X(0), T2, W, "plain", "Brief", ["task, metric, split,", "hardware, licence"], { h: H }),
      card(X(1), T2, W, "plain", "Scout, shortlist", ["cut by licence first,", "your yes, 6 at most"], { h: H }),
      card(X(2), T2, W, "plain", "researcher", ["sonnet, high", "one per candidate"], { h: H, style: READ }),
      card(X(3), T2, W, "plain", "claim-verifier", ["haiku, medium: blind", "to the claimed value"], { h: H, style: READ }),
      card(X(4), T2, W, "plain", "Lint", ["confirmed or differs,", "claim by claim"], { h: H }),
      card(X(5), T2, W, "store", "report.md", ["7 key points at most,", "every number sourced"], { h: H }),
    ]);

    // ---- Legend ----
    box(50, 570, 40, 26, "plain");
    left(102, 588, "main thread", 20);
    box(330, 570, 40, 26, "plain", "", READ);
    left(382, 588, "agent, cannot edit your code", 20);
    box(760, 570, 40, 26, "plain", "", EDIT);
    left(812, 588, "agent, edits code test first", 20);
    box(1180, 570, 40, 26, "store");
    left(1232, 588, "what you get", 20);
  }
};
