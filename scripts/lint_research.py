"""Reject a research claims ledger, the verifier's checks, or a report the evidence does not support.

Usage: lint_research.py CLAIMS.json [--blind OUT.json] [--checks CHECKS.json] [--report REPORT.md]

Every claim needs its common fields, the fields its kind needs, and exactly one source. The
value must appear as a whole number in the quote. A claim with a `source_file` (a saved copy
of the page, relative to the ledger's folder) must have its quote in that file.

--blind writes the ledger without values, quotes or saved copies: what the verifier is given,
so it copies what the source says before it can know what the scout claimed. The verifier
answers in a checks file, one entry per claim: `found` with the text it copied at the locator,
or `wrong-paper`, `absent` or `unreachable` with a note. --checks merges them and sets each
claim's verdict: `confirmed` when the claimed value is in the copied text, `differs` when not.
--report (which needs --checks) also checks the report: every claim tag names a claim, a claim
that is not `confirmed` is cited only on a line that says "unconfirmed", and every number in
the comparison table of section 3 is the value of a claim its row names.
"""
from __future__ import annotations

import argparse
import html.parser
import json
import re
import sys
import unicodedata
from pathlib import Path

COMMON = ("id", "kind", "value", "metric", "locator", "quote", "label", "retrieved")
KIND_FIELDS = {
    "accuracy": ("dataset", "split", "resolution"),
    "latency": ("hardware", "precision", "batch", "resolution"),
    "size": (),
}
SOURCES = ("arxiv", "doi", "url")
LABELS = {"reported", "reproduced", "unverified"}
MEASURED_BY = {"authors", "third-party"}
STATUSES = {"found", "wrong-paper", "absent", "unreachable"}
CHECK_KEYS = {"id", "status", "found", "note"}
# Fields only the verifier's checks file may set, and fields the verifier must not see.
VERDICT_FIELDS = ("check", "found", "note")
HIDDEN = ("value", "quote", "source_file", "label", "measured_by", "run", "retrieved")
# Pages that change between commits: a claim read from them names the revision it read.
MOVING_HOSTS = re.compile(r"^https://(huggingface\.co|github\.com|raw\.githubusercontent\.com)/")
ARXIV_RE = re.compile(r"^\d{4}\.\d{4,5}v\d+$")
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# A claim id is the candidate's slug and a number, so ids from different scouts never collide.
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*-\d+$")
TAG_RE = re.compile(r"\[([a-z0-9]+(?:-[a-z0-9]+)*-\d+)\](?!\()")
UNCONFIRMED = "unconfirmed"
SKIPPED_TAGS = {"script", "style", "annotation", "annotation-xml"}


def _is_blank(value: object) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _has_number(value: str, text: str) -> bool:
    # The value must be a whole number in the text: no digit or dot before it, and no digit
    # or fraction after it. So "7" and "4.7" do not match "54.7", while a sentence-final
    # period ("54.7. AP") and "(54.7)" or "54.7%" still match.
    return re.search(r"(?<![\d.])" + re.escape(value.strip()) + r"(?!\d|\.\d)", text) is not None


