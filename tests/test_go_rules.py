"""The Go catalogue is well formed, and every rule ID the Go summaries cite exists in it."""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "shared" / "go-style.md"
SUMMARIES = sorted((ROOT / "rules").glob("go-*.md")) + [ROOT / "skills" / "develop" / "references" / "go-testing.md"]
AREAS = {"TOOL", "NAME", "DOC", "IMP", "ERR", "LANG", "VAR", "FN", "IFACE", "STATE", "RES", "CONC", "EDGE", "TEST", "LIB"}
ENTRY = re.compile(r"^- \*\*(GO-([A-Z]+)-(\d+))\*\* \[(MUST NOT|MUST|PREFER)\] ")
CITED = re.compile(r"\bGO-[A-Z]+-\d+\b")


def _entries():
    rows = []
    for line in CATALOGUE.read_text(encoding="utf-8").splitlines():
        if line.startswith("- **GO-"):
            match = ENTRY.match(line)
            assert match, f"malformed entry: {line[:90]}"
            rows.append((match.group(1), match.group(2), int(match.group(3)), line))
    return rows


def test_the_catalogue_has_entries_for_every_area():
    assert {area for _, area, _, _ in _entries()} == AREAS


def test_ids_are_unique():
    ids = [rid for rid, _, _, _ in _entries()]
    assert len(ids) == len(set(ids))


def test_numbering_has_no_gaps_within_an_area():
    numbers: dict[str, list[int]] = {}
    for _, area, number, _ in _entries():
        numbers.setdefault(area, []).append(number)
    for area, seen in numbers.items():
        assert sorted(seen) == list(range(1, len(seen) + 1)), area


@pytest.mark.parametrize("field", ["*Why:*", "*Check:*", "*Severity:*", "*Source:*"])
def test_every_entry_has_each_field(field):
    for rid, _, _, line in _entries():
        assert field in line, f"{rid} lacks {field}"


def test_every_severity_is_critical_major_or_minor():
    for rid, _, _, line in _entries():
        assert re.search(r"\*Severity:\* (Critical|Major|Minor)\b", line), rid


def test_every_id_cited_by_a_summary_exists():
    known = {rid for rid, _, _, _ in _entries()}
    for summary in SUMMARIES:
        cited = set(CITED.findall(summary.read_text(encoding="utf-8")))
        if summary.parent.name == "rules":
            assert cited, f"{summary.name} cites no rule"
        assert cited - known == set(), f"{summary.name} cites unknown IDs"


@pytest.mark.parametrize("name, glob", [
    ("go-style.md", "**/*.go"),
    ("go-concurrency.md", "**/*.go"),
    ("go-tests.md", "**/*_test.go"),
])
def test_rule_files_are_scoped_to_go_sources(name, glob):
    text = (ROOT / "rules" / name).read_text(encoding="utf-8")
    assert text.startswith("---\npaths:\n")
    assert f'"{glob}"' in text.split("---", 2)[1]


def test_rule_files_stay_within_the_line_limit():
    for summary in SUMMARIES:
        if summary.parent.name == "rules":
            assert summary.read_text(encoding="utf-8").count("\n") + 1 <= 200, summary.name
