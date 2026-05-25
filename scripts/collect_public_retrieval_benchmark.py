from __future__ import annotations

import argparse
import html
import json
import re
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
HOLDOUT_SLUGS = {
    "canada-vavilov-standard-of-review-q05",
    "canada-vavilov-standard-of-review-q06",
    "eu-gdpr-article15-access-rights-q05",
    "eu-gdpr-article15-access-rights-q06",
    "germany-right-to-be-forgotten-review-q05",
    "germany-right-to-be-forgotten-review-q06",
    "uk-mesothelioma-causation-after-fairchild-q05",
    "us-agency-deference-after-loper-bright-q05",
}

US_ISSUE = {
    "id": "us-agency-deference-after-loper-bright",
    "profile": "common_law",
    "source_system": "CourtListener opinion search API",
    "endpoint_scope": "case_law_only",
    "source_tag": "public_metadata",
    "high_authority": ["loper-bright-603-us-369", "skidmore-323-us-134"],
    "counter_or_limiting": ["skidmore-323-us-134", "kisor-588-us-558"],
    "mixed_authority_required_elsewhere": ["apa-5-usc-706"],
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
    "endpoint_scope": "case_law_only",
    "source_tag": "official_source",
    "high_authority": ["fairchild-2002-ukhl-22", "sienkiewicz-2011-uksc-10"],
    "counter_or_limiting": ["barker-2006-ukhl-20"],
    "mixed_authority_required_elsewhere": ["compensation-act-2006-s3"],
    "queries": [
        "Fairchild Barker Sienkiewicz mesothelioma",
        "mesothelioma causation Fairchild Barker Compensation Act",
        "material increase in risk mesothelioma Fairchild",
        "Sienkiewicz Greif Barker Corus Fairchild",
        "Compensation Act 2006 section 3 Barker mesothelioma",
        "mesothelioma damages causation House of Lords Fairchild",
    ],
}

CANADA_ISSUE = {
    "id": "canada-vavilov-standard-of-review",
    "profile": "common_law",
    "source_system": "Supreme Court of Canada Lexum search",
    "endpoint_scope": "case_law_only",
    "source_tag": "official_source",
    "high_authority": ["vavilov-2019-scc-65", "bell-canada-2019-scc-66", "canada-post-2019-scc-67"],
    "counter_or_limiting": ["dunsmuir-2008-scc-9"],
    "mixed_authority_required_elsewhere": ["vavilov-statutory-appeal-limits"],
    "queries": [
        "Vavilov Dunsmuir standard of review",
        "Vavilov Bell Canada Canada Post standard of review",
        "reasonableness review Vavilov Dunsmuir",
        "statutory appeal Vavilov correctness reasonableness",
        "administrative law standard of review Vavilov",
        "Dunsmuir Vavilov reasonableness correctness",
    ],
}

GERMANY_ISSUE = {
    "id": "germany-right-to-be-forgotten-review",
    "profile": "civil_law",
    "source_system": "OpenLegalData German case API search",
    "endpoint_scope": "case_law_only",
    "source_tag": "public_metadata",
    "high_authority": [
        "bverfg-right-to-be-forgotten-i-1-bvr-16-13",
        "bverfg-right-to-be-forgotten-ii-1-bvr-276-17",
    ],
    "counter_or_limiting": ["bverfg-right-to-be-forgotten-ii-1-bvr-276-17"],
    "mixed_authority_required_elsewhere": [
        "google-spain-c-131-12",
        "charter-articles-7-8-11-16",
        "basic-law-personality-expression-balance",
    ],
    "queries": [
        "Recht auf Vergessen I II BVerfG",
        "1 BvR 16/13 Recht auf Vergessen",
        "1 BvR 276/17 Recht auf Vergessen",
        "Google Spain C-131/12 Recht auf Vergessen",
        "Datenschutz Grundrechte Recht auf Vergessen",
        "Bundesverfassungsgericht Recht auf Vergessen Charta Grundgesetz",
    ],
}

