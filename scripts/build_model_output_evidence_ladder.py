from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from audit_harness.model import RANK_SALIENCE_WINDOW
from build_model_output_repairs import repair

SOURCE = ROOT / "experiments" / "ai_outputs" / "scenarios"
OUT = ROOT / "experiments" / "model_output_evidence_ladder" / "scenarios"
RESULTS = ROOT / "experiments" / "model_output_evidence_ladder" / "results"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.json"):
        old.unlink()
    count = 0
    for path in sorted(SOURCE.glob("codex55_*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        for scenario in ladder(raw):
            (OUT / f"{scenario['id']}.json").write_text(
                json.dumps(scenario, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            count += 1
    print(f"Wrote {count} model-output evidence-ladder scenarios")
    return 0


def ladder(raw: dict) -> list[dict]:
    return [
        raw_unverified(raw),
        source_bound_no_counter(raw),
        source_bound_no_contestability(raw),
        source_bound_no_logging(raw),
        contestable_screening(raw),
        authorized_decision_support(raw),
        unauthorized_external_action(raw),
    ]


def raw_unverified(raw: dict) -> dict:
    scenario = deepcopy(raw)
    disposition = "suspension" if counter_material_below_salience_window(raw) else "downgrade"
    return with_step(
        scenario,
        raw,
        "raw-unverified",
        "Unverified model output keeps nonprocedural source tags and pending review.",
        "reference_information",
        disposition,
    )


def source_bound_no_counter(raw: dict) -> dict:
    scenario = repair(raw)
    authority_sets = scenario["authority_sets"]
    omitted = authority_sets["counter_or_limiting"][0]
    authority_sets["retrieved_counter_or_limiting"] = [
        item for item in authority_sets["retrieved_counter_or_limiting"] if item != omitted
    ]
    authority_sets["retrieved"] = [item for item in authority_sets["retrieved"] if item != omitted]
    scenario["counter_material_complete"] = True
    validation = scenario.get("source_binding_validation", {})
    validation["counter_material_complete"] = False
    validation["all_links_source_bound"] = False
    scenario["source_binding_validation"] = validation
    return with_step(
        scenario,
        raw,
        "source-bound-no-counter",
        "Source links validate, but one issue-defined counter or limiting authority is omitted.",
        "reference_information",
        "suspension",
    )


def source_bound_no_contestability(raw: dict) -> dict:
    scenario = repair(raw)
    scenario["scores"]["T"]["score"] = 0
    scenario["scores"]["T"]["evidence"] = "The evidence is source-bound, but affected parties cannot inspect or contest the output."
    scenario.get("review_gate", {}).pop("contestability_channel", None)
    return with_step(
        scenario,
        raw,
        "source-bound-no-contestability",
        "Source-bound output lacks a contestation channel.",
        "reference_information",
        "downgrade",
    )


def source_bound_no_logging(raw: dict) -> dict:
    scenario = repair(raw)
    scenario["scores"]["L"]["score"] = 0
    scenario["scores"]["L"]["evidence"] = "The evidence is source-bound, but no audit or adoption log is preserved."
    return with_step(
        scenario,
        raw,
        "source-bound-no-logging",
        "Source-bound output lacks audit logging.",
        "reference_information",
        "none",
    )


def contestable_screening(raw: dict) -> dict:
    scenario = repair(raw)
    return with_step(
        scenario,
        raw,
        "contestable-screening",
        "Source-bound, contestable and logged output qualifies as normative material screening.",
        "normative_material_screening_output",
        "none",
    )


def authorized_decision_support(raw: dict) -> dict:
    scenario = repair(raw)
    scenario["claimed_status"] = "decision_support_reason"
    scenario["system_role"] = "authorized_decision_support_tool"
    scenario["scores"]["T"]["score"] = 2
    scenario["scores"]["L"]["score"] = 2
    scenario["review_gate"] = {
        "attorney_review_required": True,
        "review_status": "completed",
        "reliance_gate": "authorized_adoption",
        "jurisdiction_assumptions": raw.get("review_gate", {}).get("jurisdiction_assumptions", []),
        "contestability_channel": "authorized-adoption-review-record",
        "irreversible_action": False,
        "human_authorization": True,
        "adoption_reasons_recorded": True,
        "contestation_recorded": True,
    }
    return with_step(
        scenario,
        raw,
        "authorized-decision-support",
        "The same source-bound output is adopted through a complete human authorization and contestation gate.",
        "decision_support_reason",
        "none",
    )


def unauthorized_external_action(raw: dict) -> dict:
    scenario = repair(raw)
    scenario["claimed_status"] = "decision_support_reason"
    scenario["system_role"] = "unaccountable_external_disposition"
    scenario["scores"]["T"]["score"] = 2
    scenario["scores"]["L"]["score"] = 2
    scenario["review_gate"] = {
        "attorney_review_required": True,
        "review_status": "completed",
        "reliance_gate": "authorized_adoption",
        "jurisdiction_assumptions": raw.get("review_gate", {}).get("jurisdiction_assumptions", []),
        "contestability_channel": "unauthorized-action-review-record",
        "irreversible_action": True,
        "human_authorization": False,
        "adoption_reasons_recorded": True,
        "contestation_recorded": True,
    }
    return with_step(
        scenario,
        raw,
        "unauthorized-external-action",
        "The same source-bound output is coupled to irreversible external action without human authorization.",
        "no_external_legal_effect",
        "withdrawal",
    )


def with_step(scenario: dict, raw: dict, step: str, purpose: str, expected_status: str, expected_disposition: str) -> dict:
    scenario["id"] = f"evidence-ladder-{raw['id']}--{step}"
    scenario["evidence_ladder_step"] = {
        "source_model_output": raw["id"],
        "step": step,
        "purpose": purpose,
    }
    scenario["expected_allowed_status"] = expected_status
    scenario["expected_disposition"] = expected_disposition
    return scenario


def counter_material_below_salience_window(scenario: dict) -> bool:
    authority_sets = scenario.get("authority_sets", {})
    counter = set(authority_sets.get("counter_or_limiting") or [])
    retrieved = set(authority_sets.get("retrieved_counter_or_limiting") or [])
    units = scenario.get("evidence_packet", {}).get("output_units", [])
    if not counter or not retrieved or len(units) < RANK_SALIENCE_WINDOW:
        return False
    visible = set()
    for unit in units[:RANK_SALIENCE_WINDOW]:
        visible.update(unit.get("source_ids") or [])
    return not bool(visible & counter)


if __name__ == "__main__":
    raise SystemExit(main())
