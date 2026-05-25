from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "legal_output_policy.json"
CERTIFICATES = ROOT / "experiments" / "status_certificates" / "results" / "status_certificates.jsonl"
RESULTS = ROOT / "experiments" / "policy_constants_replay" / "results"
SCENARIO_DIRS = [
    ROOT / "examples" / "scenarios",
    ROOT / "experiments" / "real_cases" / "scenarios",
    ROOT / "experiments" / "public_system_outputs" / "scenarios",
    ROOT / "experiments" / "issue_public_outputs" / "scenarios",
    ROOT / "experiments" / "public_retrieval_benchmark" / "scenarios",
    ROOT / "experiments" / "holdout_validation" / "scenarios",
    ROOT / "experiments" / "ai_outputs" / "scenarios",
    ROOT / "experiments" / "model_output_repairs" / "scenarios",
    ROOT / "experiments" / "model_output_evidence_ladder" / "scenarios",
    ROOT / "experiments" / "model_output_adversarial" / "scenarios",
    ROOT / "experiments" / "issue_gold_sets" / "scenarios",
    ROOT / "experiments" / "issue_ablations" / "scenarios",
]
CHECKS = (
    "scenario_hash",
    "policy",
    "claimed_status",
    "jurisdiction_profile",
    "score_vector",
    "total_score",
    "score_candidate",
    "system_role",
    "role_cap",
    "missing_gates",
    "failure_flags",
    "disposition",
    "failure_cap",
    "allowed_status",
    "claim_supported",
    "expected_passed",
    "metric_bundle",
)


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    policy = _load_json(POLICY_PATH)
    certificates = _load_certificates()
    paths = _scenario_paths()
    _assert_path_sets_match(paths, certificates)
    rows = [_replay(path, policy, certificates[str(path.relative_to(ROOT))]) for path in paths]
    failures = [row for row in rows if not row["passed"]]
    payload = {
        "policy_path": str(POLICY_PATH.relative_to(ROOT)),
        "certificate_path": str(CERTIFICATES.relative_to(ROOT)),
        "certificate_count": len(certificates),
        "scenario_count": len(rows),
        "check_count": len(rows) * len(CHECKS),
        "passed_check_count": sum(row["passed_check_count"] for row in rows),
        "failed_check_count": sum(row["failed_check_count"] for row in rows),
        "verified_scenario_count": len(rows) - len(failures),
        "failed_scenario_count": len(failures),
        "status_distribution": _distribution(rows, "allowed_status"),
        "score_candidate_distribution": _distribution(rows, "score_candidate"),
        "cap_or_failure_transition_count": sum(1 for row in rows if row["score_candidate"] != row["allowed_status"]),
        "failures": failures,
        "rows": rows,
    }
    report = _format_report(payload)
    (RESULTS / "policy_constants_replay.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    (RESULTS / "policy_constants_replay.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0 if not failures else 1


def _scenario_paths() -> list[Path]:
    paths: list[Path] = []
    for directory in SCENARIO_DIRS:
        paths.extend(sorted(directory.glob("*.json")))
    return paths


def _load_certificates() -> dict[str, dict]:
    items = [json.loads(line) for line in CERTIFICATES.read_text(encoding="utf-8").splitlines() if line]
    paths = [item["path"] for item in items]
    duplicates = sorted({path for path in paths if paths.count(path) > 1})
    if duplicates:
        raise ValueError(f"Duplicate certificate paths: {duplicates[:5]}")
    return {item["path"]: item for item in items}


def _assert_path_sets_match(paths: list[Path], certificates: dict[str, dict]) -> None:
    scenario_paths = {str(path.relative_to(ROOT)) for path in paths}
    certificate_paths = set(certificates)
    missing = sorted(scenario_paths - certificate_paths)
    extra = sorted(certificate_paths - scenario_paths)
    if missing or extra:
        raise ValueError(f"Certificate/scenario path mismatch: missing={missing[:5]}, extra={extra[:5]}")


def _replay(path: Path, policy: dict, certificate: dict) -> dict:
    scenario = _load_json(path)
    replay = _evaluate(scenario, policy)
    checks = {
        "scenario_hash": certificate["scenario_sha256"] == _scenario_hash(scenario),
        "policy": certificate["policy"] == replay["policy"],
        "claimed_status": certificate["claimed_status"] == replay["claimed_status"],
        "jurisdiction_profile": certificate["jurisdiction_profile"] == replay["jurisdiction_profile"],
        "score_vector": certificate["score_vector"] == replay["score_vector"],
        "total_score": certificate["total_score"] == replay["total_score"],
        "score_candidate": certificate["score_candidate"] == replay["score_candidate"],
        "system_role": certificate["system_role"] == replay["system_role"],
        "role_cap": certificate["role_cap"] == replay["role_cap"],
        "missing_gates": certificate["missing_gates"] == replay["missing_gates"],
        "failure_flags": certificate["failure_flags"] == replay["failure_flags"],
        "disposition": certificate["disposition"] == replay["disposition"],
        "failure_cap": certificate["failure_cap"] == replay["failure_cap"],
        "allowed_status": certificate["allowed_status"] == replay["allowed_status"],
        "claim_supported": certificate["claim_supported"] == replay["claim_supported"],
        "expected_passed": certificate["expected_passed"] == replay["expected_passed"],
        "metric_bundle": certificate["metric_bundle"] == replay["metric_bundle"],
    }
    return {
        "scenario_id": scenario["id"],
        "path": str(path.relative_to(ROOT)),
        "passed": all(checks.values()),
        "passed_check_count": sum(1 for passed in checks.values() if passed),
        "failed_check_count": sum(1 for passed in checks.values() if not passed),
        "failed_checks": [name for name, passed in checks.items() if not passed],
        **replay,
    }


def _evaluate(scenario: dict, policy: dict) -> dict:
    rank = policy["status_rank"]
    scores = _scores(scenario, policy)
    total = sum(scores.values())
    missing_gates: list[str] = []
    score_candidate = _score_candidate(scenario, policy, scores, total, missing_gates)
    system_role = _system_role(scenario, policy)
    role_cap = policy["system_role_caps"][system_role]
    allowed = _lower_status(score_candidate, role_cap, rank)
    if rank[score_candidate] > rank[role_cap]:
        missing_gates.append(f"system_role:{system_role}->max:{role_cap}")
    target_rank = max(rank[scenario.get("claimed_status", "reference_information")], rank[allowed])
    metrics = _metrics(scenario, policy)
    failure_flags = sorted(set(_failure_flags(scenario, policy, metrics, target_rank)))
    disposition = _disposition(failure_flags, policy)
    if disposition == "withdrawal":
        allowed = "no_external_legal_effect"
    elif disposition in {"downgrade", "suspension"} and rank[allowed] > rank["reference_information"]:
        allowed = "reference_information"
    expected_passed = True
    if scenario.get("expected_allowed_status") is not None:
        expected_passed = expected_passed and allowed == scenario["expected_allowed_status"]
    if scenario.get("expected_disposition") is not None:
        expected_passed = expected_passed and disposition == scenario["expected_disposition"]
    return {
        "policy": _status_policy(policy),
        "claimed_status": scenario.get("claimed_status", "reference_information"),
        "jurisdiction_profile": scenario.get("jurisdiction_profile", "unspecified"),
        "score_vector": scores,
        "total_score": total,
        "score_candidate": score_candidate,
        "system_role": system_role,
        "role_cap": role_cap,
        "missing_gates": missing_gates,
        "failure_flags": failure_flags,
        "disposition": disposition,
        "failure_cap": _failure_cap(failure_flags, disposition),
        "allowed_status": allowed,
        "claim_supported": rank[allowed] >= rank[scenario.get("claimed_status", "reference_information")],
        "expected_passed": expected_passed,
        "metric_bundle": metrics,
    }


def _scores(scenario: dict, policy: dict) -> dict[str, int]:
    scores = {}
    for dimension in policy["dimensions"]:
        raw = scenario["scores"][dimension]
        scores[dimension] = int(raw.get("score", raw) if isinstance(raw, dict) else raw)
    return scores


def _score_candidate(scenario: dict, policy: dict, scores: dict[str, int], total: int, missing_gates: list[str]) -> str:
    dimensions = policy["dimensions"]
    thresholds = policy["thresholds"]
    if (
        all(scores[dimension] >= 1 for dimension in dimensions)
        and total >= thresholds["decision_support_reason"]
        and scores["T"] == 2
        and scores["L"] == 2
        and _adoption_gate_satisfied(scenario, policy)
    ):
        return "decision_support_reason"
    if all(scores[dimension] >= 1 for dimension in dimensions) and total >= thresholds["normative_material_screening_output"]:
        return "normative_material_screening_output"
    if scores["S"] >= 1 and scores["Q"] >= 1 and scores["L"] >= 1:
        missing_gates.extend(_normative_missing_gates(scores, total, policy))
        return "professional_support_output"
    if scores["S"] >= 1 and scores["Q"] >= 1:
        missing_gates.append("L")
        return "reference_information"
    if scores["S"] == 0:
        missing_gates.append("S")
    if scores["Q"] == 0:
        missing_gates.append("Q")
    return "no_external_legal_effect"


def _normative_missing_gates(scores: dict[str, int], total: int, policy: dict) -> list[str]:
    missing = [dimension for dimension in policy["dimensions"] if scores[dimension] < 1]
    threshold = policy["thresholds"]["normative_material_screening_output"]
    if total < threshold:
        missing.append(f"total_score>={threshold}")
    return missing


def _status_policy(policy: dict) -> dict[str, int]:
    thresholds = policy["thresholds"]
    return {
        "normative_threshold": thresholds["normative_material_screening_output"],
        "decision_threshold": thresholds["decision_support_reason"],
    }


def _system_role(scenario: dict, policy: dict) -> str:
    if scenario.get("system_role"):
        return scenario["system_role"]
    gate = scenario.get("review_gate", {})
    inference = policy["role_inference"]
    reliance_gate = gate.get("reliance_gate")
    if gate.get("irreversible_action") is True and gate.get("human_authorization") is not True:
        return inference["irreversible_without_authorization"]
    if reliance_gate == "authorized_adoption":
        return inference["authorized_adoption"]
    if reliance_gate in inference["procedural_reliance_gates"]:
        return inference["procedural_reliance_role"]
    if reliance_gate in inference["professional_reliance_gates"]:
        return inference["professional_reliance_role"]
    return inference["default_role"]


def _adoption_gate_satisfied(scenario: dict, policy: dict) -> bool:
    gate = scenario.get("review_gate", {})
    return (
        gate.get("review_status") == "completed"
        and gate.get("reliance_gate") == "authorized_adoption"
        and gate.get("human_authorization") is True
        and _jurisdiction_assumptions_supported(scenario, policy)
        and gate.get("adoption_reasons_recorded") is True
        and gate.get("contestation_recorded") is True
    )


def _jurisdiction_assumptions_supported(scenario: dict, policy: dict) -> bool:
    assumptions = set(scenario.get("review_gate", {}).get("jurisdiction_assumptions") or [])
    if not assumptions:
        return False
    profile = scenario.get("jurisdiction_profile")
    if not profile:
        return True
    aliases = set(policy["profile_assumption_aliases"].get(profile, [profile]))
    return bool(assumptions & aliases)


def _metrics(scenario: dict, policy: dict) -> dict[str, float | None]:
    authority_sets = scenario.get("authority_sets", {})
    evidence_packet = scenario.get("evidence_packet", {})
    return {
        "counter_authority_recall": _set_recall(authority_sets.get("counter_or_limiting") or scenario.get("counter_authority", {}).get("known"), authority_sets.get("retrieved_counter_or_limiting") or scenario.get("counter_authority", {}).get("retrieved")),
        "authority_coverage": _set_recall(authority_sets.get("high_authority"), authority_sets.get("retrieved_high_authority")),
        "invalid_authority_rate": _invalid_authority_rate(authority_sets),
        "evidence_fidelity": _evidence_fidelity(evidence_packet),
        "evidence_coverage": _evidence_coverage(evidence_packet),
        "source_tag_coverage": _source_tag_coverage(evidence_packet, policy),
        "procedural_source_tag_coverage": _procedural_source_tag_coverage(evidence_packet, policy),
    }


def _set_recall(known_raw, retrieved_raw) -> float | None:
    known = set(known_raw or [])
    if not known:
        return None
    retrieved = set(retrieved_raw or [])
    return len(known & retrieved) / len(known)


def _invalid_authority_rate(authority_sets: dict) -> float | None:
    retrieved = set(authority_sets.get("retrieved", []))
    invalid = set(authority_sets.get("invalid_or_superseded", []))
    retrieved_treatments = set(authority_sets.get("retrieved_invalid_treatments", []))
    invalid_treatments = set(authority_sets.get("invalid_treatments", []))
    denominator = len(retrieved) + len(retrieved_treatments)
    if denominator == 0:
        return None
    return (len(retrieved & invalid) + len(retrieved_treatments & invalid_treatments)) / denominator


def _evidence_fidelity(packet: dict) -> float | None:
    links = packet.get("output_links", [])
    if not links:
        return None
    units = {unit.get("id"): unit for unit in packet.get("output_units", [])}
    faithful = [link for link in links if link.get("supports_claim") is True and link.get("locator") and _link_matches_unit(link, units)]
    return len(faithful) / len(links)


def _link_matches_unit(link: dict, units: dict) -> bool:
    unit_id = link.get("unit_id")
    if not unit_id:
        return True
    unit = units.get(unit_id)
    if not unit:
        return False
    return link.get("source_id") in set(unit.get("source_ids", [])) and link.get("locator") in set(unit.get("locators", []))


def _evidence_coverage(packet: dict) -> float | None:
    units = packet.get("output_units", [])
    if not units:
        return None
    return len([unit for unit in units if unit.get("source_ids") and unit.get("locators")]) / len(units)


def _source_tag_coverage(packet: dict, policy: dict) -> float | None:
    links = packet.get("output_links", [])
    if not links:
        return None
    source_tags = set(policy["source_tags"])
    return len([link for link in links if link.get("source_tag") in source_tags]) / len(links)


def _procedural_source_tag_coverage(packet: dict, policy: dict) -> float | None:
    links = packet.get("output_links", [])
    if not links:
        return None
    procedural_tags = set(policy["procedural_source_tags"])
    return len([link for link in links if link.get("source_tag") in procedural_tags]) / len(links)


def _failure_flags(scenario: dict, policy: dict, metrics: dict, target_rank: int) -> list[str]:
    flags = list(scenario.get("failure_flags", []))
    external_screening_claimed = target_rank >= policy["status_rank"]["normative_material_screening_output"]
    if external_screening_claimed:
        flags.extend(_required_external_evidence_flags(scenario))
    if scenario.get("authority_sets"):
        if metrics["authority_coverage"] is not None and metrics["authority_coverage"] < 1:
            flags.append("authority_omission")
        if metrics["counter_authority_recall"] == 0 or (
            metrics["counter_authority_recall"] is not None and metrics["counter_authority_recall"] < 1 and scenario.get("counter_material_complete") is True
        ):
            flags.append("counter_material_suppression")
        if metrics["invalid_authority_rate"] is not None and metrics["invalid_authority_rate"] > 0:
            flags.append("invalid_authority")
    if scenario.get("evidence_packet"):
        if metrics["evidence_fidelity"] is not None and metrics["evidence_fidelity"] < 1:
            flags.append("summary_distortion")
        if metrics["evidence_coverage"] is not None and metrics["evidence_coverage"] < 1:
            flags.append("summary_distortion")
        if external_screening_claimed and metrics["source_tag_coverage"] is not None and metrics["source_tag_coverage"] < 1:
            flags.append("source_attribution_gap")
        if external_screening_claimed and _has_nonprocedural_source_tags(scenario["evidence_packet"], policy):
            flags.append("source_attribution_gap")
        if external_screening_claimed and _counter_material_below_salience_window(scenario, policy):
            flags.append("ranking_drift")
    flags.extend(_source_binding_validation_flags(scenario, policy, target_rank))
    flags.extend(_review_gate_flags(scenario, policy, target_rank))
    return flags


def _required_external_evidence_flags(scenario: dict) -> list[str]:
    flags: list[str] = []
    authority_sets = scenario.get("authority_sets")
    if not isinstance(authority_sets, dict) or not authority_sets:
        flags.extend(["authority_omission", "counter_material_suppression"])
    else:
        if "high_authority" not in authority_sets or "retrieved_high_authority" not in authority_sets or not authority_sets.get("high_authority"):
            flags.append("authority_omission")
        if "counter_or_limiting" not in authority_sets or "retrieved_counter_or_limiting" not in authority_sets:
            flags.append("counter_material_suppression")
        elif not authority_sets.get("counter_or_limiting") and scenario.get("counter_material_complete") is not True:
            flags.append("counter_material_suppression")
    packet = scenario.get("evidence_packet")
    if not isinstance(packet, dict) or not packet.get("output_units") or not packet.get("output_links"):
        flags.append("source_attribution_gap")
    gate = scenario.get("review_gate")
    if not isinstance(gate, dict) or not gate:
        flags.append("contestation_failure")
    return flags


def _source_binding_validation_flags(scenario: dict, policy: dict, target_rank: int) -> list[str]:
    if target_rank < policy["status_rank"]["normative_material_screening_output"]:
        return []
    validation = scenario.get("source_binding_validation")
    if not isinstance(validation, dict):
        return []
    flags: list[str] = []
    if validation.get("all_links_source_bound") is False:
        flags.append("source_attribution_gap")
    if validation.get("high_authority_complete") is False:
        flags.append("authority_omission")
    if validation.get("counter_material_complete") is False:
        flags.append("counter_material_suppression")
    material_support_failures = {"contradiction_pattern_matched", "support_terms_not_shared_by_claim_and_excerpt", "missing_claim"}
    if any(item.get("reason") in material_support_failures for item in validation.get("unsupported_source_support", [])):
        flags.append("summary_distortion")
    return flags


def _review_gate_flags(scenario: dict, policy: dict, target_rank: int) -> list[str]:
    gate = scenario.get("review_gate", {})
    if not gate:
        return []
    flags: list[str] = []
    if gate.get("irreversible_action") is True and gate.get("human_authorization") is not True:
        flags.append("unauthorized_action")
    if target_rank >= policy["status_rank"]["normative_material_screening_output"] and not _jurisdiction_assumptions_supported(scenario, policy):
        flags.append("jurisdiction_assumption_gap")
    review_required = gate.get("attorney_review_required") is True
    review_incomplete = gate.get("review_status") not in {"completed", "not_required"}
    protected_reliance = gate.get("reliance_gate") in {
        "attorney_review",
        "external_reliance",
        "filing",
        "sending",
        "execution",
        "authorized_adoption",
    }
    if review_required and review_incomplete and (protected_reliance or target_rank >= policy["status_rank"]["decision_support_reason"]):
        flags.append("review_gate_failure")
    return flags


def _counter_material_below_salience_window(scenario: dict, policy: dict) -> bool:
    authority_sets = scenario.get("authority_sets", {})
    counter = set(authority_sets.get("counter_or_limiting") or [])
    retrieved_counter = set(authority_sets.get("retrieved_counter_or_limiting") or [])
    if not counter or not retrieved_counter:
        return False
    units = _ranked_units(scenario.get("evidence_packet", {}).get("output_units") or [])
    if len(units) < policy["rank_salience_window"]:
        return False
    visible = set()
    for unit in units[: policy["rank_salience_window"]]:
        visible.update(unit.get("source_ids") or [])
    return not bool(visible & counter)


def _ranked_units(units: list[dict]) -> list[dict]:
    if any("output_rank" in unit for unit in units):
        return sorted(units, key=lambda unit: unit.get("output_rank", len(units) + 1))
    return units


def _has_nonprocedural_source_tags(packet: dict, policy: dict) -> bool:
    procedural_tags = set(policy["procedural_source_tags"])
    return any(link.get("source_tag") not in procedural_tags for link in packet.get("output_links", []))


def _disposition(flags: list[str], policy: dict) -> str:
    disposition = "none"
    for flag in flags:
        candidate = policy["flag_dispositions"].get(flag, "warning")
        if policy["disposition_rank"][candidate] > policy["disposition_rank"][disposition]:
            disposition = candidate
    return disposition


def _failure_cap(failure_flags: list[str], disposition: str) -> str | None:
    if disposition == "withdrawal":
        return "no_external_legal_effect"
    if failure_flags and disposition in {"suspension", "downgrade"}:
        return "reference_information"
    return None


def _lower_status(left: str, right: str, rank: dict[str, int]) -> str:
    return left if rank[left] <= rank[right] else right


def _scenario_hash(scenario: dict) -> str:
    return hashlib.sha256(json.dumps(scenario, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _distribution(rows: list[dict], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = row[key]
        counts[value] = counts.get(value, 0) + 1
    return counts


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _format_report(payload: dict) -> str:
    lines = [
        "# Policy-Constants Replay",
        "",
        f"Scenarios: {payload['verified_scenario_count']}/{payload['scenario_count']} verified",
        f"Replay checks: {payload['passed_check_count']}/{payload['check_count']} passed",
        f"Cap or failure transitions: {payload['cap_or_failure_transition_count']}",
        f"Policy file: `{payload['policy_path']}`",
        f"Certificate file: `{payload['certificate_path']}`",
    ]
    if payload["failures"]:
        lines.extend(["", "## Failures", ""])
        for failure in payload["failures"]:
            lines.append(f"- {failure['scenario_id']}: {', '.join(failure['failed_checks'])}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
