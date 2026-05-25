# Full Legal AI Audit Harness Validation

Validation suites: 41
Scenario files: 264
Base embedded records/items: 697 (10 stress scenarios, 120 public metadata records, 60 public-system records, 169 public retrieval records, 126 holdout records/items, 10 raw model outputs, 10 source-supported model-output variants, 9 cross-engine raw outputs, 9 cross-engine source-supported outputs, 70 evidence-ladder model-output variants, 60 adversarial source-support variants, 19 issue-specific public output/source records, 5 mixed-authority source-screening packets, 20 issue ablations)
Strict/lenient recoded evaluations: 528
Annotation-uncertainty perturbations: 66000
Score-blinded coding-pass evaluations: 480
Full-threshold sensitivity evaluations: 1320
Source-chain attack variants: 1953/1953 passed; high-upstream attacked variants blocked 1953/1953
Source-chain attack dispositions: downgrade 63, suspension 378, withdrawal 1512
Contestation challenge variants: 315/315 passed; valid challenges blocked 252/252; unsupported controls preserved 63/63
Public source-text anchor checks: 30/30 verified across 30 records with text snapshots
Model-output transcript locator checks: 50/50 verified across 10 raw transcript sections
Cross-engine transcript locator checks: 36/36 verified across 3 engines and 3 issues
Formal invariant checks: 51646/51646 passed
Status-lattice exhaustion: 466560 high-status claim-attempt states, 3499200 cover edges, 1019/1019 necessity checks and 1019/1019 gate-ablation drops
Metric separation evaluations: 219 upstream-metric scenario packets; high-recall blocked outputs 153/215
Metric statistical resamples: 1000 bootstrap resamples and 1000 permutation shuffles
Baseline rule comparisons: 3252 predictions across 13 rules; best simplified false positives 38; reference rule false positives 0
Gate ablation evaluations: 390/390 passed over 63 qualified packets
Gate-contrast witness pairs: 390/390 passed; score/metric/role preserved 390/390; status separated 390/390
Repair frontier evaluations: 193/193 blocked claims repairable across 5097 counterfactual repairs
Jurisdiction-profile evaluations: 251/251 profile checks supported; 189/189 counterfactual mutations passed
Ranking-visibility checks: 956 rank-window checks over 248 high-status claims; 85/85 rank-order counterfactuals downgraded with coverage preserved; top-3 counter visible 198/235; drifted top-3 counter visible 0/85; median first counter rank 3.0
Proof-carrying certificate replay checks: 6072/6072 passed over 264 certificates
Status certificate proof obligations: 4488/4488 passed
Certificate tamper-resistance: 5811/5811 tamper cases rejected across 25 families
Policy-constants replay checks: 4752/4752 passed over 264 packets
Metamorphic policy tests: 1233/1233 passed over 264 packets
Policy mutation analysis: 15/15 mutants killed across 3111 evaluations; invalid promotions 2264; false negatives 2
Review-provenance analysis: 627/627 passed; review/adoption placebos blocked 402/402; high-status provenance defects blocked 189/189; decision provenance defects demoted 36/36
Claim-anchor analysis: 1080/1080 passed over 250 output units and 290 output links; claim-text removals blocked 250/250; link-to-claim removals blocked 290/290; support-attestation removals withdrawn 290/290; locator removals withdrawn 250/250
Model-identity invariance: 1320/1320 identity substitutions passed over 264 packets and 5 identity profiles; status changes 0; disposition changes 0
Query-perturbation diagnostics: 30 query variants across 5 issue groups; status-stable groups 5/5; authority-coverage unstable groups 3/5; record-set unstable groups 4/5; mean record overlap 0.39
Query-portfolio frontier: 315 portfolios plus 5 group summaries across 5 issue groups; qualified portfolios 0/315; full high-authority portfolios 56/315; full counter-material portfolios 0/315
Derived robustness evaluations: 7864314
Scenario-regression expectations passed: 264/264
High-upstream-performance but procedurally blocked scenarios: 2362
Blocked reason distribution: authority_omission: 1013, contestation_failure: 103, counter_material_suppression: 1098, invalid_authority: 1, jurisdiction_assumption_gap: 63, ranking_drift: 12, source_attribution_gap: 1186, summary_distortion: 1533, unauthorized_action: 10
Annotation robustness: 262/264 stable across base, strict and lenient coding policies
Annotation uncertainty: 66000 score perturbations; sample stability 0.937; qualified high-status stability 0.916; boundary scenarios 151
Score-blinded coding: 240 packets, 2 coding passes, 0.99 coder-coder exact agreement, 0.99 coder-coder kappa, 0.96 coder-coder weighted kappa, 0.93 minimum dimension kappa, 0.97 minimum derived failure-flag exact agreement, 0.98 minimum derived missing-gate exact agreement, 0.37 minimum base-dimension kappa (Q, 0.97 exact), 0.87 minimum base-dimension exact agreement, 0.81 minimum base-dimension PABAK, 0.13 maximum base-dimension mean absolute delta, 0.95 minimum base-coder exact agreement, 0.98 minimum base-coder weighted agreement, 0.92 minimum base-coder kappa, 0.90 minimum base-coder weighted kappa

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
| Cross-engine raw model outputs | identity-neutral model-output audit | 36 cross-engine raw outputs | 9 | 9/9 | 9.00 | 1.00 | 9 | reference_information: 9 |
| Cross-engine source-supported repairs | identity-neutral source-support intervention | 36 cross-engine source-supported outputs | 9 | 9/9 | 11.00 | 1.00 | 0 | normative_material_screening_output: 9 |
| Model-output evidence ladder | controlled model-output intervention | 70 evidence-ladder model-output variants | 70 | 70/70 | 10.57 | 1.00 | 50 | decision_support_reason: 10, no_external_legal_effect: 10, normative_material_screening_output: 10, reference_information: 40 |
| Adversarial source-support repairs | negative-control model-output validation | 60 adversarial source-support variants | 60 | 60/60 | 8.83 | 1.00 | 60 | no_external_legal_effect: 20, reference_information: 40 |
| Mixed-authority public source-screening packets | mixed-authority construct test | 5 curated issue packets | 5 | 5/5 | 11.00 | 1.00 | 0 | normative_material_screening_output: 5 |
| Issue-defined ablations | negative-control construct test | 20 issue-packet ablations | 20 | 20/20 | 10.50 | 0.92 | 13 | normative_material_screening_output: 5, reference_information: 15 |
| Qualified-output source-chain attacks | whole-matrix source-chain negative control | 1953 attack variants over qualified packets | 1953 | 1953/1953 | 11.24 | 0.99 | 1953 | no_external_legal_effect: 1512, reference_information: 441 |
| Dynamic contestation challenges | whole-matrix challenge-response validation | 315 challenge variants over qualified packets | 315 | 315/315 | 11.24 | 0.99 | 252 | decision_support_reason: 12, normative_material_screening_output: 51, reference_information: 252 |
| Public source-text anchors | external source-grounding check | 30 public source-support anchor checks | 30 | 30/30 verified | n/a | n/a | n/a | records_with_text_snapshot: 30, verified_ratio: 1.0 |
| Model-output transcript anchors | raw-output provenance check | 50 raw transcript locator checks | 50 | 50/50 verified | n/a | n/a | n/a | all_locators_verified: True, output_units: 40, scenario_sections_verified: 10 |
| Cross-engine transcript anchors | identity-neutral raw-output provenance check | 36 cross-engine transcript locator checks | 36 | 36/36 verified | n/a | n/a | n/a | all_locators_verified: True, engines: 3, issues: 3, scenario_sections_verified: 9 |
| Formal invariant verification | exhaustive model-property check | 51646 generated audit-policy states | 51646 | 51646/51646 passed | n/a | n/a | n/a | authority_gate_necessity: 0, claim_anchor_necessity: 0, contestability_channel_necessity: 0, counter_material_gate_necessity: 0, decision_adoption_necessity: 0, evidence_packet_necessity: 0, failure_cap_absorption: 0, gate_non_substitutability: 0, gated_monotonicity: 0, metric_non_equivalence: 0, role_cap_dominance: 0 |
| Status-lattice exhaustion | finite status-lattice characterization | 466560 high-status claim-attempt states, 3499200 cover edges and 3732480 substitute-rule predictions | 7700278 | 1019/1019 necessity; 1019/1019 ablations | n/a | n/a | n/a | best_partial_rule_false_positive: 672, decision_status_states: 11, full_predicate_false_positive: 0, high_status_states: 168 |
| Metric separation analysis | retrieval/status non-equivalence check | 219 upstream-metric scenario packets | 219 | recall-threshold precision 0.29; reference gate FP 0 | n/a | n/a | n/a | high_recall_blocked_rate: 0.71, recall_point_biserial: 0.06, reference_gate_false_positive: 0 |
| Baseline rule comparison | alternative-policy comparison | 3252 baseline predictions over 13 rules | 3252 | best simplified FP 38; reference rule FP 0 | n/a | n/a | n/a | best_simplified_precision: 0.62, best_simplified_recall: 1.0, reference_rule_false_negative: 0, reference_rule_false_positive: 0, simplified_rules_with_errors: 1 |
| Qualified-output gate ablations | counterfactual gate-necessity check | 390 ablations over 63 qualified packets | 390 | 390/390 | n/a | n/a | n/a | missing_counter_material: 0, missing_decision_adoption: 0, missing_evidence_packet: 0, missing_high_authority: 0, missing_review_gate: 0, nonprocedural_source_tags: 0, professional_role_cap: 0 |
| Gate-contrast witness pairs | non-substitution witness validation | 390 witness pairs over 63 qualified packets | 390 | 390/390 | n/a | n/a | n/a | normative_material_screening_output: 12, reference_information: 378 |
| Blocked-claim repair frontiers | counterfactual repair-necessity check | 5097 repair counterfactuals over 193 blocked claims | 5097 | 193/193 repairable | n/a | n/a | n/a | 1: 98, 2: 50, 3: 41, 4: 3, 5: 1 |
| Jurisdiction-profile mutations | cross-profile gate check | 440 profile checks and counterfactuals | 440 | 251/251 profile checks; 189/189 mutations | n/a | n/a | n/a | generic_preserved: 63, mismatch_downgraded: 63, missing_downgraded: 63 |
| Ranking-visibility diagnostics | rank-salience counterfactual check | 956 rank-window checks over 248 high-status claims plus 85 rank-order counterfactuals | 1041 | 85/85 rank-order | n/a | n/a | n/a | counterfactual_front_window_counter_visible: 0, coverage_preserved: 85, downgraded: 85, front_window_counter_not_visible: 37, front_window_counter_visible: 198, mean_reciprocal_first_counter_rank: 0.43, median_first_counter_rank: 3.0, rank_intervention_applied: 85 |
| Proof-carrying status certificates | proof-carrying certificate replay | 6072 replay checks and 4488 proof obligations over 264 certificates | 10560 | 6072/6072 checks; 4488/4488 obligations | n/a | n/a | n/a | cap_or_failure_transitions: 177, proof_obligations: 4488, proof_obligations_passed: 4488, verified_certificates: 264 |
| Certificate tamper-resistance | proof-certificate negative-control validation | 5811 tamper cases across 25 families | 5811 | 5811/5811 rejected | n/a | n/a | n/a | base_certificates: 264, missed_tamper_cases: 0, tamper_families: 25 |
| Policy-constants replay | second implementation check | 4752 replay checks over 264 packets | 4752 | 4752/4752 | n/a | n/a | n/a | decision_support_reason: 12, no_external_legal_effect: 32, normative_material_screening_output: 51, professional_support_output: 13, reference_information: 156 |
| Metamorphic policy tests | expected-label-free policy-invariant validation | 1233 transformations over 264 packets | 1233 | 1233/1233 | n/a | n/a | n/a | back_office_role_cap: 264, benign_source_append_preserves_high_status: 63, claim_escalation_nonpromotion: 264, review_gate_removal_blocks_high_status: 63, score_and_role_inflation_without_adoption: 252, source_tag_deproceduralization_blocks_high_status: 63, upstream_metric_inflation_invariance: 264 |
| Policy mutation analysis | policy-mutant killing | 3111 mutation evaluations over 15 policy mutants | 3111 | 15/15 killed | n/a | n/a | n/a | classification_errors: 2266, false_negatives: 2, invalid_promotions: 2264 |
| Review-provenance analysis | human-review and adoption-record falsification | 627 provenance evaluations over 264 packets | 627 | 627/627 | n/a | n/a | n/a | decision_provenance_defects_demoted: 36, high_status_provenance_defects_blocked: 189, review_adoption_placebos_blocked: 402 |
| Claim-anchor analysis | claim-level source-anchor falsification | 1080 claim-anchor mutations over 250 units and 290 links | 1080 | 1080/1080 | n/a | n/a | n/a | claim_text_absence_blocked: 250, link_unit_binding_absence_blocked: 290, locator_absence_withdrawn: 250, support_attestation_absence_withdrawn: 290 |
| Model-identity invariance | identity-substitution invariance check | 1320 identity mutations over 264 packets and 5 model identities | 1320 | 1320/1320 | n/a | n/a | n/a | disposition_changes: 0, identity_profiles: 5, status_changes: 0 |
| Query-perturbation stability | public-retrieval query-sensitivity diagnostic | 30 query variants across 5 issue groups | 30 | 5/5 status-stable groups | n/a | n/a | 2 | authority_unstable_groups: 3, counter_recall_unstable_groups: 0, mean_record_overlap: 0.39, min_record_overlap: 0.0, record_set_unstable_groups: 4, top_result_unstable_groups: 4 |
| Query-portfolio frontier | public-retrieval query-expansion frontier | 315 query portfolios plus 5 group frontier summaries | 320 | 0/315 portfolios qualified | n/a | n/a | n/a | full_counter_material_portfolios: 0, full_high_authority_portfolios: 56, full_screening_material_portfolios: 0, groups_counter_repaired: 0, groups_high_repaired: 1, max_authority_coverage: 1.0, max_counter_recall: 0.0 |
| Annotation robustness recoding | coding robustness | 528 strict/lenient recoded evaluations | 264 | 262/264 stable across all policies | n/a | n/a | n/a | base_vs_lenient_weighted_agreement: 1.0, base_vs_strict_weighted_agreement: 1.0 |
| Annotation uncertainty Monte Carlo | score-noise robustness | 66000 score-perturbed evaluations | 66000 | 0.937 sample stability; 0.916 qualified high-status stability | n/a | n/a | n/a | boundary_scenarios: 151, exact_stable_scenarios: 112, high_status_stable_scenarios: 203, mean_status_rank_shift: 0.085 |
| Score-blinded dual coding | codebook reproducibility | 240 packets x 2 coding passes | 240 | 0.99 coder kappa; 0.37 weakest base-dimension kappa (Q); 0.87 min base-dimension exact; 0.13 max score drift | n/a | n/a | n/a | base_dimension_max_mean_absolute_delta: 0.13, base_dimension_min_exact_agreement: 0.87, base_dimension_min_kappa: 0.37, base_dimension_min_kappa_coder: coder_a, base_dimension_min_kappa_dimension: Q, base_dimension_min_kappa_exact_agreement: 0.97, base_dimension_min_pabak: 0.81, coder_cohen_kappa: 0.99, coder_exact_status_agreement: 0.99, coder_quadratic_weighted_kappa: 0.96, coder_weighted_status_agreement: 0.99, min_base_cohen_kappa: 0.92, min_base_exact_status_agreement: 0.95, min_base_quadratic_weighted_kappa: 0.9, min_base_weighted_status_agreement: 0.98, minimum_dimension_kappa: 0.93, minimum_failure_flag_exact_agreement: 0.97, minimum_missing_gate_exact_agreement: 0.98, status_disagreements: 2 |

