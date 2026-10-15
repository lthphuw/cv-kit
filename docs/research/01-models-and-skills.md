# cv-kit research 01: reference skill, model catalog, skill breakdown

Date of research: 2026-10-14. Sources: GitHub API (`gh api`), raw.githubusercontent.com, Hugging Face Hub API (`/api/models/<id>`, tags give license + arXiv), arXiv API (titles of every arXiv id below were fetched and matched to the model; none are guessed).

Legend: **V** = verified this session against the live source named. **UNVERIFIED** = not confirmed this session (comes from prior knowledge or could not be fetched). "Gotcha (exp.)" = engineering knowledge I did not test or confirm against a doc in this session; treat it as a hypothesis to check before writing it into a skill.

---

## Task A. Reference skill: `senior-computer-vision` (davila7/claude-code-templates)

Path: `cli-tool/components/skills/development/senior-computer-vision`. Downloaded to `.../scratchpad/ref-skill/` (read only, nothing executed).

Structure (7 files, listed with `gh api git/trees`):

| File | Size | What it is |
|---|---|---|
| `SKILL.md` | 5593 B, 226 lines | Frontmatter + generic "senior engineer" prose |
| `references/computer_vision_architectures.md` | 1447 B | Placeholder |
| `references/object_detection_optimization.md` | 1447 B | Placeholder |
| `references/production_vision_systems.md` | 1439 B | Placeholder |
| `scripts/vision_model_trainer.py` | 2817 B | Stub |
| `scripts/inference_optimizer.py` | 2794 B | Stub |
| `scripts/dataset_pipeline_builder.py` | 2797 B | Stub |

Findings (V, by reading and diffing the files):

- The frontmatter description names "PyTorch, OpenCV, YOLO, SAM, diffusion models, vision transformers, 3D vision, video analysis", but the body has **no CV content at all**. No model names, no code, no dataset/metric/export guidance. The words CLIP, SigLIP, DINO, VLM do not occur anywhere in the folder (grep).
- Body is templated boilerplate shared with other "senior-*" skills: generic Tech Stack (Spark, Airflow, dbt, Kafka, Snowflake, Pinecone, LangChain), "Performance Targets" (P50 < 50 ms, 1000 rps, 99.9% uptime), "Security & Compliance" bullets, "Team Leadership".
- The three reference files are the same template with the title swapped (diff of `production_vision_systems.md` vs `object_detection_optimization.md` differs only in the H1 and one line). They contain headings like "Pattern 1: Distributed Processing" with no body.
- The three scripts are the same 90-line class skeleton (argparse, `validate_config()` that only logs "validated", `_execute()` returning `{'success': True}`). Only the class name/description differ. They do nothing, and SKILL.md advertises them as "Core Tool 1/2/3" (`--deploy`, `--analyze`), which would mislead an agent.

Conclusion for cv-kit: do not model structure on its content. What is worth keeping is only the layout convention (SKILL.md + `references/` + `scripts/`). The user's complaint (no VLM / foundation-model coverage) is understated: it has no model coverage of any kind, including detectors. Avoid its failure modes: (1) description that promises topics the body lacks, (2) stub scripts presented as tools, (3) duplicated reference files, (4) generic enterprise filler that costs context and teaches nothing.

---

## Task B. Gap analysis

Dimensions an experienced CV engineer needs vs. what the reference skill gives:

| Area | Reference skill | Gap |
|---|---|---|
| Closed-set detection (RF-DETR, RT-DETR, D-FINE, DEIM, YOLO) | name-drops "YOLO" | full: selection by license/latency, finetune recipe, COCO-format data, NMS-free vs NMS export differences |
| Instance/semantic/panoptic segmentation | name-drops SAM | full |
| Keypoints / pose | none | full |
| Tracking | none | full (tracker choice, ID switches, MOT metrics) |
| OCR / documents | none | full |
| Depth / 3D | "3D vision" word only | full (relative vs metric depth, licence traps) |
| Image-text embeddings (CLIP, OpenCLIP, EVA-CLIP, SigLIP, SigLIP2, MobileCLIP, PE) | none | full: zero-shot classification, retrieval, linear probe, text-prompt pitfalls |
| Self-supervised features (DINOv2/v3, TIPS) | none | full: kNN/linear probe, dense features, dedup/clustering, backbone for finetune |
| Promptable segmentation (SAM 1/2/3/3.1, EdgeTAM, MobileSAM) | none | full: box/point/text prompts, video propagation, auto-label |
| Open-vocabulary detection (Grounding DINO, MM-Grounding-DINO, OWL-ViT/OWLv2, YOLO-World, YOLOE, LLMDet) | none | full: auto-labeling and zero-shot baseline |
| Generative VLMs (Florence-2, PaliGemma/2, Qwen2.5/3-VL, Qwen3.5+, InternVL3/3.5, LLaVA-OneVision, Gemma 4, SmolVLM, Moondream) | none | full: when a VLM beats a detector, grounding output formats, finetune/quantise, hallucination eval |
| Dataset/labeling workflow (COCO/YOLO formats, split leakage, label QA, auto-label with foundation models, active learning) | stub script | full |
| Evaluation (COCO mAP pitfalls, per-class AP, confusion, small-object, calibration, VLM eval, retrieval recall@k) | none | full |
| Export/deploy (ONNX, TensorRT, OpenVINO, CoreML, LiteRT, INT8, latency benchmarking) | generic "Docker/K8s" | full |
| Licence triage (AGPL/GPL/NC/custom Meta licences) | "Security & compliance" bullets | full: this decides model choice in practice |

