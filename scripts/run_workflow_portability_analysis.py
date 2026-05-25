from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_harness.model import STATUS_RANK, evaluate_scenario
from run_full_validation import SUITES

RESULTS = ROOT / "experiments" / "workflow_portability" / "results"

ARCHITECTURE_PROFILES = [
    "public_search_interface",
    "retrieval_augmented_generation",
    "agentic_research_workflow",
    "commercial_legal_database",
    "manual_review_packet",
]

ENTITLEMENT_PROFILES = [
    ("internal_reference", "back_office_tool", "reference_information"),
    ("professional_assistance", "disclosed_assistance_tool", "professional_support_output"),
    ("procedural_screening", "auditable_procedural_tool", "normative_material_screening_output"),
    ("authorized_decision", "authorized_decision_support_tool", "decision_support_reason"),
]

INVARIANT_FIELDS = (
    "allowed_status",
    "disposition",
    "failure_flags",
    "missing_gates",
    "total_score",
    "scores",
    "claim_supported",
)


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    scenarios = _load_scenarios()
    architecture_rows = _architecture_rows(scenarios)
    entitlement_rows, dependency_rows = _entitlement_rows(scenarios)
    unaccountable_rows = _unaccountable_rows(scenarios)
    rows = architecture_rows + entitlement_rows + dependency_rows + unaccountable_rows
    failures = [row for row in rows if not row["passed"]]
    payload = {
        "scenario_count": len(scenarios),
        "architecture_profile_count": len(ARCHITECTURE_PROFILES),
        "entitlement_profile_count": len(ENTITLEMENT_PROFILES),
        "architecture_invariance_evaluation_count": len(architecture_rows),
        "architecture_invariance_passed_count": _passed(architecture_rows),
        "entitlement_profile_evaluation_count": len(entitlement_rows),
        "entitlement_profile_passed_count": _passed(entitlement_rows),
        "decision_dependency_check_count": len(dependency_rows),
        "decision_dependency_passed_count": _passed(dependency_rows),
        "unaccountable_bar_evaluation_count": len(unaccountable_rows),
        "unaccountable_bar_passed_count": _passed(unaccountable_rows),
        "evaluation_count": len(rows),
        "passed_count": len(rows) - len(failures),
        "failed_count": len(failures),
        "architecture_profiles": ARCHITECTURE_PROFILES,
        "entitlement_profiles": [profile[0] for profile in ENTITLEMENT_PROFILES],
        "by_architecture_profile": _by_profile(architecture_rows, "architecture_profile"),
        "by_entitlement_profile": _by_profile(entitlement_rows, "entitlement_profile"),
        "failures": failures,
        "rows": rows,
    }
    report = _format_report(payload)
    (RESULTS / "workflow_portability_analysis.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (RESULTS / "workflow_portability_analysis.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0 if not failures else 1


def _load_scenarios() -> list[dict]:
    scenarios: list[dict] = []
    for suite in SUITES:
        for path in sorted(suite["path"].glob("*.json")):
            scenario = json.loads(path.read_text(encoding="utf-8"))
            scenario["_source_path"] = str(path.relative_to(ROOT))
            scenarios.append(scenario)
    return scenarios


def _architecture_rows(scenarios: list[dict]) -> list[dict]:
    rows = []
    for scenario in scenarios:
        base = evaluate_scenario(scenario)
        base_projection = _projection(base)
        for profile in ARCHITECTURE_PROFILES:
            mutated = deepcopy(scenario)
            upstream = mutated.setdefault("upstream_output", {})
            upstream["workflow_architecture"] = profile
            upstream["runtime_stack"] = profile
            mutated["workflow_architecture"] = profile
            result = evaluate_scenario(mutated)
            result_projection = _projection(result)
            changed_fields = [field for field in INVARIANT_FIELDS if base_projection[field] != result_projection[field]]
            rows.append(
                {
                    "kind": "architecture_invariance",
                    "scenario_id": scenario["id"],
                    "source_path": scenario["_source_path"],
                    "architecture_profile": profile,
                    "base_allowed_status": base.allowed_status,
                    "mutated_allowed_status": result.allowed_status,
                    "changed_fields": changed_fields,
                    "passed": not changed_fields,
                }
            )
    return rows


def _entitlement_rows(scenarios: list[dict]) -> tuple[list[dict], list[dict]]:
    rows = []
    dependency_rows = []
    for scenario in scenarios:
        profile_results = {}
        for profile_id, role, claim in ENTITLEMENT_PROFILES:
            mutated = _entitlement_variant(scenario, role, claim)
            result = evaluate_scenario(mutated)
            cap = STATUS_RANK[claim]
            profile_results[profile_id] = result
            rows.append(
                {
                    "kind": "entitlement_cap",
                    "scenario_id": scenario["id"],
                    "source_path": scenario["_source_path"],
                    "entitlement_profile": profile_id,
                    "system_role": role,
                    "claimed_status": claim,
                    "allowed_status": result.allowed_status,
                    "disposition": result.disposition,
                    "expected_max_rank": cap,
                    "passed": STATUS_RANK[result.allowed_status] <= cap,
                }
            )
        procedural = profile_results["procedural_screening"]
        decision = profile_results["authorized_decision"]
        dependency_rows.append(
            {
                "kind": "decision_depends_on_screening_chain",
                "scenario_id": scenario["id"],
                "source_path": scenario["_source_path"],
                "procedural_status": procedural.allowed_status,
                "decision_status": decision.allowed_status,
                "passed": (
                    decision.allowed_status != "decision_support_reason"
                    or STATUS_RANK[procedural.allowed_status] >= STATUS_RANK["normative_material_screening_output"]
                ),
            }
        )
    return rows, dependency_rows


def _unaccountable_rows(scenarios: list[dict]) -> list[dict]:
    rows = []
    for scenario in scenarios:
        mutated = deepcopy(scenario)
        mutated["system_role"] = "unaccountable_external_disposition"
        mutated["claimed_status"] = "decision_support_reason"
        gate = dict(mutated.get("review_gate") or {})
        gate["irreversible_action"] = True
        gate["human_authorization"] = False
        mutated["review_gate"] = gate
        result = evaluate_scenario(mutated)
        rows.append(
            {
                "kind": "unaccountable_external_bar",
                "scenario_id": scenario["id"],
                "source_path": scenario["_source_path"],
                "allowed_status": result.allowed_status,
                "disposition": result.disposition,
                "failure_flags": result.failure_flags,
                "passed": result.allowed_status == "no_external_legal_effect",
            }
        )
    return rows


def _entitlement_variant(scenario: dict, role: str, claim: str) -> dict:
    mutated = deepcopy(scenario)
    mutated["system_role"] = role
    mutated["claimed_status"] = claim
    gate = dict(mutated.get("review_gate") or {})
    if STATUS_RANK[claim] >= STATUS_RANK["normative_material_screening_output"]:
        gate.update(
            {
                "attorney_review_required": True,
                "review_status": "completed",
                "reliance_gate": "attorney_review",
                "jurisdiction_assumptions": gate.get("jurisdiction_assumptions")
                or [mutated.get("jurisdiction_profile", "common_law")],
                "contestability_channel": gate.get("contestability_channel") or "workflow-portability-channel",
                "irreversible_action": False,
            }
        )
    if claim == "decision_support_reason":
        gate.update(
            {
                "reliance_gate": "authorized_adoption",
                "human_authorization": True,
                "adoption_reasons_recorded": True,
                "contestation_recorded": True,
            }
        )
    if gate:
        mutated["review_gate"] = gate
    return mutated


def _projection(result) -> dict:
    return {
        "allowed_status": result.allowed_status,
        "disposition": result.disposition,
        "failure_flags": result.failure_flags,
        "missing_gates": result.missing_gates,
        "total_score": result.total_score,
        "scores": result.scores,
        "claim_supported": result.claim_supported,
    }


def _passed(rows: list[dict]) -> int:
    return sum(row["passed"] for row in rows)


def _by_profile(rows: list[dict], field: str) -> dict[str, dict]:
    buckets: dict[str, dict] = {}
    for row in rows:
        bucket = buckets.setdefault(row[field], {"count": 0, "passed": 0, "failed": 0})
        bucket["count"] += 1
        if row["passed"]:
            bucket["passed"] += 1
        else:
            bucket["failed"] += 1
    return buckets


def _format_report(payload: dict) -> str:
    return "\n".join(
        [
            "# Workflow Portability Analysis",
            "",
            f"Scenario packets: {payload['scenario_count']}",
            f"Architecture profiles: {payload['architecture_profile_count']}",
            f"Entitlement profiles: {payload['entitlement_profile_count']}",
            f"Architecture invariance: {payload['architecture_invariance_passed_count']}/{payload['architecture_invariance_evaluation_count']}",
            f"Entitlement cap checks: {payload['entitlement_profile_passed_count']}/{payload['entitlement_profile_evaluation_count']}",
            f"Decision dependency checks: {payload['decision_dependency_passed_count']}/{payload['decision_dependency_check_count']}",
            f"Unaccountable external bars: {payload['unaccountable_bar_passed_count']}/{payload['unaccountable_bar_evaluation_count']}",
            f"Total checks: {payload['passed_count']}/{payload['evaluation_count']}",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
