from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_harness.model import RANK_SALIENCE_WINDOW, evaluate_scenario
from build_model_output_repairs import promote_counter_material_salience, validate_source_binding, validated_scores
from collect_public_retrieval_benchmark import (
    CANADA_ISSUE,
    EU_ISSUE,
    GERMANY_ISSUE,
    HOLDOUT_SLUGS,
    UK_ISSUE,
    US_ISSUE,
    build_manifest,
    build_scenario,
    collect,
)


OUT = ROOT / "experiments" / "holdout_validation"
DOWNLOADS = OUT / "downloads"
MANIFESTS = OUT / "manifests"
SCENARIOS = OUT / "scenarios"
RESULTS = OUT / "results"
TOP_K = 10

ISSUES = {
    "us-agency-deference-after-loper-bright": US_ISSUE,
    "uk-mesothelioma-causation-after-fairchild": UK_ISSUE,
    "canada-vavilov-standard-of-review": CANADA_ISSUE,
    "germany-right-to-be-forgotten-review": GERMANY_ISSUE,
    "eu-gdpr-article15-access-rights": EU_ISSUE,
}

RAW_HOLDOUTS = [
    {
        "id": "holdout-raw-us-deference-01",
        "profile": "common_law",
        "source_collection": "experiments/issue_gold_sets/manifests/us_agency_deference_after_loper_bright.json",
        "high": ["loper-bright-603-us-369", "apa-5-usc-706", "skidmore-323-us-134"],
        "counter": ["skidmore-323-us-134", "kisor-588-us-558"],
        "retrieved": ["loper-bright-603-us-369", "skidmore-323-us-134", "apa-5-usc-706", "kisor-588-us-558"],
        "assumptions": ["united_states_federal_administrative_law"],
    },
    {
        "id": "holdout-raw-us-deference-02",
        "profile": "common_law",
        "source_collection": "experiments/issue_gold_sets/manifests/us_agency_deference_after_loper_bright.json",
        "high": ["loper-bright-603-us-369", "apa-5-usc-706", "skidmore-323-us-134"],
        "counter": ["skidmore-323-us-134", "kisor-588-us-558"],
        "retrieved": ["apa-5-usc-706", "loper-bright-603-us-369", "kisor-588-us-558", "skidmore-323-us-134"],
        "assumptions": ["united_states_federal_administrative_law"],
    },
    {
        "id": "holdout-raw-uk-mesothelioma-01",
        "profile": "common_law",
        "source_collection": "experiments/issue_gold_sets/manifests/uk_mesothelioma_causation_after_fairchild.json",
        "high": ["fairchild-2002-ukhl-22", "sienkiewicz-2011-uksc-10"],
        "counter": ["barker-2006-ukhl-20", "compensation-act-2006-s3"],
        "retrieved": ["fairchild-2002-ukhl-22", "barker-2006-ukhl-20", "sienkiewicz-2011-uksc-10", "compensation-act-2006-s3"],
        "assumptions": ["england_and_wales_tort_law"],
    },
    {
        "id": "holdout-raw-uk-mesothelioma-02",
        "profile": "common_law",
        "source_collection": "experiments/issue_gold_sets/manifests/uk_mesothelioma_causation_after_fairchild.json",
        "high": ["fairchild-2002-ukhl-22", "sienkiewicz-2011-uksc-10"],
        "counter": ["barker-2006-ukhl-20", "compensation-act-2006-s3"],
        "retrieved": ["sienkiewicz-2011-uksc-10", "fairchild-2002-ukhl-22", "compensation-act-2006-s3", "barker-2006-ukhl-20"],
        "assumptions": ["england_and_wales_tort_law"],
    },
    {
        "id": "holdout-raw-eu-gdpr-01",
        "profile": "civil_law",
        "source_collection": "experiments/issue_gold_sets/manifests/eu_gdpr_article15_access_rights.json",
        "high": ["gdpr-art-15", "cjeu-c-154-21-osterreichische-post", "cjeu-c-487-21-crif"],
        "counter": ["gdpr-art-12-5", "gdpr-art-15-4"],
        "retrieved": ["gdpr-art-15", "cjeu-c-154-21-osterreichische-post", "gdpr-art-12-5", "cjeu-c-487-21-crif", "gdpr-art-15-4"],
        "assumptions": ["european_union_data_protection_law"],
    },
    {
        "id": "holdout-raw-eu-gdpr-02",
        "profile": "civil_law",
        "source_collection": "experiments/issue_gold_sets/manifests/eu_gdpr_article15_access_rights.json",
        "high": ["gdpr-art-15", "cjeu-c-154-21-osterreichische-post", "cjeu-c-307-22-ft"],
        "counter": ["gdpr-art-15-4", "gdpr-art-12-5"],
        "retrieved": ["cjeu-c-307-22-ft", "gdpr-art-15", "gdpr-art-15-4", "cjeu-c-154-21-osterreichische-post", "gdpr-art-12-5"],
        "assumptions": ["european_union_data_protection_law"],
    },
    {
        "id": "holdout-raw-canada-vavilov-01",
        "profile": "common_law",
        "source_collection": "experiments/issue_gold_sets/manifests/canada_vavilov_standard_of_review.json",
        "high": ["vavilov-2019-scc-65", "bell-canada-2019-scc-66", "canada-post-2019-scc-67"],
        "counter": ["dunsmuir-2008-scc-9", "vavilov-statutory-appeal-limits"],
        "retrieved": ["vavilov-2019-scc-65", "dunsmuir-2008-scc-9", "bell-canada-2019-scc-66", "canada-post-2019-scc-67", "vavilov-statutory-appeal-limits"],
        "assumptions": ["canadian_administrative_law"],
    },
    {
        "id": "holdout-raw-germany-rtbf-01",
        "profile": "civil_law",
        "source_collection": "experiments/issue_gold_sets/manifests/germany_right_to_be_forgotten_review.json",
        "high": ["bverfg-right-to-be-forgotten-i-1-bvr-16-13", "bverfg-right-to-be-forgotten-ii-1-bvr-276-17"],
        "counter": ["google-spain-c-131-12", "charter-articles-7-8-11-16"],
        "retrieved": ["bverfg-right-to-be-forgotten-i-1-bvr-16-13", "google-spain-c-131-12", "bverfg-right-to-be-forgotten-ii-1-bvr-276-17", "charter-articles-7-8-11-16"],
        "assumptions": ["german_constitutional_law"],
    },
]