Things that changed since typical training cutoffs and which a skill must not get wrong (V = verified on HF/GitHub this session):

- **SAM 3 / SAM 3.1** exist (arXiv 2511.16719; HF `facebook/sam3` 2025-11-20, `facebook/sam3.1` 2026-03-26; gated, custom "SAM License"). Concept (text/exemplar) prompts, not only points/boxes. Transformers has `sam3`, `sam3_tracker`, `sam3_video`.
- **DINOv3** (2508.10104) is gated + custom licence; **Depth Anything 3** (2511.10647) exists with Apache-2.0 for the main checkpoints; **SigLIP 2** (2502.14786) is the current Google SigLIP (no SigLIP 3 found on the hub, UNVERIFIED that none exists elsewhere).
- **Qwen line moved on**: Qwen3-VL (Oct 2025, 2511.21631); Qwen3-VL-Embedding/Reranker (2601.04720, Jan 2026); then Qwen3.5 / 3.6 / 3.8 on the Hub (Mar-Aug 2026), which are natively `image-text-to-text` (Qwen3.8-27B card: "Causal Language Model with Vision Encoder"). No separate "Qwen3.5-VL" repo exists (`Qwen/Qwen3.5-VL-7B` NOT FOUND). No tech-report arXiv id found for 3.5/3.6/3.8 (UNVERIFIED).
- **Gemma 4** (arXiv 2607.02770, Apache-2.0 on the 31B and E4B cards, multimodal) supersedes the Gemma-licensed PaliGemma line for general VLM use; no PaliGemma 3 found in this session (UNVERIFIED).
- **YOLO26** exists: `Ultralytics/YOLO26` on HF (AGPL-3.0), arXiv 2606.03748 "Ultralytics YOLO26". YOLO12 (2502.12524) and YOLO11 exist; YOLO11 has no arXiv paper (HF card has no arxiv tag).
- **RF-DETR** is at repo release 1.11.2 (2026-10-04); official weights are now on the HF org `Roboflow/` (e.g. `Roboflow/rf-detr-nano`, `-small`, `-base`, `rf-detr-seg-*`), Apache-2.0, and RF-DETR, D-FINE, DEIMv2, LW-DETR, RT-DETR(v2) are all natively in Transformers (`rf_detr.md`, `d_fine.md`, `deimv2.md`, `lw_detr.md`, `rt_detr*.md` in the docs tree).
- Newer encoders seen on the Hub that a catalog may want to mention as "watch": `google/tipsv1-*` (TIPS, 2410.16512, Apache-2.0), `facebook/MoEViE-*` (2608.17402, CC-BY-NC-4.0), `facebook/meta-encoder` (2610.11316, gated, 2026-10-13). Only TIPS was fully checked (card read). Do not put the others in a skill without a use-case.

---

## Model catalog

All "HF id" cells were fetched from `https://huggingface.co/api/models/<id>` unless marked. "Licence" is the HF tag (weights) and, where different, the GitHub repo licence (code). arXiv ids were matched to titles via the arXiv API.

### 1. Image-text embedding (contrastive)

