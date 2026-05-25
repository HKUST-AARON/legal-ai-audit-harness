from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "experiments" / "claim_consistency" / "results"


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    payload = json.loads((ROOT / "experiments" / "full_validation" / "results" / "full_validation_report.json").read_text(encoding="utf-8"))
    checks = _checks(payload)
    failures = [check for check in checks if not check["passed"]]
    report = {
        "check_count": len(checks),
        "passed_count": len(checks) - len(failures),
        "failed_count": len(failures),
        "failures": failures,
        "checks": checks,
    }
    markdown = _format_report(report)
    (RESULTS / "claim_consistency_verification.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    (RESULTS / "claim_consistency_verification.md").write_text(markdown + "\n", encoding="utf-8")
    print(markdown)
    return 0 if not failures else 1


def _checks(payload: dict) -> list[dict]:
    units = payload["validation_units"]
    gate = payload["gate_ablation"]
    metric = payload["metric_separation"]
    baseline = payload["baseline_comparison"]
    repair = payload["repair_frontier"]
    source_chain = payload["source_chain_attacks"]
    contestation = payload["contestation_challenges"]
    metamorphic = payload["metamorphic_policy"]
    query_perturbation = payload["query_perturbation"]
    query_portfolio = payload["query_portfolio"]
    jurisdiction = payload["jurisdiction_profile"]
    ranking = payload["ranking_visibility"]
    certificate = payload["status_certificate"]
    policy_constants = payload["policy_constants_replay"]
    uncertainty = payload["annotation_uncertainty"]
    threshold_sensitivity = payload["threshold_sensitivity"]
    blind = payload["blind_coding"]
    blind_pair = blind["pairwise_status"][0]
    blind_base = list(blind["base_status_agreement"].values())
    values = {
        "suite_count": payload["suite_count"],
        "scenario_files": payload["scenario_files"],
        "embedded": units["total"],
        "rows": payload["total_evaluation_rows"],
        "derived": payload["total_evaluation_rows"] - units["total"],
        "formal": units["formal_invariant_checks"],
        "metric": units["metric_separation_evaluations"],
        "metric_resamples": units["metric_statistical_resamples"],
        "metric_bootstrap": metric["bootstrap"]["iterations"],
        "metric_permutation": metric["permutation"]["iterations"],
        "baseline_predictions": units["baseline_comparison_predictions"],
        "baseline_count": baseline["baseline_count"],
        "baseline_best_fp": baseline["best_simplified"]["false_positive"],
        "baseline_full_fp": baseline["full_gate"]["false_positive"],
        "gate": units["gate_ablation_evaluations"],
        "gate_passed": gate["passed_count"],
        "qualified": gate["qualified_scenario_count"],
        "source_chain": source_chain["scenario_count"],
        "source_chain_passed": source_chain["expected_passed"],
        "source_chain_high_blocked": source_chain["high_upstream_but_blocked"],
        "source_chain_reference": source_chain["status_distribution"]["reference_information"],
        "source_chain_no_effect": source_chain["status_distribution"]["no_external_legal_effect"],
        "source_chain_downgrade": source_chain["disposition_distribution"]["downgrade"],
        "source_chain_suspension": source_chain["disposition_distribution"]["suspension"],
        "source_chain_withdrawal": source_chain["disposition_distribution"]["withdrawal"],
        "contestation": contestation["scenario_count"],
        "contestation_passed": contestation["expected_passed"],
        "contestation_high_blocked": contestation["high_upstream_but_blocked"],
        "contestation_valid_blocked": contestation["valid_challenges_blocked"],
        "contestation_unsupported_preserved": contestation["unsupported_controls_preserved"],
        "metamorphic": metamorphic["metamorphic_evaluation_count"],
        "metamorphic_passed": metamorphic["passed_count"],
        "metamorphic_scenarios": metamorphic["scenario_count"],
        "metamorphic_failed": metamorphic["failed_count"],
        "query_perturbation": payload["query_perturbation_evaluations"],
        "query_variants": query_perturbation["query_variant_count"],
        "query_groups": query_perturbation["issue_group_count"],
        "query_status_stable": query_perturbation["status_stable_group_count"],
        "query_authority_unstable": query_perturbation["authority_coverage_unstable_group_count"],
        "query_counter_unstable": query_perturbation["counter_recall_unstable_group_count"],
        "query_record_unstable": query_perturbation["record_set_unstable_group_count"],
        "query_top_unstable": query_perturbation["top_result_unstable_group_count"],
        "query_mean_overlap": query_perturbation["mean_pairwise_record_overlap"],
        "query_portfolio": payload["query_portfolio_evaluations"],
        "query_portfolios": query_portfolio["portfolio_count"],
        "query_portfolio_groups": query_portfolio["issue_group_count"],
        "query_portfolio_qualified": query_portfolio["qualified_portfolio_count"],
        "query_portfolio_full_high": query_portfolio["full_high_authority_portfolio_count"],
        "query_portfolio_full_counter": query_portfolio["full_counter_material_portfolio_count"],
        "query_portfolio_full_screening": query_portfolio["full_screening_material_portfolio_count"],
        "repair": units["repair_frontier_evaluations"],
        "repairable": repair["repairable_count"],
        "blocked_claims": repair["blocked_claim_count"],
        "jurisdiction": units["jurisdiction_profile_evaluations"],
        "jurisdiction_profile_checks": jurisdiction["profile_check_count"],
        "jurisdiction_supported": jurisdiction["profile_supported_count"],
        "jurisdiction_mutations": jurisdiction["counterfactual_evaluation_count"],
        "jurisdiction_mutations_passed": jurisdiction["passed_count"],
        "jurisdiction_qualified": jurisdiction["qualified_status_count"],
        "ranking": units["ranking_visibility_checks"],
        "ranking_window": units["ranking_visibility_window_checks"],
        "ranking_counterfactuals": units["ranking_visibility_counterfactuals"],
        "ranking_passed": ranking["rank_order_passed_count"],
        "ranking_eligible": ranking["eligible_packet_count"],
        "ranking_front_window": ranking["front_window_packet_count"],
        "ranking_visible": ranking["front_window_counter_visible"],
        "ranking_drifted_visible": ranking["counterfactual_front_window_counter_visible"],
        "ranking_median": ranking["median_first_counter_rank"],
        "certificate_checks": units["status_certificate_replay_checks"],
        "certificate_count": certificate["certificate_count"],
        "certificates_verified": certificate["verified_certificate_count"],
        "certificate_passed": certificate["passed_check_count"],
        "policy_constants_checks": policy_constants["check_count"],
        "policy_constants_passed": policy_constants["passed_check_count"],
        "policy_constants_scenarios": policy_constants["scenario_count"],
        "policy_constants_verified": policy_constants["verified_scenario_count"],
        "uncertainty": uncertainty["evaluation_count"],
        "uncertainty_stability": uncertainty["status_stability_rate"],
        "uncertainty_qualified_high": uncertainty["qualified_high_status_stability_rate"],
        "uncertainty_boundary": uncertainty["boundary_scenario_count"],
        "blind_packets": blind["packet_count"],
        "blind_passes": blind["coder_count"],
        "blind_exact": blind_pair["exact_status_agreement"],
        "blind_kappa": blind_pair["cohen_kappa"],
        "blind_weighted_kappa": blind_pair["quadratic_weighted_kappa"],
        "blind_base_exact": min(item["exact_status_agreement"] for item in blind_base),
        "blind_base_weighted": min(item["weighted_status_agreement"] for item in blind_base),
        "blind_base_kappa": min(item["cohen_kappa"] for item in blind_base),
        "blind_base_weighted_kappa": min(item["quadratic_weighted_kappa"] for item in blind_base),
        "blind_min_dimension_kappa": blind["minimum_dimension_kappa"],
        "blind_min_failure_flag_exact": blind["minimum_failure_flag_exact_agreement"],
        "blind_min_missing_gate_exact": blind["minimum_missing_gate_exact_agreement"],
        "blind_base_dimension_min_kappa": blind["base_dimension_min_kappa"],
        "blind_base_dimension_min_kappa_dimension": blind["base_dimension_min_kappa_dimension"],
        "blind_base_dimension_min_kappa_exact": blind["base_dimension_min_kappa_exact_agreement"],
        "blind_base_dimension_min_exact": blind["base_dimension_min_exact_agreement"],
        "blind_base_dimension_min_pabak": blind["base_dimension_min_pabak"],
        "blind_base_dimension_max_delta": blind["base_dimension_max_mean_absolute_delta"],
        "expected_passed": payload["expected_passed"],
        "expected_total": payload["expected_total"],
        "source_verified": units["source_text_anchor_verified"],
        "source_total": units["source_text_anchor_checks"],
        "transcript_verified": units["model_output_transcript_locators_verified"],
        "transcript_total": units["model_output_transcript_locator_checks"],
        "metric_high_recall_blocked": metric["high_recall_blocked"]["count"],
        "metric_high_recall_total": metric["high_recall_blocked"]["denominator"],
        "pdf_pages": _pdf_page_count(ROOT / "manuscript" / "ai_law_case_recommendation_verifiability.pdf"),
    }
    expectations = [
        ("ARTIFACT.md", f"- {values['suite_count']} validation suites"),
        ("ARTIFACT.md", f"- {values['scenario_files']} scenario files"),
        ("ARTIFACT.md", f"- {values['embedded']} embedded records or output items"),
        ("ARTIFACT.md", f"- {_comma(values['rows'])} total evaluation rows"),
        ("ARTIFACT.md", f"- {_comma(values['formal'])}/{_comma(values['formal'])} formal invariant checks passed"),
        ("ARTIFACT.md", f"- {values['metric']} metric-separation evaluations"),
        ("ARTIFACT.md", f"- {_comma(values['metric_bootstrap'])} metric bootstrap resamples and {_comma(values['metric_permutation'])} metric permutation shuffles"),
        ("ARTIFACT.md", f"- {_comma(values['baseline_predictions'])} baseline-rule predictions across {values['baseline_count']} alternative status rules"),
        ("ARTIFACT.md", f"- {values['gate_passed']}/{values['gate']} gate-ablation evaluations passed"),
        ("ARTIFACT.md", f"- {values['source_chain_passed']}/{values['source_chain']} source-chain attack variants passed"),
        ("ARTIFACT.md", f"- {values['contestation_passed']}/{values['contestation']} contestation challenge variants passed"),
        ("ARTIFACT.md", f"- {_comma(values['metamorphic_passed'])}/{_comma(values['metamorphic'])} metamorphic policy tests passed"),
        ("ARTIFACT.md", f"- {values['query_variants']} query-perturbation variants across {values['query_groups']} issue groups; {values['query_status_stable']}/{values['query_groups']} status-stable groups, {values['query_authority_unstable']}/{values['query_groups']} authority-coverage unstable groups and {values['query_record_unstable']}/{values['query_groups']} record-set unstable groups"),
        ("ARTIFACT.md", f"- {values['query_portfolios']} query portfolios plus {values['query_portfolio_groups']} group frontier summaries across {values['query_portfolio_groups']} issue groups; {values['query_portfolio_qualified']}/{values['query_portfolios']} qualified, {values['query_portfolio_full_high']}/{values['query_portfolios']} full high-authority portfolios and {values['query_portfolio_full_counter']}/{values['query_portfolios']} full counter-material portfolios"),
        ("ARTIFACT.md", f"- {values['repairable']}/{values['blocked_claims']} blocked procedural claims repairable across {_comma(values['repair'])} repair-frontier evaluations"),
        ("ARTIFACT.md", f"- {values['jurisdiction_supported']}/{values['jurisdiction_profile_checks']} jurisdiction-profile checks and {values['jurisdiction_mutations_passed']}/{values['jurisdiction_mutations']} profile mutations passed"),
        ("ARTIFACT.md", f"- {values['ranking_window']} rank-window visibility checks over {values['ranking']} high-status claims"),
        ("ARTIFACT.md", f"- {values['ranking_passed']}/{values['ranking_counterfactuals']} rank-order visibility counterfactuals downgraded with coverage preserved"),
        ("ARTIFACT.md", f"- {_comma(values['certificate_passed'])}/{_comma(values['certificate_checks'])} status-certificate replay checks passed over {values['certificate_count']} certificates"),
        ("ARTIFACT.md", f"- {_comma(values['policy_constants_passed'])}/{_comma(values['policy_constants_checks'])} policy-constants replay checks passed"),
        ("ARTIFACT.md", f"- {_comma(values['uncertainty'])} annotation-uncertainty perturbations with {values['uncertainty_stability']:.3f} sample stability"),
        ("ARTIFACT.md", f"- score-blinded coding inter-coder minimum dimension kappa {values['blind_min_dimension_kappa']:.2f}, minimum derived failure-flag exact agreement {values['blind_min_failure_flag_exact']:.2f}, minimum derived missing-gate exact agreement {values['blind_min_missing_gate_exact']:.2f}, weakest base-dimension kappa {values['blind_base_dimension_min_kappa']:.2f} on {values['blind_base_dimension_min_kappa_dimension']}, base-dimension minimum exact agreement {values['blind_base_dimension_min_exact']:.2f}, minimum three-category PABAK {values['blind_base_dimension_min_pabak']:.2f} and maximum mean absolute score drift {values['blind_base_dimension_max_delta']:.2f}"),
        ("ARTIFACT.md", f"- {values['expected_passed']}/{values['expected_total']} scenario-regression expectations passed"),
        ("ARTIFACT.md", f"- {values['source_verified']}/{values['source_total']} public source-text anchors verified"),
        ("ARTIFACT.md", f"- {values['transcript_verified']}/{values['transcript_total']} raw model-output transcript locators verified"),
        ("README.md", f"{values['scenario_files']} scenario files containing {values['embedded']} embedded records/items"),
        ("README.md", f"{_comma(values['formal'])} formal invariant checks"),
        ("README.md", f"{values['metric']} metric-separation evaluations, {_comma(values['metric_resamples'])} metric statistical resamples, {_comma(values['baseline_predictions'])} baseline-rule predictions, {values['gate']} gate-ablation evaluations, {values['source_chain']} source-chain attack variants, {values['contestation']} contestation challenge variants, {_comma(values['metamorphic'])} metamorphic policy tests, {values['query_variants']} query-perturbation variants across {values['query_groups']} issue groups, {values['query_portfolios']} query portfolios plus {values['query_portfolio_groups']} group frontier summaries, {_comma(values['repair'])} repair-frontier evaluations, {values['jurisdiction']} jurisdiction-profile checks, {values['ranking_window']} rank-window visibility checks, {values['ranking_counterfactuals']} rank-order counterfactuals, {_comma(values['certificate_checks'])} status-certificate replay checks and {_comma(values['policy_constants_checks'])} policy-constants replay checks"),
        ("README.md", f"{values['query_variants']} query-perturbation variants across {values['query_groups']} issue groups, {values['query_portfolios']} query portfolios plus {values['query_portfolio_groups']} group frontier summaries"),
        ("README.md", f"{_comma(values['uncertainty'])} score-uncertainty perturbations"),
        ("README.md", f"| Metric separation analysis | {values['metric']} |"),
        ("README.md", f"| Metric statistical robustness | {values['metric_resamples']} |"),
        ("README.md", f"| Baseline rule comparison | {values['baseline_predictions']} |"),
        ("README.md", f"| Qualified-output gate ablations | {values['gate']} |"),
        ("README.md", f"| Qualified-output source-chain attacks | {values['source_chain']} |"),
        ("README.md", f"| Dynamic contestation challenges | {values['contestation']} |"),
        ("README.md", f"| Metamorphic policy tests | {values['metamorphic']} |"),
        ("README.md", f"| Query-perturbation stability | {values['query_perturbation']} |"),
        ("README.md", f"| Query-portfolio frontier | {values['query_portfolio']} |"),
        ("README.md", "python scripts/run_query_portfolio_frontier.py"),
        ("README.md", "score-and-role inflation without adoption"),
        ("README.md", f"| Blocked-claim repair frontiers | {values['repair']} |"),
        ("README.md", f"| Jurisdiction-profile mutations | {values['jurisdiction']} |"),
        ("README.md", f"| Ranking-visibility diagnostics | {values['ranking_window']} |"),
        ("README.md", f"| Status certificate replay | {values['certificate_checks']} |"),
        ("README.md", f"| Policy-constants replay | {values['policy_constants_checks']} |"),
        ("README.md", f"| Annotation uncertainty Monte Carlo | {values['uncertainty']} |"),
        ("README.md", f"| Score-blinded dual coding | {values['blind_packets'] * values['blind_passes']} |"),
        ("README.md", f"Current results are inter-coder minimum dimension kappa {values['blind_min_dimension_kappa']:.2f}, minimum derived failure-flag exact agreement {values['blind_min_failure_flag_exact']:.2f}, minimum derived missing-gate exact agreement {values['blind_min_missing_gate_exact']:.2f}, weakest base-dimension kappa {values['blind_base_dimension_min_kappa']:.2f} on {values['blind_base_dimension_min_kappa_dimension']}, base-dimension minimum exact agreement {values['blind_base_dimension_min_exact']:.2f}, minimum three-category PABAK {values['blind_base_dimension_min_pabak']:.2f} and maximum mean absolute score drift {values['blind_base_dimension_max_delta']:.2f}."),
        ("README.md", f"| Out-of-sample holdout validation | {units['holdout_records']} |"),
        ("README.md", "python scripts/run_gate_ablation_analysis.py"),
        ("README.md", "python scripts/run_repair_frontier_analysis.py"),
        ("README.md", "python scripts/run_jurisdiction_profile_analysis.py"),
        ("README.md", "python scripts/run_ranking_visibility_analysis.py"),
        ("README.md", "python scripts/run_status_certificate_validation.py"),
        ("README.md", "python scripts/run_policy_constants_replay.py"),
        ("README.md", "python scripts/run_metamorphic_policy_tests.py"),
        ("README.md", "python scripts/run_query_perturbation_analysis.py"),
        ("README.md", "python scripts/build_source_chain_attacks.py"),
        ("README.md", "python scripts/build_contestation_challenges.py"),
        ("docs/paper_mapping.md", "Qualified-output gate ablations"),
        ("docs/paper_mapping.md", "Qualified-output source-chain attacks"),
        ("docs/paper_mapping.md", "Dynamic contestation challenges"),
        ("docs/paper_mapping.md", "Metamorphic policy tests"),
        ("docs/paper_mapping.md", "Query-perturbation stability"),
        ("docs/paper_mapping.md", "Query-portfolio frontier"),
        ("docs/paper_mapping.md", "Metric bootstrap/permutation robustness"),
        ("docs/paper_mapping.md", "Baseline rule comparison"),
        ("docs/paper_mapping.md", "Blocked-claim repair frontiers"),
        ("docs/paper_mapping.md", "Jurisdiction-profile mutations"),
        ("docs/paper_mapping.md", "Ranking-visibility diagnostics"),
        ("docs/paper_mapping.md", "Status certificate replay"),
        ("docs/paper_mapping.md", "Policy-constants replay"),
        ("docs/paper_mapping.md", "Annotation uncertainty Monte Carlo"),
        ("docs/paper_mapping.md", "Out-of-sample holdout validation"),
        ("docs/paper_mapping.md", "bootstrap/permutation robustness"),
        ("docs/paper_mapping.md", "baseline-comparison layer"),
        ("docs/paper_mapping.md", "gate-ablation layer"),
        ("docs/paper_mapping.md", "source-chain attack layer"),
        ("docs/paper_mapping.md", "contestation challenge layer"),
        ("docs/paper_mapping.md", "metamorphic policy layer"),
        ("docs/paper_mapping.md", "query-perturbation layer"),
        ("docs/paper_mapping.md", "query-portfolio layer"),
        ("docs/paper_mapping.md", "repair-frontier layer"),
        ("docs/paper_mapping.md", "jurisdiction-profile layer"),
        ("docs/paper_mapping.md", "ranking-visibility layer"),
        ("docs/paper_mapping.md", "status-certificate layer"),
        ("docs/paper_mapping.md", "policy-constants replay layer"),
        ("docs/paper_mapping.md", "annotation-uncertainty layer"),
        ("docs/paper_mapping.md", "inter-coder dimension-level, post-evaluation failure-flag and missing-gate agreement"),
        ("docs/paper_mapping.md", "base-dimension calibration"),
        ("docs/paper_mapping.md", "holdout layer"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{values['gate_passed']}/{values['gate']} gate-ablation evaluations"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{values['source_chain_passed']}/{values['source_chain']} source-chain attack variants"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{values['contestation_passed']}/{values['contestation']} contestation challenge variants"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{_comma(values['metamorphic_passed'])}/{_comma(values['metamorphic'])} metamorphic policy tests"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{values['query_variants']} query-perturbation variants across {values['query_groups']} issue groups"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{values['query_portfolios']} query portfolios plus {values['query_portfolio_groups']} group frontier summaries across {values['query_portfolio_groups']} issue groups"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{_comma(values['metric_bootstrap'])} metric bootstrap resamples, {_comma(values['metric_permutation'])} metric permutation shuffles"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{_comma(values['baseline_predictions'])} baseline-rule predictions across {values['baseline_count']} alternative status rules"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{values['repairable']}/{values['blocked_claims']} blocked procedural claims repairable across {_comma(values['repair'])} repair-frontier evaluations"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{values['jurisdiction_supported']}/{values['jurisdiction_profile_checks']} jurisdiction-profile checks, {values['jurisdiction_mutations_passed']}/{values['jurisdiction_mutations']} profile mutations"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{values['ranking_window']} rank-window visibility checks over {values['ranking']} high-status claims"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{values['ranking_passed']}/{values['ranking_counterfactuals']} rank-order counterfactuals"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{values['certificates_verified']}/{values['certificate_count']} status certificates verified, {_comma(values['certificate_passed'])}/{_comma(values['certificate_checks'])} replay checks"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{_comma(values['policy_constants_passed'])}/{_comma(values['policy_constants_checks'])} policy-constants replay checks"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{_comma(values['uncertainty'])} annotation-uncertainty perturbations"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{values['blind_min_dimension_kappa']:.2f} inter-coder minimum dimension kappa, {values['blind_min_failure_flag_exact']:.2f} minimum derived failure-flag exact agreement, {values['blind_min_missing_gate_exact']:.2f} minimum derived missing-gate exact agreement, {values['blind_base_dimension_min_kappa']:.2f} weakest base-dimension kappa on {values['blind_base_dimension_min_kappa_dimension']}, {values['blind_base_dimension_min_exact']:.2f} base-dimension minimum exact agreement, {values['blind_base_dimension_min_pabak']:.2f} minimum three-category PABAK, {values['blind_base_dimension_max_delta']:.2f} maximum mean absolute score drift"),
        ("skills/legal-ai-audit-harness/SKILL.md", "holdout file"),
        ("skills/legal-ai-audit-harness/SKILL.md", "baseline-comparison file"),
        ("skills/legal-ai-audit-harness/SKILL.md", "python scripts/run_baseline_comparison_analysis.py"),
        ("skills/legal-ai-audit-harness/SKILL.md", "python scripts/run_gate_ablation_analysis.py"),
        ("skills/legal-ai-audit-harness/SKILL.md", "python scripts/run_repair_frontier_analysis.py"),
        ("skills/legal-ai-audit-harness/SKILL.md", "python scripts/run_jurisdiction_profile_analysis.py"),
        ("skills/legal-ai-audit-harness/SKILL.md", "python scripts/run_ranking_visibility_analysis.py"),
        ("skills/legal-ai-audit-harness/SKILL.md", "python scripts/run_status_certificate_validation.py"),
        ("skills/legal-ai-audit-harness/SKILL.md", "python scripts/run_policy_constants_replay.py"),
        ("skills/legal-ai-audit-harness/SKILL.md", "python scripts/run_metamorphic_policy_tests.py"),
        ("skills/legal-ai-audit-harness/SKILL.md", "python scripts/run_query_perturbation_analysis.py"),
        ("skills/legal-ai-audit-harness/SKILL.md", "python scripts/run_query_portfolio_frontier.py"),
        ("skills/legal-ai-audit-harness/SKILL.md", "python scripts/build_source_chain_attacks.py"),
        ("skills/legal-ai-audit-harness/SKILL.md", "python scripts/build_contestation_challenges.py"),
        ("skills/legal-ai-audit-harness/SKILL.md", "source-chain attack file"),
        ("skills/legal-ai-audit-harness/SKILL.md", "contestation challenge file"),
        ("skills/legal-ai-audit-harness/SKILL.md", "metamorphic policy file"),
        ("skills/legal-ai-audit-harness/SKILL.md", "query-perturbation file"),
        ("skills/legal-ai-audit-harness/SKILL.md", "query-portfolio file"),
        ("skills/legal-ai-audit-harness/SKILL.md", "policy-constants replay file"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['scenario_files']} scenario packets with {values['embedded']} embedded records or outputs"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{_comma(values['derived'])} derived robustness checks"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{_comma(values['metric_resamples'])} metric bootstrap/permutation resamples"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{_comma(values['baseline_predictions'])} baseline-rule predictions"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Across {values['baseline_count']} simplified substitute rules"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"still produced {values['baseline_best_fp']} false positives"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{_comma(values['uncertainty'])} perturbations"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Sample-level status stability was {values['uncertainty_stability']:.3f}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"high-status stability was {values['uncertainty_qualified_high']:.3f}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{_comma(values['certificate_checks'])} status-certificate replay checks"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['query_variants']} query-perturbation variants across {values['query_groups']} issue groups"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['query_portfolios']} query portfolios plus {values['query_portfolio_groups']} group frontier summaries across the same public retrieval variants"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"authority coverage was unstable in {values['query_authority_unstable']}/{values['query_groups']} groups"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"mean pairwise record overlap was {values['query_mean_overlap']:.2f}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['query_portfolios']} non-empty query portfolios"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['query_portfolio_full_high']}/{values['query_portfolios']} portfolios recovered full high-authority coverage"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['query_portfolio_full_counter']}/{values['query_portfolios']} recovered full counter-material coverage"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", "Within this frozen five-issue public-retrieval matrix"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['certificates_verified']}/{values['certificate_count']} status certificates"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['qualified']} packets that reached normative screening or decision-support status"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"All {values['gate_passed']} ablations fell below"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"across {values['blocked_claims']} blocked high-status claims"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", "B_A(o)"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", "B_E(o)"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", "B_P(o)"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", "B_C(o)"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", "B_J(o)"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", "B_T(o)"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", "B_D(o)"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", "B_F(o)"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['jurisdiction_supported']}/{values['jurisdiction_profile_checks']} profile checks"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['jurisdiction_mutations_passed']}/{values['jurisdiction_mutations']} profile mutations"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['ranking_window']} rank-window visibility checks"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['ranking_counterfactuals']} rank-order visibility counterfactuals"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"top-3 counter-material visibility was {values['ranking_visible']}/{values['ranking_front_window']}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"drifted top-3 counter-material visibility was {values['ranking_drifted_visible']}/{values['ranking_counterfactuals']}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"median first counter-material rank was {values['ranking_median']:.1f}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Qualified-output gate ablations & {values['gate']} ablations & {values['gate_passed']}/{values['gate']}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Source-chain attacks & {values['source_chain']} variants & {values['source_chain_passed']}/{values['source_chain']}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"All {values['source_chain']} attacked variants lost high status"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['source_chain_downgrade']} were downgraded, {values['source_chain_suspension']} were suspended and {values['source_chain_withdrawal']} were withdrawn"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['source_chain_reference']} were capped at reference information and {values['source_chain_no_effect']} were withdrawn"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Dynamic contestation challenges & {values['contestation']} variants & {values['contestation_passed']}/{values['contestation']}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"All {values['contestation_valid_blocked']} valid challenges blocked high status"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"all {values['contestation_unsupported_preserved']} unsupported controls preserved the original qualified status"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Metamorphic policy tests & {_comma(values['metamorphic'])} transformations & {_comma(values['metamorphic_passed'])}/{_comma(values['metamorphic'])}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Query-perturbation stability & {values['query_variants']} variants / {values['query_groups']} groups & {values['query_status_stable']}/{values['query_groups']} status-stable groups"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Query-portfolio frontier & {values['query_portfolios']} portfolios / {values['query_portfolio_groups']} groups & {values['query_portfolio_qualified']}/{values['query_portfolios']} qualified"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"All {_comma(values['metamorphic'])} metamorphic tests passed"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Blocked-claim repair frontiers & {_comma(values['repair'])} counterfactuals & {values['repairable']}/{values['blocked_claims']}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Jurisdiction-profile mutations & {values['jurisdiction']} checks & {values['jurisdiction_mutations_passed']}/{values['jurisdiction_mutations']}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Ranking-visibility diagnostics & {values['ranking_window']} window checks / {values['ranking_counterfactuals']} counterfactuals & {values['ranking_passed']}/{values['ranking_counterfactuals']}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Status certificate replay & {_comma(values['certificate_checks'])} checks & {_comma(values['certificate_passed'])}/{_comma(values['certificate_checks'])}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Policy-constants replay & {_comma(values['policy_constants_checks'])} checks & {_comma(values['policy_constants_passed'])}/{_comma(values['policy_constants_checks'])}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Baseline rule comparison & {_comma(values['baseline_predictions'])} predictions & Best simplified false positives {values['baseline_best_fp']}; reference rule false positives {values['baseline_full_fp']}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Annotation uncertainty & {_comma(values['uncertainty'])} perturbations & {values['uncertainty_stability']:.3f} sample stability; {values['uncertainty_qualified_high']:.3f} qualified high-status stability"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Score-blinded dual coding & {values['blind_packets']} packets, {values['blind_passes']} passes & {values['blind_kappa']:.2f} coder kappa; {values['blind_min_dimension_kappa']:.2f} min dimension kappa; {values['blind_base_dimension_min_exact']:.2f} min base exact"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"weakest dimension was authority hierarchy (H), with minimum dimension kappa {values['blind_min_dimension_kappa']:.2f}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Derived failure-flag exact agreement was {values['blind_min_failure_flag_exact']:.2f} and derived missing-gate exact agreement was {values['blind_min_missing_gate_exact']:.2f}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"The weakest base-dimension Cohen's kappa was {values['blind_base_dimension_min_kappa_dimension']}={values['blind_base_dimension_min_kappa']:.2f}, while exact agreement on that same three-level score was {values['blind_base_dimension_min_kappa_exact']:.2f}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Base-dimension calibration otherwise showed minimum exact agreement {values['blind_base_dimension_min_exact']:.2f}, minimum three-category prevalence-adjusted bias-adjusted kappa (PABAK) {values['blind_base_dimension_min_pabak']:.2f} and maximum mean absolute score drift {values['blind_base_dimension_max_delta']:.2f}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"The passes reached {values['blind_exact']:.2f} exact inter-coder agreement, {values['blind_kappa']:.2f} Cohen's kappa and {values['blind_weighted_kappa']:.2f} quadratic weighted kappa"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"the weaker coder reached {values['blind_base_exact']:.2f} exact agreement, {values['blind_base_weighted']:.2f} weighted agreement, {values['blind_base_kappa']:.2f} kappa and {values['blind_base_weighted_kappa']:.2f} weighted kappa"),
        ("experiments/full_validation/results/full_validation_report.md", f"Validation suites: {values['suite_count']}"),
        ("experiments/full_validation/results/full_validation_report.md", f"Scenario files: {values['scenario_files']}"),
        ("experiments/full_validation/results/full_validation_report.md", f"Metric statistical resamples: {values['metric_bootstrap']} bootstrap resamples and {values['metric_permutation']} permutation shuffles"),
        ("experiments/full_validation/results/full_validation_report.md", f"Baseline rule comparisons: {values['baseline_predictions']} predictions across {values['baseline_count']} rules; best simplified false positives {values['baseline_best_fp']}; reference rule false positives {values['baseline_full_fp']}"),
        ("experiments/full_validation/results/full_validation_report.md", f"Gate ablation evaluations: {values['gate_passed']}/{values['gate']} passed over {values['qualified']} qualified packets"),
        ("experiments/full_validation/results/full_validation_report.md", f"Source-chain attack variants: {values['source_chain_passed']}/{values['source_chain']} passed; high-upstream attacked variants blocked {values['source_chain_high_blocked']}/{values['source_chain']}"),
        ("experiments/full_validation/results/full_validation_report.md", f"Source-chain attack dispositions: downgrade {values['source_chain_downgrade']}, suspension {values['source_chain_suspension']}, withdrawal {values['source_chain_withdrawal']}"),
        ("experiments/full_validation/results/full_validation_report.md", f"Qualified-output source-chain attacks | whole-matrix source-chain negative control | {values['source_chain']} attack variants over qualified packets | {values['source_chain']} | {values['source_chain_passed']}/{values['source_chain']}"),
        ("experiments/full_validation/results/full_validation_report.md", f"Contestation challenge variants: {values['contestation_passed']}/{values['contestation']} passed; valid challenges blocked {values['contestation_valid_blocked']}/216; unsupported controls preserved {values['contestation_unsupported_preserved']}/54"),
        ("experiments/full_validation/results/full_validation_report.md", f"Dynamic contestation challenges | whole-matrix challenge-response validation | {values['contestation']} challenge variants over qualified packets | {values['contestation']} | {values['contestation_passed']}/{values['contestation']}"),
        ("experiments/full_validation/results/full_validation_report.md", f"Metamorphic policy tests: {values['metamorphic_passed']}/{values['metamorphic']} passed over {values['metamorphic_scenarios']} packets"),
        ("experiments/full_validation/results/full_validation_report.md", f"Metamorphic policy tests | expected-label-free policy-invariant validation | {values['metamorphic']} transformations over {values['metamorphic_scenarios']} packets | {values['metamorphic']} | {values['metamorphic_passed']}/{values['metamorphic']}"),
        ("experiments/full_validation/results/full_validation_report.md", f"Query-perturbation diagnostics: {values['query_variants']} query variants across {values['query_groups']} issue groups; status-stable groups {values['query_status_stable']}/{values['query_groups']}; authority-coverage unstable groups {values['query_authority_unstable']}/{values['query_groups']}; record-set unstable groups {values['query_record_unstable']}/{values['query_groups']}; mean record overlap {values['query_mean_overlap']:.2f}"),
        ("experiments/full_validation/results/full_validation_report.md", f"Query-perturbation stability | public-retrieval query-sensitivity diagnostic | {values['query_variants']} query variants across {values['query_groups']} issue groups | {values['query_variants']} | {values['query_status_stable']}/{values['query_groups']} status-stable groups"),
        ("experiments/full_validation/results/full_validation_report.md", f"Query-portfolio frontier: {values['query_portfolios']} portfolios plus {values['query_portfolio_groups']} group summaries across {values['query_portfolio_groups']} issue groups; qualified portfolios {values['query_portfolio_qualified']}/{values['query_portfolios']}; full high-authority portfolios {values['query_portfolio_full_high']}/{values['query_portfolios']}; full counter-material portfolios {values['query_portfolio_full_counter']}/{values['query_portfolios']}"),
        ("experiments/full_validation/results/full_validation_report.md", f"Query-portfolio frontier | public-retrieval query-expansion frontier | {values['query_portfolios']} query portfolios plus {values['query_portfolio_groups']} group frontier summaries | {values['query_portfolio']} | {values['query_portfolio_qualified']}/{values['query_portfolios']} portfolios qualified"),
        ("experiments/full_validation/results/full_validation_report.md", f"Repair frontier evaluations: {values['repairable']}/{values['blocked_claims']} blocked claims repairable across {values['repair']} counterfactual repairs"),
        ("experiments/full_validation/results/full_validation_report.md", f"Jurisdiction-profile evaluations: {values['jurisdiction_supported']}/{values['jurisdiction_profile_checks']} profile checks supported; {values['jurisdiction_mutations_passed']}/{values['jurisdiction_mutations']} counterfactual mutations passed"),
        ("experiments/full_validation/results/full_validation_report.md", f"Ranking-visibility checks: {values['ranking_window']} rank-window checks over {values['ranking']} high-status claims; {values['ranking_passed']}/{values['ranking_counterfactuals']} rank-order counterfactuals downgraded with coverage preserved; top-3 counter visible {values['ranking_visible']}/{values['ranking_front_window']}; drifted top-3 counter visible {values['ranking_drifted_visible']}/{values['ranking_counterfactuals']}; median first counter rank {values['ranking_median']:.1f}"),
        ("experiments/full_validation/results/full_validation_report.md", f"Status certificate replay checks: {values['certificate_passed']}/{values['certificate_checks']} passed over {values['certificate_count']} certificates"),
        ("experiments/full_validation/results/full_validation_report.md", f"Policy-constants replay checks: {values['policy_constants_passed']}/{values['policy_constants_checks']} passed over {values['policy_constants_scenarios']} packets"),
        ("experiments/full_validation/results/full_validation_report.md", f"Annotation uncertainty: {values['uncertainty']} score perturbations; sample stability {values['uncertainty_stability']:.3f}; qualified high-status stability {values['uncertainty_qualified_high']:.3f}; boundary scenarios {values['uncertainty_boundary']}"),
        ("experiments/full_validation/results/full_validation_report.md", f"Score-blinded coding: {values['blind_packets']} packets, {values['blind_passes']} coding passes, {values['blind_exact']:.2f} coder-coder exact agreement, {values['blind_kappa']:.2f} coder-coder kappa, {values['blind_weighted_kappa']:.2f} coder-coder weighted kappa, {values['blind_min_dimension_kappa']:.2f} minimum dimension kappa, {values['blind_min_failure_flag_exact']:.2f} minimum derived failure-flag exact agreement, {values['blind_min_missing_gate_exact']:.2f} minimum derived missing-gate exact agreement, {values['blind_base_dimension_min_kappa']:.2f} minimum base-dimension kappa ({values['blind_base_dimension_min_kappa_dimension']}, {values['blind_base_dimension_min_kappa_exact']:.2f} exact), {values['blind_base_dimension_min_exact']:.2f} minimum base-dimension exact agreement, {values['blind_base_dimension_min_pabak']:.2f} minimum base-dimension PABAK, {values['blind_base_dimension_max_delta']:.2f} maximum base-dimension mean absolute delta, {values['blind_base_exact']:.2f} minimum base-coder exact agreement, {values['blind_base_weighted']:.2f} minimum base-coder weighted agreement, {values['blind_base_kappa']:.2f} minimum base-coder kappa, {values['blind_base_weighted_kappa']:.2f} minimum base-coder weighted kappa"),
        ("experiments/full_validation/results/full_validation_report.md", f"Metric separation evaluations: {values['metric']} upstream-metric scenario packets; high-recall blocked outputs {values['metric_high_recall_blocked']}/{values['metric_high_recall_total']}"),
    ]
    for run in threshold_sensitivity["runs"]:
        expectations.append(
            (
                "manuscript/ai_law_case_recommendation_verifiability.tex",
                (
                    f"{run['normative_threshold']} & {run['decision_threshold']} & "
                    f"{run['status_flips_from_default']} & {run['demotions_from_default']} & "
                    f"{_threshold_distribution(run['status_distribution'])}"
                ),
            )
        )
    if values["pdf_pages"] is not None:
        expectations.append(("ARTIFACT.md", f"The expected manuscript build is {values['pdf_pages']} pages"))
    checks = []
    for path, expected in expectations:
        text = (ROOT / path).read_text(encoding="utf-8")
        checks.append({"path": path, "expected": expected, "passed": expected in text})
    abstract_count = _abstract_word_count()
    checks.append(
        {
            "path": "manuscript/ai_law_case_recommendation_verifiability.tex",
            "expected": f"abstract word count 150-250 (actual {abstract_count})",
            "passed": 150 <= abstract_count <= 250,
        }
    )
    checks.extend(_forbidden_checks())
    return checks


