from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


DIMENSIONS = ("S", "Q", "H", "K", "T", "L")
RANK_SALIENCE_WINDOW = 3
SOURCE_TAGS = {
    "tool_verified",
    "official_source",
    "public_metadata",
    "user_provided",
    "user_provided_verified",
    "settled",
    "needs_verification",
    "pinpoint_needs_verification",
    "web_search_verify",
}
PROCEDURAL_SOURCE_TAGS = {"tool_verified", "official_source", "user_provided_verified", "settled"}
PROFILE_ASSUMPTION_ALIASES = {
    "common_law": {
        "common_law",
        "canadian_administrative_law",
        "england_and_wales_tort_law",
        "united_states_federal_administrative_law",
    },
    "civil_law": {
        "civil_law",
        "european_union_data_protection_law",
        "european_union_fundamental_rights",
        "german_constitutional_law",
    },
    "administrative": {
        "administrative",
        "canadian_administrative_law",
        "united_states_federal_administrative_law",
    },
    "arbitral": {"arbitral"},
    "odr": {"odr"},
}


class Status(str, Enum):
    NO_EXTERNAL_LEGAL_EFFECT = "no_external_legal_effect"
    REFERENCE_INFORMATION = "reference_information"
    PROFESSIONAL_SUPPORT_OUTPUT = "professional_support_output"
    NORMATIVE_MATERIAL_SCREENING_OUTPUT = "normative_material_screening_output"
    DECISION_SUPPORT_REASON = "decision_support_reason"


STATUS_RANK = {
    Status.NO_EXTERNAL_LEGAL_EFFECT.value: 0,
    Status.REFERENCE_INFORMATION.value: 1,
    Status.PROFESSIONAL_SUPPORT_OUTPUT.value: 2,
    Status.NORMATIVE_MATERIAL_SCREENING_OUTPUT.value: 3,
    Status.DECISION_SUPPORT_REASON.value: 4,
}

SYSTEM_ROLE_CAPS = {
    "back_office_tool": Status.REFERENCE_INFORMATION.value,
    "disclosed_assistance_tool": Status.PROFESSIONAL_SUPPORT_OUTPUT.value,
    "auditable_procedural_tool": Status.NORMATIVE_MATERIAL_SCREENING_OUTPUT.value,
    "authorized_decision_support_tool": Status.DECISION_SUPPORT_REASON.value,
    "unaccountable_external_disposition": Status.NO_EXTERNAL_LEGAL_EFFECT.value,
}

FLAG_DISPOSITIONS = {
    "authority_omission": "suspension",
    "counter_material_suppression": "suspension",
    "invalid_authority": "suspension",
    "ranking_drift": "suspension",
    "source_attribution_gap": "downgrade",
    "jurisdiction_assumption_gap": "downgrade",
    "review_gate_failure": "downgrade",
    "unauthorized_action": "withdrawal",
    "summary_distortion": "withdrawal",
    "automation_dependence": "downgrade",
    "contestation_failure": "downgrade",
}

DISPOSITION_RANK = {
    "none": 0,
    "warning": 1,
    "downgrade": 2,
    "suspension": 3,
    "withdrawal": 4,
}


@dataclass(frozen=True)
class AuditResult:
    scenario_id: str
    claimed_status: str
    system_role: str
    allowed_status: str
    total_score: int
    scores: dict[str, int]
    missing_gates: list[str]
    claim_supported: bool
    counter_authority_recall: float | None
    authority_coverage: float | None
    invalid_authority_rate: float | None
    evidence_fidelity: float | None
    evidence_coverage: float | None
    source_tag_coverage: float | None
    procedural_source_tag_coverage: float | None
    failure_flags: list[str]
    disposition: str
    expected_allowed_status: str | None
    expected_disposition: str | None
    expected_passed: bool


@dataclass(frozen=True)
class StatusPolicy:
    normative_threshold: int = 9
    decision_threshold: int = 10