| Model | Task | arXiv | Repo / HF id | Licence | Typical use | Gotcha |
|---|---|---|---|---|---|---|
| CLIP | image-text embedding | 2103.00020 CLIP (V) | github `openai/CLIP` (MIT, V); HF `openai/clip-vit-large-patch14`, `openai/clip-vit-base-patch32` (no licence tag on HF, V) | MIT code; weights: HF tag empty | zero-shot classify, retrieval, linear probe | 77-token text limit; zero-shot accuracy is highly prompt-template dependent ("a photo of a {}"); softmax over given labels cannot say "none of these" |
| OpenCLIP | open reproduction + model zoo | 2212.07143 scaling laws (V); 1910.04867 (VTAB, listed on HF tags, UNVERIFIED as the citation to use) | github `mlfoundations/open_clip` (MIT text, GitHub says NOASSERTION); HF `laion/CLIP-ViT-H-14-laion2B-s32B-b79K`, `laion/CLIP-ViT-bigG-14-laion2B-39B-b160k` (MIT, V) | MIT | embeddings for retrieval / dedup, linear probe | Per-checkpoint weight licence differs (e.g. MobileCLIP2 weights are `apple-amlr`); LAION-trained checkpoints inherit dataset caveats |
| EVA-CLIP | stronger CLIP | 2303.15389 EVA-CLIP (V); 2402.04252 EVA-CLIP-18B (V) | github `baaivision/EVA` (MIT, last push 2024-08, V); HF `BAAI/EVA-CLIP-8B` (apache-2.0, V), `timm/eva02_large_patch14_clip_224.merged2b_s4b_b131k` (MIT, V) | MIT / Apache-2.0 | strong zero-shot, embeddings | 8B/18B variants are heavy; the `-8B` HF card cites the 18B paper id (V: tag shows 2402.04252) |
| MetaCLIP | data-curated CLIP | 2309.16671 Demystifying CLIP Data (V) | HF `facebook/metaclip-b32-400m` | **cc-by-nc-4.0** (V) | research baseline | non-commercial weights; MetaCLIP 2 is in Transformers docs (`metaclip_2.md`, V) but I did not check its paper/licence (UNVERIFIED) |
| SigLIP | sigmoid-loss CLIP | 2303.15343 (V) | big_vision `google-research/big_vision` (Apache-2.0, V); HF `google/siglip-so400m-patch14-384` (apache-2.0, V) | Apache-2.0 | zero-shot, retrieval, vision tower of many VLMs | Pairwise sigmoid: scores are independent probabilities, not a softmax over labels; text must be padded to fixed `max_length` (exp., check model card) |
| SigLIP 2 | multilingual, dense-aware encoder | 2502.14786 (V) | HF `google/siglip2-so400m-patch14-384`, `google/siglip2-base-patch16-224`, `google/siglip2-giant-opt-patch16-384`, `google/siglip2-so400m-patch16-naflex` (all apache-2.0, V); Transformers `siglip2.md` (V) | Apache-2.0 | default pick for zero-shot/retrieval/embeddings; NaFlex variant for variable aspect ratio | NaFlex needs the NaFlex processor/mask path, not the fixed-res one (exp.); `-jax` checkpoints are JAX-only |
| Perception Encoder (PE-Core) | CLIP-style, also video | 2504.13181 (V) | github `facebookresearch/perception_models` (Apache-2.0, V); HF `facebook/PE-Core-L14-336` (apache-2.0, V) | Apache-2.0 | SigLIP2 alternative; strong intermediate-layer features | Best features are in intermediate layers, not the output (title of paper, V) |
| MobileCLIP / MobileCLIP2 | on-device CLIP | 2311.17049 (HF tag), 2508.20691 MobileCLIP2 (V) | github `apple-aiml-research/ml-mobileclip`; HF `apple/MobileCLIP2-S0`, `timm/MobileCLIP2-S4-OpenCLIP` | **apple-amlr** (V; custom Apple research licence) | edge/mobile retrieval | licence is not OSI; read before shipping commercially |
| TIPS | spatially-aware image-text | 2410.16512 (V) | HF `google/tipsv1-so400m14` etc. (apache-2.0, V; card read) | Apache-2.0 | dense/zero-shot segmentation features | needs `trust_remote_code=True` per card (V) |

### 2. Self-supervised vision backbones

| Model | Task | arXiv | Repo / HF id | Licence | Typical use | Gotcha |
|---|---|---|---|---|---|---|
| DINOv2 | SSL features | 2304.07193 (V) | github `facebookresearch/dinov2` (Apache-2.0, V); HF `facebook/dinov2-small/base` (apache-2.0, V), `facebook/dinov2-with-registers-base` (arXiv 2309.16588 registers, V tag) | Apache-2.0 | kNN / linear probe, dedup, dense features, detector backbone (RF-DETR uses it, README) | patch size 14, so input size should be a multiple of 14; non-register models show artefact high-norm patch tokens in dense maps |
| DINOv3 | SSL features, sat variants, 7B | 2508.10104 (V) | github `facebookresearch/dinov3`; HF `facebook/dinov3-vitb16-pretrain-lvd1689m`, `facebook/dinov3-convnext-base-pretrain-lvd1689m`, `facebook/dinov3-vitl16-pretrain-sat493m` (V); ungated mirror `timm/vit_small_patch16_dinov3.lvd1689m` (V) | **custom "DINOv3 License"** (V: royalty-free limited grant + trade-control clauses; I did not parse remaining restrictions, UNVERIFIED for commercial suitability); HF gated=manual | linear probe, dense tasks, satellite (`sat493m`), backbone of DEIMv2/EoMT-DINOv3 | gated download needs HF login + approval; patch size 16 (not 14); `lvd1689m` vs `sat493m` weights are not interchangeable by domain |

### 3. Promptable and concept segmentation

