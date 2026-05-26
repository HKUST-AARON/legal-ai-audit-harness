# Artifact Replication Guide

This repository is the companion artifact for the paper. It contains the audit harness, scenario packets, committed public snapshots, raw model-output transcripts, validation scripts and generated Markdown/JSON reports.

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

- 47 validation suites
- 264 scenario files
- 697 embedded records or output items
- 8,023,761 validation operations, with scenario rows, generated counterfactuals, finite-state edges, substitute-rule predictions and replay checks reported separately
- 51,646/51,646 formal invariant checks passed
- 466,560 high-status claim-attempt states, 3,499,200 cover edges and 3,732,480 substitute-rule predictions
- 1019/1019 status-lattice high-status necessity checks and 1019/1019 gate-ablation drops passed
- 219 metric-separation evaluations
- 1,000 metric bootstrap resamples and 1,000 metric permutation shuffles
- 3,252 baseline-rule predictions across 13 alternative status rules
- 3,014 issue-family holdout predictions across 5 leave-one-out issue families, with 0 full-protocol holdout false positives, 0 full-protocol holdout false negatives and 38 best-trained simplified-rule holdout false positives
- 110,568 multi-axis generalization predictions across 34 holdout folds on 6 axes, with 0 full-protocol holdout false positives, 0 full-protocol holdout false negatives and 510 best-trained simplified-rule holdout false positives
- 42,192 policy-family robustness evaluations across 12 policy variants, with 0 high-status promotions and 449 best-simplified-rule false positives
- a substitute-theory falsification summary for performance, source-label, authority-material, review-label, score and model-identity sufficiency, with 0 full-protocol false positives and 0 full-protocol false negatives
- 390/390 gate-ablation evaluations passed
- 390/390 gate-contrast witness pairs passed with 390/390 score/metric/role preservation and 390/390 status separation
- 1,953/1,953 source-chain attack variants passed
- 315/315 contestation challenge variants passed
- 1,233/1,233 metamorphic policy tests passed
- 15/15 policy mutants killed across 3,111 mutation evaluations
- 627/627 review-provenance checks passed: 402/402 review/adoption placebos blocked, 189/189 high-status provenance defects blocked and 36/36 decision-provenance defects demoted
- 1,080/1,080 claim-anchor mutations passed across 250 output units and 290 output links
- 2,904/2,904 workflow-portability checks passed: 1,320/1,320 architecture invariance checks, 1,056/1,056 entitlement-cap checks, 264/264 decision-dependency checks and 264/264 unaccountable external bars
- 193/193 blocked procedural claims repairable across 5,097 repair-frontier evaluations
- 251/251 jurisdiction-profile checks and 189/189 profile mutations passed
- 956 rank-window visibility checks over 248 high-status claims
- 85/85 rank-order visibility counterfactuals downgraded with coverage preserved
- 6,072/6,072 status-certificate replay checks and 4,488/4,488 proof obligations passed over 264 proof-carrying certificates
- 5,811/5,811 certificate tamper-resistance cases rejected across 25 families
- 4,752/4,752 policy-constants replay checks passed
- 1,320/1,320 model-identity substitutions passed with 0 status changes and 0 disposition changes
- 30 query-perturbation variants across 5 issue groups; 5/5 status-stable groups, 3/5 authority-coverage unstable groups and 4/5 record-set unstable groups
- 315 query portfolios plus 5 group frontier summaries across 5 issue groups; 0/315 qualified, 56/315 full high-authority portfolios and 0/315 full counter-material portfolios
- 40/40 construct-operationalization checks passed across 10 core constructs and 31 evidence layers
- 32/32 threat-model coverage checks passed across 8 validity threats and 30 evidence layers
- 66,000 annotation-uncertainty perturbations with 0.937 sample stability
- score-blinded coding inter-coder minimum dimension kappa 0.93, minimum derived failure-flag exact agreement 0.97, minimum derived missing-gate exact agreement 0.98, weakest base-dimension kappa 0.37 on Q, base-dimension minimum exact agreement 0.87, minimum three-category PABAK 0.81 and maximum mean absolute score drift 0.13
- 264/264 scenario-regression expectations passed
- 30/30 public source-text anchors verified
- 50/50 raw model-output transcript locators verified
- 36/36 cross-engine transcript locators verified across 3 model engines and 3 issue families

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

The expected manuscript build is 41 pages in the current local format.

## Submission Package

The double-anonymous manuscript is `manuscript/ai_law_case_recommendation_verifiability.tex` and its generated PDF. The non-anonymous title page and statements template is `submission/title_page_and_declarations.md`; fill its author-specific fields in the Springer submission interface or separate title-page upload rather than in the reviewer manuscript.

## Interpretation

The artifact evaluates legal-output procedural status. It tests whether outputs can be source-bound, claim-anchored, reconstructed, contested, status-qualified, downgraded or withdrawn under the paper's audit protocol. Scenario-regression expectations check rule conformance and artifact integrity; public retrieval, raw model-output, cross-engine model-output, source-anchor, adversarial, invariant, status-lattice, metric-separation, issue-family generalization, multi-axis holdout generalization, policy-family robustness, gate-ablation, gate-contrast witness, source-chain attack, contestation challenge, policy-constants replay, metamorphic policy, policy-mutation, review-provenance, claim-anchor, workflow portability, model-identity invariance, query-perturbation, query-portfolio, construct-operationalization coverage, threat-model coverage, repair-frontier, jurisdiction-profile, ranking-visibility, proof-carrying status certificates, certificate tamper-resistance, recoding, score-uncertainty and sensitivity layers test whether status allocation survives realistic upstream outputs, source-support interventions, high-status claim-attempt state exhaustion, upstream metric thresholds, cross-issue and cross-stratum holdout testing, policy-threshold and gate-configuration variation, procedural-gate removal, score/metric/role-preserving gate contrast, source-chain falsification, dynamic contestation, second-implementation replay from JSON policy constants, expected-label-free policy transformations, killed gate-removal and status-conferring policy mutants, review/adoption label falsification without a contestability-channel record, claim-level source-anchor falsification, architecture and deployment-role portability, identity-label substitution under a fixed legal-material chain, query reformulation, query expansion, construct-to-evidence coverage, validity-threat coverage, repair-path diagnosis, profile mismatch, ranking drift, replayed derivation checks, tampered proof objects and coding uncertainty.