def _forbidden_checks() -> list[dict]:
    forbidden = [
        "62,497",
        "62,641",
        "64,996",
        "65,528",
        "2,236",
        "3,886",
        "174 rank-window",
        "46 high-status packets",
        "214 high-status packets",
        "11/11 rank-order",
        "11 rank-order visibility counterfactuals",
        "top-3 counter-material visibility was 31/41",
        "33 pages",
        "23 validation suites",
        "24 validation suites",
        "27 validation suites",
        "28 validation suites",
        "29 validation suites",
        "230 scenario files",
        "609 embedded records",
        "123,028",
        "127,632",
        "129,725",
        "129,995",
        "126,953",
        "130,404",
        "130,674",
        "130,944",
        "130,265",
        "132,078",
        "131,399",
        "135,276",
        "135,616",
        "3,198/3,198 declarative",
        "136,260",
        "136,295",
        "135,581",
        "declarative policy replay checks",
        "independent declarative",
        "from a declarative policy file",
        "from a declarative policy specification",
        "independent replay from a declarative policy file",
        "downgrade or withdrawal",
        "downgrade or withdraw",
        "adoption inflation",
        "oracle-free policy transformations",
        "oracle-free status-function",
        "57,500",
        "2,990",
        "1,150",
        "4,418",
        "820 rank-window",
        "70/70 rank-order",
        "225 returned records",
        "30 public retrieval outputs",
        "screening 34",
        "screening 32",
        "reference 129",
        "professional 52",
        "full gate precision",
        "full gate false positives",
        "full gate FP",
    ]
    paths = [
        "ARTIFACT.md",
        "README.md",
        "docs/paper_mapping.md",
        "skills/legal-ai-audit-harness/SKILL.md",
        "manuscript/ai_law_case_recommendation_verifiability.tex",
    ]
    checks = []
    for path in paths:
        text = (ROOT / path).read_text(encoding="utf-8")
        for item in forbidden:
            checks.append({"path": path, "expected": f"absence of stale claim `{item}`", "passed": item not in text})
    return checks