| Model | Task | arXiv | Repo / HF id | Licence | Typical use | Gotcha |
|---|---|---|---|---|---|---|
| SAM | promptable mask | 2304.02643 (V) | github `facebookresearch/segment-anything` (Apache-2.0, last push 2024-09, V); HF `facebook/sam-vit-base`, `facebook/sam-vit-huge` (apache-2.0, V) | Apache-2.0 | box/point prompts, auto-label | image-only; masks are class-agnostic, so you still need a detector or labels for class identity |
| SAM 2 / 2.1 | image + video | 2408.00714 (V) | github `facebookresearch/sam2` (Apache-2.0, V); HF `facebook/sam2.1-hiera-large` (apache-2.0, V) | Apache-2.0 | video object propagation, auto-label sequences | prefer the `sam2.1` checkpoints over `sam2`; memory grows with video length unless frames are offloaded (exp.) |
| SAM 3 / 3.1 | concept-prompted segmentation + tracking (text, exemplar) | 2511.16719 "SAM 3: Segment Anything with Concepts" (V) | github `facebookresearch/sam3` (11.9k stars, V); HF `facebook/sam3`, `facebook/sam3.1` (gated=manual, V); Transformers `sam3*.md` (V) | **custom "SAM License"** (V: royalty-free limited grant; remaining terms not fully parsed, UNVERIFIED for commercial) | open-vocabulary instance seg by text/exemplar, auto-label, video tracking | gated access; ~850M params per RF-DETR README (cited there, not re-measured); SAM 3.1 changes not read (UNVERIFIED) |
| Efficient SAMs | edge/real-time | MobileSAM 2306.14289, EfficientSAM 2312.00863, EdgeTAM 2501.07256, SAM-HQ 2306.01567 (all V titles) | `ChaoningZhang/MobileSAM` (Apache-2.0), `yformer/EfficientSAM` (Apache-2.0), HF `facebook/EdgeTAM` / `yonigozlan/EdgeTAM-hf` (apache-2.0, V) | Apache-2.0 | on-device interactive seg | SAM-HQ repo/HF licence not checked (UNVERIFIED); MobileSAM HF id not found as `ChaoningZhang/MobileSAM` (NOT FOUND on HF) |
| Grounded-SAM(-2) | pipeline: GDINO + SAM | 2401.14159 (V) | github `IDEA-Research/Grounded-SAM-2` (Apache-2.0, last push 2025-11, V) | Apache-2.0 | classic auto-label recipe; being superseded by SAM 3 for text prompts | pipeline is two models, two failure modes (box recall then mask quality) |
| Universal seg | semantic/instance/panoptic | Mask2Former 2112.01527, OneFormer 2211.06220, SegFormer 2105.15203 (all V) | HF `facebook/mask2former-swin-large-coco-panoptic` (licence `other`, V), `shi-labs/oneformer_coco_swin_large` (MIT, V), `nvidia/segformer-b5-finetuned-ade-640-640` (licence `other`, V); repos: Mask2Former MIT but **archived** (V), SegFormer "NVIDIA Source Code License" (V) | mixed; check per checkpoint | closed-set semantic/panoptic finetune | Mask2Former repo archived; use the Transformers port; SegFormer licence is NVIDIA's non-OSI one |
| RF-DETR-Seg | real-time instance seg | 2511.09554 (V) | HF `Roboflow/rf-detr-seg-nano ... -xxlarge` (apache-2.0 for the two checked: small, xxlarge, V) | Apache-2.0 here; this repo's AGENTS.md says XLarge/2XLarge plus models need `rfdetr_plus` under PML 1.0, which conflicts with the HF tag on `seg-xxlarge` (UNRESOLVED, check before documenting) | finetune on own data | conflicting licence signals for the largest sizes |

### 4. Detectors (closed-set)

