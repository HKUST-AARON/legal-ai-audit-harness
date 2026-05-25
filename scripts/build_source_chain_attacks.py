from __future__ import annotations

import json
import sys
from copy import deepcopy
from itertools import combinations
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
    variants = []
    for size in range(1, len(ATTACKS) + 1):
        for selected in combinations(ATTACKS, size):
            suffix = selected[0][1] if size == 1 else "compound-" + "-".join(item[2] for item in selected)
            expected_status, expected_disposition = _expected(selected)
            attacked = _clone(scenario, suffix, expected_status, expected_disposition)
            for *_, mutator in selected:
                mutator(attacked)
            variants.append(("+".join(item[0] for item in selected), attacked))
    return variants


def _expected(selected: tuple[tuple, ...]) -> tuple[str, str]:
    disposition = max((item[3] for item in selected), key=lambda item: {"downgrade": 2, "suspension": 3, "withdrawal": 4}[item])
    if disposition == "withdrawal":
        return "no_external_legal_effect", "withdrawal"
    return "reference_information", disposition


def _locator_mismatch(attacked: dict) -> None:
    link = _first_output_link(attacked)
    link["locator"] = "__wrong_locator__"


def _source_id_mismatch(attacked: dict) -> None:
    link = _first_output_link(attacked)
    link["source_id"] = "__nonmanifest_source__"


def _nonprocedural_source_tags(attacked: dict) -> None:
    for link in attacked.get("evidence_packet", {}).get("output_links", []):
        link["source_tag"] = "needs_verification"


def _high_authority_omission(attacked: dict) -> None:
    authority_sets = attacked.setdefault("authority_sets", {})
    high_authority = authority_sets.get("high_authority") or []
    if high_authority:
        omitted = high_authority[0]
        authority_sets["retrieved_high_authority"] = [
            item for item in authority_sets.get("retrieved_high_authority", []) if item != omitted
        ]
        authority_sets["retrieved"] = [item for item in authority_sets.get("retrieved", []) if item != omitted]


def _counter_material_omission(attacked: dict) -> None:
    authority_sets = attacked.setdefault("authority_sets", {})
    counter_material = authority_sets.get("counter_or_limiting") or []
    if counter_material:
        omitted = counter_material[0]
        authority_sets["retrieved_counter_or_limiting"] = [
            item for item in authority_sets.get("retrieved_counter_or_limiting", []) if item != omitted
        ]
        authority_sets["retrieved"] = [item for item in authority_sets.get("retrieved", []) if item != omitted]
        attacked["counter_material_complete"] = True


ATTACKS = (
    ("locator_mismatch", "locator-mismatch", "loc", "withdrawal", _locator_mismatch),
    ("source_id_mismatch", "source-id-mismatch", "src", "withdrawal", _source_id_mismatch),
    ("nonprocedural_source_tags", "nonprocedural-source-tags", "tag", "downgrade", _nonprocedural_source_tags),
    ("high_authority_omission", "high-authority-omission", "ha", "suspension", _high_authority_omission),
    ("counter_material_omission", "counter-material-omission", "cm", "suspension", _counter_material_omission),
)


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
