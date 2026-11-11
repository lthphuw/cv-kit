#!/usr/bin/env python3
"""Build docs/assets/develop.gif and research.gif: scripted runs, with the agent rows drawn by hooks/agent_status.py.

    python3 docs/figures/demo_gifs.py [develop|research ...]

Needs Chrome or Chromium (`CHROME=` if not on PATH) and ffmpeg. The transcript text is written here by hand and shows
the shape of a run; the rows are what the status line prints for the same tasks.
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "hooks"))
import agent_status  # noqa: E402

WIDTH, LINES, LINE_PX, COLUMNS = 880, 16, 22, 94
HEIGHT = 30 + 32 + LINES * LINE_PX
TICK_MS = 5000
COLORS = {"31": "#f85149", "32": "#3fb950", "33": "#d29922", "36": "#39c5cf", "90": "#6e7681", "38;5;208": "#f0883e"}
SGR = re.compile(r"\x1b\[([0-9;]*)m(.*?)\x1b\[0m|([^\x1b]+)", re.S)
PAGE = """<!doctype html><meta charset="utf-8"><style>
html,body{{margin:0;background:#0d1117}}
body{{width:{width}px;height:{height}px;overflow:hidden;font:14px/{line}px "DejaVu Sans Mono",monospace;color:#c9d1d9}}
.bar{{height:30px;line-height:30px;background:#161b22;color:#8b949e;text-align:center;font-size:12px;position:relative}}
.bar i{{position:absolute;top:10px;width:10px;height:10px;border-radius:50%}}
pre{{margin:0;padding:16px 20px;font:inherit}}
.p{{color:#f0f6fc;font-weight:700}} .b{{color:#58a6ff}} .d{{color:#8b949e}} .g{{color:#3fb950}} .y{{color:#d29922}}
</style><div class="bar"><i style="left:12px;background:#f85149"></i><i style="left:28px;background:#d29922"></i>
<i style="left:44px;background:#3fb950"></i>{title}</div><pre>{body}</pre>"""


def ansi_to_html(text: str) -> str:
    out = []
    for style, styled, plain in SGR.findall(text):
        if plain:
            out.append(html.escape(plain))
            continue
        css, color, inverse = [], "#c9d1d9", False
        rest = style
        for code, value in COLORS.items():
            if re.search(rf"(^|;){code}($|;)", rest):
                color, rest = value, rest.replace(code, "")
                break
        codes = [c for c in rest.split(";") if c]
        if "1" in codes:
            css.append("font-weight:700")
        if "2" in codes:
            color = "#6e7681"
        inverse = "7" in codes
        css.append(f"background:{color};color:#0d1117" if inverse else f"color:{color}")
        out.append(f'<span style="{";".join(css)}">{html.escape(styled)}</span>')
    return "".join(out)


def mark(text: str) -> str:
    """`{b|text}` wraps text in a class; everything else is escaped."""
    return re.sub(r"\{(\w)\|([^}]*)\}", r'<span class="\1">\2</span>', html.escape(text))


class Scene:
    def __init__(self, title: str, prompt: str):
        self.title, self.prompt = title, prompt
        self.lines: list[str] = []
        self.tasks: list[dict] = []
        self.rates: dict[str, int] = {}
        self.memory: dict = {}
        self.now = 0.0
        self.frames: list[tuple[str, float]] = []

    def say(self, *lines: str, hold: float = 1.4) -> None:
        self.lines += lines
        self.snap(hold)

    def cut(self) -> None:
        self.lines = []

    def start(self, agent: str, model: str, effort: str, label: str, rate: int) -> str:
        task_id = f"t{len(self.tasks)}"
        self.tasks.append({"id": task_id, "status": "running", "agentType": f"cv-kit:{agent}", "label": label,
                           "model": model, "effort": effort, "tokenCount": rate // 3, "startTime": self.now - 2000})
        self.rates[task_id] = rate
        return task_id

    def tick(self, count: int = 1, hold: float = 0.6) -> None:
        for _ in range(count):
            self.now += TICK_MS
            for task in self.tasks:
                if task["status"] == "running":
                    task["tokenCount"] += self.rates[task["id"]]
            self.snap(hold)

    def finish(self, *task_ids: str) -> None:
        for task in self.tasks:
            if task["id"] in task_ids:
                task["status"] = "completed"

    def snap(self, hold: float) -> None:
        rows = [json.loads(line)["content"] for line in
                agent_status.render({"columns": COLUMNS, "tasks": self.tasks}, self.now, memory=self.memory)]
        body = [f'<span class="d">&gt;</span> <span class="p">{html.escape(self.prompt)}</span>']
        tail = [mark(line) for line in self.lines]
        if rows:
            tail += [""] + ["  " + ansi_to_html(row) for row in rows]
        body += tail[-(LINES - 1):]
        self.frames.append((PAGE.format(width=WIDTH, height=HEIGHT, line=LINE_PX, title=self.title,
                                        body="\n".join(body)), hold))


def develop() -> Scene:
    s = Scene("cv-kit · develop", "/cv-kit:develop add a tracker between detection and the writer")
    s.snap(1.2)
    s.say("{b|●} Brief",
          "  {d|Goal}       every detection the writer saves carries a track id",
          "  {d|Done when}  new tracker tests failed first, then pytest -q and ruff check . pass",
          "  {d|Not doing}  re-identification across cameras",
          "  Go ahead?", hold=2.6)
    s.say("{d|>} {p|yes}", hold=0.9)
    explorer = s.start("explorer", "haiku", "low", "where frames reach the writer", 2100)
    s.tick(3)
    s.finish(explorer)
    s.cut()
    s.say("{b|●} Baseline: pytest -q, 41 passed. Frames reach the writer at pipeline.py:57.", hold=1.6)
    architect = s.start("architect", "opus", "high", "design: tracker between detect and writer", 3400)
    s.tick(5)
    s.finish(architect)
    s.say("{b|●} Design: two packages share one interface, Track(id, box, score)",
          "  1  tracker core                vision/track.py",
          "  2  writer accepts track ids    io/writer.py",
          "  Go ahead?", hold=2.6)
    s.say("{d|>} {p|yes}", hold=0.9)
    s.cut()
    s.say("{b|●} Design approved: two engineers in parallel, each in its own worktree", hold=0.8)
    core = s.start("engineer", "sonnet", "high", "tracker core: failing test, then code", 2900)
    writer = s.start("engineer", "sonnet", "high", "writer accepts track ids", 2500)
    s.tick(4)
    s.finish(writer)
    s.say("",
          "  Progress (1/2 done):",
          "  - engineer#1 tracker core: running",
          "  - engineer#2 writer accepts track ids: {g|done}, 3 tests pass", hold=1.8)
    s.tick(2)
    s.finish(core)
    s.tick(1, hold=0.9)
    s.cut()
    s.say("{b|●} Both packages green: reviewer reads the diff against the design", hold=0.8)
    reviewer = s.start("reviewer", "opus", "high", "review against the design", 3000)
    s.tick(4)
    s.finish(reviewer)
    s.tick(1, hold=0.9)
    s.cut()
    s.say("{b|●} Nothing is committed.",
          "  {p|Summarization:}",
          "  - Tracker in vision/track.py, called at pipeline.py:57",
          "  - 9 new tests, each failed first",
          "  - pytest -q: {g|50 passed}   ruff check .: {g|All checks passed!}",
          "  - Review: Blocking: 0 Critical, 0 Major",
          "  {p|Next:}",
          "  - commit the change", hold=1.0)
    s.snap(6.0)
    return s


def research() -> Scene:
    s = Scene("cv-kit · research",
              "/cv-kit:research which detector for 30 FPS on a Jetson Orin NX, Apache-2.0 only")
    s.snap(1.2)
    s.say("{b|●} brief.md",
          "  detection · COCO val2017 AP · Orin NX, 30 FPS at FP16 · Apache-2.0 only", hold=1.8)
    s.say("{b|●} Shortlist: 6 scouted, 3 advance",
          "  RF-DETR     {g|advance}    Apache-2.0, weights on Hugging Face",
          "  D-FINE      {g|advance}    Apache-2.0, weights on Hugging Face",
          "  RT-DETRv2   {g|advance}    Apache-2.0, weights on Hugging Face",
          "  YOLO11      {y|excluded}   licence: AGPL-3.0",
          "  YOLO26      {y|excluded}   licence: AGPL-3.0",
          "  DEIMv2      {y|excluded}   licence: non-commercial",
          "  Deep-read the three?", hold=3.2)
    s.say("{d|>} {p|yes}", hold=0.9)
    s.cut()
    s.say("{b|●} Deep-read: one researcher per candidate, sources saved to sources/", hold=0.8)
    names = ("RF-DETR", "D-FINE", "RT-DETRv2")
    readers = [s.start("researcher", "sonnet", "high", f"{name}: paper, model card, repo", rate)
               for name, rate in zip(names, (4100, 3600, 3900))]
    s.tick(4)
    s.finish(readers[1])
    s.say("",
          "  Progress (1/3 done):",
          "  - researcher#1 RF-DETR: running",
          "  - researcher#2 D-FINE: {g|done}, 6 claims",
          "  - researcher#3 RT-DETRv2: running", hold=1.8)
    s.tick(2)
    s.finish(readers[0], readers[2])
    s.tick(1, hold=0.9)
    s.cut()
    s.say("{b|●} Cross-check: verifiers re-read the sources without the claimed values", hold=0.8)
    verifiers = [s.start("claim-verifier", "haiku", "medium", f"re-read {name} sources, blind", rate)
                 for name, rate in zip(names, (1900, 1700, 1800))]
    s.tick(3)
    s.finish(*verifiers)
    s.tick(1, hold=0.9)
    s.cut()
    s.say("{b|●} Lint",
          "  17 claims, 17 checked against a saved copy of their source",
          "  verdicts: {g|15 confirmed}, {y|1 differs}, {y|1 unreachable}",
          "  {y|differs}      [rt-detrv2-3]  two sources, two values: both rows kept",
          "  {y|unreachable}  [d-fine-5]     listed under Not found or not checked", hold=3.0)
    s.cut()
    s.say("{b|●} Overview: start with RF-DETR-S. No candidate publishes latency on an Orin NX;",
          "  every FPS figure comes from a T4, so the 30 FPS budget is unconfirmed.",
          "  Confidence: medium.",
          "  Report: research/detector-orin-nx/report.md",
          "  {p|Next:}",
          "  - /cv-kit:develop benchmark RF-DETR-S and D-FINE-S at FP16 on the Orin NX", hold=1.0)
    s.snap(6.0)
    return s


def chrome() -> str:
    for name in (os.environ.get("CHROME"), "google-chrome", "chromium", "chromium-browser"):
        if name and shutil.which(name):
            return name
    raise SystemExit("Chrome or Chromium not found; set CHROME=")


def build(scene: Scene, out: Path) -> None:
    browser = chrome()
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)

        def shot(index: int) -> None:
            page = work / f"f{index:03d}.html"
            page.write_text(scene.frames[index][0], encoding="utf-8")
            subprocess.run([browser, "--headless=new", "--no-sandbox", "--hide-scrollbars", "--disable-gpu",
                            f"--user-data-dir={work / f'profile{index}'}", f"--window-size={WIDTH},{HEIGHT}",
                            f"--screenshot={page.with_suffix('.png')}", page.as_uri()],
                           check=True, capture_output=True, timeout=120)

        with ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(shot, range(len(scene.frames))))
        listing = "".join(f"file 'f{i:03d}.png'\nduration {hold}\n" for i, (_, hold) in enumerate(scene.frames))
        listing += f"file 'f{len(scene.frames) - 1:03d}.png'\n"
        (work / "frames.txt").write_text(listing, encoding="utf-8")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "frames.txt",
                        "-vf", "split[a][b];[a]palettegen=max_colors=48[p];[b][p]paletteuse=dither=none",
                        "-fps_mode", "vfr", "-loop", "0", str(out)], check=True, cwd=work)
    print(f"wrote {out} ({len(scene.frames)} frames, {out.stat().st_size // 1024} kB)")


def main() -> int:
    scenes = {"develop": develop, "research": research}
    for name in sys.argv[1:] or scenes:
        build(scenes[name](), ROOT / "docs" / "assets" / f"{name}.gif")
    return 0


if __name__ == "__main__":
    sys.exit(main())
