# Artifact Replication Guide

This repository is the companion artifact for the paper. It contains the audit harness, scenario packets, committed public snapshots, raw model-output transcript, validation scripts and generated Markdown/JSON reports.

## Environment

- Python 3.12 or later
- No LLM API key is required
- Public snapshots are committed for deterministic reruns; collectors use `--refresh` only when explicitly requested

Optional editable install:

```bash
python -m pip install -e .
```

## Primary Replication Command

```bash
python scripts/run_full_validation.py
python scripts/verify_claim_consistency.py
```

Expected aggregate output:

- 29 validation suites
- 246 scenario files
- 679 embedded records or output items
- 136,260 total evaluation rows
- 51,643/51,643 formal invariant checks passed
- 201 metric-separation evaluations
- 1,000 metric bootstrap resamples and 1,000 metric permutation shuffles
- 2,772 baseline-rule predictions across 12 alternative status rules
- 336/336 gate-ablation evaluations passed
- 270/270 source-chain attack variants passed
- 270/270 contestation challenge variants passed
- 1,134/1,134 metamorphic policy tests passed
- 184/184 blocked procedural claims repairable across 4,474 repair-frontier evaluations
- 233/233 jurisdiction-profile checks and 162/162 profile mutations passed
- 884 rank-window visibility checks over 230 high-status claims
- 76/76 rank-order visibility counterfactuals downgraded with coverage preserved
- 3,198/3,198 status-certificate replay checks passed over 246 certificates
- 4,182/4,182 policy-constants replay checks passed
- 61,500 annotation-uncertainty perturbations with 0.933 sample stability
- 246/246 scenario-regression expectations passed
- 30/30 public source-text anchors verified
- 50/50 raw model-output transcript locators verified

The aggregate reports are written to:

```text
experiments/full_validation/results/full_validation_report.md
experiments/full_validation/results/full_validation_report.json
```

## Additional Verification

```bash
python -m unittest discover -s tests
pytest -q
```

Compile the manuscript from the `manuscript/` directory:

```bash
pdflatex ai_law_case_recommendation_verifiability.tex
pdflatex ai_law_case_recommendation_verifiability.tex
```

The expected manuscript build is 35 pages in the current local format.

## Interpretation

The artifact evaluates legal-output procedural status, not legal merits. It tests whether outputs can be source-bound, reconstructed, contested, status-qualified, downgraded or withdrawn under the paper's audit protocol. Scenario-regression expectations check rule conformance and artifact integrity; public retrieval, model-output, source-anchor, adversarial, invariant, metric-separation, gate-ablation, source-chain attack, contestation challenge, policy-constants replay, metamorphic policy, repair-frontier, jurisdiction-profile, ranking-visibility, status-certificate, recoding, score-uncertainty and sensitivity layers test whether status allocation survives realistic upstream outputs, source-support interventions, upstream metric thresholds, procedural-gate removal, source-chain falsification, dynamic contestation, second-implementation replay from JSON policy constants, expected-label-free policy transformations, repair-path diagnosis, profile mismatch, ranking drift, replayed derivation checks and coding uncertainty.
