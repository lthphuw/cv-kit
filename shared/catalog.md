# Model catalog

Transcribed from `docs/research/01-models-and-skills.md` (research date 2026-10-14). Nothing here is newer than that file.

How to read the table:

- `Status` is `verified` only where the research file marks the id and the licence as fetched and matched, and the Paper cell is one bare arXiv id or `—`. Everything else is `UNVERIFIED`, including rows whose research entry cites several arXiv ids, rows with a licence conflict, and rows whose repo or licence was not checked.
- A Gotcha cell that starts with `(experience)` is the research author's engineering knowledge. It was not tested and not confirmed against a document, so treat it as a hypothesis to check, not as measured fact.
- A `—` means the research file gives no value for that cell.
- Licences are the Hugging Face tag for weights and, where it differs, the GitHub licence for code. Licences change: re-check at release time.
- Sections 4, 5 and 7 of the research file have no Task column. The Task cell there is taken from the section heading.

## 1. Image-text embedding (contrastive)

| Model | Task | Paper (arXiv) | Repo / HF id | Licence | Typical use | Gotcha | Status |
|---|---|---|---|---|---|---|---|
| CLIP | image-text embedding | 2103.00020 | github `openai/CLIP`; HF `openai/clip-vit-large-patch14`, `openai/clip-vit-base-patch32` | MIT code (github); weights: HF licence tag empty, so weight licence not stated | zero-shot classify, retrieval, linear probe | 77-token text limit; zero-shot accuracy is highly prompt-template dependent ("a photo of a {}"); softmax over given labels cannot say "none of these" | UNVERIFIED |
| OpenCLIP | open reproduction + model zoo | 2212.07143 (scaling laws); 1910.04867 (VTAB, listed on HF tags, UNVERIFIED as the citation to use) | github `mlfoundations/open_clip` (MIT text, GitHub says NOASSERTION); HF `laion/CLIP-ViT-H-14-laion2B-s32B-b79K`, `laion/CLIP-ViT-bigG-14-laion2B-39B-b160k` | MIT | embeddings for retrieval / dedup, linear probe | Per-checkpoint weight licence differs (e.g. MobileCLIP2 weights are `apple-amlr`); LAION-trained checkpoints inherit dataset caveats | UNVERIFIED |
| EVA-CLIP | stronger CLIP | 2303.15389 (EVA-CLIP); 2402.04252 (EVA-CLIP-18B) | github `baaivision/EVA` (last push 2024-08); HF `BAAI/EVA-CLIP-8B`, `timm/eva02_large_patch14_clip_224.merged2b_s4b_b131k` | MIT / Apache-2.0 (code MIT; `EVA-CLIP-8B` Apache-2.0; timm checkpoint MIT) | strong zero-shot, embeddings | 8B/18B variants are heavy; the `-8B` HF card cites the 18B paper id (the tag shows 2402.04252) | UNVERIFIED |
| MetaCLIP | data-curated CLIP | 2309.16671 | HF `facebook/metaclip-b32-400m` | **cc-by-nc-4.0** (non-commercial) | research baseline | non-commercial weights; MetaCLIP 2 is in Transformers docs (`metaclip_2.md`) but its paper and licence were not checked (UNVERIFIED) | verified |
| SigLIP | sigmoid-loss CLIP | 2303.15343 | big_vision `google-research/big_vision`; HF `google/siglip-so400m-patch14-384` | Apache-2.0 | zero-shot, retrieval, vision tower of many VLMs | (experience) Pairwise sigmoid: scores are independent probabilities, not a softmax over labels; text must be padded to fixed `max_length` (check model card) | verified |
| SigLIP 2 | multilingual, dense-aware encoder | 2502.14786 | HF `google/siglip2-so400m-patch14-384`, `google/siglip2-base-patch16-224`, `google/siglip2-giant-opt-patch16-384`, `google/siglip2-so400m-patch16-naflex` (all apache-2.0); Transformers `siglip2.md` | Apache-2.0 | default pick for zero-shot/retrieval/embeddings; NaFlex variant for variable aspect ratio | (experience) NaFlex needs the NaFlex processor/mask path, not the fixed-res one; `-jax` checkpoints are JAX-only | verified |
| Perception Encoder (PE-Core) | CLIP-style, also video | 2504.13181 | github `facebookresearch/perception_models`; HF `facebook/PE-Core-L14-336` | Apache-2.0 | SigLIP2 alternative; strong intermediate-layer features | Best features are in intermediate layers, not the output (per the paper title) | verified |
| MobileCLIP / MobileCLIP2 | on-device CLIP | 2311.17049 (HF tag); 2508.20691 (MobileCLIP2) | github `apple-aiml-research/ml-mobileclip`; HF `apple/MobileCLIP2-S0`, `timm/MobileCLIP2-S4-OpenCLIP` | **apple-amlr** (custom Apple research licence, not OSI) | edge/mobile retrieval | licence is not OSI; read before shipping commercially | UNVERIFIED |
| TIPS | spatially-aware image-text | 2410.16512 | HF `google/tipsv1-so400m14` etc. (model card read) | Apache-2.0 | dense/zero-shot segmentation features | needs `trust_remote_code=True` per the model card | verified |

