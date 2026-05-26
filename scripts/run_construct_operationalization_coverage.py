from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "experiments" / "construct_operationalization" / "results"
MINIMUM_LAYERS_PER_CONSTRUCT = 4
MINIMUM_ROLES_PER_CONSTRUCT = 3

EVIDENCE_LAYERS = {
    "formal_invariants": {
        "path": "experiments/formal_invariants/results/formal_invariant_verification.json",
        "roles": ["formal", "invariant"],
        "required": [["total_checks"], ["passed_checks"]],
    },
    "status_lattice": {
        "path": "experiments/status_lattice/results/status_lattice_analysis.json",
        "roles": ["formal", "substitute"],
        "required": [["state_count"], ["necessity"], ["gate_ablation"]],
    },
    "policy_constants_replay": {
        "path": "experiments/policy_constants_replay/results/policy_constants_replay.json",
        "roles": ["replay", "second_implementation"],
        "required": [["check_count"], ["passed_check_count"]],
    },
    "status_certificates": {
        "path": "experiments/status_certificates/results/status_certificate_validation.json",
        "roles": ["certificate", "replay"],
        "required": [["certificate_count"], ["replay_check_count"], ["proof_obligation_count"]],
    },
    "gate_ablations": {
        "path": "experiments/gate_ablations/results/gate_ablation_analysis.json",
        "roles": ["gate", "necessity"],
        "required": [["ablation_count"], ["passed_count"]],
    },
    "gate_contrast_witnesses": {
        "path": "experiments/gate_contrast_witnesses/results/gate_contrast_witness_analysis.json",
        "roles": ["construct", "negative_control"],
        "required": [["witness_count"], ["status_separated_count"]],
    },
    "source_chain_attacks": {
        "path": "experiments/source_chain_attacks/results/source_chain_attack_experiment.json",
        "roles": ["source_chain", "negative_control"],
        "required": [["summary", "scenario_count"], ["summary", "expected_passed"]],
    },
    "claim_anchor": {
        "path": "experiments/claim_anchor_analysis/results/claim_anchor_analysis.json",
        "roles": ["claim_level", "source_chain"],
        "required": [["evaluation_count"], ["passed_count"]],
    },
    "temporal_validity": {
        "path": "experiments/temporal_validity/results/temporal_validity_analysis.json",
        "roles": ["temporal", "source_chain"],
        "required": [["evaluation_count"], ["passed_count"]],
    },
    "source_text_verification": {
        "path": "experiments/source_text_verification/results/source_text_anchor_verification.json",
        "roles": ["external_source", "anchor"],
        "required": [["support_item_count"], ["support_items_verified"]],
    },
    "model_output_adversarial": {
        "path": "experiments/model_output_adversarial/results/model_output_adversarial_experiment.json",
        "roles": ["model_output", "negative_control"],
        "required": [["summary", "scenario_count"], ["summary", "expected_passed"]],
    },
    "issue_gold_sets": {
        "path": "experiments/issue_gold_sets/results/issue_gold_set_experiment.json",
        "roles": ["construct", "public_source"],
        "required": [["summary", "scenario_count"], ["summary", "expected_passed"]],
    },
    "issue_ablations": {
        "path": "experiments/issue_ablations/results/issue_ablation_experiment.json",
        "roles": ["gate", "negative_control"],
        "required": [["summary", "scenario_count"], ["summary", "expected_passed"]],
    },
    "public_retrieval_benchmark": {
        "path": "experiments/public_retrieval_benchmark/results/public_retrieval_benchmark.json",
        "roles": ["public", "retrieval"],
        "required": [["summary", "scenario_count"], ["summary", "expected_passed"]],
    },
    "jurisdiction_profiles": {
        "path": "experiments/jurisdiction_profiles/results/jurisdiction_profile_analysis.json",
        "roles": ["jurisdiction", "portability"],
        "required": [["profile_check_count"], ["passed_count"]],
    },
    "ranking_visibility": {
        "path": "experiments/ranking_visibility/results/ranking_visibility_analysis.json",
        "roles": ["ranking", "salience"],
        "required": [["window_check_count"], ["rank_order_passed_count"]],
    },
    "contestation_challenges": {
        "path": "experiments/contestation_challenges/results/contestation_challenge_experiment.json",
        "roles": ["contestability", "challenge"],
        "required": [["summary", "scenario_count"], ["summary", "expected_passed"]],
    },
    "review_provenance": {
        "path": "experiments/review_provenance/results/review_provenance_analysis.json",
        "roles": ["provenance", "review"],
        "required": [["evaluation_count"], ["passed_count"]],
    },
    "query_portfolios": {
        "path": "experiments/query_portfolios/results/query_portfolio_frontier.json",
        "roles": ["retrieval", "frontier"],
        "required": [["portfolio_count"], ["qualified_portfolio_count"]],
    },
    "metric_separation": {
        "path": "experiments/metric_separation/results/metric_separation_analysis.json",
        "roles": ["metric", "substitute"],
        "required": [["metric_scenario_count"], ["high_recall_blocked"]],
    },
    "baseline_comparison": {
        "path": "experiments/baseline_comparisons/results/baseline_comparison_analysis.json",
        "roles": ["baseline", "substitute"],
        "required": [["baseline_prediction_count"], ["best_simplified"]],
    },
    "issue_family_generalization": {
        "path": "experiments/issue_family_generalization/results/issue_family_generalization.json",
        "roles": ["holdout", "generalization"],
        "required": [["holdout_prediction_count"], ["folds_with_best_trained_rule_error"]],
    },
    "policy_family_robustness": {
        "path": "experiments/policy_family_robustness/results/policy_family_robustness.json",
        "roles": ["policy", "robustness"],
        "required": [["total_evaluation_count"], ["variants_with_simplified_errors"]],
    },
    "workflow_portability": {
        "path": "experiments/workflow_portability/results/workflow_portability_analysis.json",
        "roles": ["architecture", "portability"],
        "required": [["evaluation_count"], ["passed_count"]],
    },
    "model_identity_invariance": {
        "path": "experiments/model_identity_invariance/results/model_identity_invariance.json",
        "roles": ["identity", "invariant"],
        "required": [["evaluation_count"], ["status_changed_count"]],
    },
    "cross_engine_model_outputs": {
        "path": "experiments/cross_engine_model_outputs/results/cross_engine_model_output_experiment.json",
        "roles": ["model_output", "cross_engine"],
        "required": [["summary", "scenario_count"], ["summary", "expected_passed"]],
    },
    "cross_engine_model_repairs": {
        "path": "experiments/cross_engine_model_repairs/results/cross_engine_model_repair_experiment.json",
        "roles": ["model_output", "intervention"],
        "required": [["summary", "scenario_count"], ["summary", "expected_passed"]],
    },
    "public_system_outputs": {
        "path": "experiments/public_system_outputs/results/public_system_output_experiment.json",
        "roles": ["public", "external"],
        "required": [["summary", "scenario_count"], ["summary", "expected_passed"]],
    },
    "holdout_validation": {
        "path": "experiments/holdout_validation/results/holdout_validation.json",
        "roles": ["holdout", "external"],
        "required": [["summary", "scenario_count"], ["summary", "expected_passed"]],
    },
    "model_output_repairs": {
        "path": "experiments/model_output_repairs/results/model_output_repair_experiment.json",
        "roles": ["model_output", "intervention"],
        "required": [["summary", "scenario_count"], ["summary", "expected_passed"]],
    },
    "certificate_tamper": {
        "path": "experiments/certificate_tamper/results/certificate_tamper_analysis.json",
        "roles": ["certificate", "negative_control"],
        "required": [["tamper_case_count"], ["rejected_count"]],
    },
    "metamorphic_policy": {
        "path": "experiments/metamorphic_policy/results/metamorphic_policy_tests.json",
        "roles": ["label_free", "invariant"],
        "required": [["metamorphic_evaluation_count"], ["passed_count"]],
    },
    "annotation_robustness": {
        "path": "experiments/annotation_robustness/results/annotation_robustness.json",
        "roles": ["coding", "robustness"],
        "required": [["recoded_evaluations"], ["all_policy_status_stable"]],
    },
    "annotation_uncertainty": {
        "path": "experiments/annotation_uncertainty/results/annotation_uncertainty.json",
        "roles": ["coding", "uncertainty"],
        "required": [["evaluation_count"], ["status_stability_rate"]],
    },
    "blind_coding": {
        "path": "experiments/blind_coding/results/blind_coding_study.json",
        "roles": ["coding", "reproducibility"],
        "required": [["packet_count"], ["minimum_dimension_kappa"]],
    },
}

