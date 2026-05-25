from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_harness.model import STATUS_RANK, evaluate_scenario
from run_full_validation import SUITES

RESULTS = ROOT / "experiments" / "metamorphic_policy" / "results"
NORMATIVE = STATUS_RANK["normative_material_screening_output"]
DECISION = STATUS_RANK["decision_support_reason"]
REFERENCE = STATUS_RANK["reference_information"]


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    scenarios = _load_scenarios()
    rows: list[dict] = []
    for scenario in scenarios:
        base = evaluate_scenario(scenario)
        rows.extend(_metamorphic_rows(scenario, base.allowed_status))

    by_relation: dict[str, dict] = {}
    for row in rows:
        relation = row["relation"]
        bucket = by_relation.setdefault(
            relation,
            {
                "count": 0,
                "passed": 0,
                "failed": 0,
                "examples": [],
            },
        )
        bucket["count"] += 1
        if row["passed"]:
            bucket["passed"] += 1
        else:
            bucket["failed"] += 1
            if len(bucket["examples"]) < 5:
                bucket["examples"].append(row)

    payload = {
        "scenario_count": len(scenarios),
        "metamorphic_evaluation_count": len(rows),
        "passed_count": sum(row["passed"] for row in rows),
        "failed_count": sum(not row["passed"] for row in rows),
        "by_relation": by_relation,
        "rows": rows,
    }
    (RESULTS / "metamorphic_policy_tests.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (RESULTS / "metamorphic_policy_tests.md").write_text(_format_report(payload), encoding="utf-8")
    print(_format_report(payload))
    return 0 if payload["failed_count"] == 0 else 1


def _load_scenarios() -> list[dict]:
    scenarios: list[dict] = []
    for suite in SUITES:
        for path in sorted(suite["path"].glob("*.json")):
            scenario = json.loads(path.read_text(encoding="utf-8"))
            scenario["_source_path"] = str(path.relative_to(ROOT))
            scenarios.append(scenario)
    return scenarios


def _metamorphic_rows(scenario: dict, base_status: str) -> list[dict]:
    base_rank = STATUS_RANK[base_status]
    rows = [
        _row(
            scenario,
            base_status,
            "claim_escalation_nonpromotion",
            _claim_escalation(scenario),
            lambda status: STATUS_RANK[status] <= base_rank,
            "Raising only the claimed procedural status cannot raise the allowed status.",
        ),
        _row(
            scenario,
            base_status,
            "upstream_metric_inflation_invariance",
            _upstream_metric_inflation(scenario),
            lambda status: status == base_status,
            "Perfect upstream precision, recall and F1 cannot change procedural status by themselves.",
        ),
        _row(
            scenario,
            base_status,
            "back_office_role_cap",
            _back_office_role_cap(scenario),
            lambda status: STATUS_RANK[status] <= REFERENCE,
            "A back-office role cap prevents external procedural status.",
        ),
    ]
    if not _adoption_gate_satisfied(scenario):
        rows.append(
            _row(
                scenario,
                base_status,
                "score_and_role_inflation_without_adoption",
                _score_and_role_inflation(scenario),
                lambda status: STATUS_RANK[status] < DECISION,
                "Perfect scores and an authorized role cannot create a decision reason without adoption artefacts.",
            )
        )
    if base_rank >= NORMATIVE:
        rows.extend(
            [
                _row(
                    scenario,
                    base_status,
                    "source_tag_deproceduralization_blocks_high_status",
                    _source_tag_deproceduralization(scenario),
                    lambda status: STATUS_RANK[status] < NORMATIVE,
                    "Replacing procedural source tags with verification-needed tags blocks high status.",
                ),
                _row(
                    scenario,
                    base_status,
                    "review_gate_removal_blocks_high_status",
                    _review_gate_removal(scenario),
                    lambda status: STATUS_RANK[status] < NORMATIVE,
                    "Removing the review and contestability gate blocks high status.",
                ),
                _row(
                    scenario,
                    base_status,
                    "benign_source_append_preserves_high_status",
                    _benign_source_append(scenario),
                    lambda status: STATUS_RANK[status] >= base_rank,
                    "Adding a faithful procedurally tagged source unit at the end must not demote a qualified packet.",
                ),
            ]
        )
    return rows


def _row(scenario: dict, base_status: str, relation: str, mutated: dict, predicate, description: str) -> dict:
    result = evaluate_scenario(mutated)
    passed = predicate(result.allowed_status)
    return {
        "scenario_id": scenario["id"],
        "source_path": scenario.get("_source_path"),
        "relation": relation,
        "description": description,
        "base_status": base_status,
        "mutated_status": result.allowed_status,
        "mutated_disposition": result.disposition,
        "passed": passed,
    }


def _claim_escalation(scenario: dict) -> dict:
    mutated = deepcopy(scenario)
    mutated["claimed_status"] = "decision_support_reason"
    return mutated


def _upstream_metric_inflation(scenario: dict) -> dict:
    mutated = deepcopy(scenario)
    mutated["upstream_metrics"] = {
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0,
        "mean_reciprocal_rank": 1.0,
    }
    return mutated


def _back_office_role_cap(scenario: dict) -> dict:
    mutated = deepcopy(scenario)
    mutated["system_role"] = "back_office_tool"
    return mutated


def _score_and_role_inflation(scenario: dict) -> dict:
    mutated = deepcopy(scenario)
    mutated["claimed_status"] = "decision_support_reason"
    mutated["system_role"] = "authorized_decision_support_tool"
    mutated["scores"] = {dimension: {"score": 2} for dimension in ("S", "Q", "H", "K", "T", "L")}
    return mutated


def _source_tag_deproceduralization(scenario: dict) -> dict:
    mutated = deepcopy(scenario)
    for link in mutated.get("evidence_packet", {}).get("output_links", []):
        link["source_tag"] = "needs_verification"
    return mutated


def _review_gate_removal(scenario: dict) -> dict:
    mutated = deepcopy(scenario)
    mutated.pop("review_gate", None)
    return mutated


def _benign_source_append(scenario: dict) -> dict:
    mutated = deepcopy(scenario)
    packet = mutated.setdefault("evidence_packet", {})
    units = packet.setdefault("output_units", [])
    links = packet.setdefault("output_links", [])
    unit_id = f"{scenario['id']}-benign-source-unit"
    source_id = f"{scenario['id']}-benign-source"
    locator = "benign-source-locator"
    units.append(
        {
            "id": unit_id,
            "claim": "Additional procedurally verified source note.",
            "source_ids": [source_id],
            "locators": [locator],
            "output_rank": len(units) + 100,
        }
    )
    links.append(
        {
            "unit_id": unit_id,
            "source_id": source_id,
            "locator": locator,
            "supports_claim": True,
            "source_tag": "tool_verified",
        }
    )
    return mutated


def _adoption_gate_satisfied(scenario: dict) -> bool:
    gate = scenario.get("review_gate", {})
    return (
        gate.get("review_status") == "completed"
        and gate.get("reliance_gate") == "authorized_adoption"
        and gate.get("human_authorization") is True
        and gate.get("adoption_reasons_recorded") is True
        and gate.get("contestation_recorded") is True
        and bool(gate.get("jurisdiction_assumptions"))
    )


def _format_report(payload: dict) -> str:
    lines = [
        "# Metamorphic Policy Tests",
        "",
        f"Scenario packets: {payload['scenario_count']}",
        f"Metamorphic evaluations: {payload['metamorphic_evaluation_count']}",
        f"Passed: {payload['passed_count']}/{payload['metamorphic_evaluation_count']}",
        "",
        "| Relation | Count | Passed | Failed |",
        "| --- | ---: | ---: | ---: |",
    ]
    for relation, bucket in sorted(payload["by_relation"].items()):
        lines.append(f"| {relation} | {bucket['count']} | {bucket['passed']} | {bucket['failed']} |")
    if payload["failed_count"]:
        lines.extend(["", "## Failure examples", ""])
        for relation, bucket in sorted(payload["by_relation"].items()):
            for example in bucket["examples"]:
                lines.append(
                    f"- {relation}: {example['scenario_id']} {example['base_status']} -> {example['mutated_status']}"
                )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