def evaluate_scenario(scenario: dict[str, Any], policy: StatusPolicy | None = None) -> AuditResult:
    policy = policy or StatusPolicy()
    _validate_scenario(scenario)
    scores = _parse_scores(scenario.get("scores", {}))
    total = sum(scores.values())
    missing_gates: list[str] = []
    system_role = _system_role(scenario)
    allowed = _allowed_status(scenario, scores, total, missing_gates, policy)
    allowed = _cap_by_system_role(allowed, system_role, missing_gates)
    metrics = _scenario_metrics(scenario)
    claimed = scenario.get("claimed_status", Status.REFERENCE_INFORMATION.value)
    if claimed not in STATUS_RANK:
        raise ValueError(f"Unknown claimed_status: {claimed}")
    target_rank = max(STATUS_RANK[claimed], STATUS_RANK[allowed])
    failure_flags = _derived_failure_flags(scenario, metrics, target_rank)
    disposition = _disposition(failure_flags)

    if disposition == "withdrawal":
        allowed = Status.NO_EXTERNAL_LEGAL_EFFECT.value
    elif disposition in {"suspension", "downgrade"} and STATUS_RANK[allowed] > STATUS_RANK[Status.REFERENCE_INFORMATION.value]:
        allowed = Status.REFERENCE_INFORMATION.value

    expected_allowed = scenario.get("expected_allowed_status")
    expected_disposition = scenario.get("expected_disposition")
    expected_passed = True
    if expected_allowed is not None:
        expected_passed = expected_passed and allowed == expected_allowed
    if expected_disposition is not None:
        expected_passed = expected_passed and disposition == expected_disposition

    return AuditResult(
        scenario_id=scenario.get("id", "unnamed-scenario"),
        claimed_status=claimed,
        system_role=system_role,
        allowed_status=allowed,
        total_score=total,
        scores=scores,
        missing_gates=missing_gates,
        claim_supported=STATUS_RANK[allowed] >= STATUS_RANK[claimed],
        counter_authority_recall=metrics["counter_authority_recall"],
        authority_coverage=metrics["authority_coverage"],
        invalid_authority_rate=metrics["invalid_authority_rate"],
        evidence_fidelity=metrics["evidence_fidelity"],
        evidence_coverage=metrics["evidence_coverage"],
        source_tag_coverage=metrics["source_tag_coverage"],
        procedural_source_tag_coverage=metrics["procedural_source_tag_coverage"],
        failure_flags=sorted(set(failure_flags)),
        disposition=disposition,
        expected_allowed_status=expected_allowed,
        expected_disposition=expected_disposition,
        expected_passed=expected_passed,
    )


def _validate_scenario(scenario: dict[str, Any]) -> None:
    if not isinstance(scenario.get("id"), str) or not scenario["id"]:
        raise ValueError("Scenario must include a non-empty string id")
    if scenario.get("claimed_status") not in STATUS_RANK:
        raise ValueError(f"Unknown claimed_status: {scenario.get('claimed_status')}")
    scores = scenario.get("scores")
    if not isinstance(scores, dict) or any(dimension not in scores for dimension in DIMENSIONS):
        raise ValueError(f"Scenario scores must include {', '.join(DIMENSIONS)}")
    unknown_flags = set(scenario.get("failure_flags", [])) - set(FLAG_DISPOSITIONS)
    if unknown_flags:
        raise ValueError(f"Unknown failure_flags: {', '.join(sorted(unknown_flags))}")
    role = scenario.get("system_role")
    if role is not None and role not in SYSTEM_ROLE_CAPS:
        raise ValueError(f"Unknown system_role: {role}")


def _parse_scores(raw_scores: dict[str, Any]) -> dict[str, int]:
    scores: dict[str, int] = {}
    for dimension in DIMENSIONS:
        raw = raw_scores.get(dimension, 0)
        score = raw.get("score", raw) if isinstance(raw, dict) else raw
        if score not in (0, 1, 2):
            raise ValueError(f"{dimension} score must be 0, 1 or 2; got {score!r}")
        scores[dimension] = int(score)
    return scores


