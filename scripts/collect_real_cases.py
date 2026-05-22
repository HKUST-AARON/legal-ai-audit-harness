from __future__ import annotations

import argparse
import html
import json
import random
import re
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from shutil import which
from urllib.parse import urljoin


BASE = Path(__file__).resolve().parents[1]
DEFAULT_OUT = BASE / "experiments" / "real_cases"
SEED = 20260523


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--sample-size", type=int, default=20)
    parser.add_argument("--refresh", action="store_true", help="download fresh source snapshots instead of using committed snapshots when present")
    args = parser.parse_args()

    out = args.out
    downloads = out / "downloads"
    manifests_dir = out / "manifests"
    scenarios_dir = out / "scenarios"
    results_dir = out / "results"
    for path in (downloads, manifests_dir, scenarios_dir, results_dir):
        path.mkdir(parents=True, exist_ok=True)

    collectors = [
        ("hong_kong", collect_hong_kong),
        ("mainland_china", collect_mainland_china),
        ("united_states", collect_united_states),
        ("united_kingdom", collect_united_kingdom),
        ("germany", collect_germany),
        ("canada", collect_canada),
    ]

    scenario_paths = []
    manifest_paths = []
    summaries = []
    for offset, (slug, collector) in enumerate(collectors):
        candidates = collector(downloads, args.refresh)
        sample = sample_records(candidates, args.sample_size, args.seed + offset)
        manifest = build_manifest(slug, candidates, sample, args.seed + offset)
        scenario = build_scenario(slug, sample)

        manifest_path = manifests_dir / f"{slug}.json"
        scenario_path = scenarios_dir / f"{slug}.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        scenario_path.write_text(json.dumps(scenario, indent=2, ensure_ascii=False), encoding="utf-8")
        manifest_paths.append(manifest_path)
        scenario_paths.append(scenario_path)
        summaries.append(
            {
                "jurisdiction": slug,
                "candidate_count": len(candidates),
                "sample_size": len(sample),
                "manifest": display_path(manifest_path),
                "scenario": display_path(scenario_path),
            }
        )

    run_harness(scenarios_dir, results_dir)
    write_summary(results_dir / "source_manifest_summary.md", summaries, args.seed, args.sample_size)
    return 0


def collect_hong_kong(downloads: Path, refresh: bool) -> list[dict]:
    url = "https://www.hklii.org/api/getcasefiles?caseDb=hkcfa&lang=EN"
    raw = fetch(url, downloads / "hong_kong_hklii_hkcfa.json", refresh)
    payload = json.loads(raw)
    records = []
    for item in payload.get("judgments", []):
        case = (item.get("cases") or [{}])[0]
        title = case.get("title") or item.get("neutral") or item.get("path")
        records.append(
            record(
                "hong_kong",
                title=title,
                court=item.get("db", "Court of Final Appeal"),
                date=item.get("date", "")[:10],
                citation=item.get("neutral", ""),
                docket=case.get("act", ""),
                url=urljoin("https://www.hklii.org", item.get("path", "")),
                source="HKLII Court of Final Appeal API",
                authority_level="apex_court",
            )
        )
    return dedupe(records)


def collect_mainland_china(downloads: Path, refresh: bool) -> list[dict]:
    base = "https://english.court.gov.cn/"
    records = []
    for page in range(1, 11):
        name = "typicalcases.html" if page == 1 else f"typicalcases_{page}.html"
        url = urljoin(base, name)
        raw_path = downloads / f"mainland_china_typicalcases_{page}.html"
        raw = fetch(url, raw_path, refresh)
        snapshot_with_scrapling(url, raw_path.with_suffix(".md"), refresh)
        for date, href, title in re.findall(
            r"<h6>\s*([0-9]{4}-[0-9]{2}-[0-9]{2})\s*</h6>\s*<h4>\s*<a href=\"([^\"]+)\">(.*?)</a>",
            raw,
            flags=re.S,
        ):
            records.append(
                record(
                    "mainland_china",
                    title=clean(title),
                    court="Supreme People's Court / People's Courts",
                    date=date,
                    citation=extract_guiding_case_number(title),
                    docket="",
                    url=urljoin(base, href),
                    source="Supreme People's Court English Typical Cases",
                    authority_level="guiding_or_typical_case",
                )
            )
    return dedupe(records)


