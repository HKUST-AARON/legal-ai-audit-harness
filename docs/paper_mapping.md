# Paper-to-Harness Mapping

This repository implements the paper's evaluation framework as a runnable audit harness.

| Paper concept | Harness field |
| --- | --- |
| Output effect `E(o)` | `claimed_status` and the scenario description |
| System role `R(o)` | `system_role`, or inferred role from `review_gate` |
| Audit vector `A(o)` | `scores.S`, `scores.Q`, `scores.H`, `scores.K`, `scores.T`, `scores.L` |
| Source and corpus verifiability | `S` |
| Query and version traceability | `Q` |
| Authority hierarchy | `H` |
| Ranking and counter-material verifiability | `K` |
| Contestability | `T` |
| Adoption logging and audit responsibility | `L` |
| Counter-authority recall | `counter_authority.known` and `counter_authority.retrieved` |
| Jurisdiction-specific authority mapping | `jurisdiction_profile` and `examples/jurisdiction_profiles/*.json` |
| Output-to-source evidence mapping | `evidence_packet.output_units` and `evidence_packet.output_links` |
| Source-attribution tiering | `evidence_packet.output_links[*].source_tag` |
| Procedural source binding | `procedural_source_tag_coverage` |
| Human review and reliance gates | `review_gate` |
| Complete-set counter-material requirement | `counter_material_complete` |
| Downgrade and withdrawal | `failure_flags` |
| Gate function `g_0` | `evaluate_scenario(..., StatusPolicy(...))` and `_allowed_status` |
| System-role cap | `SYSTEM_ROLE_CAPS` and `_cap_by_system_role` |
| Failure cap operator | `_derived_failure_flags`, `_disposition` and disposition caps in `evaluate_scenario` |
| Threshold sensitivity | `python -m audit_harness.cli sensitivity ...` |
| Full validation matrix | `scripts/run_full_validation.py` and `experiments/full_validation/results/full_validation_report.*` |
| Public legal system output pilot | `scripts/collect_public_system_outputs.py` and `experiments/public_system_outputs/scenarios/*.json` |
| Issue-specific public output study | `scripts/collect_issue_public_outputs.py` and `experiments/issue_public_outputs/scenarios/*.json` |
| Public retrieval benchmark | `scripts/collect_public_retrieval_benchmark.py` and `experiments/public_retrieval_benchmark/scenarios/*.json` |
| Raw Codex model output pilot | `experiments/ai_outputs/raw/codex_gpt55_xhigh_first10.md` and `experiments/ai_outputs/scenarios/codex55_*.json` |
| Model-output transcript anchors | `scripts/verify_model_output_transcripts.py` and `experiments/ai_outputs/results/model_output_transcript_verification.*` |
| Source-supported model-output repair intervention | `scripts/build_model_output_repairs.py` and `experiments/model_output_repairs/scenarios/source-bound-*.json` |
| Model-output evidence ladder | `scripts/build_model_output_evidence_ladder.py` and `experiments/model_output_evidence_ladder/scenarios/*.json` |
| Adversarial source-support repair validation | `scripts/build_model_output_adversarial.py` and `experiments/model_output_adversarial/scenarios/*.json` |
| Public source-text anchor verification | `scripts/verify_source_text_anchors.py` and `experiments/source_text_verification/results/source_text_anchor_verification.*` |
| Issue ablation suite | `scripts/build_issue_ablations.py` and `experiments/issue_ablations/scenarios/*.json` |
| Annotation robustness | `scripts/run_annotation_robustness.py` and `experiments/annotation_robustness/results/annotation_robustness.*` |
| Score-blinded dual coding | `scripts/build_blind_coding_packets.py`, `scripts/run_blind_coding_study.py`, and `experiments/blind_coding/` |

The harness is not a legal merits evaluator. It does not decide whether a legal answer is correct. It decides the highest procedural status that an output may claim given the audit artefacts available.

The full validation suite is the repository-level replication entry point. It reruns stress scenarios, public metadata records, public legal-system outputs, issue-specific public output/source packets, the endpoint-matched public retrieval benchmark, raw Codex model outputs, raw-output transcript anchors, source-supported model-output repairs, the model-output evidence ladder, adversarial source-support repairs, public source-text anchor checks, mixed-authority source-screening packets, issue ablations, annotation robustness recoding, score-blinded coding and full-threshold sensitivity, then writes one aggregate validation report. It is scenario-regression and artifact validation: the base `scores` vector is human-coded, while the harness computes status allocation, role caps, set-overlap metrics, evidence-packet metrics, source-tag checks, procedural-source binding and failure caps. The source-text anchor layer checks manifest support terms against extracted public source snapshots; the transcript-anchor layer checks raw model-output scenario locators against the committed model transcript. The annotation robustness layer re-scores all 230 committed scenario packets under strict and lenient coding policies. The score-blinded coding layer strips original scores and expected outcomes from all 230 packets, then compares coder-coder and base-coder status agreement across two codebook-based audit passes. The full-threshold layer re-evaluates all 230 packets under thresholds 8-12.

The implementation adopts the legal-workflow logic in `anthropics/claude-for-legal`: outputs are treated as draft or screening artefacts until review is complete; citations and source links are tagged by verification posture; jurisdiction assumptions are surfaced; and external reliance, filing, sending or execution requires accountable human authorization. It does not depend on an agent runtime or autonomy-level taxonomy.

The public system output pilot uses ordered top-k records from committed public legal system snapshots. It validates source reconstruction and status allocation for real upstream outputs, but it is not a retrieval benchmark and does not test legal merits or issue-specific counter-material recall.

The issue-specific public output/source study is stricter: it freezes two naturally returned public issue-search outputs and one source-bound public-source packet, then measures whether the visible records contain the relevant high-authority and counter-material materials. It is the bridge between source reconstruction and the curated issue packets.

The public retrieval benchmark is the non-tautological public-search layer: it runs thirty committed public query outputs from CourtListener, the National Archives, Supreme Court of Canada Lexum search, OpenLegalData and CURIA against endpoint-compatible high-authority and counter-material sets, then lets the harness compute coverage failures and procedural status. Mixed statute/case authority screening is tested by the source-screening packets instead of requiring case-only endpoints to return legislation.

The Codex output pilot evaluates ten `gpt-5.5` / `xhigh` legal authority recommendations. It shows that high authority coverage and counter-material coverage do not by themselves qualify raw model text as `normative_material_screening_output`: without source-support evidence, the harness caps the outputs at `reference_information`. The repair intervention holds the same visible authorities constant, then validates each repaired output-source link against an issue manifest, locator, hashed manifest source-support excerpt, contradiction patterns, procedural source tag and issue-set coverage before deriving the repair scores. Those variants qualify as `normative_material_screening_output`, which tests the paper's claim that source support, not model identity, controls procedural status. The adversarial repair layer then generates sixty negative controls over the same outputs and confirms that locator, source, claim, output-link and counter-material failures are rejected rather than upgraded.
