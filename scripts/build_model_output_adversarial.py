from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_model_output_repairs import repair, source_collection_for

SOURCE = ROOT / "experiments" / "ai_outputs" / "scenarios"
OUT = ROOT / "experiments" / "model_output_adversarial" / "scenarios"
RESULTS = ROOT / "experiments" / "model_output_adversarial" / "results"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.json"):
        old.unlink()
    count = 0
    for path in sorted(SOURCE.glob("codex55_*.json")):
        scenario = json.loads(path.read_text(encoding="utf-8"))
        for variant in variants(scenario):
            repaired = repair(variant)
            repaired["adversarial_intervention"] = variant["adversarial_intervention"]
            attack = variant["adversarial_intervention"]["attack"]
            if attack in {"claim_support_gap", "contradiction_pattern"}:
                repaired["expected_allowed_status"] = "no_external_legal_effect"
                repaired["expected_disposition"] = "withdrawal"
            else:
                repaired["expected_allowed_status"] = "reference_information"
                repaired["expected_disposition"] = "suspension" if attack == "counter_material_omission" else "downgrade"
            (OUT / f"{repaired['id']}.json").write_text(
                json.dumps(repaired, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            count += 1
    print(f"Wrote {count} adversarial source-support validation scenarios")
    return 0


def variants(scenario: dict) -> list[dict]:
    return [
        wrong_locator(scenario),
        unsupported_claim(scenario),
        contradictory_claim(scenario),
        out_of_manifest_source(scenario),
        missing_output_link(scenario),
        counter_material_omission(scenario),
    ]


def wrong_locator(scenario: dict) -> dict:
    mutated = clone(scenario, "wrong-locator", "locator_mismatch")
    unit, link = first_unit_and_link(mutated)
    unit["locators"][0] = "unrelated locator"
    link["locator"] = "unrelated locator"
    return mutated


def unsupported_claim(scenario: dict) -> dict:
    mutated = clone(scenario, "unsupported-claim", "claim_support_gap")
    unit, _ = first_unit_and_link(mutated)
    unit["claim"] = "This unrelated procedural proposition is not supported by the cited authority."
    return mutated


def contradictory_claim(scenario: dict) -> dict:
    mutated = clone(scenario, "contradictory-claim", "contradiction_pattern")
    unit, link = first_unit_and_link(mutated)
    pattern = first_contradiction_pattern(mutated, link["source_id"])
    unit["claim"] = f"{pattern}."
    return mutated


def out_of_manifest_source(scenario: dict) -> dict:
    mutated = clone(scenario, "out-of-manifest-source", "manifest_membership_gap")
    unit, link = first_unit_and_link(mutated)
    unit["source_ids"][0] = "adversarial-nonmanifest-source"
    link["source_id"] = "adversarial-nonmanifest-source"
    return mutated


def missing_output_link(scenario: dict) -> dict:
    mutated = clone(scenario, "missing-output-link", "unit_source_link_gap")
    _, link = first_unit_and_link(mutated)
    packet = mutated["evidence_packet"]
    packet["output_links"] = [
        item
        for item in packet["output_links"]
        if not (item.get("unit_id") == link.get("unit_id") and item.get("source_id") == link.get("source_id"))
    ]
    return mutated


def counter_material_omission(scenario: dict) -> dict:
    mutated = clone(scenario, "counter-material-omission", "counter_material_omission")
    authority_sets = mutated["authority_sets"]
    omitted = authority_sets["counter_or_limiting"][0]
    authority_sets["retrieved_counter_or_limiting"] = [
        item for item in authority_sets["retrieved_counter_or_limiting"] if item != omitted
    ]
    authority_sets["retrieved"] = [item for item in authority_sets["retrieved"] if item != omitted]
    mutated["counter_material_complete"] = True
    return mutated


def clone(scenario: dict, suffix: str, attack: str) -> dict:
    mutated = deepcopy(scenario)
    mutated["id"] = f"{scenario['id']}--{suffix}"
    mutated["adversarial_intervention"] = {
        "attack": attack,
        "source": scenario["id"],
        "purpose": "negative-control validation for source-support repair gates",
    }
    return mutated


def first_unit_and_link(scenario: dict) -> tuple[dict, dict]:
    unit = scenario["evidence_packet"]["output_units"][0]
    for link in scenario["evidence_packet"]["output_links"]:
        if link.get("unit_id") == unit["id"]:
            return unit, link
    raise ValueError(f"No link found for first unit in {scenario['id']}")


def first_contradiction_pattern(scenario: dict, source_id: str) -> str:
    manifest = json.loads((ROOT / source_collection_for(scenario["id"])).read_text(encoding="utf-8"))
    records = {record["id"]: record for record in manifest.get("records", [])}
    for support in records[source_id].get("source_support", []):
        patterns = support.get("contradiction_patterns", [])
        if patterns:
            return patterns[0]
    return "the cited authority does not support this proposition"


if __name__ == "__main__":
    raise SystemExit(main())
