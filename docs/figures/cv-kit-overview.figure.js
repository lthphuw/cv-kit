// cv-kit overview: who does what in the four skills (develop, research, review, figure), and why.
// Sources: skills/develop/SKILL.md (flow, routing table, brief, what comes back), skills/research/SKILL.md
// (pipeline), skills/review/SKILL.md and its report-format.md, skills/figure/SKILL.md, agents/*.md (model, effort
// and tools of each agent), scripts/lint_research.py (verdicts). Build:
//   python3 skills/figure/scripts/build_figure.py docs/figures/cv-kit-overview.figure.js docs/figures/cv-kit-overview.html
//   python3 skills/figure/scripts/check_figure.py docs/figures/cv-kit-overview.html --png docs/assets/overview.png
// Blue boxes are agents that cannot edit your code, the purple box is the only agent that does, white boxes are
// the main thread, green boxes are what you get, yellow notes say why.
const FIGURE = {
  title: "cv-kit: one prompt, agents sized to the task",
  subtitle: "The skill scopes the work on the main thread and hands each step to the cheapest agent that can do it.",
  width: 1760,
  height: 1220,
  draw(k) {
    const { card, panel, text, label, connect, box, left, note, pointer } = k;
    const W = 250, H = 140;
    const X = (i) => 50 + i * 283;
    const READ = { fill: "#e4eefb" }, EDIT = { fill: "#efe7fb" };
    const chain = (boxes) => boxes.slice(1).forEach((b, i) =>
      connect([[boxes[i].right, boxes[i].mid], [b.left, b.mid]]));

    // ---- /cv-kit:develop ----
    panel(30, 30, 1700, 460, "plain", "develop");
    text(54, 66, "/cv-kit:develop", 24, true, "start");
    const T1 = 150;
    const brief = card(X(0), T1, W, "plain", "Brief",
      ["scope on the main thread,", "one question at a time,", "your yes before any code"], { h: H });
    const explorer = card(X(1), T1, W, "plain", "explorer",
      ["haiku, low, read-only", "finds the code, returns", "facts with path:line"], { h: H, style: READ });
    const architect = card(X(2), T1, W, "plain", "architect",
      ["opus, high, read-only", "options, flow, interfaces,", "packages, then your yes"], { h: H, style: READ });
    const engineer = card(X(3), T1, W, "plain", "engineer x N",
      ["sonnet, high, edits code", "failing test, then the fix,", "parallel in worktrees"], { h: H, style: EDIT });
    const reviewer = card(X(4), T1, W, "plain", "reviewer",
      ["sonnet, high, read-only", "reads the pasted diff,", "findings with rule IDs"], { h: H, style: READ });
    const report = card(X(5), T1, W, "store", "Report",
      ["cause at path:line,", "tests by name,", "literal command output"], { h: H });
    chain([brief, explorer, architect, engineer, reviewer, report]);

    // One package needs no design: explorer's facts go straight into the engineer's brief.
    const SKIP = T1 - 30;
    connect([[explorer.cx, explorer.top], [explorer.cx, SKIP], [engineer.cx, SKIP], [engineer.cx, engineer.top]]);
    label(architect.cx, SKIP - 12, "one package: no design", 20);

    // Blocking findings go back to an engineer.
    const BACK = T1 + H + 32;
    connect([[reviewer.cx, reviewer.bottom], [reviewer.cx, BACK], [engineer.cx, BACK], [engineer.cx, engineer.bottom]]);
    label((engineer.cx + reviewer.cx) / 2, BACK + 28, "blocking findings: fix, test first", 20);

    const N1 = T1 + H + 82;
    note(X(0), N1, 440, ["Failed on the brief: fix it, same model.",
      "Failed on the reasoning: sonnet -> opus", "-> opus at xhigh once, then a report."]);
    const why = note(X(2) - 30, N1, 270, ["Only when packages share", "an interface or a data flow."]);
    pointer([[architect.cx, why.top], [architect.cx, architect.bottom]]);
    const how = note(X(3) - 30, N1, 330, ["Brief: Goal, Done when, Facts, Files,",
      "Constraints, Ruled out, Mode.", "Threads or memory safety: opus."]);
    pointer([[engineer.left + 60, how.top], [engineer.left + 60, engineer.bottom]]);
    const risk = note(X(4) + 40, N1, 300, ["Opus for concurrency, security,", "published numbers and",
      "designed or opus-written code."]);
    pointer([[reviewer.right - 40, risk.top], [reviewer.right - 40, reviewer.bottom]]);

    // ---- /cv-kit:research ----
    panel(30, 520, 1700, 330, "plain", "research");
    text(54, 556, "/cv-kit:research", 24, true, "start");
    const T2 = 590;
    const frame = card(X(0), T2, W, "plain", "Brief",
      ["task, metric, dataset split,", "hardware, latency budget,", "licence limit"], { h: H });
    const scout = card(X(1), T2, W, "plain", "Scout, shortlist",
      ["arXiv, HF, CVF, GitHub,", "cut by licence first,", "your yes, 6 at most"], { h: H });
    const researcher = card(X(2), T2, W, "plain", "researcher x N",
      ["sonnet, high, per candidate", "paper, model card, repo", "at a pinned commit"], { h: H, style: READ });
    const verifier = card(X(3), T2, W, "plain", "claim-verifier x N",
      ["haiku, medium", "re-reads each source, blind", "to the claimed value"], { h: H, style: READ });
    const lint = card(X(4), T2, W, "plain", "Lint",
      ["confirmed, differs,", "wrong-paper, absent,", "unreachable"], { h: H });
    const paper = card(X(5), T2, W, "store", "report.md",
      ["overview, 7 key points,", "comparison table,", "every number sourced"], { h: H });
    chain([frame, scout, researcher, verifier, lint, paper]);

    const N2 = T2 + H + 30;
    const memory = note(X(2) - 30, N2, 310, ["Nothing from memory: each number", "is a quote from a saved copy."]);
    pointer([[researcher.cx, memory.top], [researcher.cx, researcher.bottom]]);
    const differs = note(X(4) - 10, N2, 270, ["A differs is shown to you,", "never resolved silently."]);
    pointer([[lint.cx, differs.top], [lint.cx, lint.bottom]]);

    // ---- /cv-kit:review and /cv-kit:figure ----
    panel(30, 880, 1700, 260, "plain", "review and figure");
    text(54, 916, "/cv-kit:review", 24, true, "start");
    text(X(3) + 4, 916, "/cv-kit:figure", 24, true, "start");
    const T3 = 950;
    const scope = card(X(0), T3, W, "plain", "Scope",
      ["paths, a diff, a branch", "or a pull request;", "installed linters run"], { h: H });
    const second = card(X(1), T3, W, "plain", "reviewer",
      ["sonnet, high, read-only", "opus for threads, memory,", "security, published numbers"], { h: H, style: READ });
    const findings = card(X(2), T3, W, "store", "Findings",
      ["severity, rule ID, path:line,", "What, Trigger, Fix,", "Blocking: n Critical, m Major"], { h: H });
    chain([scope, second, findings]);
    const facts = card(X(3), T3, W, "plain", "Read the code",
      ["shapes, counts and names", "come from your code,", "never from memory"], { h: H });
    const spec = card(X(4), T3, W, "plain", "Spec, build, check",
      ["one .figure.js spec,", "built to one HTML file,", "layout checked in Chrome"], { h: H });
    const drawn = card(X(5), T3, W, "store", "Figure",
      ["hand-drawn HTML and PNG,", "SVG for papers,", "unconfirmed facts listed"], { h: H });
    chain([facts, spec, drawn]);

    // ---- Legend ----
    box(50, 1170, 40, 26, "plain");
    left(102, 1188, "main thread", 20);
    box(300, 1170, 40, 26, "plain", "", READ);
    left(352, 1188, "agent, cannot edit your code", 20);
    box(700, 1170, 40, 26, "plain", "", EDIT);
    left(752, 1188, "agent, edits code test first", 20);
    box(1090, 1170, 40, 26, "store");
    left(1142, 1188, "what you get", 20);
    box(1340, 1170, 40, 26, "note");
    left(1392, 1188, "why", 20);
  }
};
