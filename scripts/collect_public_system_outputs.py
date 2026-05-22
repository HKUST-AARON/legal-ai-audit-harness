from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from collect_real_cases import (
    BASE,
    collect_canada,
    collect_germany,
    collect_hong_kong,
    collect_mainland_china,
    collect_united_kingdom,
    collect_united_states,
    display_path,
    locator,
    profile_for,
)


DEFAULT_OUT = BASE / "experiments" / "public_system_outputs"
SOURCE_DOWNLOADS = BASE / "experiments" / "real_cases" / "downloads"
REQUIRED_SNAPSHOTS = [
    "canada_scc_json_feed.json",
    "germany_openlegaldata_cases.json",
    "hong_kong_hklii_hkcfa.json",
    "united_kingdom_tna_contract_page_1.xml",
    "united_kingdom_tna_contract_page_2.xml",
    "united_kingdom_tna_contract_page_3.xml",
    "united_states_scotus_term_22.html",
    "united_states_scotus_term_23.html",
    "united_states_scotus_term_24.html",
    "united_states_scotus_term_25.html",
    *[f"mainland_china_typicalcases_{index}.html" for index in range(1, 11)],
    *[f"mainland_china_typicalcases_{index}.md" for index in range(1, 11)],
]


COLLECTORS = [
    ("united_states", collect_united_states),
    ("united_kingdom", collect_united_kingdom),
    ("germany", collect_germany),
    ("canada", collect_canada),
    ("hong_kong", collect_hong_kong),
    ("mainland_china", collect_mainland_china),
]


SOURCE_LABELS = {
    "united_states": "Supreme Court of the United States slip-opinion output stream",
    "united_kingdom": "The National Archives Find Case Law Atom output stream",
    "germany": "OpenLegalData German case API output stream",
    "canada": "Supreme Court of Canada JSON output stream",
    "hong_kong": "HKLII Court of Final Appeal API output stream",
    "mainland_china": "Supreme People's Court English typical-cases output stream",
}


