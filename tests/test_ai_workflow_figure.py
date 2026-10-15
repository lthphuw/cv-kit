import io
import os
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1] / "skills/ai-workflow-figure"
BUILD = SKILL / "scripts/build_figure.py"
CHECK = SKILL / "scripts/check_figure.py"
BUNDLED_FONT = SKILL / "assets/fonts/PatrickHand-Regular.woff2"
TEMPLATES = sorted((SKILL / "templates").glob("*.figure.js"))
PLACEHOLDERS = ("/*FONT_FACE*/", "/*ROUGH_JS*/", "/*FIGURE_KIT*/", "/*FIGURE_SPEC*/", "__FONT_FAMILY__")

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


needs_browser = pytest.mark.skipif(not have_browser(), reason="no Chrome or Chromium")


def test_every_template_is_found():
    names = {p.name for p in TEMPLATES}
    assert {"high-level.figure.js", "low-level.figure.js", "pipeline.figure.js",
            "whole-model.figure.js", "icon-sheet.figure.js"} <= names


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
def test_png_holds_the_whole_page(tmp_path):
    html, png = tmp_path / "fig.html", tmp_path / "png" / "fig.png"
    build(SKILL / "templates/whole-model.figure.js", html)
    result = run(CHECK, html, "--png", png)
    assert result.returncode == 0, result.stdout + result.stderr
    width, height = struct.unpack(">II", png.read_bytes()[16:24])
    assert f"({width} x {height})" in result.stdout
    # The figure is 1710 units tall; the page adds the title and margins.
    assert 1710 < height < 2000


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
