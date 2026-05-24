# Full Legal AI Audit Harness Validation

Validation suites: 10
Scenario files: 72
Base embedded records/items: 343 (10 stress scenarios, 120 public metadata records, 60 public-system records, 99 public retrieval records, 10 raw model outputs, 19 issue-specific public output/source records, 5 issue-defined positive controls, 20 issue ablations)
Strict/lenient recoded evaluations: 144
Score-blinded coding-pass evaluations: 144
Full-threshold sensitivity evaluations: 360
Composite validation observations: 991
Expected outcomes passed: 72/72
High-upstream-performance but procedurally blocked scenarios: 26
Annotation robustness: 70/72 stable across base, strict and lenient coding policies
Score-blinded coding: 72 packets, 2 coding passes, 0.97 coder-coder exact agreement, 0.85 minimum base-coder exact agreement, 0.92 minimum base-coder weighted agreement

| Suite | Embedded records/items | Files/evals | Rule/stability | Mean score | Mean recall | Blocked high-upstream | Status distribution |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Protocol stress scenarios | 10 stress scenarios | 10 | 10/10 | 8.30 | 0.84 | 3 | decision_support_reason: 2, no_external_legal_effect: 2, normative_material_screening_output: 3, professional_support_output: 1, reference_information: 2 |
| Public legal-record metadata | 120 public metadata records | 6 | 6/6 | 8.67 | n/a | 0 | professional_support_output: 6 |
| Public legal-system outputs | 60 visible public-system records | 6 | 6/6 | 8.67 | n/a | 0 | professional_support_output: 6 |
| Issue-specific public output/source packets | 19 issue-specific public output/source records | 3 | 3/3 | 9.67 | 0.44 | 0 | normative_material_screening_output: 1, reference_information: 2 |
| Public retrieval benchmark | 99 public search result records | 12 | 12/12 | 9.00 | 0.11 | 0 | reference_information: 12 |
| Raw Codex GPT-5.5 xhigh outputs | 10 raw model outputs | 10 | 10/10 | 9.00 | 1.00 | 10 | reference_information: 10 |
| Issue-defined positive controls | 5 curated issue packets | 5 | 5/5 | 11.00 | 1.00 | 0 | normative_material_screening_output: 5 |
| Issue-defined ablations | 20 issue-packet ablations | 20 | 20/20 | 10.50 | 0.92 | 13 | normative_material_screening_output: 5, reference_information: 15 |
| Annotation robustness recoding | 144 strict/lenient recoded evaluations | 72 | 70/72 stable across all policies | n/a | n/a | n/a | base_vs_lenient_weighted_agreement: 1.0, base_vs_strict_weighted_agreement: 0.98 |
| Score-blinded dual coding | 72 packets x 2 coding passes | 72 | 0.97 coder agreement; 0.85 min base agreement | n/a | n/a | n/a | coder_weighted_status_agreement: 0.98, min_base_weighted_status_agreement: 0.92, status_disagreements: 2 |

## Findings

- **Protocol stress scenarios:** Tests downgrade, withdrawal, decision-support and high-recall-but-blocked behavior.
- **Public legal-record metadata:** Tests source reconstruction across six public legal-record sources.
- **Public legal-system outputs:** Tests ordered real upstream legal-output reconstruction.
- **Issue-specific public output/source packets:** Tests public issue-search outputs and a source-bound public-source packet against high-authority and counter-material requirements.
- **Public retrieval benchmark:** Tests true public search outputs against issue-defined high-authority and counter-material gold sets.
- **Raw Codex GPT-5.5 xhigh outputs:** Tests whether strong authority coverage without source binding remains procedurally capped.
- **Issue-defined positive controls:** Tests normative material screening with source-bound high-authority and counter-material sets.
- **Issue-defined ablations:** Tests whether high-authority omissions, counter-material suppression, unverified source tags and missing adoption gates trigger the expected caps.
- **Annotation robustness recoding:** Tests whether status allocation survives strict and lenient recoding of the same evidence packets.
- **Score-blinded dual coding:** Tests whether score-blinded coders agree with each other and how far their status assignments track the base harness allocation.

## Full-Threshold Sensitivity

All 72 scenario packets were re-evaluated under normative thresholds 8--12.

| Normative threshold | Decision threshold | Status flips from default | Promotions | Demotions | Status distribution |
| ---: | ---: | ---: | ---: | ---: | --- |
| 8 | 10 | 0 | 0 | 0 | decision_support_reason: 2, no_external_legal_effect: 2, normative_material_screening_output: 14, professional_support_output: 13, reference_information: 41 |
| 9 | 10 | 0 | 0 | 0 | decision_support_reason: 2, no_external_legal_effect: 2, normative_material_screening_output: 14, professional_support_output: 13, reference_information: 41 |
| 10 | 11 | 0 | 0 | 0 | decision_support_reason: 2, no_external_legal_effect: 2, normative_material_screening_output: 14, professional_support_output: 13, reference_information: 41 |
| 11 | 12 | 2 | 0 | 2 | decision_support_reason: 2, no_external_legal_effect: 2, normative_material_screening_output: 12, professional_support_output: 15, reference_information: 41 |
| 12 | 13 | 11 | 0 | 11 | no_external_legal_effect: 2, normative_material_screening_output: 7, professional_support_output: 22, reference_information: 41 |