def collect_united_states(downloads: Path, refresh: bool) -> list[dict]:
    base = "https://www.supremecourt.gov"
    records = []
    for term in ("25", "24", "23", "22"):
        url = f"{base}/opinions/slipopinion/{term}"
        raw = fetch(url, downloads / f"united_states_scotus_term_{term}.html", refresh)
        for row in re.findall(r"<tr>(.*?)</tr>", raw, flags=re.S):
            cells = re.findall(r"<td[^>]*>(.*?)</td>", row, flags=re.S)
            if len(cells) < 6 or "href" not in cells[3]:
                continue
            href = re.search(r"href=['\"]([^'\"]+)['\"]", cells[3])
            title = re.search(r"<a[^>]*>(.*?)</a>", cells[3], flags=re.S)
            if not href or not title:
                continue
            records.append(
                record(
                    "united_states",
                    title=clean(title.group(1)),
                    court="Supreme Court of the United States",
                    date=normalize_us_date(clean(cells[1])),
                    citation=clean(cells[5]),
                    docket=clean(cells[2]),
                    url=urljoin(base, href.group(1)),
                    source="Supreme Court of the United States slip opinions",
                    authority_level="apex_court",
                )
            )
    return dedupe(records)


def collect_united_kingdom(downloads: Path, refresh: bool) -> list[dict]:
    records = []
    for page in range(1, 4):
        url = f"https://caselaw.nationalarchives.gov.uk/atom.xml?query=contract&page={page}"
        raw = fetch(url, downloads / f"united_kingdom_tna_contract_page_{page}.xml", refresh)
        root = ET.fromstring(raw)
        ns = {"atom": "http://www.w3.org/2005/Atom", "tna": "https://caselaw.nationalarchives.gov.uk"}
        for entry in root.findall("atom:entry", ns):
            link = next((l.get("href") for l in entry.findall("atom:link", ns) if l.get("rel") == "alternate" and not l.get("type")), "")
            identifier = next((i.text or "" for i in entry.findall("tna:identifier", ns) if i.get("type") == "ukncn"), "")
            records.append(
                record(
                    "united_kingdom",
                    title=text(entry.find("atom:title", ns)),
                    court=text(entry.find("atom:author/atom:name", ns)),
                    date=text(entry.find("atom:published", ns))[:10],
                    citation=identifier,
                    docket=text(entry.find("tna:uri", ns)),
                    url=link,
                    source="The National Archives Find Case Law Atom feed",
                    authority_level=uk_authority_level(identifier),
                )
            )
    return dedupe(records)


def collect_germany(downloads: Path, refresh: bool) -> list[dict]:
    url = "https://de.openlegaldata.io/api/cases/?format=json&page_size=100"
    raw = fetch(url, downloads / "germany_openlegaldata_cases.json", refresh)
    payload = json.loads(raw)
    records = []
    for item in payload.get("results", []):
        court = item.get("court") or {}
        records.append(
            record(
                "germany",
                title=f"{court.get('name', 'Court')} {item.get('file_number', '')}".strip(),
                court=court.get("name", ""),
                date=item.get("date", ""),
                citation=item.get("ecli") or item.get("file_number", ""),
                docket=item.get("file_number", ""),
                url=f"https://de.openlegaldata.io/api/cases/{item.get('id')}/",
                source="OpenLegalData German case API",
                authority_level=court.get("jurisdiction") or "court_decision",
            )
        )
    return dedupe(records)


