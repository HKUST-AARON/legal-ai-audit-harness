# Full Legal AI Audit Harness Validation

Validation suites: 15
Scenario files: 230
Base embedded records/items: 609 (10 stress scenarios, 120 public metadata records, 60 public-system records, 225 public retrieval records, 10 raw model outputs, 10 source-supported model-output variants, 70 evidence-ladder model-output variants, 60 adversarial source-support variants, 19 issue-specific public output/source records, 5 mixed-authority source-screening packets, 20 issue ablations)
Strict/lenient recoded evaluations: 460
Score-blinded coding-pass evaluations: 460
Full-threshold sensitivity evaluations: 1150
Public source-text anchor checks: 30/30 verified across 30 records with text snapshots
Model-output transcript locator checks: 50/50 verified across 10 raw transcript sections
Derived robustness evaluations: 2150
Expected outcomes passed: 230/230
High-upstream-performance but procedurally blocked scenarios: 128
Blocked reason distribution: authority_omission: 5, contestation_failure: 1, counter_material_suppression: 27, invalid_authority: 1, source_attribution_gap: 95, summary_distortion: 21, unauthorized_action: 10
Annotation robustness: 218/230 stable across base, strict and lenient coding policies
Score-blinded coding: 230 packets, 2 coding passes, 0.99 coder-coder exact agreement, 0.95 minimum base-coder exact agreement, 0.97 minimum base-coder weighted agreement

| Suite | Evidence role | Embedded records/items | Files/evals | Rule/stability | Mean score | Mean recall | Blocked high-upstream | Status distribution |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Protocol stress scenarios | construct test | 10 stress scenarios | 10 | 10/10 | 8.30 | 0.84 | 3 | decision_support_reason: 2, no_external_legal_effect: 2, normative_material_screening_output: 3, professional_support_output: 1, reference_information: 2 |
| Public legal-record metadata | public-source reconstruction | 120 public metadata records | 6 | 6/6 | 8.67 | n/a | 0 | professional_support_output: 6 |
| Public legal-system outputs | public-output audit | 60 visible public-system records | 6 | 6/6 | 8.67 | n/a | 0 | professional_support_output: 6 |
| Issue-specific public output/source packets | mixed public-output/source audit | 19 issue-specific public output/source records | 3 | 3/3 | 9.67 | 0.44 | 0 | normative_material_screening_output: 1, reference_information: 2 |
| Endpoint-matched public retrieval benchmark | endpoint-compatible public-output benchmark | 225 public search result records | 30 | 30/30 | 9.07 | 0.26 | 2 | reference_information: 30 |
| Raw Codex GPT-5.5 xhigh outputs | model-output audit | 10 raw model outputs | 10 | 10/10 | 9.00 | 1.00 | 10 | reference_information: 10 |
| Source-supported model-output repairs | model-output intervention | 10 source-supported model-output variants | 10 | 10/10 | 11.00 | 1.00 | 0 | normative_material_screening_output: 10 |
| Model-output evidence ladder | controlled model-output intervention | 70 evidence-ladder model-output variants | 70 | 70/70 | 10.57 | 1.00 | 40 | decision_support_reason: 10, no_external_legal_effect: 10, normative_material_screening_output: 10, professional_support_output: 10, reference_information: 30 |
| Adversarial source-support repairs | negative-control model-output validation | 60 adversarial source-support variants | 60 | 60/60 | 8.83 | 1.00 | 60 | no_external_legal_effect: 20, reference_information: 40 |
| Mixed-authority public source-screening packets | mixed-authority construct test | 5 curated issue packets | 5 | 5/5 | 11.00 | 1.00 | 0 | normative_material_screening_output: 5 |
| Issue-defined ablations | negative-control construct test | 20 issue-packet ablations | 20 | 20/20 | 10.50 | 0.92 | 13 | normative_material_screening_output: 5, reference_information: 15 |
| Public source-text anchors | external source-grounding check | 30 public source-support anchor checks | 30 | 30/30 verified | n/a | n/a | n/a | records_with_text_snapshot: 30, verified_ratio: 1.0 |
| Model-output transcript anchors | raw-output provenance check | 50 raw transcript locator checks | 50 | 50/50 verified | n/a | n/a | n/a | all_locators_verified: True, output_units: 40, scenario_sections_verified: 10 |
| Annotation robustness recoding | coding robustness | 460 strict/lenient recoded evaluations | 230 | 218/230 stable across all policies | n/a | n/a | n/a | base_vs_lenient_weighted_agreement: 0.98, base_vs_strict_weighted_agreement: 1.0 |
| Score-blinded dual coding | codebook reproducibility | 230 packets x 2 coding passes | 230 | 0.99 coder agreement; 0.95 min base agreement | n/a | n/a | n/a | coder_weighted_status_agreement: 0.99, min_base_weighted_status_agreement: 0.97, status_disagreements: 2 |

