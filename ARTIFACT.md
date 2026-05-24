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

- 21 validation suites
- 230 scenario files
- 609 embedded records or output items
- 62,456 total evaluation rows
- 51,643/51,643 formal invariant checks passed
- 185 metric-separation evaluations
- 1,000 metric bootstrap resamples and 1,000 metric permutation shuffles
- 288/288 gate-ablation evaluations passed
- 176/176 blocked procedural claims repairable across 2,236 repair-frontier evaluations
- 217/217 jurisdiction-profile checks and 138/138 profile mutations passed
- 2,990/2,990 status-certificate replay checks passed over 230 certificates
- 230/230 scenario-regression expectations passed
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

The expected manuscript build is 33 pages in the current local format.

## Interpretation

The artifact evaluates legal-output procedural status, not legal merits. It tests whether outputs can be source-bound, reconstructed, contested, status-qualified, downgraded or withdrawn under the paper's audit protocol. Scenario-regression expectations check rule conformance and artifact integrity; public retrieval, model-output, source-anchor, adversarial, invariant, metric-separation, gate-ablation, repair-frontier, jurisdiction-profile, status-certificate, recoding and sensitivity layers test whether status allocation survives realistic upstream outputs, source-support interventions, upstream metric thresholds, procedural-gate removal, repair-path diagnosis, profile mismatch, replayed derivation checks and coding uncertainty.
