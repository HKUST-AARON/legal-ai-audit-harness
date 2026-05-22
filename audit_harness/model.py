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
    disposition: str
    expected_allowed_status: str | None
    expected_disposition: str | None
    expected_passed: bool


def evaluate_scenario(scenario: dict[str, Any]) -> AuditResult:
    scores = _parse_scores(scenario.get("scores", {}))
    total = sum(scores.values())
    missing_gates: list[str] = []
    allowed = _allowed_status(scores, total, missing_gates)
    disposition = _disposition(scenario.get("failure_flags", []))

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
        counter_authority_recall=_counter_authority_recall(scenario.get("counter_authority")),
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


def _counter_authority_recall(raw: Any) -> float | None:
    if not raw:
        return None
    known = set(raw.get("known", []))
    if not known:
        return None
    retrieved = set(raw.get("retrieved", []))
    return len(retrieved & known) / len(known)


def _disposition(flags: list[str]) -> str:
    disposition = "none"
    for flag in flags:
        candidate = FLAG_DISPOSITIONS.get(flag, "warning")
        if DISPOSITION_RANK[candidate] > DISPOSITION_RANK[disposition]:
            disposition = candidate
    return disposition
