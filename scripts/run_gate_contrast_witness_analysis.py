from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_harness.model import STATUS_RANK, evaluate_scenario
from run_full_validation import SUITES

RESULTS = ROOT / "experiments" / "gate_contrast_witnesses" / "results"
NORMATIVE = STATUS_RANK["normative_material_screening_output"]
DECISION = STATUS_RANK["decision_support_reason"]


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = _witness_rows()
    failed = [row for row in rows if not row["passed"]]
    payload = {
        "qualified_scenario_count": len({row["scenario_id"] for row in rows}),
        "witness_count": len(rows),
        "passed_count": len(rows) - len(failed),
        "failed_count": len(failed),
        "score_metric_role_preserved_count": sum(row["score_metric_role_preserved"] for row in rows),
        "status_separated_count": sum(row["status_separated"] for row in rows),
        "by_witness": _by_witness(rows),
        "status_distribution": _status_distribution(rows),
        "failures": failed,
        "results": rows,
    }
    markdown = _format_report(payload)
    (RESULTS / "gate_contrast_witness_analysis.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    (RESULTS / "gate_contrast_witness_analysis.md").write_text(markdown + "\n", encoding="utf-8")
    print(markdown)
    return 0 if not failed else 1


def _witness_rows() -> list[dict]:
    rows = []
    for path in _scenario_paths():
        scenario = json.loads(path.read_text(encoding="utf-8"))
        base = evaluate_scenario(scenario)
        if STATUS_RANK[base.allowed_status] < NORMATIVE:
            continue
        base_signature = _signature(scenario, base.system_role)
        for witness_id, variant, expected_below in _witnesses(scenario, base.allowed_status, base.system_role):
            result = evaluate_scenario(variant)
            score_metric_role_preserved = _signature(variant, result.system_role) == base_signature
            status_separated = STATUS_RANK[result.allowed_status] < expected_below
            rows.append(
                {
                    "scenario_id": scenario["id"],
                    "path": str(path.relative_to(ROOT)),
                    "witness": witness_id,
                    "base_status": base.allowed_status,
                    "witness_status": result.allowed_status,
                    "expected_below": _status_name(expected_below),
                    "base_role": base.system_role,
                    "witness_role": result.system_role,
                    "score_metric_role_preserved": score_metric_role_preserved,
                    "status_separated": status_separated,
                    "failure_flags": result.failure_flags,
                    "missing_gates": result.missing_gates,
                    "disposition": result.disposition,
                    "passed": score_metric_role_preserved and status_separated,
                }
            )
    return rows


def _scenario_paths() -> list[Path]:
    paths = []
    for suite in SUITES:
        paths.extend(sorted(suite["path"].glob("*.json")))
    return paths


def _witnesses(scenario: dict, base_status: str, base_role: str) -> list[tuple[str, dict, int]]:
    variants = [
        ("evidence_packet_gate", _without_evidence_packet(scenario, base_role), NORMATIVE),
        ("procedural_source_tag_gate", _with_nonprocedural_source_tags(scenario, base_role), NORMATIVE),
        ("high_authority_gate", _without_retrieved_high_authority(scenario, base_role), NORMATIVE),
        ("counter_material_gate", _without_retrieved_counter_material(scenario, base_role), NORMATIVE),
        ("jurisdiction_gate", _without_jurisdiction_assumptions(scenario, base_role), NORMATIVE),
        ("contestability_gate", _without_completed_review(scenario, base_role), NORMATIVE),
    ]
    if base_status == "decision_support_reason":
        variants.append(("adoption_gate", _without_decision_adoption(scenario, base_role), DECISION))
    return variants


def _without_evidence_packet(scenario: dict, role: str) -> dict:
    variant = _clone_with_role(scenario, role)
    variant.pop("evidence_packet", None)
    return variant


def _with_nonprocedural_source_tags(scenario: dict, role: str) -> dict:
    variant = _clone_with_role(scenario, role)
    for link in variant.get("evidence_packet", {}).get("output_links", []):
        link["source_tag"] = "needs_verification"
    return variant


def _without_retrieved_high_authority(scenario: dict, role: str) -> dict:
    variant = _clone_with_role(scenario, role)
    authority_sets = variant.setdefault("authority_sets", {})
    omitted = set(authority_sets.get("high_authority") or [])
    authority_sets["retrieved_high_authority"] = []
    authority_sets["retrieved"] = [item for item in authority_sets.get("retrieved", []) if item not in omitted]
    return variant


def _without_retrieved_counter_material(scenario: dict, role: str) -> dict:
    variant = _clone_with_role(scenario, role)
    authority_sets = variant.setdefault("authority_sets", {})
    omitted = set(authority_sets.get("counter_or_limiting") or [])
    authority_sets["retrieved_counter_or_limiting"] = []
    authority_sets["retrieved"] = [item for item in authority_sets.get("retrieved", []) if item not in omitted]
    variant.setdefault("counter_authority", {})["retrieved"] = []
    variant.pop("counter_material_complete", None)
    return variant


def _without_jurisdiction_assumptions(scenario: dict, role: str) -> dict:
    variant = _clone_with_role(scenario, role)
    variant.setdefault("review_gate", {})["jurisdiction_assumptions"] = []
    return variant


def _without_completed_review(scenario: dict, role: str) -> dict:
    variant = _clone_with_role(scenario, role)
    variant.setdefault("review_gate", {})["review_status"] = "pending"
    return variant


def _without_decision_adoption(scenario: dict, role: str) -> dict:
    variant = _clone_with_role(scenario, role)
    variant.setdefault("review_gate", {})["adoption_reasons_recorded"] = False
    return variant


def _clone_with_role(scenario: dict, role: str) -> dict:
    variant = copy.deepcopy(scenario)
    variant["system_role"] = role
    variant["id"] = scenario["id"] + "--gate-contrast-witness"
    return variant


def _signature(scenario: dict, role: str) -> dict:
    return {
        "scores": scenario.get("scores", {}),
        "upstream_metrics": scenario.get("upstream_metrics", {}),
        "system_role": role,
    }


def _status_name(rank: int) -> str:
    for status, status_rank in STATUS_RANK.items():
        if status_rank == rank:
            return status
    return str(rank)


def _by_witness(rows: list[dict]) -> dict[str, dict[str, int]]:
    grouped: dict[str, dict[str, int]] = {}
    for row in rows:
        item = grouped.setdefault(
            row["witness"],
            {"total": 0, "passed": 0, "failed": 0, "score_metric_role_preserved": 0, "status_separated": 0},
        )
        item["total"] += 1
        item["passed" if row["passed"] else "failed"] += 1
        item["score_metric_role_preserved"] += int(row["score_metric_role_preserved"])
        item["status_separated"] += int(row["status_separated"])
    return grouped


def _status_distribution(rows: list[dict]) -> dict[str, int]:
    distribution: dict[str, int] = {}
    for row in rows:
        distribution[row["witness_status"]] = distribution.get(row["witness_status"], 0) + 1
    return distribution


def _format_report(payload: dict) -> str:
    lines = [
        "# Gate-Contrast Witness Analysis",
        "",
        f"Qualified packets: {payload['qualified_scenario_count']}",
        f"Witness pairs: {payload['witness_count']}",
        f"Passed: {payload['passed_count']}/{payload['witness_count']}",
        f"Score/metric/role preserved: {payload['score_metric_role_preserved_count']}/{payload['witness_count']}",
        f"Status separated: {payload['status_separated_count']}/{payload['witness_count']}",
        "",
        "| Witness | Total | Preserved | Separated | Passed | Failed |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for witness_id, item in sorted(payload["by_witness"].items()):
        lines.append(
            f"| {witness_id} | {item['total']} | {item['score_metric_role_preserved']} | "
            f"{item['status_separated']} | {item['passed']} | {item['failed']} |"
        )
    lines.extend(["", "Status distribution after witness mutation: " + _distribution(payload["status_distribution"])])
    if payload["failures"]:
        lines.extend(["", "## Failures", ""])
        for failure in payload["failures"]:
            lines.append(
                f"- {failure['scenario_id']} / {failure['witness']}: {failure['witness_status']} "
                f"preserved={failure['score_metric_role_preserved']} separated={failure['status_separated']}"
            )
    return "\n".join(lines)


def _distribution(distribution: dict[str, int]) -> str:
    if not distribution:
        return "none"
    return ", ".join(f"{key}: {value}" for key, value in sorted(distribution.items()))


if __name__ == "__main__":
    raise SystemExit(main())
