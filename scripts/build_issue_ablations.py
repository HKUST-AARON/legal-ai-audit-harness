from __future__ import annotations

import argparse
import json
import shutil
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments" / "issue_gold_sets" / "scenarios"
DEFAULT_OUT = ROOT / "experiments" / "issue_ablations"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    scenarios = args.out / "scenarios"
    results = args.out / "results"
    if scenarios.exists():
        shutil.rmtree(scenarios)
    scenarios.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)

    for path in sorted(SOURCE.glob("*.json")):
        base = json.loads(path.read_text(encoding="utf-8"))
        for scenario in build_ablations(base):
            target = scenarios / f"{scenario['id']}.json"
            target.write_text(json.dumps(scenario, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


def build_ablations(base: dict) -> list[dict]:
    return [
        missing_high_authority(base),
        counter_material_suppressed(base),
        unverified_source_tags(base),
        decision_reason_without_adoption(base),
    ]


def missing_high_authority(base: dict) -> dict:
    scenario = clone(base, "missing-high-authority")
    high = scenario["authority_sets"]["retrieved_high_authority"]
    omitted = high[-1]
    scenario["authority_sets"]["retrieved_high_authority"] = high[:-1]
    scenario["authority_sets"]["retrieved"] = [item for item in scenario["authority_sets"]["retrieved"] if item != omitted]
    remove_source(scenario, omitted)
    scenario["scores"]["K"]["score"] = 1
    scenario["scores"]["K"]["evidence"] = "The packet is source-bound, but it omits a known high-authority material for the issue."
    scenario["expected_allowed_status"] = "reference_information"
    scenario["expected_disposition"] = "suspension"
    update_upstream_metrics(scenario)
    return scenario


def counter_material_suppressed(base: dict) -> dict:
    scenario = clone(base, "counter-material-suppressed")
    scenario["counter_material_complete"] = True
    counter = scenario["authority_sets"]["counter_or_limiting"][0]
    scenario["authority_sets"]["retrieved_counter_or_limiting"] = [
        item for item in scenario["authority_sets"]["retrieved_counter_or_limiting"] if item != counter
    ]
    scenario["scores"]["K"]["score"] = 1
    scenario["scores"]["K"]["evidence"] = "The packet suppresses at least one known limiting or contrary material."
    scenario["expected_allowed_status"] = "reference_information"
    scenario["expected_disposition"] = "suspension"
    update_upstream_metrics(scenario)
    return scenario


def unverified_source_tags(base: dict) -> dict:
    scenario = clone(base, "unverified-source-tags")
    for link in scenario["evidence_packet"]["output_links"]:
        link["source_tag"] = "needs_verification"
    scenario["scores"]["S"]["score"] = 1
    scenario["scores"]["S"]["evidence"] = "The packet names sources, but every source tag still requires independent verification."
    scenario["expected_allowed_status"] = "reference_information"
    scenario["expected_disposition"] = "downgrade"
    update_upstream_metrics(scenario)
    return scenario


def decision_reason_without_adoption(base: dict) -> dict:
    scenario = clone(base, "decision-reason-without-adoption")
    scenario["claimed_status"] = "decision_support_reason"
    scenario["scores"]["L"]["score"] = 2
    scenario["scores"]["L"]["evidence"] = "The output packet is fully logged, but the review gate does not record authorized institutional adoption."
    scenario["expected_allowed_status"] = "normative_material_screening_output"
    scenario["expected_disposition"] = "none"
    update_upstream_metrics(scenario)
    return scenario


def clone(base: dict, suffix: str) -> dict:
    scenario = deepcopy(base)
    scenario["id"] = f"{base['id']}-{suffix}"
    scenario["deployment_context"] = f"{base['deployment_context']} Ablation: {suffix.replace('-', ' ')}."
    scenario["failure_flags"] = []
    return scenario


def remove_source(scenario: dict, source_id: str) -> None:
    packet = scenario["evidence_packet"]
    packet["output_links"] = [link for link in packet["output_links"] if link["source_id"] != source_id]
    packet["output_units"] = [
        unit
        for unit in packet["output_units"]
        if source_id not in set(unit.get("source_ids", []))
    ]


def update_upstream_metrics(scenario: dict) -> None:
    authority_sets = scenario["authority_sets"]
    known = set(authority_sets.get("high_authority", [])) | set(authority_sets.get("counter_or_limiting", []))
    retrieved = set(authority_sets.get("retrieved_high_authority", [])) | set(authority_sets.get("retrieved_counter_or_limiting", []))
    if not known:
        return
    recall = len(known & retrieved) / len(known)
    precision = len(known & retrieved) / len(retrieved) if retrieved else 0.0
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    scenario["upstream_metrics"] = {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


if __name__ == "__main__":
    raise SystemExit(main())
