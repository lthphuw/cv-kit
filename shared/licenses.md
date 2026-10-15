# Licences

Filled from the Licence column of `catalog.md`. Check `catalog.md` for the status of each row; a licence named here is only as reliable as that row.

## 1. Licence families

| Licence family | What it means for a product | Models in the catalog that carry it |
|---|---|---|
| Permissive: Apache-2.0 | Weights and code may generally be used commercially; keep the licence and notices. Confirm per checkpoint. | SigLIP, SigLIP 2, Perception Encoder, TIPS, DINOv2, SAM, SAM 2, EdgeTAM, MobileSAM, EfficientSAM, Grounded-SAM-2, RF-DETR (nano, small, base), RT-DETR, D-FINE, LW-DETR, Grounding DINO, OWL-ViT / OWLv2, Roboflow100-VL, Gemma 4, Qwen2.5-VL (7B), Qwen3-VL, Qwen3-VL-Embedding, SmolVLM2, Moondream, Depth Anything V2 Small, Depth Anything 3 (`-1.1` and metric checkpoints), ViTPose, RTMPose / mmpose, PaddleOCR, GOT-OCR 2.0, Recognize Anything (RAM++), InternVL3 / 3.5 weights |
| Permissive: MIT | Weights and code may generally be used commercially; keep the licence text. Confirm per checkpoint. | OpenCLIP, EVA-CLIP (code and the timm checkpoint), CLIP (code only; weight licence not stated), Florence-2, BiRefNet, OneFormer, InternVL code, `roboflow/supervision` |
| Copyleft: AGPL-3.0 | Strong copyleft that the research notes reaches network use, so a hosted service built on it can carry source-disclosure duties; the Ultralytics line has a separate enterprise licence whose terms are UNVERIFIED. Get legal review before commercial use. | YOLOv10, YOLOv12, YOLO11, YOLO26, YOLOE |
| Copyleft: GPL-3.0 | Copyleft: a distributed product that includes it can have to be released under GPL. Get legal review before commercial use. | YOLO-World (an Ultralytics port exists; its licence is UNVERIFIED) |
| Non-commercial: CC-BY-NC-4.0 | Not for commercial use. Research and internal evaluation only. | MetaCLIP, Depth Anything V2 Base and Large, Depth Anything 3 original `DA3-LARGE`, VGGT weights, Sapiens |
| Non-commercial: DEIMv2 | LICENSE.md says non-commercial only; commercial use needs a separate licence. The Transformers port does not change this (legal reading UNVERIFIED). | DEIMv2 |
| Gated custom licence (Meta) | Access is gated on Hugging Face and the terms are a custom licence: a royalty-free limited grant plus trade-control clauses were seen, but the full text was not read, so commercial terms are UNVERIFIED. | DINOv3 ("DINOv3 License"), SAM 3 / 3.1 ("SAM License") |
| Gated custom licence (Gemma) | Gated download under Gemma terms; read the terms before shipping. | PaliGemma, PaliGemma 2 |
| Custom, non-OSI, research | Custom licences that are not OSI-approved; read before shipping commercially. | MobileCLIP / MobileCLIP2 and Depth Pro (apple-amlr), SegFormer repo (NVIDIA Source Code License), VGGT repo (custom VGGT License) |
| Inherited from the base LLM | The licence follows the LLM the VLM is built on. | LLaVA-1.5 (`llava-hf/llava-1.5-7b-hf` is the Llama 2 licence) |
| Mixed or tagged `other` | The Hugging Face tag is `other` or differs between checkpoints; read the card. | Mask2Former and SegFormer checkpoints, `Qwen3.8-Flash-Next` |
| Conflicting sources | Two sources disagree; treat as unresolved until checked. | RF-DETR XLarge / 2XLarge plus models and RF-DETR-Seg largest sizes: conflicting sources: PML 1.0 vs Apache-2.0 |
| Not stated or not checked | No licence tag, or the licence was not read: `licence UNVERIFIED`. | CLIP weights, Depth Anything v1, TrOCR, MM-Grounding-DINO, YOLOv9, LLMDet, SAM-HQ, SAMURAI, and the rows marked UNVERIFIED in `catalog.md` |

Per-checkpoint traps to remember:

- Depth Anything V2: Small is Apache-2.0, Base and Large are CC-BY-NC.
- Depth Anything 3: `DA3-LARGE-1.1` and the metric checkpoint are Apache-2.0, the original `DA3-LARGE` is CC-BY-NC.
- OpenCLIP: weight licences differ per checkpoint (MobileCLIP2 weights are `apple-amlr`).
- LLaVA: the licence follows the LLM base.
- Qwen: per-size licences vary.

## 2. Rule

State the licence beside every recommendation; if unchecked write `licence UNVERIFIED`.

## 3. Disclaimer

This file is engineering guidance, not legal advice; read the licence text before shipping.
