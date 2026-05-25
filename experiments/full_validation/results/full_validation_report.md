# Full Legal AI Audit Harness Validation

Validation suites: 27
Scenario files: 246
Base embedded records/items: 679 (10 stress scenarios, 120 public metadata records, 60 public-system records, 169 public retrieval records, 126 holdout records/items, 10 raw model outputs, 10 source-supported model-output variants, 70 evidence-ladder model-output variants, 60 adversarial source-support variants, 19 issue-specific public output/source records, 5 mixed-authority source-screening packets, 20 issue ablations)
Strict/lenient recoded evaluations: 492
Annotation-uncertainty perturbations: 61500
Score-blinded coding-pass evaluations: 444
Full-threshold sensitivity evaluations: 1230
Source-chain attack variants: 270/270 passed; high-upstream attacked variants blocked 270/270
Contestation challenge variants: 270/270 passed; valid challenges blocked 216/216; unsupported controls preserved 54/54
Public source-text anchor checks: 30/30 verified across 30 records with text snapshots
Model-output transcript locator checks: 50/50 verified across 10 raw transcript sections
Formal invariant checks: 51643/51643 passed
Metric separation evaluations: 201 upstream-metric scenario packets; high-recall blocked outputs 144/197
Metric statistical resamples: 1000 bootstrap resamples and 1000 permutation shuffles
Baseline rule comparisons: 2772 predictions across 12 rules; best simplified false positives 38; reference rule false positives 0
Gate ablation evaluations: 336/336 passed over 54 qualified packets
Repair frontier evaluations: 184/184 blocked claims repairable across 4474 counterfactual repairs
Jurisdiction-profile evaluations: 233/233 profile checks supported; 162/162 counterfactual mutations passed
Ranking-visibility checks: 884 rank-window checks over 230 high-status claims; 76/76 rank-order counterfactuals downgraded with coverage preserved; top-3 counter visible 183/217; drifted top-3 counter visible 0/76; median first counter rank 3.0
Status certificate replay checks: 3198/3198 passed over 246 certificates
Derived robustness evaluations: 130265
Scenario-regression expectations passed: 246/246
High-upstream-performance but procedurally blocked scenarios: 622
Blocked reason distribution: authority_omission: 59, contestation_failure: 55, counter_material_suppression: 135, invalid_authority: 1, jurisdiction_assumption_gap: 54, ranking_drift: 9, source_attribution_gap: 213, summary_distortion: 129, unauthorized_action: 10
Annotation robustness: 234/246 stable across base, strict and lenient coding policies
Annotation uncertainty: 61500 score perturbations; sample stability 0.933; qualified high-status stability 0.924; boundary scenarios 143
Score-blinded coding: 222 packets, 2 coding passes, 0.99 coder-coder exact agreement, 0.99 coder-coder kappa, 0.96 coder-coder weighted kappa, 0.95 minimum base-coder exact agreement, 0.97 minimum base-coder weighted agreement, 0.92 minimum base-coder kappa, 0.90 minimum base-coder weighted kappa