def _comma(value: int) -> str:
    return f"{value:,}"


def _threshold_distribution(distribution: dict[str, int]) -> str:
    return (
        f"decision {distribution.get('decision_support_reason', 0)}; "
        f"screening {distribution.get('normative_material_screening_output', 0)}; "
        f"professional {distribution.get('professional_support_output', 0)}; "
        f"reference {distribution.get('reference_information', 0)}; "
        f"no effect {distribution.get('no_external_legal_effect', 0)}"
    )


def _abstract_word_count() -> int:
    text = (ROOT / "manuscript" / "ai_law_case_recommendation_verifiability.tex").read_text(encoding="utf-8")
    match = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", text, re.DOTALL)
    if not match:
        return 0
    abstract = re.sub(r"\\textit\{([^}]*)\}", r"\1", match.group(1))
    abstract = re.sub(r"\\[a-zA-Z]+(?:\[[^\]]*\])?(?:\{[^}]*\})?", " ", abstract)
    return len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*", abstract))


def _pdf_page_count(path: Path) -> int | None:
    log = path.with_suffix(".log")
    if log.exists():
        match = re.search(r"Output written on .+ \((\d+) pages", log.read_text(encoding="utf-8", errors="ignore"))
        if match:
            return int(match.group(1))
    return None


def _format_report(payload: dict) -> str:
    lines = [
        "# Claim Consistency Verification",
        "",
        f"Checks: {payload['passed_count']}/{payload['check_count']}",
        f"All passed: {payload['failed_count'] == 0}",
    ]
    if payload["failures"]:
        lines.extend(["", "## Failures", ""])
        for failure in payload["failures"]:
            lines.append(f"- {failure['path']}: missing `{failure['expected']}`")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
