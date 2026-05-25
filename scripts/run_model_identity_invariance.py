from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_harness.model import evaluate_scenario
from run_full_validation import SUITES

RESULTS = ROOT / "experiments" / "model_identity_invariance" / "results"

IDENTITY_PROFILES = [
    {
        "profile_id": "frontier_general_model",
        "provider": "frontier-general-provider",
        "model": "frontier-general-model",
        "engine": "frontier-general-engine",
        "claimed_capability": "general frontier model",
    },
    {
        "profile_id": "legal_vendor_model",
        "provider": "legal-research-vendor",
        "model": "legal-research-specialist",
        "engine": "legal-vendor-engine",
        "claimed_capability": "legal specialist model",
    },
    {
        "profile_id": "open_weight_model",
        "provider": "open-weight-provider",
        "model": "open-weight-legal-tuned",
        "engine": "open-weight-engine",
        "claimed_capability": "open-weight legal tuned model",
    },
    {
        "profile_id": "small_fast_model",
        "provider": "small-fast-provider",
        "model": "small-fast-model",
        "engine": "small-fast-engine",
        "claimed_capability": "small low-latency model",
    },
    {
        "profile_id": "undisclosed_agentic_model",
        "provider": "undisclosed-agentic-provider",
        "model": "undisclosed-agent-stack",
        "engine": "agentic-search-and-generation-stack",
        "claimed_capability": "agentic legal workflow",
    },
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
    rows: list[dict] = []
    for scenario in scenarios:
        base = evaluate_scenario(scenario)
        base_projection = _projection(base)
        for profile in IDENTITY_PROFILES:
            mutated = _with_identity(scenario, profile)
            result = evaluate_scenario(mutated)
            result_projection = _projection(result)
            changed_fields = [
                field
                for field in INVARIANT_FIELDS
                if base_projection[field] != result_projection[field]
            ]
            rows.append(
                {
                    "scenario_id": scenario["id"],
                    "source_path": scenario.get("_source_path"),
                    "identity_profile": profile["profile_id"],
                    "provider": profile["provider"],
                    "model": profile["model"],
                    "engine": profile["engine"],
                    "claimed_capability": profile["claimed_capability"],
                    "base_allowed_status": base.allowed_status,
                    "mutated_allowed_status": result.allowed_status,
                    "base_disposition": base.disposition,
                    "mutated_disposition": result.disposition,
                    "changed_fields": changed_fields,
                    "passed": not changed_fields,
                }
            )
    failures = [row for row in rows if not row["passed"]]
    payload = {
        "scenario_count": len(scenarios),
        "identity_profile_count": len(IDENTITY_PROFILES),
        "evaluation_count": len(rows),
        "passed_count": len(rows) - len(failures),
        "failed_count": len(failures),
        "status_changed_count": sum(
            row["base_allowed_status"] != row["mutated_allowed_status"] for row in rows
        ),
        "disposition_changed_count": sum(
            row["base_disposition"] != row["mutated_disposition"] for row in rows
        ),
        "identity_profiles": IDENTITY_PROFILES,
        "by_identity_profile": _by_profile(rows),
        "base_status_distribution_by_scenario": _scenario_distribution(scenarios),
        "row_weighted_base_status_distribution": _distribution(rows, "base_allowed_status"),
        "row_weighted_mutated_status_distribution": _distribution(rows, "mutated_allowed_status"),
        "failures": failures,
        "rows": rows,
    }
    (RESULTS / "model_identity_invariance.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    report = _format_report(payload)
    (RESULTS / "model_identity_invariance.md").write_text(report + "\n", encoding="utf-8")
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


def _with_identity(scenario: dict, profile: dict) -> dict:
    mutated = deepcopy(scenario)
    upstream = mutated.setdefault("upstream_output", {})
    upstream.update(
        {
            "provider": profile["provider"],
            "model": profile["model"],
            "engine": profile["engine"],
            "model_identity_profile": profile["profile_id"],
            "claimed_capability": profile["claimed_capability"],
        }
    )
    mutated["model_identity_profile"] = profile["profile_id"]
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


def _by_profile(rows: list[dict]) -> dict[str, dict]:
    buckets: dict[str, dict] = {}
    for row in rows:
        bucket = buckets.setdefault(
            row["identity_profile"],
            {
                "count": 0,
                "passed": 0,
                "failed": 0,
                "status_changed": 0,
                "disposition_changed": 0,
            },
        )
        bucket["count"] += 1
        if row["passed"]:
            bucket["passed"] += 1
        else:
            bucket["failed"] += 1
        if row["base_allowed_status"] != row["mutated_allowed_status"]:
            bucket["status_changed"] += 1
        if row["base_disposition"] != row["mutated_disposition"]:
            bucket["disposition_changed"] += 1
    return buckets


def _distribution(rows: list[dict], field: str) -> dict[str, int]:
    distribution: dict[str, int] = {}
    for row in rows:
        value = row[field]
        distribution[value] = distribution.get(value, 0) + 1
    return dict(sorted(distribution.items()))


def _scenario_distribution(scenarios: list[dict]) -> dict[str, int]:
    distribution: dict[str, int] = {}
    for scenario in scenarios:
        status = evaluate_scenario(scenario).allowed_status
        distribution[status] = distribution.get(status, 0) + 1
    return dict(sorted(distribution.items()))


def _format_report(payload: dict) -> str:
    lines = [
        "# Model Identity Invariance",
        "",
        f"Scenario packets: {payload['scenario_count']}",
        f"Identity profiles: {payload['identity_profile_count']}",
        f"Identity-mutated evaluations: {payload['evaluation_count']}",
        f"Passed: {payload['passed_count']}/{payload['evaluation_count']}",
        f"Status changes: {payload['status_changed_count']}",
        f"Disposition changes: {payload['disposition_changed_count']}",
        "",
        "| Identity profile | Provider | Model | Engine | Capability |",
        "| --- | --- | --- | --- | --- |",
    ]
    for profile in payload["identity_profiles"]:
        lines.append(
            f"| {profile['profile_id']} | {profile['provider']} | {profile['model']} | "
            f"{profile['engine']} | {profile['claimed_capability']} |"
        )
    lines.extend(
        [
            "",
            "## Invariance Results",
            "",
            "| Identity profile | Count | Passed | Failed | Status changes | Disposition changes |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for profile, bucket in sorted(payload["by_identity_profile"].items()):
        lines.append(
            f"| {profile} | {bucket['count']} | {bucket['passed']} | {bucket['failed']} | "
            f"{bucket['status_changed']} | {bucket['disposition_changed']} |"
        )
    if payload["failed_count"]:
        lines.extend(["", "## Failure examples", ""])
        for row in payload["failures"][:10]:
            lines.append(
                f"- {row['scenario_id']} under {row['identity_profile']}: "
                f"{', '.join(row['changed_fields'])}"
            )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
