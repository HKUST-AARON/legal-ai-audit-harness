from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))

from audit_harness.model import STATUS_RANK, StatusPolicy, evaluate_scenario

RESULTS = ROOT / "experiments" / "full_validation" / "results"
BASE_VALIDATION_UNITS = 343
THRESHOLDS = [8, 9, 10, 11, 12]

SUITES = [
    {
        "id": "stress_tests",
        "label": "Protocol stress scenarios",
        "path": ROOT / "examples" / "scenarios",
        "out": ROOT / "experiments" / "stress_tests" / "results" / "stress_test_experiment.md",
        "json_out": ROOT / "experiments" / "stress_tests" / "results" / "stress_test_experiment.json",
        "validation_units": "10 stress scenarios",
        "finding": "Tests downgrade, withdrawal, decision-support and high-recall-but-blocked behavior.",
    },
    {
        "id": "real_cases",
        "label": "Public legal-record metadata",
        "path": ROOT / "experiments" / "real_cases" / "scenarios",
        "out": ROOT / "experiments" / "real_cases" / "results" / "real_case_experiment.md",
        "json_out": ROOT / "experiments" / "real_cases" / "results" / "real_case_experiment.json",
        "validation_units": "120 public metadata records",
        "finding": "Tests source reconstruction across six public legal-record sources.",
    },
    {
        "id": "public_system_outputs",
        "label": "Public legal-system outputs",
        "path": ROOT / "experiments" / "public_system_outputs" / "scenarios",
        "out": ROOT / "experiments" / "public_system_outputs" / "results" / "public_system_output_experiment.md",
        "json_out": ROOT / "experiments" / "public_system_outputs" / "results" / "public_system_output_experiment.json",
        "validation_units": "60 visible public-system records",
        "finding": "Tests ordered real upstream legal-output reconstruction.",
    },
    {
        "id": "issue_public_outputs",
        "label": "Issue-specific public output/source packets",
        "path": ROOT / "experiments" / "issue_public_outputs" / "scenarios",
        "out": ROOT / "experiments" / "issue_public_outputs" / "results" / "issue_public_output_experiment.md",
        "json_out": ROOT / "experiments" / "issue_public_outputs" / "results" / "issue_public_output_experiment.json",
        "validation_units": "19 issue-specific public output/source records",
        "finding": "Tests public issue-search outputs and a source-bound public-source packet against high-authority and counter-material requirements.",
    },
    {
        "id": "public_retrieval_benchmark",
        "label": "Public retrieval benchmark",
        "path": ROOT / "experiments" / "public_retrieval_benchmark" / "scenarios",
        "out": ROOT / "experiments" / "public_retrieval_benchmark" / "results" / "public_retrieval_benchmark.md",
        "json_out": ROOT / "experiments" / "public_retrieval_benchmark" / "results" / "public_retrieval_benchmark.json",
        "validation_units": "99 public search result records",
        "finding": "Tests true public search outputs against issue-defined high-authority and counter-material gold sets.",
    },
    {
        "id": "ai_outputs",
        "label": "Raw Codex GPT-5.5 xhigh outputs",
        "path": ROOT / "experiments" / "ai_outputs" / "scenarios",
        "out": ROOT / "experiments" / "ai_outputs" / "results" / "ai_output_experiment.md",
        "json_out": ROOT / "experiments" / "ai_outputs" / "results" / "ai_output_experiment.json",
        "validation_units": "10 raw model outputs",
        "finding": "Tests whether strong authority coverage without source binding remains procedurally capped.",
    },
    {
        "id": "issue_gold_sets",
        "label": "Issue-defined positive controls",
        "path": ROOT / "experiments" / "issue_gold_sets" / "scenarios",
        "out": ROOT / "experiments" / "issue_gold_sets" / "results" / "issue_gold_set_experiment.md",
        "json_out": ROOT / "experiments" / "issue_gold_sets" / "results" / "issue_gold_set_experiment.json",
        "validation_units": "5 curated issue packets",
        "finding": "Tests normative material screening with source-bound high-authority and counter-material sets.",
    },
    {
        "id": "issue_ablations",
        "label": "Issue-defined ablations",
        "path": ROOT / "experiments" / "issue_ablations" / "scenarios",
        "out": ROOT / "experiments" / "issue_ablations" / "results" / "issue_ablation_experiment.md",
        "json_out": ROOT / "experiments" / "issue_ablations" / "results" / "issue_ablation_experiment.json",
        "validation_units": "20 issue-packet ablations",
        "finding": "Tests whether high-authority omissions, counter-material suppression, unverified source tags and missing adoption gates trigger the expected caps.",
    },
]


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    _run([sys.executable, "scripts/collect_real_cases.py"])
    _run([sys.executable, "scripts/collect_public_system_outputs.py"])
    _run([sys.executable, "scripts/collect_issue_public_outputs.py"])
    _run([sys.executable, "scripts/collect_public_retrieval_benchmark.py"])
    _run([sys.executable, "scripts/build_issue_ablations.py"])
    _run([sys.executable, "scripts/build_blind_coding_packets.py"])

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

    threshold_sensitivity = _threshold_sensitivity(_load_all_scenarios())
    threshold_evaluations = threshold_sensitivity["scenario_count"] * len(threshold_sensitivity["runs"])
    payload = {
        "suite_count": len(rows),
        "scenario_files": sum(row["scenario_count"] for row in rows if "expected_passed" in row),
        "recoded_evaluations": robustness_payload["recoded_evaluations"],
        "blind_coding_evaluations": 0 if blind_coding_payload is None else blind_coding_payload["packet_count"] * blind_coding_payload["coder_count"],
        "threshold_sensitivity_evaluations": threshold_evaluations,
        "total_evaluation_rows": BASE_VALIDATION_UNITS
        + robustness_payload["recoded_evaluations"]
        + (0 if blind_coding_payload is None else blind_coding_payload["packet_count"] * blind_coding_payload["coder_count"])
        + threshold_evaluations,
        "validation_units": {
            "stress_scenarios": 10,
            "public_metadata_records": 120,
            "public_system_records": 60,
            "public_retrieval_records": 99,
            "raw_model_outputs": 10,
            "issue_public_records": 19,
            "issue_gold_sets": 5,
            "issue_ablations": 20,
            "annotation_recodings": robustness_payload["recoded_evaluations"],
            "blind_coding_packets": 0 if blind_coding_payload is None else blind_coding_payload["packet_count"],
            "threshold_sensitivity_evaluations": threshold_evaluations,
            "total": BASE_VALIDATION_UNITS,
        },
        "expected_passed": sum(row["expected_passed"] for row in rows if "expected_passed" in row),
        "expected_total": sum(row["scenario_count"] for row in rows if "expected_passed" in row),
        "high_upstream_but_blocked": sum(
            row["high_upstream_but_blocked"]
            for row in rows
            if row.get("high_upstream_but_blocked") is not None
        ),
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
        "validation_units": suite["validation_units"],
        "scenario_count": summary["scenario_count"],
        "expected_passed": summary["expected_passed"],
        "mean_audit_score": summary["mean_audit_score"],
        "mean_upstream_recall": summary["mean_upstream_recall"],
        "high_upstream_but_blocked": summary["high_upstream_but_blocked"],
        "status_distribution": status_distribution,
        "finding": suite["finding"],
    }


