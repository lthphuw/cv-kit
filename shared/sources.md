# Sources

Reachability and use of the research sources, from `docs/research/02-deep-research.md` Task B. Probed 2026-10-14 from one residential IP; results can differ elsewhere.

## Tiers

- T1: camera-ready proceedings (CVF, ECVA, accepted OpenReview).
- T2: arXiv paper (latest version) with an official repository.
- T3: Hugging Face model cards and benchmark spaces.
- T4: aggregators, discovery only.
- T5: blogs and social posts, never cited for numbers.

The Tier column below is cv-kit's own assignment using these definitions. Research 02 Task B has a reliability column, not tiers; research 02 line 193 (its T4 row) is where the OpenVLM and MTEB boards being aggregators comes from.

## Sources

| Source | URL | Access | Key needed | Tier | Use for |
|---|---|---|---|---|---|
| arXiv API, abs and HTML | `https://export.arxiv.org/api/query`; `https://arxiv.org/abs/<id>`; `https://arxiv.org/html/<id>` | Works (HTTP 200, Atom). The `http://` URL answers 301 to `https`: follow redirects (`curl -L`). Search is title and abstract only. Pin the version (`v2`): numbers can change between versions. An `id_list` with a version that does not exist answered HTTP 200 with `opensearch:totalResults` 0 and no entry (probed 2026-10-15): read an empty feed as "no such version", and a response that is not a feed as an outage. Documented etiquette (not re-tested): at most 1 request per 3 s, descriptive User-Agent. | No | T2 | Exact id, version, authors, abstract; tables via the HTML page. A preprint is not peer reviewed. |
| Hugging Face Papers JSON | `https://huggingface.co/api/papers/<arxiv_id>`; `https://huggingface.co/api/papers/search?q=`; `https://huggingface.co/api/daily_papers`; `https://huggingface.co/api/arxiv/<id>/repos` | Works (JSON). The HTML trending page showed a limit of 100 page loads per 5 minutes; API limits were not measured. | No (optional `HF_TOKEN` raises quota) | T4 | Linked repos, models, datasets, stars. Upvotes are popularity, not quality; `ai_summary` is machine generated and is never cited. |
| Hugging Face model cards and Hub API | `https://huggingface.co/api/models/<id>` | Used in the model research for ids and licence tags (the `Other (cheap additions)` note in the research file). | No | T3 | Released checkpoints and weight licence. |
| CVF Open Access | `https://openaccess.thecvf.com/menu` | Works (static HTML). `https://openaccess.thecvf.com/CVPR2026?day=all` returned a 12 MB page: download once, grep titles locally. Author search is a POST form, no GET API. | No | T1 | Peer-reviewed camera-ready CVPR, ICCV, WACV papers. Workshop and findings tracks are weaker: label them. |
| ECVA (ECCV) | `https://www.ecva.net/papers.php` | Works (static HTML, 3.6 MB). ECCV is not on CVF. | No | T1 | Peer-reviewed ECCV papers. |
| Semantic Scholar Graph API | `https://api.semanticscholar.org/graph/v1/paper/arXiv:<id>` | Alive but throttled: HTTP 429 on every unauthenticated attempt. Response shape was never seen (UNVERIFIED). Read `S2_API_KEY` (header `x-api-key`), back off on 429, fall back to arXiv and Hugging Face. | Yes (a free key by form) | T4 | Citation counts, references, venue and publication type, to tell whether a preprint was accepted. |
| OpenAlex works API | `https://api.openalex.org/works/doi:<doi>`; `https://api.openalex.org/works?filter=title.search:<words>` | Works without a key (probed 2026-10-15, HTTP 200). Fields seen: `title`, `type` (`preprint`, `conference-paper`, `article`), `doi`, `publication_year`, `locations[].source.display_name` and `.version`, `is_retracted`, `cited_by_count`, `updated_date`. A preprint and its published version are separate records: the arXiv record of RF-DETR listed only arXiv, and the title search for Segment Anything found the ICCV record under its IEEE DOI. The DOI lookup `10.48550/arXiv.2304.02643` (Segment Anything) returned an unrelated record: always compare the returned title with the paper. | No | T4 | Whether a preprint was published, where, and under which DOI; retraction flag. Never the citation for a number. |
| Crossref works API | `https://api.crossref.org/works/<doi>` | Works without a key (probed 2026-10-15). An IEEE DOI (`10.1109/iccv51070.2023.00371`) answered 200 with `title`, `container-title`, `type` `proceedings-article`, `published` and `publisher`; an arXiv DOI answered 404, because arXiv DOIs are not registered with Crossref. Send a contact address in the User-Agent (documented etiquette, not re-tested). | No | T4 | Metadata of a published version once you have its DOI. Not for arXiv preprints. |
| OpenReview | `https://openreview.net/forum?id=<id>` | Blocks plain curl: the API answered 403 `ChallengeRequiredError`; the HTML group page answered 200 (JS shell). Use `openreview-py` (documented, not tested) or a browser; else write "OpenReview not consulted". | No | T1 (accepted papers); reviews and rebuttals for risk claims | Review text, decisions, reviewer concerns. |
| GitHub code search via `gh` | `gh api -X GET search/code -f q='<query>'` | Works with an authenticated `gh`. The code-search limit is 10 requests per minute. Unauthenticated code search is not available (documented). Zero hits can be true: state the query. | Yes (`gh auth`) | T4 | What the code does versus what the paper says; repo health via `gh api repos/<o>/<r>` (stars, pushed_at, licence, archived). Not evidence of accuracy. |
| alphaXiv | `https://api.alphaxiv.org/papers/v3/<arxiv_id>` | Undocumented JSON API; it returned 200 but may break. The `/overview/en` path returned 400. | No | T4 | Convenience reader only. Cite arXiv, never alphaXiv comments or AI overviews. |
| `paperswithcode.co` | `https://paperswithcode.co` | Third-party site, operator not stated, no API documented or found. Benchmark pages exist (for example `/task/object-detection` and `/benchmark/coco-val2017`); the site and those paths were probed by this project on 2026-10-14 and are not covered by research 02, which marks the site UNVERIFIED and not citable. Not corroborated as the original team or Hugging Face. | No | T4 | Discovery only, never cited. |
| Papers with Code (original) | `https://paperswithcode.com` | Shut down: every path, including `/api/v1/`, answers 302 to `https://huggingface.co/papers/trending`. The old REST API and `paperswithcode-client` no longer work. A frozen snapshot of 2025-07-28 is in the Hugging Face org `pwc-archive` (for example the `evaluation-tables` dataset). | No | T4 | Historic leaderboard values (to mid-2025) as candidate hints only. Re-verify every number against the paper; never present as current SOTA. |
| Roboflow100-VL (RF100-VL) | `https://rf100-vl.org/`; github `roboflow/rf100-vl` | Site and repo live. `/leaderboard` returns 404: no leaderboard page exists (a live leaderboard is UNVERIFIED). | No | T2 (paper and repo) | The benchmark definition and loaders. Per-model numbers come from the paper tables, not the website. |
| MTEB / MIEB Space | Hugging Face Space `mteb/leaderboard` | Live (Docker, RUNNING, updated 2026-10-14). Runs through the `mteb` package (documented, not tested). MIEB paper: arXiv 2504.10471. | No | T4 | Choosing an image-embedding backbone (retrieval, linear probe, kNN). Not for detection heads. |
| Open VLM Leaderboard | Hugging Face Space `opencompass/open_vlm_leaderboard`; generator repo `open-compass/VLMEvalKit` | Space runs (last commit 2026-03-11). The data host `opencompass.openxlab.space` had an expired TLS certificate: do not bypass with `-k`. VLMEvalKit repo is live. | No | T4 | VLM and grounding candidates. Cite the paper or VLMEvalKit result file, not a board screenshot. |
| COCO leaderboards | `https://cocodataset.org/` | Stale: the leaderboard page is 404, and the data are 2015 to 2017 challenge entries in static files. CodaLab submissions are winding down. | No | T4 | Dataset facts only (stale; never a SOTA source). Use paper tables for COCO AP. |
| LVIS, ADE20K, ImageNet | `lvisdataset.org`; `ade20k.csail.mit.edu`; `image-net.org` | Sites are alive; no machine-readable live leaderboard found (LVIS content UNVERIFIED because the site is JS-only). | No | T4 | Dataset specifications only. Use paper tables for numbers. |
| Connected Papers, Litmaps | `https://www.connectedpapers.com`; `https://www.litmaps.com` | Homepages answer 200; no public API found (UNVERIFIED that none exists). | Login for free-tier graphs | T4 | Optional human exploration only. Do not automate. |

## Recommended fetch order

1. `curl -L` the arXiv API for candidates and ids; `arxiv.org/html/<id>` for tables.
2. Hugging Face `/api/papers/<id>` and `/api/arxiv/<id>/repos` for code, checkpoints and stars.
3. OpenAlex (title search, then compare the title) for whether and where a preprint was published; Crossref for the published DOI's metadata. Semantic Scholar with `S2_API_KEY` for citations and references; with no key, skip it and say so.
4. CVF and ECVA with local grep for peer-reviewed versions; OpenReview for reviews, if reachable.
5. `gh` for repo health, code reading and issue triage.
6. WebSearch only to fill gaps with blogs and benchmarks, tagged T5.

## When a source fails

- HTTP 429: wait and retry at most three times, slower each time; arXiv no faster than one request per 3 s.
- HTTP 5xx, a timeout or a TLS error: mark the source unreachable for this run and move on. Do not loop, and never bypass TLS with `-k`.
- Never switch to bulk downloads or scraping to get round a limit.
- An unreachable source goes into the report's "not found or not checked" section. It is not evidence that a paper or a number does not exist.

Probed 2026-10-14 (OpenAlex, Crossref and the arXiv empty-feed case on 2026-10-15); re-probe before relying on a row.