| Model | arXiv | Repo / HF id | Licence | Typical use | Gotcha |
|---|---|---|---|---|---|
| RF-DETR | 2511.09554 (V) | github `roboflow/rf-detr` (Apache-2.0, release 1.11.2 on 2026-10-04, V); HF `Roboflow/rf-detr-nano/small/base` (apache-2.0, V); local repo `src/rfdetr/variants.py` | Apache-2.0 (plus models: PML 1.0 per this repo's AGENTS.md, not re-verified) | finetune on COCO-format data, real-time deploy | DINOv2-register backbone is fixed-resolution friendly; resolution must be a multiple of the model's patch/window size (exp.); `RFDETRBase` is deprecated by this repo's own conventions |
| RT-DETR / RT-DETRv2 | 2304.08069, 2407.17140 (V) | github `lyuwenyu/RT-DETR` (Apache-2.0, V); HF `PekingU/rtdetr_r50vd`, `PekingU/rtdetr_v2_r50vd` (apache-2.0, V) | Apache-2.0 | NMS-free real-time baseline | Original code is PaddlePaddle; the PyTorch port is the practical route; v4 exists (2510.25257, V title) but repo/weights not checked (UNVERIFIED) |
| D-FINE | 2410.13842 (V) | github `Peterande/D-FINE` (Apache-2.0, V); HF `ustc-community/dfine-small-coco`, `dfine-xlarge-coco` (apache-2.0, V) | Apache-2.0 | high-AP real-time | distribution-based box regression; ONNX export needs a check of the integral head (exp.) |
| DEIM / DEIMv2 | 2412.04234 DEIM (V), 2509.20787 DEIMv2 "Real-Time Object Detection Meets DINOv3" (V) | github `Intellindust-AI-Lab/DEIM` (LICENSE file text says Apache; GitHub shows NOASSERTION, V), `.../DEIMv2` (**LICENSE.md: non-commercial only, commercial use needs separate licence**, V); Transformers `deimv2.md` (V); HF weights id NOT FOUND for the guesses `Intellindust/DEIM*` (UNVERIFIED) | DEIM Apache (per file); **DEIMv2 non-commercial** | research / benchmark | DEIMv2 licence blocks commercial deployment; the Transformers port does not change that (UNVERIFIED legal reading) |
| LW-DETR | 2406.03459 (V) | github `Atten4Vis/LW-DETR` (Apache-2.0, V); Transformers `lw_detr.md` (V) | Apache-2.0 | light real-time baseline, ancestor of RF-DETR (README, V) | HF weight ids not checked (UNVERIFIED) |
| YOLOv10 | 2405.14458 (V) | github `THU-MIG/yolov10` (AGPL-3.0, last push 2025-03, V); HF `jameslahm/yolov10n` (agpl-3.0, V) | AGPL-3.0 | NMS-free YOLO | AGPL reaches network use |
| YOLOv12 | 2502.12524 (V) | github `sunsmarterjie/yolov12` (AGPL-3.0, V) | AGPL-3.0 | attention-centric YOLO | training instability/memory notes in community: UNVERIFIED |
| YOLO11 | no paper (HF card has no arxiv tag, V) | github `ultralytics/ultralytics` (AGPL-3.0, V); HF `Ultralytics/YOLO11` (agpl-3.0, V) | AGPL-3.0 (enterprise licence exists, UNVERIFIED terms) | default YOLO toolchain | AGPL for model, code and often derived apps |
| YOLO26 | 2606.03748 "Ultralytics YOLO26" (V) | HF `Ultralytics/YOLO26` (agpl-3.0, created 2026-01-26, V) | AGPL-3.0 | newest Ultralytics line | release notes/architecture not read; claims about NMS-free/edge features UNVERIFIED |
| YOLOv9 | 2402.13616 (V) | repo not checked | UNVERIFIED | | |

### 5. Open-vocabulary detection / grounding

| Model | arXiv | Repo / HF id | Licence | Typical use | Gotcha |
|---|---|---|---|---|---|
| Grounding DINO | 2303.05499 (V) | github `IDEA-Research/GroundingDINO` (Apache-2.0, last push 2024-08, V); HF `IDEA-Research/grounding-dino-base`, `-tiny` (apache-2.0, V); Transformers `grounding-dino.md` (V) | Apache-2.0 | zero-shot detect from text, auto-label | text prompt format and the box/text thresholds change recall a lot (exp.: lowercase, period-separated phrases) |
| MM-Grounding-DINO | 2401.02361 (V) | HF `openmmlab-community/mm_grounding_dino_base_all` etc. (V exists; licence not read, UNVERIFIED); Transformers `mm-grounding-dino.md` (V) | UNVERIFIED | stronger open GDINO reproduction | checkpoint names encode the training data mix; choose deliberately |
| OWL-ViT / OWLv2 | 2205.06230, 2306.09683 (V) | HF `google/owlvit-base-patch32`, `google/owlv2-base-patch16-ensemble` (apache-2.0, V); Transformers `owlv2.md` (V) | Apache-2.0 | text/image-query detection | images are padded to square, so boxes need un-padding when mapping back (exp.); also supports image-conditioned queries |
| YOLO-World | 2401.17270 (V) | github `AILab-CVC/YOLO-World` (GPL-3.0, last push 2025-02, V); HF `wondervictor/YOLO-World` (gpl-3.0, V) | GPL-3.0 | real-time open-vocab | GPL; also an Ultralytics port exists (licence not checked, UNVERIFIED) |
| YOLOE | 2503.07465 (V) | github `THU-MIG/yoloe` (AGPL-3.0, V); HF `jameslahm/yoloe-v8l-seg` (agpl-3.0, V) | AGPL-3.0 | text/visual/prompt-free open-vocab with seg | AGPL |
| LLMDet | 2501.18954 (V) | repo/weights not checked | UNVERIFIED | | |
| Roboflow100-VL (benchmark) | 2505.20612 (V) | github `roboflow/rf100-vl` (Apache-2.0, V) | Apache-2.0 | measuring zero-shot vs finetune on 100 domains | the right "should I finetune?" benchmark; numbers not re-measured here |

### 6. Generative VLMs

| Model | Task | arXiv | Repo / HF id | Licence | Typical use | Gotcha |
|---|---|---|---|---|---|---|
| Florence-2 | captioning, OD, grounding, OCR, seg via task tokens | 2311.06242 (V) | HF `microsoft/Florence-2-base/large` (+`-ft`) (MIT, V); native port `florence-community/Florence-2-large` (MIT, V); Transformers `florence2.md` (V); no `microsoft/Florence-2` GitHub repo (404) | MIT | small multi-task model, auto-label, OCR | the `microsoft/` checkpoints used `trust_remote_code`; prefer the native `florence-community` port (V that it exists) |
| PaliGemma | transfer VLM (3B) | 2407.07726 (V) | HF `google/paligemma-3b-pt-224` (gemma licence, gated, V) | Gemma terms | finetune for detect/segment/VQA | `-pt` checkpoints are for transfer, `-mix` for direct use; location output is as special tokens (exp.) |
| PaliGemma 2 | same, Gemma 2 base | 2412.03555 (V) | HF `google/paligemma2-3b-pt-224`, `paligemma2-3b-mix-448` (gemma, gated, V) | Gemma terms | same | HF tags list 2407.07726 first on these cards; the correct PaliGemma 2 paper is 2412.03555 (V) |
| Gemma 4 | multimodal LLM | 2607.02770 Gemma 4 Technical Report (V) | HF `google/gemma-4-31B-it`, `gemma-4-E4B-it` (apache-2.0, V); Transformers `gemma4.md` (V) | Apache-2.0 (as tagged) | open general VLM | I did not verify its grounding/detection quality (UNVERIFIED) |
| Qwen2.5-VL | VLM, grounding, OCR, video | 2502.13923 (V) | HF `Qwen/Qwen2.5-VL-7B-Instruct` (apache-2.0, V) | Apache-2.0 (7B; other sizes may differ, UNVERIFIED) | document/OCR, grounding, VQA | coordinate convention differs between Qwen generations (exp., UNVERIFIED); check the model card before parsing boxes |
| Qwen3-VL | VLM, 2B-235B incl. MoE | 2511.21631 Qwen3-VL Technical Report (V) | github `QwenLM/Qwen3-VL` (Apache-2.0, V); HF `Qwen/Qwen3-VL-8B-Instruct`, `-2B-`, `-30B-A3B-` (apache-2.0, V); Transformers `qwen3_vl.md` (V) | Apache-2.0 | current Qwen VLM default | HF cards cite 2505.09388 (the Qwen3 LLM report), not the VL report; use 2511.21631 |
| Qwen3-VL-Embedding / Reranker | multimodal retrieval | 2601.04720 (V) | HF `Qwen/Qwen3-VL-Embedding-8B` (apache-2.0, V) | Apache-2.0 | multimodal retrieval alternative to CLIP-family | heavier than SigLIP2; compare on your data (not measured) |
| Qwen3.5 / 3.6 / 3.8 | natively multimodal LLM line | no arXiv found (UNVERIFIED) | HF `Qwen/Qwen3.5-9B`, `Qwen/Qwen3.6-27B`, `Qwen/Qwen3.8-27B` (apache-2.0, V); `Qwen3.8-Flash-Next` licence `other` (V) | Apache-2.0 for the three checked | newest open Qwen, vision included | per-size licences vary (one `other`); CV-specific quality not evaluated |
| InternVL3 / 3.5 | VLM | 2504.10479 InternVL3, 2508.18265 InternVL3.5, 2312.14238 InternVL (all V) | github `OpenGVLab/InternVL` (MIT, last push 2025-09, V); HF `OpenGVLab/InternVL3-8B`, `InternVL3_5-8B` (apache-2.0, V); Transformers `internvl.md` (V) | MIT code, Apache-2.0 weights | strong OCR/doc/chart VLM | the repo has not been pushed since 2025-09 (V) |
| LLaVA family | VLM baselines | 2304.08485 LLaVA, 2310.03744 LLaVA-1.5, 2408.03326 LLaVA-OneVision, 2509.23661 LLaVA-OneVision-1.5 (all V) | github `haotian-liu/LLaVA` (Apache-2.0, V), `LLaVA-VL/LLaVA-NeXT` (Apache-2.0, V); HF `llava-hf/llava-1.5-7b-hf` (**llama2**, V), `llava-hf/llava-v1.6-mistral-7b-hf` (apache-2.0, V), `llava-hf/llava-onevision-qwen2-7b-ov-hf` (apache-2.0, V), `lmms-lab/LLaVA-OneVision-1.5-8B-Instruct` (apache-2.0, V) | varies per checkpoint | baselines, finetune recipes | the licence follows the LLM base (llava-1.5 = Llama 2 licence) |
| SmolVLM / SmolVLM2 | small VLM | 2504.05299 (V) | HF `HuggingFaceTB/SmolVLM2-2.2B-Instruct` (apache-2.0, V) | Apache-2.0 | edge VLM | quality ceiling is low for dense OCR (exp.) |
| Moondream | small VLM | no paper tag | HF `vikhyatk/moondream2` (apache-2.0, V, updated 2026-09-23) | Apache-2.0 | tiny captioning/detect/point | revision-pinned (use a dated revision); capabilities not verified |

### 7. Depth and 3D

| Model | arXiv | Repo / HF id | Licence | Typical use | Gotcha |
|---|---|---|---|---|---|
| Depth Anything v1 | 2401.10891 (V) | HF `LiheYoung/depth_anything_vitl14` (no licence tag, V) | UNVERIFIED | historical | superseded |
| Depth Anything V2 | 2406.09414 (V) | github `DepthAnything/Depth-Anything-V2` (Apache-2.0 repo, V); HF `depth-anything/Depth-Anything-V2-Small-hf` (**apache-2.0**), `...-Base-hf`, `...-Large-hf` (**cc-by-nc-4.0**), `...-Metric-Indoor-Large-hf` (no tag) (V) | **Small Apache; Base/Large CC-BY-NC** | relative depth, edge-friendly Small | the licence differs by checkpoint size, which is the classic trap; default output is relative (affine-invariant) not metric |
| Depth Anything 3 | 2511.10647 (V) | github `ByteDance-Seed/Depth-Anything-3` (Apache-2.0, V); HF `depth-anything/DA3-LARGE-1.1`, `DA3METRIC-LARGE` (apache-2.0, V), `DA3-LARGE` (cc-by-nc-4.0, V) | mixed: `-1.1` and METRIC Apache, original `DA3-LARGE` NC | multi-view depth/pose, metric depth | `DA3-LARGE` vs `DA3-LARGE-1.1` licences differ (V); not listed in Transformers docs (V) |
| Depth Pro | 2410.02073 (V) | HF `apple/DepthPro-hf` (apple-amlr, V) | Apple research licence | sharp metric depth, no intrinsics | non-OSI licence |
| VGGT | 2503.11651 (V) | github `facebookresearch/vggt` (custom VGGT License, V); HF `facebook/VGGT-1B` (cc-by-nc-4.0, V) | NC / custom | multi-view geometry | NC weights |

### 8. Keypoints, tracking, OCR, background removal

| Model | Task | arXiv | Repo / HF id | Licence | Typical use | Gotcha |
|---|---|---|---|---|---|---|
| ViTPose | pose | 2204.12484 (V) | github `ViTAE-Transformer/ViTPose` (Apache-2.0, V); HF `usyd-community/vitpose-base-simple`, `vitpose-plus-base` (apache-2.0, V); Transformers `vitpose.md` (V) | Apache-2.0 | top-down human pose | top-down: needs a person detector first; boxes in, keypoints out |
| RTMPose / mmpose | pose | 2303.07399 (V) | github `open-mmlab/mmpose` (Apache-2.0, last push 2025-08, V) | Apache-2.0 | real-time pose | mm* stack install friction (exp.) |
| Sapiens | human-centric tasks | 2408.12569 (V) | github `facebookresearch/sapiens` (CC-BY-NC, V); HF `facebook/sapiens-pose-0.3b` (cc-by-nc-4.0, V) | NC | research | non-commercial |
| RF-DETR keypoints | pose | n/a | `RFDETRKeypointPreview` in `src/rfdetr/variants.py` (V local) | preview | | preview only per AGENTS.md |
| ByteTrack, BoT-SORT, OC-SORT | MOT | 2110.06864, 2206.14651, 2203.14360 (all V) | `roboflow/trackers` (Apache-2.0, V), `roboflow/supervision` (MIT, V) | permissive | tracking-by-detection | tracker quality is bounded by detector recall/threshold; confidence threshold tuning matters more than tracker choice (exp.) |
| SAMURAI | zero-shot tracking | 2411.11922 (V) | repo not found as `zhengyuf/SAMURAI` (UNVERIFIED) | UNVERIFIED | | |
| PaddleOCR 3.0 | OCR/doc | 2507.05595 (V) | github `PaddlePaddle/PaddleOCR` (Apache-2.0, 91k stars, V) | Apache-2.0 | production OCR pipeline | Paddle dependency; check ONNX route |
| GOT-OCR 2.0 | OCR-2.0 end-to-end | 2409.01704 (V) | HF `stepfun-ai/GOT-OCR-2.0-hf` (apache-2.0, V); Transformers `got_ocr2.md` (V) | Apache-2.0 | formulas, tables, doc OCR | VLM-class latency |
| TrOCR | line-level OCR | 2109.10282 (V) | HF `microsoft/trocr-base-printed` (no licence tag, V) | UNVERIFIED | single text-line recognition | needs line crops; not a page-level OCR |
| BiRefNet | background removal / dichotomous seg | 2401.03407 (V) | HF `ZhengPeng7/BiRefNet` (MIT, V) | MIT | matting-like cut-outs | |
| Recognize Anything (RAM++) | tagging | 2306.03514 (HF tag) | HF `xinyu1205/recognize-anything-plus-model` (apache-2.0, V) | Apache-2.0 | image tagging | paper id from HF tag, title not fetched (UNVERIFIED) |
| Not checked | EasyOCR, docTR, Surya, MMDetection (repo Apache, last push 2024-08, V) | | | UNVERIFIED | | |

---

## Task C. Proposed cv-kit skill breakdown (ordered by priority)

Principle: split by engineer workflow, one skill per decision an engineer makes. Models live in shared reference files that several skills point at; no per-model skills. Each skill's SKILL.md stays short (decision procedure + pointers); detail goes in `references/`. Every model claim in the references must carry its verification status and date (use the table above as seed; re-verify licences at release time because they change).

Shared reference files (single source of truth, avoid the duplicated-reference problem of the reference skill):

- `references/model-catalog.md` (Task B tables, verified/unverified marks)
- `references/licenses.md` (AGPL/GPL/NC/custom-Meta/Gemma/apple-amlr triage + per-checkpoint traps such as Depth Anything V2 Small vs Base/Large)
- `references/data-formats.md` (COCO, YOLO txt, Pascal VOC, RLE masks, keypoint formats, conversion pitfalls)
- `references/metrics.md` (COCO mAP variants, PR/F1 operating point, retrieval recall@k, tracking metrics, VLM grounding metrics)

| # | Skill | One-line trigger description | Reference files it needs |
|---|---|---|---|
| 1 | `cv-model-selection` | Use when choosing a model or approach for a vision task (detect, segment, classify, track, depth, OCR, retrieval) given latency, accuracy, data, and licence constraints. | `model-catalog.md`, `licenses.md`, `selection-flowchart.md` (task, data volume, latency budget, device -> closed-set detector vs open-vocab vs VLM vs foundation features) |
| 2 | `cv-dataset-prep` | Use when building, converting, auditing, or splitting an image/video dataset (COCO/YOLO/VOC, masks, keypoints), including split leakage and label QA. | `data-formats.md`, `dataset-audit.md` (dup/near-dup detection with embeddings, class imbalance, leakage by video/scene, label-noise checks) |
| 3 | `cv-auto-label` | Use when bootstrapping labels with foundation models (Grounding DINO / OWLv2 / SAM / SAM 3 / Florence-2 / VLM) and then reviewing them. | `model-catalog.md` (sections 3, 5, 6), `autolabel-recipes.md` (prompt formats, threshold tuning, human review loop, measuring auto-label precision vs a hand-labeled sample) |
| 4 | `cv-finetune-detector` | Use when finetuning or training a detector/segmenter (RF-DETR, RT-DETR, D-FINE, YOLO) on a custom dataset, or debugging training (not converging, overfitting, small objects). | `model-catalog.md` (sections 3, 4), `training-checklist.md` (resolution/multiple constraints, LR/epochs, augmentation, backbone freezing, class mapping), `licenses.md` |
| 5 | `cv-evaluate` | Use when measuring or comparing vision models: mAP, per-class/size AP, operating-point choice, error analysis, retrieval metrics, tracking metrics, VLM output checks. | `metrics.md`, `error-analysis.md` (confusion by class/size/occlusion, FP/FN galleries, calibration), `benchmarks.md` (COCO, RF100-VL, how to avoid test-set leakage) |
| 6 | `cv-embeddings-retrieval` | Use when you need image/text embeddings: CLIP/OpenCLIP/SigLIP2/DINOv2/DINOv3 zero-shot classification, linear probe, kNN, dedup, clustering, image search. | `model-catalog.md` (sections 1, 2), `embedding-recipes.md` (preprocessing parity, normalisation, prompt templates, sigmoid vs softmax, ANN index choice, probe vs finetune), `licenses.md` |
| 7 | `cv-export-deploy` | Use when exporting and shipping a model (ONNX, TensorRT, OpenVINO, CoreML, LiteRT, INT8) or benchmarking latency on target hardware. | `export-matrix.md` (formats vs model families, dynamic batch, NMS-free vs NMS heads), `benchmarking.md` (warmup, sync, batch, pre/post-processing included), `quantization.md` (calibration data, accuracy re-check) |
| 8 | `cv-vlm-usage` | Use when applying or finetuning a generative VLM (Qwen-VL, Gemma 4, Florence-2, PaliGemma, InternVL, SmolVLM) for captioning, VQA, grounding, OCR or structured extraction on images. | `model-catalog.md` (section 6), `vlm-output-parsing.md` (per-model box/coord conventions, JSON-constrained output, hallucination checks), `vlm-finetune.md` (LoRA, quantisation, memory) |
| 9 | `cv-video-tracking` | Use when working with video: tracking-by-detection, SAM 2/3 propagation, re-ID, MOT metrics. | `model-catalog.md` (sections 3, 8), `tracking-recipes.md` |
| 10 | `cv-depth-3d-pose-ocr` | Use for depth, multi-view geometry, keypoints/pose, or OCR/document extraction tasks. Split later only if any of the four grows. | `model-catalog.md` (sections 7, 8), `licenses.md` |

Suggested rules (always-on, short) rather than skills:

- `rules/licenses.md`: never recommend a model for commercial use without stating its licence and any per-checkpoint caveat; AGPL/GPL/NC/custom Meta licences require a callout.
- `rules/verification.md`: never state an arXiv id, HF id, or number unless it was fetched; mark UNVERIFIED.
- `rules/reproducibility.md`: pin model revisions and library versions; fix seeds; log preprocessing.

Suggested agents:

- `model-scout` (read-only, web + HF API): re-verifies catalog rows (ids, licences, arXiv titles) using the same three-source method as this research.
- `cv-reviewer`: reviews a finetune/eval script for train/val leakage, preprocessing mismatches between training and inference, and metric misuse.

YAGNI notes:

- Skills 9 and 10 are lowest priority; ship 1-8 first. Merge 5 into 4 if evaluation guidance ends up under ~100 lines.
- Do not add scripts until one is actually executed and tested; ship the model-scout verification helper (HF API + arXiv API) as the only script, because it is the only automation this research needed (see `hfcheck.sh` and `arx.py` in the scratchpad for the approach).
- No per-model skills; they go stale and duplicate the catalog.

---

## Verification log and open items

- Not checked at all (not in tables or marked UNVERIFIED): EasyOCR, docTR, Surya, Detectron2, MMDetection weights, SAM-HQ licence, MM-Grounding-DINO licence, LLMDet repo/weights, RT-DETRv4 repo/weights, YOLOv9 repo, DEIM/DEIMv2 HF weights, TrOCR licence, Depth Anything v1 licence, SAMURAI repo, SigLIP 3 (existence), PaliGemma 3 (existence), Qwen3.5-3.8 papers.
- Conflicting signal to resolve before documenting: RF-DETR plus (XLarge/2XLarge) licence. This repo's AGENTS.md says PML 1.0 via `rfdetr_plus`; HF tag on `Roboflow/rf-detr-seg-xxlarge` says apache-2.0.
- DINOv3 and SAM licences: custom Meta licences. I confirmed the royalty-free limited grant and trade-control clauses but did not read the full text for commercial restrictions, so "commercial OK?" is UNVERIFIED for both.
- Web search for "latest VLM releases" returned only aggregator blogs (e.g. mentions of DeepSeek V4-Flash-Vision-Exp, Cohere Embed 5); I did not use these claims.
- Gotchas tagged "exp." are from engineering knowledge, not confirmed in this session.
- Reference skill: all 7 files were read (diffed), nothing was executed.