def collect_canada(downloads: Path, refresh: bool) -> list[dict]:
    url = "https://decisions.scc-csc.ca/scc-csc/scc-csc/en/json/rss.do"
    raw = fetch(url, downloads / "canada_scc_json_feed.json", refresh)
    payload = json.loads(raw)
    records = []
    for item in payload.get("items", []):
        records.append(
            record(
                "canada",
                title=(item.get("title") or "").split(" - ")[0],
                court="Supreme Court of Canada",
                date=item.get("date_published", ""),
                citation=item.get("_neutral_citation") or item.get("_report_citation") or "",
                docket=", ".join(item.get("_docket_numbers", [])),
                url=item.get("url", ""),
                source="Supreme Court of Canada JSON feed",
                authority_level="apex_court",
            )
        )
    if len(records) >= 20:
        return dedupe(records)

    raw = fetch("https://decisions.scc-csc.ca/scc-csc/scc-csc/en/nav_date.do?iframe=true", downloads / "canada_scc_nav_date.html", refresh)
    for block in re.findall(r'<span class="title">(.*?)<div class="documents">', raw, flags=re.S):
        href = re.search(r'href="([^"]+)">([^<]+)</a>', block)
        citation = re.search(r'<span class="citation">([^<]+)</span>', block)
        if not href:
            continue
        records.append(
            record(
                "canada",
                title=clean(href.group(2)),
                court="Supreme Court of Canada",
                date="",
                citation=clean(citation.group(1)) if citation else "",
                docket="",
                url=urljoin("https://decisions.scc-csc.ca", href.group(1)),
                source="Supreme Court of Canada navigation by date",
                authority_level="apex_court",
            )
        )
    return dedupe(records)


def build_manifest(slug: str, candidates: list[dict], sample: list[dict], seed: int) -> dict:
    return {
        "jurisdiction": slug,
        "created_at": "2026-05-23T00:00:00Z",
        "sampling": {
            "method": "random.sample over normalized public case metadata candidates",
            "seed": seed,
            "candidate_count": len(candidates),
            "sample_size": len(sample),
        },
        "records": sample,
        "candidate_ids": [item["id"] for item in candidates],
    }


