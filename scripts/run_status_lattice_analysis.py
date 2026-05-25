from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))

from audit_harness.model import DIMENSIONS, STATUS_RANK, SYSTEM_ROLE_CAPS, evaluate_scenario


RESULTS = ROOT / "experiments" / "status_lattice" / "results"
ROLES = tuple(SYSTEM_ROLE_CAPS)
GATES = ("evidence", "procedural_source", "high_authority", "counter_material", "review", "adoption")


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    states = _states()
    status_by_key = {key: evaluate_scenario(_scenario(key)).allowed_status for key in states}
    substitution_rules = _substitution_rules(status_by_key)
    payload = {
        "state_count": len(states),
        "role_count": len(ROLES),
        "score_vector_count": 3 ** len(DIMENSIONS),
        "gate_count": len(GATES),
        "status_distribution": _distribution(status_by_key.values()),
        "high_status_count": sum(_high(status) for status in status_by_key.values()),
        "decision_status_count": sum(status == "decision_support_reason" for status in status_by_key.values()),
        "cover_edge_diagnostics": _cover_edge_diagnostics(status_by_key),
        "necessity": _necessity(status_by_key),
        "gate_ablation": _gate_ablation(status_by_key),
        "substitution_rules": substitution_rules,
        "substitution_checks": _substitution_checks(substitution_rules),
    }
    (RESULTS / "status_lattice_analysis.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (RESULTS / "status_lattice_analysis.md").write_text(_format_report(payload) + "\n", encoding="utf-8")
    print(_format_report(payload))
    return (
        0
        if payload["necessity"]["failed"] == 0
        and payload["gate_ablation"]["failed"] == 0
        and payload["substitution_checks"]["failed"] == 0
        else 1
    )


def _states() -> list[tuple]:
    return [
        (vector, role, gates)
        for vector in itertools.product((0, 1, 2), repeat=len(DIMENSIONS))
        for role in ROLES
        for gates in itertools.product((False, True), repeat=len(GATES))
    ]


def _scenario(key: tuple) -> dict:
    vector, role, gates = key
    gate = dict(zip(GATES, gates, strict=True))
    scenario = {
        "id": "status-lattice-state",
        "claimed_status": "decision_support_reason",
        "system_role": role,
        "scores": {dimension: score for dimension, score in zip(DIMENSIONS, vector, strict=True)},
        "authority_sets": {
            "high_authority": ["high-a"],
            "retrieved_high_authority": ["high-a"] if gate["high_authority"] else [],
            "counter_or_limiting": ["counter-a"],
            "retrieved_counter_or_limiting": ["counter-a"] if gate["counter_material"] else [],
            "retrieved": [
                item
                for item, present in (
                    ("high-a", gate["high_authority"]),
                    ("counter-a", gate["counter_material"]),
                )
                if present
            ],
        },
        "review_gate": {
            "review_status": "completed" if gate["review"] else "pending",
            "reliance_gate": "authorized_adoption" if gate["adoption"] else "attorney_review",
            "human_authorization": gate["adoption"],
            "jurisdiction_assumptions": ["abstract_common_law"] if gate["review"] else [],
            "adoption_reasons_recorded": gate["adoption"],
            "contestation_recorded": gate["adoption"],
            "attorney_review_required": True,
        },
    }
    if gate["evidence"]:
        tag = "official_source" if gate["procedural_source"] else "needs_verification"
        scenario["evidence_packet"] = {
            "output_units": [
                {
                    "id": "u1",
                    "source_ids": scenario["authority_sets"]["retrieved"],
                    "locators": [f"{source}:1" for source in scenario["authority_sets"]["retrieved"]],
                }
            ],
            "output_links": [
                {
                    "unit_id": "u1",
                    "source_id": source,
                    "locator": f"{source}:1",
                    "supports_claim": True,
                    "source_tag": tag,
                }
                for source in scenario["authority_sets"]["retrieved"]
            ],
        }
    return scenario


def _cover_edge_diagnostics(status_by_key: dict[tuple, str]) -> dict:
    checks = promotions = demotions = stable = 0
    for key, status in status_by_key.items():
        vector, role, gates = key
        base_rank = STATUS_RANK[status]
        for index, score in enumerate(vector):
            if score == 2:
                continue
            upper = list(vector)
            upper[index] += 1
            checks += 1
            delta = STATUS_RANK[status_by_key[(tuple(upper), role, gates)]] - base_rank
            promotions += int(delta > 0)
            demotions += int(delta < 0)
            stable += int(delta == 0)
        for index, value in enumerate(gates):
            if value:
                continue
            upper_gates = list(gates)
            upper_gates[index] = True
            checks += 1
            delta = STATUS_RANK[status_by_key[(vector, role, tuple(upper_gates))]] - base_rank
            promotions += int(delta > 0)
            demotions += int(delta < 0)
            stable += int(delta == 0)
    return {"checks": checks, "promotions": promotions, "demotions": demotions, "stable": stable}


def _necessity(status_by_key: dict[tuple, str]) -> dict:
    required_for_high = ("evidence", "procedural_source", "high_authority", "counter_material", "review")
    failures = []
    checks = 0
    for key, status in status_by_key.items():
        if not _high(status):
            continue
        gates = dict(zip(GATES, key[2], strict=True))
        for name in required_for_high:
            checks += 1
            if not gates[name]:
                failures.append({"state": _state_dict(key), "status": status, "missing": name})
        if status == "decision_support_reason":
            checks += 1
            if not gates["adoption"]:
                failures.append({"state": _state_dict(key), "status": status, "missing": "adoption"})
    return {"checks": checks, "passed": checks - len(failures), "failed": len(failures), "failures": failures[:10]}


def _gate_ablation(status_by_key: dict[tuple, str]) -> dict:
    checks = passed = 0
    by_gate = {gate: {"checks": 0, "passed": 0} for gate in GATES}
    for key, status in status_by_key.items():
        if not _high(status):
            continue
        gates = list(key[2])
        for index, gate in enumerate(GATES):
            if not gates[index]:
                continue
            lowered_gates = list(gates)
            lowered_gates[index] = False
            lowered = (key[0], key[1], tuple(lowered_gates))
            lowered_status = status_by_key[lowered]
            expected_drop = STATUS_RANK[lowered_status] < STATUS_RANK[status]
            if status == "normative_material_screening_output" and gate == "adoption":
                continue
            checks += 1
            by_gate[gate]["checks"] += 1
            if expected_drop:
                passed += 1
                by_gate[gate]["passed"] += 1
    for gate, row in by_gate.items():
        row["failed"] = row["checks"] - row["passed"]
    return {"checks": checks, "passed": passed, "failed": checks - passed, "by_gate": by_gate}


def _substitution_rules(status_by_key: dict[tuple, str]) -> list[dict]:
    rules = {
        "total_score_at_least_9": lambda key: sum(key[0]) >= 9,
        "complete_vector_and_score": lambda key: all(score >= 1 for score in key[0]) and sum(key[0]) >= 9,
        "role_ready_and_score": lambda key: key[1] in {"auditable_procedural_tool", "authorized_decision_support_tool"} and sum(key[0]) >= 9,
        "source_bound_score": lambda key: _gates(key, "evidence", "procedural_source") and all(score >= 1 for score in key[0]) and sum(key[0]) >= 9,
        "source_authority_score": lambda key: _gates(key, "evidence", "procedural_source", "high_authority") and all(score >= 1 for score in key[0]) and sum(key[0]) >= 9,
        "source_authority_counter_score": lambda key: _gates(key, "evidence", "procedural_source", "high_authority", "counter_material") and all(score >= 1 for score in key[0]) and sum(key[0]) >= 9,
        "full_screening_predicate": lambda key: _gates(key, "evidence", "procedural_source", "high_authority", "counter_material", "review")
        and key[1] in {"auditable_procedural_tool", "authorized_decision_support_tool"}
        and all(score >= 1 for score in key[0])
        and sum(key[0]) >= 9,
    }
    return [_rule_stats(name, rule, status_by_key) for name, rule in rules.items()]


def _rule_stats(name: str, rule, status_by_key: dict[tuple, str]) -> dict:
    tp = fp = tn = fn = 0
    for key, status in status_by_key.items():
        predicted = rule(key)
        actual = _high(status)
        if predicted and actual:
            tp += 1
        elif predicted and not actual:
            fp += 1
        elif not predicted and actual:
            fn += 1
        else:
            tn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "rule": name,
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
    }


