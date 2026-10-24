# Questions to ask of a reported CV result

Questions only: this file states no numbers and no effect sizes. A scout answers each question for its candidate under `caveats` in its evidence file, with a locator or `no information`. "No information" is a concern, not a pass.

1. **Split.** Which split holds the number (val, test-dev, a held-out test set)? Was anything tuned on that same split?
2. **Data overlap.** Did the model see extra training or pre-training data the baselines did not? Does the paper say whether the evaluation images could be in that data?
3. **Protocol.** Are resolution, test-time augmentation, multi-scale testing, score threshold, maximum detections and NMS settings stated, and the same as for the baselines?
4. **Baselines.** Were the baseline numbers re-run in the same code and schedule, or copied from older papers? Same backbone size, schedule length and compute?
5. **Latency.** Does the timing state hardware, precision, batch, resolution and whether pre- and post-processing are timed? Does it say how it warmed up and synchronised the device, and does it give a median or a percentile over many runs? Who measured it, on which hardware?
6. **Spread.** How many runs or seeds? Is any spread reported, or one best run?
7. **Selective reporting.** Are all the paper's benchmarks shown, or a chosen subset? Is a weak result moved to the appendix?
8. **Ablation.** Does the ablation remove the claimed mechanism, or only change a hyperparameter next to it?
9. **Versions.** Which arXiv version, camera-ready paper, README or model card holds the number? Did it change between them?
10. **Reproducibility.** Are code and weights released at a commit that matches the table, and under which licence? Has anyone independent reproduced it, and do repository issues report a failure to reproduce?
11. **Other explanation.** What is the strongest other explanation of the gain (a bigger backbone, more data, a longer schedule, test-time augmentation)?

The report's TL;DR states a confidence word for the pick: `high` only when an independent reproduction exists and no answer above is a concern; `medium` with one concern; `low` otherwise.