## 2. Self-supervised vision backbones

| Model | Task | Paper (arXiv) | Repo / HF id | Licence | Typical use | Gotcha | Status |
|---|---|---|---|---|---|---|---|
| DINOv2 | SSL features | 2304.07193 | github `facebookresearch/dinov2`; HF `facebook/dinov2-small`, `facebook/dinov2-base`, `facebook/dinov2-with-registers-base` (registers paper 2309.16588, from the HF tag) | Apache-2.0 | kNN / linear probe, dedup, dense features, detector backbone (RF-DETR uses it, per its README) | patch size 14, so input size should be a multiple of 14; non-register models show artefact high-norm patch tokens in dense maps | verified |
| DINOv3 | SSL features, satellite variants, 7B | 2508.10104 | github `facebookresearch/dinov3`; HF `facebook/dinov3-vitb16-pretrain-lvd1689m`, `facebook/dinov3-convnext-base-pretrain-lvd1689m`, `facebook/dinov3-vitl16-pretrain-sat493m`; ungated mirror `timm/vit_small_patch16_dinov3.lvd1689m` | **custom "DINOv3 License"**, gated=manual on HF (royalty-free limited grant plus trade-control clauses seen; remaining restrictions not parsed, so commercial suitability is UNVERIFIED) | linear probe, dense tasks, satellite (`sat493m`), backbone of DEIMv2/EoMT-DINOv3 | gated download needs HF login + approval; patch size 16 (not 14); `lvd1689m` vs `sat493m` weights are not interchangeable by domain | UNVERIFIED |

## 3. Promptable and concept segmentation

