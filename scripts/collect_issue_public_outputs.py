from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote, urljoin


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "experiments" / "issue_public_outputs"
DOWNLOADS = "downloads"
REQUIRED = [
    "us_courtlistener_loper_bright.json",
    "uk_tna_fairchild.xml",
    "eu_curia_c154.html",
    "eu_curia_c487.html",
    "eu_gdpr_article15.html",
    "eu_gdpr_article12.html",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    out = args.out
    downloads = out / DOWNLOADS
    manifests = out / "manifests"
    scenarios = out / "scenarios"
    results = out / "results"
    for path in (downloads, manifests, scenarios, results):
        path.mkdir(parents=True, exist_ok=True)
    if not args.refresh:
        missing = [name for name in REQUIRED if not (downloads / name).exists()]
        if missing:
            raise RuntimeError("Missing issue public-output snapshots: " + ", ".join(missing) + ". Run with --refresh.")

    experiments = [
        build_us(downloads, args.refresh),
        build_uk(downloads, args.refresh),
        build_eu(downloads, args.refresh),
    ]
    for manifest, scenario in experiments:
        slug = manifest["id"]
        (manifests / f"{slug}.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        (scenarios / f"{slug}.json").write_text(json.dumps(scenario, indent=2, ensure_ascii=False), encoding="utf-8")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "audit_harness.cli",
            "experiment",
            str(scenarios),
            "--out",
            str(results / "issue_public_output_experiment.md"),
            "--json-out",
            str(results / "issue_public_output_experiment.json"),
        ],
        cwd=ROOT,
        check=True,
    )
    write_summary(results / "issue_public_output_summary.md", experiments)
    return 0


def build_us(downloads: Path, refresh: bool) -> tuple[dict, dict]:
    query = "Loper Bright Chevron Skidmore Kisor"
    url = "https://www.courtlistener.com/api/rest/v4/search/?q=" + quote(query) + "&type=o&order_by=score%20desc"
    payload = json.loads(fetch(url, downloads / "us_courtlistener_loper_bright.json", refresh))
    records = []
    for rank, item in enumerate(payload.get("results", [])[:10], start=1):
        case_name = item.get("caseName") or item.get("caseNameFull") or "Untitled result"
        citations = item.get("citation") or []
        record_id = map_us_record(case_name, citations, item.get("absolute_url", ""))
        records.append(
            {
                "id": record_id,
                "title": case_name,
                "citation": "; ".join(citations),
                "source_url": urljoin("https://www.courtlistener.com", item.get("absolute_url", "")),
                "rank": rank,
                "source_system": "CourtListener opinion search API",
            }
        )
    manifest = {
        "id": "us-courtlistener-loper-bright",
        "jurisdiction": "united_states",
        "issue": "Agency statutory deference after Loper Bright.",
        "query": query,
        "source_system": "CourtListener opinion search API",
        "records": records,
    }
    retrieved = [record["id"] for record in records]
    high = ["loper-bright-603-us-369", "apa-5-usc-706", "skidmore-323-us-134"]
    counter = ["skidmore-323-us-134", "kisor-588-us-558"]
    scenario = issue_search_scenario(
        slug="us-courtlistener-loper-bright",
        profile="common_law",
        context="CourtListener issue-search output for U.S. agency deference after Loper Bright.",
        manifest_path="experiments/issue_public_outputs/manifests/us-courtlistener-loper-bright.json",
        records=records,
        high=high,
        retrieved_high=[item for item in retrieved if item in high],
        counter=counter,
        retrieved_counter=[item for item in retrieved if item in counter],
        expected="reference_information",
    )
    return manifest, scenario