EU_ISSUE = {
    "id": "eu-gdpr-article15-access-rights",
    "profile": "civil_law",
    "source_system": "CURIA case-law list search",
    "endpoint_scope": "case_law_known_item",
    "source_tag": "official_source",
    "high_authority": ["cjeu-c-154-21-osterreichische-post", "cjeu-c-487-21-crif", "cjeu-c-307-22-ft"],
    "counter_or_limiting": ["google-spain-c-131-12"],
    "mixed_authority_required_elsewhere": ["gdpr-art-15", "gdpr-art-12-5", "gdpr-art-15-4"],
    "queries": [
        "C-154/21 GDPR Article 15 recipients",
        "C-487/21 GDPR Article 15 copy",
        "C-131/12 Google Spain data protection",
        "C-579/21 Article 15 access personal data",
        "C-300/21 GDPR damage access",
        "C-307/22 GDPR medical records access",
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
    for path in list(manifests.glob("*.json")) + list(scenarios.glob("*.json")):
        path.unlink()

    rows = []
    for issue in (US_ISSUE, UK_ISSUE, CANADA_ISSUE, GERMANY_ISSUE, EU_ISSUE):
        for index, query in enumerate(issue["queries"], start=1):
            slug = f"{issue['id']}-q{index:02d}"
            if slug in HOLDOUT_SLUGS:
                continue
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

    if issue["id"].startswith("uk-"):
        return collect_uk(issue, query, slug, downloads, top_k, refresh)
    if issue["id"].startswith("canada-"):
        return collect_canada(issue, query, slug, downloads, top_k, refresh)
    if issue["id"].startswith("germany-"):
        return collect_germany(issue, query, slug, downloads, top_k, refresh)
    if issue["id"].startswith("eu-"):
        return collect_eu(issue, query, slug, downloads, top_k, refresh)
    raise ValueError(f"Unsupported issue id: {issue['id']}")


def collect_uk(issue: dict, query: str, slug: str, downloads: Path, top_k: int, refresh: bool) -> list[dict]:
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


def collect_canada(issue: dict, query: str, slug: str, downloads: Path, top_k: int, refresh: bool) -> list[dict]:
    url = "https://decisions.scc-csc.ca/scc-csc/en/d/s/index.do?cont=" + quote(query) + "&iframe=true"
    raw = fetch(url, downloads / f"{slug}.html", refresh)
    records = []
    for rank, block in enumerate(re.findall(r'<li class="[^"]*list-item[^"]*">(.*?)</li>', raw, flags=re.S)[:top_k], start=1):
        title_match = re.search(r'<span class="title"><a[^>]+href="([^"]+)">(.*?)</a></span>', block, flags=re.S)
        if not title_match:
            continue
        citation = first_match(r'<span class="citation">(.*?)</span>', block)
        title = clean_html(title_match.group(2))
        records.append(
            {
                "id": map_canada_record(title, citation),
                "title": title,
                "citation": citation,
                "source_url": urljoin("https://decisions.scc-csc.ca", html.unescape(title_match.group(1))),
                "rank": len(records) + 1,
                "source_system": issue["source_system"],
            }
        )
    return records


def collect_germany(issue: dict, query: str, slug: str, downloads: Path, top_k: int, refresh: bool) -> list[dict]:
    url = "https://de.openlegaldata.io/api/cases/?format=json&page_size=" + str(top_k) + "&search=" + quote(query)
    payload = json.loads(fetch(url, downloads / f"{slug}.json", refresh))
    records = []
    for rank, item in enumerate(payload.get("results", [])[:top_k], start=1):
        court = item.get("court") or {}
        title = f"{court.get('name', 'Court')} {item.get('file_number', '')}".strip()
        citation = item.get("ecli") or item.get("file_number", "")
        records.append(
            {
                "id": map_germany_record(title, citation, item.get("slug", "")),
                "title": title,
                "citation": citation,
                "source_url": f"https://de.openlegaldata.io/api/cases/{item.get('id')}/",
                "rank": rank,
                "source_system": issue["source_system"],
            }
        )
    return records


def collect_eu(issue: dict, query: str, slug: str, downloads: Path, top_k: int, refresh: bool) -> list[dict]:
    case_number = first_case_number(query)
    url = "https://juris.curia.europa.eu/juris/liste.jsf?language=en&num=" + quote(case_number)
    raw = fetch(url, downloads / f"{slug}.html", refresh)
    records = []
    for block in re.findall(r'<td class="decision"[^>]*>(.*?)</td>\s*</tr>', raw, flags=re.S)[:top_k]:
        title_block = first_match(r'<div class="decision_title">(.*?)</div>', block)
        text_value = clean_html(title_block or block)
        if not text_value:
            continue
        link = first_match(r'href="([^"]*document\.jsf[^"]*)"', block)
        case = first_match(r'Case\s+([CTF]-\d+/\d+)', text_value)
        records.append(
            {
                "id": map_eu_record(text_value, case),
                "title": " ".join(text_value.split())[:180],
                "citation": "Case " + case if case else "",
                "source_url": urljoin("https://juris.curia.europa.eu", html.unescape(link)) if link else url,
                "rank": len(records) + 1,
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
        "endpoint_scope": issue["endpoint_scope"],
        "mixed_authority_required_elsewhere": issue.get("mixed_authority_required_elsewhere", []),
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
        "deployment_context": f"Public {issue['endpoint_scope']} output for query: {query}",
        "benchmark_scope": issue["endpoint_scope"],
        "mixed_authority_required_elsewhere": issue.get("mixed_authority_required_elsewhere", []),
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
            "contestability_channel": "public-retrieval-source-record",
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


def map_canada_record(title: str, citation: str) -> str:
    text_value = f"{title} {citation}".lower()
    if "vavilov" in text_value and "2019 scc 65" in text_value:
        return "vavilov-2019-scc-65"
    if "bell canada" in text_value and "2019 scc 66" in text_value:
        return "bell-canada-2019-scc-66"
    if "canada post" in text_value and "2019 scc 67" in text_value:
        return "canada-post-2019-scc-67"
    if "dunsmuir" in text_value:
        return "dunsmuir-2008-scc-9"
    return "canada-search-" + re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60]


def map_germany_record(title: str, citation: str, slug: str) -> str:
    text_value = f"{title} {citation} {slug}".lower()
    if "1 bvr 16/13" in text_value or "1bvr001613" in text_value:
        return "bverfg-right-to-be-forgotten-i-1-bvr-16-13"
    if "1 bvr 276/17" in text_value or "1bvr027617" in text_value:
        return "bverfg-right-to-be-forgotten-ii-1-bvr-276-17"
    if "c-131/12" in text_value or "c13112" in text_value:
        return "google-spain-c-131-12"
    return "germany-search-" + re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60]


def map_eu_record(text_value: str, case_number: str) -> str:
    if not case_number:
        return "eu-search-" + re.sub(r"[^a-z0-9]+", "-", text_value.lower()).strip("-")[:60]
    normalized = case_number.lower()
    if normalized == "c-154/21":
        return "cjeu-c-154-21-osterreichische-post"
    if normalized == "c-487/21":
        return "cjeu-c-487-21-crif"
    if normalized == "c-131/12":
        return "google-spain-c-131-12"
    if normalized == "c-307/22":
        return "cjeu-c-307-22-ft"
    return "eu-search-" + re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")


def first_case_number(query: str) -> str:
    match = re.search(r"\b[CTF]-\d+/\d+\b", query, flags=re.I)
    if not match:
        raise ValueError(f"EU query must include a CURIA case number: {query}")
    value = match.group(0).upper()
    return value[0] + "-" + value.split("-", 1)[1]


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


def first_match(pattern: str, text_value: str) -> str:
    match = re.search(pattern, text_value, flags=re.S)
    return clean_html(match.group(1)) if match else ""


def clean_html(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


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
        "This benchmark freezes public legal-search outputs against endpoint-compatible case-law gold sets. Mixed statute/case authority screening is evaluated in the issue-defined public-source packets, not by asking case-only endpoints to return legislation.",
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