OFFICIAL_SOURCE_TAGS = {
    "united_states": "official_source",
    "united_kingdom": "official_source",
    "canada": "official_source",
    "mainland_china": "official_source",
    "germany": "public_metadata",
    "hong_kong": "public_metadata",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--refresh", action="store_true", help="download fresh source snapshots instead of using committed snapshots")
    args = parser.parse_args()

    out = args.out
    downloads = out / "downloads"
    manifests_dir = out / "manifests"
    scenarios_dir = out / "scenarios"
    results_dir = out / "results"
    for path in (downloads, manifests_dir, scenarios_dir, results_dir):
        path.mkdir(parents=True, exist_ok=True)

    if not args.refresh:
        seed_committed_snapshots(downloads)
        require_committed_snapshots(downloads)

    summaries = []
    for slug, collector in COLLECTORS:
        records = collector(downloads, args.refresh)
        output = records[: args.top_k]
        if len(output) < args.top_k:
            raise RuntimeError(f"{slug} produced {len(output)} records; need {args.top_k}")

        manifest = build_manifest(slug, records, output, args.top_k)
        scenario = build_scenario(slug, output)
        manifest_path = manifests_dir / f"{slug}.json"
        scenario_path = scenarios_dir / f"{slug}.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        scenario_path.write_text(json.dumps(scenario, indent=2, ensure_ascii=False), encoding="utf-8")
        summaries.append(
            {
                "jurisdiction": slug,
                "candidate_count": len(records),
                "output_count": len(output),
                "manifest": display_path(manifest_path),
                "scenario": display_path(scenario_path),
            }
        )

    run_harness(scenarios_dir, results_dir)
    write_summary(results_dir / "public_system_output_summary.md", summaries, args.top_k)
    return 0


def seed_committed_snapshots(downloads: Path) -> None:
    if not SOURCE_DOWNLOADS.exists():
        return
    for source in SOURCE_DOWNLOADS.iterdir():
        target = downloads / source.name
        if not target.exists():
            shutil.copy2(source, target)


def require_committed_snapshots(downloads: Path) -> None:
    missing = [name for name in REQUIRED_SNAPSHOTS if not (downloads / name).exists()]
    if missing:
        raise RuntimeError(
            "Missing committed public-system snapshots: "
            + ", ".join(missing)
            + ". Run with --refresh to download fresh snapshots."
        )


def build_manifest(slug: str, records: list[dict], output: list[dict], top_k: int) -> dict:
    return {
        "jurisdiction": slug,
        "created_at": "2026-05-23T00:00:00Z",
        "experiment": "public_legal_system_output_pilot",
        "source_output": {
            "label": SOURCE_LABELS[slug],
            "method": "top-k ordered records as exposed by the committed public system output snapshot",
            "top_k": top_k,
            "candidate_count": len(records),
        },
        "records": [dict(item, output_rank=index + 1) for index, item in enumerate(output)],
    }


def build_scenario(slug: str, output: list[dict]) -> dict:
    source_ids = [item["id"] for item in output]
    high_authority = [item["id"] for item in output if item["authority_level"] in {"apex_court", "guiding_or_typical_case"}]
    return {
        "id": f"public-system-output-{slug}",
        "claimed_status": "professional_support_output",
        "jurisdiction_profile": profile_for(slug),
        "deployment_context": "Provider-agnostic audit of the top ten records exposed by a public legal retrieval or listing system output.",
        "scores": {
            "S": {"score": 2, "evidence": "Each visible output item has a public source URL, source-system label, citation or docket field, and source identifier."},
            "Q": {"score": 2, "evidence": "The output stream, committed snapshot and top-k ordering are recorded in the manifest."},
            "H": {"score": 2 if high_authority else 1, "evidence": "Court, institution or authority-level labels are preserved for each visible item."},
            "K": {"score": 0, "evidence": "The public output exposes ordering but does not define an issue-specific ranking task or counter-material gold set."},
            "T": {"score": 1, "evidence": "A reviewer can inspect the public output items and source links; party-facing contestation is outside this pilot."},
            "L": {"score": 2, "evidence": "The harness writes a reproducible public-output manifest, scenario and result artifact."},
        },
        "authority_sets": {
            "high_authority": high_authority,
            "retrieved_high_authority": high_authority,
            "counter_or_limiting": [],
            "retrieved_counter_or_limiting": [],
            "invalid_or_superseded": [],
            "retrieved": source_ids,
        },
        "upstream_metrics": {
            "precision": None,
            "recall": None,
            "f1": None,
        },
        "evidence_packet": {
            "source_collection": f"experiments/public_system_outputs/manifests/{slug}.json",
            "output_units": [
                {
                    "id": f"rank-{index + 1:02d}",
                    "claim": f"Public system output rank {index + 1} makes this legal material visible: {item['title']}",
                    "source_ids": [item["id"]],
                    "locators": [locator(item)],
                    "output_rank": index + 1,
                }
                for index, item in enumerate(output)
            ],
            "output_links": [
                {
                    "unit_id": f"rank-{index + 1:02d}",
                    "source_id": item["id"],
                    "locator": locator(item),
                    "supports_claim": True,
                    "source_tag": OFFICIAL_SOURCE_TAGS[slug],
                }
                for index, item in enumerate(output)
            ],
        },
        "review_gate": {
            "attorney_review_required": True,
            "review_status": "source_integrity_only",
            "reliance_gate": "not_for_merits_reliance",
            "jurisdiction_assumptions": [profile_for(slug)],
            "irreversible_action": False,
            "human_authorization": False,
        },
        "expected_allowed_status": "professional_support_output",
        "expected_disposition": "none",
    }


def run_harness(scenarios_dir: Path, results_dir: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "audit_harness.cli",
            "experiment",
            str(scenarios_dir),
            "--out",
            str(results_dir / "public_system_output_experiment.md"),
            "--json-out",
            str(results_dir / "public_system_output_experiment.json"),
        ],
        cwd=BASE,
        check=True,
    )


def write_summary(path: Path, summaries: list[dict], top_k: int) -> None:
    lines = [
        "# Public Legal System Output Pilot",
        "",
        f"Top-k records per jurisdiction: `{top_k}`",
        "",
        "This pilot freezes ordered outputs from public legal retrieval or listing systems and converts the visible records into provider-agnostic evidence packets. It tests output reconstructability, source tagging and audit status allocation. It does not evaluate legal merits, doctrinal correctness, issue-specific ranking quality, or any upstream search/generation architecture.",
        "",
        "| Jurisdiction | Candidate records | Output records | Manifest | Scenario |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for item in summaries:
        lines.append(
            f"| {item['jurisdiction']} | {item['candidate_count']} | {item['output_count']} | `{item['manifest']}` | `{item['scenario']}` |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