| Model | Task | Paper (arXiv) | Repo / HF id | Licence | Typical use | Gotcha | Status |
|---|---|---|---|---|---|---|---|
| SAM | promptable mask | 2304.02643 | github `facebookresearch/segment-anything` (last push 2024-09); HF `facebook/sam-vit-base`, `facebook/sam-vit-huge` | Apache-2.0 | box/point prompts, auto-label | image-only; masks are class-agnostic, so you still need a detector or labels for class identity | verified |
| SAM 2 / 2.1 | image + video | 2408.00714 | github `facebookresearch/sam2`; HF `facebook/sam2.1-hiera-large` | Apache-2.0 | video object propagation, auto-label sequences | (experience) prefer the `sam2.1` checkpoints over `sam2`; memory grows with video length unless frames are offloaded | verified |
| SAM 3 / 3.1 | concept-prompted segmentation + tracking (text, exemplar) | 2511.16719 ("SAM 3: Segment Anything with Concepts") | github `facebookresearch/sam3`; HF `facebook/sam3`, `facebook/sam3.1` (gated=manual); Transformers `sam3*.md` | **custom "SAM License"**, gated (royalty-free limited grant seen; remaining terms not fully parsed, so commercial suitability is UNVERIFIED) | open-vocabulary instance seg by text/exemplar, auto-label, video tracking | gated access; about 850M params per the RF-DETR README (cited there, not re-measured); SAM 3.1 changes not read (UNVERIFIED) | UNVERIFIED |
| Efficient SAMs | edge/real-time | MobileSAM 2306.14289; EfficientSAM 2312.00863; EdgeTAM 2501.07256; SAM-HQ 2306.01567 (titles fetched) | `ChaoningZhang/MobileSAM`, `yformer/EfficientSAM`; HF `facebook/EdgeTAM`, `yonigozlan/EdgeTAM-hf` | Apache-2.0 (MobileSAM, EfficientSAM, EdgeTAM); SAM-HQ licence not checked (UNVERIFIED) | on-device interactive seg | SAM-HQ repo/HF licence not checked (UNVERIFIED); MobileSAM HF id not found as `ChaoningZhang/MobileSAM` (NOT FOUND on HF) | UNVERIFIED |
| Grounded-SAM(-2) | pipeline: Grounding DINO + SAM | 2401.14159 | github `IDEA-Research/Grounded-SAM-2` (last push 2025-11) | Apache-2.0 | classic auto-label recipe; being superseded by SAM 3 for text prompts | pipeline is two models, two failure modes (box recall then mask quality) | verified |
| Universal seg | semantic/instance/panoptic | Mask2Former 2112.01527; OneFormer 2211.06220; SegFormer 2105.15203 | HF `facebook/mask2former-swin-large-coco-panoptic`, `shi-labs/oneformer_coco_swin_large`, `nvidia/segformer-b5-finetuned-ade-640-640`; repos: Mask2Former (archived), SegFormer | mixed, check per checkpoint: Mask2Former HF tag `other` (repo MIT, archived); OneFormer MIT; SegFormer HF tag `other` (repo "NVIDIA Source Code License", non-OSI) | closed-set semantic/panoptic finetune | Mask2Former repo archived; use the Transformers port; SegFormer licence is NVIDIA's non-OSI one | UNVERIFIED |
| RF-DETR-Seg | real-time instance seg | 2511.09554 | HF `Roboflow/rf-detr-seg-nano` to `-xxlarge` (apache-2.0 on the two tags checked: small and xxlarge) | conflicting sources: PML 1.0 vs Apache-2.0 (HF tag on `seg-xxlarge` says Apache-2.0; rf-detr's AGENTS.md says XLarge/2XLarge plus models need `rfdetr_plus` under PML 1.0; UNRESOLVED, check before documenting) | finetune on own data | conflicting licence signals for the largest sizes | UNVERIFIED |

## 4. Detectors (closed-set)

| Model | Task | Paper (arXiv) | Repo / HF id | Licence | Typical use | Gotcha | Status |
|---|---|---|---|---|---|---|---|
| RF-DETR | closed-set detection | 2511.09554 | github `roboflow/rf-detr` (release 1.11.2 on 2026-10-04); HF `Roboflow/rf-detr-nano`, `Roboflow/rf-detr-small`, `Roboflow/rf-detr-base`; rf-detr source `src/rfdetr/variants.py` | Apache-2.0 for the repo and the nano/small/base tags; XLarge/2XLarge plus models: conflicting sources: PML 1.0 vs Apache-2.0 (PML 1.0 per rf-detr's AGENTS.md, not re-verified; HF tag on `Roboflow/rf-detr-seg-xxlarge` says Apache-2.0) | finetune on COCO-format data, real-time deploy | (experience) DINOv2-register backbone is fixed-resolution friendly; resolution must be a multiple of the model's patch/window size. `RFDETRBase` is deprecated by rf-detr's own conventions | UNVERIFIED |
| RT-DETR / RT-DETRv2 | closed-set detection | 2304.08069 (RT-DETR); 2407.17140 (RT-DETRv2) | github `lyuwenyu/RT-DETR`; HF `PekingU/rtdetr_r50vd`, `PekingU/rtdetr_v2_r50vd` | Apache-2.0 | NMS-free real-time baseline | Original code is PaddlePaddle; the PyTorch port is the practical route; v4 exists (2510.25257, title fetched) but repo/weights not checked (UNVERIFIED) | UNVERIFIED |
| D-FINE | closed-set detection | 2410.13842 | github `Peterande/D-FINE`; HF `ustc-community/dfine-small-coco`, `ustc-community/dfine-xlarge-coco` | Apache-2.0 | high-AP real-time | (experience) distribution-based box regression; ONNX export needs a check of the integral head | verified |
| DEIM / DEIMv2 | closed-set detection | 2412.04234 (DEIM); 2509.20787 (DEIMv2, "Real-Time Object Detection Meets DINOv3") | github `Intellindust-AI-Lab/DEIM` (LICENSE file text says Apache; GitHub shows NOASSERTION), `Intellindust-AI-Lab/DEIMv2` (LICENSE.md); Transformers `deimv2.md`; HF weights id NOT FOUND for the guesses `Intellindust/DEIM*` (UNVERIFIED) | DEIM Apache (per the LICENSE file); **DEIMv2 non-commercial only, commercial use needs a separate licence** (LICENSE.md) | research / benchmark | DEIMv2 licence blocks commercial deployment; the Transformers port does not change that (UNVERIFIED legal reading) | UNVERIFIED |
| LW-DETR | closed-set detection | 2406.03459 | github `Atten4Vis/LW-DETR`; Transformers `lw_detr.md` | Apache-2.0 | light real-time baseline, ancestor of RF-DETR (per its README) | HF weight ids not checked (UNVERIFIED) | verified |
| YOLOv10 | closed-set detection | 2405.14458 | github `THU-MIG/yolov10` (last push 2025-03); HF `jameslahm/yolov10n` | AGPL-3.0 | NMS-free YOLO | AGPL reaches network use | verified |
| YOLOv12 | closed-set detection | 2502.12524 | github `sunsmarterjie/yolov12` | AGPL-3.0 | attention-centric YOLO | training instability/memory notes in community: UNVERIFIED | verified |
| YOLO11 | closed-set detection (no paper: the HF card has no arxiv tag) | — | github `ultralytics/ultralytics`; HF `Ultralytics/YOLO11` | AGPL-3.0 (an enterprise licence exists, terms UNVERIFIED) | default YOLO toolchain | AGPL for model, code and often derived apps | verified |
| YOLO26 | closed-set detection (paper title: "Ultralytics YOLO26") | 2606.03748 | HF `Ultralytics/YOLO26` (created 2026-01-26) | AGPL-3.0 | newest Ultralytics line | release notes/architecture not read; claims about NMS-free/edge features UNVERIFIED | verified |
| YOLOv9 | closed-set detection | 2402.13616 | repo not checked | UNVERIFIED | — | — | UNVERIFIED |

## 5. Open-vocabulary detection / grounding

| Model | Task | Paper (arXiv) | Repo / HF id | Licence | Typical use | Gotcha | Status |
|---|---|---|---|---|---|---|---|
| Grounding DINO | open-vocabulary detection | 2303.05499 | github `IDEA-Research/GroundingDINO` (last push 2024-08); HF `IDEA-Research/grounding-dino-base`, `IDEA-Research/grounding-dino-tiny`; Transformers `grounding-dino.md` | Apache-2.0 | zero-shot detect from text, auto-label | (experience) text prompt format and the box/text thresholds change recall a lot (lowercase, period-separated phrases) | verified |
| MM-Grounding-DINO | open-vocabulary detection | 2401.02361 | HF `openmmlab-community/mm_grounding_dino_base_all` etc. (exist; licence not read, UNVERIFIED); Transformers `mm-grounding-dino.md` | UNVERIFIED | stronger open GDINO reproduction | checkpoint names encode the training data mix; choose deliberately | UNVERIFIED |
| OWL-ViT / OWLv2 | open-vocabulary detection | 2205.06230 (OWL-ViT); 2306.09683 (OWLv2) | HF `google/owlvit-base-patch32`, `google/owlv2-base-patch16-ensemble`; Transformers `owlv2.md` | Apache-2.0 | text/image-query detection | (experience) images are padded to square, so boxes need un-padding when mapping back; also supports image-conditioned queries | UNVERIFIED |
| YOLO-World | open-vocabulary detection | 2401.17270 | github `AILab-CVC/YOLO-World` (last push 2025-02); HF `wondervictor/YOLO-World` | **GPL-3.0** | real-time open-vocab | GPL; also an Ultralytics port exists (licence not checked, UNVERIFIED) | verified |
| YOLOE | open-vocabulary detection | 2503.07465 | github `THU-MIG/yoloe`; HF `jameslahm/yoloe-v8l-seg` | AGPL-3.0 | text/visual/prompt-free open-vocab with seg | AGPL | verified |
| LLMDet | open-vocabulary detection | 2501.18954 | repo/weights not checked | UNVERIFIED | — | — | UNVERIFIED |
| Roboflow100-VL (benchmark) | benchmark | 2505.20612 | github `roboflow/rf100-vl` | Apache-2.0 | measuring zero-shot vs finetune on 100 domains | the right "should I finetune?" benchmark; numbers not re-measured | verified |

## 6. Generative VLMs

| Model | Task | Paper (arXiv) | Repo / HF id | Licence | Typical use | Gotcha | Status |
|---|---|---|---|---|---|---|---|
| Florence-2 | captioning, OD, grounding, OCR, seg via task tokens | 2311.06242 | HF `microsoft/Florence-2-base`, `microsoft/Florence-2-large` (+`-ft`); native port `florence-community/Florence-2-large`; Transformers `florence2.md`; no `microsoft/Florence-2` GitHub repo (404) | MIT | small multi-task model, auto-label, OCR | the `microsoft/` checkpoints used `trust_remote_code`; prefer the native `florence-community` port (it exists) | verified |
| PaliGemma | transfer VLM (3B) | 2407.07726 | HF `google/paligemma-3b-pt-224` (gated) | Gemma terms (gated) | finetune for detect/segment/VQA | (experience) `-pt` checkpoints are for transfer, `-mix` for direct use; location output is as special tokens | verified |
| PaliGemma 2 | same, Gemma 2 base | 2412.03555 | HF `google/paligemma2-3b-pt-224`, `google/paligemma2-3b-mix-448` (gated) | Gemma terms (gated) | same | HF tags list 2407.07726 first on these cards; the correct PaliGemma 2 paper is 2412.03555 | verified |
| Gemma 4 | multimodal LLM (paper: Gemma 4 Technical Report) | 2607.02770 | HF `google/gemma-4-31B-it`, `google/gemma-4-E4B-it`; Transformers `gemma4.md` | Apache-2.0 (as tagged) | open general VLM | grounding/detection quality not verified (UNVERIFIED) | verified |
| Qwen2.5-VL | VLM, grounding, OCR, video | 2502.13923 | HF `Qwen/Qwen2.5-VL-7B-Instruct` | Apache-2.0 (7B; other sizes may differ, UNVERIFIED) | document/OCR, grounding, VQA | (experience) coordinate convention differs between Qwen generations (UNVERIFIED); check the model card before parsing boxes | verified |
| Qwen3-VL | VLM, 2B-235B incl. MoE (paper: Qwen3-VL Technical Report) | 2511.21631 | github `QwenLM/Qwen3-VL`; HF `Qwen/Qwen3-VL-8B-Instruct`, `-2B-`, `-30B-A3B-` variants; Transformers `qwen3_vl.md` | Apache-2.0 | current Qwen VLM default | HF cards cite 2505.09388 (the Qwen3 LLM report), not the VL report; use 2511.21631 | verified |
| Qwen3-VL-Embedding / Reranker | multimodal retrieval | 2601.04720 | HF `Qwen/Qwen3-VL-Embedding-8B` | Apache-2.0 | multimodal retrieval alternative to CLIP-family | heavier than SigLIP2; compare on your data (not measured) | verified |
| Qwen3.5 / 3.6 / 3.8 | natively multimodal LLM line | no arXiv id found (UNVERIFIED) | HF `Qwen/Qwen3.5-9B`, `Qwen/Qwen3.6-27B`, `Qwen/Qwen3.8-27B`; `Qwen3.8-Flash-Next` | Apache-2.0 for the three checked; `Qwen3.8-Flash-Next` is tagged `other` | newest open Qwen, vision included | per-size licences vary (one `other`); CV-specific quality not evaluated | UNVERIFIED |
| InternVL3 / 3.5 | VLM | 2504.10479 (InternVL3); 2508.18265 (InternVL3.5); 2312.14238 (InternVL) | github `OpenGVLab/InternVL` (last push 2025-09); HF `OpenGVLab/InternVL3-8B`, `OpenGVLab/InternVL3_5-8B`; Transformers `internvl.md` | MIT code, Apache-2.0 weights | strong OCR/doc/chart VLM | the repo has not been pushed since 2025-09 | UNVERIFIED |
| LLaVA family | VLM baselines | 2304.08485 (LLaVA); 2310.03744 (LLaVA-1.5); 2408.03326 (LLaVA-OneVision); 2509.23661 (LLaVA-OneVision-1.5) | github `haotian-liu/LLaVA`, `LLaVA-VL/LLaVA-NeXT`; HF `llava-hf/llava-1.5-7b-hf`, `llava-hf/llava-v1.6-mistral-7b-hf`, `llava-hf/llava-onevision-qwen2-7b-ov-hf`, `lmms-lab/LLaVA-OneVision-1.5-8B-Instruct` | varies per checkpoint: repos Apache-2.0; `llava-1.5-7b-hf` is **llama2** licence; the other three HF checkpoints are apache-2.0 | baselines, finetune recipes | the licence follows the LLM base (llava-1.5 = Llama 2 licence) | UNVERIFIED |
| SmolVLM / SmolVLM2 | small VLM | 2504.05299 | HF `HuggingFaceTB/SmolVLM2-2.2B-Instruct` | Apache-2.0 | edge VLM | (experience) quality ceiling is low for dense OCR | verified |
| Moondream | small VLM (no paper tag) | — | HF `vikhyatk/moondream2` (updated 2026-09-23) | Apache-2.0 | tiny captioning/detect/point | revision-pinned (use a dated revision); capabilities not verified | verified |

## 7. Depth and 3D

| Model | Task | Paper (arXiv) | Repo / HF id | Licence | Typical use | Gotcha | Status |
|---|---|---|---|---|---|---|---|
| Depth Anything v1 | depth | 2401.10891 | HF `LiheYoung/depth_anything_vitl14` (no licence tag) | UNVERIFIED | historical | superseded | UNVERIFIED |
| Depth Anything V2 | depth | 2406.09414 | github `DepthAnything/Depth-Anything-V2` (Apache-2.0 repo); HF `depth-anything/Depth-Anything-V2-Small-hf` (apache-2.0), `...-Base-hf` and `...-Large-hf` (cc-by-nc-4.0), `...-Metric-Indoor-Large-hf` (no licence tag) | **Small Apache-2.0; Base and Large CC-BY-NC** (non-commercial); Metric-Indoor-Large carries no tag | relative depth, edge-friendly Small | the licence differs by checkpoint size, which is the classic trap; default output is relative (affine-invariant) not metric | verified |
| Depth Anything 3 | depth / multi-view | 2511.10647 | github `ByteDance-Seed/Depth-Anything-3`; HF `depth-anything/DA3-LARGE-1.1`, `depth-anything/DA3METRIC-LARGE`, `depth-anything/DA3-LARGE` | mixed: `DA3-LARGE-1.1` and `DA3METRIC-LARGE` Apache-2.0; original `DA3-LARGE` cc-by-nc-4.0 (non-commercial); repo Apache-2.0 | multi-view depth/pose, metric depth | `DA3-LARGE` vs `DA3-LARGE-1.1` licences differ; not listed in Transformers docs | verified |
| Depth Pro | metric depth | 2410.02073 | HF `apple/DepthPro-hf` | apple-amlr (Apple research licence, non-OSI) | sharp metric depth, no intrinsics | non-OSI licence | verified |
| VGGT | multi-view geometry | 2503.11651 | github `facebookresearch/vggt`; HF `facebook/VGGT-1B` | custom VGGT License (repo); cc-by-nc-4.0 (weights, non-commercial) | multi-view geometry | NC weights | verified |

## 8. Keypoints, tracking, OCR, background removal

| Model | Task | Paper (arXiv) | Repo / HF id | Licence | Typical use | Gotcha | Status |
|---|---|---|---|---|---|---|---|
| ViTPose | pose | 2204.12484 | github `ViTAE-Transformer/ViTPose`; HF `usyd-community/vitpose-base-simple`, `usyd-community/vitpose-plus-base`; Transformers `vitpose.md` | Apache-2.0 | top-down human pose | top-down: needs a person detector first; boxes in, keypoints out | verified |
| RTMPose / mmpose | pose | 2303.07399 | github `open-mmlab/mmpose` (last push 2025-08) | Apache-2.0 | real-time pose | (experience) mm* stack install friction | verified |
| Sapiens | human-centric tasks | 2408.12569 | github `facebookresearch/sapiens`; HF `facebook/sapiens-pose-0.3b` | CC-BY-NC (repo); cc-by-nc-4.0 (weights); non-commercial | research | non-commercial | verified |
| RF-DETR keypoints | pose | n/a | `RFDETRKeypointPreview` in rf-detr source `src/rfdetr/variants.py` | preview (no licence stated in the research file) | — | preview only per rf-detr's AGENTS.md | UNVERIFIED |
| ByteTrack, BoT-SORT, OC-SORT | MOT | 2110.06864 (ByteTrack); 2206.14651 (BoT-SORT); 2203.14360 (OC-SORT) | `roboflow/trackers`, `roboflow/supervision` | permissive: `roboflow/trackers` Apache-2.0, `roboflow/supervision` MIT | tracking-by-detection | (experience) tracker quality is bounded by detector recall/threshold; confidence threshold tuning matters more than tracker choice | UNVERIFIED |
| SAMURAI | zero-shot tracking | 2411.11922 | repo not found as `zhengyuf/SAMURAI` (UNVERIFIED) | UNVERIFIED | — | — | UNVERIFIED |
| PaddleOCR 3.0 | OCR/doc | 2507.05595 | github `PaddlePaddle/PaddleOCR` (91k stars) | Apache-2.0 | production OCR pipeline | Paddle dependency; check ONNX route | verified |
| GOT-OCR 2.0 | OCR-2.0 end-to-end | 2409.01704 | HF `stepfun-ai/GOT-OCR-2.0-hf`; Transformers `got_ocr2.md` | Apache-2.0 | formulas, tables, doc OCR | VLM-class latency | verified |
| TrOCR | line-level OCR | 2109.10282 | HF `microsoft/trocr-base-printed` (no licence tag) | UNVERIFIED | single text-line recognition | needs line crops; not a page-level OCR | UNVERIFIED |
| BiRefNet | background removal / dichotomous seg | 2401.03407 | HF `ZhengPeng7/BiRefNet` | MIT | matting-like cut-outs | — | verified |
| Recognize Anything (RAM++) | tagging | 2306.03514 (from the HF tag; title not fetched, UNVERIFIED) | HF `xinyu1205/recognize-anything-plus-model` | Apache-2.0 | image tagging | paper id from HF tag, title not fetched (UNVERIFIED) | UNVERIFIED |
| Not checked (EasyOCR, docTR, Surya, MMDetection) | — | — | MMDetection repo: Apache licence, last push 2024-08; the others not checked | UNVERIFIED | — | — | UNVERIFIED |

## Open items

Copied from "Verification log and open items" in `docs/research/01-models-and-skills.md`.

- Not checked at all (not in tables or marked UNVERIFIED): EasyOCR, docTR, Surya, Detectron2, MMDetection weights, SAM-HQ licence, MM-Grounding-DINO licence, LLMDet repo/weights, RT-DETRv4 repo/weights, YOLOv9 repo, DEIM/DEIMv2 HF weights, TrOCR licence, Depth Anything v1 licence, SAMURAI repo, SigLIP 3 (existence), PaliGemma 3 (existence), Qwen3.5-3.8 papers.
- Conflicting signal to resolve before documenting: RF-DETR plus (XLarge/2XLarge) licence. rf-detr's AGENTS.md says PML 1.0 via `rfdetr_plus`; the HF tag on `Roboflow/rf-detr-seg-xxlarge` says apache-2.0.
- DINOv3 and SAM licences: custom Meta licences. The royalty-free limited grant and trade-control clauses were confirmed, but the full text was not read for commercial restrictions, so "commercial OK?" is UNVERIFIED for both.
- A web search for "latest VLM releases" returned only aggregator blogs (e.g. mentions of DeepSeek V4-Flash-Vision-Exp, Cohere Embed 5); those claims were not used.
- Gotchas tagged "exp." are from engineering knowledge, not confirmed in the research session. They carry the `(experience)` prefix above.