CONSTRUCTS = [
    {
        "id": "status_ordering",
        "label": "Procedural status ordering",
        "layers": ["formal_invariants", "status_lattice", "policy_constants_replay", "status_certificates"],
    },
    {
        "id": "role_and_failure_caps",
        "label": "System-role and failure caps",
        "layers": ["formal_invariants", "workflow_portability", "policy_constants_replay", "policy_family_robustness"],
    },
    {
        "id": "audit_vector_operationalization",
        "label": "Six-part audit-vector coding",
        "layers": ["formal_invariants", "annotation_robustness", "annotation_uncertainty", "blind_coding"],
    },
    {
        "id": "evidence_packet_source_chain",
        "label": "Output evidence packet and source chain",
        "layers": [
            "claim_anchor",
            "temporal_validity",
            "source_chain_attacks",
            "source_text_verification",
            "model_output_adversarial",
        ],
    },
    {
        "id": "authority_hierarchy_issue_sets",
        "label": "Authority hierarchy and issue sets",
        "layers": ["issue_gold_sets", "issue_ablations", "public_retrieval_benchmark", "jurisdiction_profiles"],
    },
    {
        "id": "counter_material_salience",
        "label": "Counter-material and rank salience",
        "layers": ["ranking_visibility", "gate_ablations", "contestation_challenges", "query_portfolios"],
    },
    {
        "id": "contestability_adoption",
        "label": "Contestability and adoption record",
        "layers": ["contestation_challenges", "review_provenance", "gate_contrast_witnesses", "status_certificates"],
    },
    {
        "id": "substitute_theory_separation",
        "label": "Substitute-theory separation",
        "layers": ["metric_separation", "baseline_comparison", "issue_family_generalization", "policy_family_robustness"],
    },
    {
        "id": "architecture_identity_portability",
        "label": "Architecture and identity portability",
        "layers": [
            "workflow_portability",
            "model_identity_invariance",
            "cross_engine_model_outputs",
            "cross_engine_model_repairs",
        ],
    },
    {
        "id": "replication_and_tamper_resistance",
        "label": "Replication and tamper resistance",
        "layers": ["status_certificates", "certificate_tamper", "policy_constants_replay", "metamorphic_policy"],
    },
]


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = [_construct_row(construct) for construct in CONSTRUCTS]
    checks = [check for row in rows for check in row["checks"]]
    failures = [check for check in checks if not check["passed"]]
    failed_constructs = [row for row in rows if not row["passed"]]
    payload = {
        "construct_count": len(rows),
        "evidence_layer_count": len({layer for construct in CONSTRUCTS for layer in construct["layers"]}),
        "coverage_check_count": len(checks),
        "passed_check_count": len(checks) - len(failures),
        "failed_check_count": len(failures),
        "passed_construct_count": len(rows) - len(failed_constructs),
        "failed_construct_count": len(failed_constructs),
        "minimum_layers_per_construct": MINIMUM_LAYERS_PER_CONSTRUCT,
        "minimum_roles_per_construct": MINIMUM_ROLES_PER_CONSTRUCT,
        "all_passed": not failures and not failed_constructs,
        "constructs": rows,
        "failures": failures,
    }
    report = _format_report(payload)
    (RESULTS / "construct_operationalization_coverage.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    (RESULTS / "construct_operationalization_coverage.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0 if payload["all_passed"] else 1


def _construct_row(construct: dict) -> dict:
    checks = [_coverage_check(construct["id"], layer_id) for layer_id in construct["layers"]]
    roles = sorted({role for layer_id in construct["layers"] for role in EVIDENCE_LAYERS[layer_id]["roles"]})
    return {
        "id": construct["id"],
        "label": construct["label"],
        "layer_count": len(construct["layers"]),
        "role_count": len(roles),
        "roles": roles,
        "evidence_layers": construct["layers"],
        "passed_checks": sum(check["passed"] for check in checks),
        "failed_checks": sum(not check["passed"] for check in checks),
        "passed": (
            all(check["passed"] for check in checks)
            and len(construct["layers"]) >= MINIMUM_LAYERS_PER_CONSTRUCT
            and len(roles) >= MINIMUM_ROLES_PER_CONSTRUCT
        ),
        "checks": checks,
    }


def _coverage_check(construct_id: str, layer_id: str) -> dict:
    layer = EVIDENCE_LAYERS[layer_id]
    path = ROOT / layer["path"]
    missing_fields = []
    parse_error = None
    passed = path.exists() and path.stat().st_size > 0
    if passed:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            payload = {}
            parse_error = str(exc)
            passed = False
        for field_path in layer["required"]:
            if not _has_path(payload, field_path):
                missing_fields.append(".".join(field_path))
        passed = passed and not missing_fields
    return {
        "construct_id": construct_id,
        "layer_id": layer_id,
        "path": layer["path"],
        "roles": layer["roles"],
        "required": [".".join(field_path) for field_path in layer["required"]],
        "missing_fields": missing_fields,
        "parse_error": parse_error,
        "passed": passed,
    }


def _has_path(payload: dict, field_path: list[str]) -> bool:
    value = payload
    for key in field_path:
        if not isinstance(value, dict) or key not in value:
            return False
        value = value[key]
    return True


def _format_report(payload: dict) -> str:
    lines = [
        "# Construct Operationalization Coverage",
        "",
        f"Core constructs: {payload['construct_count']}",
        f"Evidence layers: {payload['evidence_layer_count']}",
        f"Coverage checks: {payload['passed_check_count']}/{payload['coverage_check_count']} passed",
        f"Minimum layers per construct: {payload['minimum_layers_per_construct']}",
        f"Minimum evidence roles per construct: {payload['minimum_roles_per_construct']}",
        "",
        "| Construct | Evidence layers | Evidence roles | Checks |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in payload["constructs"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["label"],
                    str(row["layer_count"]),
                    str(row["role_count"]),
                    f"{row['passed_checks']}/{row['layer_count']}",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