def _substitution_checks(rows: list[dict]) -> dict:
    full = next(row for row in rows if row["rule"] == "full_screening_predicate")
    partials = [row for row in rows if row["rule"] != "full_screening_predicate"]
    best_partial = min(partials, key=lambda row: (row["false_positive"] + row["false_negative"], row["false_positive"]))
    failures = []
    if full["false_positive"] or full["false_negative"]:
        failures.append("full_screening_predicate_mismatch")
    if best_partial["false_positive"] <= 0:
        failures.append("partial_predicate_did_not_over_admit")
    return {
        "checks": 2,
        "passed": 2 - len(failures),
        "failed": len(failures),
        "failures": failures,
        "best_partial_rule": best_partial["rule"],
        "best_partial_false_positive": best_partial["false_positive"],
        "full_predicate_false_positive": full["false_positive"],
        "full_predicate_false_negative": full["false_negative"],
    }


def _gates(key: tuple, *names: str) -> bool:
    gate = dict(zip(GATES, key[2], strict=True))
    return all(gate[name] for name in names)


def _high(status: str) -> bool:
    return STATUS_RANK[status] >= STATUS_RANK["normative_material_screening_output"]


def _distribution(statuses) -> dict[str, int]:
    distribution: dict[str, int] = {}
    for status in statuses:
        distribution[status] = distribution.get(status, 0) + 1
    return dict(sorted(distribution.items()))


