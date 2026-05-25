from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_harness.model import STATUS_RANK, SYSTEM_ROLE_CAPS, evaluate_scenario
from run_full_validation import SUITES
from run_model_identity_invariance import IDENTITY_PROFILES

RESULTS = ROOT / "experiments" / "policy_mutations" / "results"
NORMATIVE_STATUS = "normative_material_screening_output"
DECISION_STATUS = "decision_support_reason"
REFERENCE_STATUS = "reference_information"
NORMATIVE = STATUS_RANK[NORMATIVE_STATUS]


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    scenarios = _load_scenarios()
    rows = _gate_removal_rows(scenarios) + _status_conferring_rows(scenarios)
    by_mutant = _by_mutant(rows)
    mutants = [
        {"mutant": mutant, **bucket}
        for mutant, bucket in sorted(by_mutant.items())
    ]
    payload = {
        "scenario_count": len(scenarios),
        "qualified_scenario_count": sum(
            STATUS_RANK[evaluate_scenario(scenario).allowed_status] >= NORMATIVE
            for scenario in scenarios
        ),
        "decision_scenario_count": sum(
            evaluate_scenario(scenario).allowed_status == DECISION_STATUS
            for scenario in scenarios
        ),
        "mutant_count": len(mutants),
        "killed_mutant_count": sum(mutant["killed"] for mutant in mutants),
        "survived_mutant_count": sum(not mutant["killed"] for mutant in mutants),
        "evaluation_count": len(rows),
        "classification_error_count": sum(row["classification_error"] for row in rows),
        "invalid_promotion_count": sum(row["invalid_promotion"] for row in rows),
        "false_negative_count": sum(row["false_negative"] for row in rows),
        "mutants": mutants,
        "rows": rows,
    }
    report = _format_report(payload)
    (RESULTS / "policy_mutation_analysis.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (RESULTS / "policy_mutation_analysis.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0 if payload["survived_mutant_count"] == 0 else 1


def _load_scenarios() -> list[dict]:
    scenarios: list[dict] = []
    for suite in SUITES:
        for path in sorted(suite["path"].glob("*.json")):
            scenario = json.loads(path.read_text(encoding="utf-8"))
            scenario["_source_path"] = str(path.relative_to(ROOT))
            scenarios.append(scenario)
    return scenarios


def _gate_removal_rows(scenarios: list[dict]) -> list[dict]:
    rows: list[dict] = []
    specs = [
        (
            "drop_evidence_packet_gate",
            "Policy no longer requires a source-linked evidence packet.",
            _without_evidence_packet,
            lambda base: STATUS_RANK[base.allowed_status] >= NORMATIVE,
        ),
        (
            "drop_procedural_source_tag_gate",
            "Policy accepts nonprocedural source tags as if they were verified.",
            _with_nonprocedural_source_tags,
            lambda base: STATUS_RANK[base.allowed_status] >= NORMATIVE,
        ),
        (
            "drop_high_authority_gate",
            "Policy stops requiring high-authority material coverage.",
            _without_high_authority,
            lambda base: STATUS_RANK[base.allowed_status] >= NORMATIVE,
        ),
        (
            "drop_counter_material_gate",
            "Policy stops requiring counter-material coverage.",
            _without_counter_material,
            lambda base: STATUS_RANK[base.allowed_status] >= NORMATIVE,
        ),
        (
            "drop_review_gate",
            "Policy allows high status without a review and contestability gate.",
            _without_review_gate,
            lambda base: STATUS_RANK[base.allowed_status] >= NORMATIVE,
        ),
        (
            "drop_jurisdiction_assumption_gate",
            "Policy ignores missing jurisdiction assumptions.",
            _without_jurisdiction_assumptions,
            lambda base: STATUS_RANK[base.allowed_status] >= NORMATIVE,
        ),
        (
            "ignore_role_caps",
            "Policy ignores system-role caps.",
            _with_back_office_role,
            lambda base: STATUS_RANK[base.allowed_status] >= NORMATIVE,
        ),
        (
            "ignore_failure_caps",
            "Policy ignores failure-cap dispositions.",
            _with_failure_cap,
            lambda base: STATUS_RANK[base.allowed_status] >= NORMATIVE,
        ),
        (
            "drop_adoption_gate_for_decision",
            "Policy treats decision support as complete without adoption reasons or contestation logging.",
            _without_decision_adoption,
            lambda base: base.allowed_status == DECISION_STATUS,
        ),
    ]
    for scenario in scenarios:
        base = evaluate_scenario(scenario)
        for mutant, description, mutate, in_scope in specs:
            if not in_scope(base):
                continue
            reference = evaluate_scenario(mutate(scenario))
            rows.append(
                _row(
                    mutant=mutant,
                    kind="gate_removal",
                    description=description,
                    scenario=scenario,
                    base_status=base.allowed_status,
                    reference_status=reference.allowed_status,
                    mutant_status=base.allowed_status,
                    reference_disposition=reference.disposition,
                    failure_flags=reference.failure_flags,
                    missing_gates=reference.missing_gates,
                )
            )
    return rows


def _status_conferring_rows(scenarios: list[dict]) -> list[dict]:
    rows: list[dict] = []
    specs = [
        (
            "metric_recall_confers_screening",
            "Policy treats recall at or above 0.8 as screening status.",
            _has_complete_metrics,
            lambda scenario, result: (scenario.get("upstream_metrics") or {}).get("recall", 0) >= 0.8,
        ),
        (
            "source_binding_confers_screening",
            "Policy treats source-bound evidence as screening status.",
            lambda _scenario, _result: True,
            lambda _scenario, result: result.evidence_fidelity == 1.0
            and result.evidence_coverage == 1.0
            and result.procedural_source_tag_coverage == 1.0,
        ),
        (
            "authority_material_confers_screening",
            "Policy treats authority and counter-material coverage as screening status.",
            lambda _scenario, _result: True,
            lambda scenario, result: result.authority_coverage == 1.0
            and (bool(scenario.get("counter_material_complete")) or result.counter_authority_recall == 1.0),
        ),
        (
            "review_label_confers_screening",
            "Policy treats review posture and role readiness as screening status.",
            lambda _scenario, _result: True,
            lambda scenario, result: STATUS_RANK[SYSTEM_ROLE_CAPS[result.system_role]] >= NORMATIVE
            and bool((scenario.get("review_gate") or {}).get("jurisdiction_assumptions")),
        ),
        (
            "total_score_confers_screening",
            "Policy treats total score at or above 9 as screening status.",
            lambda _scenario, _result: True,
            lambda _scenario, result: result.total_score >= 9,
        ),
    ]
    for scenario in scenarios:
        reference = evaluate_scenario(scenario)
        for mutant, description, in_scope, predicate in specs:
            if not in_scope(scenario, reference):
                continue
            mutant_high = bool(predicate(scenario, reference))
            rows.append(
                _row(
                    mutant=mutant,
                    kind="status_conferring",
                    description=description,
                    scenario=scenario,
                    base_status=reference.allowed_status,
                    reference_status=reference.allowed_status,
                    mutant_status=NORMATIVE_STATUS if mutant_high else REFERENCE_STATUS,
                    reference_disposition=reference.disposition,
                    failure_flags=reference.failure_flags,
                    missing_gates=reference.missing_gates,
                )
            )
        for profile in IDENTITY_PROFILES:
            rows.append(
                _row(
                    mutant="model_identity_confers_screening",
                    kind="status_conferring",
                    description="Policy treats provider, model or engine identity as screening status.",
                    scenario=scenario,
                    base_status=reference.allowed_status,
                    reference_status=reference.allowed_status,
                    mutant_status=NORMATIVE_STATUS,
                    reference_disposition=reference.disposition,
                    failure_flags=reference.failure_flags,
                    missing_gates=reference.missing_gates,
                    identity_profile=profile["profile_id"],
                )
            )
    return rows


def _row(
    *,
    mutant: str,
    kind: str,
    description: str,
    scenario: dict,
    base_status: str,
    reference_status: str,
    mutant_status: str,
    reference_disposition: str,
    failure_flags: list[str],
    missing_gates: list[str],
    identity_profile: str | None = None,
) -> dict:
    reference_high = STATUS_RANK[reference_status] >= NORMATIVE
    mutant_high = STATUS_RANK[mutant_status] >= NORMATIVE
    invalid_promotion = STATUS_RANK[mutant_status] > STATUS_RANK[reference_status]
    false_negative = reference_high and not mutant_high
    classification_error = invalid_promotion or false_negative
    row = {
        "mutant": mutant,
        "kind": kind,
        "description": description,
        "scenario_id": scenario["id"],
        "source_path": scenario.get("_source_path"),
        "base_status": base_status,
        "reference_status": reference_status,
        "mutant_status": mutant_status,
        "reference_disposition": reference_disposition,
        "reference_high": reference_high,
        "mutant_high": mutant_high,
        "invalid_promotion": invalid_promotion,
        "false_negative": false_negative,
        "classification_error": classification_error,
        "failure_flags": failure_flags,
        "missing_gates": missing_gates,
    }
    if identity_profile is not None:
        row["identity_profile"] = identity_profile
    return row


def _has_complete_metrics(scenario: dict, _result) -> bool:
    metrics = scenario.get("upstream_metrics") or {}
    return all(isinstance(metrics.get(key), (int, float)) for key in ("precision", "recall", "f1"))


def _without_evidence_packet(scenario: dict) -> dict:
    variant = copy.deepcopy(scenario)
    variant.pop("evidence_packet", None)
    return variant


def _with_nonprocedural_source_tags(scenario: dict) -> dict:
    variant = copy.deepcopy(scenario)
    for link in variant.get("evidence_packet", {}).get("output_links", []):
        link["source_tag"] = "needs_verification"
    return variant


def _without_high_authority(scenario: dict) -> dict:
    variant = copy.deepcopy(scenario)
    authority_sets = variant.setdefault("authority_sets", {})
    authority_sets["high_authority"] = []
    authority_sets["retrieved_high_authority"] = []
    return variant


def _without_counter_material(scenario: dict) -> dict:
    variant = copy.deepcopy(scenario)
    authority_sets = variant.setdefault("authority_sets", {})
    authority_sets.setdefault("counter_or_limiting", ["__counter_material_required__"])
    authority_sets["retrieved_counter_or_limiting"] = ["__omitted_counter_material__"]
    variant.setdefault("counter_authority", {})["retrieved"] = ["__omitted_counter_material__"]
    variant.pop("counter_material_complete", None)
    return variant


def _without_review_gate(scenario: dict) -> dict:
    variant = copy.deepcopy(scenario)
    variant.pop("review_gate", None)
    return variant


def _without_jurisdiction_assumptions(scenario: dict) -> dict:
    variant = copy.deepcopy(scenario)
    variant.setdefault("review_gate", {})["jurisdiction_assumptions"] = []
    return variant


def _with_back_office_role(scenario: dict) -> dict:
    variant = copy.deepcopy(scenario)
    variant["system_role"] = "back_office_tool"
    return variant


def _with_failure_cap(scenario: dict) -> dict:
    variant = copy.deepcopy(scenario)
    flags = set(variant.get("failure_flags", []))
    flags.add("summary_distortion")
    variant["failure_flags"] = sorted(flags)
    return variant


def _without_decision_adoption(scenario: dict) -> dict:
    variant = copy.deepcopy(scenario)
    gate = variant.setdefault("review_gate", {})
    gate["adoption_reasons_recorded"] = False
    gate["contestation_recorded"] = False
    return variant


def _by_mutant(rows: list[dict]) -> dict[str, dict]:
    buckets: dict[str, dict] = {}
    for row in rows:
        bucket = buckets.setdefault(
            row["mutant"],
            {
                "kind": row["kind"],
                "description": row["description"],
                "evaluation_count": 0,
                "classification_error_count": 0,
                "invalid_promotion_count": 0,
                "false_negative_count": 0,
                "killed": False,
                "examples": [],
            },
        )
        bucket["evaluation_count"] += 1
        bucket["classification_error_count"] += int(row["classification_error"])
        bucket["invalid_promotion_count"] += int(row["invalid_promotion"])
        bucket["false_negative_count"] += int(row["false_negative"])
        bucket["killed"] = bucket["killed"] or row["classification_error"]
        if row["classification_error"] and len(bucket["examples"]) < 5:
            bucket["examples"].append(
                {
                    "scenario_id": row["scenario_id"],
                    "reference_status": row["reference_status"],
                    "mutant_status": row["mutant_status"],
                }
            )
    return buckets


def _format_report(payload: dict) -> str:
    lines = [
        "# Policy Mutation Analysis",
        "",
        f"Scenario packets: {payload['scenario_count']}",
        f"Qualified packets: {payload['qualified_scenario_count']}",
        f"Decision-support packets: {payload['decision_scenario_count']}",
        f"Policy mutants: {payload['killed_mutant_count']}/{payload['mutant_count']} killed",
        f"Mutation evaluations: {payload['evaluation_count']}",
        f"Classification errors: {payload['classification_error_count']}",
        f"Invalid promotions: {payload['invalid_promotion_count']}",
        f"False negatives: {payload['false_negative_count']}",
        "",
        "| Mutant | Kind | Evaluations | Errors | Invalid promotions | False negatives | Killed |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for mutant in payload["mutants"]:
        lines.append(
            f"| {mutant['mutant']} | {mutant['kind']} | {mutant['evaluation_count']} | "
            f"{mutant['classification_error_count']} | {mutant['invalid_promotion_count']} | "
            f"{mutant['false_negative_count']} | {mutant['killed']} |"
        )
    survived = [mutant for mutant in payload["mutants"] if not mutant["killed"]]
    if survived:
        lines.extend(["", "## Survived Mutants", ""])
        for mutant in survived:
            lines.append(f"- {mutant['mutant']}: {mutant['description']}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
