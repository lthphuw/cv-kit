# Metrics

Definitions only. This file carries no benchmark numbers.

## Detection and segmentation

**COCO AP.** Average precision per class, averaged over classes and over IoU thresholds from 0.50 to 0.95. This is the headline COCO number; "mAP" in a paper usually means this unless the paper says otherwise.

**AP50 and AP75.** AP at a single IoU threshold of 0.50 (loose localisation) or 0.75 (strict localisation). A large gap between AP50 and AP75 points to imprecise boxes rather than missed objects.

**APs, APm, APl.** COCO AP restricted to small, medium and large objects, split by object area in pixels. Use them to see whether a model fails on small objects.

**AR.** Average recall: the maximum recall for a fixed number of detections per image, averaged over classes and IoU thresholds. It says nothing about false positives.

**Box AP versus mask AP.** Box AP scores IoU between predicted and ground-truth boxes; mask AP scores IoU between masks. Mask AP is the metric for instance segmentation. Never compare a box AP with a mask AP.

**mIoU.** Mean intersection over union for semantic segmentation: per-class IoU between predicted and ground-truth pixel sets, averaged over classes.

## Classification

**Top-1 and top-5.** The share of images whose true label is the single highest-scoring class (top-1), or is among the five highest-scoring classes (top-5).

## Retrieval

**Recall@k.** The share of queries for which at least one correct item appears in the top k results. State k and the gallery size.

**Mean reciprocal rank (MRR).** The mean over queries of one divided by the rank of the first correct result. It rewards putting a correct item first.

## Latency measurement protocol

State the hardware, precision, batch size and input resolution. Warm up before timing. Synchronise the device before reading the clock (for example `torch.cuda.synchronize()` on CUDA), because kernels launch asynchronously. Report the median and a high percentile (for example p95 or p99) over many runs, not a single run or a mean. Say whether pre-processing and post-processing (resize, NMS) are included.

When comparing two numbers, they are comparable only if dataset, split, resolution, precision and hardware match.
