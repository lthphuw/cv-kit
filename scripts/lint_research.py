"""Reject a research claims ledger that has missing fields or numbers absent from their quote."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

FIELDS = ("id", "value", "metric", "dataset", "split", "resolution", "hardware", "arxiv", "locator", "quote", "label")
ARXIV_RE = re.compile(r"^\d{4}\.\d{4,5}v\d+$")
LABELS = {"reported", "reproduced", "unverified"}


def _is_blank(value: object) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def lint_claims(claims: list[dict]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, claim in enumerate(claims):
        tag = str(claim.get("id") or f"#{index}")
        for field in FIELDS:
            if _is_blank(claim.get(field)):
                errors.append(f"{tag}: missing {field}")
        if tag in seen:
            errors.append(f"{tag}: duplicate id")
        seen.add(tag)
        if claim.get("arxiv") and not ARXIV_RE.match(str(claim["arxiv"])):
            errors.append(f"{tag}: arxiv {claim['arxiv']!r} must look like 2511.09554v2 (id plus version)")
        if claim.get("label") and claim["label"] not in LABELS:
            errors.append(f"{tag}: label {claim['label']!r} must be one of {sorted(LABELS)}")
        value = claim.get("value")
        if not _is_blank(value):
            if not isinstance(value, str):
                errors.append(f"{tag}: value must be a string copied from the quote")
            # The value must be a whole number in the quote: no digit or dot before it, and no digit
            # or fraction after it. So "7" and "4.7" do not match "54.7", while a sentence-final
            # period ("54.7. AP") and "(54.7)" or "54.7%" still match.
            elif claim.get("quote") and not re.search(
                r"(?<![\d.])" + re.escape(value.strip()) + r"(?!\d|\.\d)", str(claim["quote"])
            ):
                errors.append(f"{tag}: value {value!r} does not appear as a whole number in its quote")
    return errors


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: lint_research.py claims.json", file=sys.stderr)
        return 2
    try:
        data = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(f"cannot read {args[0]}: {error}", file=sys.stderr)
        return 1
    claims = data.get("claims") if isinstance(data, dict) else data
    if not isinstance(claims, list) or not all(isinstance(claim, dict) for claim in claims):
        print(f"{args[0]}: expected a JSON array of claim objects or an object with a 'claims' array", file=sys.stderr)
        return 1
    errors = lint_claims(claims)
    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
