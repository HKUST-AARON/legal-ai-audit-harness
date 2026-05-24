from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_harness.model import STATUS_RANK, evaluate_scenario
from run_full_validation import SUITES

RESULTS = ROOT / "experiments" / "gate_ablations" / "results"
NORMATIVE = STATUS_RANK["normative_material_screening_output"]
DECISION = STATUS_RANK["decision_support_reason"]


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = _ablation_rows()
    failed = [row for row in rows if not row["passed"]]
    payload = {
        "qualified_scenario_count": len({row["scenario_id"] for row in rows}),
        "ablation_count": len(rows),
        "passed_count": len(rows) - len(failed),
        "failed_count": len(failed),
        "by_ablation": _by_ablation(rows),
        "status_distribution": _status_distribution(rows),
        "failures": failed,
        "results": rows,
    }
    report = _format_report(payload)
    (RESULTS / "gate_ablation_analysis.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    (RESULTS / "gate_ablation_analysis.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0 if not failed else 1


def _scenario_paths() -> list[Path]:
    paths: list[Path] = []
    for suite in SUITES:
        paths.extend(sorted(suite["path"].glob("*.json")))
    return paths


def _ablation_rows() -> list[dict]:
    rows: list[dict] = []
    for path in _scenario_paths():
        scenario = json.loads(path.read_text(encoding="utf-8"))
        base = evaluate_scenario(scenario)
        if STATUS_RANK[base.allowed_status] < NORMATIVE:
            continue
        for ablation_id, ablated, expected_below in _ablations(scenario, base.allowed_status):
            result = evaluate_scenario(ablated)
            passed = STATUS_RANK[result.allowed_status] < expected_below
            rows.append(
                {
                    "scenario_id": scenario["id"],
                    "path": str(path.relative_to(ROOT)),
                    "base_status": base.allowed_status,
                    "ablation": ablation_id,
                    "expected_below": _status_name(expected_below),
                    "allowed_status": result.allowed_status,
                    "disposition": result.disposition,
                    "failure_flags": result.failure_flags,
                    "missing_gates": result.missing_gates,
                    "passed": passed,
                }
            )
    return rows


def _ablations(scenario: dict, base_status: str) -> list[tuple[str, dict, int]]:
    variants = [
        ("missing_evidence_packet", _without_evidence_packet(scenario), NORMATIVE),
        ("nonprocedural_source_tags", _with_nonprocedural_source_tags(scenario), NORMATIVE),
        ("missing_high_authority", _without_high_authority(scenario), NORMATIVE),
        ("missing_counter_material", _without_counter_material(scenario), NORMATIVE),
        ("missing_review_gate", _without_review_gate(scenario), NORMATIVE),
        ("professional_role_cap", _with_professional_role_cap(scenario), NORMATIVE),
    ]
    if base_status == "decision_support_reason":
        variants.append(("missing_decision_adoption", _without_decision_adoption(scenario), DECISION))
    return variants


def _without_evidence_packet(scenario: dict) -> dict:
    variant = copy.deepcopy(scenario)
    variant.pop("evidence_packet", None)
    return variant


def _with_nonprocedural_source_tags(scenario: dict) -> dict:
    variant = copy.deepcopy(scenario)
    for link in variant.get("evidence_packet", {}).get("output_links", []):
        link["source_tag"] = "needs_verification"
    return variant


def _without_high_authority(scenario: dict) -> dict:
    variant = copy.deepcopy(scenario)
    authority_sets = variant.setdefault("authority_sets", {})
    authority_sets["high_authority"] = []
    authority_sets["retrieved_high_authority"] = []
    return variant


def _without_counter_material(scenario: dict) -> dict:
    variant = copy.deepcopy(scenario)
    authority_sets = variant.setdefault("authority_sets", {})
    authority_sets.setdefault("counter_or_limiting", ["__counter_material_required__"])
    authority_sets["retrieved_counter_or_limiting"] = ["__omitted_counter_material__"]
    variant.setdefault("counter_authority", {})["retrieved"] = ["__omitted_counter_material__"]
    variant.pop("counter_material_complete", None)
    return variant


def _without_review_gate(scenario: dict) -> dict:
    variant = copy.deepcopy(scenario)
    variant.pop("review_gate", None)
    return variant


def _with_professional_role_cap(scenario: dict) -> dict:
    variant = copy.deepcopy(scenario)
    variant["system_role"] = "disclosed_assistance_tool"
    return variant


def _without_decision_adoption(scenario: dict) -> dict:
    variant = copy.deepcopy(scenario)
    variant.setdefault("review_gate", {})["adoption_reasons_recorded"] = False
    return variant


def _status_name(rank: int) -> str:
    for status, status_rank in STATUS_RANK.items():
        if status_rank == rank:
            return status
    return str(rank)


def _by_ablation(rows: list[dict]) -> dict[str, dict[str, int]]:
    grouped: dict[str, dict[str, int]] = {}
    for row in rows:
        item = grouped.setdefault(row["ablation"], {"total": 0, "passed": 0, "failed": 0})
        item["total"] += 1
        item["passed" if row["passed"] else "failed"] += 1
    return grouped


def _status_distribution(rows: list[dict]) -> dict[str, int]:
    distribution: dict[str, int] = {}
    for row in rows:
        distribution[row["allowed_status"]] = distribution.get(row["allowed_status"], 0) + 1
    return distribution


def _format_report(payload: dict) -> str:
    lines = [
        "# Gate Ablation Analysis",
        "",
        f"Qualified scenarios ablated: {payload['qualified_scenario_count']}",
        f"Ablations: {payload['ablation_count']}",
        f"Passed: {payload['passed_count']}/{payload['ablation_count']}",
        "",
        "| Ablation | Total | Passed | Failed |",
        "| --- | ---: | ---: | ---: |",
    ]
    for ablation_id, item in sorted(payload["by_ablation"].items()):
        lines.append(f"| {ablation_id} | {item['total']} | {item['passed']} | {item['failed']} |")
    lines.extend(
        [
            "",
            "Status distribution after ablation: " + _distribution(payload["status_distribution"]),
        ]
    )
    if payload["failures"]:
        lines.extend(["", "## Failures", ""])
        for failure in payload["failures"]:
            lines.append(
                f"- {failure['scenario_id']} / {failure['ablation']}: {failure['allowed_status']} "
                f"with {failure['failure_flags']}"
            )
    return "\n".join(lines)


def _distribution(distribution: dict[str, int]) -> str:
    if not distribution:
        return "none"
    return ", ".join(f"{key}: {value}" for key, value in sorted(distribution.items()))


if __name__ == "__main__":
    raise SystemExit(main())