def build_uk(downloads: Path, refresh: bool) -> tuple[dict, dict]:
    query = "Fairchild Barker Sienkiewicz mesothelioma"
    url = "https://caselaw.nationalarchives.gov.uk/atom.xml?query=" + quote(query) + "&page=1"
    raw = fetch(url, downloads / "uk_tna_fairchild.xml", refresh)
    root = ET.fromstring(raw)
    ns = {"atom": "http://www.w3.org/2005/Atom", "tna": "https://caselaw.nationalarchives.gov.uk"}
    records = []
    for rank, entry in enumerate(root.findall("atom:entry", ns)[:10], start=1):
        title = text(entry.find("atom:title", ns))
        identifier = next((item.text or "" for item in entry.findall("tna:identifier", ns) if item.get("type") == "ukncn"), "")
        link = next((item.get("href") or "" for item in entry.findall("atom:link", ns) if item.get("rel") == "alternate"), "")
        record_id = map_uk_record(title, identifier)
        records.append(
            {
                "id": record_id,
                "title": title,
                "citation": identifier,
                "source_url": link,
                "rank": rank,
                "source_system": "The National Archives Find Case Law Atom search",
            }
        )
    manifest = {
        "id": "uk-tna-fairchild-mesothelioma",
        "jurisdiction": "united_kingdom",
        "issue": "Mesothelioma causation after Fairchild, Barker, the Compensation Act 2006 and Sienkiewicz.",
        "query": query,
        "source_system": "The National Archives Find Case Law Atom search",
        "records": records,
    }
    retrieved = [record["id"] for record in records]
    high = ["fairchild-2002-ukhl-22", "compensation-act-2006-s3", "sienkiewicz-2011-uksc-10"]
    counter = ["barker-2006-ukhl-20"]
    scenario = issue_search_scenario(
        slug="uk-tna-fairchild-mesothelioma",
        profile="common_law",
        context="The National Archives issue-search output for English mesothelioma causation.",
        manifest_path="experiments/issue_public_outputs/manifests/uk-tna-fairchild-mesothelioma.json",
        records=records,
        high=high,
        retrieved_high=[item for item in retrieved if item in high],
        counter=counter,
        retrieved_counter=[item for item in retrieved if item in counter],
        expected="reference_information",
    )
    return manifest, scenario


def build_eu(downloads: Path, refresh: bool) -> tuple[dict, dict]:
    urls = [
        ("gdpr-art-15", "Regulation (EU) 2016/679 Article 15", "GDPR Article 15", "https://www.legislation.gov.uk/eur/2016/679/article/15/data.html", "eu_gdpr_article15.html"),
        ("cjeu-c-154-21-osterreichische-post", "RW v Österreichische Post AG", "Case C-154/21", "https://curia.europa.eu/juris/liste.jsf?language=en&num=C-154/21", "eu_curia_c154.html"),
        ("cjeu-c-487-21-crif", "Österreichische Datenschutzbehörde and CRIF", "Case C-487/21", "https://curia.europa.eu/juris/liste.jsf?language=en&num=C-487/21", "eu_curia_c487.html"),
        ("gdpr-art-12-5", "Regulation (EU) 2016/679 Article 12(5)", "GDPR Article 12(5)", "https://www.legislation.gov.uk/eur/2016/679/article/12/data.html", "eu_gdpr_article12.html"),
        ("gdpr-art-15-4", "Regulation (EU) 2016/679 Article 15(4)", "GDPR Article 15(4)", "https://www.legislation.gov.uk/eur/2016/679/article/15/data.html", "eu_gdpr_article15.html"),
    ]
    for _, _, _, url, filename in urls:
        fetch(url, downloads / filename, refresh)
    records = [
        {"id": record_id, "title": title, "citation": citation, "source_url": url, "rank": rank, "source_system": "Legislation.gov.uk/CURIA public source packet"}
        for rank, (record_id, title, citation, url, _) in enumerate(urls, start=1)
    ]
    manifest = {
        "id": "eu-official-gdpr-article15",
        "jurisdiction": "european_union",
        "issue": "GDPR Article 15 access to recipients and copies of personal data.",
        "query": "GDPR Article 15 C-154/21 C-487/21",
        "source_system": "Legislation.gov.uk and CURIA public source packet",
        "records": records,
    }
    scenario = issue_search_scenario(
        slug="eu-official-gdpr-article15",
        profile="civil_law",
        context="Legislation.gov.uk/CURIA public source packet for GDPR Article 15 access rights.",
        manifest_path="experiments/issue_public_outputs/manifests/eu-official-gdpr-article15.json",
        records=records,
        high=["gdpr-art-15", "cjeu-c-154-21-osterreichische-post", "cjeu-c-487-21-crif"],
        retrieved_high=["gdpr-art-15", "cjeu-c-154-21-osterreichische-post", "cjeu-c-487-21-crif"],
        counter=["gdpr-art-12-5", "gdpr-art-15-4"],
        retrieved_counter=["gdpr-art-12-5", "gdpr-art-15-4"],
        expected="normative_material_screening_output",
        scores={"S": 2, "Q": 2, "H": 2, "K": 2, "T": 2, "L": 1},
    )
    return manifest, scenario


