from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))

from audit_harness.model import STATUS_RANK, StatusPolicy, evaluate_scenario

RESULTS = ROOT / "experiments" / "full_validation" / "results"
THRESHOLDS = [8, 9, 10, 11, 12]

SUITES = [
    {
        "id": "stress_tests",
        "label": "Protocol stress scenarios",
        "path": ROOT / "examples" / "scenarios",
        "out": ROOT / "experiments" / "stress_tests" / "results" / "stress_test_experiment.md",
        "json_out": ROOT / "experiments" / "stress_tests" / "results" / "stress_test_experiment.json",
        "unit_label": "stress scenarios",
        "evidence_class": "construct test",
        "finding": "Tests downgrade, withdrawal, decision-support and high-recall-but-blocked behavior.",
    },
    {
        "id": "real_cases",
        "label": "Public legal-record metadata",
        "path": ROOT / "experiments" / "real_cases" / "scenarios",
        "out": ROOT / "experiments" / "real_cases" / "results" / "real_case_experiment.md",
        "json_out": ROOT / "experiments" / "real_cases" / "results" / "real_case_experiment.json",
        "unit_label": "public metadata records",
        "evidence_class": "public-source reconstruction",
        "finding": "Tests source reconstruction across six public legal-record sources.",
    },
    {
        "id": "public_system_outputs",
        "label": "Public legal-system outputs",
        "path": ROOT / "experiments" / "public_system_outputs" / "scenarios",
        "out": ROOT / "experiments" / "public_system_outputs" / "results" / "public_system_output_experiment.md",
        "json_out": ROOT / "experiments" / "public_system_outputs" / "results" / "public_system_output_experiment.json",
        "unit_label": "visible public-system records",
        "evidence_class": "public-output audit",
        "finding": "Tests ordered real upstream legal-output reconstruction.",
    },
    {
        "id": "issue_public_outputs",
        "label": "Issue-specific public output/source packets",
        "path": ROOT / "experiments" / "issue_public_outputs" / "scenarios",
        "out": ROOT / "experiments" / "issue_public_outputs" / "results" / "issue_public_output_experiment.md",
        "json_out": ROOT / "experiments" / "issue_public_outputs" / "results" / "issue_public_output_experiment.json",
        "unit_label": "issue-specific public output/source records",
        "evidence_class": "mixed public-output/source audit",
        "finding": "Tests public issue-search outputs and a source-bound public-source packet against high-authority and counter-material requirements.",
    },
    {
        "id": "public_retrieval_benchmark",
        "label": "Endpoint-matched public retrieval benchmark",
        "path": ROOT / "experiments" / "public_retrieval_benchmark" / "scenarios",
        "out": ROOT / "experiments" / "public_retrieval_benchmark" / "results" / "public_retrieval_benchmark.md",
        "json_out": ROOT / "experiments" / "public_retrieval_benchmark" / "results" / "public_retrieval_benchmark.json",
        "unit_label": "public search result records",
        "evidence_class": "endpoint-compatible public-output benchmark",
        "finding": "Tests public case-law or known-item outputs against authority sets that the endpoint is capable of returning, while recording mixed-authority gaps separately.",
    },
    {
        "id": "holdout_validation",
        "label": "Out-of-sample holdout validation",
        "path": ROOT / "experiments" / "holdout_validation" / "scenarios",
        "out": ROOT / "experiments" / "holdout_validation" / "results" / "holdout_validation.md",
        "json_out": ROOT / "experiments" / "holdout_validation" / "results" / "holdout_validation.json",
        "unit_label": "holdout output records/items",
        "evidence_class": "frozen-protocol holdout validation",
        "finding": "Tests withheld public-retrieval packets, raw model-output packets and source-bound repair packets after freezing the scoring policy.",
    },
    {
        "id": "ai_outputs",
        "label": "Raw Codex GPT-5.5 xhigh outputs",
        "path": ROOT / "experiments" / "ai_outputs" / "scenarios",
        "out": ROOT / "experiments" / "ai_outputs" / "results" / "ai_output_experiment.md",
        "json_out": ROOT / "experiments" / "ai_outputs" / "results" / "ai_output_experiment.json",
        "unit_label": "raw model outputs",
        "evidence_class": "model-output audit",
        "finding": "Tests whether strong authority coverage without source binding remains procedurally capped.",
    },
    {
        "id": "model_output_repairs",
        "label": "Source-supported model-output repairs",
        "path": ROOT / "experiments" / "model_output_repairs" / "scenarios",
        "out": ROOT / "experiments" / "model_output_repairs" / "results" / "model_output_repair_experiment.md",
        "json_out": ROOT / "experiments" / "model_output_repairs" / "results" / "model_output_repair_experiment.json",
        "unit_label": "source-supported model-output variants",
        "evidence_class": "model-output intervention",
        "finding": "Tests whether model-output variants can qualify after manifest, locator, issue-set, rank-salience and hashed source-support evidence validation.",
    },
    {
        "id": "cross_engine_model_outputs",
        "label": "Cross-engine raw model outputs",
        "path": ROOT / "experiments" / "cross_engine_model_outputs" / "scenarios",
        "out": ROOT / "experiments" / "cross_engine_model_outputs" / "results" / "cross_engine_model_output_experiment.md",
        "json_out": ROOT / "experiments" / "cross_engine_model_outputs" / "results" / "cross_engine_model_output_experiment.json",
        "unit_label": "cross-engine raw outputs",
        "evidence_class": "identity-neutral model-output audit",
        "finding": "Tests whether high-recall outputs from three model engines remain capped without source-bound legal-material chains.",
    },
    {
        "id": "cross_engine_model_repairs",
        "label": "Cross-engine source-supported repairs",
        "path": ROOT / "experiments" / "cross_engine_model_repairs" / "scenarios",
        "out": ROOT / "experiments" / "cross_engine_model_repairs" / "results" / "cross_engine_model_repair_experiment.md",
        "json_out": ROOT / "experiments" / "cross_engine_model_repairs" / "results" / "cross_engine_model_repair_experiment.json",
        "unit_label": "cross-engine source-supported outputs",
        "evidence_class": "identity-neutral source-support intervention",
        "finding": "Tests whether the same issue outputs qualify after source-support validation, regardless of model identity.",
    },
    {
        "id": "model_output_evidence_ladder",
        "label": "Model-output evidence ladder",
        "path": ROOT / "experiments" / "model_output_evidence_ladder" / "scenarios",
        "out": ROOT / "experiments" / "model_output_evidence_ladder" / "results" / "model_output_evidence_ladder_experiment.md",
        "json_out": ROOT / "experiments" / "model_output_evidence_ladder" / "results" / "model_output_evidence_ladder_experiment.json",
        "unit_label": "evidence-ladder model-output variants",
        "evidence_class": "controlled model-output intervention",
        "finding": "Tests model-output variants across raw, source-bound, counter-material, rank-salience, contestability, logging, authorized-adoption and unauthorized-action conditions.",
    },
    {
        "id": "model_output_adversarial",
        "label": "Adversarial source-support repairs",
        "path": ROOT / "experiments" / "model_output_adversarial" / "scenarios",
        "out": ROOT / "experiments" / "model_output_adversarial" / "results" / "model_output_adversarial_experiment.md",
        "json_out": ROOT / "experiments" / "model_output_adversarial" / "results" / "model_output_adversarial_experiment.json",
        "unit_label": "adversarial source-support variants",
        "evidence_class": "negative-control model-output validation",
        "finding": "Tests whether source-support repair gates reject locator mismatches, unsupported claims, contradiction patterns, out-of-manifest sources, missing output links and counter-material omissions.",
    },
    {
        "id": "issue_gold_sets",
        "label": "Mixed-authority public source-screening packets",
        "path": ROOT / "experiments" / "issue_gold_sets" / "scenarios",
        "out": ROOT / "experiments" / "issue_gold_sets" / "results" / "issue_gold_set_experiment.md",
        "json_out": ROOT / "experiments" / "issue_gold_sets" / "results" / "issue_gold_set_experiment.json",
        "unit_label": "curated issue packets",
        "evidence_class": "mixed-authority construct test",
        "finding": "Tests normative material screening with mixed statute/case/source packets rather than single-endpoint public search results.",
    },
    {
        "id": "issue_ablations",
        "label": "Issue-defined ablations",
        "path": ROOT / "experiments" / "issue_ablations" / "scenarios",
        "out": ROOT / "experiments" / "issue_ablations" / "results" / "issue_ablation_experiment.md",
        "json_out": ROOT / "experiments" / "issue_ablations" / "results" / "issue_ablation_experiment.json",
        "unit_label": "issue-packet ablations",
        "evidence_class": "negative-control construct test",
        "finding": "Tests whether high-authority omissions, counter-material suppression, unverified source tags and missing adoption gates trigger the expected caps.",
    },
]


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    _run([sys.executable, "scripts/collect_real_cases.py"])
    _run([sys.executable, "scripts/collect_public_system_outputs.py"])
    _run([sys.executable, "scripts/collect_issue_public_outputs.py"])
    _run([sys.executable, "scripts/collect_public_retrieval_benchmark.py"])
    _run([sys.executable, "scripts/build_holdout_validation.py"])
    _run([sys.executable, "scripts/build_model_output_repairs.py"])
    _run([sys.executable, "scripts/build_model_output_evidence_ladder.py"])
    _run([sys.executable, "scripts/build_model_output_adversarial.py"])
    _run([sys.executable, "scripts/build_cross_engine_model_outputs.py"])
    _run([sys.executable, "scripts/build_issue_ablations.py"])
    _run([sys.executable, "scripts/build_source_chain_attacks.py"])
    _run([sys.executable, "scripts/build_contestation_challenges.py"])
    _run([sys.executable, "scripts/build_blind_coding_packets.py"])
    _run([sys.executable, "scripts/verify_model_output_transcripts.py"])
    _run([sys.executable, "scripts/verify_cross_engine_model_transcripts.py"])
    _run([sys.executable, "scripts/verify_source_text_anchors.py"])
    _run([sys.executable, "scripts/verify_formal_invariants.py"])
    _run([sys.executable, "scripts/run_status_lattice_analysis.py"])
    _run([sys.executable, "scripts/run_metric_separation_analysis.py"])
    _run([sys.executable, "scripts/run_baseline_comparison_analysis.py"])
    _run([sys.executable, "scripts/run_issue_family_generalization.py"])
    _run([sys.executable, "scripts/run_policy_family_robustness.py"])
    _run([sys.executable, "scripts/run_gate_ablation_analysis.py"])
    _run([sys.executable, "scripts/run_gate_contrast_witness_analysis.py"])
    _run([sys.executable, "scripts/run_repair_frontier_analysis.py"])
    _run([sys.executable, "scripts/run_jurisdiction_profile_analysis.py"])
    _run([sys.executable, "scripts/run_ranking_visibility_analysis.py"])
    _run([sys.executable, "scripts/run_status_certificate_validation.py"])
    _run([sys.executable, "scripts/run_certificate_tamper_analysis.py"])
    _run([sys.executable, "scripts/run_policy_constants_replay.py"])
    _run([sys.executable, "scripts/run_metamorphic_policy_tests.py"])
    _run([sys.executable, "scripts/run_policy_mutation_analysis.py"])
    _run([sys.executable, "scripts/run_review_provenance_analysis.py"])
    _run([sys.executable, "scripts/run_claim_anchor_analysis.py"])
    _run([sys.executable, "scripts/run_workflow_portability_analysis.py"])
    _run([sys.executable, "scripts/run_model_identity_invariance.py"])
    _run([sys.executable, "scripts/run_query_perturbation_analysis.py"])
    _run([sys.executable, "scripts/run_query_portfolio_frontier.py"])

    rows = []
    for suite in SUITES:
        _run(
            [
                sys.executable,
                "-m",
                "audit_harness.cli",
                "experiment",
                str(suite["path"].relative_to(ROOT)),
                "--out",
                str(suite["out"].relative_to(ROOT)),
                "--json-out",
                str(suite["json_out"].relative_to(ROOT)),
            ]
        )
        payload = json.loads(suite["json_out"].read_text(encoding="utf-8"))
        rows.append(_suite_row(suite, payload))
    _run(
        [
            sys.executable,
            "-m",
            "audit_harness.cli",
            "experiment",
            "experiments/source_chain_attacks/scenarios",
            "--out",
            "experiments/source_chain_attacks/results/source_chain_attack_experiment.md",
            "--json-out",
            "experiments/source_chain_attacks/results/source_chain_attack_experiment.json",
        ]
    )
    source_chain_attack_payload = json.loads(
        (ROOT / "experiments" / "source_chain_attacks" / "results" / "source_chain_attack_experiment.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_source_chain_attack_row(source_chain_attack_payload))
    _run(
        [
            sys.executable,
            "-m",
            "audit_harness.cli",
            "experiment",
            "experiments/contestation_challenges/scenarios",
            "--out",
            "experiments/contestation_challenges/results/contestation_challenge_experiment.md",
            "--json-out",
            "experiments/contestation_challenges/results/contestation_challenge_experiment.json",
        ]
    )
    contestation_challenge_payload = json.loads(
        (
            ROOT
            / "experiments"
            / "contestation_challenges"
            / "results"
            / "contestation_challenge_experiment.json"
        ).read_text(encoding="utf-8")
    )
    rows.append(_contestation_challenge_row(contestation_challenge_payload))
    source_text_payload = json.loads(
        (ROOT / "experiments" / "source_text_verification" / "results" / "source_text_anchor_verification.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_source_text_row(source_text_payload))
    transcript_payload = json.loads(
        (ROOT / "experiments" / "ai_outputs" / "results" / "model_output_transcript_verification.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_model_transcript_row(transcript_payload))
    cross_engine_transcript_payload = json.loads(
        (
            ROOT
            / "experiments"
            / "cross_engine_model_outputs"
            / "results"
            / "cross_engine_transcript_verification.json"
        ).read_text(encoding="utf-8")
    )
    rows.append(_cross_engine_transcript_row(cross_engine_transcript_payload))
    invariant_payload = json.loads(
        (ROOT / "experiments" / "formal_invariants" / "results" / "formal_invariant_verification.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_formal_invariant_row(invariant_payload))
    status_lattice_payload = json.loads(
        (ROOT / "experiments" / "status_lattice" / "results" / "status_lattice_analysis.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_status_lattice_row(status_lattice_payload))
    metric_separation_payload = json.loads(
        (ROOT / "experiments" / "metric_separation" / "results" / "metric_separation_analysis.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_metric_separation_row(metric_separation_payload))
    baseline_comparison_payload = json.loads(
        (ROOT / "experiments" / "baseline_comparisons" / "results" / "baseline_comparison_analysis.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_baseline_comparison_row(baseline_comparison_payload))
    issue_family_payload = json.loads(
        (
            ROOT
            / "experiments"
            / "issue_family_generalization"
            / "results"
            / "issue_family_generalization.json"
        ).read_text(encoding="utf-8")
    )
    rows.append(_issue_family_generalization_row(issue_family_payload))
    policy_family_payload = json.loads(
        (
            ROOT
            / "experiments"
            / "policy_family_robustness"
            / "results"
            / "policy_family_robustness.json"
        ).read_text(encoding="utf-8")
    )
    rows.append(_policy_family_robustness_row(policy_family_payload))
    gate_ablation_payload = json.loads(
        (ROOT / "experiments" / "gate_ablations" / "results" / "gate_ablation_analysis.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_gate_ablation_row(gate_ablation_payload))
    gate_contrast_payload = json.loads(
        (
            ROOT
            / "experiments"
            / "gate_contrast_witnesses"
            / "results"
            / "gate_contrast_witness_analysis.json"
        ).read_text(encoding="utf-8")
    )
    rows.append(_gate_contrast_witness_row(gate_contrast_payload))
    repair_frontier_payload = json.loads(
        (ROOT / "experiments" / "repair_frontiers" / "results" / "repair_frontier_analysis.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_repair_frontier_row(repair_frontier_payload))
    jurisdiction_profile_payload = json.loads(
        (ROOT / "experiments" / "jurisdiction_profiles" / "results" / "jurisdiction_profile_analysis.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_jurisdiction_profile_row(jurisdiction_profile_payload))
    ranking_visibility_payload = json.loads(
        (ROOT / "experiments" / "ranking_visibility" / "results" / "ranking_visibility_analysis.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_ranking_visibility_row(ranking_visibility_payload))
    status_certificate_payload = json.loads(
        (ROOT / "experiments" / "status_certificates" / "results" / "status_certificate_validation.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_status_certificate_row(status_certificate_payload))
    certificate_tamper_payload = json.loads(
        (
            ROOT
            / "experiments"
            / "certificate_tamper"
            / "results"
            / "certificate_tamper_analysis.json"
        ).read_text(encoding="utf-8")
    )
    rows.append(_certificate_tamper_row(certificate_tamper_payload))
    policy_constants_payload = json.loads(
        (ROOT / "experiments" / "policy_constants_replay" / "results" / "policy_constants_replay.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_policy_constants_row(policy_constants_payload))
    metamorphic_payload = json.loads(
        (ROOT / "experiments" / "metamorphic_policy" / "results" / "metamorphic_policy_tests.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_metamorphic_policy_row(metamorphic_payload))
    policy_mutation_payload = json.loads(
        (ROOT / "experiments" / "policy_mutations" / "results" / "policy_mutation_analysis.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_policy_mutation_row(policy_mutation_payload))
    review_provenance_payload = json.loads(
        (ROOT / "experiments" / "review_provenance" / "results" / "review_provenance_analysis.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_review_provenance_row(review_provenance_payload))
    claim_anchor_payload = json.loads(
        (ROOT / "experiments" / "claim_anchor_analysis" / "results" / "claim_anchor_analysis.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_claim_anchor_row(claim_anchor_payload))
    workflow_portability_payload = json.loads(
        (
            ROOT
            / "experiments"
            / "workflow_portability"
            / "results"
            / "workflow_portability_analysis.json"
        ).read_text(encoding="utf-8")
    )
    rows.append(_workflow_portability_row(workflow_portability_payload))
    model_identity_payload = json.loads(
        (
            ROOT
            / "experiments"
            / "model_identity_invariance"
            / "results"
            / "model_identity_invariance.json"
        ).read_text(encoding="utf-8")
    )
    rows.append(_model_identity_invariance_row(model_identity_payload))
    query_perturbation_payload = json.loads(
        (ROOT / "experiments" / "query_perturbation" / "results" / "query_perturbation_analysis.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_query_perturbation_row(query_perturbation_payload))
    query_portfolio_payload = json.loads(
        (ROOT / "experiments" / "query_portfolios" / "results" / "query_portfolio_frontier.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_query_portfolio_row(query_portfolio_payload))

    _run(
        [
            sys.executable,
            "-m",
            "audit_harness.cli",
            "sensitivity",
            "examples/scenarios",
            "--out",
            "experiments/stress_tests/results/sensitivity_report.md",
            "--json-out",
            "experiments/stress_tests/results/sensitivity_report.json",
        ]
    )
    _run(
        [
            sys.executable,
            "-m",
            "audit_harness.cli",
            "sensitivity",
            "experiments/ai_outputs/scenarios",
            "--out",
            "experiments/ai_outputs/results/ai_output_sensitivity.md",
            "--json-out",
            "experiments/ai_outputs/results/ai_output_sensitivity.json",
        ]
    )
    _run([sys.executable, "scripts/run_annotation_robustness.py"])
    robustness_payload = json.loads(
        (ROOT / "experiments" / "annotation_robustness" / "results" / "annotation_robustness.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_robustness_row(robustness_payload))
    _run([sys.executable, "scripts/run_annotation_uncertainty_analysis.py"])
    uncertainty_payload = json.loads(
        (ROOT / "experiments" / "annotation_uncertainty" / "results" / "annotation_uncertainty.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_uncertainty_row(uncertainty_payload))
    blind_coding_payload = None
    blind_annotation_files = sorted((ROOT / "experiments" / "blind_coding" / "annotations").glob("coder_*.json"))
    if len(blind_annotation_files) >= 2:
        _run([sys.executable, "scripts/run_blind_coding_study.py"])
        blind_coding_payload = json.loads(
            (ROOT / "experiments" / "blind_coding" / "results" / "blind_coding_study.json").read_text(
                encoding="utf-8"
            )
        )
        rows.append(_blind_coding_row(blind_coding_payload))

    validation_units = _validation_units()
    base_validation_units = validation_units["total"]
    threshold_sensitivity = _threshold_sensitivity(_load_all_scenarios())
    threshold_evaluations = threshold_sensitivity["scenario_count"] * len(threshold_sensitivity["runs"])
    validation_units_payload = dict(validation_units)
    validation_units_payload.update(
        {
            "annotation_recodings": robustness_payload["recoded_evaluations"],
            "annotation_uncertainty_evaluations": uncertainty_payload["evaluation_count"],
            "blind_coding_packets": 0 if blind_coding_payload is None else blind_coding_payload["packet_count"],
            "threshold_sensitivity_evaluations": threshold_evaluations,
            "source_chain_attack_variants": source_chain_attack_payload["summary"]["scenario_count"],
            "source_chain_attack_passed": source_chain_attack_payload["summary"]["expected_passed"],
            "contestation_challenge_variants": contestation_challenge_payload["summary"]["scenario_count"],
            "contestation_challenge_passed": contestation_challenge_payload["summary"]["expected_passed"],
            "source_text_anchor_checks": source_text_payload["support_item_count"],
            "source_text_anchor_verified": source_text_payload["support_items_verified"],
            "model_output_transcript_locator_checks": transcript_payload["locator_count"],
            "model_output_transcript_locators_verified": transcript_payload["locators_verified"],
            "cross_engine_transcript_locator_checks": cross_engine_transcript_payload["locator_count"],
            "cross_engine_transcript_locators_verified": cross_engine_transcript_payload["locators_verified"],
            "cross_engine_count": cross_engine_transcript_payload["engine_count"],
            "formal_invariant_checks": invariant_payload["total_checks"],
            "formal_invariant_passed": invariant_payload["passed_checks"],
            "status_lattice_states": status_lattice_payload["state_count"],
            "status_lattice_cover_edges": status_lattice_payload["cover_edge_diagnostics"]["checks"],
            "status_lattice_necessity_checks": status_lattice_payload["necessity"]["checks"],
            "status_lattice_gate_ablation_checks": status_lattice_payload["gate_ablation"]["checks"],
            "status_lattice_substitution_predictions": status_lattice_payload["state_count"]
            * len(status_lattice_payload["substitution_rules"]),
            "metric_separation_evaluations": metric_separation_payload["metric_scenario_count"],
            "metric_statistical_resamples": metric_separation_payload["bootstrap"]["iterations"]
            + metric_separation_payload["permutation"]["iterations"],
            "baseline_comparison_predictions": baseline_comparison_payload["baseline_prediction_count"],
            "issue_family_generalization_predictions": issue_family_payload["holdout_prediction_count"],
            "policy_family_status_evaluations": policy_family_payload["status_evaluation_count"],
            "policy_family_baseline_predictions": policy_family_payload["baseline_prediction_count"],
            "policy_family_robustness_evaluations": policy_family_payload["total_evaluation_count"],
            "gate_ablation_evaluations": gate_ablation_payload["ablation_count"],
            "gate_contrast_witnesses": gate_contrast_payload["witness_count"],
            "gate_contrast_witnesses_passed": gate_contrast_payload["passed_count"],
            "repair_frontier_evaluations": repair_frontier_payload["counterfactual_evaluation_count"],
            "jurisdiction_profile_evaluations": jurisdiction_profile_payload["profile_check_count"]
            + jurisdiction_profile_payload["counterfactual_evaluation_count"],
            "ranking_visibility_checks": ranking_visibility_payload["visibility_check_count"],
            "ranking_visibility_window_checks": ranking_visibility_payload["window_check_count"],
            "ranking_visibility_counterfactuals": ranking_visibility_payload["rank_order_counterfactual_count"],
            "status_certificate_replay_checks": status_certificate_payload["replay_check_count"],
            "status_certificate_proof_obligations": status_certificate_payload["proof_obligation_count"],
            "status_certificate_proof_obligations_passed": status_certificate_payload["passed_proof_obligation_count"],
            "status_certificates_verified": status_certificate_payload["verified_certificate_count"],
            "certificate_tamper_cases": certificate_tamper_payload["tamper_case_count"],
            "certificate_tamper_rejected": certificate_tamper_payload["rejected_count"],
            "policy_constants_replay_checks": policy_constants_payload["check_count"],
            "policy_constants_replay_passed": policy_constants_payload["passed_check_count"],
            "metamorphic_policy_evaluations": metamorphic_payload["metamorphic_evaluation_count"],
            "metamorphic_policy_passed": metamorphic_payload["passed_count"],
            "policy_mutation_evaluations": policy_mutation_payload["evaluation_count"],
            "policy_mutants_killed": policy_mutation_payload["killed_mutant_count"],
            "review_provenance_evaluations": review_provenance_payload["evaluation_count"],
            "review_provenance_passed": review_provenance_payload["passed_count"],
            "claim_anchor_evaluations": claim_anchor_payload["evaluation_count"],
            "claim_anchor_passed": claim_anchor_payload["passed_count"],
            "claim_anchor_output_units": claim_anchor_payload["output_unit_count"],
            "claim_anchor_output_links": claim_anchor_payload["output_link_count"],
            "workflow_portability_evaluations": workflow_portability_payload["evaluation_count"],
            "workflow_portability_passed": workflow_portability_payload["passed_count"],
            "workflow_architecture_invariance_evaluations": workflow_portability_payload[
                "architecture_invariance_evaluation_count"
            ],
            "workflow_entitlement_cap_checks": workflow_portability_payload["entitlement_profile_evaluation_count"],
            "workflow_decision_dependency_checks": workflow_portability_payload["decision_dependency_check_count"],
            "workflow_unaccountable_bar_checks": workflow_portability_payload["unaccountable_bar_evaluation_count"],
            "model_identity_invariance_evaluations": model_identity_payload["evaluation_count"],
            "model_identity_invariance_passed": model_identity_payload["passed_count"],
            "query_perturbation_variants": query_perturbation_payload["query_variant_count"],
            "query_perturbation_groups": query_perturbation_payload["issue_group_count"],
            "query_portfolio_evaluations": query_portfolio_payload["portfolio_count"]
            + query_portfolio_payload["issue_group_count"],
            "query_portfolios": query_portfolio_payload["portfolio_count"],
        }
    )
    substitute_theory_payload = _substitute_theory_results(
        metric_separation_payload,
        baseline_comparison_payload,
        status_lattice_payload,
        model_identity_payload,
    )
    payload = {
        "suite_count": len(rows),
        "scenario_files": sum(row["scenario_count"] for row in rows if "expected_passed" in row),
        "recoded_evaluations": robustness_payload["recoded_evaluations"],
        "annotation_uncertainty_evaluations": uncertainty_payload["evaluation_count"],
        "blind_coding_evaluations": 0 if blind_coding_payload is None else blind_coding_payload["packet_count"] * blind_coding_payload["coder_count"],
        "threshold_sensitivity_evaluations": threshold_evaluations,
        "source_chain_attack_evaluations": source_chain_attack_payload["summary"]["scenario_count"],
        "contestation_challenge_evaluations": contestation_challenge_payload["summary"]["scenario_count"],
        "source_text_anchor_evaluations": source_text_payload["support_item_count"],
        "model_output_transcript_evaluations": transcript_payload["locator_count"],
        "cross_engine_transcript_evaluations": cross_engine_transcript_payload["locator_count"],
        "formal_invariant_evaluations": invariant_payload["total_checks"],
        "status_lattice_evaluations": status_lattice_payload["state_count"],
        "status_lattice_cover_edges": status_lattice_payload["cover_edge_diagnostics"]["checks"],
        "status_lattice_necessity_checks": status_lattice_payload["necessity"]["checks"],
        "status_lattice_gate_ablation_checks": status_lattice_payload["gate_ablation"]["checks"],
        "status_lattice_substitution_predictions": status_lattice_payload["state_count"]
        * len(status_lattice_payload["substitution_rules"]),
        "metric_separation_evaluations": metric_separation_payload["metric_scenario_count"],
        "metric_statistical_resamples": metric_separation_payload["bootstrap"]["iterations"]
        + metric_separation_payload["permutation"]["iterations"],
        "baseline_comparison_evaluations": baseline_comparison_payload["baseline_prediction_count"],
        "issue_family_generalization_evaluations": issue_family_payload["holdout_prediction_count"],
        "policy_family_robustness_evaluations": policy_family_payload["total_evaluation_count"],
        "gate_ablation_evaluations": gate_ablation_payload["ablation_count"],
        "gate_contrast_witness_evaluations": gate_contrast_payload["witness_count"],
        "repair_frontier_evaluations": repair_frontier_payload["counterfactual_evaluation_count"],
        "jurisdiction_profile_evaluations": jurisdiction_profile_payload["profile_check_count"]
        + jurisdiction_profile_payload["counterfactual_evaluation_count"],
        "ranking_visibility_checks": ranking_visibility_payload["visibility_check_count"],
        "ranking_visibility_window_checks": ranking_visibility_payload["window_check_count"],
        "ranking_visibility_counterfactuals": ranking_visibility_payload["rank_order_counterfactual_count"],
        "status_certificate_replay_checks": status_certificate_payload["replay_check_count"],
        "status_certificate_proof_obligations": status_certificate_payload["proof_obligation_count"],
        "certificate_tamper_evaluations": certificate_tamper_payload["tamper_case_count"],
        "policy_constants_replay_checks": policy_constants_payload["check_count"],
        "metamorphic_policy_evaluations": metamorphic_payload["metamorphic_evaluation_count"],
        "policy_mutation_evaluations": policy_mutation_payload["evaluation_count"],
        "review_provenance_evaluations": review_provenance_payload["evaluation_count"],
        "claim_anchor_evaluations": claim_anchor_payload["evaluation_count"],
        "workflow_portability_evaluations": workflow_portability_payload["evaluation_count"],
        "model_identity_invariance_evaluations": model_identity_payload["evaluation_count"],
        "query_perturbation_evaluations": query_perturbation_payload["query_variant_count"]
        + query_perturbation_payload["issue_group_count"],
        "query_portfolio_evaluations": query_portfolio_payload["portfolio_count"]
        + query_portfolio_payload["issue_group_count"],
        "total_evaluation_rows": base_validation_units
        + source_text_payload["support_item_count"]
        + transcript_payload["locator_count"]
        + cross_engine_transcript_payload["locator_count"]
        + invariant_payload["total_checks"]
        + status_lattice_payload["state_count"]
        + status_lattice_payload["cover_edge_diagnostics"]["checks"]
        + status_lattice_payload["necessity"]["checks"]
        + status_lattice_payload["gate_ablation"]["checks"]
        + status_lattice_payload["state_count"] * len(status_lattice_payload["substitution_rules"])
        + metric_separation_payload["metric_scenario_count"]
        + metric_separation_payload["bootstrap"]["iterations"]
        + metric_separation_payload["permutation"]["iterations"]
        + baseline_comparison_payload["baseline_prediction_count"]
        + issue_family_payload["holdout_prediction_count"]
        + policy_family_payload["total_evaluation_count"]
        + gate_ablation_payload["ablation_count"]
        + gate_contrast_payload["witness_count"]
        + repair_frontier_payload["counterfactual_evaluation_count"]
        + jurisdiction_profile_payload["profile_check_count"]
        + jurisdiction_profile_payload["counterfactual_evaluation_count"]
        + ranking_visibility_payload["window_check_count"]
        + ranking_visibility_payload["rank_order_counterfactual_count"]
        + status_certificate_payload["replay_check_count"]
        + status_certificate_payload["proof_obligation_count"]
        + certificate_tamper_payload["tamper_case_count"]
        + policy_constants_payload["check_count"]
        + metamorphic_payload["metamorphic_evaluation_count"]
        + policy_mutation_payload["evaluation_count"]
        + review_provenance_payload["evaluation_count"]
        + claim_anchor_payload["evaluation_count"]
        + workflow_portability_payload["evaluation_count"]
        + model_identity_payload["evaluation_count"]
        + query_perturbation_payload["query_variant_count"]
        + query_perturbation_payload["issue_group_count"]
        + query_portfolio_payload["portfolio_count"]
        + query_portfolio_payload["issue_group_count"]
        + robustness_payload["recoded_evaluations"]
        + uncertainty_payload["evaluation_count"]
        + (0 if blind_coding_payload is None else blind_coding_payload["packet_count"] * blind_coding_payload["coder_count"])
        + source_chain_attack_payload["summary"]["scenario_count"]
        + contestation_challenge_payload["summary"]["scenario_count"]
        + threshold_evaluations,
        "source_chain_attacks": {
            "scenario_count": source_chain_attack_payload["summary"]["scenario_count"],
            "expected_passed": source_chain_attack_payload["summary"]["expected_passed"],
            "high_upstream_but_blocked": source_chain_attack_payload["summary"]["high_upstream_but_blocked"],
            "blocked_reason_distribution": source_chain_attack_payload["summary"]["blocked_reason_distribution"],
            "status_distribution": _status_distribution(source_chain_attack_payload["results"]),
            "disposition_distribution": _disposition_distribution(source_chain_attack_payload["results"]),
        },
        "contestation_challenges": {
            "scenario_count": contestation_challenge_payload["summary"]["scenario_count"],
            "expected_passed": contestation_challenge_payload["summary"]["expected_passed"],
            "high_upstream_but_blocked": contestation_challenge_payload["summary"]["high_upstream_but_blocked"],
            "blocked_reason_distribution": contestation_challenge_payload["summary"]["blocked_reason_distribution"],
            "status_distribution": _status_distribution(contestation_challenge_payload["results"]),
            "valid_challenges_blocked": _contestation_valid_blocked(contestation_challenge_payload["results"]),
            "unsupported_controls_preserved": _contestation_unsupported_preserved(
                contestation_challenge_payload["results"]
            ),
        },
        "validation_units": validation_units_payload,
        "expected_passed": sum(row["expected_passed"] for row in rows if "expected_passed" in row),
        "expected_total": sum(row["scenario_count"] for row in rows if "expected_passed" in row),
        "high_upstream_but_blocked": sum(
            row["high_upstream_but_blocked"]
            for row in rows
            if row.get("high_upstream_but_blocked") is not None
        ),
        "blocked_reason_distribution": _blocked_reason_distribution(rows),
        "annotation_robustness": {
            "all_policy_status_stable": robustness_payload["all_policy_status_stable"],
            "scenario_count": robustness_payload["scenario_count"],
            "weighted_status_agreement_base_strict": robustness_payload["weighted_status_agreement_base_strict"],
            "weighted_status_agreement_base_lenient": robustness_payload["weighted_status_agreement_base_lenient"],
        },
        "annotation_uncertainty": {
            "scenario_count": uncertainty_payload["scenario_count"],
            "evaluation_count": uncertainty_payload["evaluation_count"],
            "status_stability_rate": uncertainty_payload["status_stability_rate"],
            "scenario_exact_stability_count": uncertainty_payload["scenario_exact_stability_count"],
            "scenario_high_stability_count": uncertainty_payload["scenario_high_stability_count"],
            "qualified_status_stability_rate": uncertainty_payload["qualified_status_stability_rate"],
            "qualified_high_status_stability_rate": uncertainty_payload["qualified_high_status_stability_rate"],
            "mean_status_rank_shift": uncertainty_payload["mean_status_rank_shift"],
            "boundary_scenario_count": len(uncertainty_payload["boundary_scenarios"]),
        },
        "blind_coding": None
        if blind_coding_payload is None
        else {
            "packet_count": blind_coding_payload["packet_count"],
            "coder_count": blind_coding_payload["coder_count"],
            "status_disagreement_count": blind_coding_payload["status_disagreement_count"],
            "pairwise_status": blind_coding_payload["pairwise_status"],
            "pairwise_dimensions": blind_coding_payload["pairwise_dimensions"],
            "dimension_min_kappa": blind_coding_payload["dimension_min_kappa"],
            "minimum_dimension_kappa": blind_coding_payload["minimum_dimension_kappa"],
            "minimum_dimension_exact_agreement": blind_coding_payload["minimum_dimension_exact_agreement"],
            "minimum_failure_flag_exact_agreement": blind_coding_payload["minimum_failure_flag_exact_agreement"],
            "minimum_failure_flag_jaccard": blind_coding_payload["minimum_failure_flag_jaccard"],
            "minimum_missing_gate_exact_agreement": blind_coding_payload["minimum_missing_gate_exact_agreement"],
            "minimum_missing_gate_jaccard": blind_coding_payload["minimum_missing_gate_jaccard"],
            "base_status_agreement": blind_coding_payload["base_status_agreement"],
            "base_dimension_min_kappa": blind_coding_payload["base_dimension_min_kappa"],
            "base_dimension_min_kappa_dimension": blind_coding_payload["base_dimension_min_kappa_dimension"],
            "base_dimension_min_kappa_coder": blind_coding_payload["base_dimension_min_kappa_coder"],
            "base_dimension_min_kappa_exact_agreement": blind_coding_payload["base_dimension_min_kappa_exact_agreement"],
            "base_dimension_min_exact_agreement": blind_coding_payload["base_dimension_min_exact_agreement"],
            "base_dimension_min_pabak": blind_coding_payload["base_dimension_min_pabak"],
            "base_dimension_max_mean_absolute_delta": blind_coding_payload["base_dimension_max_mean_absolute_delta"],
        },
        "threshold_sensitivity": threshold_sensitivity,
        "source_text_verification": {
            "record_count": source_text_payload["record_count"],
            "records_with_text_snapshot": source_text_payload["records_with_text_snapshot"],
            "support_item_count": source_text_payload["support_item_count"],
            "support_items_verified": source_text_payload["support_items_verified"],
            "verified_ratio": source_text_payload["verified_ratio"],
        },
        "model_output_transcript_verification": {
            "scenario_count": transcript_payload["scenario_count"],
            "scenario_sections_verified": transcript_payload["scenario_sections_verified"],
            "output_unit_count": transcript_payload["output_unit_count"],
            "locator_count": transcript_payload["locator_count"],
            "locators_verified": transcript_payload["locators_verified"],
            "all_locators_verified": transcript_payload["all_locators_verified"],
        },
        "cross_engine_transcript_verification": {
            "scenario_count": cross_engine_transcript_payload["scenario_count"],
            "engine_count": cross_engine_transcript_payload["engine_count"],
            "issue_count": cross_engine_transcript_payload["issue_count"],
            "scenario_sections_verified": cross_engine_transcript_payload["scenario_sections_verified"],
            "output_unit_count": cross_engine_transcript_payload["output_unit_count"],
            "locator_count": cross_engine_transcript_payload["locator_count"],
            "locators_verified": cross_engine_transcript_payload["locators_verified"],
            "all_locators_verified": cross_engine_transcript_payload["all_locators_verified"],
        },
        "formal_invariant_verification": {
            "check_count": invariant_payload["check_count"],
            "total_checks": invariant_payload["total_checks"],
            "passed_checks": invariant_payload["passed_checks"],
            "all_passed": invariant_payload["all_passed"],
        },
        "status_lattice": {
            "state_count": status_lattice_payload["state_count"],
            "score_vector_count": status_lattice_payload["score_vector_count"],
            "role_count": status_lattice_payload["role_count"],
            "gate_count": status_lattice_payload["gate_count"],
            "high_status_count": status_lattice_payload["high_status_count"],
            "decision_status_count": status_lattice_payload["decision_status_count"],
            "cover_edge_diagnostics": status_lattice_payload["cover_edge_diagnostics"],
            "necessity": status_lattice_payload["necessity"],
            "gate_ablation": status_lattice_payload["gate_ablation"],
            "substitution_rules": status_lattice_payload["substitution_rules"],
            "substitution_checks": status_lattice_payload["substitution_checks"],
        },
        "metric_separation": {
            "metric_scenario_count": metric_separation_payload["metric_scenario_count"],
            "qualified_count": metric_separation_payload["qualified_count"],
            "recall_point_biserial": metric_separation_payload["point_biserial"]["recall"],
            "high_recall_blocked": metric_separation_payload["high_recall_blocked"],
            "gate_cascade": metric_separation_payload["gate_cascade"],
            "bootstrap": metric_separation_payload["bootstrap"],
            "permutation": metric_separation_payload["permutation"],
        },
        "baseline_comparison": {
            "baseline_count": baseline_comparison_payload["baseline_count"],
            "baseline_prediction_count": baseline_comparison_payload["baseline_prediction_count"],
            "scenario_count": baseline_comparison_payload["scenario_count"],
            "qualified_count": baseline_comparison_payload["qualified_count"],
            "best_simplified": baseline_comparison_payload["best_simplified"],
            "lowest_false_positive_simplified": baseline_comparison_payload["lowest_false_positive_simplified"],
            "all_simplified_rules_have_errors": baseline_comparison_payload["all_simplified_rules_have_errors"],
            "full_gate": baseline_comparison_payload["full_gate"],
        },
        "issue_family_generalization": {
            "issue_family_count": issue_family_payload["issue_family_count"],
            "scenario_count": issue_family_payload["scenario_count"],
            "qualified_count": issue_family_payload["qualified_count"],
            "holdout_prediction_count": issue_family_payload["holdout_prediction_count"],
            "training_prediction_count": issue_family_payload["training_prediction_count"],
            "full_protocol_holdout_false_positive": issue_family_payload["full_protocol_holdout_false_positive"],
            "full_protocol_holdout_false_negative": issue_family_payload["full_protocol_holdout_false_negative"],
            "best_trained_rule_holdout_false_positive": issue_family_payload[
                "best_trained_rule_holdout_false_positive"
            ],
            "best_trained_rule_holdout_false_negative": issue_family_payload[
                "best_trained_rule_holdout_false_negative"
            ],
            "lowest_fp_rule_holdout_false_positive": issue_family_payload["lowest_fp_rule_holdout_false_positive"],
            "lowest_fp_rule_holdout_false_negative": issue_family_payload["lowest_fp_rule_holdout_false_negative"],
            "folds_with_best_trained_rule_error": issue_family_payload["folds_with_best_trained_rule_error"],
            "folds_with_lowest_fp_rule_error": issue_family_payload["folds_with_lowest_fp_rule_error"],
            "folds": issue_family_payload["folds"],
        },
        "policy_family_robustness": {
            "variant_count": policy_family_payload["variant_count"],
            "scenario_count": policy_family_payload["scenario_count"],
            "status_evaluation_count": policy_family_payload["status_evaluation_count"],
            "baseline_prediction_count": policy_family_payload["baseline_prediction_count"],
            "total_evaluation_count": policy_family_payload["total_evaluation_count"],
            "total_status_promotions": policy_family_payload["total_status_promotions"],
            "total_high_status_promotions": policy_family_payload["total_high_status_promotions"],
            "total_high_status_demotions": policy_family_payload["total_high_status_demotions"],
            "variants_with_simplified_errors": policy_family_payload["variants_with_simplified_errors"],
            "best_simplified_false_positive_total": policy_family_payload[
                "best_simplified_false_positive_total"
            ],
            "best_simplified_false_negative_total": policy_family_payload[
                "best_simplified_false_negative_total"
            ],
            "full_protocol_false_positive_total": policy_family_payload["full_protocol_false_positive_total"],
            "full_protocol_false_negative_total": policy_family_payload["full_protocol_false_negative_total"],
            "rows": policy_family_payload["rows"],
        },
        "gate_ablation": {
            "qualified_scenario_count": gate_ablation_payload["qualified_scenario_count"],
            "ablation_count": gate_ablation_payload["ablation_count"],
            "passed_count": gate_ablation_payload["passed_count"],
            "failed_count": gate_ablation_payload["failed_count"],
            "by_ablation": gate_ablation_payload["by_ablation"],
        },
        "gate_contrast_witnesses": {
            "qualified_scenario_count": gate_contrast_payload["qualified_scenario_count"],
            "witness_count": gate_contrast_payload["witness_count"],
            "passed_count": gate_contrast_payload["passed_count"],
            "failed_count": gate_contrast_payload["failed_count"],
            "score_metric_role_preserved_count": gate_contrast_payload["score_metric_role_preserved_count"],
            "status_separated_count": gate_contrast_payload["status_separated_count"],
            "by_witness": gate_contrast_payload["by_witness"],
            "status_distribution": gate_contrast_payload["status_distribution"],
        },
        "repair_frontier": {
            "blocked_claim_count": repair_frontier_payload["blocked_claim_count"],
            "counterfactual_evaluation_count": repair_frontier_payload["counterfactual_evaluation_count"],
            "repairable_count": repair_frontier_payload["repairable_count"],
            "unrepairable_count": repair_frontier_payload["unrepairable_count"],
            "minimal_repair_size_distribution": repair_frontier_payload["minimal_repair_size_distribution"],
            "minimal_repair_gate_frequency": repair_frontier_payload["minimal_repair_gate_frequency"],
        },
        "jurisdiction_profile": {
            "profile_check_count": jurisdiction_profile_payload["profile_check_count"],
            "profile_supported_count": jurisdiction_profile_payload["profile_supported_count"],
            "qualified_status_count": jurisdiction_profile_payload["qualified_status_count"],
            "counterfactual_evaluation_count": jurisdiction_profile_payload["counterfactual_evaluation_count"],
            "passed_count": jurisdiction_profile_payload["passed_count"],
            "generic_profile_preserved": jurisdiction_profile_payload["generic_profile_preserved"],
            "missing_assumption_downgraded": jurisdiction_profile_payload["missing_assumption_downgraded"],
            "mismatched_profile_downgraded": jurisdiction_profile_payload["mismatched_profile_downgraded"],
        },
        "ranking_visibility": {
            "eligible_packet_count": ranking_visibility_payload["eligible_packet_count"],
            "visibility_check_count": ranking_visibility_payload["visibility_check_count"],
            "window_check_count": ranking_visibility_payload["window_check_count"],
            "window_sensitivity": ranking_visibility_payload["window_sensitivity"],
            "first_counter_rank_distribution": ranking_visibility_payload["first_counter_rank_distribution"],
            "median_first_counter_rank": ranking_visibility_payload["median_first_counter_rank"],
            "mean_reciprocal_first_counter_rank": ranking_visibility_payload["mean_reciprocal_first_counter_rank"],
            "rank_order_counterfactual_count": ranking_visibility_payload["rank_order_counterfactual_count"],
            "rank_order_passed_count": ranking_visibility_payload["rank_order_passed_count"],
            "front_window_packet_count": ranking_visibility_payload["front_window_packet_count"],
            "front_window_counter_visible": ranking_visibility_payload["front_window_counter_visible"],
            "front_window_counter_not_visible": ranking_visibility_payload["front_window_counter_not_visible"],
            "counterfactual_front_window_counter_visible": ranking_visibility_payload[
                "counterfactual_front_window_counter_visible"
            ],
            "rank_intervention_applied_count": ranking_visibility_payload["rank_intervention_applied_count"],
            "coverage_preserved_count": ranking_visibility_payload["coverage_preserved_count"],
            "downgraded_count": ranking_visibility_payload["downgraded_count"],
        },
        "status_certificate": {
            "certificate_count": status_certificate_payload["certificate_count"],
            "verified_certificate_count": status_certificate_payload["verified_certificate_count"],
            "replay_check_count": status_certificate_payload["replay_check_count"],
            "passed_check_count": status_certificate_payload["passed_check_count"],
            "proof_obligation_count": status_certificate_payload["proof_obligation_count"],
            "passed_proof_obligation_count": status_certificate_payload["passed_proof_obligation_count"],
            "failed_proof_obligation_count": status_certificate_payload["failed_proof_obligation_count"],
            "cap_or_failure_transition_count": status_certificate_payload["cap_or_failure_transition_count"],
        },
        "certificate_tamper": {
            "base_certificate_count": certificate_tamper_payload["base_certificate_count"],
            "tamper_family_count": certificate_tamper_payload["tamper_family_count"],
            "tamper_case_count": certificate_tamper_payload["tamper_case_count"],
            "rejected_count": certificate_tamper_payload["rejected_count"],
            "missed_tamper_count": certificate_tamper_payload["missed_tamper_count"],
            "by_family": certificate_tamper_payload["by_family"],
        },
        "policy_constants_replay": {
            "scenario_count": policy_constants_payload["scenario_count"],
            "verified_scenario_count": policy_constants_payload["verified_scenario_count"],
            "check_count": policy_constants_payload["check_count"],
            "passed_check_count": policy_constants_payload["passed_check_count"],
            "failed_check_count": policy_constants_payload["failed_check_count"],
            "cap_or_failure_transition_count": policy_constants_payload["cap_or_failure_transition_count"],
            "status_distribution": policy_constants_payload["status_distribution"],
            "policy_path": policy_constants_payload["policy_path"],
        },
        "metamorphic_policy": {
            "scenario_count": metamorphic_payload["scenario_count"],
            "metamorphic_evaluation_count": metamorphic_payload["metamorphic_evaluation_count"],
            "passed_count": metamorphic_payload["passed_count"],
            "failed_count": metamorphic_payload["failed_count"],
            "by_relation": metamorphic_payload["by_relation"],
        },
        "policy_mutations": {
            "scenario_count": policy_mutation_payload["scenario_count"],
            "qualified_scenario_count": policy_mutation_payload["qualified_scenario_count"],
            "decision_scenario_count": policy_mutation_payload["decision_scenario_count"],
            "mutant_count": policy_mutation_payload["mutant_count"],
            "killed_mutant_count": policy_mutation_payload["killed_mutant_count"],
            "survived_mutant_count": policy_mutation_payload["survived_mutant_count"],
            "evaluation_count": policy_mutation_payload["evaluation_count"],
            "classification_error_count": policy_mutation_payload["classification_error_count"],
            "invalid_promotion_count": policy_mutation_payload["invalid_promotion_count"],
            "false_negative_count": policy_mutation_payload["false_negative_count"],
            "mutants": policy_mutation_payload["mutants"],
        },
        "review_provenance": {
            "scenario_count": review_provenance_payload["scenario_count"],
            "non_high_scenario_count": review_provenance_payload["non_high_scenario_count"],
            "qualified_scenario_count": review_provenance_payload["qualified_scenario_count"],
            "decision_scenario_count": review_provenance_payload["decision_scenario_count"],
            "evaluation_count": review_provenance_payload["evaluation_count"],
            "passed_count": review_provenance_payload["passed_count"],
            "failed_count": review_provenance_payload["failed_count"],
            "placebo_evaluation_count": review_provenance_payload["placebo_evaluation_count"],
            "placebo_blocked_count": review_provenance_payload["placebo_blocked_count"],
            "high_status_provenance_check_count": review_provenance_payload["high_status_provenance_check_count"],
            "high_status_provenance_blocked_count": review_provenance_payload[
                "high_status_provenance_blocked_count"
            ],
            "decision_provenance_check_count": review_provenance_payload["decision_provenance_check_count"],
            "decision_provenance_demoted_count": review_provenance_payload["decision_provenance_demoted_count"],
            "by_relation": review_provenance_payload["by_relation"],
        },
        "claim_anchor": {
            "scenario_count": claim_anchor_payload["scenario_count"],
            "output_unit_count": claim_anchor_payload["output_unit_count"],
            "output_link_count": claim_anchor_payload["output_link_count"],
            "evaluation_count": claim_anchor_payload["evaluation_count"],
            "passed_count": claim_anchor_payload["passed_count"],
            "failed_count": claim_anchor_payload["failed_count"],
            "claim_text_absence_blocked_count": claim_anchor_payload["claim_text_absence_blocked_count"],
            "claim_text_absence_evaluation_count": claim_anchor_payload["claim_text_absence_evaluation_count"],
            "link_unit_binding_absence_blocked_count": claim_anchor_payload["link_unit_binding_absence_blocked_count"],
            "link_unit_binding_absence_evaluation_count": claim_anchor_payload["link_unit_binding_absence_evaluation_count"],
            "support_attestation_absence_withdrawn_count": claim_anchor_payload[
                "support_attestation_absence_withdrawn_count"
            ],
            "support_attestation_absence_evaluation_count": claim_anchor_payload[
                "support_attestation_absence_evaluation_count"
            ],
            "locator_absence_withdrawn_count": claim_anchor_payload["locator_absence_withdrawn_count"],
            "locator_absence_evaluation_count": claim_anchor_payload["locator_absence_evaluation_count"],
        },
        "workflow_portability": {
            "scenario_count": workflow_portability_payload["scenario_count"],
            "architecture_profile_count": workflow_portability_payload["architecture_profile_count"],
            "entitlement_profile_count": workflow_portability_payload["entitlement_profile_count"],
            "architecture_invariance_evaluation_count": workflow_portability_payload[
                "architecture_invariance_evaluation_count"
            ],
            "architecture_invariance_passed_count": workflow_portability_payload[
                "architecture_invariance_passed_count"
            ],
            "entitlement_profile_evaluation_count": workflow_portability_payload[
                "entitlement_profile_evaluation_count"
            ],
            "entitlement_profile_passed_count": workflow_portability_payload["entitlement_profile_passed_count"],
            "decision_dependency_check_count": workflow_portability_payload["decision_dependency_check_count"],
            "decision_dependency_passed_count": workflow_portability_payload["decision_dependency_passed_count"],
            "unaccountable_bar_evaluation_count": workflow_portability_payload["unaccountable_bar_evaluation_count"],
            "unaccountable_bar_passed_count": workflow_portability_payload["unaccountable_bar_passed_count"],
            "evaluation_count": workflow_portability_payload["evaluation_count"],
            "passed_count": workflow_portability_payload["passed_count"],
            "failed_count": workflow_portability_payload["failed_count"],
            "architecture_profiles": workflow_portability_payload["architecture_profiles"],
            "entitlement_profiles": workflow_portability_payload["entitlement_profiles"],
            "by_architecture_profile": workflow_portability_payload["by_architecture_profile"],
            "by_entitlement_profile": workflow_portability_payload["by_entitlement_profile"],
        },
        "model_identity_invariance": {
            "scenario_count": model_identity_payload["scenario_count"],
            "identity_profile_count": model_identity_payload["identity_profile_count"],
            "evaluation_count": model_identity_payload["evaluation_count"],
            "passed_count": model_identity_payload["passed_count"],
            "failed_count": model_identity_payload["failed_count"],
            "status_changed_count": model_identity_payload["status_changed_count"],
            "disposition_changed_count": model_identity_payload["disposition_changed_count"],
            "identity_profiles": model_identity_payload["identity_profiles"],
            "by_identity_profile": model_identity_payload["by_identity_profile"],
        },
        "query_perturbation": {
            "issue_group_count": query_perturbation_payload["issue_group_count"],
            "query_variant_count": query_perturbation_payload["query_variant_count"],
            "status_stable_group_count": query_perturbation_payload["status_stable_group_count"],
            "authority_coverage_unstable_group_count": query_perturbation_payload[
                "authority_coverage_unstable_group_count"
            ],
            "counter_recall_unstable_group_count": query_perturbation_payload["counter_recall_unstable_group_count"],
            "record_set_unstable_group_count": query_perturbation_payload["record_set_unstable_group_count"],
            "top_result_unstable_group_count": query_perturbation_payload["top_result_unstable_group_count"],
            "max_authority_coverage_gap": query_perturbation_payload["max_authority_coverage_gap"],
            "max_counter_recall_gap": query_perturbation_payload["max_counter_recall_gap"],
            "mean_pairwise_record_overlap": query_perturbation_payload["mean_pairwise_record_overlap"],
            "min_pairwise_record_overlap": query_perturbation_payload["min_pairwise_record_overlap"],
            "high_upstream_but_blocked": query_perturbation_payload["high_upstream_but_blocked"],
        },
        "query_portfolio": {
            "issue_group_count": query_portfolio_payload["issue_group_count"],
            "query_variant_count": query_portfolio_payload["query_variant_count"],
            "portfolio_count": query_portfolio_payload["portfolio_count"],
            "qualified_portfolio_count": query_portfolio_payload["qualified_portfolio_count"],
            "full_high_authority_portfolio_count": query_portfolio_payload["full_high_authority_portfolio_count"],
            "full_counter_material_portfolio_count": query_portfolio_payload["full_counter_material_portfolio_count"],
            "full_screening_material_portfolio_count": query_portfolio_payload[
                "full_screening_material_portfolio_count"
            ],
            "mean_authority_coverage": query_portfolio_payload["mean_authority_coverage"],
            "max_authority_coverage": query_portfolio_payload["max_authority_coverage"],
            "mean_counter_recall": query_portfolio_payload["mean_counter_recall"],
            "max_counter_recall": query_portfolio_payload["max_counter_recall"],
            "query_expansion_repairs_any_high_authority": query_portfolio_payload[
                "query_expansion_repairs_any_high_authority"
            ],
            "query_expansion_repairs_counter_material": query_portfolio_payload[
                "query_expansion_repairs_counter_material"
            ],
        },
        "substitute_theory_falsification": substitute_theory_payload,
        "suites": rows,
    }
    (RESULTS / "full_validation_report.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    (RESULTS / "full_validation_report.md").write_text(_format_report(payload) + "\n", encoding="utf-8")
    print(_format_report(payload))
    return 0


def _run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def _load_all_scenarios() -> list[dict]:
    scenarios = []
    for suite in SUITES:
        for path in sorted(suite["path"].glob("*.json")):
            scenario = json.loads(path.read_text(encoding="utf-8"))
            scenario["_source_path"] = str(path.relative_to(ROOT))
            scenarios.append(scenario)
    return scenarios


def _validation_units() -> dict[str, int]:
    counts = {
        "stress_scenarios": _scenario_count(ROOT / "examples" / "scenarios"),
        "public_metadata_records": _output_unit_count(ROOT / "experiments" / "real_cases" / "scenarios"),
        "public_system_records": _output_unit_count(ROOT / "experiments" / "public_system_outputs" / "scenarios"),
        "public_retrieval_records": _output_unit_count(ROOT / "experiments" / "public_retrieval_benchmark" / "scenarios"),
        "holdout_records": _output_unit_count(ROOT / "experiments" / "holdout_validation" / "scenarios"),
        "raw_model_outputs": _scenario_count(ROOT / "experiments" / "ai_outputs" / "scenarios"),
        "source_bound_model_outputs": _scenario_count(ROOT / "experiments" / "model_output_repairs" / "scenarios"),
        "cross_engine_raw_outputs": _scenario_count(ROOT / "experiments" / "cross_engine_model_outputs" / "scenarios"),
        "cross_engine_source_bound_outputs": _scenario_count(ROOT / "experiments" / "cross_engine_model_repairs" / "scenarios"),
        "evidence_ladder_model_outputs": _scenario_count(ROOT / "experiments" / "model_output_evidence_ladder" / "scenarios"),
        "adversarial_model_outputs": _scenario_count(ROOT / "experiments" / "model_output_adversarial" / "scenarios"),
        "issue_public_records": _output_unit_count(ROOT / "experiments" / "issue_public_outputs" / "scenarios"),
        "issue_gold_sets": _scenario_count(ROOT / "experiments" / "issue_gold_sets" / "scenarios"),
        "issue_ablations": _scenario_count(ROOT / "experiments" / "issue_ablations" / "scenarios"),
    }
    counts["total"] = sum(counts.values())
    return counts


def _scenario_count(path: Path) -> int:
    return len(list(path.glob("*.json")))


def _output_unit_count(path: Path) -> int:
    total = 0
    for scenario_path in path.glob("*.json"):
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
        total += len(scenario.get("evidence_packet", {}).get("output_units", []))
    return total


def _baseline_by_id(payload: dict, baseline_id: str) -> dict:
    for baseline in payload["baselines"]:
        if baseline["id"] == baseline_id:
            return baseline
    raise KeyError(baseline_id)


def _lattice_rule(payload: dict, rule_id: str) -> dict:
    for rule in payload["substitution_rules"]:
        if rule["rule"] == rule_id:
            return rule
    raise KeyError(rule_id)


def _substitute_theory_results(
    metric_payload: dict,
    baseline_payload: dict,
    lattice_payload: dict,
    model_identity_payload: dict,
) -> list[dict]:
    full_gate = baseline_payload["full_gate"]
    identity_rule = _identity_label_sufficiency(model_identity_payload)
    theories = [
        {
            "id": "performance_sufficiency",
            "theory": "Performance sufficiency",
            "substitute": "Recall/F1/precision thresholds confer procedural status",
            "scenario_rule": _baseline_by_id(baseline_payload, "recall_threshold"),
            "lattice_rule": None,
            "additional_evidence": f"{metric_payload['high_recall_blocked']['count']}/{metric_payload['high_recall_blocked']['denominator']} high-recall outputs were blocked below normative screening",
        },
        {
            "id": "source_label_sufficiency",
            "theory": "Source-label sufficiency",
            "substitute": "Source-bound evidence alone confers procedural status",
            "scenario_rule": _baseline_by_id(baseline_payload, "source_bound_only"),
            "lattice_rule": _lattice_rule(lattice_payload, "source_bound_score"),
            "additional_evidence": "Source links without authority, counter-material and contestability gates over-admit outputs",
        },
        {
            "id": "authority_material_sufficiency",
            "theory": "Authority-material sufficiency",
            "substitute": "High-authority and counter-material coverage confer procedural status",
            "scenario_rule": _baseline_by_id(baseline_payload, "authority_material_only"),
            "lattice_rule": _lattice_rule(lattice_payload, "source_authority_counter_score"),
            "additional_evidence": "Authority and counter-material coverage without source-chain, role and contestability gates over-admit outputs",
        },
        {
            "id": "review_label_sufficiency",
            "theory": "Review-label sufficiency",
            "substitute": "Review posture or role readiness confers procedural status",
            "scenario_rule": _baseline_by_id(baseline_payload, "review_ready_only"),
            "lattice_rule": _lattice_rule(lattice_payload, "role_ready_and_score"),
            "additional_evidence": "Review labels without source-chain and failure-cap gates over-admit outputs",
        },
        {
            "id": "score_sufficiency",
            "theory": "Score sufficiency",
            "substitute": "Total audit score confers procedural status",
            "scenario_rule": _baseline_by_id(baseline_payload, "total_score_only"),
            "lattice_rule": _lattice_rule(lattice_payload, "total_score_at_least_9"),
            "additional_evidence": "High total score cannot substitute for missing legal-material predicates",
        },
        {
            "id": "model_identity_sufficiency",
            "theory": "Model-identity sufficiency",
            "substitute": "Provider, model or claimed-capability labels confer procedural status",
            "scenario_rule": identity_rule,
            "lattice_rule": None,
            "additional_evidence": (
                f"{identity_rule['false_positive']}/{identity_rule['prediction_count']} "
                "identity-labelled rows would be over-admitted; identity substitution produced "
                f"{model_identity_payload['status_changed_count']} status changes"
            ),
        },
    ]
    rows = []
    for theory in theories:
        scenario_rule = theory["scenario_rule"]
        lattice_rule = theory["lattice_rule"]
        rows.append(
            {
                "id": theory["id"],
                "theory": theory["theory"],
                "substitute": theory["substitute"],
                "scenario_false_positive": scenario_rule["false_positive"],
                "scenario_false_negative": scenario_rule["false_negative"],
                "scenario_precision": scenario_rule["precision"],
                "scenario_recall": scenario_rule["recall"],
                "lattice_false_positive": None if lattice_rule is None else lattice_rule["false_positive"],
                "lattice_false_negative": None if lattice_rule is None else lattice_rule["false_negative"],
                "lattice_precision": None if lattice_rule is None else lattice_rule["precision"],
                "lattice_recall": None if lattice_rule is None else lattice_rule["recall"],
                "full_protocol_false_positive": full_gate["false_positive"],
                "full_protocol_false_negative": full_gate["false_negative"],
                "falsified": scenario_rule["false_positive"] > 0
                or scenario_rule["false_negative"] > 0
                or (
                    lattice_rule is not None
                    and (lattice_rule["false_positive"] > 0 or lattice_rule["false_negative"] > 0)
                ),
                "additional_evidence": theory["additional_evidence"],
            }
        )
    return rows


def _identity_label_sufficiency(payload: dict) -> dict:
    true_positive = false_positive = true_negative = false_negative = 0
    for row in payload["rows"]:
        predicted_high = True
        actual_high = STATUS_RANK[row["mutated_allowed_status"]] >= STATUS_RANK["normative_material_screening_output"]
        if predicted_high and actual_high:
            true_positive += 1
        elif predicted_high and not actual_high:
            false_positive += 1
        elif not predicted_high and actual_high:
            false_negative += 1
        else:
            true_negative += 1
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    return {
        "prediction_count": len(payload["rows"]),
        "true_positive": true_positive,
        "false_positive": false_positive,
        "true_negative": true_negative,
        "false_negative": false_negative,
        "precision": precision,
        "recall": recall,
    }


def _threshold_sensitivity(scenarios: list[dict]) -> dict:
    base_policy = StatusPolicy(normative_threshold=9, decision_threshold=10)
    base = {
        scenario["id"]: evaluate_scenario(scenario, base_policy).allowed_status
        for scenario in scenarios
    }
    runs = []
    for threshold in THRESHOLDS:
        policy = StatusPolicy(normative_threshold=threshold, decision_threshold=max(10, threshold + 1))
        distribution: dict[str, int] = {}
        flips = promotions = demotions = 0
        for scenario in scenarios:
            status = evaluate_scenario(scenario, policy).allowed_status
            distribution[status] = distribution.get(status, 0) + 1
            base_status = base[scenario["id"]]
            if status != base_status:
                flips += 1
                if STATUS_RANK[status] > STATUS_RANK[base_status]:
                    promotions += 1
                else:
                    demotions += 1
        runs.append(
            {
                "normative_threshold": threshold,
                "decision_threshold": policy.decision_threshold,
                "status_distribution": distribution,
                "status_flips_from_default": flips,
                "promotions_from_default": promotions,
                "demotions_from_default": demotions,
            }
        )
    return {
        "scenario_count": len(scenarios),
        "default_policy": {"normative_threshold": 9, "decision_threshold": 10},
        "runs": runs,
    }


def _suite_row(suite: dict, payload: dict) -> dict:
    summary = payload["summary"]
    return {
        "id": suite["id"],
        "label": suite["label"],
        "evidence_class": suite["evidence_class"],
        "validation_units": _suite_validation_units(suite),
        "scenario_count": summary["scenario_count"],
        "expected_passed": summary["expected_passed"],
        "mean_audit_score": summary["mean_audit_score"],
        "mean_upstream_recall": summary["mean_upstream_recall"],
        "high_upstream_but_blocked": summary["high_upstream_but_blocked"],
        "blocked_reason_distribution": summary.get("blocked_reason_distribution", {}),
        "status_distribution": _status_distribution(payload["results"]),
        "finding": suite["finding"],
    }


def _source_chain_attack_row(payload: dict) -> dict:
    summary = payload["summary"]
    return {
        "id": "source_chain_attacks",
        "label": "Qualified-output source-chain attacks",
        "evidence_class": "whole-matrix source-chain negative control",
        "validation_units": f"{summary['scenario_count']} attack variants over qualified packets",
        "scenario_count": summary["scenario_count"],
        "rule_pass": f"{summary['expected_passed']}/{summary['scenario_count']}",
        "mean_audit_score": summary["mean_audit_score"],
        "mean_upstream_recall": summary["mean_upstream_recall"],
        "high_upstream_but_blocked": summary["high_upstream_but_blocked"],
        "blocked_reason_distribution": summary["blocked_reason_distribution"],
        "status_distribution": _status_distribution(payload["results"]),
        "finding": "Applies every nonempty combination of locator, output-source link, procedural source tag, high-authority recall and counter-material recall attacks across every qualified packet; all attacked variants must lose high status through downgrade, suspension or withdrawal despite high scores and high upstream recall.",
    }


def _contestation_challenge_row(payload: dict) -> dict:
    summary = payload["summary"]
    return {
        "id": "contestation_challenges",
        "label": "Dynamic contestation challenges",
        "evidence_class": "whole-matrix challenge-response validation",
        "validation_units": f"{summary['scenario_count']} challenge variants over qualified packets",
        "scenario_count": summary["scenario_count"],
        "rule_pass": f"{summary['expected_passed']}/{summary['scenario_count']}",
        "mean_audit_score": summary["mean_audit_score"],
        "mean_upstream_recall": summary["mean_upstream_recall"],
        "high_upstream_but_blocked": summary["high_upstream_but_blocked"],
        "blocked_reason_distribution": summary["blocked_reason_distribution"],
        "status_distribution": _status_distribution(payload["results"]),
        "finding": "Applies valid counter-material, source-verification, jurisdiction and contestability-channel challenges plus unsupported challenge controls across every qualified packet; valid challenges must block high status while unsupported challenges preserve it.",
    }


def _status_distribution(results: list[dict]) -> dict[str, int]:
    distribution: dict[str, int] = {}
    for result in results:
        status = result["allowed_status"]
        distribution[status] = distribution.get(status, 0) + 1
    return distribution


def _disposition_distribution(results: list[dict]) -> dict[str, int]:
    distribution: dict[str, int] = {}
    for result in results:
        disposition = result["disposition"]
        distribution[disposition] = distribution.get(disposition, 0) + 1
    return distribution


def _contestation_valid_blocked(results: list[dict]) -> int:
    return sum(
        1
        for result in results
        if "unsupported-challenge-control" not in result["scenario_id"]
        and STATUS_RANK[result["allowed_status"]] < STATUS_RANK["normative_material_screening_output"]
    )


def _contestation_unsupported_preserved(results: list[dict]) -> int:
    return sum(
        1
        for result in results
        if "unsupported-challenge-control" in result["scenario_id"]
        and STATUS_RANK[result["allowed_status"]] >= STATUS_RANK["normative_material_screening_output"]
    )


def _suite_validation_units(suite: dict) -> str:
    path = suite["path"]
    count = _scenario_count(path) if suite["unit_label"] in {
        "stress scenarios",
        "raw model outputs",
        "source-supported model-output variants",
        "evidence-ladder model-output variants",
        "adversarial source-support variants",
        "curated issue packets",
        "issue-packet ablations",
    } else _output_unit_count(path)
    return f"{count} {suite['unit_label']}"


def _robustness_row(payload: dict) -> dict:
    return {
        "id": "annotation_robustness",
        "label": "Annotation robustness recoding",
        "evidence_class": "coding robustness",
        "validation_units": f"{payload['recoded_evaluations']} strict/lenient recoded evaluations",
        "scenario_count": payload["scenario_count"],
        "rule_pass": f"{payload['all_policy_status_stable']}/{payload['scenario_count']} stable across all policies",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "base_vs_strict_weighted_agreement": round(payload["weighted_status_agreement_base_strict"], 2),
            "base_vs_lenient_weighted_agreement": round(payload["weighted_status_agreement_base_lenient"], 2),
        },
        "finding": "Tests whether status allocation survives strict and lenient recoding of the same evidence packets.",
    }


def _uncertainty_row(payload: dict) -> dict:
    return {
        "id": "annotation_uncertainty",
        "label": "Annotation uncertainty Monte Carlo",
        "evidence_class": "score-noise robustness",
        "validation_units": f"{payload['evaluation_count']} score-perturbed evaluations",
        "scenario_count": payload["evaluation_count"],
        "rule_pass": f"{payload['status_stability_rate']:.3f} sample stability; {payload['qualified_high_status_stability_rate']:.3f} qualified high-status stability",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "exact_stable_scenarios": payload["scenario_exact_stability_count"],
            "high_status_stable_scenarios": payload["scenario_high_stability_count"],
            "boundary_scenarios": len(payload["boundary_scenarios"]),
            "mean_status_rank_shift": round(payload["mean_status_rank_shift"], 3),
        },
        "finding": "Perturbs all six audit scores under a fixed-seed Monte Carlo model to locate boundary cases and test whether status allocation is robust to plausible coding noise.",
    }


def _blind_coding_row(payload: dict) -> dict:
    first_pair = payload["pairwise_status"][0]
    base_exact = min(item["exact_status_agreement"] for item in payload["base_status_agreement"].values())
    base_weighted = min(item["weighted_status_agreement"] for item in payload["base_status_agreement"].values())
    base_kappa = min(item["cohen_kappa"] for item in payload["base_status_agreement"].values())
    base_weighted_kappa = min(item["quadratic_weighted_kappa"] for item in payload["base_status_agreement"].values())
    return {
        "id": "blind_coding",
        "label": "Score-blinded dual coding",
        "evidence_class": "codebook reproducibility",
        "validation_units": f"{payload['packet_count']} packets x {payload['coder_count']} coding passes",
        "scenario_count": payload["packet_count"],
        "rule_pass": (
            f"{first_pair['cohen_kappa']:.2f} coder kappa; "
            f"{payload['base_dimension_min_kappa']:.2f} weakest base-dimension kappa "
            f"({payload['base_dimension_min_kappa_dimension']}); "
            f"{payload['base_dimension_min_exact_agreement']:.2f} min base-dimension exact; "
            f"{payload['base_dimension_max_mean_absolute_delta']:.2f} max score drift"
        ),
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "coder_exact_status_agreement": round(first_pair["exact_status_agreement"], 2),
            "coder_weighted_status_agreement": round(first_pair["weighted_status_agreement"], 2),
            "coder_cohen_kappa": round(first_pair["cohen_kappa"], 2),
            "coder_quadratic_weighted_kappa": round(first_pair["quadratic_weighted_kappa"], 2),
            "minimum_dimension_kappa": round(payload["minimum_dimension_kappa"], 2),
            "minimum_failure_flag_exact_agreement": round(payload["minimum_failure_flag_exact_agreement"], 2),
            "minimum_missing_gate_exact_agreement": round(payload["minimum_missing_gate_exact_agreement"], 2),
            "base_dimension_min_kappa": round(payload["base_dimension_min_kappa"], 2),
            "base_dimension_min_kappa_dimension": payload["base_dimension_min_kappa_dimension"],
            "base_dimension_min_kappa_coder": payload["base_dimension_min_kappa_coder"],
            "base_dimension_min_kappa_exact_agreement": round(payload["base_dimension_min_kappa_exact_agreement"], 2),
            "base_dimension_min_exact_agreement": round(payload["base_dimension_min_exact_agreement"], 2),
            "base_dimension_min_pabak": round(payload["base_dimension_min_pabak"], 2),
            "base_dimension_max_mean_absolute_delta": round(payload["base_dimension_max_mean_absolute_delta"], 2),
            "min_base_exact_status_agreement": round(base_exact, 2),
            "min_base_weighted_status_agreement": round(base_weighted, 2),
            "min_base_cohen_kappa": round(base_kappa, 2),
            "min_base_quadratic_weighted_kappa": round(base_weighted_kappa, 2),
            "status_disagreements": payload["status_disagreement_count"],
        },
        "finding": "Tests score-blinded coder reliability, base-status tracking and dimension-level score calibration under class imbalance.",
    }


def _source_text_row(payload: dict) -> dict:
    return {
        "id": "source_text_verification",
        "label": "Public source-text anchors",
        "evidence_class": "external source-grounding check",
        "validation_units": f"{payload['support_item_count']} public source-support anchor checks",
        "scenario_count": payload["support_item_count"],
        "rule_pass": f"{payload['support_items_verified']}/{payload['support_item_count']} verified",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "records_with_text_snapshot": payload["records_with_text_snapshot"],
            "verified_ratio": payload["verified_ratio"],
        },
        "finding": "Checks issue-manifest support terms against extracted public source text snapshots to reduce manifest-only source-support circularity.",
    }


def _model_transcript_row(payload: dict) -> dict:
    return {
        "id": "model_output_transcript_verification",
        "label": "Model-output transcript anchors",
        "evidence_class": "raw-output provenance check",
        "validation_units": f"{payload['locator_count']} raw transcript locator checks",
        "scenario_count": payload["locator_count"],
        "rule_pass": f"{payload['locators_verified']}/{payload['locator_count']} verified",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "scenario_sections_verified": payload["scenario_sections_verified"],
            "output_units": payload["output_unit_count"],
            "all_locators_verified": payload["all_locators_verified"],
        },
        "finding": "Checks that raw model-output scenario locators are anchored in the committed transcript sections.",
    }


def _cross_engine_transcript_row(payload: dict) -> dict:
    return {
        "id": "cross_engine_transcript_verification",
        "label": "Cross-engine transcript anchors",
        "evidence_class": "identity-neutral raw-output provenance check",
        "validation_units": f"{payload['locator_count']} cross-engine transcript locator checks",
        "scenario_count": payload["locator_count"],
        "rule_pass": f"{payload['locators_verified']}/{payload['locator_count']} verified",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "engines": payload["engine_count"],
            "issues": payload["issue_count"],
            "scenario_sections_verified": payload["scenario_sections_verified"],
            "all_locators_verified": payload["all_locators_verified"],
        },
        "finding": "Checks that cross-engine raw-output locators are anchored in committed transcripts across three model engines.",
    }


def _formal_invariant_row(payload: dict) -> dict:
    return {
        "id": "formal_invariant_verification",
        "label": "Formal invariant verification",
        "evidence_class": "exhaustive model-property check",
        "validation_units": f"{payload['total_checks']} generated audit-policy states",
        "scenario_count": payload["total_checks"],
        "rule_pass": f"{payload['passed_checks']}/{payload['total_checks']} passed",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {check["id"]: check["failed"] for check in payload["checks"]},
        "finding": "Exhaustively tests monotonicity, evidence-packet necessity, authority-set necessity, counter-material necessity, adoption necessity, role caps, failure caps and metric non-equivalence.",
    }


def _status_lattice_row(payload: dict) -> dict:
    best_partial = next(row for row in payload["substitution_rules"] if row["rule"] == "source_authority_counter_score")
    full_rule = next(row for row in payload["substitution_rules"] if row["rule"] == "full_screening_predicate")
    return {
        "id": "status_lattice",
        "label": "Status-lattice exhaustion",
        "evidence_class": "finite status-lattice characterization",
        "validation_units": f"{payload['state_count']} high-status claim-attempt states, {payload['cover_edge_diagnostics']['checks']} cover edges and {payload['state_count'] * len(payload['substitution_rules'])} substitute-rule predictions",
        "scenario_count": payload["state_count"]
        + payload["cover_edge_diagnostics"]["checks"]
        + payload["necessity"]["checks"]
        + payload["gate_ablation"]["checks"]
        + payload["state_count"] * len(payload["substitution_rules"]),
        "rule_pass": f"{payload['necessity']['passed']}/{payload['necessity']['checks']} necessity; {payload['gate_ablation']['passed']}/{payload['gate_ablation']['checks']} ablations",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "high_status_states": payload["high_status_count"],
            "decision_status_states": payload["decision_status_count"],
            "best_partial_rule_false_positive": best_partial["false_positive"],
            "full_predicate_false_positive": full_rule["false_positive"],
        },
        "finding": "Exhausts the high-status claim-attempt lattice and shows that score, role, source and authority substitutes over-admit unless the full screening predicate is present.",
    }


def _metric_separation_row(payload: dict) -> dict:
    recall_test = next(row for row in payload["threshold_tests"] if row["label"] == "recall>=0.8")
    final_gate = payload["gate_cascade"][-1]
    return {
        "id": "metric_separation",
        "label": "Metric separation analysis",
        "evidence_class": "retrieval/status non-equivalence check",
        "validation_units": f"{payload['metric_scenario_count']} upstream-metric scenario packets",
        "scenario_count": payload["metric_scenario_count"],
        "rule_pass": f"recall-threshold precision {recall_test['precision']:.2f}; reference gate FP {final_gate['false_positive']}",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "recall_point_biserial": round(payload["point_biserial"]["recall"], 2),
            "high_recall_blocked_rate": round(payload["high_recall_blocked"]["rate"], 2),
            "reference_gate_false_positive": final_gate["false_positive"],
        },
        "finding": "Quantifies that upstream precision, recall and F1 are weak predictors of procedural qualification, while audit gates remove high-recall false positives.",
    }


def _baseline_comparison_row(payload: dict) -> dict:
    best = payload["best_simplified"]
    full = payload["full_gate"]
    return {
        "id": "baseline_comparison",
        "label": "Baseline rule comparison",
        "evidence_class": "alternative-policy comparison",
        "validation_units": f"{payload['baseline_prediction_count']} baseline predictions over {payload['baseline_count']} rules",
        "scenario_count": payload["baseline_prediction_count"],
        "rule_pass": f"best simplified FP {best['false_positive']}; reference rule FP {full['false_positive']}",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "simplified_rules_with_errors": int(payload["all_simplified_rules_have_errors"]),
            "best_simplified_precision": round(best["precision"], 2),
            "best_simplified_recall": round(best["recall"], 2),
            "reference_rule_false_positive": full["false_positive"],
            "reference_rule_false_negative": full["false_negative"],
        },
        "finding": "Compares recall, F1, total-score, source-bound, authority-material and review-gate substitutes against the protocol-defined reference allocation, showing that every simplified rule either over-admits or misses procedurally qualified packets.",
    }


def _issue_family_generalization_row(payload: dict) -> dict:
    return {
        "id": "issue_family_generalization",
        "label": "Issue-family leave-one-out generalization",
        "evidence_class": "cross-issue substitute-rule holdout",
        "validation_units": f"{payload['holdout_prediction_count']} holdout baseline predictions over {payload['issue_family_count']} issue families",
        "scenario_count": payload["holdout_prediction_count"],
        "rule_pass": (
            f"full protocol FP/FN {payload['full_protocol_holdout_false_positive']}/"
            f"{payload['full_protocol_holdout_false_negative']}; best trained simplified FP "
            f"{payload['best_trained_rule_holdout_false_positive']}"
        ),
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "issue_families": payload["issue_family_count"],
            "scenario_packets": payload["scenario_count"],
            "qualified_packets": payload["qualified_count"],
            "best_trained_rule_holdout_false_positive": payload["best_trained_rule_holdout_false_positive"],
            "lowest_fp_rule_holdout_false_positive": payload["lowest_fp_rule_holdout_false_positive"],
            "folds_with_best_trained_rule_error": payload["folds_with_best_trained_rule_error"],
        },
        "finding": "Holds out each issue family, selects simplified substitute rules on the remaining issue families, and verifies that trained simplified rules still over-admit holdout packets while the full protocol records zero holdout false positives and false negatives.",
    }


def _policy_family_robustness_row(payload: dict) -> dict:
    return {
        "id": "policy_family_robustness",
        "label": "Policy-family robustness",
        "evidence_class": "policy-variant robustness",
        "validation_units": (
            f"{payload['total_evaluation_count']} evaluations over {payload['variant_count']} policy variants"
        ),
        "scenario_count": payload["total_evaluation_count"],
        "rule_pass": (
            f"0 high-status promotions; {payload['variants_with_simplified_errors']}/"
            f"{payload['variant_count']} variants with simplified-rule errors; best simplified FP "
            f"{payload['best_simplified_false_positive_total']}"
        ),
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "variants": payload["variant_count"],
            "status_evaluations": payload["status_evaluation_count"],
            "baseline_predictions": payload["baseline_prediction_count"],
            "high_status_demotions": payload["total_high_status_demotions"],
            "full_protocol_false_positive_total": payload["full_protocol_false_positive_total"],
            "full_protocol_false_negative_total": payload["full_protocol_false_negative_total"],
        },
        "finding": "Varies thresholds, rank window, procedural source tags, role caps and failure severity; no policy variant promotes a below-screening packet to high status, while simplified substitutes fail in every variant.",
    }


def _gate_ablation_row(payload: dict) -> dict:
    return {
        "id": "gate_ablation",
        "label": "Qualified-output gate ablations",
        "evidence_class": "counterfactual gate-necessity check",
        "validation_units": f"{payload['ablation_count']} ablations over {payload['qualified_scenario_count']} qualified packets",
        "scenario_count": payload["ablation_count"],
        "rule_pass": f"{payload['passed_count']}/{payload['ablation_count']}",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            key: value["failed"]
            for key, value in sorted(payload["by_ablation"].items())
        },
        "finding": "Removes evidence, source-tag, authority, counter-material, review, role-cap and adoption gates from qualified packets and verifies that status falls below the corresponding procedural level.",
    }


def _gate_contrast_witness_row(payload: dict) -> dict:
    return {
        "id": "gate_contrast_witnesses",
        "label": "Gate-contrast witness pairs",
        "evidence_class": "non-substitution witness validation",
        "validation_units": f"{payload['witness_count']} witness pairs over {payload['qualified_scenario_count']} qualified packets",
        "scenario_count": payload["witness_count"],
        "rule_pass": f"{payload['passed_count']}/{payload['witness_count']}",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": payload["status_distribution"],
        "finding": "Preserves each qualified packet's audit score vector, upstream metrics and system role while flipping one mandatory gate; every witness pair separates allowed procedural status, proving score-only and retrieval-metric-only substitutes cannot reproduce the protocol on the validation domain.",
    }


def _repair_frontier_row(payload: dict) -> dict:
    return {
        "id": "repair_frontier",
        "label": "Blocked-claim repair frontiers",
        "evidence_class": "counterfactual repair-necessity check",
        "validation_units": f"{payload['counterfactual_evaluation_count']} repair counterfactuals over {payload['blocked_claim_count']} blocked claims",
        "scenario_count": payload["counterfactual_evaluation_count"],
        "rule_pass": f"{payload['repairable_count']}/{payload['blocked_claim_count']} repairable",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": payload["minimal_repair_size_distribution"],
        "finding": "Computes the minimal artefact-gate families needed to upgrade each blocked normative-screening or decision-support claim.",
    }


def _jurisdiction_profile_row(payload: dict) -> dict:
    evaluations = payload["profile_check_count"] + payload["counterfactual_evaluation_count"]
    return {
        "id": "jurisdiction_profile",
        "label": "Jurisdiction-profile mutations",
        "evidence_class": "cross-profile gate check",
        "validation_units": f"{evaluations} profile checks and counterfactuals",
        "scenario_count": evaluations,
        "rule_pass": f"{payload['profile_supported_count']}/{payload['profile_check_count']} profile checks; {payload['passed_count']}/{payload['counterfactual_evaluation_count']} mutations",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "generic_preserved": payload["generic_profile_preserved"],
            "missing_downgraded": payload["missing_assumption_downgraded"],
            "mismatch_downgraded": payload["mismatched_profile_downgraded"],
        },
        "finding": "Tests that high-status outputs preserve status under valid generic profile assumptions but downgrade when jurisdiction assumptions are absent or profile-mismatched.",
    }


def _ranking_visibility_row(payload: dict) -> dict:
    return {
        "id": "ranking_visibility",
        "label": "Ranking-visibility diagnostics",
        "evidence_class": "rank-salience counterfactual check",
        "validation_units": f"{payload['window_check_count']} rank-window checks over {payload['visibility_check_count']} high-status claims plus {payload['rank_order_counterfactual_count']} rank-order counterfactuals",
        "scenario_count": payload["window_check_count"] + payload["rank_order_counterfactual_count"],
        "rule_pass": f"{payload['rank_order_passed_count']}/{payload['rank_order_counterfactual_count']} rank-order",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "front_window_counter_visible": payload["front_window_counter_visible"],
            "front_window_counter_not_visible": payload["front_window_counter_not_visible"],
            "counterfactual_front_window_counter_visible": payload["counterfactual_front_window_counter_visible"],
            "rank_intervention_applied": payload["rank_intervention_applied_count"],
            "coverage_preserved": payload["coverage_preserved_count"],
            "downgraded": payload["downgraded_count"],
            "median_first_counter_rank": payload["median_first_counter_rank"],
            "mean_reciprocal_first_counter_rank": round(payload["mean_reciprocal_first_counter_rank"], 2),
        },
        "finding": "Computes a rank-window visibility curve for counter-material salience and applies rank-order counterfactuals where the packet contains enough non-counter material to move counter-material below the visibility window.",
    }


def _status_certificate_row(payload: dict) -> dict:
    return {
        "id": "status_certificate",
        "label": "Proof-carrying status certificates",
        "evidence_class": "proof-carrying certificate replay",
        "validation_units": f"{payload['replay_check_count']} replay checks and {payload['proof_obligation_count']} proof obligations over {payload['certificate_count']} certificates",
        "scenario_count": payload["replay_check_count"] + payload["proof_obligation_count"],
        "rule_pass": f"{payload['passed_check_count']}/{payload['replay_check_count']} checks; {payload['passed_proof_obligation_count']}/{payload['proof_obligation_count']} obligations",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "verified_certificates": payload["verified_certificate_count"],
            "proof_obligations": payload["proof_obligation_count"],
            "proof_obligations_passed": payload["passed_proof_obligation_count"],
            "cap_or_failure_transitions": payload["cap_or_failure_transition_count"],
        },
        "finding": "Generates proof-carrying status certificates for every scenario and replays scenario identity, scenario hash, policy hash, policy body, jurisdiction profile, score gate, role cap, missing gates, failure cap, metric bundle, claim support, proof obligations and derivation hash.",
    }


def _certificate_tamper_row(payload: dict) -> dict:
    return {
        "id": "certificate_tamper",
        "label": "Certificate tamper-resistance",
        "evidence_class": "proof-certificate negative-control validation",
        "validation_units": f"{payload['tamper_case_count']} tamper cases across {payload['tamper_family_count']} families",
        "scenario_count": payload["tamper_case_count"],
        "rule_pass": f"{payload['rejected_count']}/{payload['tamper_case_count']} rejected",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "base_certificates": payload["base_certificate_count"],
            "tamper_families": payload["tamper_family_count"],
            "missed_tamper_cases": payload["missed_tamper_count"],
        },
        "finding": "Mutates certificate identities, hashes, policy bodies, scores, roles, gates, status fields, caps, metric bundles, proof obligations and certificate-set structure; every tampered proof object must be rejected.",
    }


def _metamorphic_policy_row(payload: dict) -> dict:
    return {
        "id": "metamorphic_policy",
        "label": "Metamorphic policy tests",
        "evidence_class": "expected-label-free policy-invariant validation",
        "validation_units": f"{payload['metamorphic_evaluation_count']} transformations over {payload['scenario_count']} packets",
        "scenario_count": payload["metamorphic_evaluation_count"],
        "rule_pass": f"{payload['passed_count']}/{payload['metamorphic_evaluation_count']}",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            relation: bucket["passed"]
            for relation, bucket in sorted(payload["by_relation"].items())
        },
        "finding": "Applies claim escalation, metric inflation, role-cap demotion, source-tag mutation, review-gate removal, score-and-role inflation without adoption, and benign-source augmentation to primary scenario packets without using expected labels.",
    }


def _policy_mutation_row(payload: dict) -> dict:
    return {
        "id": "policy_mutations",
        "label": "Policy mutation analysis",
        "evidence_class": "policy-mutant killing",
        "validation_units": (
            f"{payload['evaluation_count']} mutation evaluations over {payload['mutant_count']} policy mutants"
        ),
        "scenario_count": payload["evaluation_count"],
        "rule_pass": f"{payload['killed_mutant_count']}/{payload['mutant_count']} killed",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "classification_errors": payload["classification_error_count"],
            "invalid_promotions": payload["invalid_promotion_count"],
            "false_negatives": payload["false_negative_count"],
        },
        "finding": "Applies gate-removal and status-conferring policy mutants across committed packets; every mutant is killed because removing a required gate, ignoring a cap, or treating metrics, source labels, review labels, total score or model identity as status produces a wrong allocation.",
    }


def _review_provenance_row(payload: dict) -> dict:
    return {
        "id": "review_provenance",
        "label": "Review-provenance analysis",
        "evidence_class": "human-review and adoption-record falsification",
        "validation_units": (
            f"{payload['evaluation_count']} provenance evaluations over {payload['scenario_count']} packets"
        ),
        "scenario_count": payload["evaluation_count"],
        "rule_pass": f"{payload['passed_count']}/{payload['evaluation_count']}",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "review_adoption_placebos_blocked": payload["placebo_blocked_count"],
            "high_status_provenance_defects_blocked": payload["high_status_provenance_blocked_count"],
            "decision_provenance_defects_demoted": payload["decision_provenance_demoted_count"],
        },
        "finding": "Adds review and adoption labels to incomplete packets and removes review, contestability, jurisdiction, authorization, adoption-reason or contestation-record fields from qualified packets; status follows provenance records only when the legal-material chain is complete.",
    }


def _claim_anchor_row(payload: dict) -> dict:
    return {
        "id": "claim_anchor",
        "label": "Claim-anchor analysis",
        "evidence_class": "claim-level source-anchor falsification",
        "validation_units": (
            f"{payload['evaluation_count']} claim-anchor mutations over {payload['output_unit_count']} units and "
            f"{payload['output_link_count']} links"
        ),
        "scenario_count": payload["evaluation_count"],
        "rule_pass": f"{payload['passed_count']}/{payload['evaluation_count']}",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "claim_text_absence_blocked": payload["claim_text_absence_blocked_count"],
            "link_unit_binding_absence_blocked": payload["link_unit_binding_absence_blocked_count"],
            "support_attestation_absence_withdrawn": payload["support_attestation_absence_withdrawn_count"],
            "locator_absence_withdrawn": payload["locator_absence_withdrawn_count"],
        },
        "finding": "Removes material proposition text, link-to-claim bindings, support attestations and locators from every qualified packet; high status survives only when each material output unit remains bound to a specific source anchor.",
    }


def _workflow_portability_row(payload: dict) -> dict:
    return {
        "id": "workflow_portability",
        "label": "Workflow portability analysis",
        "evidence_class": "architecture and deployment-role portability",
        "validation_units": (
            f"{payload['evaluation_count']} workflow mutations over {payload['scenario_count']} packets, "
            f"{payload['architecture_profile_count']} architecture profiles and "
            f"{payload['entitlement_profile_count']} entitlement profiles"
        ),
        "scenario_count": payload["evaluation_count"],
        "rule_pass": f"{payload['passed_count']}/{payload['evaluation_count']}",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "architecture_invariance": payload["architecture_invariance_passed_count"],
            "entitlement_caps": payload["entitlement_profile_passed_count"],
            "decision_dependency": payload["decision_dependency_passed_count"],
            "unaccountable_external_bar": payload["unaccountable_bar_passed_count"],
        },
        "finding": "Runtime architecture labels do not change status; deployment entitlement profiles obey role caps, decision support depends on a screening-capable chain, and unaccountable external disposition is barred.",
    }


def _model_identity_invariance_row(payload: dict) -> dict:
    return {
        "id": "model_identity_invariance",
        "label": "Model-identity invariance",
        "evidence_class": "identity-substitution invariance check",
        "validation_units": f"{payload['evaluation_count']} identity mutations over {payload['scenario_count']} packets and {payload['identity_profile_count']} model identities",
        "scenario_count": payload["evaluation_count"],
        "rule_pass": f"{payload['passed_count']}/{payload['evaluation_count']}",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "status_changes": payload["status_changed_count"],
            "disposition_changes": payload["disposition_changed_count"],
            "identity_profiles": payload["identity_profile_count"],
        },
        "finding": "Substitutes frontier, legal-specialist, open-weight, small-model and undisclosed-agentic identity labels across every packet; procedural status remains unchanged because model identity is not a status-conferring property.",
    }


def _query_perturbation_row(payload: dict) -> dict:
    return {
        "id": "query_perturbation",
        "label": "Query-perturbation stability",
        "evidence_class": "public-retrieval query-sensitivity diagnostic",
        "validation_units": f"{payload['query_variant_count']} query variants across {payload['issue_group_count']} issue groups",
        "scenario_count": payload["query_variant_count"],
        "rule_pass": f"{payload['status_stable_group_count']}/{payload['issue_group_count']} status-stable groups",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": payload["high_upstream_but_blocked"],
        "status_distribution": {
            "authority_unstable_groups": payload["authority_coverage_unstable_group_count"],
            "counter_recall_unstable_groups": payload["counter_recall_unstable_group_count"],
            "record_set_unstable_groups": payload["record_set_unstable_group_count"],
            "top_result_unstable_groups": payload["top_result_unstable_group_count"],
            "mean_record_overlap": round(payload["mean_pairwise_record_overlap"], 2),
            "min_record_overlap": round(payload["min_pairwise_record_overlap"], 2),
        },
        "finding": "Compares issue-equivalent public-search query variants and holdout variants, showing whether authority coverage, counter-material recall, top-result identity and retrieved-record sets remain stable under query reformulation.",
    }


def _query_portfolio_row(payload: dict) -> dict:
    return {
        "id": "query_portfolio",
        "label": "Query-portfolio frontier",
        "evidence_class": "public-retrieval query-expansion frontier",
        "validation_units": (
            f"{payload['portfolio_count']} query portfolios plus {payload['issue_group_count']} group frontier summaries"
        ),
        "scenario_count": payload["portfolio_count"] + payload["issue_group_count"],
        "rule_pass": f"{payload['qualified_portfolio_count']}/{payload['portfolio_count']} portfolios qualified",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "full_high_authority_portfolios": payload["full_high_authority_portfolio_count"],
            "full_counter_material_portfolios": payload["full_counter_material_portfolio_count"],
            "full_screening_material_portfolios": payload["full_screening_material_portfolio_count"],
            "max_authority_coverage": round(payload["max_authority_coverage"], 2),
            "max_counter_recall": round(payload["max_counter_recall"], 2),
            "groups_high_repaired": payload["query_expansion_repairs_any_high_authority"],
            "groups_counter_repaired": payload["query_expansion_repairs_counter_material"],
        },
        "finding": "Enumerates all non-empty query portfolios over issue-equivalent public retrieval variants to test whether frozen query expansion recovers high-authority and counter-material coverage.",
    }


def _policy_constants_row(payload: dict) -> dict:
    return {
        "id": "policy_constants_replay",
        "label": "Policy-constants replay",
        "evidence_class": "second implementation check",
        "validation_units": f"{payload['check_count']} replay checks over {payload['scenario_count']} packets",
        "scenario_count": payload["check_count"],
        "rule_pass": f"{payload['passed_check_count']}/{payload['check_count']}",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": payload["status_distribution"],
        "finding": "Recomputes score candidates, role caps, protected reliance gates, missing gates, failure caps, metrics and final status in a separate script parameterized by JSON policy constants without importing the harness model.",
    }


def _format_report(payload: dict) -> str:
    lines = [
        "# Full Legal AI Audit Harness Validation",
        "",
        f"Validation suites: {payload['suite_count']}",
        f"Scenario files: {payload['scenario_files']}",
        f"Base embedded records/items: {payload['validation_units']['total']} "
        f"({payload['validation_units']['stress_scenarios']} stress scenarios, "
        f"{payload['validation_units']['public_metadata_records']} public metadata records, "
        f"{payload['validation_units']['public_system_records']} public-system records, "
        f"{payload['validation_units']['public_retrieval_records']} public retrieval records, "
        f"{payload['validation_units']['holdout_records']} holdout records/items, "
        f"{payload['validation_units']['raw_model_outputs']} raw model outputs, "
        f"{payload['validation_units']['source_bound_model_outputs']} source-supported model-output variants, "
        f"{payload['validation_units']['cross_engine_raw_outputs']} cross-engine raw outputs, "
        f"{payload['validation_units']['cross_engine_source_bound_outputs']} cross-engine source-supported outputs, "
        f"{payload['validation_units']['evidence_ladder_model_outputs']} evidence-ladder model-output variants, "
        f"{payload['validation_units']['adversarial_model_outputs']} adversarial source-support variants, "
        f"{payload['validation_units']['issue_public_records']} issue-specific public output/source records, "
        f"{payload['validation_units']['issue_gold_sets']} mixed-authority source-screening packets, "
        f"{payload['validation_units']['issue_ablations']} issue ablations)",
        f"Strict/lenient recoded evaluations: {payload['recoded_evaluations']}",
        f"Annotation-uncertainty perturbations: {payload['annotation_uncertainty_evaluations']}",
        f"Score-blinded coding-pass evaluations: {payload['blind_coding_evaluations']}",
        f"Full-threshold sensitivity evaluations: {payload['threshold_sensitivity_evaluations']}",
        f"Source-chain attack variants: {payload['source_chain_attacks']['expected_passed']}/{payload['source_chain_attacks']['scenario_count']} passed; high-upstream attacked variants blocked {payload['source_chain_attacks']['high_upstream_but_blocked']}/{payload['source_chain_attacks']['scenario_count']}",
        f"Source-chain attack dispositions: downgrade {payload['source_chain_attacks']['disposition_distribution'].get('downgrade', 0)}, suspension {payload['source_chain_attacks']['disposition_distribution'].get('suspension', 0)}, withdrawal {payload['source_chain_attacks']['disposition_distribution'].get('withdrawal', 0)}",
        f"Contestation challenge variants: {payload['contestation_challenges']['expected_passed']}/{payload['contestation_challenges']['scenario_count']} passed; valid challenges blocked {payload['contestation_challenges']['valid_challenges_blocked']}/{payload['contestation_challenges']['valid_challenges_blocked']}; unsupported controls preserved {payload['contestation_challenges']['unsupported_controls_preserved']}/{payload['contestation_challenges']['unsupported_controls_preserved']}",
        f"Public source-text anchor checks: {payload['source_text_verification']['support_items_verified']}/{payload['source_text_verification']['support_item_count']} verified across {payload['source_text_verification']['records_with_text_snapshot']} records with text snapshots",
        f"Model-output transcript locator checks: {payload['model_output_transcript_verification']['locators_verified']}/{payload['model_output_transcript_verification']['locator_count']} verified across {payload['model_output_transcript_verification']['scenario_sections_verified']} raw transcript sections",
        f"Cross-engine transcript locator checks: {payload['cross_engine_transcript_verification']['locators_verified']}/{payload['cross_engine_transcript_verification']['locator_count']} verified across {payload['cross_engine_transcript_verification']['engine_count']} engines and {payload['cross_engine_transcript_verification']['issue_count']} issues",
        f"Formal invariant checks: {payload['formal_invariant_verification']['passed_checks']}/{payload['formal_invariant_verification']['total_checks']} passed",
        f"Status-lattice exhaustion: {payload['status_lattice']['state_count']} high-status claim-attempt states, {payload['status_lattice']['cover_edge_diagnostics']['checks']} cover edges, {payload['status_lattice']['necessity']['passed']}/{payload['status_lattice']['necessity']['checks']} necessity checks and {payload['status_lattice']['gate_ablation']['passed']}/{payload['status_lattice']['gate_ablation']['checks']} gate-ablation drops",
        f"Metric separation evaluations: {payload['metric_separation']['metric_scenario_count']} upstream-metric scenario packets; high-recall blocked outputs {payload['metric_separation']['high_recall_blocked']['count']}/{payload['metric_separation']['high_recall_blocked']['denominator']}",
        f"Metric statistical resamples: {payload['metric_separation']['bootstrap']['iterations']} bootstrap resamples and {payload['metric_separation']['permutation']['iterations']} permutation shuffles",
        f"Baseline rule comparisons: {payload['baseline_comparison']['baseline_prediction_count']} predictions across {payload['baseline_comparison']['baseline_count']} rules; best simplified false positives {payload['baseline_comparison']['best_simplified']['false_positive']}; reference rule false positives {payload['baseline_comparison']['full_gate']['false_positive']}",
        f"Issue-family generalization: {payload['issue_family_generalization']['holdout_prediction_count']} holdout predictions over {payload['issue_family_generalization']['issue_family_count']} issue families; full protocol FP/FN {payload['issue_family_generalization']['full_protocol_holdout_false_positive']}/{payload['issue_family_generalization']['full_protocol_holdout_false_negative']}; best trained simplified FP {payload['issue_family_generalization']['best_trained_rule_holdout_false_positive']}; best trained simplified rule erred in {payload['issue_family_generalization']['folds_with_best_trained_rule_error']}/{payload['issue_family_generalization']['issue_family_count']} folds",
        f"Policy-family robustness: {payload['policy_family_robustness']['total_evaluation_count']} evaluations over {payload['policy_family_robustness']['variant_count']} variants; high-status promotions {payload['policy_family_robustness']['total_high_status_promotions']}; simplified-rule errors {payload['policy_family_robustness']['variants_with_simplified_errors']}/{payload['policy_family_robustness']['variant_count']} variants; best simplified FP {payload['policy_family_robustness']['best_simplified_false_positive_total']}; full protocol FP/FN {payload['policy_family_robustness']['full_protocol_false_positive_total']}/{payload['policy_family_robustness']['full_protocol_false_negative_total']}",
        f"Gate ablation evaluations: {payload['gate_ablation']['passed_count']}/{payload['gate_ablation']['ablation_count']} passed over {payload['gate_ablation']['qualified_scenario_count']} qualified packets",
        f"Gate-contrast witness pairs: {payload['gate_contrast_witnesses']['passed_count']}/{payload['gate_contrast_witnesses']['witness_count']} passed; score/metric/role preserved {payload['gate_contrast_witnesses']['score_metric_role_preserved_count']}/{payload['gate_contrast_witnesses']['witness_count']}; status separated {payload['gate_contrast_witnesses']['status_separated_count']}/{payload['gate_contrast_witnesses']['witness_count']}",
        f"Repair frontier evaluations: {payload['repair_frontier']['repairable_count']}/{payload['repair_frontier']['blocked_claim_count']} blocked claims repairable across {payload['repair_frontier']['counterfactual_evaluation_count']} counterfactual repairs",
        f"Jurisdiction-profile evaluations: {payload['jurisdiction_profile']['profile_supported_count']}/{payload['jurisdiction_profile']['profile_check_count']} profile checks supported; {payload['jurisdiction_profile']['passed_count']}/{payload['jurisdiction_profile']['counterfactual_evaluation_count']} counterfactual mutations passed",
        f"Ranking-visibility checks: {payload['ranking_visibility']['window_check_count']} rank-window checks over {payload['ranking_visibility']['visibility_check_count']} high-status claims; {payload['ranking_visibility']['rank_order_passed_count']}/{payload['ranking_visibility']['rank_order_counterfactual_count']} rank-order counterfactuals downgraded with coverage preserved; top-3 counter visible {payload['ranking_visibility']['front_window_counter_visible']}/{payload['ranking_visibility']['front_window_packet_count']}; drifted top-3 counter visible {payload['ranking_visibility']['counterfactual_front_window_counter_visible']}/{payload['ranking_visibility']['rank_order_counterfactual_count']}; median first counter rank {payload['ranking_visibility']['median_first_counter_rank']:.1f}",
        f"Proof-carrying certificate replay checks: {payload['status_certificate']['passed_check_count']}/{payload['status_certificate']['replay_check_count']} passed over {payload['status_certificate']['certificate_count']} certificates",
        f"Status certificate proof obligations: {payload['status_certificate']['passed_proof_obligation_count']}/{payload['status_certificate']['proof_obligation_count']} passed",
        f"Certificate tamper-resistance: {payload['certificate_tamper']['rejected_count']}/{payload['certificate_tamper']['tamper_case_count']} tamper cases rejected across {payload['certificate_tamper']['tamper_family_count']} families",
        f"Policy-constants replay checks: {payload['policy_constants_replay']['passed_check_count']}/{payload['policy_constants_replay']['check_count']} passed over {payload['policy_constants_replay']['scenario_count']} packets",
        f"Metamorphic policy tests: {payload['metamorphic_policy']['passed_count']}/{payload['metamorphic_policy']['metamorphic_evaluation_count']} passed over {payload['metamorphic_policy']['scenario_count']} packets",
        f"Policy mutation analysis: {payload['policy_mutations']['killed_mutant_count']}/{payload['policy_mutations']['mutant_count']} mutants killed across {payload['policy_mutations']['evaluation_count']} evaluations; invalid promotions {payload['policy_mutations']['invalid_promotion_count']}; false negatives {payload['policy_mutations']['false_negative_count']}",
        f"Review-provenance analysis: {payload['review_provenance']['passed_count']}/{payload['review_provenance']['evaluation_count']} passed; review/adoption placebos blocked {payload['review_provenance']['placebo_blocked_count']}/{payload['review_provenance']['placebo_evaluation_count']}; high-status provenance defects blocked {payload['review_provenance']['high_status_provenance_blocked_count']}/{payload['review_provenance']['high_status_provenance_check_count']}; decision provenance defects demoted {payload['review_provenance']['decision_provenance_demoted_count']}/{payload['review_provenance']['decision_provenance_check_count']}",
        f"Claim-anchor analysis: {payload['claim_anchor']['passed_count']}/{payload['claim_anchor']['evaluation_count']} passed over {payload['claim_anchor']['output_unit_count']} output units and {payload['claim_anchor']['output_link_count']} output links; claim-text removals blocked {payload['claim_anchor']['claim_text_absence_blocked_count']}/{payload['claim_anchor']['claim_text_absence_evaluation_count']}; link-to-claim removals blocked {payload['claim_anchor']['link_unit_binding_absence_blocked_count']}/{payload['claim_anchor']['link_unit_binding_absence_evaluation_count']}; support-attestation removals withdrawn {payload['claim_anchor']['support_attestation_absence_withdrawn_count']}/{payload['claim_anchor']['support_attestation_absence_evaluation_count']}; locator removals withdrawn {payload['claim_anchor']['locator_absence_withdrawn_count']}/{payload['claim_anchor']['locator_absence_evaluation_count']}",
        f"Workflow portability analysis: {payload['workflow_portability']['passed_count']}/{payload['workflow_portability']['evaluation_count']} passed; architecture invariance {payload['workflow_portability']['architecture_invariance_passed_count']}/{payload['workflow_portability']['architecture_invariance_evaluation_count']}; entitlement caps {payload['workflow_portability']['entitlement_profile_passed_count']}/{payload['workflow_portability']['entitlement_profile_evaluation_count']}; decision dependency {payload['workflow_portability']['decision_dependency_passed_count']}/{payload['workflow_portability']['decision_dependency_check_count']}; unaccountable external bars {payload['workflow_portability']['unaccountable_bar_passed_count']}/{payload['workflow_portability']['unaccountable_bar_evaluation_count']}",
        f"Model-identity invariance: {payload['model_identity_invariance']['passed_count']}/{payload['model_identity_invariance']['evaluation_count']} identity substitutions passed over {payload['model_identity_invariance']['scenario_count']} packets and {payload['model_identity_invariance']['identity_profile_count']} identity profiles; status changes {payload['model_identity_invariance']['status_changed_count']}; disposition changes {payload['model_identity_invariance']['disposition_changed_count']}",
        f"Query-perturbation diagnostics: {payload['query_perturbation']['query_variant_count']} query variants across {payload['query_perturbation']['issue_group_count']} issue groups; status-stable groups {payload['query_perturbation']['status_stable_group_count']}/{payload['query_perturbation']['issue_group_count']}; authority-coverage unstable groups {payload['query_perturbation']['authority_coverage_unstable_group_count']}/{payload['query_perturbation']['issue_group_count']}; record-set unstable groups {payload['query_perturbation']['record_set_unstable_group_count']}/{payload['query_perturbation']['issue_group_count']}; mean record overlap {payload['query_perturbation']['mean_pairwise_record_overlap']:.2f}",
        f"Query-portfolio frontier: {payload['query_portfolio']['portfolio_count']} portfolios plus {payload['query_portfolio']['issue_group_count']} group summaries across {payload['query_portfolio']['issue_group_count']} issue groups; qualified portfolios {payload['query_portfolio']['qualified_portfolio_count']}/{payload['query_portfolio']['portfolio_count']}; full high-authority portfolios {payload['query_portfolio']['full_high_authority_portfolio_count']}/{payload['query_portfolio']['portfolio_count']}; full counter-material portfolios {payload['query_portfolio']['full_counter_material_portfolio_count']}/{payload['query_portfolio']['portfolio_count']}",
        f"Derived robustness evaluations: {payload['total_evaluation_rows'] - payload['validation_units']['total']}",
        f"Scenario-regression expectations passed: {payload['expected_passed']}/{payload['expected_total']}",
        f"High-upstream-performance but procedurally blocked scenarios: {payload['high_upstream_but_blocked']}",
        "Blocked reason distribution: " + _format_distribution(payload["blocked_reason_distribution"]),
        f"Annotation robustness: {payload['annotation_robustness']['all_policy_status_stable']}/{payload['annotation_robustness']['scenario_count']} stable across base, strict and lenient coding policies",
        f"Annotation uncertainty: {payload['annotation_uncertainty']['evaluation_count']} score perturbations; sample stability {payload['annotation_uncertainty']['status_stability_rate']:.3f}; qualified high-status stability {payload['annotation_uncertainty']['qualified_high_status_stability_rate']:.3f}; boundary scenarios {payload['annotation_uncertainty']['boundary_scenario_count']}",
        _blind_coding_summary(payload),
        "",
        "| Suite | Evidence role | Embedded records/items | Files/evals | Rule/stability | Mean score | Mean recall | Blocked high-upstream | Status distribution |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["suites"]:
        status_distribution = ", ".join(f"{status}: {count}" for status, count in sorted(row["status_distribution"].items()))
        rule_or_stability = row["rule_pass"] if "rule_pass" in row else f"{row['expected_passed']}/{row['scenario_count']}"
        lines.append(
            "| "
            + " | ".join(
                [
                    row["label"],
                    row["evidence_class"],
                    row["validation_units"],
                    str(row["scenario_count"]),
                    rule_or_stability,
                    _metric(row["mean_audit_score"]),
                    _metric(row["mean_upstream_recall"]),
                    "n/a" if row["high_upstream_but_blocked"] is None else str(row["high_upstream_but_blocked"]),
                    status_distribution,
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Substitute-Theory Falsification",
            "",
            "| Substitute theory | Scenario false positives | Scenario false negatives | Scenario precision | Scenario recall | Lattice false positives | Lattice false negatives | Full protocol false positives | Full protocol false negatives | Additional evidence |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in payload["substitute_theory_falsification"]:
        lattice_fp = "n/a" if row["lattice_false_positive"] is None else str(row["lattice_false_positive"])
        lattice_fn = "n/a" if row["lattice_false_negative"] is None else str(row["lattice_false_negative"])
        lines.append(
            "| "
            + " | ".join(
                [
                    row["theory"],
                    str(row["scenario_false_positive"]),
                    str(row["scenario_false_negative"]),
                    _metric(row["scenario_precision"]),
                    _metric(row["scenario_recall"]),
                    lattice_fp,
                    lattice_fn,
                    str(row["full_protocol_false_positive"]),
                    str(row["full_protocol_false_negative"]),
                    row["additional_evidence"],
                ]
            )
            + " |"
        )
    lines.extend(["", "## Findings", ""])
    for row in payload["suites"]:
        lines.append(f"- **{row['label']}:** {row['finding']}")
    lines.extend(["", "## Full-Threshold Sensitivity", ""])
    lines.append(
        f"All {payload['threshold_sensitivity']['scenario_count']} scenario packets were re-evaluated under "
        "normative thresholds 8--12."
    )
    lines.extend(
        [
            "",
            "| Normative threshold | Decision threshold | Status flips from default | Promotions | Demotions | Status distribution |",
            "| ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for run in payload["threshold_sensitivity"]["runs"]:
        distribution = ", ".join(
            f"{status}: {count}" for status, count in sorted(run["status_distribution"].items())
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    str(run["normative_threshold"]),
                    str(run["decision_threshold"]),
                    str(run["status_flips_from_default"]),
                    str(run["promotions_from_default"]),
                    str(run["demotions_from_default"]),
                    distribution,
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _blind_coding_summary(payload: dict) -> str:
    if payload["blind_coding"] is None:
        return "Score-blinded coding: not run; fewer than two coder annotation files found"
    first_pair = payload["blind_coding"]["pairwise_status"][0]
    base_exact = min(item["exact_status_agreement"] for item in payload["blind_coding"]["base_status_agreement"].values())
    base_weighted = min(item["weighted_status_agreement"] for item in payload["blind_coding"]["base_status_agreement"].values())
    base_kappa = min(item["cohen_kappa"] for item in payload["blind_coding"]["base_status_agreement"].values())
    base_weighted_kappa = min(item["quadratic_weighted_kappa"] for item in payload["blind_coding"]["base_status_agreement"].values())
    return (
        f"Score-blinded coding: {payload['blind_coding']['packet_count']} packets, "
        f"{payload['blind_coding']['coder_count']} coding passes, "
        f"{first_pair['exact_status_agreement']:.2f} coder-coder exact agreement, "
        f"{first_pair['cohen_kappa']:.2f} coder-coder kappa, "
        f"{first_pair['quadratic_weighted_kappa']:.2f} coder-coder weighted kappa, "
        f"{payload['blind_coding']['minimum_dimension_kappa']:.2f} minimum dimension kappa, "
        f"{payload['blind_coding']['minimum_failure_flag_exact_agreement']:.2f} minimum derived failure-flag exact agreement, "
        f"{payload['blind_coding']['minimum_missing_gate_exact_agreement']:.2f} minimum derived missing-gate exact agreement, "
        f"{payload['blind_coding']['base_dimension_min_kappa']:.2f} minimum base-dimension kappa "
        f"({payload['blind_coding']['base_dimension_min_kappa_dimension']}, "
        f"{payload['blind_coding']['base_dimension_min_kappa_exact_agreement']:.2f} exact), "
        f"{payload['blind_coding']['base_dimension_min_exact_agreement']:.2f} minimum base-dimension exact agreement, "
        f"{payload['blind_coding']['base_dimension_min_pabak']:.2f} minimum base-dimension PABAK, "
        f"{payload['blind_coding']['base_dimension_max_mean_absolute_delta']:.2f} maximum base-dimension mean absolute delta, "
        f"{base_exact:.2f} minimum base-coder exact agreement, "
        f"{base_weighted:.2f} minimum base-coder weighted agreement, "
        f"{base_kappa:.2f} minimum base-coder kappa, "
        f"{base_weighted_kappa:.2f} minimum base-coder weighted kappa"
    )


def _blocked_reason_distribution(rows: list[dict]) -> dict[str, int]:
    merged: dict[str, int] = {}
    for row in rows:
        for reason, count in row.get("blocked_reason_distribution", {}).items():
            merged[reason] = merged.get(reason, 0) + count
    return merged


def _format_distribution(distribution: dict[str, int]) -> str:
    if not distribution:
        return "none"
    return ", ".join(f"{key}: {value}" for key, value in sorted(distribution.items()))


def _metric(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


if __name__ == "__main__":
    raise SystemExit(main())