def _allowed_status(scenario: dict[str, Any], scores: dict[str, int], total: int, missing_gates: list[str], policy: StatusPolicy) -> str:
    if (
        all(scores[d] >= 1 for d in DIMENSIONS)
        and total >= policy.decision_threshold
        and scores["T"] == 2
        and scores["L"] == 2
        and _adoption_gate_satisfied(scenario)
    ):
        return Status.DECISION_SUPPORT_REASON.value

    if all(scores[d] >= 1 for d in DIMENSIONS) and total >= policy.normative_threshold:
        return Status.NORMATIVE_MATERIAL_SCREENING_OUTPUT.value

    if scores["S"] >= 1 and scores["Q"] >= 1 and scores["L"] >= 1:
        missing_gates.extend(_normative_missing_gates(scores, total, policy))
        return Status.PROFESSIONAL_SUPPORT_OUTPUT.value

    if scores["S"] >= 1 and scores["Q"] >= 1:
        missing_gates.extend(["L"])
        return Status.REFERENCE_INFORMATION.value

    if scores["S"] == 0:
        missing_gates.append("S")
    if scores["Q"] == 0:
        missing_gates.append("Q")
    return Status.NO_EXTERNAL_LEGAL_EFFECT.value


def _system_role(scenario: dict[str, Any]) -> str:
    explicit = scenario.get("system_role")
    if explicit:
        return explicit
    gate = scenario.get("review_gate", {})
    reliance_gate = gate.get("reliance_gate")
    if gate.get("irreversible_action") is True and gate.get("human_authorization") is not True:
        return "unaccountable_external_disposition"
    if reliance_gate == "authorized_adoption":
        return "authorized_decision_support_tool"
    if reliance_gate in {"attorney_review", "external_reliance", "filing", "sending", "execution"}:
        return "auditable_procedural_tool"
    if reliance_gate in {"internal_research", "not_for_merits_reliance"}:
        return "disclosed_assistance_tool"
    return "back_office_tool"


def _cap_by_system_role(allowed: str, system_role: str, missing_gates: list[str]) -> str:
    cap = SYSTEM_ROLE_CAPS[system_role]
    if STATUS_RANK[allowed] <= STATUS_RANK[cap]:
        return allowed
    missing_gates.append(f"system_role:{system_role}->max:{cap}")
    return cap


def _adoption_gate_satisfied(scenario: dict[str, Any]) -> bool:
    gate = scenario.get("review_gate", {})
    return (
        gate.get("review_status") == "completed"
        and gate.get("reliance_gate") == "authorized_adoption"
        and gate.get("human_authorization") is True
        and _jurisdiction_assumptions_supported(scenario)
        and gate.get("adoption_reasons_recorded") is True
        and gate.get("contestation_recorded") is True
    )


def _jurisdiction_assumptions_supported(scenario: dict[str, Any]) -> bool:
    assumptions = set(scenario.get("review_gate", {}).get("jurisdiction_assumptions") or [])
    if not assumptions:
        return False
    profile = scenario.get("jurisdiction_profile")
    if not profile:
        return True
    aliases = PROFILE_ASSUMPTION_ALIASES.get(profile, {profile})
    return bool(assumptions & aliases)


def _normative_missing_gates(scores: dict[str, int], total: int, policy: StatusPolicy) -> list[str]:
    missing = [dimension for dimension in DIMENSIONS if scores[dimension] < 1]
    if total < policy.normative_threshold:
        missing.append(f"total_score>={policy.normative_threshold}")
    return missing


def _scenario_metrics(scenario: dict[str, Any]) -> dict[str, float | None]:
    authority_sets = scenario.get("authority_sets", {})
    evidence_packet = scenario.get("evidence_packet", {})
    return {
        "counter_authority_recall": _set_recall(authority_sets.get("counter_or_limiting") or scenario.get("counter_authority", {}).get("known"), authority_sets.get("retrieved_counter_or_limiting") or scenario.get("counter_authority", {}).get("retrieved")),
        "authority_coverage": _set_recall(authority_sets.get("high_authority"), authority_sets.get("retrieved_high_authority")),
        "invalid_authority_rate": _invalid_authority_rate(authority_sets),
        "evidence_fidelity": _evidence_fidelity(evidence_packet),
        "evidence_coverage": _evidence_coverage(evidence_packet),
        "source_tag_coverage": _source_tag_coverage(evidence_packet),
        "procedural_source_tag_coverage": _procedural_source_tag_coverage(evidence_packet),
    }


