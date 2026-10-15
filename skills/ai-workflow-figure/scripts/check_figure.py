#!/usr/bin/env python3
"""Report layout problems in a built figure and, on request, render it to PNG or SVG.

Usage: python3 check_figure.py FIGURE.html [--png OUT.png] [--svg OUT.svg] [--bare] [--scale N] [--width PX]

The figure kit measures its text and connectors once the font has loaded, and
writes a JSON report into the page. This script dumps the page with headless
Chrome, prints the report and exits 1 when it lists any issue. With --png it also
takes a screenshot as tall as the page, so nothing is cropped; --bare leaves out the
page title and subtitle, and --scale multiplies its pixels by 1 to 4 (a sharper PNG). With
--svg it writes the drawn SVG as a standalone file that carries its font. Both files
are written even when there are issues, to look at them. Set CHROME to the browser
binary when it is not on PATH under a usual name.

Chrome keeps its sandbox on, except as root (where Chrome refuses to start with it)
or when CI is set, on a throwaway machine.
"""

import argparse
import json
import math
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import xml.etree.ElementTree as ElementTree

REPORT = re.compile(r'<script type="application/json" id="layout-report">(.*?)</script>', re.DOTALL)
# The page holds one drawn SVG, and rough.js draws no nested <svg>.
DRAWN_SVG = re.compile(r'<svg id="fig".*?</svg>', re.DOTALL)
# What the built page styles its text with, and its background: kit/shell.html and build_figure.py.
FONT_FACE = re.compile(r"@font-face \{[^}]*\}")
TEXT_RULE = re.compile(r"svg text \{([^}]*)\}")
FAMILY = re.compile(r"font-family: '([^']+)'")
PAGE_COLOUR = re.compile(r"body \{[^}]*background: (#[0-9a-fA-F]{6})")
DEFAULT_FAMILY = "Patrick Hand"
MAX_SCALE = 4
CHROME_TIMEOUT_S = 120
BROWSER_NAMES = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome")
MACOS_CHROME = pathlib.Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
DEFAULT_WIDTH = 1800
# Any height works for the dump: the page height follows the window width alone.
DUMP_HEIGHT = 1000
SNAP_HINT = (
    "; a snap-packaged Chromium cannot read or write /tmp, /mnt or hidden folders: keep the "
    "figure and the PNG in a visible folder under your home directory, or install Google Chrome"
)


def find_browser() -> str:
    """Return the Chrome or Chromium binary: $CHROME, then the usual names on PATH."""
    if os.environ.get("CHROME"):
        chosen = shutil.which(os.environ["CHROME"])
        if chosen is None:
            sys.exit(f"CHROME={os.environ['CHROME']!r} is not an executable browser")
        return chosen
    for name in BROWSER_NAMES:
        found = shutil.which(name)
        if found:
            return found
    if MACOS_CHROME.is_file():
        return str(MACOS_CHROME)
    sys.exit("no Chrome or Chromium found; install one or set CHROME to its binary")


def hint(browser: str) -> str:
    """Return the snap hint when the browser is a snap, else nothing."""
    return SNAP_HINT if "/snap/" in os.path.realpath(browser) or "/snap/" in browser else ""


def sandbox_flags() -> list[str]:
    """Return --no-sandbox only where Chrome cannot or need not use its sandbox."""
    as_root = hasattr(os, "geteuid") and os.geteuid() == 0
    return ["--no-sandbox"] if as_root or os.environ.get("CI") else []