## Substitute-Theory Falsification

| Substitute theory | Scenario false positives | Scenario false negatives | Scenario precision | Scenario recall | Lattice false positives | Lattice false negatives | Full protocol false positives | Full protocol false negatives | Additional evidence |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Performance sufficiency | 153 | 0 | 0.29 | 1.00 | n/a | n/a | 0 | 0 | 153/215 high-recall outputs were blocked below normative screening |
| Source-label sufficiency | 72 | 0 | 0.47 | 1.00 | 6552 | 0 | 0 | 0 | Source links without authority, counter-material and contestability gates over-admit outputs |
| Authority-material sufficiency | 150 | 2 | 0.29 | 0.97 | 672 | 0 | 0 | 0 | Authority and counter-material coverage without source-chain, role and contestability gates over-admit outputs |
| Review-label sufficiency | 149 | 0 | 0.30 | 1.00 | 19800 | 0 | 0 | 0 | Review labels without source-chain and failure-cap gates over-admit outputs |
| Score sufficiency | 183 | 0 | 0.26 | 1.00 | 49752 | 0 | 0 | 0 | High total score cannot substitute for missing legal-material predicates |
| Model-identity sufficiency | 1005 | 0 | 0.24 | 1.00 | n/a | n/a | 0 | 0 | 1005/1320 identity-labelled rows would be over-admitted; identity substitution produced 0 status changes |

