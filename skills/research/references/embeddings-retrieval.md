# Embeddings and retrieval

Read the encoder rows in `${CLAUDE_SKILL_DIR}/../../shared/catalog.md` (sections for contrastive image-text models and self-supervised backbones) before choosing; check each row's Status, Licence and Gotcha columns. A Gotcha starting `(experience)` is a hypothesis to check, not measured fact; keep that label when you repeat it.

## Choose the encoder by the query type
- Text to image, or zero-shot classification by class names: a contrastive image-text model (CLIP, OpenCLIP, SigLIP, SigLIP2).
- Image to image similarity, or features for a linear probe or dense tasks: a self-supervised backbone (DINOv2, DINOv3), then compare with a contrastive model on the user's data.

## Steps
1. **Licence and status.** Check `${CLAUDE_SKILL_DIR}/../../shared/licenses.md` and the row's Licence cell. Drop encoders whose licence conflicts with the stated use, and say which were dropped. Keep UNVERIFIED rows only with the label `UNVERIFIED` and what to check.
2. **Load with the model's own processor** and a pinned revision; do not hand-roll resize or normalisation.
3. **Embed in batches**, L2-normalise, and store the model id and revision next to the vectors, since vectors from different models or revisions are not comparable.
4. **Search exactly first** (cosine similarity on normalised vectors). Move to an approximate index only after measuring that exact search is too slow for the collection size.
5. **Evaluate on the user's data**: build a held-out set of queries with known relevant items, report Recall@k (see `${CLAUDE_SKILL_DIR}/../../shared/metrics.md`), and say which hardware and resolution were used. For a linear probe, split by image group (not by image) to avoid leakage.
6. **Zero-shot classification**: write several prompt templates per class, average their normalised text embeddings, and test the choice of template on a validation split.

State the licence of the chosen encoder next to its name; some releases are gated or non-commercial. Do not quote leaderboard numbers from memory; route to the pipeline in `SKILL.md` for sourced comparisons.
