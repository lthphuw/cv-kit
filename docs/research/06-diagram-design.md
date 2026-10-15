# 06 - diagram-design: what cv-kit took, and from where

Date: 2026-10-15. Input for the `ai-workflow-figure` changes made the same day.
Legend: **VERIFIED** = seen in a file, a build or a render today. **UNVERIFIED** = named in the repository, not checked by us.

## The resource

| Field | Value |
|---|---|
| Repository | https://github.com/cathrynlavery/diagram-design |
| Commit read | `d97c5c7477e54cee17cfa6459190610da0643a05` (2026-10-14), plugin version 2.6.99, 335 commits, 680 files |
| Licence | **MIT**, copyright 2025 Cathryn Lavery (`LICENSE:1-3`). Vendored icons and fonts carry their own licences (`THIRD_PARTY_LICENSES.md`). |
| Stars | 55,511 (`gh api repos/cathrynlavery/diagram-design`, 2026-10-15) |
| What it is | A skill for editorial diagrams (44 types) as self-contained HTML and SVG, with geometry checkers, import from Mermaid, draw.io and Excalidraw, and SVG/PNG export, packaged for several agent hosts. |
| Clone | `/mnt/data2/projects/cv-kit-refs/diagram-design`, outside this repository. Read only; nothing in it was run, installed or built. |

**Licence consequence.** MIT allows reuse with attribution. cv-kit still wrote its own code: diagram-design draws crisp editorial SVG, cv-kit draws hand-drawn rough.js figures, so the rules and checks were adopted, not the files. The adopted checks are attributed in `kit/figure-kit.js` (the connector rules and the label rule), `references/kit.md` and `references/house-style.md` (the delta layout). No vendored icon, font or SVG was copied.

## How it was read

Three research agents with disjoint scopes, each reading its files in full (or saying which it skimmed), comparing them with `ai-workflow-figure`, and citing every fact as `path:line`. Their notes, 1,756 lines in total, are kept outside the repository in `/mnt/data2/projects/cv-kit-refs/notes/`:

| Note | Scope |
|---|---|
| `dd-1-skill-style.md` | `skills/diagram-design/SKILL.md` (394 lines), the style, layout, primitive, profile, doctor and animation references, the architecture-like type references in full, the chart types skimmed, all ADRs and `docs/cookbook.md` |
| `dd-2-checks-ci.md` | `self_check.py`, `export_svg.py`, the `verify-*`, `lint-*` and screenshot scripts with their tests, fixtures, CI and the visual-proof process. It also ran cv-kit's own figure tests (34 passed) and the five templates through cv-kit's kit in memory to test the proposed checks. |
| `dd-3-templates-icons.md` | the HTML templates and about 70 example types, `primitive-icons.md`, the 87 vendored icons and their licences, import and export references, `commands/`, `prompts/`, the host manifests, README and CHANGELOG |

## What cv-kit adopted

| cv-kit change | Files | Idea taken from (diagram-design path:line) |
|---|---|---|
| A **model delta** mode: before, numbered changes, after, all drawn from one parts list so the two sides line up and the ADDED / REMOVED / CHANGED / REWIRED ledger is computed, not typed. Marks are ASCII tags (`+2`, `-4`, `~1`), never dashes, because dashed means training only in cv-kit. Settings that changed without changing a part go in their own card. | `templates/delta.figure.js`, `SKILL.md` mode table, `references/house-style.md` | `skills/diagram-design/references/type-architecture-delta.md:5-21`; `docs/adr/0012-architecture-delta.md` |
| A connector budget per mode, a fixed cut order (repeated blocks to one counted box, internals to one box, side outputs out, then split), the "can I remove it" test for high-level and pipeline figures, a one-message plan naming the cuts, and "Merged:" / "Left out:" lines in the report. The budgets were set from the templates' own counts and are starting values. | `SKILL.md` | `skills/diagram-design/SKILL.md:46`, `:141-143`, `:233-245`, `:269-274`; `skills/diagram-design/references/output-spec.md:187-203`, `:245-257` |
| "Fit the figure to its use": printed size = size x printed width / canvas width, with a worked example, asking for the template's own column width. No venue widths are stated from memory. | `SKILL.md` | `skills/diagram-design/references/output-spec.md:27-55`, `:109-121` |
| Prose rules turned into checks in `finish()`: a label runs into a box it does not sit in; a box crosses another box's edge; a filled panel hides what was drawn before it; a diagonal segment; two lanes under 30 apart (fan-outs and merges exempt); a connector running along a box edge. No template needed changes, and the five existing templates draw byte-identical SVG. | `kit/figure-kit.js`, `references/kit.md`, `SKILL.md` "Common mistakes" | `docs/adr/0005-label-geometry-is-verified.md:19-34` ("a rule that only lives in prose ships broken examples"); `scripts/verify-geometry.py` (lane rules); `scripts/verify-architecture-containment.py` (containment) |
| Every checker rule tested both ways (a spec that must be flagged and a twin that must pass, asserting the exact issue list), a test that every issue message the kit can report has a case, and no silent skip when Chrome is missing in CI. | `tests/test_ai_workflow_figure.py` | the per-checker `test-verify-*.py` files with their `scripts/fixtures/` |
| Golden SVG digests of every template, refreshed with `UPDATE_GOLDEN=1`, which automate the rule that a kit change must leave every template's SVG unchanged; template PNGs uploaded as a CI artifact. diagram-design's committed per-PR screenshots (`.github/pr-visual-proof/`) were judged too heavy. | `tests/golden/figure-svg.json`, `tests/test_ai_workflow_figure.py`, `.github/workflows/validate.yml` | `scripts/verify-screenshot-freshness.py`; `scripts/render-canonical-screenshots.py` |
| Export for papers and slides: `--bare` (no page title), `--scale 1-4`, and `--svg` (a standalone SVG with its font, checked with `xml.etree`); `<title>` and `<desc>` in the SVG. PDF was left out. | `scripts/check_figure.py`, `kit/shell.html`, `SKILL.md`, `references/kit.md` | `skills/diagram-design/references/export.md:21-23`; `skills/diagram-design/scripts/export_svg.py` (diagram-only scope, ElementTree gate) |
| Ten hand-drawn CV icons: camera, video, mask, keypoints, depth, gpu, text, embed, crop, track, appended after the existing ones so old figures keep their strokes. Drawn from scratch: diagram-design's 87 icons cover IT and data platforms and none of them is a CV icon. | `kit/figure-kit.js`, `references/kit.md`, `references/house-style.md`, `templates/icon-sheet.figure.js` | catalogue discipline (name, one-line meaning) `skills/diagram-design/references/primitive-icons.md:13-20` |
| More trigger words in the description: block diagram, docs, paper or slides, exporting, what changed between two versions. | `SKILL.md` description | `docs/adr/0004-skill-md-byte-cap-and-trigger-rich-description.md` |