## Findings

- **Protocol stress scenarios:** Tests downgrade, withdrawal, decision-support and high-recall-but-blocked behavior.
- **Public legal-record metadata:** Tests source reconstruction across six public legal-record sources.
- **Public legal-system outputs:** Tests ordered real upstream legal-output reconstruction.
- **Issue-specific public output/source packets:** Tests public issue-search outputs and a source-bound public-source packet against high-authority and counter-material requirements.
- **Endpoint-matched public retrieval benchmark:** Tests public case-law or known-item outputs against authority sets that the endpoint is capable of returning, while recording mixed-authority gaps separately.
- **Out-of-sample holdout validation:** Tests withheld public-retrieval packets, raw model-output packets and source-bound repair packets after freezing the scoring policy.
- **Raw Codex GPT-5.5 xhigh outputs:** Tests whether strong authority coverage without source binding remains procedurally capped.
- **Source-supported model-output repairs:** Tests whether model-output variants can qualify after manifest, locator, issue-set, rank-salience and hashed source-support evidence validation.
- **Cross-engine raw model outputs:** Tests whether high-recall outputs from three model engines remain capped without source-bound legal-material chains.
- **Cross-engine source-supported repairs:** Tests whether the same issue outputs qualify after source-support validation, regardless of model identity.
- **Model-output evidence ladder:** Tests model-output variants across raw, source-bound, counter-material, rank-salience, contestability, logging, authorized-adoption and unauthorized-action conditions.
- **Adversarial source-support repairs:** Tests whether source-support repair gates reject locator mismatches, unsupported claims, contradiction patterns, out-of-manifest sources, missing output links and counter-material omissions.
- **Mixed-authority public source-screening packets:** Tests normative material screening with mixed statute/case/source packets rather than single-endpoint public search results.
- **Issue-defined ablations:** Tests whether high-authority omissions, counter-material suppression, unverified source tags and missing adoption gates trigger the expected caps.
- **Qualified-output source-chain attacks:** Applies every nonempty combination of locator, output-source link, procedural source tag, high-authority recall and counter-material recall attacks across every qualified packet; all attacked variants must lose high status through downgrade, suspension or withdrawal despite high scores and high upstream recall.
- **Dynamic contestation challenges:** Applies valid counter-material, source-verification, jurisdiction and contestability-channel challenges plus unsupported challenge controls across every qualified packet; valid challenges must block high status while unsupported challenges preserve it.
- **Public source-text anchors:** Checks issue-manifest support terms against extracted public source text snapshots to reduce manifest-only source-support circularity.
- **Model-output transcript anchors:** Checks that raw model-output scenario locators are anchored in the committed transcript sections.
- **Cross-engine transcript anchors:** Checks that cross-engine raw-output locators are anchored in committed transcripts across three model engines.
- **Formal invariant verification:** Exhaustively tests monotonicity, evidence-packet necessity, authority-set necessity, counter-material necessity, adoption necessity, role caps, failure caps and metric non-equivalence.
- **Status-lattice exhaustion:** Exhausts the high-status claim-attempt lattice and shows that score, role, source and authority substitutes over-admit unless the full screening predicate is present.
- **Metric separation analysis:** Quantifies that upstream precision, recall and F1 are weak predictors of procedural qualification, while audit gates remove high-recall false positives.
- **Baseline rule comparison:** Compares recall, F1, total-score, source-bound, authority-material and review-gate substitutes against the protocol-defined reference allocation, showing that every simplified rule either over-admits or misses procedurally qualified packets.
- **Qualified-output gate ablations:** Removes evidence, source-tag, authority, counter-material, review, role-cap and adoption gates from qualified packets and verifies that status falls below the corresponding procedural level.
- **Gate-contrast witness pairs:** Preserves each qualified packet's audit score vector, upstream metrics and system role while flipping one mandatory gate; every witness pair separates allowed procedural status, proving score-only and retrieval-metric-only substitutes cannot reproduce the protocol on the validation domain.
- **Blocked-claim repair frontiers:** Computes the minimal artefact-gate families needed to upgrade each blocked normative-screening or decision-support claim.
- **Jurisdiction-profile mutations:** Tests that high-status outputs preserve status under valid generic profile assumptions but downgrade when jurisdiction assumptions are absent or profile-mismatched.
- **Ranking-visibility diagnostics:** Computes a rank-window visibility curve for counter-material salience and applies rank-order counterfactuals where the packet contains enough non-counter material to move counter-material below the visibility window.
- **Proof-carrying status certificates:** Generates proof-carrying status certificates for every scenario and replays scenario identity, scenario hash, policy hash, policy body, jurisdiction profile, score gate, role cap, missing gates, failure cap, metric bundle, claim support, proof obligations and derivation hash.
- **Certificate tamper-resistance:** Mutates certificate identities, hashes, policy bodies, scores, roles, gates, status fields, caps, metric bundles, proof obligations and certificate-set structure; every tampered proof object must be rejected.
- **Policy-constants replay:** Recomputes score candidates, role caps, protected reliance gates, missing gates, failure caps, metrics and final status in a separate script parameterized by JSON policy constants without importing the harness model.
- **Metamorphic policy tests:** Applies claim escalation, metric inflation, role-cap demotion, source-tag mutation, review-gate removal, score-and-role inflation without adoption, and benign-source augmentation to primary scenario packets without using expected labels.
- **Policy mutation analysis:** Applies gate-removal and status-conferring policy mutants across committed packets; every mutant is killed because removing a required gate, ignoring a cap, or treating metrics, source labels, review labels, total score or model identity as status produces a wrong allocation.
- **Review-provenance analysis:** Adds review and adoption labels to incomplete packets and removes review, contestability, jurisdiction, authorization, adoption-reason or contestation-record fields from qualified packets; status follows provenance records only when the legal-material chain is complete.
- **Claim-anchor analysis:** Removes material proposition text, link-to-claim bindings, support attestations and locators from every qualified packet; high status survives only when each material output unit remains bound to a specific source anchor.
- **Model-identity invariance:** Substitutes frontier, legal-specialist, open-weight, small-model and undisclosed-agentic identity labels across every packet; procedural status remains unchanged because model identity is not a status-conferring property.
- **Query-perturbation stability:** Compares issue-equivalent public-search query variants and holdout variants, showing whether authority coverage, counter-material recall, top-result identity and retrieved-record sets remain stable under query reformulation.
- **Query-portfolio frontier:** Enumerates all non-empty query portfolios over issue-equivalent public retrieval variants to test whether frozen query expansion recovers high-authority and counter-material coverage.
- **Annotation robustness recoding:** Tests whether status allocation survives strict and lenient recoding of the same evidence packets.
- **Annotation uncertainty Monte Carlo:** Perturbs all six audit scores under a fixed-seed Monte Carlo model to locate boundary cases and test whether status allocation is robust to plausible coding noise.
- **Score-blinded dual coding:** Tests score-blinded coder reliability, base-status tracking and dimension-level score calibration under class imbalance.

## Full-Threshold Sensitivity

All 264 scenario packets were re-evaluated under normative thresholds 8--12.

| Normative threshold | Decision threshold | Status flips from default | Promotions | Demotions | Status distribution |
| ---: | ---: | ---: | ---: | ---: | --- |
| 8 | 10 | 0 | 0 | 0 | decision_support_reason: 12, no_external_legal_effect: 32, normative_material_screening_output: 51, professional_support_output: 13, reference_information: 156 |
| 9 | 10 | 0 | 0 | 0 | decision_support_reason: 12, no_external_legal_effect: 32, normative_material_screening_output: 51, professional_support_output: 13, reference_information: 156 |
| 10 | 11 | 0 | 0 | 0 | decision_support_reason: 12, no_external_legal_effect: 32, normative_material_screening_output: 51, professional_support_output: 13, reference_information: 156 |
| 11 | 12 | 2 | 0 | 2 | decision_support_reason: 12, no_external_legal_effect: 32, normative_material_screening_output: 49, professional_support_output: 15, reference_information: 156 |
| 12 | 13 | 58 | 0 | 58 | no_external_legal_effect: 32, normative_material_screening_output: 17, professional_support_output: 59, reference_information: 156 |