def run_chrome(browser: str, url: str, width: int, height: int, *mode: str) -> str:
    """Run headless Chrome on the figure's URL in the given mode and return its stdout."""
    command = [
        browser,
        "--headless",
        "--disable-gpu",
        *sandbox_flags(),
        "--hide-scrollbars",
        "--virtual-time-budget=4000",
        f"--window-size={width},{height}",
        *mode,
        url,
    ]
    # Chrome's own process group, so a hang can be ended with every renderer it started.
    posix = hasattr(os, "killpg")
    with subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        encoding="utf-8", errors="replace", start_new_session=posix,
    ) as process:
        try:
            out, err = process.communicate(timeout=CHROME_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            if posix:
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            process.communicate()
            sys.exit(f"chrome did not finish within {CHROME_TIMEOUT_S} s")
    if process.returncode != 0:
        sys.exit(f"chrome failed ({process.returncode}): {err.strip()}{hint(browser)}")
    return out


def read_report(dom: str, figure: pathlib.Path, browser: str) -> dict:
    """Return the layout report the kit wrote into the page."""
    match = REPORT.search(dom)
    if match is None:
        sys.exit(f"no layout report in {figure}: the page did not load or run{hint(browser)}")
    return json.loads(match.group(1))


def standalone_svg(dom: str, page: str) -> tuple[str, str]:
    """Return the drawn SVG as a standalone document, and the font family it embeds.

    The figure's @font-face and text style go into the SVG, so its text keeps the font
    the layout check measured, and the page colour goes behind it, so labels in the
    gutters stay readable on any background.
    """
    match = DRAWN_SVG.search(dom)
    face, rule, colour = FONT_FACE.search(page), TEXT_RULE.search(page), PAGE_COLOUR.search(page)
    if match is None or face is None or rule is None or colour is None:
        sys.exit("cannot export the SVG: the page is not a figure built by build_figure.py")
    family = FAMILY.search(face.group(0))
    # HTML writes a no-break space as &nbsp;, which XML does not define.
    svg = match.group(0).replace("&nbsp;", "&#160;")
    head, rest = svg.split(">", 1)
    if "xmlns=" not in head:
        head += ' xmlns="http://www.w3.org/2000/svg"'
    view = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', head)
    if view:
        head += f' width="{view.group(1)}" height="{view.group(2)}"'
    style = (f"<style><![CDATA[\n{face.group(0)}\ntext {{{rule.group(1)}}}\n]]></style>"
             f'<rect width="100%" height="100%" fill="{colour.group(1)}"/>')
    # The title and desc stay the first children; the style and the background follow them.
    at = rest.find("</desc>")
    rest = rest[:at + len("</desc>")] + style + rest[at + len("</desc>"):] if at >= 0 else style + rest
    out = '<?xml version="1.0" encoding="UTF-8"?>\n' + head + ">" + rest + "\n"
    try:
        ElementTree.fromstring(out.encode("utf-8"))
    except ElementTree.ParseError as error:
        sys.exit(f"cannot export the SVG: it is not well-formed XML ({error})")
    return out, family.group(1) if family else ""


def scale_factor(text: str) -> float:
    """Parse --scale: a number from 1 to MAX_SCALE."""
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a number: {text!r}") from None
    if not math.isfinite(value) or not 1 <= value <= MAX_SCALE:
        raise argparse.ArgumentTypeError(f"scale must be from 1 to {MAX_SCALE}, got {text}")
    return value


def main() -> None:
    """Print the layout report, write the PNG and SVG if asked, and exit 1 when there are issues."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("figure", type=pathlib.Path, help="built figure (.html)")
    parser.add_argument("--png", type=pathlib.Path, help="also write a full-page screenshot here")
    parser.add_argument("--svg", type=pathlib.Path, help="also write the drawn SVG as a standalone file here")
    parser.add_argument("--bare", action="store_true", help="the figure alone, without the page title and subtitle")
    parser.add_argument("--scale", type=scale_factor, default=1, help=f"multiply the PNG's pixels, 1 to {MAX_SCALE}")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH, help="window width in px")
    args = parser.parse_args()
    if not args.figure.is_file():
        sys.exit(f"no such figure: {args.figure}")

    browser = find_browser()
    url = args.figure.resolve().as_uri() + ("?bare" if args.bare else "")
    dom = run_chrome(browser, url, args.width, DUMP_HEIGHT, "--dump-dom")
    report = read_report(dom, args.figure, browser)
    print(f"shapes {report['shapes']}, texts {report['texts']}, connectors {report['connectors']}")
    issues = report["issues"]
    for issue in issues:
        print("issue:", issue)

    if args.svg is not None:
        svg, family = standalone_svg(dom, args.figure.read_text(encoding="utf-8"))
        args.svg.parent.mkdir(parents=True, exist_ok=True)
        args.svg.write_text(svg, encoding="utf-8")
        print(f"exported {args.svg} ({len(svg) // 1024} KB)")
        if family != DEFAULT_FAMILY:
            print(f"note: the SVG embeds the font {family!r}; check that its licence lets you share the file "
                  "(Stay With Me is for personal use only)")

    if args.png is not None:
        args.png.parent.mkdir(parents=True, exist_ok=True)
        args.png.unlink(missing_ok=True)
        height = report["pageHeight"]
        scale = [f"--force-device-scale-factor={args.scale:g}"] if args.scale != 1 else []
        run_chrome(browser, url, args.width, height, *scale, f"--screenshot={args.png.resolve()}")
        if not args.png.is_file() or args.png.stat().st_size == 0:
            sys.exit(f"render failed: {args.png} was not written{hint(browser)}")
        size = f"{round(args.width * args.scale)} x {round(height * args.scale)}"
        print(f"rendered {args.png} ({size})")

    if issues:
        sys.exit(1)
    print("layout: ok")


if __name__ == "__main__":
    main()