class _TextOnly(html.parser.HTMLParser):
    """Collect the visible text of an HTML page, without scripts, styles or TeX annotations."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skipping = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in SKIPPED_TAGS:
            self.skipping += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIPPED_TAGS and self.skipping:
            self.skipping -= 1

    def handle_data(self, data: str) -> None:
        if not self.skipping:
            self.parts.append(data)


def normalise(text: str, is_html: bool = False) -> str:
    """Return text as compared with a quote: visible text, NFKC, one space per run, casefolded."""
    if is_html:
        parser = _TextOnly()
        parser.feed(text)
        parser.close()
        text = " ".join(parser.parts)
    return " ".join(unicodedata.normalize("NFKC", text).split()).casefold()


def _check_source(tag: str, claim: dict) -> list[str]:
    named = [field for field in SOURCES if not _is_blank(claim.get(field))]
    if len(named) != 1:
        return [f"{tag}: needs exactly one source of {', '.join(SOURCES)} (found {len(named)})"]
    field, ref = named[0], str(claim[named[0]])
    if field == "arxiv" and not ARXIV_RE.match(ref):
        return [f"{tag}: arxiv {ref!r} must look like 2511.09554v2 (id plus version)"]
    if field == "doi" and not DOI_RE.match(ref):
        return [f"{tag}: doi {ref!r} must look like 10.1109/ICCV51070.2023.00371 (no https://doi.org/)"]
    if field == "url":
        if not ref.startswith("https://"):
            return [f"{tag}: url {ref!r} must start with https://"]
        if MOVING_HOSTS.match(ref) and _is_blank(claim.get("revision")):
            return [f"{tag}: a claim read from {ref} needs the commit or tag it read in revision"]
    return []


def _check_saved_copy(tag: str, claim: dict, root: Path) -> list[str]:
    path = (root / str(claim["source_file"])).resolve()
    if root.resolve() not in path.parents or not path.is_file():
        return [f"{tag}: source_file {claim['source_file']!r} is not a file inside the ledger's folder"]
    text = path.read_text(encoding="utf-8", errors="replace")
    page = normalise(text, path.suffix.lower() in {".html", ".htm", ".xml"})
    if normalise(str(claim.get("quote", ""))) not in page:
        return [f"{tag}: quote is not in {claim['source_file']}; copy it from the saved page, not from memory"]
    return []


def lint_claims(claims: list[dict], root: Path | None = None) -> list[str]:
    """Return one error string per problem in the claims; root resolves each source_file."""
    errors: list[str] = []
    seen: set[str] = set()
    for index, claim in enumerate(claims):
        tag = str(claim.get("id") or f"#{index}")
        kind = claim.get("kind")
        fields = COMMON + KIND_FIELDS.get(kind, ())
        errors += [f"{tag}: missing {field}" for field in fields if _is_blank(claim.get(field))]
        if not _is_blank(claim.get("id")) and not ID_RE.match(tag):
            errors.append(f"{tag}: id must be the candidate slug and a number, like rf-detr-3")
        if tag in seen:
            errors.append(f"{tag}: duplicate id")
        seen.add(tag)
        if kind is not None and kind not in KIND_FIELDS:
            errors.append(f"{tag}: kind {kind!r} must be one of {sorted(KIND_FIELDS)}")
        errors += _check_source(tag, claim)
        label = claim.get("label")
        if label and label not in LABELS:
            errors.append(f"{tag}: label {label!r} must be one of {sorted(LABELS)}")
        if label == "reported" and claim.get("measured_by") not in MEASURED_BY:
            errors.append(f"{tag}: a reported claim needs measured_by, one of {sorted(MEASURED_BY)}")
        if label == "reproduced" and _is_blank(claim.get("run")):
            errors.append(f"{tag}: a reproduced claim needs run, the log or notebook of that run")
        if claim.get("retrieved") and not DATE_RE.match(str(claim["retrieved"])):
            errors.append(f"{tag}: retrieved {claim['retrieved']!r} must be a date like 2026-10-15")
        value = claim.get("value")
        if not _is_blank(value):
            if not isinstance(value, str):
                errors.append(f"{tag}: value must be a string copied from the quote")
            elif claim.get("quote") and not _has_number(value, str(claim["quote"])):
                errors.append(f"{tag}: value {value!r} does not appear as a whole number in its quote")
        errors += [f"{tag}: {field} belongs in the verifier's checks file, not the ledger"
                   for field in VERDICT_FIELDS if field in claim]
        if not _is_blank(claim.get("source_file")) and not _is_blank(claim.get("quote")) and root is not None:
            errors += _check_saved_copy(tag, claim, root)
    return errors


def blind(claims: list[dict]) -> list[dict]:
    """Return the claims as the verifier sees them: where to look, not what was found there."""
    return [{k: v for k, v in claim.items() if k not in HIDDEN} for claim in claims]


def merge_checks(claims: list[dict], checks: list[dict]) -> tuple[list[dict], list[str]]:
    """Return the claims with their verdicts, and one error per malformed or missing check."""
    errors: list[str] = []
    by_id: dict[str, dict] = {}
    known = {str(claim.get("id")) for claim in claims}
    for index, entry in enumerate(checks):
        tag = str(entry.get("id") or f"check #{index}")
        status = entry.get("status")
        errors += [f"{tag}: unknown key {key!r} in checks" for key in sorted(set(entry) - CHECK_KEYS)]
        if tag not in known:
            errors.append(f"{tag}: checks name a claim that is not in the ledger")
        elif tag in by_id:
            errors.append(f"{tag}: checked twice")
        if status not in STATUSES:
            errors.append(f"{tag}: status {status!r} must be one of {sorted(STATUSES)}")
        elif status == "found" and (_is_blank(entry.get("found")) or not isinstance(entry["found"], str)):
            errors.append(f"{tag}: status found needs found, the text copied at the locator")
        elif status != "found" and _is_blank(entry.get("note")):
            errors.append(f"{tag}: status {status!r} needs a note saying why")
        by_id.setdefault(tag, entry)
    merged = []
    for claim in claims:
        entry = by_id.get(str(claim.get("id")))
        if entry is None:
            errors.append(f"{claim.get('id')}: not checked by the verifier")
            merged.append(claim)
            continue
        check = entry.get("status")
        if check == "found":
            hit = isinstance(entry.get("found"), str) and _has_number(str(claim.get("value", "")), entry["found"])
            check = "confirmed" if hit else "differs"
        merged.append({**claim, "check": check, "found": entry.get("found"), "note": entry.get("note")})
    return merged, errors


def _comparison_table(lines: list[str]) -> tuple[int, list[str], list[tuple[int, list[str]]]] | None:
    """Return the header line number, header cells and body rows of the table in section 3."""
    start = next((i for i, line in enumerate(lines) if re.match(r"##\s*3\.", line)), None)
    if start is None:
        return None
    rows: list[tuple[int, list[str]]] = []
    for number in range(start + 1, len(lines)):
        line = lines[number]
        if line.startswith("## "):
            break
        if line.lstrip().startswith("|"):
            rows.append((number + 1, [c.strip() for c in line.strip().strip("|").split("|")]))
        elif rows:
            break
    if len(rows) < 2:
        return None
    (header_line, header), body = rows[0], rows[2:]
    return header_line, [h.lower() for h in header], body


def lint_report(text: str, claims: list[dict], name: str = "report") -> list[str]:
    """Return one error string per report line that the claims do not back."""
    by_id = {str(c.get("id")): c for c in claims}
    errors: list[str] = []
    lines = text.splitlines()
    for number, line in enumerate(lines, 1):
        for cited in TAG_RE.findall(line):
            claim = by_id.get(cited)
            if claim is None:
                errors.append(f"{name}:{number}: [{cited}] names no claim in the ledger")
            elif claim.get("check") != "confirmed" and UNCONFIRMED not in line.lower():
                errors.append(f"{name}:{number}: [{cited}] is {claim.get('check')!r}; say unconfirmed on this line")
    table = _comparison_table(lines)
    if table is None:
        return errors + [f"{name}: section 3 has no comparison table"]
    header_line, header, body = table
    if "value" not in header or "claim" not in header:
        return errors + [f"{name}:{header_line}: the comparison table needs a Value and a Claim column"]
    value_at, claim_at = header.index("value"), header.index("claim")
    for number, cells in body:
        if len(cells) != len(header):
            errors.append(f"{name}:{number}: row has {len(cells)} cells, the header has {len(header)}")
            continue
        # Unknown and unconfirmed tags are reported line by line above; here the row's number
        # must be the value of one of the claims it names.
        value, cited = cells[value_at], TAG_RE.findall(cells[claim_at])
        if not re.search(r"\d", value):
            continue
        backing = [by_id[c] for c in cited if c in by_id]
        if not cited:
            errors.append(f"{name}:{number}: value {value!r} names no claim tag like [rf-detr-3]")
        elif backing and not any(_has_number(str(c.get("value", "")), value) for c in backing):
            errors.append(f"{name}:{number}: value {value!r} is not the value of {', '.join(cited)}")
    return errors


def _strict_object(pairs: list[tuple[str, object]]) -> dict:
    keys = [key for key, _ in pairs]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        raise ValueError(f"duplicate key {duplicates[0]!r}")
    return dict(pairs)


def _no_constant(name: str) -> object:
    raise ValueError(f"{name} is not a JSON number")


def _load(path: Path, key: str) -> list[dict]:
    """Return the list of objects in a JSON file: a bare array, or the array under key."""
    data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_strict_object,
                      parse_constant=_no_constant)
    items = data.get(key) if isinstance(data, dict) else data
    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        raise ValueError(f"expected a JSON array of objects or an object with a {key!r} array")
    return items


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("claims", type=Path)
    parser.add_argument("--blind", type=Path, help="write the ledger the verifier is given")
    parser.add_argument("--checks", type=Path, help="the verifier's checks file")
    parser.add_argument("--report", type=Path, help="the report to check against the ledger")
    try:
        args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    except SystemExit as stop:
        return int(stop.code or 0)
    if args.report is not None and args.checks is None:
        print("--report needs --checks: a report is checked against verified claims", file=sys.stderr)
        return 2
    try:
        claims = _load(args.claims, "claims")
        checks = _load(args.checks, "checks") if args.checks is not None else None
        text = args.report.read_text(encoding="utf-8") if args.report is not None else None
    except (OSError, ValueError) as error:
        print(f"cannot read input: {error}", file=sys.stderr)
        return 1
    errors = lint_claims(claims, args.claims.parent)
    given = claims
    if checks is not None:
        claims, more = merge_checks(claims, checks)
        errors += more
    if text is not None:
        errors += lint_report(text, claims, args.report.name)
    for error in errors:
        print(error, file=sys.stderr)
    saved = sum(1 for claim in claims if not _is_blank(claim.get("source_file")))
    print(f"{len(claims)} claims, {saved} checked against a saved copy of their source")
    if checks is not None:
        counts = {v: sum(1 for c in claims if c.get("check") == v)
                  for v in ("confirmed", "differs", "wrong-paper", "absent", "unreachable")}
        print("verdicts: " + ", ".join(f"{n} {v}" for v, n in counts.items()))
    if errors:
        return 1
    if args.blind is not None:
        args.blind.write_text(json.dumps(blind(given), indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.blind}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
