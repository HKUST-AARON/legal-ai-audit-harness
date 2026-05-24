from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_harness.model import DIMENSIONS, PROFILE_ASSUMPTION_ALIASES, SYSTEM_ROLE_CAPS, Status, StatusPolicy, evaluate_scenario
from run_full_validation import SUITES


RESULTS = ROOT / "experiments" / "status_certificates" / "results"
CERTIFICATES = RESULTS / "status_certificates.jsonl"
CHECKS = (
    "scenario_hash",
    "claimed_status",
    "score_vector",
    "total_score",
    "score_candidate",
    "system_role",
    "role_cap",
    "failure_cap",
    "allowed_status",
    "failure_flags",
    "disposition",
    "expected_passed",
    "metric_bundle",
)


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    certificates = [_certificate(path) for path in _scenario_paths()]
    CERTIFICATES.write_text("\n".join(json.dumps(item, sort_keys=True) for item in certificates) + "\n", encoding="utf-8")
    replay_rows = [_replay(certificate) for certificate in certificates]
    failures = [row for row in replay_rows if not row["passed"]]
    payload = {
        "certificate_count": len(certificates),
        "replay_check_count": len(certificates) * len(CHECKS),
        "passed_check_count": sum(row["passed_check_count"] for row in replay_rows),
        "failed_check_count": sum(row["failed_check_count"] for row in replay_rows),
        "verified_certificate_count": len(certificates) - len(failures),
        "failed_certificate_count": len(failures),
        "status_distribution": _distribution(certificates, "allowed_status"),
        "candidate_distribution": _distribution(certificates, "score_candidate"),
        "cap_or_failure_transition_count": sum(1 for item in certificates if item["score_candidate"] != item["allowed_status"]),
        "failures": failures,
        "certificates_path": str(CERTIFICATES.relative_to(ROOT)),
        "replay_rows": replay_rows,
    }
    report = _format_report(payload)
    (RESULTS / "status_certificate_validation.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    (RESULTS / "status_certificate_validation.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0 if not failures else 1


def _scenario_paths() -> list[Path]:
    paths: list[Path] = []
    for suite in SUITES:
        paths.extend(sorted(suite["path"].glob("*.json")))
    return paths


def _certificate(path: Path) -> dict:
    scenario = json.loads(path.read_text(encoding="utf-8"))
    result = evaluate_scenario(scenario)
    scores = result.scores
    score_candidate = _score_candidate(scenario, scores, result.total_score)
    return {
        "scenario_id": scenario["id"],
        "path": str(path.relative_to(ROOT)),
        "scenario_sha256": _scenario_hash(scenario),
        "policy": asdict(StatusPolicy()),
        "claimed_status": result.claimed_status,
        "jurisdiction_profile": scenario.get("jurisdiction_profile", "unspecified"),
        "score_vector": scores,
        "total_score": result.total_score,
        "score_candidate": score_candidate,
        "system_role": result.system_role,
        "role_cap": SYSTEM_ROLE_CAPS[result.system_role],
        "missing_gates": result.missing_gates,
        "failure_flags": result.failure_flags,
        "failure_cap": _failure_cap(result.failure_flags, result.disposition),
        "disposition": result.disposition,
        "allowed_status": result.allowed_status,
        "claim_supported": result.claim_supported,
        "expected_passed": result.expected_passed,
        "metric_bundle": {
            "counter_authority_recall": result.counter_authority_recall,
            "authority_coverage": result.authority_coverage,
            "invalid_authority_rate": result.invalid_authority_rate,
            "evidence_fidelity": result.evidence_fidelity,
            "evidence_coverage": result.evidence_coverage,
            "source_tag_coverage": result.source_tag_coverage,
            "procedural_source_tag_coverage": result.procedural_source_tag_coverage,
        },
    }


def _replay(certificate: dict) -> dict:
    path = ROOT / certificate["path"]
    scenario = json.loads(path.read_text(encoding="utf-8"))
    result = evaluate_scenario(scenario)
    checks = {
        "scenario_hash": certificate["scenario_sha256"] == _scenario_hash(scenario),
        "claimed_status": certificate["claimed_status"] == result.claimed_status,
        "score_vector": certificate["score_vector"] == result.scores,
        "total_score": certificate["total_score"] == result.total_score,
        "score_candidate": certificate["score_candidate"] == _score_candidate(scenario, result.scores, result.total_score),
        "system_role": certificate["system_role"] == result.system_role,
        "role_cap": certificate["role_cap"] == SYSTEM_ROLE_CAPS[result.system_role],
        "failure_cap": certificate["failure_cap"] == _failure_cap(result.failure_flags, result.disposition),
        "allowed_status": certificate["allowed_status"] == result.allowed_status,
        "failure_flags": certificate["failure_flags"] == result.failure_flags,
        "disposition": certificate["disposition"] == result.disposition,
        "expected_passed": certificate["expected_passed"] == result.expected_passed,
        "metric_bundle": certificate["metric_bundle"] == {
            "counter_authority_recall": result.counter_authority_recall,
            "authority_coverage": result.authority_coverage,
            "invalid_authority_rate": result.invalid_authority_rate,
            "evidence_fidelity": result.evidence_fidelity,
            "evidence_coverage": result.evidence_coverage,
            "source_tag_coverage": result.source_tag_coverage,
            "procedural_source_tag_coverage": result.procedural_source_tag_coverage,
        },
    }
    return {
        "scenario_id": certificate["scenario_id"],
        "path": certificate["path"],
        "passed": all(checks.values()),
        "passed_check_count": sum(1 for passed in checks.values() if passed),
        "failed_check_count": sum(1 for passed in checks.values() if not passed),
        "failed_checks": [name for name, passed in checks.items() if not passed],
    }


def _score_candidate(scenario: dict, scores: dict[str, int], total: int) -> str:
    if (
        all(scores[dimension] >= 1 for dimension in DIMENSIONS)
        and total >= StatusPolicy().decision_threshold
        and scores["T"] == 2
        and scores["L"] == 2
        and _adoption_gate_satisfied(scenario)
    ):
        return Status.DECISION_SUPPORT_REASON.value
    if all(scores[dimension] >= 1 for dimension in DIMENSIONS) and total >= StatusPolicy().normative_threshold:
        return Status.NORMATIVE_MATERIAL_SCREENING_OUTPUT.value
    if scores["S"] >= 1 and scores["Q"] >= 1 and scores["L"] >= 1:
        return Status.PROFESSIONAL_SUPPORT_OUTPUT.value
    if scores["S"] >= 1 and scores["Q"] >= 1:
        return Status.REFERENCE_INFORMATION.value
    return Status.NO_EXTERNAL_LEGAL_EFFECT.value


def _adoption_gate_satisfied(scenario: dict) -> bool:
    gate = scenario.get("review_gate", {})
    return (
        gate.get("review_status") == "completed"
        and gate.get("reliance_gate") == "authorized_adoption"
        and gate.get("human_authorization") is True
        and _jurisdiction_assumptions_supported(scenario)
        and gate.get("adoption_reasons_recorded") is True
        and gate.get("contestation_recorded") is True
    )


def _jurisdiction_assumptions_supported(scenario: dict) -> bool:
    assumptions = set(scenario.get("review_gate", {}).get("jurisdiction_assumptions") or [])
    if not assumptions:
        return False
    profile = scenario.get("jurisdiction_profile")
    if not profile:
        return True
    return bool(assumptions & PROFILE_ASSUMPTION_ALIASES.get(profile, {profile}))


def _failure_cap(failure_flags: list[str], disposition: str) -> str | None:
    if disposition == "withdrawal":
        return Status.NO_EXTERNAL_LEGAL_EFFECT.value
    if failure_flags and disposition in {"suspension", "downgrade"}:
        return Status.REFERENCE_INFORMATION.value
    return None


def _scenario_hash(scenario: dict) -> str:
    return hashlib.sha256(json.dumps(scenario, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _distribution(certificates: list[dict], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for certificate in certificates:
        value = certificate[key]
        counts[value] = counts.get(value, 0) + 1
    return counts


def _format_report(payload: dict) -> str:
    lines = [
        "# Status Certificate Replay Validation",
        "",
        f"Status certificates: {payload['verified_certificate_count']}/{payload['certificate_count']} verified",
        f"Replay checks: {payload['passed_check_count']}/{payload['replay_check_count']} passed",
        f"Cap or failure transitions: {payload['cap_or_failure_transition_count']}",
        f"Certificate file: `{payload['certificates_path']}`",
    ]
    if payload["failures"]:
        lines.extend(["", "## Failures", ""])
        for failure in payload["failures"]:
            lines.append(f"- {failure['scenario_id']}: {', '.join(failure['failed_checks'])}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