Proof on 2026-10-15 (VERIFIED): the full test suite passed; the delta template and the icon sheet were built, passed the layout check, and were rendered and looked at; the exported SVG of the delta template parsed as SVG with `title`, `desc` and `style` first.

## Deferred, with the reason

- **A `tensor()` cuboid helper** for C x H x W feature maps (`scripts/axonometry.py:1-8`): it changes the kit and needs its own bounding-box registration.
- **Redraw from a Mermaid or draw.io file**: the source would give topology only, and every fact must still be read from code; a safe decoder needs the guards diagram-design uses (size caps, no DOCTYPE or ENTITY, bounded decompression; `skills/diagram-design/references/import-mermaid.md:5`).
- **Registering icon and mark bounds** for the layout check, a WCAG contrast test of the kit palette, a check that `kit.md` lists every helper, a network block during the check (`--host-resolver-rules`, `scripts/lint-render.py`), a Python 3.10 CI job, and a pinned CLI version in CI.

## Not adopted

A dark theme (hand-drawn wobble "reads as artifact on dark backgrounds", `skills/diagram-design/references/primitive-sketchy.md:43`), results charts (rough strokes misplace values, and chart values come from logs, not code; `skills/diagram-design/references/primitive-sketchy.md:41`), a sequence mode (its dashed return arrows clash with cv-kit's training-only meaning), brand onboarding and profiles (cv-kit's colours encode kind), editorial fonts and the Google Fonts dependency (cv-kit builds offline), animation, the doctor reference, vendored or brand icons, copied dark/full/terminal template variants, `commands/` and Pi prompts (thin wrappers that have already drifted, for example there is no `prompts/import-drawio.md`), and the multi-host manifests (a stated non-goal of cv-kit).

## External resources the repository cites

Named as written in diagram-design; not opened for this note (UNVERIFIED) unless a row says otherwise.

| Resource | Licence as written | As written | Cited at |
|---|---|---|---|
| WCAG 2.x contrast ratio; WCAG 1.4.11 non-text contrast | — | no URL | `scripts/verify-contrast.py:7`; `scripts/verify-dumbbell.py:20` |
| C4 model (context, container, component) | — | no URL | `docs/adr/0007-new-layout-grammars.md:49` |
| Tabler Icons | MIT | `https://github.com/tabler/tabler-icons` | `THIRD_PARTY_LICENSES.md:5-11` |
| Simple Icons | CC0 1.0 | `https://github.com/simple-icons/simple-icons` | `THIRD_PARTY_LICENSES.md:13-19` |
| log-z/logos; Devicon | MIT | `https://github.com/log-z/logos`; `https://github.com/devicons/devicon` | `THIRD_PARTY_LICENSES.md:21-35` |
| Hop, Pentaho, Dagster logos; Stata icon | not stated ("verify license before use") | URLs in `scripts/build-icons.py:147-165` | `skills/diagram-design/references/primitive-icons.md:639-657` |
| Instrument Serif | SIL OFL 1.1 | `https://github.com/Instrument/instrument-serif` | `THIRD_PARTY_LICENSES.md:37-43` |
| Playwright with Chromium | not stated | `pip install playwright && playwright install chromium` | `scripts/lint-render.py:77-80` |
| Edward Tufte, *The Visual Display of Quantitative Information* | — | book | `skills/diagram-design/references/type-line.md:49` |
| IDEF0 (FIPS PUB 183), SysML block definition diagrams | — | named, then rejected | `docs/adr/0010-block-registry-metadata-contract.md:9`, `:31` |
| Keep a Changelog; Semantic Versioning | — | `https://keepachangelog.com/en/1.1.0/`; `https://semver.org/spec/v2.0.0.html` | `CHANGELOG.md:3` |

## Content that read like instructions

Treated as data and not followed: the adversarial import fixtures contain "IGNORE ALL PREVIOUS INSTRUCTIONS" on purpose, to test the importers (`scripts/fixtures/sample-adversarial.mmd:5`, `scripts/fixtures/sample-adversarial.excalidraw:45`); `.maintainer-policy.json:136-164` reads as operating rules for an automated maintainer agent; the command and prompt files are addressed to an agent. The repository also has two ADRs numbered 0015, and its own licence file omits 8 of the 22 Simple Icons it vendors.
