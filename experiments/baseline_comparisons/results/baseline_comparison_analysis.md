# Baseline Rule Comparison

Scenario packets: 246
Qualified packets under the full audit model: 54
Baseline rules: 12
Baseline predictions: 2772
Simplified rules with at least one error: True

Best simplified rule by F1: Source-bound score candidate with review gate (precision 0.59, recall 1.00, false positives 38, false negatives 0)
Lowest-false-positive simplified rule: Source-bound score candidate with review gate (false positives 38, false negatives 0)

| Rule | Denom. | Precision | Recall | Specificity | F1 | FP | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Recall >= 0.8 | 201 | 0.27 | 1.00 | 0.03 | 0.42 | 144 | 0 |
| F1 >= 0.8 | 201 | 0.27 | 1.00 | 0.01 | 0.42 | 146 | 0 |
| Precision >= 0.8 | 201 | 0.27 | 1.00 | 0.01 | 0.42 | 146 | 0 |
| Total score >= 9 | 246 | 0.24 | 1.00 | 0.09 | 0.38 | 174 | 0 |
| All dimensions present and total >= 9 | 246 | 0.27 | 1.00 | 0.24 | 0.43 | 146 | 0 |
| Source-bound output evidence | 246 | 0.43 | 1.00 | 0.62 | 0.60 | 72 | 0 |
| Review gate and role ready | 246 | 0.27 | 1.00 | 0.22 | 0.42 | 149 | 0 |
| Source-bound evidence plus recall >= 0.8 | 201 | 0.52 | 1.00 | 0.68 | 0.69 | 48 | 0 |
| Source-bound score candidate with counter-material | 246 | 0.52 | 0.96 | 0.75 | 0.68 | 48 | 2 |
| Source-bound score candidate with review gate | 246 | 0.59 | 1.00 | 0.80 | 0.74 | 38 | 0 |
| Source-bound evidence, counter-material and review gate | 246 | 0.47 | 0.96 | 0.70 | 0.63 | 58 | 2 |
| Full audit gate function | 246 | 1.00 | 1.00 | 1.00 | 1.00 | 0 | 0 |
