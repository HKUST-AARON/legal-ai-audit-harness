import json
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


if __name__ == "__main__":
    unittest.main()
