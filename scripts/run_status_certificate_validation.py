from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_harness.model import (
    DIMENSIONS,
    DISPOSITION_RANK,
    FLAG_DISPOSITIONS,
    PROFILE_ASSUMPTION_ALIASES,
    STATUS_RANK,
    SYSTEM_ROLE_CAPS,
    Status,
    StatusPolicy,
    evaluate_scenario,
)
from run_full_validation import SUITES


POLICY_PATH = ROOT / "policy" / "legal_output_policy.json"
RESULTS = ROOT / "experiments" / "status_certificates" / "results"
CERTIFICATES = RESULTS / "status_certificates.jsonl"
CHECKS = (
    "scenario_hash",
    "policy_hash",
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
    "proof_obligations",
    "proof_obligation_count",
    "derivation_hash",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate or verify proof-carrying legal-output status certificates.")
    parser.add_argument(
        "--verify-existing",
        action="store_true",
        help="verify the committed certificate JSONL without regenerating it first",
    )
    args = parser.parse_args(argv)
    RESULTS.mkdir(parents=True, exist_ok=True)
    if args.verify_existing:
        certificates = _load_certificates()
    else:
        certificates = [_certificate(path) for path in _scenario_paths()]
        CERTIFICATES.write_text("\n".join(json.dumps(item, sort_keys=True) for item in certificates) + "\n", encoding="utf-8")
        certificates = _load_certificates()
    payload = _validate_certificates(certificates)
    report = _format_report(payload)
    (RESULTS / "status_certificate_validation.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    (RESULTS / "status_certificate_validation.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0 if not payload["failures"] and payload["failed_proof_obligation_count"] == 0 else 1


def _load_certificates() -> list[dict]:
    return [json.loads(line) for line in CERTIFICATES.read_text(encoding="utf-8").splitlines() if line.strip()]


def _validate_certificates(certificates: list[dict]) -> dict:
    replay_rows = [_replay(certificate) for certificate in certificates]
    path_failures = _path_set_failures(certificates)
    failures = [row for row in replay_rows if not row["passed"]] + path_failures
    proof_obligation_count = sum(item["proof_obligation_count"] for item in certificates)
    passed_proof_obligation_count = sum(
        sum(1 for obligation in item["proof_obligations"] if obligation["passed"])
        for item in certificates
    )
    payload = {
        "certificate_count": len(certificates),
        "replay_check_count": len(certificates) * len(CHECKS),
        "passed_check_count": sum(row["passed_check_count"] for row in replay_rows),
        "failed_check_count": sum(row["failed_check_count"] for row in replay_rows),
        "proof_obligation_count": proof_obligation_count,
        "passed_proof_obligation_count": passed_proof_obligation_count,
        "failed_proof_obligation_count": proof_obligation_count - passed_proof_obligation_count,
        "verified_certificate_count": len(certificates) - len(failures),
        "failed_certificate_count": len(failures),
        "status_distribution": _distribution(certificates, "allowed_status"),
        "candidate_distribution": _distribution(certificates, "score_candidate"),
        "cap_or_failure_transition_count": sum(1 for item in certificates if item["score_candidate"] != item["allowed_status"]),
        "failures": failures,
        "missing_certificate_paths": path_failures[0]["missing_certificate_paths"] if path_failures else [],
        "extra_certificate_paths": path_failures[0]["extra_certificate_paths"] if path_failures else [],
        "duplicate_certificate_paths": path_failures[0]["duplicate_certificate_paths"] if path_failures else [],
        "certificates_path": str(CERTIFICATES.relative_to(ROOT)),
        "replay_rows": replay_rows,
    }
    return payload


def _path_set_failures(certificates: list[dict]) -> list[dict]:
    expected_paths = {str(path.relative_to(ROOT)) for path in _scenario_paths()}
    seen: dict[str, int] = {}
    for certificate in certificates:
        path = certificate["path"]
        seen[path] = seen.get(path, 0) + 1
    actual_paths = set(seen)
    missing = sorted(expected_paths - actual_paths)
    extra = sorted(actual_paths - expected_paths)
    duplicates = sorted(path for path, count in seen.items() if count > 1)
    if not missing and not extra and not duplicates:
        return []
    failed_checks = []
    if missing:
        failed_checks.append("missing_certificate_paths")
    if extra:
        failed_checks.append("extra_certificate_paths")
    if duplicates:
        failed_checks.append("duplicate_certificate_paths")
    return [
        {
            "scenario_id": "__certificate_set__",
            "path": str(CERTIFICATES.relative_to(ROOT)),
            "passed": False,
            "passed_check_count": 0,
            "failed_check_count": len(failed_checks),
            "failed_checks": failed_checks,
            "missing_certificate_paths": missing,
            "extra_certificate_paths": extra,
            "duplicate_certificate_paths": duplicates,
        }
    ]


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
    certificate = {
        "scenario_id": scenario["id"],
        "path": str(path.relative_to(ROOT)),
        "scenario_sha256": _scenario_hash(scenario),
        "policy_sha256": _file_hash(POLICY_PATH),
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
    certificate["proof_obligations"] = _proof_obligations(certificate)
    certificate["proof_obligation_count"] = len(certificate["proof_obligations"])
    certificate["derivation_sha256"] = _certificate_hash(certificate)
    return certificate


def _replay(certificate: dict) -> dict:
    path = ROOT / certificate["path"]
    scenario = json.loads(path.read_text(encoding="utf-8"))
    result = evaluate_scenario(scenario)
    replay_certificate = _certificate(path)
    checks = {
        "scenario_hash": certificate["scenario_sha256"] == _scenario_hash(scenario),
        "policy_hash": certificate["policy_sha256"] == _file_hash(POLICY_PATH),
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
        "proof_obligations": certificate["proof_obligations"] == replay_certificate["proof_obligations"] and all(
            obligation["passed"] for obligation in certificate["proof_obligations"]
        ),
        "proof_obligation_count": certificate["proof_obligation_count"] == replay_certificate["proof_obligation_count"],
        "derivation_hash": certificate["derivation_sha256"] == replay_certificate["derivation_sha256"],
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


def _proof_obligations(certificate: dict) -> list[dict]:
    rank = STATUS_RANK
    score_vector = certificate["score_vector"]
    metrics = certificate["metric_bundle"]
    failure_cap = certificate["failure_cap"]
    score_candidate = certificate["score_candidate"]
    allowed_status = certificate["allowed_status"]
    role_cap = certificate["role_cap"]
    obligations = {
        "scenario_hash_bound": len(certificate["scenario_sha256"]) == 64,
        "policy_hash_bound": len(certificate["policy_sha256"]) == 64,
        "score_vector_complete": set(score_vector) == set(DIMENSIONS) and all(value in (0, 1, 2) for value in score_vector.values()),
        "total_score_recomputable": certificate["total_score"] == sum(score_vector.values()),
        "score_candidate_ranked": score_candidate in rank,
        "system_role_known": certificate["system_role"] in SYSTEM_ROLE_CAPS,
        "role_cap_recomputable": role_cap == SYSTEM_ROLE_CAPS[certificate["system_role"]],
        "role_cap_respected": rank[allowed_status] <= rank[role_cap],
        "failure_flags_known": set(certificate["failure_flags"]).issubset(set(FLAG_DISPOSITIONS)),
        "disposition_ranked": certificate["disposition"] in DISPOSITION_RANK,
        "failure_cap_recomputable": failure_cap == _failure_cap(certificate["failure_flags"], certificate["disposition"]),
        "failure_cap_respected": failure_cap is None or rank[allowed_status] <= rank[failure_cap],
        "metric_bundle_bounded": all(value is None or 0 <= value <= 1 for value in metrics.values()),
        "expected_outcome_checked": isinstance(certificate["expected_passed"], bool),
        "claim_support_matches_rank": certificate["claim_supported"] == (rank[allowed_status] >= rank[certificate["claimed_status"]]),
        "allowed_status_exact_derivation": allowed_status == _derived_allowed_status(certificate),
    }
    return [{"id": name, "passed": passed} for name, passed in obligations.items()]


def _derived_allowed_status(certificate: dict) -> str:
    candidates = [certificate["score_candidate"], certificate["role_cap"]]
    if certificate["failure_cap"] is not None:
        candidates.append(certificate["failure_cap"])
    return min(candidates, key=lambda status: STATUS_RANK[status])


def _scenario_hash(scenario: dict) -> str:
    return hashlib.sha256(json.dumps(scenario, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _certificate_hash(certificate: dict) -> str:
    body = {key: value for key, value in certificate.items() if key != "derivation_sha256"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


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
        f"Proof obligations: {payload['passed_proof_obligation_count']}/{payload['proof_obligation_count']} passed",
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
