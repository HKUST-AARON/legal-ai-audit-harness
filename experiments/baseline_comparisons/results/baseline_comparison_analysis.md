# Baseline Rule Comparison

Scenario packets: 264
Qualified packets under the full audit model: 63
Baseline rules: 13
Baseline predictions: 3252
Simplified rules with at least one reproduction error: True
Target label: protocol-defined reference allocation.

Best simplified rule by F1: Source-bound score candidate with review gate (precision 0.62, recall 1.00, false positives 38, false negatives 0)
Lowest-false-positive simplified rule: Source-bound score candidate with review gate (false positives 38, false negatives 0)

| Rule | Denom. | Precision | Recall | Specificity | F1 | Reproduction FP | Reproduction FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Recall >= 0.8 | 219 | 0.29 | 1.00 | 0.03 | 0.45 | 153 | 0 |
| F1 >= 0.8 | 219 | 0.29 | 1.00 | 0.01 | 0.44 | 155 | 0 |
| Precision >= 0.8 | 219 | 0.29 | 1.00 | 0.01 | 0.44 | 155 | 0 |
| Total score >= 9 | 264 | 0.26 | 1.00 | 0.09 | 0.41 | 183 | 0 |
| All dimensions present and total >= 9 | 264 | 0.29 | 1.00 | 0.23 | 0.45 | 155 | 0 |
| Source-bound output evidence | 264 | 0.47 | 1.00 | 0.64 | 0.64 | 72 | 0 |
| Review gate and role ready | 264 | 0.30 | 1.00 | 0.26 | 0.46 | 149 | 0 |
| High-authority and counter-material coverage | 264 | 0.29 | 0.97 | 0.25 | 0.45 | 150 | 2 |
| Source-bound evidence plus recall >= 0.8 | 219 | 0.56 | 1.00 | 0.69 | 0.72 | 48 | 0 |
| Source-bound score candidate with counter-material | 264 | 0.56 | 0.97 | 0.76 | 0.71 | 48 | 2 |
| Source-bound score candidate with review gate | 264 | 0.62 | 1.00 | 0.81 | 0.77 | 38 | 0 |
| Source-bound evidence, counter-material and review gate | 264 | 0.51 | 0.97 | 0.71 | 0.67 | 58 | 2 |
| Full audit gate reference allocation | 264 | 1.00 | 1.00 | 1.00 | 1.00 | 0 | 0 |