def _set_recall(known_raw: Any, retrieved_raw: Any) -> float | None:
    known = set(known_raw or [])
    if not known:
        return None
    retrieved = set(retrieved_raw or [])
    return len(retrieved & known) / len(known)


def _invalid_authority_rate(authority_sets: dict[str, Any]) -> float | None:
    retrieved = set(authority_sets.get("retrieved", []))
    invalid = set(authority_sets.get("invalid_or_superseded", []))
    retrieved_treatments = set(authority_sets.get("retrieved_invalid_treatments", []))
    invalid_treatments = set(authority_sets.get("invalid_treatments", []))
    denominator = len(retrieved) + len(retrieved_treatments)
    if denominator == 0:
        return None
    invalid_hits = len(retrieved & invalid) + len(retrieved_treatments & invalid_treatments)
    return invalid_hits / denominator


def _evidence_fidelity(evidence_packet: dict[str, Any]) -> float | None:
    links = evidence_packet.get("output_links", [])
    if not links:
        return None
    units = {unit.get("id"): unit for unit in evidence_packet.get("output_units", [])}
    faithful = [
        link
        for link in links
        if link.get("supports_claim") is True
        and link.get("locator")
        and _link_matches_unit(link, units)
    ]
    return len(faithful) / len(links)


def _link_matches_unit(link: dict[str, Any], units: dict[str, dict[str, Any]]) -> bool:
    unit_id = link.get("unit_id")
    if not unit_id:
        return True
    unit = units.get(unit_id)
    if not unit:
        return False
    return link.get("source_id") in set(unit.get("source_ids", [])) and link.get("locator") in set(unit.get("locators", []))


def _evidence_coverage(evidence_packet: dict[str, Any]) -> float | None:
    output_units = evidence_packet.get("output_units", [])
    if not output_units:
        return None
    covered = [unit for unit in output_units if unit.get("source_ids") and unit.get("locators")]
    return len(covered) / len(output_units)


def _source_tag_coverage(evidence_packet: dict[str, Any]) -> float | None:
    links = evidence_packet.get("output_links", [])
    if not links:
        return None
    tagged = [link for link in links if link.get("source_tag") in SOURCE_TAGS]
    return len(tagged) / len(links)


def _procedural_source_tag_coverage(evidence_packet: dict[str, Any]) -> float | None:
    links = evidence_packet.get("output_links", [])
    if not links:
        return None
    tagged = [link for link in links if link.get("source_tag") in PROCEDURAL_SOURCE_TAGS]
    return len(tagged) / len(links)