| Suite | Evidence role | Embedded records/items | Files/evals | Rule/stability | Mean score | Mean recall | Blocked high-upstream | Status distribution |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Protocol stress scenarios | construct test | 10 stress scenarios | 10 | 10/10 | 8.30 | 0.84 | 3 | decision_support_reason: 2, no_external_legal_effect: 2, normative_material_screening_output: 3, professional_support_output: 1, reference_information: 2 |
| Public legal-record metadata | public-source reconstruction | 120 public metadata records | 6 | 6/6 | 8.67 | n/a | 0 | professional_support_output: 6 |
| Public legal-system outputs | public-output audit | 60 visible public-system records | 6 | 6/6 | 8.67 | n/a | 0 | professional_support_output: 6 |
| Issue-specific public output/source packets | mixed public-output/source audit | 19 issue-specific public output/source records | 3 | 3/3 | 9.67 | 0.44 | 0 | normative_material_screening_output: 1, reference_information: 2 |
| Endpoint-matched public retrieval benchmark | endpoint-compatible public-output benchmark | 169 public search result records | 22 | 22/22 | 9.05 | 0.23 | 1 | reference_information: 22 |
| Out-of-sample holdout validation | frozen-protocol holdout validation | 126 holdout output records/items | 24 | 24/24 | 9.71 | 0.77 | 9 | normative_material_screening_output: 8, reference_information: 16 |
| Raw Codex GPT-5.5 xhigh outputs | model-output audit | 10 raw model outputs | 10 | 10/10 | 9.00 | 1.00 | 10 | reference_information: 10 |
| Source-supported model-output repairs | model-output intervention | 10 source-supported model-output variants | 10 | 10/10 | 11.00 | 1.00 | 0 | normative_material_screening_output: 10 |
| Model-output evidence ladder | controlled model-output intervention | 70 evidence-ladder model-output variants | 70 | 70/70 | 10.57 | 1.00 | 40 | decision_support_reason: 10, no_external_legal_effect: 10, normative_material_screening_output: 10, professional_support_output: 10, reference_information: 30 |
| Adversarial source-support repairs | negative-control model-output validation | 60 adversarial source-support variants | 60 | 60/60 | 8.83 | 1.00 | 60 | no_external_legal_effect: 20, reference_information: 40 |
| Mixed-authority public source-screening packets | mixed-authority construct test | 5 curated issue packets | 5 | 5/5 | 11.00 | 1.00 | 0 | normative_material_screening_output: 5 |
| Issue-defined ablations | negative-control construct test | 20 issue-packet ablations | 20 | 20/20 | 10.50 | 0.92 | 13 | normative_material_screening_output: 5, reference_information: 15 |
| Qualified-output source-chain attacks | whole-matrix source-chain negative control | 270 attack variants over qualified packets | 270 | 270/270 | 11.28 | 0.99 | 270 | no_external_legal_effect: 108, reference_information: 162 |
| Dynamic contestation challenges | whole-matrix challenge-response validation | 270 challenge variants over qualified packets | 270 | 270/270 | 11.28 | 0.99 | 216 | decision_support_reason: 12, normative_material_screening_output: 42, reference_information: 216 |
| Public source-text anchors | external source-grounding check | 30 public source-support anchor checks | 30 | 30/30 verified | n/a | n/a | n/a | records_with_text_snapshot: 30, verified_ratio: 1.0 |
| Model-output transcript anchors | raw-output provenance check | 50 raw transcript locator checks | 50 | 50/50 verified | n/a | n/a | n/a | all_locators_verified: True, output_units: 40, scenario_sections_verified: 10 |
| Formal invariant verification | exhaustive model-property check | 51643 generated audit-policy states | 51643 | 51643/51643 passed | n/a | n/a | n/a | authority_gate_necessity: 0, counter_material_gate_necessity: 0, decision_adoption_necessity: 0, evidence_packet_necessity: 0, failure_cap_absorption: 0, gate_non_substitutability: 0, gated_monotonicity: 0, metric_non_equivalence: 0, role_cap_dominance: 0 |
| Metric separation analysis | retrieval/status non-equivalence check | 201 upstream-metric scenario packets | 201 | recall-threshold precision 0.27; reference gate FP 0 | n/a | n/a | n/a | high_recall_blocked_rate: 0.73, recall_point_biserial: 0.06, reference_gate_false_positive: 0 |
| Baseline rule comparison | alternative-policy comparison | 2772 baseline predictions over 12 rules | 2772 | best simplified FP 38; reference rule FP 0 | n/a | n/a | n/a | best_simplified_precision: 0.59, best_simplified_recall: 1.0, reference_rule_false_negative: 0, reference_rule_false_positive: 0, simplified_rules_with_errors: 1 |
| Qualified-output gate ablations | counterfactual gate-necessity check | 336 ablations over 54 qualified packets | 336 | 336/336 | n/a | n/a | n/a | missing_counter_material: 0, missing_decision_adoption: 0, missing_evidence_packet: 0, missing_high_authority: 0, missing_review_gate: 0, nonprocedural_source_tags: 0, professional_role_cap: 0 |
| Blocked-claim repair frontiers | counterfactual repair-necessity check | 4474 repair counterfactuals over 184 blocked claims | 4474 | 184/184 repairable | n/a | n/a | n/a | 1: 108, 2: 34, 3: 39, 4: 3 |
| Jurisdiction-profile mutations | cross-profile gate check | 395 profile checks and counterfactuals | 395 | 233/233 profile checks; 162/162 mutations | n/a | n/a | n/a | generic_preserved: 54, mismatch_downgraded: 54, missing_downgraded: 54 |
| Ranking-visibility diagnostics | rank-salience counterfactual check | 884 rank-window checks over 230 high-status claims plus 76 rank-order counterfactuals | 960 | 76/76 rank-order | n/a | n/a | n/a | counterfactual_front_window_counter_visible: 0, coverage_preserved: 76, downgraded: 76, front_window_counter_not_visible: 34, front_window_counter_visible: 183, mean_reciprocal_first_counter_rank: 0.43, median_first_counter_rank: 3.0, rank_intervention_applied: 76 |
| Status certificate replay | derivation-certificate check | 3198 replay checks over 246 certificates | 3198 | 3198/3198 | n/a | n/a | n/a | cap_or_failure_transitions: 158, verified_certificates: 246 |
| Annotation robustness recoding | coding robustness | 492 strict/lenient recoded evaluations | 246 | 234/246 stable across all policies | n/a | n/a | n/a | base_vs_lenient_weighted_agreement: 0.98, base_vs_strict_weighted_agreement: 1.0 |
| Annotation uncertainty Monte Carlo | score-noise robustness | 61500 score-perturbed evaluations | 61500 | 0.933 sample stability; 0.924 qualified high-status stability | n/a | n/a | n/a | boundary_scenarios: 143, exact_stable_scenarios: 102, high_status_stable_scenarios: 183, mean_status_rank_shift: 0.086 |
| Score-blinded dual coding | codebook reproducibility | 222 packets x 2 coding passes | 222 | 0.99 coder kappa; 0.92 min base kappa | n/a | n/a | n/a | coder_cohen_kappa: 0.99, coder_exact_status_agreement: 0.99, coder_quadratic_weighted_kappa: 0.96, coder_weighted_status_agreement: 0.99, min_base_cohen_kappa: 0.92, min_base_exact_status_agreement: 0.95, min_base_quadratic_weighted_kappa: 0.9, min_base_weighted_status_agreement: 0.97, status_disagreements: 2 |

