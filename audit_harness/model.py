from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


DIMENSIONS = ("S", "Q", "H", "K", "T", "L")


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
    disposition: str
    expected_allowed_status: str | None
    expected_disposition: str | None
    expected_passed: bool


def evaluate_scenario(scenario: dict[str, Any]) -> AuditResult:
    scores = _parse_scores(scenario.get("scores", {}))
    total = sum(scores.values())
    missing_gates: list[str] = []
    allowed = _allowed_status(scores, total, missing_gates)
    metrics = _scenario_metrics(scenario)
    disposition = _disposition(_derived_failure_flags(scenario, metrics))

    if disposition == "withdrawal":
        allowed = Status.NO_EXTERNAL_LEGAL_EFFECT.value
    elif disposition in {"suspension", "downgrade"} and STATUS_RANK[allowed] > STATUS_RANK[Status.REFERENCE_INFORMATION.value]:
        allowed = Status.REFERENCE_INFORMATION.value

    claimed = scenario.get("claimed_status", Status.REFERENCE_INFORMATION.value)
    if claimed not in STATUS_RANK:
        raise ValueError(f"Unknown claimed_status: {claimed}")

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
        disposition=disposition,
        expected_allowed_status=expected_allowed,
        expected_disposition=expected_disposition,
        expected_passed=expected_passed,
    )


def _parse_scores(raw_scores: dict[str, Any]) -> dict[str, int]:
    scores: dict[str, int] = {}
    for dimension in DIMENSIONS:
        raw = raw_scores.get(dimension, 0)
        score = raw.get("score", raw) if isinstance(raw, dict) else raw
        if score not in (0, 1, 2):
            raise ValueError(f"{dimension} score must be 0, 1 or 2; got {score!r}")
        scores[dimension] = int(score)
    return scores


def _allowed_status(scores: dict[str, int], total: int, missing_gates: list[str]) -> str:
    if scores["S"] >= 1 and scores["Q"] >= 1 and scores["H"] >= 1 and scores["K"] >= 1 and scores["T"] == 2 and scores["L"] == 2:
        return Status.DECISION_SUPPORT_REASON.value

    if all(scores[d] >= 1 for d in DIMENSIONS) and total >= 9:
        return Status.NORMATIVE_MATERIAL_SCREENING_OUTPUT.value

    if scores["S"] >= 1 and scores["Q"] >= 1 and scores["L"] >= 1:
        missing_gates.extend(_normative_missing_gates(scores, total))
        return Status.PROFESSIONAL_SUPPORT_OUTPUT.value

    if scores["S"] >= 1 and scores["Q"] >= 1:
        missing_gates.extend(["L"])
        return Status.REFERENCE_INFORMATION.value

    if scores["S"] == 0:
        missing_gates.append("S")
    if scores["Q"] == 0:
        missing_gates.append("Q")
    return Status.NO_EXTERNAL_LEGAL_EFFECT.value


def _normative_missing_gates(scores: dict[str, int], total: int) -> list[str]:
    missing = [dimension for dimension in DIMENSIONS if scores[dimension] < 1]
    if total < 9:
        missing.append("total_score>=9")
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
    if not retrieved:
        return None
    return len(retrieved & invalid) / len(retrieved)


def _evidence_fidelity(evidence_packet: dict[str, Any]) -> float | None:
    links = evidence_packet.get("output_links", [])
    if not links:
        return None
    faithful = [link for link in links if link.get("supports_claim") is True and link.get("locator")]
    return len(faithful) / len(links)


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
    tagged = [link for link in links if link.get("source_tag")]
    return len(tagged) / len(links)


def _derived_failure_flags(scenario: dict[str, Any], metrics: dict[str, float | None]) -> list[str]:
    flags = list(scenario.get("failure_flags", []))
    claimed_rank = STATUS_RANK.get(scenario.get("claimed_status", Status.REFERENCE_INFORMATION.value), 1)
    if scenario.get("authority_sets"):
        if metrics["authority_coverage"] == 0:
            flags.append("authority_omission")
        if metrics["counter_authority_recall"] == 0:
            flags.append("counter_material_suppression")
        if metrics["invalid_authority_rate"] is not None and metrics["invalid_authority_rate"] > 0:
            flags.append("invalid_authority")
    if scenario.get("evidence_packet"):
        if metrics["evidence_fidelity"] is not None and metrics["evidence_fidelity"] < 1:
            flags.append("summary_distortion")
        if metrics["evidence_coverage"] is not None and metrics["evidence_coverage"] < 1:
            flags.append("summary_distortion")
        if claimed_rank >= STATUS_RANK[Status.NORMATIVE_MATERIAL_SCREENING_OUTPUT.value] and metrics["source_tag_coverage"] is not None and metrics["source_tag_coverage"] < 1:
            flags.append("source_attribution_gap")
    flags.extend(_review_gate_flags(scenario, claimed_rank))
    return flags


def _review_gate_flags(scenario: dict[str, Any], claimed_rank: int) -> list[str]:
    gate = scenario.get("review_gate", {})
    if not gate:
        return []
    flags: list[str] = []
    if gate.get("irreversible_action") is True and gate.get("human_authorization") is not True:
        flags.append("unauthorized_action")
    if claimed_rank >= STATUS_RANK[Status.NORMATIVE_MATERIAL_SCREENING_OUTPUT.value] and not gate.get("jurisdiction_assumptions"):
        flags.append("jurisdiction_assumption_gap")
    review_required = gate.get("attorney_review_required") is True
    review_incomplete = gate.get("review_status") not in {"completed", "not_required"}
    protected_reliance = gate.get("reliance_gate") in {"external_reliance", "filing", "sending", "execution", "authorized_adoption"}
    if review_required and review_incomplete and (protected_reliance or claimed_rank >= STATUS_RANK[Status.DECISION_SUPPORT_REASON.value]):
        flags.append("review_gate_failure")
    return flags


def _disposition(flags: list[str]) -> str:
    disposition = "none"
    for flag in flags:
        candidate = FLAG_DISPOSITIONS.get(flag, "warning")
        if DISPOSITION_RANK[candidate] > DISPOSITION_RANK[disposition]:
            disposition = candidate
    return disposition
