# Metric Separation Analysis

Scenario packets: 246
Scenario packets with upstream precision/recall/F1: 201
Procedurally qualified outputs: 53

## Point-Biserial Correlation With Procedural Qualification

| Metric | Correlation |
| --- | ---: |
| precision | 0.12 |
| recall | 0.06 |
| f1 | 0.11 |

## Threshold Tests

| Predictor | TP | FP | TN | FN | Precision | Recall | Specificity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| precision>=0.8 | 53 | 146 | 2 | 0 | 0.27 | 1.00 | 0.01 |
| recall>=0.8 | 53 | 144 | 4 | 0 | 0.27 | 1.00 | 0.03 |
| f1>=0.8 | 53 | 146 | 2 | 0 | 0.27 | 1.00 | 0.01 |

## Gate Cascade

| Predictor | TP | FP | TN | FN | Precision | Recall | Specificity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| recall>=0.8 | 53 | 144 | 4 | 0 | 0.27 | 1.00 | 0.03 |
| + score candidate | 53 | 112 | 36 | 0 | 0.32 | 1.00 | 0.24 |
| + source bound | 53 | 28 | 120 | 0 | 0.65 | 1.00 | 0.81 |
| + review role | 53 | 18 | 130 | 0 | 0.75 | 1.00 | 0.88 |
| + no failure cap | 53 | 0 | 148 | 0 | 1.00 | 1.00 | 1.00 |

## Bootstrap and Permutation Robustness

Bootstrap resamples: 1000 with seed 10506.
Recall point-biserial permutation p-value: 0.434.

| Metric | 2.5% | Median | 97.5% |
| --- | ---: | ---: | ---: |
| full_gate_precision | 1.00 | 1.00 | 1.00 |
| full_gate_specificity | 1.00 | 1.00 | 1.00 |
| high_recall_blocked_rate | 0.67 | 0.73 | 0.79 |
| recall_point_biserial | -0.07 | 0.06 | 0.15 |
| recall_threshold_precision | 0.21 | 0.27 | 0.33 |

## High-Recall Blocked Outputs

High-recall outputs blocked below normative screening: 144/197 (0.73).

Failure flags: authority_omission: 5, contestation_failure: 1, counter_material_suppression: 25, invalid_authority: 1, ranking_drift: 9, source_attribution_gap: 105, summary_distortion: 21, unauthorized_action: 10
Status distribution: no_external_legal_effect: 31, professional_support_output: 10, reference_information: 103
