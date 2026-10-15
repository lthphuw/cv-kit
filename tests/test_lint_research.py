import json

import pytest

from lint_research import blind, lint_claims, lint_report, main, merge_checks, normalise

GOOD = {
    "id": "rf-detr-1", "kind": "accuracy", "value": "54.7", "metric": "AP", "dataset": "COCO",
    "split": "val2017", "resolution": "640", "arxiv": "2511.09554v2", "locator": "Table 3",
    "quote": "RF-DETR reaches 54.7 AP on COCO val2017", "label": "reported",
    "measured_by": "authors", "retrieved": "2026-10-15",
}
LATENCY = {
    **{k: v for k, v in GOOD.items() if k not in ("dataset", "split")},
    "id": "rf-detr-2", "kind": "latency", "value": "4.5", "metric": "latency ms",
    "hardware": "T4", "precision": "FP16", "batch": "1", "quote": "runs at 4.5 ms on a T4",
}
FOUND = {"id": "rf-detr-1", "status": "found", "found": "Table 3: RF-DETR (L) 54.7 AP"}
CHECKED = {**GOOD, "check": "confirmed", "found": FOUND["found"], "note": None}

TABLE = """# Decision

## 3. Candidate comparison

| Candidate | Value | Metric | Claim |
|---|---|---|---|
| RF-DETR | {value} | AP | {tag} |
| Other | not comparable | AP | — |

## 4. Recommended design
RF-DETR is the pick [rf-detr-1].
"""


def report(value="54.7", tag="[rf-detr-1]"):
    return TABLE.format(value=value, tag=tag)


# ---- claims ----

def test_good_claims_pass():
    assert lint_claims([GOOD, LATENCY]) == []


@pytest.mark.parametrize("field", ["kind", "metric", "locator", "retrieved", "dataset", "split"])
def test_missing_field_is_reported(field):
    claim = {k: v for k, v in GOOD.items() if k != field}
    assert f"rf-detr-1: missing {field}" in lint_claims([claim])


def test_accuracy_claim_needs_no_hardware():
    assert "hardware" not in GOOD and lint_claims([GOOD]) == []


@pytest.mark.parametrize("field", ["hardware", "precision", "batch", "resolution"])
def test_latency_claim_needs_its_protocol(field):
    claim = {k: v for k, v in LATENCY.items() if k != field}
    assert lint_claims([claim]) == [f"rf-detr-2: missing {field}"]


def test_unknown_kind_is_reported():
    assert any("kind 'speed'" in e for e in lint_claims([{**GOOD, "kind": "speed"}]))


def test_empty_field_is_reported():
    assert "rf-detr-1: missing locator" in lint_claims([{**GOOD, "locator": ""}])


def test_arxiv_needs_version():
    assert any("arxiv" in e for e in lint_claims([{**GOOD, "arxiv": "2511.09554"}]))


def test_a_doi_or_url_can_be_the_source():
    no_arxiv = {k: v for k, v in GOOD.items() if k != "arxiv"}
    assert lint_claims([{**no_arxiv, "doi": "10.1109/ICCV51070.2023.00371"}]) == []
    assert lint_claims([{**no_arxiv, "url": "https://openaccess.thecvf.com/content/x.html"}]) == []


def test_exactly_one_source():
    no_arxiv = {k: v for k, v in GOOD.items() if k != "arxiv"}
    assert any("exactly one source" in e for e in lint_claims([no_arxiv]))
    assert any("exactly one source" in e for e in lint_claims([{**GOOD, "doi": "10.1/x"}]))


@pytest.mark.parametrize("ref", ["https://doi.org/10.1109/x", "doi:10.1109/x"])
def test_doi_is_bare(ref):
    claim = {**{k: v for k, v in GOOD.items() if k != "arxiv"}, "doi": ref}
    assert any("doi" in e for e in lint_claims([claim]))


def test_url_on_a_moving_host_needs_a_revision():
    claim = {**{k: v for k, v in GOOD.items() if k != "arxiv"},
             "url": "https://huggingface.co/org/model/blob/main/README.md"}
    assert any("revision" in e for e in lint_claims([claim]))
    assert lint_claims([{**claim, "revision": "0123abc"}]) == []


def test_url_must_be_https():
    claim = {**{k: v for k, v in GOOD.items() if k != "arxiv"}, "url": "http://example.org/x"}
    assert any("https://" in e for e in lint_claims([claim]))


def test_label_must_be_known():
    assert any("label" in e for e in lint_claims([{**GOOD, "label": "sota"}]))


def test_reported_claim_says_who_measured():
    assert any("measured_by" in e for e in lint_claims([{**GOOD, "measured_by": None}]))
    assert lint_claims([{**GOOD, "measured_by": "third-party"}]) == []


def test_reproduced_claim_points_at_its_run():
    claim = {**GOOD, "label": "reproduced"}
    assert any("run" in e for e in lint_claims([claim]))
    assert lint_claims([{**claim, "run": "runs/2026-10-15/eval.log"}]) == []


