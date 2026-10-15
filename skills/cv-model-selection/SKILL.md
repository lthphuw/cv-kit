---
name: cv-model-selection
description: Use when choosing a detector, segmenter, keypoint model, image encoder or VLM for a stated task, budget and licence, or when asked which model to start from.
---

# Choose a model

Read `${CLAUDE_SKILL_DIR}/../../shared/catalog.md` and `${CLAUDE_SKILL_DIR}/../../shared/licenses.md`.

1. **Collect constraints.** Task (detection, segmentation, keypoints, embeddings, captioning), number of classes and whether classes are fixed or open-vocabulary, training images available, target hardware and latency, precision, and whether the product is commercial. Ask one question at a time for anything missing.
2. **Filter by licence first.** Drop catalog rows whose licence conflicts with the stated use. Say which rows were dropped and why.
3. **Shortlist at most three** from the remaining rows. For each give: model, task, repository or Hugging Face id, licence, the catalog's gotcha, and its Status.
4. **Say what to measure.** Name the metric (see `${CLAUDE_SKILL_DIR}/../../shared/metrics.md`) and a protocol on the user's own validation split, with hardware and resolution fixed. Do not quote benchmark numbers from memory.
5. **Gaps.** If the catalog has no suitable row, or a needed row is `UNVERIFIED`, say so and offer `cv-deep-research` to source it.

Never recommend a model whose licence you have not read; write `licence UNVERIFIED` and say what to check.
