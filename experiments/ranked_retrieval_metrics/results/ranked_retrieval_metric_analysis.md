# Ranked Retrieval Metric Analysis

Scenario packets: 264
Ranked packets with known relevant authority sets: 258
Procedurally qualified outputs: 63
Metric threshold predictions: 1806

## Point-Biserial Correlation With Procedural Qualification

| Metric | Correlation |
| --- | ---: |
| precision_at_5 | 0.27 |
| recall_at_5 | 0.27 |
| recall_at_10 | 0.25 |
| average_precision | 0.25 |
| reciprocal_rank | 0.16 |
| ndcg_at_5 | 0.22 |
| ndcg_at_10 | 0.21 |

## Threshold Tests

| Predictor | TP | FP | TN | FN | Precision | Recall | Specificity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| precision_at_5>=0.8 | 63 | 147 | 48 | 0 | 0.30 | 1.00 | 0.25 |
| recall_at_5>=0.8 | 61 | 135 | 60 | 2 | 0.31 | 0.97 | 0.31 |
| recall_at_10>=0.8 | 61 | 139 | 56 | 2 | 0.30 | 0.97 | 0.29 |
| average_precision>=0.8 | 61 | 141 | 54 | 2 | 0.30 | 0.97 | 0.28 |
| reciprocal_rank>=0.8 | 63 | 175 | 20 | 0 | 0.26 | 1.00 | 0.10 |
| ndcg_at_5>=0.8 | 63 | 158 | 37 | 0 | 0.29 | 1.00 | 0.19 |
| ndcg_at_10>=0.8 | 63 | 160 | 35 | 0 | 0.28 | 1.00 | 0.18 |

## Best Single-Metric Rule

Best threshold rule: recall_at_5>=0.8 with 135 false positives and 2 false negatives.

## High-Metric Blocked Outputs

| Metric | Blocked | Denominator | Blocked rate | Invalid treatment hits |
| --- | ---: | ---: | ---: | ---: |
| precision_at_5 | 147 | 210 | 0.70 | 0 |
| recall_at_5 | 135 | 196 | 0.69 | 0 |
| recall_at_10 | 139 | 200 | 0.69 | 0 |
| average_precision | 141 | 202 | 0.70 | 0 |
| reciprocal_rank | 175 | 238 | 0.74 | 0 |
| ndcg_at_5 | 158 | 221 | 0.71 | 0 |
| ndcg_at_10 | 160 | 223 | 0.72 | 0 |

## Bootstrap and Permutation Robustness

Bootstrap resamples: 1000 with seed 20526.
nDCG@10 point-biserial permutation p-value: 0.001.

| Metric | 2.5% | Median | 97.5% |
| --- | ---: | ---: | ---: |
| ndcg_at_10_blocked_rate | 0.66 | 0.72 | 0.77 |
| ndcg_at_10_point_biserial | 0.17 | 0.21 | 0.26 |
| ndcg_at_10_threshold_precision | 0.23 | 0.28 | 0.34 |
