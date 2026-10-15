import json

import pytest

from lint_research import lint_claims, main

GOOD = {
    "id": "c1", "value": "54.7", "metric": "AP", "dataset": "COCO", "split": "val2017",
    "resolution": "640", "hardware": "T4", "arxiv": "2511.09554v2", "locator": "Table 3",
    "quote": "RF-DETR reaches 54.7 AP on COCO val2017", "label": "reported",
}


def test_good_claim_passes():
    assert lint_claims([GOOD]) == []


def test_missing_field_is_reported():
    claim = {k: v for k, v in GOOD.items() if k != "hardware"}
    assert any("c1: missing hardware" in e for e in lint_claims([claim]))


def test_empty_field_is_reported():
    assert any("missing locator" in e for e in lint_claims([{**GOOD, "locator": ""}]))


def test_arxiv_needs_version():
    assert any("arxiv" in e for e in lint_claims([{**GOOD, "arxiv": "2511.09554"}]))


def test_label_must_be_known():
    assert any("label" in e for e in lint_claims([{**GOOD, "label": "sota"}]))


def test_value_must_appear_in_quote():
    assert any("quote" in e for e in lint_claims([{**GOOD, "value": "55.1"}]))


def test_value_must_be_a_string():
    assert any("string" in e for e in lint_claims([{**GOOD, "value": 54.7}]))


def test_duplicate_ids_are_reported():
    assert any("duplicate" in e for e in lint_claims([GOOD, GOOD]))


def test_cli_exit_codes(tmp_path):
    path = tmp_path / "claims.json"
    path.write_text(json.dumps([GOOD]), encoding="utf-8")
    assert main([str(path)]) == 0
    path.write_text(json.dumps([{**GOOD, "value": "1.0"}]), encoding="utf-8")
    assert main([str(path)]) == 1


@pytest.mark.parametrize("value", ["7", "4.7", "54"])
def test_truncated_value_is_rejected(value):
    assert any("quote" in e for e in lint_claims([{**GOOD, "value": value}]))


@pytest.mark.parametrize("quote", [
    "RF-DETR reaches (54.7) AP on COCO val2017",
    "RF-DETR reaches 54.7% AP on COCO val2017",
    "RF-DETR reaches 54.7. AP on COCO val2017",
])
def test_whole_number_in_quote_is_accepted(quote):
    assert lint_claims([{**GOOD, "quote": quote}]) == []


def test_whitespace_only_value_is_missing():
    assert lint_claims([{**GOOD, "value": "   "}]) == ["c1: missing value"]


def test_whitespace_only_hardware_is_missing():
    assert lint_claims([{**GOOD, "hardware": "  "}]) == ["c1: missing hardware"]


def test_cli_accepts_scout_object_with_claims(tmp_path):
    path = tmp_path / "scout.json"
    path.write_text(json.dumps({"claims": [GOOD], "not_found": ["x"]}), encoding="utf-8")
    assert main([str(path)]) == 0


def test_cli_accepts_bare_list(tmp_path):
    path = tmp_path / "claims.json"
    path.write_text(json.dumps([GOOD]), encoding="utf-8")
    assert main([str(path)]) == 0


@pytest.mark.parametrize("text", ['{"claims": "x"}', "[1]", "3", '"x"', "{}", "{not json"])
def test_cli_rejects_bad_shape_cleanly(tmp_path, capsys, text):
    path = tmp_path / "claims.json"
    path.write_text(text, encoding="utf-8")
    assert main([str(path)]) == 1
    err = capsys.readouterr().err.strip()
    assert err and "Traceback" not in err and len(err.splitlines()) == 1


def test_cli_missing_file_is_a_clean_error(tmp_path, capsys):
    assert main([str(tmp_path / "nope.json")]) == 1
    err = capsys.readouterr().err.strip()
    assert err and "Traceback" not in err and len(err.splitlines()) == 1
