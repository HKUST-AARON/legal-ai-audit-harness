from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "experiments" / "threat_model_coverage" / "results"
MINIMUM_LAYERS_PER_THREAT = 4
MINIMUM_ROLES_PER_THREAT = 3

EVIDENCE_LAYERS = {
    "metric_separation": {
        "path": "experiments/metric_separation/results/metric_separation_analysis.json",
        "roles": ["construct", "substitute"],
    },
    "baseline_comparison": {
        "path": "experiments/baseline_comparisons/results/baseline_comparison_analysis.json",
        "roles": ["construct", "substitute"],
    },
    "status_lattice": {
        "path": "experiments/status_lattice/results/status_lattice_analysis.json",
        "roles": ["formal", "substitute"],
    },
    "gate_contrast_witnesses": {
        "path": "experiments/gate_contrast_witnesses/results/gate_contrast_witness_analysis.json",
        "roles": ["construct", "negative_control"],
    },
    "formal_invariants": {
        "path": "experiments/formal_invariants/results/formal_invariant_verification.json",
        "roles": ["formal", "replay"],
    },
    "metamorphic_policy": {
        "path": "experiments/metamorphic_policy/results/metamorphic_policy_tests.json",
        "roles": ["label_free", "invariant"],
    },
    "policy_constants_replay": {
        "path": "experiments/policy_constants_replay/results/policy_constants_replay.json",
        "roles": ["replay", "second_implementation"],
    },
    "status_certificates": {
        "path": "experiments/status_certificates/results/status_certificate_validation.json",
        "roles": ["certificate", "replay"],
    },
    "source_chain_attacks": {
        "path": "experiments/source_chain_attacks/results/source_chain_attack_experiment.json",
        "roles": ["source_chain", "negative_control"],
    },
    "claim_anchor": {
        "path": "experiments/claim_anchor_analysis/results/claim_anchor_analysis.json",
        "roles": ["source_chain", "claim_level"],
    },
    "source_text_verification": {
        "path": "experiments/source_text_verification/results/source_text_anchor_verification.json",
        "roles": ["external_source", "anchor"],
    },
    "model_output_adversarial": {
        "path": "experiments/model_output_adversarial/results/model_output_adversarial_experiment.json",
        "roles": ["model_output", "negative_control"],
    },
    "real_cases": {
        "path": "experiments/real_cases/results/real_case_experiment.json",
        "roles": ["public", "external"],
    },
    "public_system_outputs": {
        "path": "experiments/public_system_outputs/results/public_system_output_experiment.json",
        "roles": ["public", "external"],
    },
    "public_retrieval_benchmark": {
        "path": "experiments/public_retrieval_benchmark/results/public_retrieval_benchmark.json",
        "roles": ["public", "retrieval"],
    },
    "holdout_validation": {
        "path": "experiments/holdout_validation/results/holdout_validation.json",
        "roles": ["holdout", "external"],
    },
    "cross_engine_model_outputs": {
        "path": "experiments/cross_engine_model_outputs/results/cross_engine_model_output_experiment.json",
        "roles": ["model_output", "cross_engine"],
    },
    "cross_engine_model_repairs": {
        "path": "experiments/cross_engine_model_repairs/results/cross_engine_model_repair_experiment.json",
        "roles": ["model_output", "intervention"],
    },
    "model_identity_invariance": {
        "path": "experiments/model_identity_invariance/results/model_identity_invariance.json",
        "roles": ["identity", "invariant"],
    },
    "workflow_portability": {
        "path": "experiments/workflow_portability/results/workflow_portability_analysis.json",
        "roles": ["architecture", "portability"],
    },
    "policy_family_robustness": {
        "path": "experiments/policy_family_robustness/results/policy_family_robustness.json",
        "roles": ["policy", "robustness"],
    },
    "policy_mutations": {
        "path": "experiments/policy_mutations/results/policy_mutation_analysis.json",
        "roles": ["policy", "negative_control"],
    },
    "gate_ablations": {
        "path": "experiments/gate_ablations/results/gate_ablation_analysis.json",
        "roles": ["gate", "necessity"],
    },
    "contestation_challenges": {
        "path": "experiments/contestation_challenges/results/contestation_challenge_experiment.json",
        "roles": ["contestability", "challenge"],
    },
    "review_provenance": {
        "path": "experiments/review_provenance/results/review_provenance_analysis.json",
        "roles": ["provenance", "review"],
    },
    "repair_frontiers": {
        "path": "experiments/repair_frontiers/results/repair_frontier_analysis.json",
        "roles": ["repair", "diagnostic"],
    },
    "annotation_robustness": {
        "path": "experiments/annotation_robustness/results/annotation_robustness.json",
        "roles": ["coding", "robustness"],
    },
    "annotation_uncertainty": {
        "path": "experiments/annotation_uncertainty/results/annotation_uncertainty.json",
        "roles": ["coding", "uncertainty"],
    },
    "blind_coding": {
        "path": "experiments/blind_coding/results/blind_coding_study.json",
        "roles": ["coding", "reproducibility"],
    },
    "ranking_visibility": {
        "path": "experiments/ranking_visibility/results/ranking_visibility_analysis.json",
        "roles": ["ranking", "salience"],
    },
}

