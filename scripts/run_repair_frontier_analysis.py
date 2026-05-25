from __future__ import annotations

import copy
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_harness.model import DIMENSIONS, RANK_SALIENCE_WINDOW, STATUS_RANK, evaluate_scenario
from run_full_validation import SUITES


RESULTS = ROOT / "experiments" / "repair_frontiers" / "results"
NORMATIVE = STATUS_RANK["normative_material_screening_output"]
DECISION = STATUS_RANK["decision_support_reason"]


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = _frontier_rows()
    unrepaired = [row for row in rows if not row["repairable"]]
    payload = {
        "blocked_claim_count": len(rows),
        "counterfactual_evaluation_count": sum(row["counterfactual_evaluations"] for row in rows),
        "repairable_count": len(rows) - len(unrepaired),
        "unrepairable_count": len(unrepaired),
        "minimal_repair_size_distribution": _size_distribution(rows),
        "minimal_repair_gate_frequency": _gate_frequency(rows),
        "target_distribution": _target_distribution(rows),
        "unrepairable": unrepaired,
        "results": rows,
    }
    report = _format_report(payload)
    (RESULTS / "repair_frontier_analysis.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    (RESULTS / "repair_frontier_analysis.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0 if not unrepaired else 1


def _scenario_paths() -> list[Path]:
    paths: list[Path] = []
    for suite in SUITES:
        paths.extend(sorted(suite["path"].glob("*.json")))
    return paths


def _frontier_rows() -> list[dict]:
    rows: list[dict] = []
    for path in _scenario_paths():
        scenario = json.loads(path.read_text(encoding="utf-8"))
        base = evaluate_scenario(scenario)
        target = scenario["claimed_status"]
        if STATUS_RANK[target] < NORMATIVE or STATUS_RANK[base.allowed_status] >= STATUS_RANK[target]:
            continue
        interventions = _interventions_for(target)
        successes = []
        evaluation_count = 0
        full_repair_status = None
        for size in range(1, len(interventions) + 1):
            for combo in itertools.combinations(interventions, size):
                evaluation_count += 1
                variant = _apply_interventions(scenario, combo, target)
                result = evaluate_scenario(variant)
                if len(combo) == len(interventions):
                    full_repair_status = result.allowed_status
                if STATUS_RANK[result.allowed_status] >= STATUS_RANK[target]:
                    successes.append(
                        {
                            "gates": [gate for gate, _ in combo],
                            "allowed_status": result.allowed_status,
                            "disposition": result.disposition,
                        }
                    )
            if successes:
                break
        minimal_size = len(successes[0]["gates"]) if successes else None
        rows.append(
            {
                "scenario_id": scenario["id"],
                "path": str(path.relative_to(ROOT)),
                "target_status": target,
                "base_allowed_status": base.allowed_status,
                "base_disposition": base.disposition,
                "base_failure_flags": base.failure_flags,
                "counterfactual_evaluations": evaluation_count,
                "repairable": bool(successes),
                "minimal_repair_size": minimal_size,
                "minimal_repairs": successes,
                "full_repair_status": full_repair_status,
            }
        )
    return rows


def _interventions_for(target: str) -> list[tuple[str, callable]]:
    interventions = [
        ("audit_vector_completion", _complete_audit_vector),
        ("authority_packet_completion", _complete_authority_packet),
        ("source_binding_completion", _complete_source_binding),
        ("rank_salience_completion", _complete_rank_salience),
        ("review_contestability_completion", _complete_review_contestability),
        ("role_cap_completion", _complete_role_cap),
        ("failure_flag_resolution", _clear_failure_flags),
    ]
    if STATUS_RANK[target] >= DECISION:
        interventions.append(("decision_adoption_completion", _complete_decision_adoption))
    return interventions


def _apply_interventions(scenario: dict, interventions: tuple[tuple[str, callable], ...], target: str) -> dict:
    variant = copy.deepcopy(scenario)
    variant.pop("expected_allowed_status", None)
    variant.pop("expected_disposition", None)
    for _, intervention in interventions:
        intervention(variant, target)
    return variant


def _complete_audit_vector(scenario: dict, target: str) -> None:
    scores = scenario.setdefault("scores", {})
    for dimension in DIMENSIONS:
        item = scores.setdefault(dimension, {})
        if not isinstance(item, dict):
            item = {"score": item}
            scores[dimension] = item
        item["score"] = max(int(item.get("score", 0)), 2 if STATUS_RANK[target] >= DECISION else 1)
    total = sum(int(scores[dimension]["score"]) for dimension in DIMENSIONS)
    threshold = 10 if STATUS_RANK[target] >= DECISION else 9
    for dimension in DIMENSIONS:
        if total >= threshold:
            break
        if scores[dimension]["score"] < 2:
            scores[dimension]["score"] = 2
            total += 1


def _complete_authority_packet(scenario: dict, target: str) -> None:
    authority_sets = scenario.setdefault("authority_sets", {})
    high = list(authority_sets.get("high_authority") or ["repair-high-authority"])
    counter = list(authority_sets.get("counter_or_limiting") or ["repair-counter-material"])
    authority_sets["high_authority"] = high
    authority_sets["retrieved_high_authority"] = high
    authority_sets["counter_or_limiting"] = counter
    authority_sets["retrieved_counter_or_limiting"] = counter
    invalid = set(authority_sets.get("invalid_or_superseded", []))
    authority_sets["retrieved"] = sorted((set(authority_sets.get("retrieved", []) + high + counter)) - invalid)
    authority_sets["retrieved_invalid_treatments"] = []
    scenario["counter_material_complete"] = True


def _complete_rank_salience(scenario: dict, target: str) -> None:
    authority_sets = scenario.get("authority_sets", {})
    counter = list(authority_sets.get("retrieved_counter_or_limiting") or [])
    if not counter:
        return
    target_source = counter[0]
    units = scenario.get("evidence_packet", {}).get("output_units", [])
    if any(target_source in set(unit.get("source_ids", [])) for unit in units[:RANK_SALIENCE_WINDOW]):
        return
    insert_at = min(RANK_SALIENCE_WINDOW - 1, len(units))
    for index, unit in enumerate(units):
        if target_source in set(unit.get("source_ids", [])):
            units.insert(insert_at, units.pop(index))
            _refresh_output_ranks(units)
            return


def _refresh_output_ranks(units: list[dict]) -> None:
    if not any("output_rank" in unit for unit in units):
        return
    for rank, unit in enumerate(units, start=1):
        unit["output_rank"] = rank


def _complete_source_binding(scenario: dict, target: str) -> None:
    packet = scenario.setdefault("evidence_packet", {})
    units = packet.setdefault("output_units", [])
    links = packet.setdefault("output_links", [])
    if not units:
        units.append(
            {
                "id": "repair-unit-1",
                "claim": "Repair-frontier source-bound output unit.",
                "source_ids": ["repair-high-authority"],
                "locators": ["repair-locator-1"],
            }
        )
    existing_sources = {source_id for unit in units for source_id in unit.get("source_ids", [])}
    authority_sets = scenario.get("authority_sets", {})
    required_sources = list(authority_sets.get("retrieved_high_authority") or []) + list(
        authority_sets.get("retrieved_counter_or_limiting") or []
    )
    for source_id in required_sources:
        if source_id in existing_sources:
            continue
        unit = {
            "id": f"repair-unit-{len(units) + 1}",
            "claim": "Repair-frontier source-bound authority unit.",
            "source_ids": [source_id],
            "locators": [f"{source_id}-locator"],
        }
        units.append(unit)
        existing_sources.add(source_id)
    for index, unit in enumerate(units, start=1):
        unit.setdefault("id", f"repair-unit-{index}")
        unit.setdefault("claim", "Repair-frontier source-bound legal proposition.")
        if not unit.get("source_ids"):
            unit["source_ids"] = [f"repair-source-{index}"]
        if not unit.get("locators"):
            unit["locators"] = [f"repair-locator-{index}"]
    if not links:
        for unit in units:
            links.append(
                {
                    "unit_id": unit["id"],
                    "source_id": unit["source_ids"][0],
                    "locator": unit["locators"][0],
                    "supports_claim": True,
                    "source_tag": "official_source",
                }
            )
    unit_map = {unit["id"]: unit for unit in units}
    for link in links:
        unit = unit_map.get(link.get("unit_id"))
        if unit is None:
            unit = units[0]
            link["unit_id"] = unit["id"]
        link["source_id"] = link.get("source_id") or unit["source_ids"][0]
        if link["source_id"] not in unit["source_ids"]:
            unit["source_ids"].append(link["source_id"])
        link["locator"] = link.get("locator") or unit["locators"][0]
        if link["locator"] not in unit["locators"]:
            unit["locators"].append(link["locator"])
        link["supports_claim"] = True
        link["source_tag"] = "official_source"
    linked_pairs = {(link.get("unit_id"), link.get("source_id")) for link in links}
    for unit in units:
        for source_id in unit.get("source_ids", []):
            pair = (unit["id"], source_id)
            if pair in linked_pairs:
                continue
            links.append(
                {
                    "unit_id": unit["id"],
                    "source_id": source_id,
                    "locator": unit["locators"][0],
                    "supports_claim": True,
                    "source_tag": "official_source",
                }
            )
            linked_pairs.add(pair)
    scenario["source_binding_validation"] = {
        "all_links_source_bound": True,
        "high_authority_complete": True,
        "counter_material_complete": True,
        "unsupported_source_support": [],
    }


def _complete_review_contestability(scenario: dict, target: str) -> None:
    gate = scenario.setdefault("review_gate", {})
    gate["attorney_review_required"] = True
    gate["review_status"] = "completed"
    gate["reliance_gate"] = "attorney_review"
    gate["jurisdiction_assumptions"] = gate.get("jurisdiction_assumptions") or [_repair_jurisdiction_profile(scenario)]
    gate["contestability_channel"] = "repair-frontier-review-record"
    gate["irreversible_action"] = False
    gate["human_authorization"] = False


def _complete_role_cap(scenario: dict, target: str) -> None:
    scenario["system_role"] = (
        "authorized_decision_support_tool"
        if STATUS_RANK[target] >= DECISION
        else "auditable_procedural_tool"
    )


def _complete_decision_adoption(scenario: dict, target: str) -> None:
    gate = scenario.setdefault("review_gate", {})
    gate["attorney_review_required"] = True
    gate["review_status"] = "completed"
    gate["reliance_gate"] = "authorized_adoption"
    gate["human_authorization"] = True
    gate["jurisdiction_assumptions"] = gate.get("jurisdiction_assumptions") or [_repair_jurisdiction_profile(scenario)]
    gate["contestability_channel"] = "repair-frontier-adoption-record"
    gate["adoption_reasons_recorded"] = True
    gate["contestation_recorded"] = True
    gate["irreversible_action"] = False
    scenario["system_role"] = "authorized_decision_support_tool"


def _clear_failure_flags(scenario: dict, target: str) -> None:
    scenario["failure_flags"] = []


def _repair_jurisdiction_profile(scenario: dict) -> str:
    return scenario.get("jurisdiction_profile") or "repair-frontier-jurisdiction"


def _size_distribution(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = "unrepairable" if row["minimal_repair_size"] is None else str(row["minimal_repair_size"])
        counts[key] = counts.get(key, 0) + 1
    return counts


def _gate_frequency(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for repair in row["minimal_repairs"]:
            for gate in repair["gates"]:
                counts[gate] = counts.get(gate, 0) + 1
    return counts


def _target_distribution(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["target_status"]] = counts.get(row["target_status"], 0) + 1
    return counts


def _format_report(payload: dict) -> str:
    lines = [
        "# Repair Frontier Analysis",
        "",
        f"Blocked procedural claims: {payload['blocked_claim_count']}",
        f"Counterfactual repair evaluations: {payload['counterfactual_evaluation_count']}",
        f"Repairable by declared gate families: {payload['repairable_count']}/{payload['blocked_claim_count']}",
        "",
        "## Minimal Repair Size",
        "",
        "| Gate families required | Blocked claims |",
        "| ---: | ---: |",
    ]
    for size, count in sorted(payload["minimal_repair_size_distribution"].items(), key=lambda item: item[0]):
        lines.append(f"| {size} | {count} |")
    lines.extend(["", "## Minimal Repair Gate Frequency", "", "| Gate family | Occurrences in minimal frontiers |", "| --- | ---: |"])
    for gate, count in sorted(payload["minimal_repair_gate_frequency"].items()):
        lines.append(f"| {gate} | {count} |")
    lines.extend(["", "## Target Status Distribution", "", "| Target status | Blocked claims |", "| --- | ---: |"])
    for status, count in sorted(payload["target_distribution"].items()):
        lines.append(f"| {status} | {count} |")
    if payload["unrepairable"]:
        lines.extend(["", "## Unrepairable", ""])
        for row in payload["unrepairable"]:
            lines.append(f"- {row['scenario_id']}: full repair ended at {row['full_repair_status']}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
