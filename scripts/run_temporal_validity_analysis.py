from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))

from audit_harness.model import STATUS_RANK, evaluate_scenario
from run_full_validation import SUITES

RESULTS = ROOT / "experiments" / "temporal_validity" / "results"
NORMATIVE = STATUS_RANK["normative_material_screening_output"]


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    qualified = _qualified_scenarios()
    rows = []
    for path, scenario in qualified:
        rows.extend(_mutations(path, scenario))
    failures = [row for row in rows if not row["passed"]]
    payload = {
        "qualified_scenario_count": len(qualified),
        "evaluation_count": len(rows),
        "passed_count": len(rows) - len(failures),
        "failed_count": len(failures),
        "stale_snapshot_blocked_count": _passed(rows, "stale_snapshot"),
        "stale_snapshot_evaluation_count": _total(rows, "stale_snapshot"),
        "authority_drift_blocked_count": _passed(rows, "authority_drift"),
        "authority_drift_evaluation_count": _total(rows, "authority_drift"),
        "refreshed_control_preserved_count": _passed(rows, "refreshed_control"),
        "refreshed_control_evaluation_count": _total(rows, "refreshed_control"),
        "failures": failures,
        "rows": rows,
    }
    report = _format_report(payload)
    (RESULTS / "temporal_validity_analysis.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (RESULTS / "temporal_validity_analysis.md").write_text(report + "\n", encoding="utf-8")
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


def _mutations(path: Path, scenario: dict) -> list[dict]:
    return [
        _row(
            path,
            scenario,
            "stale_snapshot",
            {
                "source_collection_current": False,
                "update_checked": False,
                "snapshot_stale": True,
                "authority_status_changed": False,
            },
            "reference_information",
            "suspension",
            "source_collection_staleness",
        ),
        _row(
            path,
            scenario,
            "authority_drift",
            {
                "source_collection_current": True,
                "update_checked": True,
                "snapshot_stale": False,
                "authority_status_changed": True,
            },
            "reference_information",
            "suspension",
            "temporal_authority_drift",
        ),
        _row(
            path,
            scenario,
            "refreshed_control",
            {
                "source_collection_current": True,
                "update_checked": True,
                "snapshot_stale": False,
                "authority_status_changed": False,
            },
            None,
            None,
            None,
        ),
    ]


def _row(
    path: Path,
    base: dict,
    mutation: str,
    temporal_validity: dict,
    expected_status: str | None,
    expected_disposition: str | None,
    expected_flag: str | None,
) -> dict:
    base_result = evaluate_scenario(base)
    mutated = deepcopy(base)
    mutated.setdefault("evidence_packet", {})["temporal_validity"] = temporal_validity
    result = evaluate_scenario(mutated)
    expected_status = expected_status or base_result.allowed_status
    expected_disposition = expected_disposition or base_result.disposition
    flag_passed = expected_flag is None or expected_flag in result.failure_flags
    return {
        "scenario_id": base["id"],
        "path": str(path.relative_to(ROOT)),
        "mutation": mutation,
        "base_allowed_status": base_result.allowed_status,
        "base_disposition": base_result.disposition,
        "allowed_status": result.allowed_status,
        "disposition": result.disposition,
        "failure_flags": result.failure_flags,
        "expected_allowed_status": expected_status,
        "expected_disposition": expected_disposition,
        "expected_flag": expected_flag,
        "passed": result.allowed_status == expected_status and result.disposition == expected_disposition and flag_passed,
    }


def _passed(rows: list[dict], mutation: str) -> int:
    return sum(1 for row in rows if row["mutation"] == mutation and row["passed"])


def _total(rows: list[dict], mutation: str) -> int:
    return sum(1 for row in rows if row["mutation"] == mutation)


def _format_report(payload: dict) -> str:
    return "\n".join(
        [
            "# Temporal Validity Analysis",
            "",
            f"Qualified packets: {payload['qualified_scenario_count']}",
            f"Mutation evaluations: {payload['passed_count']}/{payload['evaluation_count']} passed",
            f"Stale source snapshots blocked: {payload['stale_snapshot_blocked_count']}/{payload['stale_snapshot_evaluation_count']}",
            f"Authority-status drift blocked: {payload['authority_drift_blocked_count']}/{payload['authority_drift_evaluation_count']}",
            f"Refreshed temporal controls preserved: {payload['refreshed_control_preserved_count']}/{payload['refreshed_control_evaluation_count']}",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
