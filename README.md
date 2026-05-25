# Legal AI Audit Harness

A lightweight scoring harness for legal AI outputs above any search, retrieval, generation, agent, database, or manual review stack.

The harness operationalizes a verifiability-based audit model for deciding whether a legal AI output should remain an internal reference, qualify as professional support, qualify as a normative material screening output, or be treated as a decision-support reason only after accountable human adoption.

## Model

Each scenario contains a human-coded audit vector with six dimensions scored from `0` to `2`:

| Code | Dimension |
| --- | --- |
| `S` | Source and corpus verifiability |
| `Q` | Query and version traceability |
| `H` | Authority-hierarchy representation |
| `K` | Ranking and counter-material verifiability |
| `T` | Contestability support |
| `L` | Adoption logging and audit responsibility |

The harness computes:

```text
PS(o) = g(E(o), R(o), A(o))
A(o) = (S, Q, H, K, T, L)
```

It applies gate rules and computes derived checks including authority coverage, counter-authority recall, output-evidence metrics, source-attribution coverage, human-review gates, and downgrade, suspension or withdrawal triggers. It is an output-status audit layer, not a legal merits evaluator.

The repository follows a local-first CLI and artifact-log pattern: each run is reproducible from local scenario files, produces Markdown/JSON artifacts, and is checked by CI. Its legal-workflow guardrails are adapted from the public [`anthropics/claude-for-legal`](https://github.com/anthropics/claude-for-legal) design: legal AI outputs remain draft or screening artefacts until a review gate is satisfied; source links carry source tags; jurisdiction assumptions are explicit; and actions such as filing, sending, external reliance, or execution require accountable human authorization. The harness does not import or require an agent runtime, and it does not inspect upstream implementation details.

## Quick Start

```bash
python -m audit_harness.cli score examples/scenarios/court_authority_report.json
python -m audit_harness.cli run examples/scenarios --out reports/sample_report.md --json-out reports/sample_report.json
python -m audit_harness.cli experiment examples/scenarios --out reports/experiment_report.md --json-out reports/experiment_report.json
python -m audit_harness.cli sensitivity examples/scenarios --out reports/sensitivity_report.md --json-out reports/sensitivity_report.json
python scripts/collect_public_system_outputs.py
python scripts/collect_issue_public_outputs.py
python scripts/collect_public_retrieval_benchmark.py
python scripts/build_model_output_repairs.py
python scripts/build_blind_coding_packets.py
python scripts/verify_formal_invariants.py
python scripts/run_metric_separation_analysis.py
python scripts/run_baseline_comparison_analysis.py
python scripts/run_gate_ablation_analysis.py
python scripts/run_repair_frontier_analysis.py
python scripts/run_jurisdiction_profile_analysis.py
python scripts/run_ranking_visibility_analysis.py
python scripts/run_status_certificate_validation.py
python scripts/run_metamorphic_policy_tests.py
python scripts/run_blind_coding_study.py
python scripts/run_annotation_robustness.py
python scripts/run_annotation_uncertainty_analysis.py
python scripts/build_source_chain_attacks.py
python scripts/build_contestation_challenges.py
python scripts/run_full_validation.py
python scripts/verify_claim_consistency.py
python -m unittest discover -s tests
```

Installed as a package:

```bash
python -m pip install -e .
legal-ai-audit run examples/scenarios --out reports/sample_report.md
```

## Scenario Format

```json
{
  "id": "court-authority-report",
  "claimed_status": "normative_material_screening_output",
  "system_role": "auditable_procedural_tool",
  "jurisdiction_profile": "common_law",
  "scores": {
    "S": { "score": 2, "evidence": "Corpus manifest and source links are recorded." },
    "Q": { "score": 2, "evidence": "Issue, filters, source-collection version, workflow version and output identifier are recorded." },
    "H": { "score": 2, "evidence": "Binding, persuasive and invalid authorities are labelled." },
    "K": { "score": 1, "evidence": "Ranking factors are broad; counter-material recall is incomplete." },
    "T": { "score": 2, "evidence": "Reviewers can inspect and challenge the result set." },
    "L": { "score": 1, "evidence": "Adoption is logged, but reasons are not structured." }
  },
  "counter_authority": {
    "known": ["limiting-authority-a", "contrary-authority-b"],
    "retrieved": ["limiting-authority-a"]
  },
  "authority_sets": {
    "high_authority": ["binding-precedent-a"],
    "retrieved_high_authority": ["binding-precedent-a"],
    "counter_or_limiting": ["limiting-authority-a"],
    "retrieved_counter_or_limiting": ["limiting-authority-a"],
    "invalid_or_superseded": [],
    "retrieved": ["binding-precedent-a", "limiting-authority-a"]
  },
  "upstream_metrics": { "precision": 0.88, "recall": 0.83, "f1": 0.85 },
  "evidence_packet": {
    "output_links": [
      { "unit_id": "unit-1", "source_id": "binding-precedent-a", "locator": "para 3", "supports_claim": true, "source_tag": "tool_verified" }
    ],
    "output_units": [
      { "id": "unit-1", "source_ids": ["binding-precedent-a"], "locators": ["para 3"] }
    ]
  },
  "review_gate": {
    "attorney_review_required": true,
    "review_status": "completed",
    "reliance_gate": "attorney_review",
    "jurisdiction_assumptions": ["common_law"],
    "irreversible_action": false,
    "human_authorization": false
  },
  "failure_flags": [],
  "expected_allowed_status": "normative_material_screening_output",
  "expected_disposition": "none"
}
```

## Status Rules

| Allowed status | Minimum rule |
| --- | --- |
| `reference_information` | `S >= 1` and `Q >= 1` |
| `professional_support_output` | `S, Q, L >= 1` |
| `normative_material_screening_output` | all six dimensions `>= 1`, total score `>= 9`, nonempty high-authority set, `retrieved_high_authority`, `counter_or_limiting` and `retrieved_counter_or_limiting` fields, nonempty counter-materials unless `counter_material_complete=true`, output evidence packet with output units and source links, review gate with jurisdiction assumptions, and no active failure cap |
| `decision_support_reason` | all normative-screening gates, total score `>= 10`, `T = L = 2`, completed review, `authorized_adoption`, human authorization, recorded jurisdiction assumptions, adoption reasons, and contestation record |
| `no_external_legal_effect` | missing gates or withdrawal-level failures |

`system_role` caps the highest status available to an output: `back_office_tool` caps at reference, `disclosed_assistance_tool` at professional support, `auditable_procedural_tool` at normative screening, `authorized_decision_support_tool` at decision support, and `unaccountable_external_disposition` at no external legal effect. When `system_role` is omitted, the harness infers it from `review_gate.reliance_gate` and irreversible-action evidence; `claimed_status` does not raise the role cap.

Failure flags can downgrade, suspend or withdraw an output from external procedural use.

For external procedural statuses, numeric scores are never enough. The harness first assigns a score-based candidate status, then applies role caps, failure flags and withdrawal rules. It caps or downgrades an otherwise high-scoring output when authority sets are empty, output-source links are missing, evidence fidelity or coverage is incomplete, source tags are nonprocedural, counter-materials are undeclared, jurisdiction assumptions are missing, the review gate is absent, the system role is too weak, or adoption evidence is incomplete.

## Artifact Replication

For the submission artifact and one-command replication checklist, see [`ARTIFACT.md`](ARTIFACT.md). The primary deterministic command is:

```bash
python scripts/run_full_validation.py
```

## Full Validation Suite

Run the complete validation matrix with:

```bash
python scripts/run_full_validation.py
```

The full suite reruns all committed validation layers and writes:

```text
experiments/full_validation/results/full_validation_report.md
experiments/full_validation/results/full_validation_report.json
```

Current coverage:

| Layer | Embedded records/items | Purpose |
| --- | ---: | --- |
| Protocol stress scenarios | 10 | Tests downgrade, withdrawal, decision-support and high-recall-but-blocked behavior. |
| Public legal-record metadata | 120 | Tests source reconstruction across six public legal-record sources. |
| Public legal-system outputs | 60 | Tests ordered real upstream public legal-output reconstruction. |
| Issue-specific public output/source packets | 19 | Tests public issue-search outputs and a source-bound public-source packet against high-authority and counter-material requirements. |
| Endpoint-matched public retrieval benchmark | 169 | Tests public case-law or known-item outputs against authority sets the endpoint can return, while mixed-authority gaps are recorded separately. |
| Out-of-sample holdout validation | 126 | Tests withheld public-retrieval packets, raw model-output packets and source-bound repairs after the scoring policy is frozen. |
| Raw Codex GPT-5.5 xhigh outputs | 10 | Tests whether strong authority coverage without source binding remains procedurally capped. |
| Source-supported model-output repairs | 10 | Tests whether model-output variants qualify only after manifest, locator, hashed source-support excerpt, procedural source-tag, issue-set and rank-salience validation. |
| Model-output evidence ladder | 70 | Tests model-output variants across raw, source-bound, counter-material, rank-salience, contestability, logging, authorized-adoption and unauthorized-action conditions. |
| Adversarial source-support repairs | 60 | Tests whether locator mismatches, unsupported claims, contradiction patterns, out-of-manifest sources, missing output links and counter-material omissions are rejected. |
| Public source-text anchors | 30 | Checks manifest support terms against extracted public source text snapshots; current result is 30/30 verified across 30 records with snapshots. |
| Model-output transcript anchors | 50 | Checks that every raw model-output scenario locator is anchored in the committed transcript section. |
| Formal invariant verification | 51643 | Exhaustively checks monotonicity, evidence-packet necessity, authority-set necessity, counter-material gate necessity, adoption necessity, role caps, failure caps and metric non-equivalence over generated audit-policy states. |
| Metric separation analysis | 201 | Tests whether upstream precision, recall and F1 predict procedural qualification across all packets with complete upstream metrics. |
| Metric statistical robustness | 2000 | Bootstraps key metric/status separation estimates and permutes recall-status association. |
| Baseline rule comparison | 2772 | Compares recall, F1, total-score, source-bound and review-gate substitutes against the protocol-defined reference allocation over 12 alternative status rules. |
| Qualified-output gate ablations | 336 | Removes procedural gates from all qualified packets and checks that status falls below the corresponding procedural level. |
| Qualified-output source-chain attacks | 270 | Mutates locators, output-source links, procedural source tags, high-authority recall and counter-material recall across all qualified packets; current result is 270/270 loss of high status through downgrade, suspension or withdrawal. |
| Dynamic contestation challenges | 270 | Applies valid counter-material, source-verification, jurisdiction and contestability-channel challenges plus unsupported challenge controls; current result is 216/216 valid challenges blocked and 54/54 unsupported controls preserved. |
| Blocked-claim repair frontiers | 4474 | Computes the minimal artifact-gate families needed to upgrade each blocked normative-screening or decision-support claim. |
| Jurisdiction-profile mutations | 395 | Checks high-status profile support and mutates qualified packets to test missing or mismatched jurisdiction assumptions. |
| Ranking-visibility diagnostics | 884 | Computes a rank-window visibility curve over 230 high-status claims and runs 76 rank-order counterfactuals where the packet can move counter-material below the visibility window. |
| Status certificate replay | 3198 | Generates machine-readable status certificates for all 246 packets and replays hash, score-candidate, role-cap, failure-cap and metric checks. |
| Metamorphic policy tests | 1134 | Applies claim escalation, upstream-metric inflation, role-cap demotion, source-tag mutation, review-gate removal, score-and-role inflation without adoption, and benign-source augmentation without using expected labels; current result is 1134/1134 passed. |
| Mixed-authority public source-screening packets | 5 | Tests normative material screening with source-bound statute, case and public-source packets. |
| Issue-defined ablations | 20 | Tests whether high-authority omissions, counter-material suppression, unverified source tags and missing adoption gates trigger the expected caps. |
| Annotation robustness recoding | 492 | Re-scores all 246 scenario packets under strict and lenient coding policies to test status stability. |
| Annotation uncertainty Monte Carlo | 61500 | Perturbs all six audit scores under a fixed-seed noise model to locate threshold-boundary cases and test status stability under plausible coding uncertainty. |
| Score-blinded dual coding | 444 | Two coding passes score 222 non-holdout packets without original scores or expected outcomes, then compare coder-coder and base-coder agreement with chance-corrected kappa. |
| Full-threshold sensitivity | 1230 | Re-evaluates all 246 scenario packets under normative thresholds 8-12. |

The current full validation report covers 246 scenario files containing 679 embedded records/items, 30 public source-text anchor checks, 50 raw model-output transcript locator checks, 51,643 formal invariant checks, 201 metric-separation evaluations, 2,000 metric statistical resamples, 2,772 baseline-rule predictions, 336 gate-ablation evaluations, 270 source-chain attack variants, 270 contestation challenge variants, 1,134 metamorphic policy tests, 4,474 repair-frontier evaluations, 395 jurisdiction-profile checks, 884 rank-window visibility checks, 76 rank-order counterfactuals and 3,198 status-certificate replay checks, plus 61,500 score-uncertainty perturbations, strict/lenient recoding, score-blinded codebook coding and full-threshold sensitivity checks. Expected outcomes are scenario-regression checks: they verify rule conformance and artifact integrity, while the endpoint-matched public retrieval benchmark, out-of-sample holdout layer, source-supported model-output repair layer, model-output evidence ladder, public source-text anchor layer, transcript-anchor layer, formal-invariant layer, metric-separation layer, metric-statistical layer, baseline-comparison layer, gate-ablation layer, source-chain attack layer, contestation challenge layer, metamorphic policy layer, repair-frontier layer, jurisdiction-profile layer, ranking-visibility layer, status-certificate replay layer, adversarial repair layer, annotation-uncertainty layer, full-threshold sensitivity, robustness and blind-coding layers test whether status allocation survives real public search outputs, withheld packets, source-support interventions, external source anchors, negative controls, upstream metric thresholds, bootstrap/permutation uncertainty, simplified status-rule substitution, procedural-gate removal, source-chain falsification, dynamic contestation, expected-label-free policy transformations, repair-path diagnosis, profile mismatch, ranking drift, derivation replay, score perturbation, threshold changes and plausible coding disagreement. The dual-coding layer is not a substitute for future external human annotation, but it separates packet evidence from original scenario scores and expected outcomes and reports exact agreement, weighted agreement, Cohen's kappa and quadratic weighted kappa for both inter-coder and base-coder comparisons.

After running the full matrix, `python scripts/verify_claim_consistency.py` checks that the manuscript, README, artifact guide, skill and generated reports still state the same headline counts as `full_validation_report.json`.

## Jurisdiction Profiles

Profiles in `examples/jurisdiction_profiles/` parameterize `H` and `K` for different legal settings. Common-law scenarios use binding and persuasive precedent labels, while civil-law scenarios use code provisions, special statutes, high-court decisions, doctrinal views and later amendments. The scoring dimensions stay stable; the legal materials used to prove each dimension vary by profile. For high-status outputs, the review gate must also carry a jurisdiction assumption that supports the declared profile; the profile mutation analysis verifies that valid generic assumptions preserve qualified status while missing or mismatched profile assumptions downgrade it.

## Output Evidence Auditing

Scenarios can include an `evidence_packet` object with output-to-source mappings. This sits above any upstream implementation. The harness reports structural evidence fidelity, evidence coverage, source-tag coverage, and procedural-source-tag coverage. Unsupported output units are withdrawal-level failures when they claim external procedural status; missing or nonprocedural source tags downgrade external status because reviewers cannot tell whether a citation was tool-verified, officially sourced, user-verified, public metadata, or still needs verification.

The source-text anchor verifier adds an external check for issue-manifest support. It uses committed public source snapshots by default and only refreshes public pages when `--refresh` is supplied:

```bash
python scripts/verify_source_text_anchors.py
python scripts/verify_source_text_anchors.py --refresh
```

## Review Gates

Scenarios can include a `review_gate` object. It records whether attorney review is required, whether review is complete, which reliance gate applies, what jurisdiction assumptions were used, whether adoption reasons and contestation records exist, and whether an irreversible action has human authorization. An unreviewed output cannot become a decision-support reason for external reliance, and an irreversible action without human authorization is withdrawn from external legal effect.

## Real Case Experiment

The repository includes a reproducible source-integrity experiment over six public legal-record sources:

```bash
python scripts/collect_real_cases.py
python -m audit_harness.cli experiment experiments/real_cases/scenarios --out experiments/real_cases/results/real_case_experiment.md --json-out experiments/real_cases/results/real_case_experiment.json
```

By default the script uses the committed public metadata snapshots for deterministic reruns. Pass `--refresh` to download fresh snapshots. The experiment samples 20 records per jurisdiction with a fixed seed, writes source manifests, and runs the harness over the generated output evidence packets. It tests whether evidence packets can be reconstructed and audited; it does not evaluate legal merits, ranking quality or any upstream system architecture. For that reason these metadata-only packets are capped at `professional_support_output`, not `normative_material_screening_output`.

The repository also includes five mixed-authority public source-screening packets:

```bash
python -m audit_harness.cli experiment experiments/issue_gold_sets/scenarios --out experiments/issue_gold_sets/results/issue_gold_set_experiment.md --json-out experiments/issue_gold_sets/results/issue_gold_set_experiment.json
```

The current mixed-authority packets cover:

- U.S. agency statutory interpretation after `Loper Bright`, with manually curated high-authority, limiting and invalidated-treatment labels for `Loper Bright`, `Chevron`, `Skidmore`, APA `5 U.S.C. 706` and `Kisor`;
- English-law mesothelioma causation after `Fairchild`, `Barker`, the Compensation Act 2006 and `Sienkiewicz`;
- EU GDPR Article 15 access-right materials on recipients and copies of personal data, including CJEU decisions C-154/21 and C-487/21 plus regulation-based limitations;
- Canadian administrative-law standard of review after `Vavilov`, including the companion Supreme Court of Canada decisions and historical `Dunsmuir` framework;
- German/EU right-to-be-forgotten review, including the Federal Constitutional Court decisions and the EU fundamental-rights materials they interact with.

The sensitivity command varies the normative-screening threshold from 8 to 11 for a selected scenario directory. The full validation suite additionally re-evaluates all 246 scenario packets under thresholds 8-12, so threshold robustness is tested across the complete artifact rather than only the stress scenarios.

The issue-ablation suite is generated from the same issue packets:

```bash
python scripts/build_issue_ablations.py
python scripts/build_source_chain_attacks.py
python scripts/build_contestation_challenges.py
python -m audit_harness.cli experiment experiments/issue_ablations/scenarios --out experiments/issue_ablations/results/issue_ablation_experiment.md --json-out experiments/issue_ablations/results/issue_ablation_experiment.json
```

It removes or weakens one procedural condition at a time. The ablations check that partial high-authority omission, complete-set counter-material suppression, unverified source tags, and missing authorized-adoption gates cap the claimed status.

## Annotation Robustness Study

The repository includes a coding-uncertainty experiment:

```bash
python scripts/run_annotation_robustness.py
```

The script re-scores all 246 committed scenario packets under two alternative coding policies. The strict policy lowers scores when evidence is only internally reviewable, counter-material recall is incomplete, source tags are not procedural, or adoption and contestation records are absent. The lenient policy raises scores only when evidence-packet metrics, authority coverage, counter-authority recall, or review gates support the higher score. It then reports status stability, score deltas, and weighted status agreement against the base coding. This is not a substitute for a future human inter-annotator study, but it directly tests whether the protocol's status outcomes are fragile to plausible audit-vector disagreement.

## Score-Blinded Dual Coding Study

The repository includes a score-blinded coding layer:

```bash
python scripts/build_blind_coding_packets.py
python scripts/run_blind_coding_study.py
```

The packet builder strips original `scores`, `expected_allowed_status`, `expected_disposition`, source paths, and manual failure flags from 222 committed non-holdout score-blinded coding packets. The resulting packet files preserve the legal-output evidence needed for coding: claimed status, jurisdiction profile, authority sets, upstream metrics, evidence packet, review gate, deployment context and packet identifiers. This is a codebook reproducibility layer, not an external annotation study. Two separate annotation files in `experiments/blind_coding/annotations/` then score the packets under the shared codebook in `experiments/blind_coding/CODEBOOK.md`. The study reports coder-coder exact agreement, weighted agreement, Cohen's kappa, quadratic weighted kappa, base-coder agreement against the harness allocation, dimension-level agreement, and disputed packets.

## Raw Model Output Pilot

The repository includes a ten-output Codex `gpt-5.5` / `xhigh` pilot:

```bash
python -m audit_harness.cli experiment experiments/ai_outputs/scenarios --out experiments/ai_outputs/results/ai_output_experiment.md --json-out experiments/ai_outputs/results/ai_output_experiment.json
```

Raw outputs are stored in `experiments/ai_outputs/raw/codex_gpt55_xhigh_first10.md`. The pilot asks whether fluent model answers with strong authority and counter-material coverage can claim `normative_material_screening_output` status without source-support evidence. The current result is deliberately strict: all ten outputs are downgraded to `reference_information` because their citations are marked `needs_verification`.

The raw transcript verifier checks that every scenario locator extracted from the ten model outputs appears in the committed transcript section:

```bash
python scripts/verify_model_output_transcripts.py
```

The current result is 50/50 locators verified across ten raw transcript sections.

The source-supported repair layer holds the same model answers constant and runs:

```bash
python scripts/build_model_output_repairs.py
python -m audit_harness.cli experiment experiments/model_output_repairs/scenarios --out experiments/model_output_repairs/results/model_output_repair_experiment.md --json-out experiments/model_output_repairs/results/model_output_repair_experiment.json
```

The builder does not simply assign higher scores. It validates each repaired output-source link against the issue manifest, locator, hashed manifest source-support excerpt, contradiction patterns, procedural source tag and high-authority/counter-material coverage before writing `source_binding_validation` and the derived audit-vector scores. The current result is the paired contrast used in the paper: all ten raw outputs remain `reference_information`; all ten manifest-backed validator repairs qualify as `normative_material_screening_output`.

The model-output evidence ladder extends the paired contrast into seven controlled conditions over the same ten outputs:

```bash
python scripts/build_model_output_evidence_ladder.py
python -m audit_harness.cli experiment experiments/model_output_evidence_ladder/scenarios --out experiments/model_output_evidence_ladder/results/model_output_evidence_ladder_experiment.md --json-out experiments/model_output_evidence_ladder/results/model_output_evidence_ladder_experiment.json
```

The current ladder result is 70/70 expected outcomes passed: 10 decision-support reasons, 10 no-effect outputs, 10 normative-material screening outputs, 10 professional-support outputs and 30 reference-information outputs.

The adversarial repair layer then attacks the same repair gate:

```bash
python scripts/build_model_output_adversarial.py
python -m audit_harness.cli experiment experiments/model_output_adversarial/scenarios --out experiments/model_output_adversarial/results/model_output_adversarial_experiment.md --json-out experiments/model_output_adversarial/results/model_output_adversarial_experiment.json
```

It generates sixty negative controls from the ten model outputs: locator mismatches, unsupported claims, contradiction-pattern claims, out-of-manifest sources, missing output-source links and counter-material omissions. All sixty are rejected despite high upstream recall: forty are capped at `reference_information`, and twenty unsupported or contradictory source-support variants are withdrawn as `no_external_legal_effect`.

## Issue-Specific Public Output/Source Study

The repository includes a stricter public layer over issue-specific public search outputs and a source-bound public-source packet:

```bash
python scripts/collect_issue_public_outputs.py
python -m audit_harness.cli experiment experiments/issue_public_outputs/scenarios --out experiments/issue_public_outputs/results/issue_public_output_experiment.md --json-out experiments/issue_public_outputs/results/issue_public_output_experiment.json
```

The default command uses committed snapshots. Pass `--refresh` to fetch current public pages/API output. The study freezes a CourtListener issue search for U.S. agency deference after `Loper Bright`, a National Archives issue search for English mesothelioma causation, and a Legislation.gov.uk/CURIA public-source packet for GDPR Article 15. It then tests whether the visible records preserve enough high-authority and counter-material evidence to claim `normative_material_screening_output` status. The current result is mixed by design: one source-bound public-source packet qualifies, while two issue-search outputs are capped at `reference_information` because their returned records omit high-authority or counter-material materials.

## Public Retrieval Benchmark

The repository includes an endpoint-matched public-search benchmark over issue-defined authority sets:

```bash
python scripts/collect_public_retrieval_benchmark.py
python -m audit_harness.cli experiment experiments/public_retrieval_benchmark/scenarios --out experiments/public_retrieval_benchmark/results/public_retrieval_benchmark.md --json-out experiments/public_retrieval_benchmark/results/public_retrieval_benchmark.json
```

The benchmark freezes thirty public search outputs across five issue families: U.S. agency deference after `Loper Bright`, English mesothelioma causation after `Fairchild`, Canadian administrative-law standard of review after `Vavilov`, German/EU right-to-be-forgotten review, and EU GDPR Article 15 access rights. It uses committed CourtListener, National Archives, Supreme Court of Canada Lexum, OpenLegalData and CURIA snapshots, then measures high-authority recall, counter-material recall, source reconstruction and procedural status. The gold sets are matched to endpoint scope, so case-law endpoints are not penalized for failing to return legislation; mixed statute/case screening is tested in the source-screening packets. The current result is stringent: all thirty real search outputs remain `reference_information`, with mean high-authority recall of 0.26 and mean counter-material recall of 0.00, because top-k public search results do not preserve the complete issue-specific authority and counter-material chain.

## Public System Output Pilot

The repository includes a public legal system output pilot:

```bash
python scripts/collect_public_system_outputs.py
python -m audit_harness.cli experiment experiments/public_system_outputs/scenarios --out experiments/public_system_outputs/results/public_system_output_experiment.md --json-out experiments/public_system_outputs/results/public_system_output_experiment.json
```

This pilot freezes the ordered top 10 records exposed by each of six public legal retrieval or listing systems and converts those visible outputs into provider-agnostic evidence packets. It tests whether real public system outputs can be reconstructed, source-tagged and status-qualified by the harness. It does not evaluate legal merits, doctrinal correctness, issue-specific ranking quality, RAG behavior or any upstream model architecture. The current public-output scenarios are capped at `professional_support_output` because they lack issue-defined counter-material packets and party-facing contestation pathways.

## Repository Layout

```text
audit_harness/          scoring model and CLI
examples/scenarios/     runnable audit scenarios
examples/jurisdiction_profiles/  legal-system parameter profiles
experiments/stress_tests/results/  committed stress-test and sensitivity outputs
experiments/full_validation/        aggregate full-suite validation report
experiments/issue_gold_sets/       curated issue packets and gold-set outputs
experiments/issue_ablations/       generated positive-control ablations
experiments/issue_public_outputs/  issue-specific public output snapshots and scenarios
experiments/public_retrieval_benchmark/ public search snapshots and issue benchmark outputs
experiments/blind_coding/          score-blinded packets and dual-coding outputs
experiments/ai_outputs/            raw Codex model-output pilot and scored scenarios
experiments/model_output_evidence_ladder/ controlled model-output evidence interventions
experiments/real_cases/            public metadata snapshots, manifests and outputs
experiments/public_system_outputs/ ordered public output snapshots and pilot outputs
tests/                  unit tests
docs/paper_mapping.md   mapping from the paper framework to code
.github/workflows/      CI test harness
```
