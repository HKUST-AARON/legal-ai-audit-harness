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
| Issue ablation suite | `scripts/build_issue_ablations.py` and `experiments/issue_ablations/scenarios/*.json` |
| Annotation robustness | `scripts/run_annotation_robustness.py` and `experiments/annotation_robustness/results/annotation_robustness.*` |
| Score-blinded dual coding | `scripts/build_blind_coding_packets.py`, `scripts/run_blind_coding_study.py`, and `experiments/blind_coding/` |

The harness is not a legal merits evaluator. It does not decide whether a legal answer is correct. It decides the highest procedural status that an output may claim given the audit artefacts available.

The full validation suite is the repository-level replication entry point. It reruns stress scenarios, public metadata records, public legal-system outputs, issue-specific public output/source packets, the public retrieval benchmark, raw Codex model outputs, issue-defined positive controls, issue ablations, annotation robustness recoding, score-blinded dual coding and threshold sensitivity reports, then writes one aggregate validation report. It is scenario-regression and artifact validation: the base `scores` vector is human-coded, while the harness computes status allocation, role caps, set-overlap metrics, evidence-packet metrics, source-tag checks and failure caps. The annotation robustness layer re-scores all 62 committed scenario packets under strict and lenient coding policies. The score-blinded coding layer strips original scores and expected outcomes from 47 packets, then compares two independent codebook-based audit passes.

The implementation adopts the legal-workflow logic in `anthropics/claude-for-legal`: outputs are treated as draft or screening artefacts until review is complete; citations and source links are tagged by verification posture; jurisdiction assumptions are surfaced; and external reliance, filing, sending or execution requires accountable human authorization. It does not depend on an agent runtime or autonomy-level taxonomy.

The public system output pilot uses ordered top-k records from committed public legal system snapshots. It validates source reconstruction and status allocation for real upstream outputs, but it is not a retrieval benchmark and does not test legal merits or issue-specific counter-material recall.

The issue-specific public output/source study is stricter: it freezes two naturally returned public issue-search outputs and one source-bound public-source packet, then measures whether the visible records contain the relevant high-authority and counter-material materials. It is the bridge between source reconstruction and the curated issue packets.

The public retrieval benchmark is the non-tautological public-search layer: it runs twelve committed CourtListener and National Archives query outputs against issue-defined high-authority and counter-material sets, then lets the harness compute coverage failures and procedural status.

The Codex output pilot evaluates ten `gpt-5.5` / `xhigh` legal authority recommendations. It shows that high authority coverage and counter-material coverage do not by themselves qualify raw model text as `normative_material_screening_output`: without source-bound evidence, the harness caps the outputs at `reference_information`.