def main() -> int:
    for path in (DOWNLOADS, MANIFESTS, SCENARIOS, RESULTS):
        path.mkdir(parents=True, exist_ok=True)
    for path in list(MANIFESTS.glob("*.json")) + list(SCENARIOS.glob("*.json")):
        path.unlink()

    public_rows = _write_public_holdouts()
    raw = [_raw_scenario(spec) for spec in RAW_HOLDOUTS]
    for scenario in raw:
        (SCENARIOS / f"{scenario['id']}.json").write_text(json.dumps(scenario, indent=2, ensure_ascii=False), encoding="utf-8")
    repaired = [_repair_holdout(scenario) for scenario in raw]
    for scenario in repaired:
        (SCENARIOS / f"{scenario['id']}.json").write_text(json.dumps(scenario, indent=2, ensure_ascii=False), encoding="utf-8")

    _run_harness()
    _write_summary(public_rows)
    return 0


def _write_public_holdouts() -> list[dict]:
    rows = []
    for slug in sorted(HOLDOUT_SLUGS):
        issue_id, query_index = slug.rsplit("-q", 1)
        issue = ISSUES[issue_id]
        query = issue["queries"][int(query_index) - 1]
        records = collect(issue, query, slug, DOWNLOADS, TOP_K, refresh=False)
        manifest = build_manifest(issue, query, slug, records, TOP_K)
        scenario = build_scenario(issue, query, slug, records)
        scenario["id"] = "holdout-" + scenario["id"]
        scenario["deployment_context"] = "Out-of-sample holdout packet. " + scenario["deployment_context"]
        scenario["evidence_packet"]["source_collection"] = f"experiments/holdout_validation/manifests/{slug}.json"
        scenario.pop("expected_allowed_status", None)
        scenario.pop("expected_disposition", None)
        (MANIFESTS / f"{slug}.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        (SCENARIOS / f"{scenario['id']}.json").write_text(json.dumps(scenario, indent=2, ensure_ascii=False), encoding="utf-8")
        rows.append({"id": scenario["id"], "kind": "public_retrieval", "records": len(records)})
    return rows


def _raw_scenario(spec: dict) -> dict:
    manifest = json.loads((ROOT / spec["source_collection"]).read_text(encoding="utf-8"))
    records = {record["id"]: record for record in manifest["records"]}
    output_units = []
    output_links = []
    for rank, source_id in enumerate(spec["retrieved"], start=1):
        record = records[source_id]
        support = record["source_support"][0]
        locator = support.get("locator") or record.get("citation") or record.get("source_url")
        claim = _claim(record, support)
        unit_id = f"unit-{rank:02d}"
        output_units.append(
            {
                "id": unit_id,
                "claim": claim,
                "source_ids": [source_id],
                "locators": [locator],
                "output_rank": rank,
            }
        )
        output_links.append(
            {
                "unit_id": unit_id,
                "source_id": source_id,
                "locator": locator,
                "supports_claim": True,
                "source_tag": "needs_verification",
            }
        )
    return {
        "id": spec["id"],
        "claimed_status": "normative_material_screening_output",
        "system_role": "auditable_procedural_tool",
        "jurisdiction_profile": spec["profile"],
        "deployment_context": "Out-of-sample raw model-style authority recommendation packet generated after the audit policy was frozen.",
        "scores": {
            "S": {"score": 1, "evidence": "Source names and locators are visible, but links are not procedurally source-bound."},
            "Q": {"score": 2, "evidence": "Holdout prompt family, issue, packet id and output version are recorded."},
            "H": {"score": 2, "evidence": "High-authority materials are identified against a holdout issue set."},
            "K": {"score": 2, "evidence": "Counter or limiting materials are visible in the output list."},
            "T": {"score": 1, "evidence": "The output can be inspected, but it has no party-facing contestation pathway."},
            "L": {"score": 1, "evidence": "The holdout output is logged, but not adopted as a decision reason."},
        },
        "authority_sets": {
            "high_authority": spec["high"],
            "retrieved_high_authority": [item for item in spec["retrieved"] if item in spec["high"]],
            "counter_or_limiting": spec["counter"],
            "retrieved_counter_or_limiting": [item for item in spec["retrieved"] if item in spec["counter"]],
            "invalid_or_superseded": [],
            "retrieved": spec["retrieved"],
        },
        "counter_material_complete": True,
        "upstream_metrics": {"precision": 1.0, "recall": 1.0, "f1": 1.0},
        "evidence_packet": {
            "source_collection": spec["source_collection"],
            "output_units": output_units,
            "output_links": output_links,
        },
        "review_gate": {
            "attorney_review_required": True,
            "review_status": "completed",
            "reliance_gate": "attorney_review",
            "jurisdiction_assumptions": spec["assumptions"],
            "contestability_channel": "holdout-source-bound-review-record",
            "irreversible_action": False,
            "human_authorization": False,
        },
    }


def _repair_holdout(scenario: dict) -> dict:
    repaired = json.loads(json.dumps(scenario))
    repaired["id"] = scenario["id"].replace("holdout-raw-", "holdout-source-bound-")
    repaired["deployment_context"] = "Out-of-sample source-bound repair packet scored after policy freeze."
    validation = validate_source_binding(repaired, ROOT / repaired["evidence_packet"]["source_collection"])
    if validation["all_links_source_bound"]:
        for link in repaired["evidence_packet"]["output_links"]:
            link["source_tag"] = "tool_verified"
            key = f"{link.get('unit_id')}::{link.get('source_id')}"
            link["support_label"] = "supports"
            evidence = validation["source_support_by_link"].get(key, [])
            link["validated_source_support"] = evidence
            link["validated_support_terms"] = sorted({term for item in evidence for term in item.get("matched_terms", [])})
        validation["source_tag_assignment"] = "assigned_after_holdout_manifest_locator_issue_set_and_source_support_validation"
    else:
        validation["source_tag_assignment"] = "not_assigned_validation_failed"
    repaired["source_binding_validation"] = validation
    repaired["scores"] = validated_scores(repaired, validation)
    if validation["all_links_source_bound"] and promote_counter_material_salience(repaired):
        repaired["deployment_context"] += " Rank salience repair moves an existing limiting material into the review window."
    return repaired


def _claim(record: dict, support: dict) -> str:
    terms = [str(term) for term in support.get("support_terms", [])[:2]]
    title = record.get("title", record["id"])
    if terms:
        return f"{title} is relevant because it addresses {' and '.join(terms)}."
    return f"{title} is relevant to the holdout issue."


def _run_harness() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "audit_harness.cli",
            "experiment",
            "experiments/holdout_validation/scenarios",
            "--out",
            "experiments/holdout_validation/results/holdout_validation.md",
            "--json-out",
            "experiments/holdout_validation/results/holdout_validation.json",
        ],
        cwd=ROOT,
        check=True,
    )


