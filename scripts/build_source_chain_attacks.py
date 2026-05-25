from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_harness.model import STATUS_RANK, evaluate_scenario
from run_full_validation import SUITES

OUT = ROOT / "experiments" / "source_chain_attacks" / "scenarios"
RESULTS = ROOT / "experiments" / "source_chain_attacks" / "results"
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
        for attack_id, attacked in _attacks(scenario):
            attacked["source_chain_attack"] = {
                "attack": attack_id,
                "source": scenario["id"],
                "base_allowed_status": base.allowed_status,
                "purpose": "whole-matrix negative-control validation for procedural source-chain gates",
            }
            (OUT / f"{attacked['id']}.json").write_text(
                json.dumps(attacked, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            count += 1
    print(f"Wrote {count} source-chain attack scenarios")
    return 0


def _scenario_paths() -> list[Path]:
    paths: list[Path] = []
    for suite in SUITES:
        paths.extend(sorted(suite["path"].glob("*.json")))
    return paths


def _attacks(scenario: dict) -> list[tuple[str, dict]]:
    return [
        ("locator_mismatch", _locator_mismatch(scenario)),
        ("source_id_mismatch", _source_id_mismatch(scenario)),
        ("nonprocedural_source_tags", _nonprocedural_source_tags(scenario)),
        ("high_authority_omission", _high_authority_omission(scenario)),
        ("counter_material_omission", _counter_material_omission(scenario)),
    ]


def _locator_mismatch(scenario: dict) -> dict:
    attacked = _clone(scenario, "locator-mismatch", "no_external_legal_effect", "withdrawal")
    link = _first_output_link(attacked)
    link["locator"] = "__wrong_locator__"
    return attacked


def _source_id_mismatch(scenario: dict) -> dict:
    attacked = _clone(scenario, "source-id-mismatch", "no_external_legal_effect", "withdrawal")
    link = _first_output_link(attacked)
    link["source_id"] = "__nonmanifest_source__"
    return attacked


def _nonprocedural_source_tags(scenario: dict) -> dict:
    attacked = _clone(scenario, "nonprocedural-source-tags", "reference_information", "downgrade")
    for link in attacked.get("evidence_packet", {}).get("output_links", []):
        link["source_tag"] = "needs_verification"
    return attacked


def _high_authority_omission(scenario: dict) -> dict:
    attacked = _clone(scenario, "high-authority-omission", "reference_information", "suspension")
    authority_sets = attacked.setdefault("authority_sets", {})
    high_authority = authority_sets.get("high_authority") or []
    if high_authority:
        omitted = high_authority[0]
        authority_sets["retrieved_high_authority"] = [
            item for item in authority_sets.get("retrieved_high_authority", []) if item != omitted
        ]
        authority_sets["retrieved"] = [item for item in authority_sets.get("retrieved", []) if item != omitted]
    return attacked


def _counter_material_omission(scenario: dict) -> dict:
    attacked = _clone(scenario, "counter-material-omission", "reference_information", "suspension")
    authority_sets = attacked.setdefault("authority_sets", {})
    counter_material = authority_sets.get("counter_or_limiting") or []
    if counter_material:
        omitted = counter_material[0]
        authority_sets["retrieved_counter_or_limiting"] = [
            item for item in authority_sets.get("retrieved_counter_or_limiting", []) if item != omitted
        ]
        authority_sets["retrieved"] = [item for item in authority_sets.get("retrieved", []) if item != omitted]
        attacked["counter_material_complete"] = True
    return attacked


def _clone(scenario: dict, suffix: str, expected_status: str, expected_disposition: str) -> dict:
    attacked = deepcopy(scenario)
    attacked["id"] = f"{scenario['id']}--source-chain-{suffix}"
    attacked["expected_allowed_status"] = expected_status
    attacked["expected_disposition"] = expected_disposition
    return attacked


def _first_output_link(scenario: dict) -> dict:
    links = scenario.get("evidence_packet", {}).get("output_links", [])
    if not links:
        raise ValueError(f"No output links available for {scenario['id']}")
    return links[0]


if __name__ == "__main__":
    raise SystemExit(main())
