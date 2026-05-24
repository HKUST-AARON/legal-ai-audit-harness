from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_harness.model import PROFILE_ASSUMPTION_ALIASES, STATUS_RANK, Status, evaluate_scenario
from run_full_validation import SUITES


RESULTS = ROOT / "experiments" / "jurisdiction_profiles" / "results"
NORMATIVE = STATUS_RANK[Status.NORMATIVE_MATERIAL_SCREENING_OUTPUT.value]


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    profile_checks, mutations = _analysis_rows()
    failures = [row for row in mutations if not row["passed"]]
    unsupported = [row for row in profile_checks if not row["profile_supported"]]
    payload = {
        "profile_check_count": len(profile_checks),
        "profile_supported_count": len(profile_checks) - len(unsupported),
        "qualified_status_count": len({row["scenario_id"] for row in mutations}),
        "counterfactual_evaluation_count": len(mutations),
        "generic_profile_preserved": _passed_count(mutations, "generic_profile"),
        "missing_assumption_downgraded": _passed_count(mutations, "missing_assumption"),
        "mismatched_profile_downgraded": _passed_count(mutations, "mismatched_profile"),
        "passed_count": len(mutations) - len(failures),
        "failed_count": len(failures),
        "unsupported_profile_checks": unsupported,
        "failures": failures,
        "profile_checks": profile_checks,
        "mutations": mutations,
    }
    report = _format_report(payload)
    (RESULTS / "jurisdiction_profile_analysis.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    (RESULTS / "jurisdiction_profile_analysis.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0 if not failures and not unsupported else 1


def _analysis_rows() -> tuple[list[dict], list[dict]]:
    profile_checks: list[dict] = []
    mutations: list[dict] = []
    for path in _scenario_paths():
        scenario = json.loads(path.read_text(encoding="utf-8"))
        base = evaluate_scenario(scenario)
        target_rank = max(STATUS_RANK[scenario["claimed_status"]], STATUS_RANK[base.allowed_status])
        if target_rank >= NORMATIVE:
            profile_checks.append(_profile_check(path, scenario))
        if STATUS_RANK[base.allowed_status] >= NORMATIVE:
            mutations.extend(_mutations(path, scenario, base.allowed_status, base.disposition))
    return profile_checks, mutations


def _scenario_paths() -> list[Path]:
    paths: list[Path] = []
    for suite in SUITES:
        paths.extend(sorted(suite["path"].glob("*.json")))
    return paths


def _profile_check(path: Path, scenario: dict) -> dict:
    return {
        "scenario_id": scenario["id"],
        "path": str(path.relative_to(ROOT)),
        "jurisdiction_profile": scenario.get("jurisdiction_profile"),
        "jurisdiction_assumptions": _assumptions(scenario),
        "profile_supported": _profile_supported(scenario),
    }


def _mutations(path: Path, scenario: dict, base_status: str, base_disposition: str) -> list[dict]:
    rows = []
    for mutation, assumptions in {
        "generic_profile": [_generic_profile(scenario)],
        "missing_assumption": [],
        "mismatched_profile": [_mismatched_profile(scenario)],
    }.items():
        variant = copy.deepcopy(scenario)
        variant.pop("expected_allowed_status", None)
        variant.pop("expected_disposition", None)
        gate = variant.setdefault("review_gate", {})
        gate["jurisdiction_assumptions"] = assumptions
        result = evaluate_scenario(variant)
        if mutation == "generic_profile":
            passed = result.allowed_status == base_status and result.disposition == base_disposition
        else:
            passed = STATUS_RANK[result.allowed_status] < NORMATIVE and "jurisdiction_assumption_gap" in result.failure_flags
        rows.append(
            {
                "scenario_id": scenario["id"],
                "path": str(path.relative_to(ROOT)),
                "mutation": mutation,
                "jurisdiction_profile": scenario.get("jurisdiction_profile"),
                "base_status": base_status,
                "mutated_status": result.allowed_status,
                "mutated_disposition": result.disposition,
                "failure_flags": result.failure_flags,
                "passed": passed,
            }
        )
    return rows


def _profile_supported(scenario: dict) -> bool:
    assumptions = set(_assumptions(scenario))
    profile = scenario.get("jurisdiction_profile")
    if not assumptions:
        return False
    if not profile:
        return True
    return bool(assumptions & PROFILE_ASSUMPTION_ALIASES.get(profile, {profile}))


def _assumptions(scenario: dict) -> list[str]:
    return list(scenario.get("review_gate", {}).get("jurisdiction_assumptions") or [])


def _generic_profile(scenario: dict) -> str:
    return scenario.get("jurisdiction_profile") or "generic_jurisdiction"


def _mismatched_profile(scenario: dict) -> str:
    profile = scenario.get("jurisdiction_profile")
    for candidate in PROFILE_ASSUMPTION_ALIASES:
        if candidate != profile:
            return candidate
    return "mismatched_jurisdiction"


def _passed_count(rows: list[dict], mutation: str) -> int:
    return sum(1 for row in rows if row["mutation"] == mutation and row["passed"])


def _format_report(payload: dict) -> str:
    return "\n".join(
        [
            "# Jurisdiction Profile Analysis",
            "",
            f"High-status profile checks: {payload['profile_supported_count']}/{payload['profile_check_count']} supported",
            f"Qualified packets mutated: {payload['qualified_status_count']}",
            f"Counterfactual profile evaluations: {payload['passed_count']}/{payload['counterfactual_evaluation_count']} passed",
            f"Generic profile substitutions preserved status: {payload['generic_profile_preserved']}/{payload['qualified_status_count']}",
            f"Missing assumptions downgraded status: {payload['missing_assumption_downgraded']}/{payload['qualified_status_count']}",
            f"Mismatched profiles downgraded status: {payload['mismatched_profile_downgraded']}/{payload['qualified_status_count']}",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