## Findings

- **Protocol stress scenarios:** Tests downgrade, withdrawal, decision-support and high-recall-but-blocked behavior.
- **Public legal-record metadata:** Tests source reconstruction across six public legal-record sources.
- **Public legal-system outputs:** Tests ordered real upstream legal-output reconstruction.
- **Issue-specific public output/source packets:** Tests public issue-search outputs and a source-bound public-source packet against high-authority and counter-material requirements.
- **Endpoint-matched public retrieval benchmark:** Tests public case-law or known-item outputs against authority sets that the endpoint is capable of returning, while recording mixed-authority gaps separately.
- **Out-of-sample holdout validation:** Tests withheld public-retrieval packets, raw model-output packets and source-bound repair packets after freezing the scoring policy.
- **Raw Codex GPT-5.5 xhigh outputs:** Tests whether strong authority coverage without source binding remains procedurally capped.
- **Source-supported model-output repairs:** Tests whether model-output variants can qualify after manifest, locator, issue-set, rank-salience and hashed source-support evidence validation.
- **Model-output evidence ladder:** Tests model-output variants across raw, source-bound, counter-material, rank-salience, contestability, logging, authorized-adoption and unauthorized-action conditions.
- **Adversarial source-support repairs:** Tests whether source-support repair gates reject locator mismatches, unsupported claims, contradiction patterns, out-of-manifest sources, missing output links and counter-material omissions.
- **Mixed-authority public source-screening packets:** Tests normative material screening with mixed statute/case/source packets rather than single-endpoint public search results.
- **Issue-defined ablations:** Tests whether high-authority omissions, counter-material suppression, unverified source tags and missing adoption gates trigger the expected caps.
- **Qualified-output source-chain attacks:** Mutates locators, output-source links, procedural source tags, high-authority recall and counter-material recall across every qualified packet; all attacked variants must downgrade or withdraw despite high scores and high upstream recall.
- **Dynamic contestation challenges:** Applies valid counter-material, source-verification, jurisdiction and contestability-channel challenges plus unsupported challenge controls across every qualified packet; valid challenges must block high status while unsupported challenges preserve it.
- **Public source-text anchors:** Checks issue-manifest support terms against extracted public source text snapshots to reduce manifest-only source-support circularity.
- **Model-output transcript anchors:** Checks that raw model-output scenario locators are anchored in the committed transcript sections.
- **Formal invariant verification:** Exhaustively tests monotonicity, evidence-packet necessity, authority-set necessity, counter-material necessity, adoption necessity, role caps, failure caps and metric non-equivalence.
- **Metric separation analysis:** Quantifies that upstream precision, recall and F1 are weak predictors of procedural qualification, while audit gates remove high-recall false positives.
- **Baseline rule comparison:** Compares recall, F1, total-score, source-bound and review-gate substitutes against the protocol-defined reference allocation, showing that every simplified rule either over-admits or misses procedurally qualified packets.
- **Qualified-output gate ablations:** Removes evidence, source-tag, authority, counter-material, review, role-cap and adoption gates from qualified packets and verifies that status falls below the corresponding procedural level.
- **Blocked-claim repair frontiers:** Computes the minimal artefact-gate families needed to upgrade each blocked normative-screening or decision-support claim.
- **Jurisdiction-profile mutations:** Tests that high-status outputs preserve status under valid generic profile assumptions but downgrade when jurisdiction assumptions are absent or profile-mismatched.
- **Ranking-visibility diagnostics:** Computes a rank-window visibility curve for counter-material salience and applies rank-order counterfactuals where the packet contains enough non-counter material to move counter-material below the visibility window.
- **Status certificate replay:** Generates and replays machine-readable status certificates for every scenario so status allocation can be audited from scenario hash, score candidate, role cap, failure cap and final status.
- **Annotation robustness recoding:** Tests whether status allocation survives strict and lenient recoding of the same evidence packets.
- **Annotation uncertainty Monte Carlo:** Perturbs all six audit scores under a fixed-seed Monte Carlo model to locate boundary cases and test whether status allocation is robust to plausible coding noise.
- **Score-blinded dual coding:** Tests chance-corrected score-blinded coder reliability and how far status assignments track the base harness allocation.

## Full-Threshold Sensitivity

All 246 scenario packets were re-evaluated under normative thresholds 8--12.

| Normative threshold | Decision threshold | Status flips from default | Promotions | Demotions | Status distribution |
| ---: | ---: | ---: | ---: | ---: | --- |
| 8 | 10 | 0 | 0 | 0 | decision_support_reason: 12, no_external_legal_effect: 32, normative_material_screening_output: 42, professional_support_output: 23, reference_information: 137 |
| 9 | 10 | 0 | 0 | 0 | decision_support_reason: 12, no_external_legal_effect: 32, normative_material_screening_output: 42, professional_support_output: 23, reference_information: 137 |
| 10 | 11 | 0 | 0 | 0 | decision_support_reason: 12, no_external_legal_effect: 32, normative_material_screening_output: 42, professional_support_output: 23, reference_information: 137 |
| 11 | 12 | 2 | 0 | 2 | decision_support_reason: 12, no_external_legal_effect: 32, normative_material_screening_output: 40, professional_support_output: 25, reference_information: 137 |
| 12 | 13 | 49 | 0 | 49 | no_external_legal_effect: 32, normative_material_screening_output: 17, professional_support_output: 60, reference_information: 137 |