def test_retrieved_is_a_date():
    assert any("retrieved" in e for e in lint_claims([{**GOOD, "retrieved": "yesterday"}]))


@pytest.mark.parametrize("bad", ["c1", "RF-DETR-1", "rf-detr", "rf_detr-1"])
def test_id_is_slug_and_number(bad):
    assert any("id must be" in e for e in lint_claims([{**GOOD, "id": bad}]))


def test_value_must_appear_in_quote():
    assert any("quote" in e for e in lint_claims([{**GOOD, "value": "55.1"}]))


def test_value_must_be_a_string():
    assert any("string" in e for e in lint_claims([{**GOOD, "value": 54.7}]))


def test_duplicate_ids_are_reported():
    assert any("duplicate" in e for e in lint_claims([GOOD, GOOD]))


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
    assert lint_claims([{**GOOD, "value": "   "}]) == ["rf-detr-1: missing value"]


# ---- blind view and verdicts ----

def test_blind_view_hides_what_the_scout_found():
    view = blind([{**GOOD, "source_file": "sources/a.html"}])[0]
    assert {"value", "quote", "source_file", "label", "measured_by", "retrieved"}.isdisjoint(view)
    assert view["locator"] == "Table 3" and view["arxiv"] == "2511.09554v2" and view["split"] == "val2017"


@pytest.mark.parametrize("field", ["check", "found", "note"])
def test_ledger_may_not_carry_a_verdict(field):
    assert any("checks file" in e for e in lint_claims([{**GOOD, field: "confirmed"}]))


def test_value_in_copied_text_is_confirmed():
    merged, errors = merge_checks([GOOD], [FOUND])
    assert errors == [] and merged[0]["check"] == "confirmed"


def test_other_value_in_copied_text_differs():
    merged, errors = merge_checks([GOOD], [{**FOUND, "found": "Table 3: RF-DETR (L) 54.1 AP"}])
    assert errors == [] and merged[0]["check"] == "differs"


@pytest.mark.parametrize("status", ["wrong-paper", "absent", "unreachable"])
def test_other_statuses_need_a_note(status):
    entry = {"id": "rf-detr-1", "status": status}
    assert any("needs a note" in e for e in merge_checks([GOOD], [entry])[1])
    merged, errors = merge_checks([GOOD], [{**entry, "note": "arXiv answered 503"}])
    assert errors == [] and merged[0]["check"] == status


def test_found_status_needs_the_copied_text():
    assert any("needs found" in e for e in merge_checks([GOOD], [{**FOUND, "found": ""}])[1])


@pytest.mark.parametrize("checks, message", [
    ([], "not checked by the verifier"),
    ([FOUND, FOUND], "checked twice"),
    ([FOUND, {**FOUND, "id": "yolo-1"}], "not in the ledger"),
    ([{**FOUND, "status": "ok"}], "status 'ok'"),
    ([{**FOUND, "value": "54.7"}], "unknown key 'value'"),
])
def test_checks_must_match_the_ledger_one_to_one(checks, message):
    assert any(message in e for e in merge_checks([GOOD], checks)[1])


# ---- saved copy of the source ----

def test_quote_is_found_in_a_saved_html_page(tmp_path):
    (tmp_path / "sources").mkdir()
    (tmp_path / "sources/page.html").write_text(
        "<p>RF-DETR <b>reaches</b>\n 54.7&nbsp;AP on COCO val2017</p>"
        "<math><annotation>54.7 AP</annotation></math><script>var x = 1;</script>", encoding="utf-8")
    assert lint_claims([{**GOOD, "source_file": "sources/page.html"}], tmp_path) == []


def test_quote_missing_from_the_saved_page(tmp_path):
    (tmp_path / "page.txt").write_text("RF-DETR reaches 53.0 AP on COCO val2017", encoding="utf-8")
    errors = lint_claims([{**GOOD, "source_file": "page.txt"}], tmp_path)
    assert errors == ["rf-detr-1: quote is not in page.txt; copy it from the saved page, not from memory"]


def test_quote_in_a_skipped_tag_does_not_count(tmp_path):
    (tmp_path / "page.html").write_text("<script>RF-DETR reaches 54.7 AP on COCO val2017</script>",
                                        encoding="utf-8")
    assert any("quote is not in" in e for e in lint_claims([{**GOOD, "source_file": "page.html"}], tmp_path))


@pytest.mark.parametrize("ref", ["missing.html", "../outside.txt"])
def test_saved_copy_must_exist_inside_the_folder(tmp_path, ref):
    (tmp_path / "outside.txt").write_text(GOOD["quote"], encoding="utf-8")
    root = tmp_path / "work"
    root.mkdir()
    assert any("inside the ledger's folder" in e for e in lint_claims([{**GOOD, "source_file": ref}], root))


