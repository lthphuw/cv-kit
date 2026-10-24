#!/usr/bin/env python3
"""Build one figure spec into a self-contained HTML file.

Usage: python3 build_figure.py SPEC.figure.js OUT.html [--font NAME] [--font-family NAME]

NAME is a known font (patrick-hand, the default, or stay-with-me) or the path to a font
file, which then needs --font-family. The kit, the spec, rough.js and the font are
inlined, so the output opens offline.
"""

import argparse
import base64
import dataclasses
import pathlib
import re
import sys

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
ASSETS = SKILL_DIR / "assets"
KIT_DIR = SKILL_DIR / "kit"
FONT_CACHE = pathlib.Path.home() / ".cache" / "ai-workflow-figure" / "fonts"
DEFAULT_FONT = "patrick-hand"
PLACEHOLDER = re.compile(r"/\*(FONT_FACE|ROUGH_JS|FIGURE_KIT|FIGURE_SPEC)\*/|__FONT_FAMILY__")
# Data URL type and CSS format() name for each font file extension.
FONT_FORMATS: dict[str, tuple[str, str]] = {
    ".otf": ("font/otf", "opentype"),
    ".ttf": ("font/ttf", "truetype"),
    ".woff": ("font/woff", "woff"),
    ".woff2": ("font/woff2", "woff2"),
}
# Characters that would break the CSS or the JS string the family name goes into.
FORBIDDEN_IN_FAMILY = frozenset("\"'\\<>\n\r")


@dataclasses.dataclass(frozen=True)
class FontFile:
    """A font file on disk and the family name its @font-face declares."""

    path: pathlib.Path
    family: str


# The bundled Patrick Hand is the full face (SIL OFL 1.1), Vietnamese letters included.
PATRICK_HAND = FontFile(ASSETS / "fonts" / "PatrickHand-Regular.woff2", "Patrick Hand")
KNOWN_FONTS: dict[str, FontFile] = {
    "patrick-hand": PATRICK_HAND,
    # Older build commands name the Vietnamese face separately; it is the same file.
    "patrick-hand-vi": PATRICK_HAND,
    # Free for personal use only; scripts/fetch_fonts.py saves it outside the repository.
    "stay-with-me": FontFile(FONT_CACHE / "StayWithMe.otf", "Stay With Me"),
}


def resolve_font(name: str, family: str | None) -> FontFile:
    """Return the font the figure uses: a known name, or a font file with its family."""
    if name in KNOWN_FONTS:
        if family is not None:
            sys.exit(f"--font-family applies to a font file, not to the known font {name!r}")
        font = KNOWN_FONTS[name]
        if not font.path.is_file():
            sys.exit(f"font file missing: {font.path} (run scripts/fetch_fonts.py)")
        return font
    path = pathlib.Path(name)
    if family is None:
        sys.exit(f"{name!r} is not a known font; a font file needs --font-family")
    if not path.is_file():
        sys.exit(f"no such font file: {path}")
    if path.suffix.lower() not in FONT_FORMATS:
        sys.exit(f"unsupported font type: {path.name!r}")
    if not family or FORBIDDEN_IN_FAMILY.intersection(family):
        sys.exit(f"invalid font family: {family!r}")
    return FontFile(path, family)


def font_face(font: FontFile) -> str:
    """Return an @font-face rule with the font inlined as base64."""
    mime, css_format = FONT_FORMATS[font.path.suffix.lower()]
    encoded = base64.b64encode(font.path.read_bytes()).decode("ascii")
    # One weight is declared on purpose: the browser then synthesises bold for
    # font-weight 700, which the figure titles use.
    return (
        f"@font-face {{ font-family: '{font.family}'; font-style: normal; font-weight: 400; "
        f"src: url(data:{mime};base64,{encoded}) format('{css_format}'); }}"
    )


def main() -> None:
    """Parse the arguments and write the built figure."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("spec", type=pathlib.Path, help="figure spec (.figure.js)")
    parser.add_argument("out", type=pathlib.Path, help="output HTML file")
    parser.add_argument("--font", default=DEFAULT_FONT, help="known font name or font file")
    parser.add_argument("--font-family", help="CSS family name, required for a font file")
    args = parser.parse_args()

    font = resolve_font(args.font, args.font_family)
    rough = (ASSETS / "rough.js").read_text(encoding="utf-8")
    kit = (KIT_DIR / "figure-kit.js").read_text(encoding="utf-8")
    spec = args.spec.read_text(encoding="utf-8")
    for label, source in (("rough.js", rough), ("figure kit", kit), ("figure spec", spec)):
        if "</script" in source.lower():
            sys.exit(f"{label} contains a closing script tag; refusing to inline it")

    # One pass over the shell: inserted sources are never scanned for placeholders.
    pieces = {
        "/*FONT_FACE*/": font_face(font),
        "/*ROUGH_JS*/": rough,
        "/*FIGURE_KIT*/": kit,
        "/*FIGURE_SPEC*/": spec,
        "__FONT_FAMILY__": font.family,
    }
    shell = (KIT_DIR / "shell.html").read_text(encoding="utf-8")
    out = PLACEHOLDER.sub(lambda m: pieces[m.group(0)], shell)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(out, encoding="utf-8")
    print("built", args.out, f"{len(out) // 1024} KB", f"font {font.family!r}")


if __name__ == "__main__":
    main()
