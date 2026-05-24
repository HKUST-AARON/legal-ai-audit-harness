from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote, urljoin

from collect_issue_public_outputs import map_uk_record, map_us_record


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "experiments" / "public_retrieval_benchmark"
TOP_K = 10

US_ISSUE = {
    "id": "us-agency-deference-after-loper-bright",
    "profile": "common_law",
    "source_system": "CourtListener opinion search API",
    "source_tag": "public_metadata",
    "high_authority": ["loper-bright-603-us-369", "apa-5-usc-706", "skidmore-323-us-134"],
    "counter_or_limiting": ["skidmore-323-us-134", "kisor-588-us-558"],
    "queries": [
        "Loper Bright Chevron Skidmore Kisor",
        "agency deference after Loper Bright Chevron",
        "Chevron overruled Skidmore APA 706",
        "Loper Bright independent judgment 5 USC 706",
        "Kisor Skidmore Chevron Loper",
        "judicial review agency statutory interpretation after Loper Bright",
    ],
}

UK_ISSUE = {
    "id": "uk-mesothelioma-causation-after-fairchild",
    "profile": "common_law",
    "source_system": "The National Archives Find Case Law Atom search",
    "source_tag": "official_source",
    "high_authority": ["fairchild-2002-ukhl-22", "compensation-act-2006-s3", "sienkiewicz-2011-uksc-10"],
    "counter_or_limiting": ["barker-2006-ukhl-20", "compensation-act-2006-s3"],
    "queries": [
        "Fairchild Barker Sienkiewicz mesothelioma",
        "mesothelioma causation Fairchild Barker Compensation Act",
        "material increase in risk mesothelioma Fairchild",
        "Sienkiewicz Greif Barker Corus Fairchild",
        "Compensation Act 2006 section 3 Barker mesothelioma",
        "mesothelioma damages causation House of Lords Fairchild",
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--top-k", type=int, default=TOP_K)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    downloads = args.out / "downloads"
    manifests = args.out / "manifests"
    scenarios = args.out / "scenarios"
    results = args.out / "results"
    for path in (downloads, manifests, scenarios, results):
        path.mkdir(parents=True, exist_ok=True)

    rows = []
    for issue in (US_ISSUE, UK_ISSUE):
        for index, query in enumerate(issue["queries"], start=1):
            slug = f"{issue['id']}-q{index:02d}"
            records = collect(issue, query, slug, downloads, args.top_k, args.refresh)
            manifest = build_manifest(issue, query, slug, records, args.top_k)
            scenario = build_scenario(issue, query, slug, records)
            (manifests / f"{slug}.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
            (scenarios / f"{slug}.json").write_text(json.dumps(scenario, indent=2, ensure_ascii=False), encoding="utf-8")
            rows.append(summary_row(issue, query, slug, records))

    run_harness(scenarios, results)
    write_summary(results / "public_retrieval_benchmark_summary.md", rows)
    return 0


def collect(issue: dict, query: str, slug: str, downloads: Path, top_k: int, refresh: bool) -> list[dict]:
    if issue["id"].startswith("us-"):
        url = "https://www.courtlistener.com/api/rest/v4/search/?q=" + quote(query) + "&type=o&order_by=score%20desc"
        payload = json.loads(fetch(url, downloads / f"{slug}.json", refresh))
        records = []
        for rank, item in enumerate(payload.get("results", [])[:top_k], start=1):
            case_name = item.get("caseName") or item.get("caseNameFull") or "Untitled result"
            citations = item.get("citation") or []
            records.append(
                {
                    "id": map_us_record(case_name, citations, item.get("absolute_url", "")),
                    "title": case_name,
                    "citation": "; ".join(citations),
                    "source_url": urljoin("https://www.courtlistener.com", item.get("absolute_url", "")),
                    "rank": rank,
                    "source_system": issue["source_system"],
                }
            )
        return records

    url = "https://caselaw.nationalarchives.gov.uk/atom.xml?query=" + quote(query) + "&page=1"
    raw = fetch(url, downloads / f"{slug}.xml", refresh)
    root = ET.fromstring(raw)
    ns = {"atom": "http://www.w3.org/2005/Atom", "tna": "https://caselaw.nationalarchives.gov.uk"}
    records = []
    for rank, entry in enumerate(root.findall("atom:entry", ns)[:top_k], start=1):
        title = text(entry.find("atom:title", ns))
        identifier = next((item.text or "" for item in entry.findall("tna:identifier", ns) if item.get("type") == "ukncn"), "")
        link = next((item.get("href") or "" for item in entry.findall("atom:link", ns) if item.get("rel") == "alternate"), "")
        records.append(
            {
                "id": map_uk_record(title, identifier),
                "title": title,
                "citation": identifier,
                "source_url": link,
                "rank": rank,
                "source_system": issue["source_system"],
            }
        )
    return records


def build_manifest(issue: dict, query: str, slug: str, records: list[dict], top_k: int) -> dict:
    return {
        "id": slug,
        "issue_id": issue["id"],
        "query": query,
        "top_k": top_k,
        "source_system": issue["source_system"],
        "records": records,
    }


def build_scenario(issue: dict, query: str, slug: str, records: list[dict]) -> dict:
    retrieved = [record["id"] for record in records]
    high = issue["high_authority"]
    counter = issue["counter_or_limiting"]
    retrieved_high = [item for item in retrieved if item in high]
    retrieved_counter = [item for item in retrieved if item in counter]
    high_complete = set(high).issubset(set(retrieved_high))
    counter_complete = set(counter).issubset(set(retrieved_counter))
    procedural_source = issue["source_tag"] == "official_source"
    expected = "normative_material_screening_output" if high_complete and counter_complete and procedural_source else "reference_information"
    disposition = "none" if expected == "normative_material_screening_output" else ("suspension" if not high_complete or not counter_complete else "downgrade")
    return {
        "id": f"public-retrieval-{slug}",
        "claimed_status": "normative_material_screening_output",
        "system_role": "auditable_procedural_tool",
        "jurisdiction_profile": issue["profile"],
        "deployment_context": f"Public search output for query: {query}",
        "scores": {
            "S": {"score": 2, "evidence": "Every visible result has a public source URL and source-system label."},
            "Q": {"score": 2, "evidence": "The query, source endpoint, snapshot and rank window are recorded."},
            "H": {"score": 2 if high_complete else 1, "evidence": "The benchmark compares returned records with an issue-defined high-authority set."},
            "K": {"score": 2 if counter_complete else 1, "evidence": "The benchmark compares returned records with an issue-defined counter-material set."},
            "T": {"score": 1, "evidence": "The output can be inspected by a reviewer but does not create a party-facing contestation pathway."},
            "L": {"score": 2, "evidence": "The query, manifest, scenario and harness result are logged as reproducible artifacts."},
        },
        "authority_sets": {
            "high_authority": high,
            "retrieved_high_authority": retrieved_high,
            "counter_or_limiting": counter,
            "retrieved_counter_or_limiting": retrieved_counter,
            "invalid_or_superseded": [],
            "retrieved": retrieved,
        },
        "counter_material_complete": True,
        "upstream_metrics": {
            "precision": precision(retrieved, high, counter),
            "recall": len(set(retrieved_high) & set(high)) / len(high),
            "f1": None,
        },
        "evidence_packet": {
            "source_collection": f"experiments/public_retrieval_benchmark/manifests/{slug}.json",
            "output_units": [
                {
                    "id": f"rank-{record['rank']:02d}",
                    "claim": f"Public search rank {record['rank']} makes this material visible: {record['title']}",
                    "source_ids": [record["id"]],
                    "locators": [record["citation"] or record["source_url"]],
                    "output_rank": record["rank"],
                }
                for record in records
            ],
            "output_links": [
                {
                    "unit_id": f"rank-{record['rank']:02d}",
                    "source_id": record["id"],
                    "locator": record["citation"] or record["source_url"],
                    "supports_claim": True,
                    "source_tag": issue["source_tag"],
                }
                for record in records
            ],
        },
        "review_gate": {
            "attorney_review_required": True,
            "review_status": "completed",
            "reliance_gate": "attorney_review",
            "jurisdiction_assumptions": [issue["profile"]],
            "irreversible_action": False,
            "human_authorization": False,
        },
        "expected_allowed_status": expected,
        "expected_disposition": disposition,
    }


def precision(retrieved: list[str], high: list[str], counter: list[str]) -> float | None:
    if not retrieved:
        return None
    relevant = set(high) | set(counter)
    return len([item for item in retrieved if item in relevant]) / len(retrieved)


def summary_row(issue: dict, query: str, slug: str, records: list[dict]) -> dict:
    retrieved = {record["id"] for record in records}
    high = set(issue["high_authority"])
    counter = set(issue["counter_or_limiting"])
    return {
        "id": slug,
        "issue": issue["id"],
        "query": query,
        "records": len(records),
        "high_authority_recall": len(retrieved & high) / len(high),
        "counter_material_recall": len(retrieved & counter) / len(counter),
    }


def fetch(url: str, path: Path, refresh: bool) -> str:
    if path.exists() and not refresh:
        return path.read_text(encoding="utf-8")
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 legal-ai-audit-harness"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read()
    text_data = data.decode("utf-8", "replace")
    path.write_text(text_data, encoding="utf-8")
    return text_data


def text(element) -> str:
    return "" if element is None or element.text is None else element.text.strip()


def run_harness(scenarios: Path, results: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "audit_harness.cli",
            "experiment",
            str(scenarios),
            "--out",
            str(results / "public_retrieval_benchmark.md"),
            "--json-out",
            str(results / "public_retrieval_benchmark.json"),
        ],
        cwd=ROOT,
        check=True,
    )


def write_summary(path: Path, rows: list[dict]) -> None:
    lines = [
        "# Public Retrieval Benchmark",
        "",
        "This benchmark freezes true public search outputs for issue-defined legal-retrieval tasks. It measures whether top-k returned records preserve high-authority and counter-material coverage before any claim to normative material screening.",
        "",
        "| Trial | Records | High-authority recall | Counter-material recall | Query |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['id']} | {row['records']} | {row['high_authority_recall']:.2f} | {row['counter_material_recall']:.2f} | {row['query']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