def _robustness_row(payload: dict) -> dict:
    return {
        "id": "annotation_robustness",
        "label": "Annotation robustness recoding",
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
        f"{payload['validation_units']['issue_public_records']} issue-specific public output/source records, "
        f"{payload['validation_units']['issue_gold_sets']} issue-defined positive controls, "
        f"{payload['validation_units']['issue_ablations']} issue ablations)",
        f"Strict/lenient recoded evaluations: {payload['recoded_evaluations']}",
        f"Score-blinded coding-pass evaluations: {payload['blind_coding_evaluations']}",
        f"Full-threshold sensitivity evaluations: {payload['threshold_sensitivity_evaluations']}",
        f"Composite validation observations: {payload['total_evaluation_rows']}",
        f"Expected outcomes passed: {payload['expected_passed']}/{payload['expected_total']}",
        f"High-upstream-performance but procedurally blocked scenarios: {payload['high_upstream_but_blocked']}",
        f"Annotation robustness: {payload['annotation_robustness']['all_policy_status_stable']}/{payload['annotation_robustness']['scenario_count']} stable across base, strict and lenient coding policies",
        _blind_coding_summary(payload),
        "",
        "| Suite | Embedded records/items | Files/evals | Rule/stability | Mean score | Mean recall | Blocked high-upstream | Status distribution |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["suites"]:
        status_distribution = ", ".join(f"{status}: {count}" for status, count in sorted(row["status_distribution"].items()))
        rule_or_stability = row["rule_pass"] if "rule_pass" in row else f"{row['expected_passed']}/{row['scenario_count']}"
        lines.append(
            "| "
            + " | ".join(
                [
                    row["label"],
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


def _metric(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


if __name__ == "__main__":
    raise SystemExit(main())
