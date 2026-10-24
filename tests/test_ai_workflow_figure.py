import hashlib
import io
import json
import os
import re
import struct
import subprocess
import sys
import xml.etree.ElementTree as ElementTree
import zipfile
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1] / "skills/figure"
BUILD = SKILL / "scripts/build_figure.py"
CHECK = SKILL / "scripts/check_figure.py"
BUNDLED_FONT = SKILL / "assets/fonts/PatrickHand-Regular.woff2"
TEMPLATES = sorted((SKILL / "templates").glob("*.figure.js"))
PLACEHOLDERS = ("/*FONT_FACE*/", "/*ROUGH_JS*/", "/*FIGURE_KIT*/", "/*FIGURE_SPEC*/", "__FONT_FAMILY__")
# sha256 of each template's drawn <svg>; UPDATE_GOLDEN=1 rewrites it.
GOLDEN = Path(__file__).resolve().parent / "golden/figure-svg.json"

sys.path.insert(0, str(SKILL / "scripts"))
import check_figure  # noqa: E402
import fetch_fonts  # noqa: E402


def run(script: Path, *args: object, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True,
                          text=True, encoding="utf-8", check=False, env=env)


def build(spec: Path, out: Path, *args: object) -> str:
    result = run(BUILD, spec, out, *args)
    assert result.returncode == 0, result.stderr
    return out.read_text(encoding="utf-8")


def spec_file(tmp_path: Path, draw: str, width: int = 800, height: int = 300) -> Path:
    path = tmp_path / "test.figure.js"
    path.write_text(
        f'const FIGURE = {{ title: "t", subtitle: "s", width: {width}, height: {height},\n'
        f"  draw(k) {{\n{draw}\n  }}\n}};\n", encoding="utf-8")
    return path


def check_spec(tmp_path: Path, draw: str, *build_args: object) -> subprocess.CompletedProcess:
    html = tmp_path / "fig.html"
    build(spec_file(tmp_path, draw), html, *build_args)
    return run(CHECK, html)


def have_browser() -> bool:
    try:
        check_figure.find_browser()
    except SystemExit:
        return False
    return True


# In CI a missing browser is a failure, not a skip: the layout checks would silently not run.
needs_browser = pytest.mark.skipif(not have_browser() and not os.environ.get("CI"), reason="no Chrome or Chromium")


def test_every_template_is_found():
    names = {p.name for p in TEMPLATES}
    assert {"high-level.figure.js", "low-level.figure.js", "pipeline.figure.js",
            "whole-model.figure.js", "delta.figure.js", "icon-sheet.figure.js"} <= names


# ---- build_figure.py ----

@pytest.mark.parametrize("template", TEMPLATES, ids=lambda p: p.stem)
def test_template_builds_offline_with_bundled_font(template, tmp_path):
    html = build(template, tmp_path / "out" / "fig.html")
    assert not any(p in html for p in PLACEHOLDERS)
    assert "font-family: 'Patrick Hand'" in html
    assert "data:font/woff2;base64," in html


def test_vietnamese_alias_uses_the_bundled_face(tmp_path):
    spec = TEMPLATES[0]
    assert build(spec, tmp_path / "a.html") == build(spec, tmp_path / "b.html", "--font", "patrick-hand-vi")


def test_spec_with_closing_script_tag_is_refused(tmp_path):
    spec = spec_file(tmp_path, 'k.label(10, 10, "</script>", 20);')
    result = run(BUILD, spec, tmp_path / "out.html")
    assert result.returncode != 0
    assert "closing script tag" in result.stderr
    assert not (tmp_path / "out.html").exists()


def test_font_file_needs_a_family(tmp_path):
    result = run(BUILD, TEMPLATES[0], tmp_path / "out.html", "--font", BUNDLED_FONT)
    assert result.returncode != 0
    assert "--font-family" in result.stderr


def test_known_font_rejects_a_family(tmp_path):
    result = run(BUILD, TEMPLATES[0], tmp_path / "out.html", "--font", "patrick-hand",
                 "--font-family", "X")
    assert result.returncode != 0


@pytest.mark.parametrize("family", ['Hand"Bad', "Hand'Bad", "Hand<Bad", ""])
def test_unsafe_font_family_is_refused(family, tmp_path):
    result = run(BUILD, TEMPLATES[0], tmp_path / "out.html", "--font", BUNDLED_FONT,
                 "--font-family", family)
    assert result.returncode != 0
    assert "invalid font family" in result.stderr


