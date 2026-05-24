from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))

from audit_harness.model import STATUS_RANK, StatusPolicy, evaluate_scenario

RESULTS = ROOT / "experiments" / "full_validation" / "results"
THRESHOLDS = [8, 9, 10, 11, 12]

SUITES = [
    {
        "id": "stress_tests",
        "label": "Protocol stress scenarios",
        "path": ROOT / "examples" / "scenarios",
        "out": ROOT / "experiments" / "stress_tests" / "results" / "stress_test_experiment.md",
        "json_out": ROOT / "experiments" / "stress_tests" / "results" / "stress_test_experiment.json",
        "unit_label": "stress scenarios",
        "evidence_class": "construct test",
        "finding": "Tests downgrade, withdrawal, decision-support and high-recall-but-blocked behavior.",
    },
    {
        "id": "real_cases",
        "label": "Public legal-record metadata",
        "path": ROOT / "experiments" / "real_cases" / "scenarios",
        "out": ROOT / "experiments" / "real_cases" / "results" / "real_case_experiment.md",
        "json_out": ROOT / "experiments" / "real_cases" / "results" / "real_case_experiment.json",
        "unit_label": "public metadata records",
        "evidence_class": "public-source reconstruction",
        "finding": "Tests source reconstruction across six public legal-record sources.",
    },
    {
        "id": "public_system_outputs",
        "label": "Public legal-system outputs",
        "path": ROOT / "experiments" / "public_system_outputs" / "scenarios",
        "out": ROOT / "experiments" / "public_system_outputs" / "results" / "public_system_output_experiment.md",
        "json_out": ROOT / "experiments" / "public_system_outputs" / "results" / "public_system_output_experiment.json",
        "unit_label": "visible public-system records",
        "evidence_class": "public-output audit",
        "finding": "Tests ordered real upstream legal-output reconstruction.",
    },
    {
        "id": "issue_public_outputs",
        "label": "Issue-specific public output/source packets",
        "path": ROOT / "experiments" / "issue_public_outputs" / "scenarios",
        "out": ROOT / "experiments" / "issue_public_outputs" / "results" / "issue_public_output_experiment.md",
        "json_out": ROOT / "experiments" / "issue_public_outputs" / "results" / "issue_public_output_experiment.json",
        "unit_label": "issue-specific public output/source records",
        "evidence_class": "mixed public-output/source audit",
        "finding": "Tests public issue-search outputs and a source-bound public-source packet against high-authority and counter-material requirements.",
    },
    {
        "id": "public_retrieval_benchmark",
        "label": "Endpoint-matched public retrieval benchmark",
        "path": ROOT / "experiments" / "public_retrieval_benchmark" / "scenarios",
        "out": ROOT / "experiments" / "public_retrieval_benchmark" / "results" / "public_retrieval_benchmark.md",
        "json_out": ROOT / "experiments" / "public_retrieval_benchmark" / "results" / "public_retrieval_benchmark.json",
        "unit_label": "public search result records",
        "evidence_class": "endpoint-compatible public-output benchmark",
        "finding": "Tests public case-law or known-item outputs against authority sets that the endpoint is capable of returning, while recording mixed-authority gaps separately.",
    },
    {
        "id": "ai_outputs",
        "label": "Raw Codex GPT-5.5 xhigh outputs",
        "path": ROOT / "experiments" / "ai_outputs" / "scenarios",
        "out": ROOT / "experiments" / "ai_outputs" / "results" / "ai_output_experiment.md",
        "json_out": ROOT / "experiments" / "ai_outputs" / "results" / "ai_output_experiment.json",
        "unit_label": "raw model outputs",
        "evidence_class": "model-output audit",
        "finding": "Tests whether strong authority coverage without source binding remains procedurally capped.",
    },
    {
        "id": "model_output_repairs",
        "label": "Source-supported model-output repairs",
        "path": ROOT / "experiments" / "model_output_repairs" / "scenarios",
        "out": ROOT / "experiments" / "model_output_repairs" / "results" / "model_output_repair_experiment.md",
        "json_out": ROOT / "experiments" / "model_output_repairs" / "results" / "model_output_repair_experiment.json",
        "unit_label": "source-supported model-output variants",
        "evidence_class": "model-output intervention",
        "finding": "Tests whether the same model outputs can qualify after manifest, locator, issue-set and hashed source-support evidence validation.",
    },
    {
        "id": "model_output_evidence_ladder",
        "label": "Model-output evidence ladder",
        "path": ROOT / "experiments" / "model_output_evidence_ladder" / "scenarios",
        "out": ROOT / "experiments" / "model_output_evidence_ladder" / "results" / "model_output_evidence_ladder_experiment.md",
        "json_out": ROOT / "experiments" / "model_output_evidence_ladder" / "results" / "model_output_evidence_ladder_experiment.json",
        "unit_label": "evidence-ladder model-output variants",
        "evidence_class": "controlled model-output intervention",
        "finding": "Tests the same model outputs across raw, source-bound, counter-material, contestability, logging, authorized-adoption and unauthorized-action conditions.",
    },
    {
        "id": "model_output_adversarial",
        "label": "Adversarial source-support repairs",
        "path": ROOT / "experiments" / "model_output_adversarial" / "scenarios",
        "out": ROOT / "experiments" / "model_output_adversarial" / "results" / "model_output_adversarial_experiment.md",
        "json_out": ROOT / "experiments" / "model_output_adversarial" / "results" / "model_output_adversarial_experiment.json",
        "unit_label": "adversarial source-support variants",
        "evidence_class": "negative-control model-output validation",
        "finding": "Tests whether source-support repair gates reject locator mismatches, unsupported claims, contradiction patterns, out-of-manifest sources, missing output links and counter-material omissions.",
    },
    {
        "id": "issue_gold_sets",
        "label": "Mixed-authority public source-screening packets",
        "path": ROOT / "experiments" / "issue_gold_sets" / "scenarios",
        "out": ROOT / "experiments" / "issue_gold_sets" / "results" / "issue_gold_set_experiment.md",
        "json_out": ROOT / "experiments" / "issue_gold_sets" / "results" / "issue_gold_set_experiment.json",
        "unit_label": "curated issue packets",
        "evidence_class": "mixed-authority construct test",
        "finding": "Tests normative material screening with mixed statute/case/source packets rather than single-endpoint public search results.",
    },
    {
        "id": "issue_ablations",
        "label": "Issue-defined ablations",
        "path": ROOT / "experiments" / "issue_ablations" / "scenarios",
        "out": ROOT / "experiments" / "issue_ablations" / "results" / "issue_ablation_experiment.md",
        "json_out": ROOT / "experiments" / "issue_ablations" / "results" / "issue_ablation_experiment.json",
        "unit_label": "issue-packet ablations",
        "evidence_class": "negative-control construct test",
        "finding": "Tests whether high-authority omissions, counter-material suppression, unverified source tags and missing adoption gates trigger the expected caps.",
    },
]


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    _run([sys.executable, "scripts/collect_real_cases.py"])
    _run([sys.executable, "scripts/collect_public_system_outputs.py"])
    _run([sys.executable, "scripts/collect_issue_public_outputs.py"])
    _run([sys.executable, "scripts/collect_public_retrieval_benchmark.py"])
    _run([sys.executable, "scripts/build_model_output_repairs.py"])
    _run([sys.executable, "scripts/build_model_output_evidence_ladder.py"])
    _run([sys.executable, "scripts/build_model_output_adversarial.py"])
    _run([sys.executable, "scripts/build_issue_ablations.py"])
    _run([sys.executable, "scripts/build_blind_coding_packets.py"])
    _run([sys.executable, "scripts/verify_model_output_transcripts.py"])
    _run([sys.executable, "scripts/verify_source_text_anchors.py"])

    rows = []
    for suite in SUITES:
        _run(
            [
                sys.executable,
                "-m",
                "audit_harness.cli",
                "experiment",
                str(suite["path"].relative_to(ROOT)),
                "--out",
                str(suite["out"].relative_to(ROOT)),
                "--json-out",
                str(suite["json_out"].relative_to(ROOT)),
            ]
        )
        payload = json.loads(suite["json_out"].read_text(encoding="utf-8"))
        rows.append(_suite_row(suite, payload))
    source_text_payload = json.loads(
        (ROOT / "experiments" / "source_text_verification" / "results" / "source_text_anchor_verification.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_source_text_row(source_text_payload))
    transcript_payload = json.loads(
        (ROOT / "experiments" / "ai_outputs" / "results" / "model_output_transcript_verification.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_model_transcript_row(transcript_payload))

    _run(
        [
            sys.executable,
            "-m",
            "audit_harness.cli",
            "sensitivity",
            "examples/scenarios",
            "--out",
            "experiments/stress_tests/results/sensitivity_report.md",
            "--json-out",
            "experiments/stress_tests/results/sensitivity_report.json",
        ]
    )
    _run(
        [
            sys.executable,
            "-m",
            "audit_harness.cli",
            "sensitivity",
            "experiments/ai_outputs/scenarios",
            "--out",
            "experiments/ai_outputs/results/ai_output_sensitivity.md",
            "--json-out",
            "experiments/ai_outputs/results/ai_output_sensitivity.json",
        ]
    )
    _run([sys.executable, "scripts/run_annotation_robustness.py"])
    robustness_payload = json.loads(
        (ROOT / "experiments" / "annotation_robustness" / "results" / "annotation_robustness.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(_robustness_row(robustness_payload))
    blind_coding_payload = None
    blind_annotation_files = sorted((ROOT / "experiments" / "blind_coding" / "annotations").glob("coder_*.json"))
    if len(blind_annotation_files) >= 2:
        _run([sys.executable, "scripts/run_blind_coding_study.py"])
        blind_coding_payload = json.loads(
            (ROOT / "experiments" / "blind_coding" / "results" / "blind_coding_study.json").read_text(
                encoding="utf-8"
            )
        )
        rows.append(_blind_coding_row(blind_coding_payload))

    validation_units = _validation_units()
    base_validation_units = validation_units["total"]
    threshold_sensitivity = _threshold_sensitivity(_load_all_scenarios())
    threshold_evaluations = threshold_sensitivity["scenario_count"] * len(threshold_sensitivity["runs"])
    validation_units_payload = dict(validation_units)
    validation_units_payload.update(
        {
            "annotation_recodings": robustness_payload["recoded_evaluations"],
            "blind_coding_packets": 0 if blind_coding_payload is None else blind_coding_payload["packet_count"],
            "threshold_sensitivity_evaluations": threshold_evaluations,
            "source_text_anchor_checks": source_text_payload["support_item_count"],
            "source_text_anchor_verified": source_text_payload["support_items_verified"],
            "model_output_transcript_locator_checks": transcript_payload["locator_count"],
            "model_output_transcript_locators_verified": transcript_payload["locators_verified"],
        }
    )
    payload = {
        "suite_count": len(rows),
        "scenario_files": sum(row["scenario_count"] for row in rows if "expected_passed" in row),
        "recoded_evaluations": robustness_payload["recoded_evaluations"],
        "blind_coding_evaluations": 0 if blind_coding_payload is None else blind_coding_payload["packet_count"] * blind_coding_payload["coder_count"],
        "threshold_sensitivity_evaluations": threshold_evaluations,
        "source_text_anchor_evaluations": source_text_payload["support_item_count"],
        "model_output_transcript_evaluations": transcript_payload["locator_count"],
        "total_evaluation_rows": base_validation_units
        + source_text_payload["support_item_count"]
        + transcript_payload["locator_count"]
        + robustness_payload["recoded_evaluations"]
        + (0 if blind_coding_payload is None else blind_coding_payload["packet_count"] * blind_coding_payload["coder_count"])
        + threshold_evaluations,
        "validation_units": validation_units_payload,
        "expected_passed": sum(row["expected_passed"] for row in rows if "expected_passed" in row),
        "expected_total": sum(row["scenario_count"] for row in rows if "expected_passed" in row),
        "high_upstream_but_blocked": sum(
            row["high_upstream_but_blocked"]
            for row in rows
            if row.get("high_upstream_but_blocked") is not None
        ),
        "blocked_reason_distribution": _blocked_reason_distribution(rows),
        "annotation_robustness": {
            "all_policy_status_stable": robustness_payload["all_policy_status_stable"],
            "scenario_count": robustness_payload["scenario_count"],
            "weighted_status_agreement_base_strict": robustness_payload["weighted_status_agreement_base_strict"],
            "weighted_status_agreement_base_lenient": robustness_payload["weighted_status_agreement_base_lenient"],
        },
        "blind_coding": None
        if blind_coding_payload is None
        else {
            "packet_count": blind_coding_payload["packet_count"],
            "coder_count": blind_coding_payload["coder_count"],
            "status_disagreement_count": blind_coding_payload["status_disagreement_count"],
            "pairwise_status": blind_coding_payload["pairwise_status"],
            "base_status_agreement": blind_coding_payload["base_status_agreement"],
        },
        "threshold_sensitivity": threshold_sensitivity,
        "source_text_verification": {
            "record_count": source_text_payload["record_count"],
            "records_with_text_snapshot": source_text_payload["records_with_text_snapshot"],
            "support_item_count": source_text_payload["support_item_count"],
            "support_items_verified": source_text_payload["support_items_verified"],
            "verified_ratio": source_text_payload["verified_ratio"],
        },
        "model_output_transcript_verification": {
            "scenario_count": transcript_payload["scenario_count"],
            "scenario_sections_verified": transcript_payload["scenario_sections_verified"],
            "output_unit_count": transcript_payload["output_unit_count"],
            "locator_count": transcript_payload["locator_count"],
            "locators_verified": transcript_payload["locators_verified"],
            "all_locators_verified": transcript_payload["all_locators_verified"],
        },
        "suites": rows,
    }
    (RESULTS / "full_validation_report.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    (RESULTS / "full_validation_report.md").write_text(_format_report(payload) + "\n", encoding="utf-8")
    print(_format_report(payload))
    return 0


def _run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def _load_all_scenarios() -> list[dict]:
    scenarios = []
    for suite in SUITES:
        for path in sorted(suite["path"].glob("*.json")):
            scenario = json.loads(path.read_text(encoding="utf-8"))
            scenario["_source_path"] = str(path.relative_to(ROOT))
            scenarios.append(scenario)
    return scenarios


def _validation_units() -> dict[str, int]:
    counts = {
        "stress_scenarios": _scenario_count(ROOT / "examples" / "scenarios"),
        "public_metadata_records": _output_unit_count(ROOT / "experiments" / "real_cases" / "scenarios"),
        "public_system_records": _output_unit_count(ROOT / "experiments" / "public_system_outputs" / "scenarios"),
        "public_retrieval_records": _output_unit_count(ROOT / "experiments" / "public_retrieval_benchmark" / "scenarios"),
        "raw_model_outputs": _scenario_count(ROOT / "experiments" / "ai_outputs" / "scenarios"),
        "source_bound_model_outputs": _scenario_count(ROOT / "experiments" / "model_output_repairs" / "scenarios"),
        "evidence_ladder_model_outputs": _scenario_count(ROOT / "experiments" / "model_output_evidence_ladder" / "scenarios"),
        "adversarial_model_outputs": _scenario_count(ROOT / "experiments" / "model_output_adversarial" / "scenarios"),
        "issue_public_records": _output_unit_count(ROOT / "experiments" / "issue_public_outputs" / "scenarios"),
        "issue_gold_sets": _scenario_count(ROOT / "experiments" / "issue_gold_sets" / "scenarios"),
        "issue_ablations": _scenario_count(ROOT / "experiments" / "issue_ablations" / "scenarios"),
    }
    counts["total"] = sum(counts.values())
    return counts


def _scenario_count(path: Path) -> int:
    return len(list(path.glob("*.json")))


def _output_unit_count(path: Path) -> int:
    total = 0
    for scenario_path in path.glob("*.json"):
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
        total += len(scenario.get("evidence_packet", {}).get("output_units", []))
    return total


def _threshold_sensitivity(scenarios: list[dict]) -> dict:
    base_policy = StatusPolicy(normative_threshold=9, decision_threshold=10)
    base = {
        scenario["id"]: evaluate_scenario(scenario, base_policy).allowed_status
        for scenario in scenarios
    }
    runs = []
    for threshold in THRESHOLDS:
        policy = StatusPolicy(normative_threshold=threshold, decision_threshold=max(10, threshold + 1))
        distribution: dict[str, int] = {}
        flips = promotions = demotions = 0
        for scenario in scenarios:
            status = evaluate_scenario(scenario, policy).allowed_status
            distribution[status] = distribution.get(status, 0) + 1
            base_status = base[scenario["id"]]
            if status != base_status:
                flips += 1
                if STATUS_RANK[status] > STATUS_RANK[base_status]:
                    promotions += 1
                else:
                    demotions += 1
        runs.append(
            {
                "normative_threshold": threshold,
                "decision_threshold": policy.decision_threshold,
                "status_distribution": distribution,
                "status_flips_from_default": flips,
                "promotions_from_default": promotions,
                "demotions_from_default": demotions,
            }
        )
    return {
        "scenario_count": len(scenarios),
        "default_policy": {"normative_threshold": 9, "decision_threshold": 10},
        "runs": runs,
    }


def _suite_row(suite: dict, payload: dict) -> dict:
    status_distribution: dict[str, int] = {}
    for result in payload["results"]:
        status = result["allowed_status"]
        status_distribution[status] = status_distribution.get(status, 0) + 1
    summary = payload["summary"]
    return {
        "id": suite["id"],
        "label": suite["label"],
        "evidence_class": suite["evidence_class"],
        "validation_units": _suite_validation_units(suite),
        "scenario_count": summary["scenario_count"],
        "expected_passed": summary["expected_passed"],
        "mean_audit_score": summary["mean_audit_score"],
        "mean_upstream_recall": summary["mean_upstream_recall"],
        "high_upstream_but_blocked": summary["high_upstream_but_blocked"],
        "blocked_reason_distribution": summary.get("blocked_reason_distribution", {}),
        "status_distribution": status_distribution,
        "finding": suite["finding"],
    }


def _suite_validation_units(suite: dict) -> str:
    path = suite["path"]
    count = _scenario_count(path) if suite["unit_label"] in {
        "stress scenarios",
        "raw model outputs",
        "source-supported model-output variants",
        "evidence-ladder model-output variants",
        "adversarial source-support variants",
        "curated issue packets",
        "issue-packet ablations",
    } else _output_unit_count(path)
    return f"{count} {suite['unit_label']}"


def _robustness_row(payload: dict) -> dict:
    return {
        "id": "annotation_robustness",
        "label": "Annotation robustness recoding",
        "evidence_class": "coding robustness",
        "validation_units": f"{payload['recoded_evaluations']} strict/lenient recoded evaluations",
        "scenario_count": payload["scenario_count"],
        "rule_pass": f"{payload['all_policy_status_stable']}/{payload['scenario_count']} stable across all policies",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "base_vs_strict_weighted_agreement": round(payload["weighted_status_agreement_base_strict"], 2),
            "base_vs_lenient_weighted_agreement": round(payload["weighted_status_agreement_base_lenient"], 2),
        },
        "finding": "Tests whether status allocation survives strict and lenient recoding of the same evidence packets.",
    }


def _blind_coding_row(payload: dict) -> dict:
    first_pair = payload["pairwise_status"][0]
    base_exact = min(item["exact_status_agreement"] for item in payload["base_status_agreement"].values())
    base_weighted = min(item["weighted_status_agreement"] for item in payload["base_status_agreement"].values())
    return {
        "id": "blind_coding",
        "label": "Score-blinded dual coding",
        "evidence_class": "codebook reproducibility",
        "validation_units": f"{payload['packet_count']} packets x {payload['coder_count']} coding passes",
        "scenario_count": payload["packet_count"],
        "rule_pass": f"{first_pair['exact_status_agreement']:.2f} coder agreement; {base_exact:.2f} min base agreement",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "coder_weighted_status_agreement": round(first_pair["weighted_status_agreement"], 2),
            "min_base_weighted_status_agreement": round(base_weighted, 2),
            "status_disagreements": payload["status_disagreement_count"],
        },
        "finding": "Tests whether score-blinded coders agree with each other and how far their status assignments track the base harness allocation.",
    }


def _source_text_row(payload: dict) -> dict:
    return {
        "id": "source_text_verification",
        "label": "Public source-text anchors",
        "evidence_class": "external source-grounding check",
        "validation_units": f"{payload['support_item_count']} public source-support anchor checks",
        "scenario_count": payload["support_item_count"],
        "rule_pass": f"{payload['support_items_verified']}/{payload['support_item_count']} verified",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "records_with_text_snapshot": payload["records_with_text_snapshot"],
            "verified_ratio": payload["verified_ratio"],
        },
        "finding": "Checks issue-manifest support terms against extracted public source text snapshots to reduce manifest-only source-support circularity.",
    }


def _model_transcript_row(payload: dict) -> dict:
    return {
        "id": "model_output_transcript_verification",
        "label": "Model-output transcript anchors",
        "evidence_class": "raw-output provenance check",
        "validation_units": f"{payload['locator_count']} raw transcript locator checks",
        "scenario_count": payload["locator_count"],
        "rule_pass": f"{payload['locators_verified']}/{payload['locator_count']} verified",
        "mean_audit_score": None,
        "mean_upstream_recall": None,
        "high_upstream_but_blocked": None,
        "status_distribution": {
            "scenario_sections_verified": payload["scenario_sections_verified"],
            "output_units": payload["output_unit_count"],
            "all_locators_verified": payload["all_locators_verified"],
        },
        "finding": "Checks that raw model-output scenario locators are anchored in the committed transcript sections.",
    }


def _format_report(payload: dict) -> str:
    lines = [
        "# Full Legal AI Audit Harness Validation",
        "",
        f"Validation suites: {payload['suite_count']}",
        f"Scenario files: {payload['scenario_files']}",
        f"Base embedded records/items: {payload['validation_units']['total']} "
        f"({payload['validation_units']['stress_scenarios']} stress scenarios, "
        f"{payload['validation_units']['public_metadata_records']} public metadata records, "
        f"{payload['validation_units']['public_system_records']} public-system records, "
        f"{payload['validation_units']['public_retrieval_records']} public retrieval records, "
        f"{payload['validation_units']['raw_model_outputs']} raw model outputs, "
        f"{payload['validation_units']['source_bound_model_outputs']} source-supported model-output variants, "
        f"{payload['validation_units']['evidence_ladder_model_outputs']} evidence-ladder model-output variants, "
        f"{payload['validation_units']['adversarial_model_outputs']} adversarial source-support variants, "
        f"{payload['validation_units']['issue_public_records']} issue-specific public output/source records, "
        f"{payload['validation_units']['issue_gold_sets']} mixed-authority source-screening packets, "
        f"{payload['validation_units']['issue_ablations']} issue ablations)",
        f"Strict/lenient recoded evaluations: {payload['recoded_evaluations']}",
        f"Score-blinded coding-pass evaluations: {payload['blind_coding_evaluations']}",
        f"Full-threshold sensitivity evaluations: {payload['threshold_sensitivity_evaluations']}",
        f"Public source-text anchor checks: {payload['source_text_verification']['support_items_verified']}/{payload['source_text_verification']['support_item_count']} verified across {payload['source_text_verification']['records_with_text_snapshot']} records with text snapshots",
        f"Model-output transcript locator checks: {payload['model_output_transcript_verification']['locators_verified']}/{payload['model_output_transcript_verification']['locator_count']} verified across {payload['model_output_transcript_verification']['scenario_sections_verified']} raw transcript sections",
        f"Derived robustness evaluations: {payload['total_evaluation_rows'] - payload['validation_units']['total']}",
        f"Expected outcomes passed: {payload['expected_passed']}/{payload['expected_total']}",
        f"High-upstream-performance but procedurally blocked scenarios: {payload['high_upstream_but_blocked']}",
        "Blocked reason distribution: " + _format_distribution(payload["blocked_reason_distribution"]),
        f"Annotation robustness: {payload['annotation_robustness']['all_policy_status_stable']}/{payload['annotation_robustness']['scenario_count']} stable across base, strict and lenient coding policies",
        _blind_coding_summary(payload),
        "",
        "| Suite | Evidence role | Embedded records/items | Files/evals | Rule/stability | Mean score | Mean recall | Blocked high-upstream | Status distribution |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["suites"]:
        status_distribution = ", ".join(f"{status}: {count}" for status, count in sorted(row["status_distribution"].items()))
        rule_or_stability = row["rule_pass"] if "rule_pass" in row else f"{row['expected_passed']}/{row['scenario_count']}"
        lines.append(
            "| "
            + " | ".join(
                [
                    row["label"],
                    row["evidence_class"],
                    row["validation_units"],
                    str(row["scenario_count"]),
                    rule_or_stability,
                    _metric(row["mean_audit_score"]),
                    _metric(row["mean_upstream_recall"]),
                    "n/a" if row["high_upstream_but_blocked"] is None else str(row["high_upstream_but_blocked"]),
                    status_distribution,
                ]
            )
            + " |"
        )
    lines.extend(["", "## Findings", ""])
    for row in payload["suites"]:
        lines.append(f"- **{row['label']}:** {row['finding']}")
    lines.extend(["", "## Full-Threshold Sensitivity", ""])
    lines.append(
        f"All {payload['threshold_sensitivity']['scenario_count']} scenario packets were re-evaluated under "
        "normative thresholds 8--12."
    )
    lines.extend(
        [
            "",
            "| Normative threshold | Decision threshold | Status flips from default | Promotions | Demotions | Status distribution |",
            "| ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for run in payload["threshold_sensitivity"]["runs"]:
        distribution = ", ".join(
            f"{status}: {count}" for status, count in sorted(run["status_distribution"].items())
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    str(run["normative_threshold"]),
                    str(run["decision_threshold"]),
                    str(run["status_flips_from_default"]),
                    str(run["promotions_from_default"]),
                    str(run["demotions_from_default"]),
                    distribution,
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _blind_coding_summary(payload: dict) -> str:
    if payload["blind_coding"] is None:
        return "Score-blinded coding: not run; fewer than two coder annotation files found"
    first_pair = payload["blind_coding"]["pairwise_status"][0]
    base_exact = min(item["exact_status_agreement"] for item in payload["blind_coding"]["base_status_agreement"].values())
    base_weighted = min(item["weighted_status_agreement"] for item in payload["blind_coding"]["base_status_agreement"].values())
    return (
        f"Score-blinded coding: {payload['blind_coding']['packet_count']} packets, "
        f"{payload['blind_coding']['coder_count']} coding passes, "
        f"{first_pair['exact_status_agreement']:.2f} coder-coder exact agreement, "
        f"{base_exact:.2f} minimum base-coder exact agreement, "
        f"{base_weighted:.2f} minimum base-coder weighted agreement"
    )


def _blocked_reason_distribution(rows: list[dict]) -> dict[str, int]:
    merged: dict[str, int] = {}
    for row in rows:
        for reason, count in row.get("blocked_reason_distribution", {}).items():
            merged[reason] = merged.get(reason, 0) + count
    return merged


def _format_distribution(distribution: dict[str, int]) -> str:
    if not distribution:
        return "none"
    return ", ".join(f"{key}: {value}" for key, value in sorted(distribution.items()))


def _metric(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


if __name__ == "__main__":
    raise SystemExit(main())