def test_normalise_folds_case_space_and_width():
    assert normalise("RF-DETR  Reaches\n５４.7") == "rf-detr reaches 54.7"


# ---- report ----

def test_good_report_passes():
    assert lint_report(report(), [CHECKED]) == []


def test_report_number_needs_a_tag():
    assert any("names no claim tag" in e for e in lint_report(report(tag="—"), [CHECKED]))


def test_report_number_must_be_the_claim_value():
    assert any("is not the value" in e for e in lint_report(report(value="55.1"), [CHECKED]))


def test_report_tag_must_exist():
    errors = lint_report(report(tag="[yolo-1]"), [CHECKED])
    assert any("[yolo-1] names no claim" in e for e in errors)


def test_unconfirmed_claim_must_be_marked():
    claim = {**GOOD, "check": "unreachable", "note": "arXiv 503"}
    errors = lint_report(report(), [claim])
    assert errors and all("say unconfirmed" in e for e in errors)
    marked = report(tag="[rf-detr-1] unconfirmed").replace("pick [rf-detr-1]", "pick [rf-detr-1] (unconfirmed)")
    assert lint_report(marked, [claim]) == []


def test_report_without_a_comparison_table():
    assert lint_report("# x\n\n## 3. Candidate comparison\nnone\n", [CHECKED]) == [
        "report: section 3 has no comparison table"]


def test_markdown_links_are_not_tags():
    text = report() + "\nSee [the paper-2](https://arxiv.org/abs/2511.09554v2).\n"
    assert lint_report(text, [CHECKED]) == []


# ---- command line ----

def write(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def test_cli_exit_codes(tmp_path):
    assert main([write(tmp_path / "claims.json", [GOOD])]) == 0
    assert main([write(tmp_path / "claims.json", [{**GOOD, "value": "1.0"}])]) == 1


def test_cli_report_mode(tmp_path):
    (tmp_path / "report.md").write_text(report(), encoding="utf-8")
    claims = write(tmp_path / "claims.json", [GOOD])
    checks = write(tmp_path / "checks.json", {"checks": [FOUND]})
    assert main([claims, "--checks", checks, "--report", str(tmp_path / "report.md")]) == 0
    differs = write(tmp_path / "checks.json", [{**FOUND, "found": "54.1 AP"}])
    assert main([claims, "--checks", differs, "--report", str(tmp_path / "report.md")]) == 1


def test_cli_report_needs_checks(tmp_path):
    (tmp_path / "report.md").write_text(report(), encoding="utf-8")
    assert main([write(tmp_path / "claims.json", [GOOD]), "--report", str(tmp_path / "report.md")]) == 2


def test_cli_prints_verdict_counts(tmp_path, capsys):
    claims = write(tmp_path / "claims.json", [GOOD, LATENCY])
    checks = write(tmp_path / "checks.json", [FOUND, {"id": "rf-detr-2", "status": "absent", "note": "no T4 row"}])
    assert main([claims, "--checks", checks]) == 0
    assert "verdicts: 1 confirmed, 0 differs, 0 wrong-paper, 1 absent, 0 unreachable" in capsys.readouterr().out


def test_cli_writes_the_blind_view_only_for_a_clean_ledger(tmp_path):
    out = tmp_path / "blind.json"
    assert main([write(tmp_path / "claims.json", [GOOD]), "--blind", str(out)]) == 0
    assert "quote" not in out.read_text(encoding="utf-8")
    out.unlink()
    assert main([write(tmp_path / "claims.json", [{**GOOD, "value": "1.0"}]), "--blind", str(out)]) == 1
    assert not out.exists()


def test_cli_reports_a_missing_report_cleanly(tmp_path, capsys):
    claims, checks = write(tmp_path / "claims.json", [GOOD]), write(tmp_path / "checks.json", [FOUND])
    assert main([claims, "--checks", checks, "--report", str(tmp_path / "no.md")]) == 1
    assert "Traceback" not in capsys.readouterr().err


def test_cli_accepts_scout_object_with_claims(tmp_path):
    assert main([write(tmp_path / "scout.json", {"claims": [GOOD], "not_found": ["x"]})]) == 0


def test_cli_prints_how_many_claims_were_checked_against_a_copy(tmp_path, capsys):
    (tmp_path / "page.txt").write_text(GOOD["quote"], encoding="utf-8")
    assert main([write(tmp_path / "claims.json", [{**GOOD, "source_file": "page.txt"}, LATENCY])]) == 0
    assert "2 claims, 1 checked against a saved copy" in capsys.readouterr().out


@pytest.mark.parametrize("text", ['{"claims": "x"}', "[1]", "3", '"x"', "{}", "{not json",
                                  '[{"id": "a-1", "id": "b-1"}]', '[{"value": NaN}]'])
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


def test_cli_usage(capsys):
    assert main([]) == 2
    assert main(["a", "--nope", "b"]) == 2
