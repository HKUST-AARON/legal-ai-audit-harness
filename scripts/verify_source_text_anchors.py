from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "experiments" / "source_text_verification"
MANIFESTS = ROOT / "experiments" / "issue_gold_sets" / "manifests"

SOURCE_ALIASES = {
    "canada-post-2019-scc-67": ["https://scc-csc.lexum.com/scc-csc/scc-csc/en/item/18086/index.do"],
    "chevron-467-us-837": ["https://www.law.cornell.edu/supremecourt/text/467/837"],
    "apa-5-usc-706": ["https://www.law.cornell.edu/uscode/text/5/706"],
    "kisor-588-us-558": ["https://www.supremecourt.gov/opinions/18pdf/18-15_9p6b.pdf"],
    "gdpr-art-15": ["https://www.legislation.gov.uk/eur/2016/679/article/15"],
    "gdpr-art-12-5": ["https://www.legislation.gov.uk/eur/2016/679/article/12"],
    "gdpr-art-15-4": ["https://www.legislation.gov.uk/eur/2016/679/article/15"],
    "gdpr-art-4-9": ["https://www.legislation.gov.uk/eur/2016/679/article/4"],
    "cjeu-c-154-21-osterreichische-post": ["https://curia.europa.eu/jcms/upload/docs/application/pdf/2023-01/cp230004en.pdf"],
    "cjeu-c-487-21-crif": ["https://files.lbr.cloud/public/2023-05/ECJ%20dataset%20-%20CRIF%20-%20Judgment.pdf?VersionId=Y0gciLZJRdR4c3R4BvXic7bR5zTy5OrQ"],
    "cjeu-c-307-22-ft": ["https://curia.europa.eu/jcms/upload/docs/application/pdf/2023-10/cp230161en.pdf"],
    "google-spain-c-131-12": ["https://curia.europa.eu/jcms/upload/docs/application/pdf/2014-05/cp140070en.pdf"],
    "charter-articles-7-8-11-16": ["https://www.europarl.europa.eu/charter/pdf/text_en.pdf"],
    "fairchild-2002-ukhl-22": ["https://zoomlaw.co.uk/2002UKHL22.html"],
    "barker-2006-ukhl-20": ["https://www.globalhealthrights.org/wp-content/uploads/2013/03/HL-2006-Barker-v.-Corus-UK-Ltd.pdf"],
    "bonnington-1956-ac-613": ["https://lawprof.co/tort/causation-cases/bonnington-castings-ltd-v-wardlaw-1956-ac-613/"],
    "sienkiewicz-2011-uksc-10": ["https://caselaw.nationalarchives.gov.uk/uksc/2011/10/data.xml"],
    "durham-2012-uksc-14": ["https://caselaw.nationalarchives.gov.uk/uksc/2012/14/data.xml"],
    "williams-2011-ewca-civ-1242": ["https://caselaw.nationalarchives.gov.uk/ewca/civ/2011/1242/data.xml"],
    "heneghan-2016-ewca-civ-86": ["https://caselaw.nationalarchives.gov.uk/ewca/civ/2016/86/data.xml"],
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "v",
    "with",
}


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self.skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self.skip = False

    def handle_data(self, data: str) -> None:
        if not self.skip:
            self.parts.append(data)

    def text(self) -> str:
        return normalize_space(html.unescape(" ".join(self.parts)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--timeout", type=int, default=25)
    args = parser.parse_args()

    out = Path(args.out)
    snapshots = out / "snapshots"
    results = out / "results"
    snapshots.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)

    items = []
    record_seen: set[str] = set()
    records_with_snapshot: set[str] = set()
    for manifest_path in sorted(MANIFESTS.glob("*.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for record in manifest.get("records", []):
            record_id = record["id"]
            record_seen.add(record_id)
            snapshot = load_or_fetch_snapshot(record, snapshots, args.refresh, args.timeout)
            if snapshot["text_length"] > 0:
                records_with_snapshot.add(record_id)
            for support in record.get("source_support", []):
                item = verify_support_item(manifest_path, record, support, snapshot)
                items.append(item)

    verified = [item for item in items if item["verified"]]
    result = {
        "manifest_count": len(list(MANIFESTS.glob("*.json"))),
        "record_count": len(record_seen),
        "records_with_text_snapshot": len(records_with_snapshot),
        "support_item_count": len(items),
        "support_items_verified": len(verified),
        "support_items_unverified": len(items) - len(verified),
        "verified_ratio": round(len(verified) / len(items), 4) if items else None,
        "items": items,
    }
    (results / "source_text_anchor_verification.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (results / "source_text_anchor_verification.md").write_text(format_report(result), encoding="utf-8")
    print(format_report(result))
    return 0 if len(verified) >= 15 else 1


def load_or_fetch_snapshot(record: dict, snapshots: Path, refresh: bool, timeout: int) -> dict:
    for url in candidate_urls(record):
        path = snapshot_path(snapshots, record["id"], url)
        meta_path = path.with_suffix(".json")
        if refresh:
            fetched = fetch_source_text(url, timeout)
            if fetched["text"]:
                path.write_text(fetched["text"], encoding="utf-8")
                meta_path.write_text(
                    json.dumps(
                        {
                            "record_id": record["id"],
                            "url": url,
                            "status": fetched["status"],
                            "content_type": fetched["content_type"],
                            "sha256": hashlib.sha256(fetched["text"].encode("utf-8")).hexdigest(),
                            "text_length": len(fetched["text"]),
                        },
                        indent=2,
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )
            elif refresh and path.exists():
                path.unlink()
                if meta_path.exists():
                    meta_path.unlink()
        if path.exists():
            text = usable_source_text(path.read_text(encoding="utf-8", errors="ignore"))
            if not text:
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
            return {
                "url": meta.get("url", url),
                "path": str(path.relative_to(ROOT)),
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "text": text,
                "text_length": len(text),
            }
    return {"url": None, "path": None, "sha256": None, "text": "", "text_length": 0}


def candidate_urls(record: dict) -> list[str]:
    urls = []
    for url in SOURCE_ALIASES.get(record["id"], []):
        urls.append(url)
    if record.get("source_url"):
        urls.append(record["source_url"])
    for support in record.get("source_support", []):
        if support.get("source_url"):
            urls.append(support["source_url"])
    seen = set()
    ordered = []
    for url in urls:
        if url and url not in seen:
            seen.add(url)
            ordered.append(url)
    return ordered


def fetch_source_text(url: str, timeout: int) -> dict:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 legal-ai-audit-harness"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            content_type = response.headers.get("content-type", "")
            text = usable_source_text(extract_text(raw, content_type, url))
            return {
                "status": getattr(response, "status", None),
                "content_type": content_type,
                "text": text,
            }
    except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError):
        return {"status": None, "content_type": None, "text": ""}


def extract_text(raw: bytes, content_type: str, url: str) -> str:
    if not raw:
        return ""
    if "pdf" in content_type.lower() or url.lower().endswith(".pdf"):
        return extract_pdf_text(raw)
    text = raw.decode("utf-8", errors="ignore")
    if "<html" in text[:1000].lower() or "xml" in content_type.lower() or "<feed" in text[:1000].lower():
        parser = TextExtractor()
        parser.feed(text)
        return parser.text()
    return normalize_space(text)


def extract_pdf_text(raw: bytes) -> str:
    if not shutil.which("pdftotext"):
        return ""
    with tempfile.TemporaryDirectory() as directory:
        pdf_path = Path(directory) / "source.pdf"
        text_path = Path(directory) / "source.txt"
        pdf_path.write_bytes(raw)
        completed = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), str(text_path)],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0 or not text_path.exists():
            return ""
        return normalize_space(text_path.read_text(encoding="utf-8", errors="ignore"))


def verify_support_item(manifest_path: Path, record: dict, support: dict, snapshot: dict) -> dict:
    text = normalize_for_match(snapshot["text"])
    terms = meaningful_terms(support.get("support_terms", []))
    matched_terms = [term for term in terms if term_matches_text(term, text)]
    locator_terms = meaningful_terms([support.get("locator"), record.get("citation"), record.get("title")])
    matched_locators = [term for term in locator_terms if term_matches_text(term, text)]
    required = 1 if len(terms) <= 2 else 2
    verified = bool(snapshot["text"]) and len(matched_terms) >= required and (
        bool(matched_locators) or len(matched_terms) >= 2 or is_statutory_anchor(record, support)
    )
    return {
        "manifest": str(manifest_path.relative_to(ROOT)),
        "record_id": record["id"],
        "support_id": support["id"],
        "snapshot_path": snapshot["path"],
        "source_url": snapshot["url"],
        "snapshot_sha256": snapshot["sha256"],
        "text_length": snapshot["text_length"],
        "matched_terms": matched_terms,
        "missing_terms": [term for term in terms if term not in matched_terms],
        "matched_locator_terms": matched_locators,
        "verified": verified,
    }


def meaningful_terms(values: list[str | None]) -> list[str]:
    terms = []
    seen = set()
    for value in values:
        if not value:
            continue
        term = normalize_for_match(str(value))
        tokens = [token for token in term.split() if token not in STOPWORDS and len(token) > 1]
        if not tokens:
            continue
        normalized = " ".join(tokens)
        if normalized not in seen:
            seen.add(normalized)
            terms.append(normalized)
    return terms


def term_matches_text(term: str, text: str) -> bool:
    if not term:
        return False
    if term in text:
        return True
    tokens = term.split()
    if len(tokens) == 1:
        return re.search(rf"\b{re.escape(tokens[0])}\b", text) is not None
    return all(re.search(rf"\b{re.escape(token)}\b", text) for token in tokens)


def snapshot_path(snapshots: Path, record_id: str, url: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    return snapshots / f"{record_id}-{digest}.txt"


def normalize_for_match(value: str) -> str:
    value = value.lower()
    value = value.replace("\u2013", " ").replace("\u2014", " ").replace("-", " ")
    value = value.replace("§", " section ")
    value = re.sub(r"[^a-z0-9/().]+", " ", value)
    return normalize_space(value)


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def format_report(result: dict) -> str:
    lines = [
        "# Public Source Text Anchor Verification",
        "",
        f"Manifests: {result['manifest_count']}",
        f"Records: {result['record_count']}",
        f"Records with text snapshots: {result['records_with_text_snapshot']}",
        f"Support items verified: {result['support_items_verified']}/{result['support_item_count']}",
        f"Verified ratio: {result['verified_ratio']}",
        "",
        "| Manifest | Record | Support | Snapshot | Terms | Verified |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in result["items"]:
        terms = ", ".join(item["matched_terms"][:5])
        lines.append(
            "| "
            + " | ".join(
                [
                    item["manifest"].split("/")[-1],
                    item["record_id"],
                    item["support_id"],
                    "yes" if item["snapshot_path"] else "no",
                    terms or "none",
                    "yes" if item["verified"] else "no",
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def usable_source_text(text: str) -> str:
    if len(text) < 50:
        return ""
    lowered = text.lower()
    if "making sure you're not a bot" in lowered or "protected by anubis" in lowered:
        return ""
    if lowered.strip() == "rpex":
        return ""
    return text


def is_statutory_anchor(record: dict, support: dict) -> bool:
    combined = " ".join(str(value) for value in (record.get("citation"), record.get("title"), support.get("locator")))
    normalized = normalize_for_match(combined)
    return any(token in normalized for token in ("article", "section", "u.s.c", "usc", "code"))


if __name__ == "__main__":
    raise SystemExit(main())
