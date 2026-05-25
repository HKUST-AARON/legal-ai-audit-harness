from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))

from audit_harness.model import STATUS_RANK, evaluate_scenario
from run_full_validation import SUITES

RESULTS = ROOT / "experiments" / "claim_anchor_analysis" / "results"
NORMATIVE = STATUS_RANK["normative_material_screening_output"]


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    qualified = _qualified_scenarios()
    rows = []
    for path, scenario in qualified:
        rows.extend(_unit_mutations(path, scenario))
        rows.extend(_link_mutations(path, scenario))
    failures = [row for row in rows if not row["passed"]]
    payload = {
        "scenario_count": len(qualified),
        "output_unit_count": sum(len(scenario.get("evidence_packet", {}).get("output_units", [])) for _, scenario in qualified),
        "output_link_count": sum(len(scenario.get("evidence_packet", {}).get("output_links", [])) for _, scenario in qualified),
        "evaluation_count": len(rows),
        "passed_count": len(rows) - len(failures),
        "failed_count": len(failures),
        "claim_text_absence_blocked_count": _passed(rows, "claim_text_absence"),
        "claim_text_absence_evaluation_count": _total(rows, "claim_text_absence"),
        "link_unit_binding_absence_blocked_count": _passed(rows, "link_unit_binding_absence"),
        "link_unit_binding_absence_evaluation_count": _total(rows, "link_unit_binding_absence"),
        "support_attestation_absence_withdrawn_count": _passed(rows, "support_attestation_absence"),
        "support_attestation_absence_evaluation_count": _total(rows, "support_attestation_absence"),
        "locator_absence_withdrawn_count": _passed(rows, "locator_absence"),
        "locator_absence_evaluation_count": _total(rows, "locator_absence"),
        "failures": failures,
        "rows": rows,
    }
    report = _format_report(payload)
    (RESULTS / "claim_anchor_analysis.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    (RESULTS / "claim_anchor_analysis.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0 if not failures else 1


def _qualified_scenarios() -> list[tuple[Path, dict]]:
    scenarios = []
    for suite in SUITES:
        for path in sorted(suite["path"].glob("*.json")):
            scenario = json.loads(path.read_text(encoding="utf-8"))
            result = evaluate_scenario(scenario)
            if STATUS_RANK[result.allowed_status] >= NORMATIVE:
                scenarios.append((path, scenario))
    return scenarios


def _unit_mutations(path: Path, scenario: dict) -> list[dict]:
    rows = []
    units = scenario.get("evidence_packet", {}).get("output_units", [])
    for index, unit in enumerate(units):
        claimless = deepcopy(scenario)
        claimless["evidence_packet"]["output_units"][index].pop("claim", None)
        rows.append(_row(path, scenario, claimless, "claim_text_absence", unit.get("id"), "reference_information", "downgrade"))

        locatorless = deepcopy(scenario)
        locatorless["evidence_packet"]["output_units"][index]["locators"] = []
        rows.append(_row(path, scenario, locatorless, "locator_absence", unit.get("id"), "no_external_legal_effect", "withdrawal"))
    return rows


def _link_mutations(path: Path, scenario: dict) -> list[dict]:
    rows = []
    links = scenario.get("evidence_packet", {}).get("output_links", [])
    for index, link in enumerate(links):
        unbound = deepcopy(scenario)
        unbound["evidence_packet"]["output_links"][index].pop("unit_id", None)
        rows.append(_row(path, scenario, unbound, "link_unit_binding_absence", link.get("unit_id"), "reference_information", "downgrade"))

        unsupported = deepcopy(scenario)
        unsupported["evidence_packet"]["output_links"][index]["supports_claim"] = False
        rows.append(_row(path, scenario, unsupported, "support_attestation_absence", link.get("unit_id"), "no_external_legal_effect", "withdrawal"))
    return rows


def _row(path: Path, base: dict, mutated: dict, mutation: str, target: str | None, expected_status: str, expected_disposition: str) -> dict:
    base_result = evaluate_scenario(base)
    result = evaluate_scenario(mutated)
    return {
        "scenario_id": base["id"],
        "path": str(path.relative_to(ROOT)),
        "mutation": mutation,
        "target": target,
        "base_allowed_status": base_result.allowed_status,
        "allowed_status": result.allowed_status,
        "disposition": result.disposition,
        "failure_flags": result.failure_flags,
        "expected_allowed_status": expected_status,
        "expected_disposition": expected_disposition,
        "passed": result.allowed_status == expected_status and result.disposition == expected_disposition,
    }


def _passed(rows: list[dict], mutation: str) -> int:
    return sum(1 for row in rows if row["mutation"] == mutation and row["passed"])


def _total(rows: list[dict], mutation: str) -> int:
    return sum(1 for row in rows if row["mutation"] == mutation)


def _format_report(payload: dict) -> str:
    return "\n".join(
        [
            "# Claim-Anchor Analysis",
            "",
            f"Qualified packets: {payload['scenario_count']}",
            f"Output units: {payload['output_unit_count']}",
            f"Output links: {payload['output_link_count']}",
            f"Mutation evaluations: {payload['passed_count']}/{payload['evaluation_count']} passed",
            f"Claim-text removals blocked: {payload['claim_text_absence_blocked_count']}/{payload['claim_text_absence_evaluation_count']}",
            f"Link-to-claim removals blocked: {payload['link_unit_binding_absence_blocked_count']}/{payload['link_unit_binding_absence_evaluation_count']}",
            f"Support-attestation removals withdrawn: {payload['support_attestation_absence_withdrawn_count']}/{payload['support_attestation_absence_evaluation_count']}",
            f"Locator removals withdrawn: {payload['locator_absence_withdrawn_count']}/{payload['locator_absence_evaluation_count']}",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
