import json
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from audit_harness.model import evaluate_scenario


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "examples" / "scenarios"
sys.path.insert(0, str(ROOT / "scripts"))
from build_model_output_repairs import matched_source_support, repair


def load(name: str) -> dict:
    return json.loads((SCENARIOS / name).read_text(encoding="utf-8"))


class AuditModelTest(unittest.TestCase):
    def test_normative_screening_threshold(self):
        result = evaluate_scenario(load("court_authority_report.json"))
        self.assertEqual(result.allowed_status, "normative_material_screening_output")
        self.assertEqual(result.total_score, 10)
        self.assertTrue(result.claim_supported)
        self.assertAlmostEqual(result.counter_authority_recall, 0.5)

    def test_professional_support_does_not_upgrade_when_k_is_zero(self):
        result = evaluate_scenario(load("professional_research_support.json"))
        self.assertEqual(result.allowed_status, "professional_support_output")
        self.assertIn("K", result.missing_gates)
        self.assertTrue(result.claim_supported)

    def test_decision_support_requires_full_contestability_and_adoption_logging(self):
        result = evaluate_scenario(load("decision_support_ready.json"))
        self.assertEqual(result.allowed_status, "decision_support_reason")
        self.assertEqual(result.total_score, 12)
        self.assertAlmostEqual(result.counter_authority_recall, 1.0)

    def test_decision_support_requires_normative_gate_and_total_threshold(self):
        scenario = deepcopy(load("decision_support_ready.json"))
        for dimension in ("S", "Q", "H", "K"):
            scenario["scores"][dimension]["score"] = 1
        result = evaluate_scenario(scenario)
        self.assertEqual(result.total_score, 8)
        self.assertEqual(result.allowed_status, "professional_support_output")
        self.assertIn("total_score>=9", result.missing_gates)

    def test_decision_support_requires_authorized_adoption_gate(self):
        scenario = deepcopy(load("decision_support_ready.json"))
        scenario["review_gate"]["reliance_gate"] = "attorney_review"
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "normative_material_screening_output")

        scenario = deepcopy(load("decision_support_ready.json"))
        scenario["review_gate"]["human_authorization"] = False
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "normative_material_screening_output")

        scenario = deepcopy(load("decision_support_ready.json"))
        scenario["review_gate"]["adoption_reasons_recorded"] = False
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "normative_material_screening_output")

        scenario = deepcopy(load("decision_support_ready.json"))
        scenario["review_gate"]["contestation_recorded"] = False
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "normative_material_screening_output")

    def test_system_role_caps_highest_available_status(self):
        scenario = deepcopy(load("decision_support_ready.json"))
        scenario["system_role"] = "auditable_procedural_tool"
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "normative_material_screening_output")
        self.assertIn("system_role:auditable_procedural_tool->max:normative_material_screening_output", result.missing_gates)

        scenario = deepcopy(load("court_authority_report.json"))
        scenario["system_role"] = "disclosed_assistance_tool"
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "professional_support_output")
        self.assertIn("system_role:disclosed_assistance_tool->max:professional_support_output", result.missing_gates)

    def test_withdrawal_blocks_external_effect(self):
        result = evaluate_scenario(load("unverifiable_legal_output.json"))
        self.assertEqual(result.allowed_status, "no_external_legal_effect")
        self.assertEqual(result.disposition, "withdrawal")
        self.assertFalse(result.claim_supported)

    def test_missing_source_tags_downgrade_external_status(self):
        scenario = deepcopy(load("grounded_output_summary.json"))
        for link in scenario["evidence_packet"]["output_links"]:
            link.pop("source_tag", None)
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "reference_information")
        self.assertEqual(result.disposition, "downgrade")
        self.assertAlmostEqual(result.source_tag_coverage, 0.0)

    def test_unverified_source_tags_downgrade_normative_status(self):
        scenario = deepcopy(load("grounded_output_summary.json"))
        for link in scenario["evidence_packet"]["output_links"]:
            link["source_tag"] = "needs_verification"
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "reference_information")
        self.assertEqual(result.disposition, "downgrade")
        self.assertAlmostEqual(result.source_tag_coverage, 1.0)
        self.assertAlmostEqual(result.procedural_source_tag_coverage, 0.0)

    def test_review_gate_blocks_unreviewed_external_reliance(self):
        scenario = deepcopy(load("decision_support_ready.json"))
        scenario["review_gate"]["review_status"] = "pending"
        scenario["review_gate"]["reliance_gate"] = "authorized_adoption"
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "reference_information")
        self.assertEqual(result.disposition, "downgrade")

    def test_unauthorized_irreversible_action_is_withdrawn(self):
        scenario = deepcopy(load("odr_authorized_review.json"))
        scenario["review_gate"]["irreversible_action"] = True
        scenario["review_gate"]["human_authorization"] = False
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "no_external_legal_effect")
        self.assertEqual(result.disposition, "withdrawal")

    def test_suspension_downgrades_to_reference(self):
        result = evaluate_scenario(load("suspended_authority_omission.json"))
        self.assertEqual(result.allowed_status, "reference_information")
        self.assertEqual(result.disposition, "suspension")
        self.assertFalse(result.claim_supported)

    def test_cli_run_examples(self):
        completed = subprocess.run(
            [sys.executable, "-m", "audit_harness.cli", "run", str(SCENARIOS)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("court-authority-report", completed.stdout)
        self.assertIn("unverifiable-legal-output", completed.stdout)

    def test_experiment_reports_high_recall_blocked_cases(self):
        completed = subprocess.run(
            [sys.executable, "-m", "audit_harness.cli", "experiment", str(SCENARIOS)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("High-upstream-performance but procedurally blocked scenarios", completed.stdout)
        self.assertIn("civil-law-statutory-interpretation", completed.stdout)
        self.assertIn("high-coverage-uncontestable-output", completed.stdout)

    def test_real_case_fixture_shape(self):
        real_scenarios = ROOT / "experiments" / "real_cases" / "scenarios"
        for path in sorted(real_scenarios.glob("*.json")):
            scenario = json.loads(path.read_text(encoding="utf-8"))
            units = scenario.get("evidence_packet", {}).get("output_units", [])
            self.assertEqual(len(units), 20, path.name)
            result = evaluate_scenario(scenario)
            self.assertEqual(result.allowed_status, "professional_support_output", path.name)

    def test_public_system_output_fixture_shape(self):
        scenarios = ROOT / "experiments" / "public_system_outputs" / "scenarios"
        paths = sorted(scenarios.glob("*.json"))
        self.assertEqual(len(paths), 6)
        for path in paths:
            scenario = json.loads(path.read_text(encoding="utf-8"))
            units = scenario.get("evidence_packet", {}).get("output_units", [])
            self.assertEqual(len(units), 10, path.name)
            result = evaluate_scenario(scenario)
            self.assertEqual(result.allowed_status, "professional_support_output", path.name)
            self.assertAlmostEqual(result.evidence_fidelity, 1.0, msg=path.name)
            self.assertAlmostEqual(result.source_tag_coverage, 1.0, msg=path.name)

    def test_schema_rejects_missing_scores(self):
        scenario = deepcopy(load("grounded_output_summary.json"))
        scenario["scores"].pop("K")
        with self.assertRaises(ValueError):
            evaluate_scenario(scenario)

    def test_issue_gold_set_qualifies_as_normative_screening(self):
        paths = sorted((ROOT / "experiments" / "issue_gold_sets" / "scenarios").glob("*.json"))
        self.assertGreaterEqual(len(paths), 3)
        for path in paths:
            scenario = json.loads(path.read_text(encoding="utf-8"))
            result = evaluate_scenario(scenario)
            self.assertEqual(result.allowed_status, "normative_material_screening_output", path.name)
            self.assertAlmostEqual(result.authority_coverage, 1.0, msg=path.name)
            self.assertAlmostEqual(result.counter_authority_recall, 1.0, msg=path.name)
            self.assertAlmostEqual(result.evidence_fidelity, 1.0, msg=path.name)

    def test_issue_manifests_include_hashed_source_support(self):
        paths = sorted((ROOT / "experiments" / "issue_gold_sets" / "manifests").glob("*.json"))
        self.assertGreaterEqual(len(paths), 5)
        for path in paths:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            for record in manifest["records"]:
                support = record.get("source_support", [])
                self.assertTrue(support, f"{path.name}:{record['id']}")
                for item in support:
                    excerpt = item.get("source_excerpt", "")
                    self.assertTrue(excerpt, f"{path.name}:{record['id']}")
                    self.assertEqual(hashlib.sha256(excerpt.encode("utf-8")).hexdigest(), item.get("excerpt_sha256"))

    def test_issue_ablations_apply_failure_caps(self):
        subprocess.run(
            [sys.executable, "scripts/build_issue_ablations.py"],
            cwd=ROOT,
            check=True,
        )
        paths = sorted((ROOT / "experiments" / "issue_ablations" / "scenarios").glob("*.json"))
        self.assertEqual(len(paths), 20)
        blocked = 0
        for path in paths:
            scenario = json.loads(path.read_text(encoding="utf-8"))
            result = evaluate_scenario(scenario)
            self.assertTrue(result.expected_passed, path.name)
            if path.stem.endswith(("missing-high-authority", "counter-material-suppressed", "unverified-source-tags")):
                blocked += 1
                self.assertEqual(result.allowed_status, "reference_information", path.name)
                if path.stem.endswith("counter-material-suppressed"):
                    scenario["failure_flags"] = []
                    self.assertEqual(evaluate_scenario(scenario).disposition, "suspension", path.name)
        self.assertEqual(blocked, 15)

    def test_codex_gpt55_xhigh_raw_outputs_are_source_capped(self):
        paths = sorted((ROOT / "experiments" / "ai_outputs" / "scenarios").glob("codex55_*.json"))
        self.assertEqual(len(paths), 10)
        for path in paths:
            scenario = json.loads(path.read_text(encoding="utf-8"))
            result = evaluate_scenario(scenario)
            self.assertEqual(result.claimed_status, "normative_material_screening_output", path.name)
            self.assertEqual(result.allowed_status, "reference_information", path.name)
            self.assertEqual(result.disposition, "downgrade", path.name)
            self.assertFalse(result.claim_supported, path.name)
            self.assertAlmostEqual(result.procedural_source_tag_coverage, 0.0, msg=path.name)
            self.assertGreaterEqual(scenario["upstream_metrics"]["recall"], 0.9, path.name)

    def test_source_bound_model_outputs_can_qualify(self):
        paths = sorted((ROOT / "experiments" / "model_output_repairs" / "scenarios").glob("source-bound-*.json"))
        self.assertEqual(len(paths), 10)
        for path in paths:
            scenario = json.loads(path.read_text(encoding="utf-8"))
            result = evaluate_scenario(scenario)
            self.assertEqual(result.allowed_status, "normative_material_screening_output", path.name)
            self.assertEqual(result.disposition, "none", path.name)
            self.assertAlmostEqual(result.procedural_source_tag_coverage, 1.0, msg=path.name)
            validation = scenario.get("source_binding_validation", {})
            self.assertTrue(validation.get("all_links_source_bound"), path.name)
            self.assertTrue(validation.get("claim_support_complete"), path.name)
            self.assertTrue(validation.get("source_support_complete"), path.name)
            self.assertEqual(validation.get("missing_source_ids"), [], path.name)
            self.assertEqual(validation.get("missing_output_links"), [], path.name)
            self.assertEqual(validation.get("unsupported_locators"), [], path.name)
            self.assertEqual(validation.get("unsupported_claims"), [], path.name)
            self.assertTrue(validation.get("source_support_by_link"), path.name)
            self.assertEqual(
                validation.get("source_tag_assignment"),
                "assigned_after_manifest_locator_issue_set_and_source_support_validation",
                path.name,
            )
            self.assertEqual(validation.get("assigned_procedural_source_tags"), len(scenario["evidence_packet"]["output_links"]), path.name)
            for link in scenario["evidence_packet"]["output_links"]:
                self.assertEqual(link.get("support_label"), "supports", path.name)
                self.assertTrue(link.get("validated_source_support"), path.name)
                self.assertTrue(link.get("validated_support_terms"), path.name)

    def test_claim_support_validator_blocks_unmatched_claims(self):
        raw = json.loads((ROOT / "experiments" / "ai_outputs" / "scenarios" / "codex55_us_01.json").read_text(encoding="utf-8"))
        raw["evidence_packet"]["output_units"][0]["claim"] = "This unrelated proposition is not supported by the cited authority."
        repaired = repair(raw)
        validation = repaired["source_binding_validation"]
        self.assertFalse(validation["all_links_source_bound"])
        self.assertFalse(validation["claim_support_complete"])
        self.assertFalse(validation["source_support_complete"])
        self.assertTrue(validation["unsupported_claims"])
        result = evaluate_scenario(repaired)
        self.assertEqual(result.allowed_status, "no_external_legal_effect")
        self.assertEqual(result.disposition, "withdrawal")

    def test_source_support_validator_blocks_same_term_contradictions(self):
        raw = json.loads((ROOT / "experiments" / "ai_outputs" / "scenarios" / "codex55_eu_01.json").read_text(encoding="utf-8"))
        raw["evidence_packet"]["output_units"][1]["claim"] = "C-154/21 does not require specific recipients where recipients are identifiable."
        repaired = repair(raw)
        validation = repaired["source_binding_validation"]
        self.assertFalse(validation["all_links_source_bound"])
        self.assertFalse(validation["source_support_complete"])
        self.assertIn("contradiction_pattern_matched", {item["reason"] for item in validation["unsupported_source_support"]})
        result = evaluate_scenario(repaired)
        self.assertEqual(result.allowed_status, "no_external_legal_effect")
        self.assertEqual(result.disposition, "withdrawal")

    def test_source_support_evidence_item_is_required(self):
        unit = {"claim": "Loper Bright overruled Chevron for statutory interpretation."}
        link = {"locator": "Loper Bright"}
        record = {
            "id": "loper-bright-603-us-369",
            "title": "Loper Bright Enterprises v. Raimondo",
            "citation": "603 U.S. 369 (2024)",
            "support_terms": ["loper bright", "overruled chevron"],
        }
        matches, errors = matched_source_support(unit, link, record)
        self.assertEqual(matches, [])
        self.assertEqual(errors[0]["reason"], "missing_source_support")

    def test_source_support_validator_blocks_missing_output_links(self):
        raw = json.loads((ROOT / "experiments" / "ai_outputs" / "scenarios" / "codex55_us_01.json").read_text(encoding="utf-8"))
        raw["evidence_packet"]["output_links"] = raw["evidence_packet"]["output_links"][1:]
        repaired = repair(raw)
        validation = repaired["source_binding_validation"]
        self.assertFalse(validation["all_links_source_bound"])
        self.assertTrue(validation["missing_output_links"])
        result = evaluate_scenario(repaired)
        self.assertEqual(result.allowed_status, "reference_information")
        self.assertEqual(result.disposition, "downgrade")

    def test_model_output_adversarial_suite_rejects_all_attacks(self):
        subprocess.run(
            [sys.executable, "scripts/build_model_output_adversarial.py"],
            cwd=ROOT,
            check=True,
        )
        paths = sorted((ROOT / "experiments" / "model_output_adversarial" / "scenarios").glob("*.json"))
        self.assertEqual(len(paths), 60)
        attacks = {}
        statuses = {}
        for path in paths:
            scenario = json.loads(path.read_text(encoding="utf-8"))
            attack = scenario["adversarial_intervention"]["attack"]
            attacks[attack] = attacks.get(attack, 0) + 1
            validation = scenario.get("source_binding_validation", {})
            self.assertFalse(validation.get("all_links_source_bound"), path.name)
            result = evaluate_scenario(scenario)
            statuses[result.allowed_status] = statuses.get(result.allowed_status, 0) + 1
            self.assertTrue(result.expected_passed, path.name)
            self.assertIn(result.allowed_status, {"reference_information", "no_external_legal_effect"}, path.name)
        self.assertEqual(statuses, {"no_external_legal_effect": 20, "reference_information": 40})
        self.assertEqual(
            attacks,
            {
                "claim_support_gap": 10,
                "contradiction_pattern": 10,
                "counter_material_omission": 10,
                "locator_mismatch": 10,
                "manifest_membership_gap": 10,
                "unit_source_link_gap": 10,
            },
        )

    def test_issue_specific_public_outputs_shape(self):
        paths = sorted((ROOT / "experiments" / "issue_public_outputs" / "scenarios").glob("*.json"))
        self.assertEqual(len(paths), 3)
        statuses = {}
        for path in paths:
            scenario = json.loads(path.read_text(encoding="utf-8"))
            result = evaluate_scenario(scenario)
            self.assertTrue(result.expected_passed, path.name)
            statuses[result.allowed_status] = statuses.get(result.allowed_status, 0) + 1
        self.assertEqual(statuses["normative_material_screening_output"], 1)
        self.assertEqual(statuses["reference_information"], 2)

    def test_public_retrieval_benchmark_shape(self):
        paths = sorted((ROOT / "experiments" / "public_retrieval_benchmark" / "scenarios").glob("*.json"))
        self.assertEqual(len(paths), 30)
        records = 0
        counter_recalls = []
        for path in paths:
            scenario = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn(scenario.get("benchmark_scope"), {"case_law_only", "case_law_known_item"}, path.name)
            endpoint_gold = set(scenario["authority_sets"]["high_authority"]) | set(scenario["authority_sets"]["counter_or_limiting"])
            self.assertFalse(
                {item for item in endpoint_gold if item.startswith(("apa-", "gdpr-", "compensation-act", "charter-", "basic-law-"))},
                path.name,
            )
            self.assertTrue(scenario.get("mixed_authority_required_elsewhere"), path.name)
            records += len(scenario["evidence_packet"]["output_units"])
            result = evaluate_scenario(scenario)
            self.assertTrue(result.expected_passed, path.name)
            self.assertEqual(result.allowed_status, "reference_information", path.name)
            self.assertEqual(result.disposition, "suspension", path.name)
            if result.counter_authority_recall is not None:
                counter_recalls.append(result.counter_authority_recall)
            if path.name.startswith("canada-vavilov"):
                self.assertNotIn("dunsmuir-2008-scc-9", scenario["authority_sets"]["retrieved"], path.name)
            if path.name == "us-agency-deference-after-loper-bright-q02.json":
                by_locator = {
                    unit["locators"][0]: unit["source_ids"][0]
                    for unit in scenario["evidence_packet"]["output_units"]
                    if unit.get("locators") and unit.get("source_ids")
                }
                self.assertNotEqual(by_locator.get("45 F.4th 359"), "loper-bright-603-us-369")
                self.assertIn("us-search-loper-bright-enterprises-inc-v-wilbur-l-ross-jr", scenario["authority_sets"]["retrieved"])
        self.assertEqual(records, 225)
        self.assertTrue(counter_recalls)
        self.assertTrue(all(recall == 0 for recall in counter_recalls))

    def test_full_validation_report_shape(self):
        report = json.loads((ROOT / "experiments" / "full_validation" / "results" / "full_validation_report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["suite_count"], 13)
        self.assertEqual(report["scenario_files"], 160)
        self.assertEqual(report["validation_units"]["total"], 539)
        self.assertEqual(report["validation_units"]["public_retrieval_records"], 225)
        self.assertEqual(report["validation_units"]["source_bound_model_outputs"], 10)
        self.assertEqual(report["validation_units"]["adversarial_model_outputs"], 60)
        self.assertEqual(report["validation_units"]["issue_public_records"], 19)
        self.assertEqual(report["validation_units"]["issue_gold_sets"], 5)
        self.assertEqual(report["validation_units"]["issue_ablations"], 20)
        self.assertEqual(report["validation_units"]["annotation_recodings"], 320)
        self.assertEqual(report["blind_coding_evaluations"], 320)
        self.assertEqual(report["validation_units"]["blind_coding_packets"], 160)
        self.assertEqual(report["threshold_sensitivity_evaluations"], 800)
        self.assertEqual(report["validation_units"]["threshold_sensitivity_evaluations"], 800)
        self.assertEqual(report["source_text_anchor_evaluations"], 30)
        self.assertEqual(report["validation_units"]["source_text_anchor_checks"], 30)
        self.assertGreaterEqual(report["validation_units"]["source_text_anchor_verified"], 20)
        self.assertEqual(report["total_evaluation_rows"], 2009)
        self.assertEqual(report["expected_passed"], 160)
        self.assertEqual(report["expected_total"], 160)
        self.assertEqual(report["annotation_robustness"]["scenario_count"], 160)
        self.assertEqual(report["blind_coding"]["packet_count"], 160)
        self.assertIn("base_status_agreement", report["blind_coding"])
        self.assertEqual(report["threshold_sensitivity"]["scenario_count"], 160)
        self.assertEqual(report["threshold_sensitivity"]["runs"][0]["status_flips_from_default"], 0)
        self.assertEqual(report["blocked_reason_distribution"]["source_attribution_gap"], 75)
        self.assertEqual(report["blocked_reason_distribution"]["summary_distortion"], 21)
        self.assertGreaterEqual(report["source_text_verification"]["support_items_verified"], 20)
        self.assertGreaterEqual(report["source_text_verification"]["records_with_text_snapshot"], 20)

    def test_public_source_text_anchor_verification(self):
        completed = subprocess.run(
            [sys.executable, "scripts/verify_source_text_anchors.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        report = json.loads((ROOT / "experiments" / "source_text_verification" / "results" / "source_text_anchor_verification.json").read_text(encoding="utf-8"))
        self.assertEqual(report["support_item_count"], 30)
        self.assertGreaterEqual(report["support_items_verified"], 20)
        self.assertGreaterEqual(report["records_with_text_snapshot"], 20)
        verified = [item for item in report["items"] if item["verified"]]
        self.assertTrue(all(item["snapshot_sha256"] for item in verified))

    def test_annotation_robustness_report_shape(self):
        completed = subprocess.run(
            [sys.executable, "scripts/run_annotation_robustness.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        report = json.loads((ROOT / "experiments" / "annotation_robustness" / "results" / "annotation_robustness.json").read_text(encoding="utf-8"))
        self.assertEqual(report["scenario_count"], 160)
        self.assertEqual(report["recoded_evaluations"], 320)
        self.assertGreaterEqual(report["weighted_status_agreement_base_strict"], 0.9)
        self.assertGreaterEqual(report["all_policy_status_stable"], 140)

    def test_blind_coding_study_report_shape(self):
        subprocess.run(
            [sys.executable, "scripts/build_model_output_adversarial.py"],
            cwd=ROOT,
            check=True,
        )
        subprocess.run(
            [sys.executable, "scripts/build_blind_coding_packets.py"],
            cwd=ROOT,
            check=True,
        )
        completed = subprocess.run(
            [sys.executable, "scripts/run_blind_coding_study.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        report = json.loads((ROOT / "experiments" / "blind_coding" / "results" / "blind_coding_study.json").read_text(encoding="utf-8"))
        self.assertEqual(report["packet_count"], 160)
        self.assertEqual(report["coder_count"], 2)
        self.assertGreaterEqual(report["pairwise_status"][0]["exact_status_agreement"], 0.9)
        base_agreements = report["base_status_agreement"].values()
        self.assertGreaterEqual(min(item["exact_status_agreement"] for item in base_agreements), 0.8)
        self.assertGreaterEqual(min(item["weighted_status_agreement"] for item in base_agreements), 0.9)

    def test_cli_sensitivity_report(self):
        completed = subprocess.run(
            [sys.executable, "-m", "audit_harness.cli", "sensitivity", str(SCENARIOS)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("Normative threshold", completed.stdout)
        self.assertIn("Decision threshold", completed.stdout)

    def test_real_case_collector_supports_external_output_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            shutil.copytree(ROOT / "experiments" / "real_cases" / "downloads", Path(directory) / "downloads")
            completed = subprocess.run(
                [sys.executable, "scripts/collect_real_cases.py", "--out", directory],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)

    def test_public_system_output_collector_supports_external_output_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            shutil.copytree(ROOT / "experiments" / "public_system_outputs" / "downloads", Path(directory) / "downloads")
            completed = subprocess.run(
                [sys.executable, "scripts/collect_public_system_outputs.py", "--out", directory],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)

    def test_issue_public_output_collector_supports_external_output_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            shutil.copytree(ROOT / "experiments" / "issue_public_outputs" / "downloads", Path(directory) / "downloads")
            completed = subprocess.run(
                [sys.executable, "scripts/collect_issue_public_outputs.py", "--out", directory],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)

    def test_public_retrieval_benchmark_collector_supports_external_output_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            shutil.copytree(ROOT / "experiments" / "public_retrieval_benchmark" / "downloads", Path(directory) / "downloads")
            completed = subprocess.run(
                [sys.executable, "scripts/collect_public_retrieval_benchmark.py", "--out", directory],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)


if __name__ == "__main__":
    unittest.main()
