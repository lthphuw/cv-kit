import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "docs/figures/demo_gifs.py"
spec = importlib.util.spec_from_file_location("demo_gifs", SCRIPT)
demo_gifs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo_gifs)


@pytest.mark.parametrize("scene", [demo_gifs.develop, demo_gifs.research])
def test_every_frame_ends_with_the_main_row_and_no_agent_rows(scene):
    frames = scene().frames
    assert frames
    for page, _hold in frames:
        assert page.count("ctx ") == 1  # the main row, drawn once
        body = page.split("<pre>", 1)[1].removesuffix("</pre>")
        assert "◐" not in body and "✓" not in body  # the agent row icons of 0.11 and older
        assert "ctx " in body.splitlines()[-1]  # the main row is the last line
