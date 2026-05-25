# Metric Separation Analysis

Scenario packets: 264
Scenario packets with upstream precision/recall/F1: 219
Procedurally qualified outputs: 62

## Point-Biserial Correlation With Procedural Qualification

| Metric | Correlation |
| --- | ---: |
| precision | 0.15 |
| recall | 0.06 |
| f1 | 0.14 |

## Threshold Tests

| Predictor | TP | FP | TN | FN | Precision | Recall | Specificity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| precision>=0.8 | 62 | 155 | 2 | 0 | 0.29 | 1.00 | 0.01 |
| recall>=0.8 | 62 | 153 | 4 | 0 | 0.29 | 1.00 | 0.03 |
| f1>=0.8 | 62 | 155 | 2 | 0 | 0.29 | 1.00 | 0.01 |

## Gate Cascade

| Predictor | TP | FP | TN | FN | Precision | Recall | Specificity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| recall>=0.8 | 62 | 153 | 4 | 0 | 0.29 | 1.00 | 0.03 |
| + score candidate | 62 | 121 | 36 | 0 | 0.34 | 1.00 | 0.23 |
| + source bound | 62 | 28 | 129 | 0 | 0.69 | 1.00 | 0.82 |
| + review role | 62 | 18 | 139 | 0 | 0.78 | 1.00 | 0.89 |
| + no failure cap | 62 | 0 | 157 | 0 | 1.00 | 1.00 | 1.00 |

## Bootstrap and Permutation Robustness

Bootstrap resamples: 1000 with seed 10506.
Recall point-biserial permutation p-value: 0.354.

| Metric | 2.5% | Median | 97.5% |
| --- | ---: | ---: | ---: |
| high_recall_blocked_rate | 0.65 | 0.71 | 0.77 |
| recall_point_biserial | -0.05 | 0.07 | 0.14 |
| recall_threshold_precision | 0.23 | 0.29 | 0.35 |

## High-Recall Blocked Outputs

High-recall outputs blocked below normative screening: 153/215 (0.71).

Failure flags: authority_omission: 5, contestation_failure: 40, counter_material_suppression: 25, invalid_authority: 1, ranking_drift: 12, source_attribution_gap: 115, summary_distortion: 21, unauthorized_action: 10
Status distribution: no_external_legal_effect: 31, reference_information: 122