def build_scenario(slug: str, sample: list[dict]) -> dict:
    high_authority = [item["id"] for item in sample if item["authority_level"] in {"apex_court", "guiding_or_typical_case"}]
    source_ids = [item["id"] for item in sample]
    return {
        "id": f"real-cases-{slug}",
        "claimed_status": "professional_support_output",
        "jurisdiction_profile": profile_for(slug),
        "deployment_context": "Provider-agnostic source-manifest and output-evidence-packet test over 20 public case records.",
        "scores": {
            "S": {"score": 2, "evidence": "Each sampled item has a public source URL, citation or docket field, and source collection label."},
            "Q": {"score": 2, "evidence": "The source endpoint, timestamp, sampling seed and candidate pool are recorded."},
            "H": {"score": 2 if high_authority else 1, "evidence": "Court or authority labels are preserved in the manifest and evidence packet."},
            "K": {"score": 0, "evidence": "This metadata validation does not define an issue-specific ranking task or counter-material gold set."},
            "T": {"score": 1, "evidence": "A reviewer can inspect and challenge the manifest and source links; party-facing workflow is outside this source-integrity test."},
            "L": {"score": 2, "evidence": "The harness writes a reproducible scenario, manifest and report for audit review."},
        },
        "authority_sets": {
            "high_authority": high_authority,
            "retrieved_high_authority": high_authority,
            "counter_or_limiting": [],
            "retrieved_counter_or_limiting": [],
            "invalid_or_superseded": [],
            "retrieved": source_ids,
        },
        "evidence_packet": {
            "source_collection": f"experiments/real_cases/manifests/{slug}.json",
            "output_units": [
                {
                    "id": f"unit-{index + 1:02d}",
                    "source_ids": [item["id"]],
                    "locators": [locator(item)],
                }
                for index, item in enumerate(sample)
            ],
            "output_links": [
                {
                    "unit_id": f"unit-{index + 1:02d}",
                    "source_id": item["id"],
                    "locator": locator(item),
                    "supports_claim": True,
                    "source_tag": "public_metadata",
                }
                for index, item in enumerate(sample)
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


def fetch(url: str, path: Path, refresh: bool) -> str:
    if path.exists() and not refresh:
        return path.read_text(encoding="utf-8", errors="replace")
    request = urllib.request.Request(url, headers={"User-Agent": "legal-ai-audit-harness/0.1"})
    with urllib.request.urlopen(request, timeout=40) as response:
        raw = response.read()
    path.write_bytes(raw)
    return raw.decode("utf-8", errors="replace")


def snapshot_with_scrapling(url: str, path: Path, refresh: bool) -> None:
    if path.exists() and not refresh:
        return
    scrapling = which("scrapling")
    if not scrapling:
        return
    subprocess.run(
        [scrapling, "extract", "get", url, str(path), "--ai-targeted", "--timeout", "30"],
        cwd=BASE,
        check=False,
        capture_output=True,
        text=True,
    )


def sample_records(records: list[dict], sample_size: int, seed: int) -> list[dict]:
    if len(records) < sample_size:
        raise RuntimeError(f"Need {sample_size} records, got {len(records)}")
    return sorted(random.Random(seed).sample(records, sample_size), key=lambda item: item["id"])


def record(jurisdiction: str, title: str, court: str, date: str, citation: str, docket: str, url: str, source: str, authority_level: str) -> dict:
    title = clean(title)
    citation = clean(citation)
    docket = clean(docket)
    url = clean(url)
    stable = re.sub(r"[^a-z0-9]+", "-", f"{jurisdiction}-{citation or docket or title}".lower()).strip("-")
    return {
        "id": stable[:120],
        "title": title,
        "court": clean(court),
        "date": date,
        "citation": citation,
        "docket": docket,
        "url": url,
        "source": source,
        "authority_level": authority_level,
    }


def dedupe(records: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for item in records:
        if not item["id"] or item["id"] in seen:
            continue
        seen.add(item["id"])
        unique.append(item)
    return unique


def clean(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(BASE))
    except ValueError:
        return str(path)


def text(node) -> str:
    return "" if node is None or node.text is None else clean(node.text)


def locator(item: dict) -> str:
    parts = [item.get("citation"), item.get("docket"), item.get("date"), item.get("url")]
    return " | ".join(part for part in parts if part)


def extract_guiding_case_number(title: str) -> str:
    match = re.search(r"Guiding Case No\.?\s*([0-9]+)", clean(title), flags=re.I)
    return f"Guiding Case No. {match.group(1)}" if match else ""


def normalize_us_date(value: str) -> str:
    match = re.match(r"([0-9]{1,2})/([0-9]{1,2})/([0-9]{2})", value)
    if not match:
        return value
    month, day, year = match.groups()
    return f"20{year}-{int(month):02d}-{int(day):02d}"


def uk_authority_level(citation: str) -> str:
    if "UKSC" in citation:
        return "apex_court"
    if "EWCA" in citation:
        return "appellate_court"
    return "court_decision"


def profile_for(slug: str) -> str:
    if slug in {"germany", "mainland_china"}:
        return "civil_law"
    return "common_law"


def run_harness(scenarios_dir: Path, results_dir: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "audit_harness.cli",
            "experiment",
            str(scenarios_dir),
            "--out",
            str(results_dir / "real_case_experiment.md"),
            "--json-out",
            str(results_dir / "real_case_experiment.json"),
        ],
        cwd=BASE,
        check=True,
    )


def write_summary(path: Path, summaries: list[dict], seed: int, sample_size: int) -> None:
    lines = [
        "# Real Case Source Manifest Summary",
        "",
        f"Seed: `{seed}`",
        f"Sample size per jurisdiction: `{sample_size}`",
        "",
        "This public metadata evidence-packet validation tests whether a provider-agnostic legal-output evidence packet can be constructed from committed public case metadata snapshots. It does not evaluate legal merits, doctrinal correctness, ranking quality, or any upstream retrieval/generation architecture. Metadata-only packets are capped at professional-support status because they do not define issue-specific counter-material gold sets.",
        "",
        "| Jurisdiction | Candidate records | Sampled records | Manifest | Scenario |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for item in summaries:
        lines.append(
            f"| {item['jurisdiction']} | {item['candidate_count']} | {item['sample_size']} | `{item['manifest']}` | `{item['scenario']}` |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