def issue_search_scenario(
    *,
    slug: str,
    profile: str,
    context: str,
    manifest_path: str,
    records: list[dict],
    high: list[str],
    retrieved_high: list[str],
    counter: list[str],
    retrieved_counter: list[str],
    expected: str,
    scores: dict[str, int] | None = None,
) -> dict:
    scores = scores or {"S": 2, "Q": 2, "H": 1, "K": 1, "T": 1, "L": 2}
    return {
        "id": f"issue-public-output-{slug}",
        "claimed_status": "normative_material_screening_output",
        "jurisdiction_profile": profile,
        "deployment_context": context,
        "scores": {key: {"score": value, "evidence": "Score assigned from score-visible public issue output packet."} for key, value in scores.items()},
        "authority_sets": {
            "high_authority": high,
            "retrieved_high_authority": retrieved_high,
            "counter_or_limiting": counter,
            "retrieved_counter_or_limiting": retrieved_counter,
            "invalid_or_superseded": [],
            "retrieved": [record["id"] for record in records],
        },
        "counter_material_complete": True,
        "upstream_metrics": {
            "precision": None,
            "recall": None if not high else len(set(retrieved_high) & set(high)) / len(high),
            "f1": None,
        },
        "evidence_packet": {
            "source_collection": manifest_path,
            "output_units": [
                {
                    "id": f"rank-{record['rank']:02d}",
                    "claim": f"Issue-specific public output rank {record['rank']} makes this material visible: {record['title']}",
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
                    "source_tag": "official_source" if profile != "common_law" else "public_metadata",
                }
                for record in records
            ],
        },
        "review_gate": {
            "attorney_review_required": True,
            "review_status": "completed",
            "reliance_gate": "attorney_review",
            "jurisdiction_assumptions": [profile],
            "irreversible_action": False,
            "human_authorization": False,
        },
        "expected_allowed_status": expected,
        "expected_disposition": "none" if expected == "normative_material_screening_output" else "suspension",
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


def map_us_record(case_name: str, citations: list[str], absolute_url: str) -> str:
    citation_text = " ".join(citations).lower()
    if "603 u.s. 369" in citation_text:
        return "loper-bright-603-us-369"
    if "467 u.s. 837" in citation_text:
        return "chevron-467-us-837"
    if "323 u.s. 134" in citation_text:
        return "skidmore-323-us-134"
    if "588 u.s. 558" in citation_text:
        return "kisor-588-us-558"
    return "us-search-" + re.sub(r"[^a-z0-9]+", "-", case_name.lower()).strip("-")[:60]


def map_uk_record(title: str, citation: str) -> str:
    text_value = f"{title} {citation}".lower()
    if "fairchild" in text_value:
        return "fairchild-2002-ukhl-22"
    if "barker" in text_value:
        return "barker-2006-ukhl-20"
    if "sienkiewicz" in text_value:
        return "sienkiewicz-2011-uksc-10"
    return "uk-search-" + re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60]


def text(element) -> str:
    return "" if element is None or element.text is None else element.text.strip()


def write_summary(path: Path, experiments: list[tuple[dict, dict]]) -> None:
    lines = [
        "# Issue-Specific Public Output Study",
        "",
        "This study freezes two issue-specific public search outputs and one source-bound public-source packet. It tests whether visible public records preserve enough issue-specific authority and counter-material evidence to claim normative material screening status.",
        "",
        "| Output | Records | Expected status |",
        "| --- | ---: | --- |",
    ]
    for manifest, scenario in experiments:
        lines.append(f"| {manifest['id']} | {len(manifest['records'])} | {scenario['expected_allowed_status']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