def test_font_file_is_inlined_under_its_family(tmp_path):
    html = build(TEMPLATES[0], tmp_path / "out.html", "--font", BUNDLED_FONT, "--font-family", "Hand Copy")
    assert "font-family: 'Hand Copy'" in html


# ---- check_figure.py ----

def test_chrome_variable_must_name_an_executable(tmp_path):
    html = tmp_path / "fig.html"
    build(TEMPLATES[0], html)
    result = run(CHECK, html, env={**os.environ, "CHROME": str(tmp_path / "no-such-browser")})
    assert result.returncode != 0
    assert "not an executable browser" in result.stderr
    assert "Traceback" not in result.stderr


@needs_browser
@pytest.mark.parametrize("template", TEMPLATES, ids=lambda p: p.stem)
def test_template_passes_layout_check(template, tmp_path):
    html = tmp_path / "fig.html"
    build(template, html)
    result = run(CHECK, html)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "layout: ok" in result.stdout


@needs_browser
def test_templates_draw_the_same_svg(tmp_path):
    # The kit is shared by every figure, so a kit change must leave each template's strokes as they were
    # (references/kit.md, "Changing the kit"). Fixed seeds make the SVG the same on every build.
    browser = check_figure.find_browser()
    digests = {}
    for template in TEMPLATES:
        html = tmp_path / f"{template.stem}.html"
        build(template, html)
        dom = check_figure.run_chrome(browser, html.resolve().as_uri(), 1800, 1000, "--dump-dom")
        digests[template.name] = hashlib.sha256(check_figure.DRAWN_SVG.search(dom).group(0).encode()).hexdigest()
    if os.environ.get("UPDATE_GOLDEN"):
        GOLDEN.write_text(json.dumps(digests, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    assert digests == json.loads(GOLDEN.read_text(encoding="utf-8")), (
        "a template's SVG changed; if the kit change is meant to change it, run with UPDATE_GOLDEN=1 "
        "and say why in the commit")


@needs_browser
def test_png_holds_the_whole_page(tmp_path):
    html, png = tmp_path / "fig.html", tmp_path / "png" / "fig.png"
    build(SKILL / "templates/whole-model.figure.js", html)
    result = run(CHECK, html, "--png", png)
    assert result.returncode == 0, result.stdout + result.stderr
    width, height = struct.unpack(">II", png.read_bytes()[16:24])
    assert f"({width} x {height})" in result.stdout
    # The figure is 1710 units tall; the page adds the title and margins.
    assert 1710 < height < 2000


def png_size(path: Path) -> tuple[int, int]:
    return struct.unpack(">II", path.read_bytes()[16:24])


@needs_browser
def test_bare_png_holds_the_figure_alone(tmp_path):
    html = tmp_path / "fig.html"
    build(spec_file(tmp_path, 'k.box(40, 40, 100, 60, "plain", "a");'), html)
    for name, args in (("page", ()), ("bare", ("--bare",))):
        result = run(CHECK, html, "--png", tmp_path / f"{name}.png", *args)
        assert result.returncode == 0, result.stdout + result.stderr
    # 800 x 300 units at the default 1800 px window; the page adds the title and its margins.
    assert png_size(tmp_path / "bare.png") == (1800, 675)
    assert png_size(tmp_path / "page.png")[1] > 675


@needs_browser
def test_scale_multiplies_the_png_pixels(tmp_path):
    html, png = tmp_path / "fig.html", tmp_path / "fig.png"
    build(spec_file(tmp_path, 'k.box(40, 40, 100, 60, "plain", "a");'), html)
    result = run(CHECK, html, "--png", png, "--bare", "--scale", "2")
    assert result.returncode == 0, result.stdout + result.stderr
    assert png_size(png) == (3600, 1350)
    assert "(3600 x 1350)" in result.stdout


@pytest.mark.parametrize("scale", ["0.5", "5", "nan", "two"])
def test_scale_outside_1_to_4_is_refused(scale, tmp_path):
    html = tmp_path / "fig.html"
    build(TEMPLATES[0], html)
    result = run(CHECK, html, "--png", tmp_path / "fig.png", "--scale", scale)
    assert result.returncode == 2
    assert "scale" in result.stderr or "number" in result.stderr


@needs_browser
def test_svg_export_is_a_standalone_document(tmp_path):
    html, out = tmp_path / "fig.html", tmp_path / "out" / "fig.svg"
    build(spec_file(tmp_path, 'k.box(40, 40, 300, 60, "plain", "a"); k.label(190, 80, "a & b < c", 21);'), html)
    result = run(CHECK, html, "--svg", out)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "note:" not in result.stdout
    root = ElementTree.fromstring(out.read_bytes())
    ns = "{http://www.w3.org/2000/svg}"
    assert root.tag == ns + "svg"
    assert (root.get("width"), root.get("height")) == ("800", "300")
    assert [child.tag for child in root[:4]] == [ns + "title", ns + "desc", ns + "style", ns + "rect"]
    assert root[0].text == "t" and root[1].text == "s"
    assert root[2].text.count("@font-face") == 1 and "font/woff2;base64," in root[2].text
    assert any(node.text == "a & b < c" for node in root.iter(ns + "text"))


@needs_browser
def test_svg_with_another_font_carries_a_licence_note(tmp_path):
    html = tmp_path / "fig.html"
    build(TEMPLATES[0], html, "--font", BUNDLED_FONT, "--font-family", "Hand Copy")
    result = run(CHECK, html, "--svg", tmp_path / "fig.svg")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "note: the SVG embeds the font 'Hand Copy'" in result.stdout


@needs_browser
def test_checker_reports_each_kind_of_issue(tmp_path):
    result = check_spec(tmp_path, """
    const { box, label, connect } = k;
    box(40, 40, 200, 80, "plain", "small");
    label(140, 90, "a label much too long for the box it sits in", 21);
    label(500, 200, "crossed label", 21);
    label(500, 210, "pressed against it", 21);
    connect([[400, 195], [600, 195]]);
    connect([[100, 150], [100, 260]]);
    box(60, 180, 100, 40, "plain", "in the way");
    box(700, 200, 200, 80, "plain", "past the edge");
    """)
    assert result.returncode == 1
    assert 'text leaves "small"' in result.stdout
    assert 'text overlaps text: "crossed label" and "pressed against it"' in result.stdout
    assert 'connector runs through text "crossed label"' in result.stdout
    assert 'connector crosses "in the way"' in result.stdout
    assert '"past the edge" leaves the canvas' in result.stdout


# One case that must be reported and a twin that must not, per rule, with the exact issue list.
# The canvas is 800 x 300. "BAD_FONT" builds the case with a file that is not a font.
LONG = "a label much too long for the box it sits in"
RULES = [
    ("draw-stops", 'k.box(40, 40, 100, 60, "plan", "a");', ['draw() stopped: Error: unknown box kind: "plan"']),
    ("draw-runs", 'k.box(40, 40, 100, 60, "plain", "a");', []),
    ("font-fails", 'k.label(100, 100, "x", 20); // BAD_FONT', ["font not loaded: text fell back to a system font"]),
    ("font-loads", 'k.label(100, 100, "x", 20);', []),
    ("text-leaves-box", f'k.box(300, 40, 200, 80, "plain", "small"); k.label(400, 90, "{LONG}", 21);',
     [f'text leaves "small": "{LONG}"']),
    ("text-fits-box", 'k.box(300, 40, 200, 80, "plain", "small"); k.label(400, 90, "short", 21);', []),
    ("lines-overlap", 'k.left(40, 100, "first line", 21); k.left(40, 110, "second line", 21);',
     ['text overlaps text: "first line" and "second line"']),
    ("lines-apart", 'k.left(40, 100, "first line", 21); k.left(40, 126, "second line", 21);', []),
    ("label-runs-into-box", 'k.box(300, 40, 200, 80, "plain", "b"); k.left(120, 85, "a gutter label that is long", 21);',
     ['text runs into "b": "a gutter label that is long"']),
    ("label-beside-box", 'k.box(300, 40, 200, 80, "plain", "b"); k.left(120, 85, "short", 21);', []),
    ("box-straddles-panel", 'k.panel(40, 40, 300, 150, "plain", "p"); k.box(200, 100, 200, 60, "plain", "b");',
     ['"b" crosses the edge of "p"']),
    ("box-inside-panel", 'k.panel(40, 40, 300, 150, "plain", "p"); k.box(100, 100, 200, 60, "plain", "b");', []),
    ("panel-hides-box", 'k.box(100, 100, 200, 60, "plain", "b"); k.panel(40, 40, 300, 150, "plain", "p");',
     ['panel "p" hides "b", drawn before it']),
    ("panel-hides-text", 'k.left(100, 100, "early", 21); k.panel(40, 40, 300, 150, "plain", "p");',
     ['panel "p" hides text "early", drawn before it']),
    ("panel-hides-connector", 'k.connect([[60, 120], [300, 120]]); k.panel(40, 40, 300, 150, "plain", "p");',
     ["panel \"p\" hides a connector drawn before it"]),
    ("unfilled-panel-hides-nothing", 'k.box(100, 100, 200, 60, "plain", "b"); k.panel(40, 40, 300, 150, "dashed", "p");',
     []),
    ("connector-crosses-box", 'k.box(300, 100, 100, 60, "plain", "wall"); k.connect([[100, 130], [600, 130]]);',
     ['connector crosses "wall"']),
    ("connector-crosses-panel", 'k.panel(300, 40, 100, 200, "plain", "p"); k.connect([[100, 130], [600, 130]]);', []),
    ("connector-through-text", 'k.label(400, 135, "in the way", 21); k.connect([[100, 130], [700, 130]]);',
     ['connector runs through text "in the way"']),
    ("connector-under-text", 'k.label(400, 100, "in the way", 21); k.connect([[100, 130], [700, 130]]);', []),
    ("diagonal", "k.connect([[100, 100], [300, 200]]);", ["connector segment (100, 100) -> (300, 200) is diagonal"]),
    ("orthogonal", "k.connect([[100, 100], [300, 100], [300, 200]]);", []),
    ("lanes-29-apart", "k.connect([[100, 100], [600, 100]]); k.connect([[100, 129], [600, 129]]);",
     ["connectors 29 apart, lanes need 30: (100, 100) -> (600, 100) and (100, 129) -> (600, 129)"]),
    ("lanes-30-apart", "k.connect([[100, 100], [600, 100]]); k.connect([[100, 130], [600, 130]]);", []),
    ("fan-out-shares-a-bus", "k.connect([[100, 100], [400, 100], [400, 200]]); k.connect([[100, 100], [600, 100]]);",
     []),
    ("merge-shares-a-lane", "k.connect([[100, 100], [600, 100]]); k.connect([[300, 200], [300, 100], [600, 100]]);",
     []),
    ("rides-box-edge", 'k.box(300, 100, 200, 60, "plain", "b"); k.connect([[100, 100], [600, 100]]);',
     ['connector runs along the edge of "b": (100, 100) -> (600, 100)']),
    ("clears-box-edge", 'k.box(300, 100, 200, 60, "plain", "b"); k.connect([[100, 70], [600, 70]]);', []),
    ("box-off-canvas", 'k.box(700, 100, 200, 60, "plain", "past");', ['"past" leaves the canvas']),
    ("box-on-canvas", 'k.box(500, 100, 200, 60, "plain", "past");', []),
    ("text-off-canvas", 'k.left(700, 100, "text past the right edge", 21);',
     ['text leaves the canvas: "text past the right edge"']),
    ("text-on-canvas", 'k.left(40, 100, "text past the right edge", 21);', []),
    ("connector-off-canvas", "k.connect([[100, 100], [900, 100]]);", ["a connector leaves the canvas"]),
    ("connector-on-canvas", "k.connect([[100, 100], [700, 100]]);", []),
]


def issues_of(result: subprocess.CompletedProcess) -> list[str]:
    return [line.removeprefix("issue: ") for line in result.stdout.splitlines() if line.startswith("issue: ")]


@needs_browser
@pytest.mark.parametrize("name, draw, expected", RULES, ids=[r[0] for r in RULES])
def test_each_rule_flags_its_case_and_passes_its_twin(name, draw, expected, tmp_path):
    args = []
    if "BAD_FONT" in draw:
        bad = tmp_path / "bad.woff2"
        bad.write_bytes(b"not a font")
        args = ["--font", bad, "--font-family", "Bad Face"]
    result = check_spec(tmp_path, draw, *args)
    assert issues_of(result) == expected, result.stdout
    assert result.returncode == (1 if expected else 0)


def test_every_issue_the_kit_reports_has_a_case():
    kit = (SKILL / "kit/figure-kit.js").read_text(encoding="utf-8")
    messages = re.findall(r"(?:issues|found)\.push\(`([^`]*)`\)", kit)
    # A push that is not one template literal would escape this test.
    assert len(messages) == len(re.findall(r"(?:issues|found)\.push\((?!\.\.\.)", kit))
    flagged = [issue for _, _, expected in RULES for issue in expected]
    for message in messages:
        pattern = ".*".join(re.escape(part) for part in re.split(r"\$\{[^}]*\}", message))
        assert any(re.fullmatch(pattern, issue) for issue in flagged), f"no RULES case reports: {message}"


@needs_browser
def test_letters_that_meet_across_lines_are_reported(tmp_path):
    # Stacked Vietnamese marks reach about 1 em, past the fixed band, into the g above them.
    result = check_spec(tmp_path, """
    const { left } = k;
    left(40, 100, "gggggggg", 21);
    left(40, 122, "ỂỂỂỂỂỂỂỂ", 21);
    """)
    assert 'text overlaps text: "gggggggg" and "ỂỂỂỂỂỂỂỂ"' in result.stdout


@needs_browser
def test_tall_mark_beside_a_descender_is_not_an_overlap(tmp_path):
    # The apostrophe reaches 0.87 em, but no descender of the title sits above it.
    result = check_spec(tmp_path, """
    const { cbox } = k;
    cbox(40, 100, 520, "dashed", "region loss, weight 1.0", ["BCE: each patch's spoof logit"]);
    """)
    assert result.returncode == 0, result.stdout


@needs_browser
def test_font_that_does_not_load_is_reported(tmp_path):
    bad = tmp_path / "bad.woff2"
    bad.write_bytes(b"not a font")
    result = check_spec(tmp_path, 'const { label } = k; label(100, 100, "x", 20);',
                        "--font", bad, "--font-family", "Bad Face")
    assert "font not loaded" in result.stdout


@needs_browser
def test_repeated_point_in_a_connector_still_draws(tmp_path):
    result = check_spec(tmp_path, """
    const { box, connect } = k;
    const a = box(40, 40, 100, 60, "plain", "a");
    const b = box(400, 40, 100, 60, "plain", "b");
    connect([[a.right, a.mid], [250, a.mid], [250, b.mid], [b.left, b.mid]]);
    """)
    assert result.returncode == 0, result.stdout + result.stderr


@needs_browser
@pytest.mark.parametrize("draw, error", [
    ('const { box } = k;\n    card(40, 40, 200, "plain", "x", []);', "ReferenceError: card is not defined"),
    ('const { box } = k;\n    box(40, 40, 100, 60, "plan", "a");', 'unknown box kind: "plan"'),
    ('const { tag } = k;\n    tag(40, 200, 200, 50, "plain", "no size");', 'text "no size" (x, y, size) needs numbers'),
    ('const { box, connect } = k;\n    const a = box(40, 40, 100, 60, "plain", "a");\n'
     '    connect([[a.right, a.middle], [300, 70]]);', "connector point 0 needs numbers"),
])
def test_what_stops_draw_is_the_first_issue(draw, error, tmp_path):
    result = check_spec(tmp_path, draw)
    assert result.returncode == 1
    first = result.stdout.splitlines()[1]
    assert first.startswith("issue: draw() stopped: ") and error in first, result.stdout


# ---- fetch_fonts.py, with the download replaced by a local archive ----

def archive(files: dict[str, bytes]) -> bytes:
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as z:
        for name, body in files.items():
            z.writestr(name, body)
    return data.getvalue()


@pytest.fixture
def font_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch_fonts, "FONT_CACHE", tmp_path)
    monkeypatch.setattr(fetch_fonts, "STAY_WITH_ME_OTF", tmp_path / "StayWithMe.otf")
    monkeypatch.setattr(fetch_fonts, "STAY_WITH_ME_TERMS", tmp_path / "StayWithMe-terms.txt")
    return tmp_path


def test_fetch_saves_font_and_terms_whatever_their_case(font_cache, monkeypatch):
    body = archive({"Stay With Me.OTF": b"OTTO font", "Terms.TXT": b"personal use only"})
    monkeypatch.setattr(fetch_fonts, "get", lambda url: body)
    fetch_fonts.main()
    assert (font_cache / "StayWithMe.otf").read_bytes() == b"OTTO font"
    assert (font_cache / "StayWithMe-terms.txt").read_bytes() == b"personal use only"
    assert not list(font_cache.glob("*.part"))


def test_fetch_refuses_a_file_that_is_not_opentype(font_cache, monkeypatch):
    body = archive({"font.otf": b"<html>", "terms.txt": b"t"})
    monkeypatch.setattr(fetch_fonts, "get", lambda url: body)
    with pytest.raises(SystemExit):
        fetch_fonts.main()
    assert not (font_cache / "StayWithMe.otf").exists()


def test_fetch_runs_again_when_the_terms_are_missing(font_cache, monkeypatch):
    (font_cache / "StayWithMe.otf").write_bytes(b"OTTO old")
    body = archive({"font.otf": b"OTTO new", "terms.txt": b"t"})
    monkeypatch.setattr(fetch_fonts, "get", lambda url: body)
    fetch_fonts.main()
    assert (font_cache / "StayWithMe-terms.txt").exists()
    assert (font_cache / "StayWithMe.otf").read_bytes() == b"OTTO new"
