"""Reject a research claims ledger, the verifier's checks, or a report the evidence does not support.

Usage: lint_research.py CLAIMS.json [--blind OUT.json] [--checks CHECKS.json ...] [--candidate SLUG]
                        [--report REPORT.md]

Every claim needs its common fields, the fields its kind needs, and exactly one source. The
value must appear as a whole number in the quote. A claim with a `source_file` (a saved copy
of the page, relative to the ledger's folder) must have its quote in that file.

--blind writes the ledger without values, quotes or saved copies: what the verifier is given,
so it copies what the source says before it can know what the scout claimed. The verifier
answers in a checks file, one entry per claim: `found` with the text it copied at the locator,
or `wrong-paper`, `absent` or `unreachable` with a note. --checks merges them and sets each
claim's verdict: `confirmed` when the claimed value is in the copied text, `differs` when not.
The copied text is the passage at the locator, at most 800 characters: a whole table would
confirm every number in it. --checks takes one file per verifier and merges them; --candidate
keeps only the claims whose id is `<SLUG>-<n>`, so a verifier can lint its own file; it cannot
be combined with --blind or --report, which need the whole ledger.
--report (which needs --checks) also checks the report: every claim tag names a claim, a claim
that is not `confirmed` is cited only on a line that says "unconfirmed", and every number in
the comparison table under `## Comparison` is the value of a claim its row names. The report is
short by design, so it also needs an `## Overview` with no bullet lines, at most 7 numbered items
under `## Key points`, and at most 400 words outside the table. A report with the old
`## 3.` comparison heading keeps the table and tag checks only. If an `appendix.md` sits next to
the report, its claim tags get the same check (the appendix has no table or length rules).
Every report line outside tables and code is also checked for the AI-writing tells in
shared/prose.md that a regex can see (dashes, "not just X but Y", run-ups, chatbot wrappers,
inflation, unnamed authority); in the appendix these are printed as warnings and do not fail.
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
COMPARISON_RE = re.compile(r"##\s*(?:comparison\b|3\.)", re.IGNORECASE)
BULLET_RE = re.compile(r"\s*(?:[-*+]|\d+[.)])\s")
NUMBERED_RE = re.compile(r"\d+\.\s")
MAX_KEY_POINTS = 7
MAX_WORDS = 400
MAX_FOUND = 800
SKIPPED_TAGS = {"script", "style", "annotation", "annotation-xml"}
# The AI-writing tells of shared/prose.md that a regex can see, as (tell, pattern, what to do instead).
# Kept narrow on purpose: "robust", "key" and "highlight" are CV terms, so they are not here.
PROSE_TELLS = tuple((tell, re.compile(pattern, re.IGNORECASE), fix) for tell, pattern, fix in (
    ("dash", r"—|(?<!\d)–|–(?!\d)|\s--\s", "use a period, comma, colon or parentheses"),
    ("not X but Y", r"\bnot (?:just|only|merely)\b.*\bbut\b|\bkhông (?:chỉ|những)\b.*\bmà còn\b",
     "state the point directly"),
    ("run-up", r"\blet[’']s (?:dive|explore|break|take a look)\b|\bhere[’']s (?:the thing|what you need)\b"
     r"|\bwithout further ado\b|\bhãy cùng\b", "start with the point"),
    ("chatbot", r"\bi hope this helps\b|\blet me know\b|\bgreat question\b|\bwould you like\b|\bwant me to\b"
     r"|\bhy vọng (?:điều|thông tin) này\b", "cut the wrapper"),
    ("about the document", r"\bthis (?:report|document|section)\b|\bbáo cáo này\b", "write about the subject"),
    ("inflation", r"\bgame[- ]changer\b|\bgroundbreaking\b|\brevolutionary\b|\bcutting[- ]edge\b"
     r"|\bparadigm shift\b", "give the number instead"),
    ("AI word", r"\b(?:delve[sd]?|delving|tapestry|testament|pivotal|showcas(?:e|es|ed|ing)"
     r"|underscor(?:e|es|ed|ing)|seamless(?:ly)?|meticulous(?:ly)?|intricate|vibrant|crucial)\b",
     "use the plain word"),
    ("unnamed authority", r"\b(?:experts?|researchers|observers|critics) (?:argue|say|believe|agree|note)\b"
     r"|\bwidely (?:regarded|considered|recogni[sz]ed)\b", "cite the claim tag or cut it"),
    ("knowledge limit", r"\bnot publicly available\b|\bnot widely documented\b|\bas of my\b"
     r"|\bmy (?:knowledge|training)\b|\bbased on (?:the )?available information\b",
     "say what the source does not show, under Not found in appendix.md"),
))
INLINE_CODE_RE = re.compile(r"`[^`]*`")
LINK_TARGET_RE = re.compile(r"\]\([^)]*\)")


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
        elif status == "found" and len(entry["found"]) > MAX_FOUND:
            errors.append(f"{tag}: found is {len(entry['found'])} characters; copy only the row or sentence "
                          f"at the locator, at most {MAX_FOUND}")
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
    """Return the header line number, header cells and body rows of the table under `## Comparison`."""
    start = next((i for i, line in enumerate(lines) if COMPARISON_RE.match(line)), None)
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


def lint_tags(text: str, claims: list[dict], name: str) -> list[str]:
    """Return one error string per claim tag the ledger does not back, or cites without saying unconfirmed."""
    by_id = {str(c.get("id")): c for c in claims}
    errors: list[str] = []
    for number, line in enumerate(text.splitlines(), 1):
        for cited in TAG_RE.findall(line):
            claim = by_id.get(cited)
            if claim is None:
                errors.append(f"{name}:{number}: [{cited}] names no claim in the ledger")
            elif claim.get("check") != "confirmed" and UNCONFIRMED not in line.lower():
                errors.append(f"{name}:{number}: [{cited}] is {claim.get('check')!r}; say unconfirmed on this line")
    return errors


def _section(lines: list[str], heading: str) -> list[str] | None:
    """Return the lines under the `## heading` (case-insensitive) up to the next `## `, or None."""
    start = next((i for i, line in enumerate(lines) if re.match(rf"##\s*{heading}\s*$", line, re.IGNORECASE)), None)
    if start is None:
        return None
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return lines[start + 1:end]


def _lint_shape(lines: list[str], name: str) -> list[str]:
    """Return the errors for a report that is not short: Overview, bullets, key points, length."""
    errors: list[str] = []
    overview = _section(lines, "overview")
    if overview is None:
        errors.append(f"{name}: no ## Overview section")
    elif any(BULLET_RE.match(line) for line in overview):
        errors.append(f"{name}: the Overview has a bullet; write 3 to 6 sentences")
    points = _section(lines, "key points")
    if points is not None:
        count = sum(1 for line in points if NUMBERED_RE.match(line))
        if count > MAX_KEY_POINTS:
            errors.append(f"{name}: Key points has {count} numbered items; at most {MAX_KEY_POINTS}, combine near-duplicates")
    words = sum(len(line.split()) for line in lines if not line.lstrip().startswith("|"))
    if words > MAX_WORDS:
        errors.append(f"{name}: the body has {words} words outside the table; at most {MAX_WORDS}, move detail to appendix.md")
    return errors


def lint_prose(text: str, name: str, label: str = "prose") -> list[str]:
    """Return one string per line and tell of shared/prose.md, outside tables, code blocks and inline code."""
    found: list[str] = []
    fenced = False
    for number, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced or line.lstrip().startswith("|"):
            continue
        prose = LINK_TARGET_RE.sub("]", INLINE_CODE_RE.sub("", line))
        found += [f"{name}:{number}: {label}: {tell}: {fix}" for tell, pattern, fix in PROSE_TELLS
                  if pattern.search(prose)]
    return found


def lint_report(text: str, claims: list[dict], name: str = "report") -> list[str]:
    """Return one error string per report line that the claims do not back, and per rule it breaks."""
    by_id = {str(c.get("id")): c for c in claims}
    lines = text.splitlines()
    errors = lint_tags(text, claims, name) + lint_prose(text, name)
    legacy = not any(re.match(r"##\s*comparison\b", line, re.IGNORECASE) for line in lines)
    if not legacy:
        errors += _lint_shape(lines, name)
    table = _comparison_table(lines)
    if table is None:
        return errors + [f"{name}: no comparison table under ## Comparison"]
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
    parser.add_argument("--checks", type=Path, nargs="+", help="the verifiers' checks files, merged")
    parser.add_argument("--candidate", help="keep only the claims whose id is <candidate>-<n>")
    parser.add_argument("--report", type=Path, help="the report to check against the ledger")
    try:
        args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    except SystemExit as stop:
        return int(stop.code or 0)
    if args.report is not None and args.checks is None:
        print("--report needs --checks: a report is checked against verified claims", file=sys.stderr)
        return 2
    if args.candidate is not None and (args.blind is not None or args.report is not None):
        print("--candidate is for one verifier's own checks; --blind and --report need the whole ledger",
              file=sys.stderr)
        return 2
    try:
        claims = _load(args.claims, "claims")
        checks = [e for path in args.checks for e in _load(path, "checks")] if args.checks is not None else None
        text = args.report.read_text(encoding="utf-8") if args.report is not None else None
        appendix = args.report.with_name("appendix.md") if args.report is not None else None
        appendix_text = appendix.read_text(encoding="utf-8") if appendix is not None and appendix.is_file() else None
    except (OSError, ValueError) as error:
        print(f"cannot read input: {error}", file=sys.stderr)
        return 1
    if args.candidate is not None:
        claims = [c for c in claims if str(c.get("id", "")).rpartition("-")[0] == args.candidate]
        if not claims:
            print(f"no claim of candidate {args.candidate!r} in {args.claims}", file=sys.stderr)
            return 1
    errors = lint_claims(claims, args.claims.parent)
    given = claims
    if checks is not None:
        claims, more = merge_checks(claims, checks)
        errors += more
    if text is not None:
        errors += lint_report(text, claims, args.report.name)
    if appendix_text is not None:
        errors += lint_tags(appendix_text, claims, "appendix.md")
        for warning in lint_prose(appendix_text, "appendix.md", "prose (warning)"):
            print(warning, file=sys.stderr)
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