def _state_dict(key: tuple) -> dict:
    vector, role, gates = key
    return {
        "scores": dict(zip(DIMENSIONS, vector, strict=True)),
        "role": role,
        "gates": dict(zip(GATES, gates, strict=True)),
    }


def _format_report(payload: dict) -> str:
    lines = [
        "# Status Lattice Analysis",
        "",
        f"States: {payload['state_count']}",
        f"Score vectors: {payload['score_vector_count']}",
        f"Roles: {payload['role_count']}",
        f"Gates: {payload['gate_count']}",
        f"High-status states: {payload['high_status_count']}",
        f"Decision-status states: {payload['decision_status_count']}",
        "",
        "## Status Distribution",
        "",
        "| Status | Count |",
        "| --- | ---: |",
    ]
    for status, count in payload["status_distribution"].items():
        lines.append(f"| {status} | {count} |")
    lines.extend(
        [
            "",
        "## Lattice Checks",
        "",
        "| Check | Passed | Total | Failed |",
        "| --- | ---: | ---: | ---: |",
        f"| High-status necessity | {payload['necessity']['passed']} | {payload['necessity']['checks']} | {payload['necessity']['failed']} |",
        f"| Gate ablation drops | {payload['gate_ablation']['passed']} | {payload['gate_ablation']['checks']} | {payload['gate_ablation']['failed']} |",
        f"| Substitute-rule non-reduction | {payload['substitution_checks']['passed']} | {payload['substitution_checks']['checks']} | {payload['substitution_checks']['failed']} |",
        "",
            "## Cover-Edge Diagnostics",
            "",
            "| Edges | Promotions | Demotions | Stable |",
            "| ---: | ---: | ---: | ---: |",
            f"| {payload['cover_edge_diagnostics']['checks']} | {payload['cover_edge_diagnostics']['promotions']} | {payload['cover_edge_diagnostics']['demotions']} | {payload['cover_edge_diagnostics']['stable']} |",
            "",
            "## Substitute Rules",
            "",
            "| Rule | Precision | Recall | FP | FN |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["substitution_rules"]:
        lines.append(
            f"| {row['rule']} | {row['precision']:.4f} | {row['recall']:.4f} | {row['false_positive']} | {row['false_negative']} |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