THREATS = [
    {
        "id": "construct_status_not_retrieval",
        "label": "Construct validity: procedural status is not retrieval success",
        "layers": ["metric_separation", "baseline_comparison", "status_lattice", "gate_contrast_witnesses"],
    },
    {
        "id": "expected_label_circularity",
        "label": "Internal validity: status is not authored expected-label bias",
        "layers": ["formal_invariants", "metamorphic_policy", "policy_constants_replay", "status_certificates"],
    },
    {
        "id": "source_chain_validity",
        "label": "Source-chain validity: citations and locators are not decorative",
        "layers": ["source_chain_attacks", "claim_anchor", "source_text_verification", "model_output_adversarial"],
    },
    {
        "id": "external_public_outputs",
        "label": "External validity: the rule is not limited to constructed examples",
        "layers": ["real_cases", "public_system_outputs", "public_retrieval_benchmark", "holdout_validation"],
    },
    {
        "id": "model_architecture_identity",
        "label": "Architecture validity: provider identity does not confer status",
        "layers": [
            "cross_engine_model_outputs",
            "cross_engine_model_repairs",
            "model_identity_invariance",
            "workflow_portability",
        ],
    },
    {
        "id": "policy_discretion",
        "label": "Policy validity: thresholds and gate settings do not drive the core result",
        "layers": ["policy_family_robustness", "policy_mutations", "gate_ablations", "status_lattice"],
    },
    {
        "id": "contestability_provenance",
        "label": "Provenance validity: review and challenge records are operational",
        "layers": ["contestation_challenges", "review_provenance", "repair_frontiers", "status_certificates"],
    },
    {
        "id": "annotation_coding_validity",
        "label": "Annotation validity: status is stable under coding uncertainty",
        "layers": ["annotation_robustness", "annotation_uncertainty", "blind_coding", "ranking_visibility"],
    },
]


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = [_threat_row(threat) for threat in THREATS]
    checks = [check for row in rows for check in row["checks"]]
    failures = [check for check in checks if not check["passed"]]
    failed_threats = [row for row in rows if not row["passed"]]
    payload = {
        "threat_count": len(rows),
        "evidence_layer_count": len(EVIDENCE_LAYERS),
        "coverage_check_count": len(checks),
        "passed_check_count": len(checks) - len(failures),
        "failed_check_count": len(failures),
        "passed_threat_count": len(rows) - len(failed_threats),
        "failed_threat_count": len(failed_threats),
        "minimum_layers_per_threat": MINIMUM_LAYERS_PER_THREAT,
        "minimum_roles_per_threat": MINIMUM_ROLES_PER_THREAT,
        "all_passed": not failures and not failed_threats,
        "threats": rows,
        "failures": failures,
    }
    report = _format_report(payload)
    (RESULTS / "threat_model_coverage_analysis.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    (RESULTS / "threat_model_coverage_analysis.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0 if payload["all_passed"] else 1


def _threat_row(threat: dict) -> dict:
    checks = [_coverage_check(threat["id"], layer_id) for layer_id in threat["layers"]]
    roles = sorted({role for layer_id in threat["layers"] for role in EVIDENCE_LAYERS[layer_id]["roles"]})
    return {
        "id": threat["id"],
        "label": threat["label"],
        "layer_count": len(threat["layers"]),
        "role_count": len(roles),
        "roles": roles,
        "evidence_layers": threat["layers"],
        "passed_checks": sum(check["passed"] for check in checks),
        "failed_checks": sum(not check["passed"] for check in checks),
        "passed": (
            all(check["passed"] for check in checks)
            and len(threat["layers"]) >= MINIMUM_LAYERS_PER_THREAT
            and len(roles) >= MINIMUM_ROLES_PER_THREAT
        ),
        "checks": checks,
    }


def _coverage_check(threat_id: str, layer_id: str) -> dict:
    layer = EVIDENCE_LAYERS[layer_id]
    path = ROOT / layer["path"]
    passed = path.exists() and path.stat().st_size > 0
    if passed:
        json.loads(path.read_text(encoding="utf-8"))
    return {
        "threat_id": threat_id,
        "layer_id": layer_id,
        "path": layer["path"],
        "roles": layer["roles"],
        "passed": passed,
    }


def _format_report(payload: dict) -> str:
    lines = [
        "# Threat-Model Coverage Analysis",
        "",
        f"Validity threats: {payload['threat_count']}",
        f"Evidence layers: {payload['evidence_layer_count']}",
        f"Coverage checks: {payload['passed_check_count']}/{payload['coverage_check_count']} passed",
        f"Minimum layers per threat: {payload['minimum_layers_per_threat']}",
        f"Minimum evidence roles per threat: {payload['minimum_roles_per_threat']}",
        "",
        "| Threat | Evidence layers | Evidence roles | Checks |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in payload["threats"]:
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