def _write_summary(public_rows: list[dict]) -> None:
    payload = json.loads((RESULTS / "holdout_validation.json").read_text(encoding="utf-8"))
    by_kind: dict[str, dict[str, int]] = {}
    for row in payload["results"]:
        kind = _kind(row["scenario_id"])
        entry = by_kind.setdefault(kind, {})
        entry[row["allowed_status"]] = entry.get(row["allowed_status"], 0) + 1
    lines = [
        "# Out-of-Sample Holdout Validation",
        "",
        "The holdout layer is built after freezing the scoring policy. It contains eight withheld public-retrieval packets, eight raw model-output packets and eight source-bound repair packets. Expected statuses are not stored in the scenario files.",
        "",
        f"Packets: {payload['summary']['scenario_count']}",
        f"Public retrieval records: {sum(row['records'] for row in public_rows)}",
        f"High-upstream-performance but procedurally blocked packets: {payload['summary']['high_upstream_but_blocked']}",
        "",
        "| Holdout kind | Status distribution |",
        "| --- | --- |",
    ]
    for kind, distribution in sorted(by_kind.items()):
        rendered = ", ".join(f"{status}: {count}" for status, count in sorted(distribution.items()))
        lines.append(f"| {kind} | {rendered} |")
    (RESULTS / "holdout_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _kind(scenario_id: str) -> str:
    if scenario_id.startswith("holdout-public-retrieval-"):
        return "public_retrieval"
    if scenario_id.startswith("holdout-raw-"):
        return "raw_model_output"
    if scenario_id.startswith("holdout-source-bound-"):
        return "source_bound_repair"
    return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
