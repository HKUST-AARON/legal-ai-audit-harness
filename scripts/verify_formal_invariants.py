from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))

from audit_harness.model import DIMENSIONS, FLAG_DISPOSITIONS, STATUS_RANK, SYSTEM_ROLE_CAPS, evaluate_scenario

RESULTS = ROOT / "experiments" / "formal_invariants" / "results"


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    checks = [
        _check_gated_monotonicity(),
        _check_gate_non_substitutability(),
        _check_evidence_packet_necessity(),
        _check_counter_material_gate_necessity(),
        _check_decision_adoption_necessity(),
        _check_role_cap_dominance(),
        _check_failure_cap_absorption(),
        _check_metric_non_equivalence(),
    ]
    total_checks = sum(check["checks"] for check in checks)
    passed_checks = sum(check["passed"] for check in checks)
    payload = {
        "check_count": len(checks),
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "all_passed": passed_checks == total_checks,
        "checks": checks,
    }
    (RESULTS / "formal_invariant_verification.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (RESULTS / "formal_invariant_verification.md").write_text(_format_report(payload) + "\n", encoding="utf-8")
    print(_format_report(payload))
    return 0 if payload["all_passed"] else 1


def _check_gated_monotonicity() -> dict:
    vectors = list(_vectors())
    status_by_vector = {
        vector: evaluate_scenario(_scenario(vector, "authorized_decision_support_tool")).allowed_status
        for vector in vectors
    }
    failures = []
    checks = 0
    for lower in vectors:
        for upper in vectors:
            if not _componentwise_lte(lower, upper):
                continue
            checks += 1
            if STATUS_RANK[status_by_vector[upper]] < STATUS_RANK[status_by_vector[lower]]:
                failures.append(
                    {
                        "lower": dict(zip(DIMENSIONS, lower, strict=True)),
                        "upper": dict(zip(DIMENSIONS, upper, strict=True)),
                        "lower_status": status_by_vector[lower],
                        "upper_status": status_by_vector[upper],
                    }
                )
    return _check("gated_monotonicity", checks, failures)


def _check_gate_non_substitutability() -> dict:
    failures = []
    checks = 0
    for vector in _vectors():
        if all(score > 0 for score in vector):
            continue
        checks += 1
        result = evaluate_scenario(_scenario(vector, "authorized_decision_support_tool"))
        if STATUS_RANK[result.allowed_status] >= STATUS_RANK["normative_material_screening_output"]:
            failures.append({"scores": dict(zip(DIMENSIONS, vector, strict=True)), "status": result.allowed_status})
    return _check("gate_non_substitutability", checks, failures)


def _check_evidence_packet_necessity() -> dict:
    cases = []
    for field in ("authority_sets", "evidence_packet", "review_gate"):
        scenario = _scenario((2, 2, 2, 2, 2, 2), "authorized_decision_support_tool")
        scenario.pop(field, None)
        cases.append((field, scenario))

    scenario = _scenario((2, 2, 2, 2, 2, 2), "authorized_decision_support_tool")
    scenario["evidence_packet"] = {"output_units": [], "output_links": []}
    cases.append(("empty_evidence_packet", scenario))

    failures = []
    for field, scenario in cases:
        result = evaluate_scenario(scenario)
        if STATUS_RANK[result.allowed_status] >= STATUS_RANK["normative_material_screening_output"]:
            failures.append({"missing": field, "status": result.allowed_status, "flags": result.failure_flags})
    return _check("evidence_packet_necessity", len(cases), failures)


def _check_counter_material_gate_necessity() -> dict:
    cases = []

    scenario = _scenario((2, 2, 2, 2, 2, 2), "authorized_decision_support_tool")
    scenario["authority_sets"].pop("counter_or_limiting")
    cases.append(("missing_counter_material_set", scenario))

    scenario = _scenario((2, 2, 2, 2, 2, 2), "authorized_decision_support_tool")
    scenario["authority_sets"].pop("retrieved_counter_or_limiting")
    cases.append(("missing_retrieved_counter_material_set", scenario))

    scenario = _scenario((2, 2, 2, 2, 2, 2), "authorized_decision_support_tool")
    scenario["authority_sets"]["retrieved_counter_or_limiting"] = ["counter-a"]
    scenario["counter_material_complete"] = True
    cases.append(("partial_counter_material_with_complete_set_claim", scenario))

    scenario = _scenario((2, 2, 2, 2, 2, 2), "authorized_decision_support_tool")
    scenario["authority_sets"]["counter_or_limiting"] = []
    scenario["authority_sets"]["retrieved_counter_or_limiting"] = []
    cases.append(("empty_counter_material_without_complete_set_claim", scenario))

    failures = []
    for label, scenario in cases:
        result = evaluate_scenario(scenario)
        if STATUS_RANK[result.allowed_status] >= STATUS_RANK["normative_material_screening_output"]:
            failures.append({"case": label, "status": result.allowed_status, "flags": result.failure_flags})
    return _check("counter_material_gate_necessity", len(cases), failures)


def _check_decision_adoption_necessity() -> dict:
    failures = []
    checks = 0
    for vector in _vectors():
        if vector[DIMENSIONS.index("T")] == 2 and vector[DIMENSIONS.index("L")] == 2:
            continue
        checks += 1
        result = evaluate_scenario(_scenario(vector, "authorized_decision_support_tool"))
        if result.allowed_status == "decision_support_reason":
            failures.append({"scores": dict(zip(DIMENSIONS, vector, strict=True)), "status": result.allowed_status})

    for field in (
        "review_status",
        "reliance_gate",
        "human_authorization",
        "jurisdiction_assumptions",
        "adoption_reasons_recorded",
        "contestation_recorded",
    ):
        checks += 1
        scenario = _scenario((2, 2, 2, 2, 2, 2), "authorized_decision_support_tool")
        if field == "review_status":
            scenario["review_gate"][field] = "pending"
        elif field == "reliance_gate":
            scenario["review_gate"][field] = "attorney_review"
        elif field == "human_authorization":
            scenario["review_gate"][field] = False
        elif field == "jurisdiction_assumptions":
            scenario["review_gate"][field] = []
        else:
            scenario["review_gate"][field] = False
        result = evaluate_scenario(scenario)
        if result.allowed_status == "decision_support_reason":
            failures.append({"missing_adoption_field": field, "status": result.allowed_status})
    return _check("decision_adoption_necessity", checks, failures)


def _check_role_cap_dominance() -> dict:
    failures = []
    checks = 0
    for role, cap in SYSTEM_ROLE_CAPS.items():
        for vector in _vectors():
            checks += 1
            result = evaluate_scenario(_scenario(vector, role))
            if STATUS_RANK[result.allowed_status] > STATUS_RANK[cap]:
                failures.append(
                    {
                        "role": role,
                        "cap": cap,
                        "scores": dict(zip(DIMENSIONS, vector, strict=True)),
                        "status": result.allowed_status,
                    }
                )
    return _check("role_cap_dominance", checks, failures)


def _check_failure_cap_absorption() -> dict:
    failures = []
    checks = 0
    for flag, disposition in FLAG_DISPOSITIONS.items():
        checks += 1
        scenario = _scenario((2, 2, 2, 2, 2, 2), "authorized_decision_support_tool")
        scenario["failure_flags"] = [flag]
        result = evaluate_scenario(scenario)
        if disposition == "withdrawal":
            expected_max = "no_external_legal_effect"
        elif disposition in {"downgrade", "suspension"}:
            expected_max = "reference_information"
        else:
            expected_max = "decision_support_reason"
        if STATUS_RANK[result.allowed_status] > STATUS_RANK[expected_max]:
            failures.append(
                {
                    "flag": flag,
                    "disposition": disposition,
                    "expected_max": expected_max,
                    "status": result.allowed_status,
                }
            )
    return _check("failure_cap_absorption", checks, failures)


def _check_metric_non_equivalence() -> dict:
    scenarios = [
        _scenario(
            (0, 2, 2, 2, 2, 2),
            "authorized_decision_support_tool",
            extra={"upstream_metrics": {"authority_recall": 1.0, "counter_material_recall": 1.0}},
        ),
        _scenario(
            (2, 2, 2, 2, 2, 2),
            "authorized_decision_support_tool",
            extra={
                "claimed_status": "normative_material_screening_output",
                "authority_sets": {
                    "high_authority": ["a"],
                    "retrieved_high_authority": ["a"],
                    "counter_or_limiting": ["b"],
                    "retrieved_counter_or_limiting": ["b"],
                    "retrieved": ["a", "b"],
                },
                "evidence_packet": {
                    "output_units": [{"id": "u1", "source_ids": ["a"], "locators": ["p.1"]}],
                    "output_links": [
                        {
                            "unit_id": "u1",
                            "source_id": "a",
                            "locator": "p.1",
                            "supports_claim": True,
                            "source_tag": "needs_verification",
                        }
                    ],
                },
                "upstream_metrics": {"authority_recall": 1.0, "counter_material_recall": 1.0},
            },
        ),
    ]
    failures = []
    for index, scenario in enumerate(scenarios, start=1):
        result = evaluate_scenario(scenario)
        if STATUS_RANK[result.allowed_status] > STATUS_RANK["reference_information"]:
            failures.append({"case": index, "status": result.allowed_status, "scores": result.scores})
    return _check("metric_non_equivalence", len(scenarios), failures)


def _vectors() -> tuple[tuple[int, ...], ...]:
    return tuple(itertools.product((0, 1, 2), repeat=len(DIMENSIONS)))


def _componentwise_lte(lower: tuple[int, ...], upper: tuple[int, ...]) -> bool:
    return all(a <= b for a, b in zip(lower, upper, strict=True))


def _scenario(vector: tuple[int, ...], role: str, extra: dict | None = None) -> dict:
    scenario = {
        "id": "formal-invariant-check",
        "claimed_status": "decision_support_reason",
        "system_role": role,
        "scores": {dimension: score for dimension, score in zip(DIMENSIONS, vector, strict=True)},
        "authority_sets": {
            "high_authority": ["authority-a", "authority-b"],
            "retrieved_high_authority": ["authority-a", "authority-b"],
            "counter_or_limiting": ["counter-a", "counter-b"],
            "retrieved_counter_or_limiting": ["counter-a", "counter-b"],
            "retrieved": ["authority-a", "authority-b", "counter-a", "counter-b"],
        },
        "evidence_packet": {
            "output_units": [
                {
                    "id": "u1",
                    "source_ids": ["authority-a", "counter-a"],
                    "locators": ["authority-a:1", "counter-a:1"],
                }
            ],
            "output_links": [
                {
                    "unit_id": "u1",
                    "source_id": "authority-a",
                    "locator": "authority-a:1",
                    "supports_claim": True,
                    "source_tag": "tool_verified",
                },
                {
                    "unit_id": "u1",
                    "source_id": "counter-a",
                    "locator": "counter-a:1",
                    "supports_claim": True,
                    "source_tag": "tool_verified",
                },
            ],
        },
        "review_gate": {
            "review_status": "completed",
            "reliance_gate": "authorized_adoption",
            "human_authorization": True,
            "jurisdiction_assumptions": ["test jurisdiction"],
            "adoption_reasons_recorded": True,
            "contestation_recorded": True,
        },
    }
    if extra:
        scenario.update(extra)
    return scenario


def _check(identifier: str, checks: int, failures: list[dict]) -> dict:
    return {
        "id": identifier,
        "checks": checks,
        "passed": checks - len(failures),
        "failed": len(failures),
        "failures": failures[:10],
    }


def _format_report(payload: dict) -> str:
    lines = [
        "# Formal Invariant Verification",
        "",
        f"Checks: {payload['passed_checks']}/{payload['total_checks']}",
        f"All passed: {payload['all_passed']}",
        "",
        "| Invariant | Checks | Passed | Failed |",
        "| --- | ---: | ---: | ---: |",
    ]
    for check in payload["checks"]:
        lines.append(f"| {check['id']} | {check['checks']} | {check['passed']} | {check['failed']} |")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
