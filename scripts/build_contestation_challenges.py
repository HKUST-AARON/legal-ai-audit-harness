from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_harness.model import STATUS_RANK, evaluate_scenario
from run_full_validation import SUITES

OUT = ROOT / "experiments" / "contestation_challenges" / "scenarios"
RESULTS = ROOT / "experiments" / "contestation_challenges" / "results"
NORMATIVE = STATUS_RANK["normative_material_screening_output"]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.json"):
        old.unlink()
    count = 0
    for path in _scenario_paths():
        scenario = json.loads(path.read_text(encoding="utf-8"))
        base = evaluate_scenario(scenario)
        if STATUS_RANK[base.allowed_status] < NORMATIVE:
            continue
        for challenge_id, challenged in _challenges(scenario, base.allowed_status, base.disposition):
            challenged["contestation_challenge"] = {
                "challenge": challenge_id,
                "source": scenario["id"],
                "base_allowed_status": base.allowed_status,
                "base_disposition": base.disposition,
                "purpose": "dynamic contestability validation for party challenge response",
            }
            (OUT / f"{challenged['id']}.json").write_text(
                json.dumps(challenged, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            count += 1
    print(f"Wrote {count} contestation challenge scenarios")
    return 0


def _scenario_paths() -> list[Path]:
    paths: list[Path] = []
    for suite in SUITES:
        paths.extend(sorted(suite["path"].glob("*.json")))
    return paths


def _challenges(scenario: dict, base_status: str, base_disposition: str) -> list[tuple[str, dict]]:
    return [
        ("valid_counter_material_challenge", _valid_counter_material_challenge(scenario)),
        ("source_verification_challenge", _source_verification_challenge(scenario)),
        ("jurisdiction_assumption_challenge", _jurisdiction_assumption_challenge(scenario)),
        ("contestability_channel_failure", _contestability_channel_failure(scenario)),
        ("unsupported_challenge_control", _unsupported_challenge_control(scenario, base_status, base_disposition)),
    ]


def _valid_counter_material_challenge(scenario: dict) -> dict:
    challenged = _clone(scenario, "valid-counter-material-challenge", "reference_information", "suspension")
    authority_sets = challenged.setdefault("authority_sets", {})
    counter_id = f"party-submitted-counter-material-for-{scenario['id']}"
    authority_sets.setdefault("counter_or_limiting", [])
    if counter_id not in authority_sets["counter_or_limiting"]:
        authority_sets["counter_or_limiting"].append(counter_id)
    authority_sets.setdefault("retrieved_counter_or_limiting", [])
    authority_sets.setdefault("retrieved", [])
    challenged["counter_material_complete"] = True
    return challenged


def _source_verification_challenge(scenario: dict) -> dict:
    challenged = _clone(scenario, "source-verification-challenge", "reference_information", "downgrade")
    for link in challenged.get("evidence_packet", {}).get("output_links", []):
        link["source_tag"] = "needs_verification"
    return challenged


def _jurisdiction_assumption_challenge(scenario: dict) -> dict:
    challenged = _clone(scenario, "jurisdiction-assumption-challenge", "reference_information", "downgrade")
    challenged.setdefault("review_gate", {})["jurisdiction_assumptions"] = []
    return challenged


def _contestability_channel_failure(scenario: dict) -> dict:
    challenged = _clone(scenario, "contestability-channel-failure", "reference_information", "downgrade")
    challenged.pop("review_gate", None)
    return challenged


def _unsupported_challenge_control(scenario: dict, base_status: str, base_disposition: str) -> dict:
    challenged = _clone(scenario, "unsupported-challenge-control", base_status, base_disposition)
    challenged["unsupported_challenge_control"] = {
        "challenge_recorded": True,
        "new_source_or_counter_material_supplied": False,
        "reason": "The challenge contests the output but supplies no new source, counter-material, jurisdictional objection or adoption-record defect.",
    }
    return challenged


def _clone(scenario: dict, suffix: str, expected_status: str, expected_disposition: str) -> dict:
    challenged = deepcopy(scenario)
    challenged["id"] = f"{scenario['id']}--challenge-{suffix}"
    challenged["expected_allowed_status"] = expected_status
    challenged["expected_disposition"] = expected_disposition
    return challenged


if __name__ == "__main__":
    raise SystemExit(main())