## Findings

- **Protocol stress scenarios:** Tests downgrade, withdrawal, decision-support and high-recall-but-blocked behavior.
- **Public legal-record metadata:** Tests source reconstruction across six public legal-record sources.
- **Public legal-system outputs:** Tests ordered real upstream legal-output reconstruction.
- **Issue-specific public output/source packets:** Tests public issue-search outputs and a source-bound public-source packet against high-authority and counter-material requirements.
- **Endpoint-matched public retrieval benchmark:** Tests public case-law or known-item outputs against authority sets that the endpoint is capable of returning, while recording mixed-authority gaps separately.
- **Raw Codex GPT-5.5 xhigh outputs:** Tests whether strong authority coverage without source binding remains procedurally capped.
- **Source-supported model-output repairs:** Tests whether the same model outputs can qualify after manifest, locator, issue-set and hashed source-support evidence validation.
- **Model-output evidence ladder:** Tests the same model outputs across raw, source-bound, counter-material, contestability, logging, authorized-adoption and unauthorized-action conditions.
- **Adversarial source-support repairs:** Tests whether source-support repair gates reject locator mismatches, unsupported claims, contradiction patterns, out-of-manifest sources, missing output links and counter-material omissions.
- **Mixed-authority public source-screening packets:** Tests normative material screening with mixed statute/case/source packets rather than single-endpoint public search results.
- **Issue-defined ablations:** Tests whether high-authority omissions, counter-material suppression, unverified source tags and missing adoption gates trigger the expected caps.
- **Public source-text anchors:** Checks issue-manifest support terms against extracted public source text snapshots to reduce manifest-only source-support circularity.
- **Model-output transcript anchors:** Checks that raw model-output scenario locators are anchored in the committed transcript sections.
- **Annotation robustness recoding:** Tests whether status allocation survives strict and lenient recoding of the same evidence packets.
- **Score-blinded dual coding:** Tests whether score-blinded coders agree with each other and how far their status assignments track the base harness allocation.

## Full-Threshold Sensitivity

All 230 scenario packets were re-evaluated under normative thresholds 8--12.

| Normative threshold | Decision threshold | Status flips from default | Promotions | Demotions | Status distribution |
| ---: | ---: | ---: | ---: | ---: | --- |
| 8 | 10 | 0 | 0 | 0 | decision_support_reason: 12, no_external_legal_effect: 32, normative_material_screening_output: 34, professional_support_output: 23, reference_information: 129 |
| 9 | 10 | 0 | 0 | 0 | decision_support_reason: 12, no_external_legal_effect: 32, normative_material_screening_output: 34, professional_support_output: 23, reference_information: 129 |
| 10 | 11 | 0 | 0 | 0 | decision_support_reason: 12, no_external_legal_effect: 32, normative_material_screening_output: 34, professional_support_output: 23, reference_information: 129 |
| 11 | 12 | 2 | 0 | 2 | decision_support_reason: 12, no_external_legal_effect: 32, normative_material_screening_output: 32, professional_support_output: 25, reference_information: 129 |
| 12 | 13 | 41 | 0 | 41 | no_external_legal_effect: 32, normative_material_screening_output: 17, professional_support_output: 52, reference_information: 129 |