def _derived_failure_flags(scenario: dict[str, Any], metrics: dict[str, float | None], target_rank: int) -> list[str]:
    flags = list(scenario.get("failure_flags", []))
    external_screening_claimed = target_rank >= STATUS_RANK[Status.NORMATIVE_MATERIAL_SCREENING_OUTPUT.value]
    if external_screening_claimed:
        flags.extend(_required_external_evidence_flags(scenario))
    if scenario.get("authority_sets"):
        if metrics["authority_coverage"] is not None and metrics["authority_coverage"] < 1:
            flags.append("authority_omission")
        if metrics["counter_authority_recall"] == 0 or (
            metrics["counter_authority_recall"] is not None
            and metrics["counter_authority_recall"] < 1
            and scenario.get("counter_material_complete") is True
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
        if external_screening_claimed and _has_nonprocedural_source_tags(scenario["evidence_packet"]):
            flags.append("source_attribution_gap")
        if external_screening_claimed and _counter_material_below_salience_window(scenario):
            flags.append("ranking_drift")
    flags.extend(_source_binding_validation_flags(scenario, target_rank))
    flags.extend(_review_gate_flags(scenario, target_rank))
    return flags


def _counter_material_below_salience_window(scenario: dict[str, Any]) -> bool:
    authority_sets = scenario.get("authority_sets", {})
    counter_material = set(authority_sets.get("counter_or_limiting") or [])
    retrieved_counter_material = set(authority_sets.get("retrieved_counter_or_limiting") or [])
    if not counter_material or not retrieved_counter_material:
        return False
    units = _ranked_output_units(scenario.get("evidence_packet", {}).get("output_units") or [])
    if len(units) < RANK_SALIENCE_WINDOW:
        return False
    visible_sources: set[str] = set()
    for unit in units[:RANK_SALIENCE_WINDOW]:
        visible_sources.update(unit.get("source_ids") or [])
    return not bool(visible_sources & counter_material)


def _ranked_output_units(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if any("output_rank" in unit for unit in units):
        return sorted(units, key=lambda unit: unit.get("output_rank", len(units) + 1))
    return units


def _required_external_evidence_flags(scenario: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    authority_sets = scenario.get("authority_sets")
    if not isinstance(authority_sets, dict) or not authority_sets:
        flags.append("authority_omission")
        flags.append("counter_material_suppression")
    else:
        if "high_authority" not in authority_sets or "retrieved_high_authority" not in authority_sets:
            flags.append("authority_omission")
        elif not authority_sets.get("high_authority"):
            flags.append("authority_omission")
        if "counter_or_limiting" not in authority_sets or "retrieved_counter_or_limiting" not in authority_sets:
            flags.append("counter_material_suppression")
        elif not authority_sets.get("counter_or_limiting") and scenario.get("counter_material_complete") is not True:
            flags.append("counter_material_suppression")

    evidence_packet = scenario.get("evidence_packet")
    if not isinstance(evidence_packet, dict) or not evidence_packet.get("output_units") or not evidence_packet.get("output_links"):
        flags.append("source_attribution_gap")

    gate = scenario.get("review_gate")
    if not isinstance(gate, dict) or not gate:
        flags.append("contestation_failure")
    return flags


def _source_binding_validation_flags(scenario: dict[str, Any], target_rank: int) -> list[str]:
    if target_rank < STATUS_RANK[Status.NORMATIVE_MATERIAL_SCREENING_OUTPUT.value]:
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
    material_support_failures = {
        "contradiction_pattern_matched",
        "support_terms_not_shared_by_claim_and_excerpt",
        "missing_claim",
    }
    if any(item.get("reason") in material_support_failures for item in validation.get("unsupported_source_support", [])):
        flags.append("summary_distortion")
    return flags


def _review_gate_flags(scenario: dict[str, Any], target_rank: int) -> list[str]:
    gate = scenario.get("review_gate", {})
    if not gate:
        return []
    flags: list[str] = []
    if gate.get("irreversible_action") is True and gate.get("human_authorization") is not True:
        flags.append("unauthorized_action")
    if target_rank >= STATUS_RANK[Status.NORMATIVE_MATERIAL_SCREENING_OUTPUT.value] and not _jurisdiction_assumptions_supported(scenario):
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
    if review_required and review_incomplete and (protected_reliance or target_rank >= STATUS_RANK[Status.DECISION_SUPPORT_REASON.value]):
        flags.append("review_gate_failure")
    return flags


def _has_nonprocedural_source_tags(evidence_packet: dict[str, Any]) -> bool:
    links = evidence_packet.get("output_links", [])
    return any(link.get("source_tag") not in PROCEDURAL_SOURCE_TAGS for link in links)


def _disposition(flags: list[str]) -> str:
    disposition = "none"
    for flag in flags:
        candidate = FLAG_DISPOSITIONS.get(flag, "warning")
        if DISPOSITION_RANK[candidate] > DISPOSITION_RANK[disposition]:
            disposition = candidate
    return disposition
