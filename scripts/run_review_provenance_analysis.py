from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_harness.model import STATUS_RANK, evaluate_scenario
from run_full_validation import SUITES

RESULTS = ROOT / "experiments" / "review_provenance" / "results"
NORMATIVE = STATUS_RANK["normative_material_screening_output"]
DECISION = STATUS_RANK["decision_support_reason"]


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    scenarios = _load_scenarios()
    rows: list[dict] = []
    for scenario in scenarios:
        base = evaluate_scenario(scenario)
        if STATUS_RANK[base.allowed_status] < NORMATIVE:
            rows.extend(_placebo_rows(scenario, base.allowed_status))
        else:
            rows.extend(_high_status_provenance_rows(scenario, base.allowed_status))
        if base.allowed_status == "decision_support_reason":
            rows.extend(_decision_provenance_rows(scenario, base.allowed_status))
    by_relation = _by_relation(rows)
    payload = {
        "scenario_count": len(scenarios),
        "non_high_scenario_count": sum(
            STATUS_RANK[evaluate_scenario(scenario).allowed_status] < NORMATIVE
            for scenario in scenarios
        ),
        "qualified_scenario_count": sum(
            STATUS_RANK[evaluate_scenario(scenario).allowed_status] >= NORMATIVE
            for scenario in scenarios
        ),
        "decision_scenario_count": sum(
            evaluate_scenario(scenario).allowed_status == "decision_support_reason"
            for scenario in scenarios
        ),
        "evaluation_count": len(rows),
        "passed_count": sum(row["passed"] for row in rows),
        "failed_count": sum(not row["passed"] for row in rows),
        "placebo_evaluation_count": sum(row["kind"] == "review_placebo" for row in rows),
        "placebo_blocked_count": sum(
            row["kind"] == "review_placebo" and row["passed"] for row in rows
        ),
        "high_status_provenance_check_count": sum(
            row["kind"] == "high_status_provenance" for row in rows
        ),
        "high_status_provenance_blocked_count": sum(
            row["kind"] == "high_status_provenance" and row["passed"] for row in rows
        ),
        "decision_provenance_check_count": sum(
            row["kind"] == "decision_provenance" for row in rows
        ),
        "decision_provenance_demoted_count": sum(
            row["kind"] == "decision_provenance" and row["passed"] for row in rows
        ),
        "by_relation": by_relation,
        "rows": rows,
    }
    report = _format_report(payload)
    (RESULTS / "review_provenance_analysis.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (RESULTS / "review_provenance_analysis.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0 if payload["failed_count"] == 0 else 1


def _load_scenarios() -> list[dict]:
    scenarios: list[dict] = []
    for suite in SUITES:
        for path in sorted(suite["path"].glob("*.json")):
            scenario = json.loads(path.read_text(encoding="utf-8"))
            scenario["_source_path"] = str(path.relative_to(ROOT))
            scenarios.append(scenario)
    return scenarios


def _placebo_rows(scenario: dict, base_status: str) -> list[dict]:
    return [
        _row(
            scenario,
            "review_placebo",
            "completed_review_label_cannot_supply_material_chain",
            base_status,
            _completed_review_label(scenario),
            lambda status, _flags: STATUS_RANK[status] < NORMATIVE,
        ),
        _row(
            scenario,
            "review_placebo",
            "authorized_adoption_label_cannot_supply_material_chain",
            base_status,
            _authorized_adoption_label(scenario),
            lambda status, _flags: STATUS_RANK[status] < NORMATIVE,
        ),
    ]


def _high_status_provenance_rows(scenario: dict, base_status: str) -> list[dict]:
    return [
        _row(
            scenario,
            "high_status_provenance",
            "contestability_channel_required_for_high_status",
            base_status,
            _without_contestability_channel(scenario),
            lambda status, flags: STATUS_RANK[status] < NORMATIVE and "contestation_failure" in flags,
        ),
        _row(
            scenario,
            "high_status_provenance",
            "completed_review_required_for_high_status",
            base_status,
            _without_completed_review(scenario),
            lambda status, flags: STATUS_RANK[status] < NORMATIVE and "review_gate_failure" in flags,
        ),
        _row(
            scenario,
            "high_status_provenance",
            "jurisdiction_assumption_required_for_high_status",
            base_status,
            _without_jurisdiction_assumptions(scenario),
            lambda status, flags: STATUS_RANK[status] < NORMATIVE and "jurisdiction_assumption_gap" in flags,
        ),
    ]


def _decision_provenance_rows(scenario: dict, base_status: str) -> list[dict]:
    return [
        _row(
            scenario,
            "decision_provenance",
            "adoption_reasons_required_for_decision_status",
            base_status,
            _without_adoption_reasons(scenario),
            lambda status, _flags: STATUS_RANK[status] < DECISION,
        ),
        _row(
            scenario,
            "decision_provenance",
            "contestation_record_required_for_decision_status",
            base_status,
            _without_contestation_record(scenario),
            lambda status, _flags: STATUS_RANK[status] < DECISION,
        ),
        _row(
            scenario,
            "decision_provenance",
            "human_authorization_required_for_decision_status",
            base_status,
            _without_human_authorization(scenario),
            lambda status, _flags: STATUS_RANK[status] < DECISION,
        ),
    ]


def _row(scenario: dict, kind: str, relation: str, base_status: str, mutated: dict, predicate) -> dict:
    result = evaluate_scenario(mutated)
    passed = predicate(result.allowed_status, result.failure_flags)
    return {
        "scenario_id": scenario["id"],
        "source_path": scenario.get("_source_path"),
        "kind": kind,
        "relation": relation,
        "base_status": base_status,
        "mutated_status": result.allowed_status,
        "mutated_disposition": result.disposition,
        "failure_flags": result.failure_flags,
        "passed": passed,
    }


def _completed_review_label(scenario: dict) -> dict:
    mutated = copy.deepcopy(scenario)
    mutated["claimed_status"] = "normative_material_screening_output"
    mutated["system_role"] = "auditable_procedural_tool"
    gate = dict(mutated.get("review_gate") or {})
    gate.update(
        {
            "attorney_review_required": True,
            "review_status": "completed",
            "reliance_gate": "attorney_review",
            "jurisdiction_assumptions": gate.get("jurisdiction_assumptions") or ["common_law", "civil_law"],
            "contestability_channel": "placebo-review-record",
            "irreversible_action": gate.get("irreversible_action", False),
            "human_authorization": False,
        }
    )
    if gate.get("irreversible_action") is True:
        gate["human_authorization"] = False
    mutated["review_gate"] = gate
    return mutated


def _authorized_adoption_label(scenario: dict) -> dict:
    mutated = _completed_review_label(scenario)
    mutated["claimed_status"] = "decision_support_reason"
    mutated["system_role"] = "authorized_decision_support_tool"
    gate = mutated["review_gate"]
    gate["reliance_gate"] = "authorized_adoption"
    gate["human_authorization"] = gate.get("irreversible_action") is not True
    gate["adoption_reasons_recorded"] = True
    gate["contestation_recorded"] = True
    return mutated


def _without_contestability_channel(scenario: dict) -> dict:
    mutated = copy.deepcopy(scenario)
    mutated.setdefault("review_gate", {}).pop("contestability_channel", None)
    return mutated


def _without_completed_review(scenario: dict) -> dict:
    mutated = copy.deepcopy(scenario)
    gate = mutated.setdefault("review_gate", {})
    gate["review_status"] = "pending"
    gate["attorney_review_required"] = True
    return mutated


def _without_jurisdiction_assumptions(scenario: dict) -> dict:
    mutated = copy.deepcopy(scenario)
    mutated.setdefault("review_gate", {})["jurisdiction_assumptions"] = []
    return mutated


def _without_adoption_reasons(scenario: dict) -> dict:
    mutated = copy.deepcopy(scenario)
    mutated.setdefault("review_gate", {})["adoption_reasons_recorded"] = False
    return mutated


def _without_contestation_record(scenario: dict) -> dict:
    mutated = copy.deepcopy(scenario)
    mutated.setdefault("review_gate", {})["contestation_recorded"] = False
    return mutated


def _without_human_authorization(scenario: dict) -> dict:
    mutated = copy.deepcopy(scenario)
    mutated.setdefault("review_gate", {})["human_authorization"] = False
    return mutated


def _by_relation(rows: list[dict]) -> dict[str, dict]:
    buckets: dict[str, dict] = {}
    for row in rows:
        bucket = buckets.setdefault(
            row["relation"],
            {"kind": row["kind"], "count": 0, "passed": 0, "failed": 0, "examples": []},
        )
        bucket["count"] += 1
        bucket["passed"] += int(row["passed"])
        bucket["failed"] += int(not row["passed"])
        if not row["passed"] and len(bucket["examples"]) < 5:
            bucket["examples"].append(row)
    return buckets


def _format_report(payload: dict) -> str:
    lines = [
        "# Review Provenance Analysis",
        "",
        f"Scenario packets: {payload['scenario_count']}",
        f"Non-high-status packets: {payload['non_high_scenario_count']}",
        f"Qualified packets: {payload['qualified_scenario_count']}",
        f"Decision-support packets: {payload['decision_scenario_count']}",
        f"Review-provenance evaluations: {payload['evaluation_count']}",
        f"Passed: {payload['passed_count']}/{payload['evaluation_count']}",
        f"Review/adoption placebo blocked: {payload['placebo_blocked_count']}/{payload['placebo_evaluation_count']}",
        f"High-status provenance defects blocked: {payload['high_status_provenance_blocked_count']}/{payload['high_status_provenance_check_count']}",
        f"Decision provenance defects demoted: {payload['decision_provenance_demoted_count']}/{payload['decision_provenance_check_count']}",
        "",
        "| Relation | Kind | Count | Passed | Failed |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for relation, bucket in sorted(payload["by_relation"].items()):
        lines.append(
            f"| {relation} | {bucket['kind']} | {bucket['count']} | {bucket['passed']} | {bucket['failed']} |"
        )
    if payload["failed_count"]:
        lines.extend(["", "## Failure examples", ""])
        for relation, bucket in sorted(payload["by_relation"].items()):
            for example in bucket["examples"]:
                lines.append(
                    f"- {relation}: {example['scenario_id']} -> {example['mutated_status']} ({example['failure_flags']})"
                )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
