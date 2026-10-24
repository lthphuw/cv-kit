#!/usr/bin/env python3
"""Fetch the optional Stay With Me font into the user font cache, once.

Stay With Me is free for personal use only; commercial or promotional use needs a licence
from its author, and its terms are saved beside the font. The file goes to the cache
(~/.cache/ai-workflow-figure/fonts), never into the plugin or a repository. Patrick Hand,
the default font, is bundled and needs no fetch. A font that is already there with its
terms is kept, so re-running is safe.
"""

import io
import sys
import urllib.request
import zipfile

from build_figure import FONT_CACHE, KNOWN_FONTS

STAY_WITH_ME_ARCHIVE = "https://dl.dafont.com/dl/?f=stay_with_me"
STAY_WITH_ME_OTF = KNOWN_FONTS["stay-with-me"].path
STAY_WITH_ME_TERMS = FONT_CACHE / "StayWithMe-terms.txt"
OTF_MAGIC = b"OTTO"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) ai-workflow-figure"


def get(url: str) -> bytes:
    """Return the response body at url."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def fetch_stay_with_me() -> None:
    """Read the OTF and its terms out of the dafont archive, in memory, into the cache."""
    try:
        archive = zipfile.ZipFile(io.BytesIO(get(STAY_WITH_ME_ARCHIVE)))
    except zipfile.BadZipFile as error:
        raise SystemExit(f"{STAY_WITH_ME_ARCHIVE!r} did not return a zip archive") from error
    names = archive.namelist()
    otf_name = next((n for n in names if n.lower().endswith(".otf")), None)
    terms_name = next((n for n in names if "terms" in n.lower() and n.lower().endswith(".txt")), None)
    if otf_name is None or terms_name is None:
        sys.exit(f"unexpected archive contents from {STAY_WITH_ME_ARCHIVE!r}: {names}")
    font_bytes = archive.read(otf_name)
    if not font_bytes.startswith(OTF_MAGIC):
        sys.exit(f"{otf_name!r} in the archive is not an OpenType font")
    FONT_CACHE.mkdir(parents=True, exist_ok=True)
    # The terms first, and the font through a rename: a font in the cache always has its
    # terms beside it, and a failed write never leaves a truncated font that looks fetched.
    STAY_WITH_ME_TERMS.write_bytes(archive.read(terms_name))
    partial = STAY_WITH_ME_OTF.with_suffix(".part")
    partial.write_bytes(font_bytes)
    partial.replace(STAY_WITH_ME_OTF)


def main() -> None:
    """Download Stay With Me unless the cache already holds it and its terms."""
    if not (STAY_WITH_ME_OTF.exists() and STAY_WITH_ME_TERMS.exists()):
        fetch_stay_with_me()
    print("ready:", STAY_WITH_ME_OTF)
    print("Stay With Me is free for personal use only; commercial use needs a licence.")


if __name__ == "__main__":
    main()
