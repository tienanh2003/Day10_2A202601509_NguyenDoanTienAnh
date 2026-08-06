from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
import re
import time
import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _clean_abstract(raw: str) -> str:
    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw)
    return normalize_whitespace(text)


def _extract_date(item: dict, fields: list[str]) -> str:
    for field in fields:
        if field in item and isinstance(item[field], dict):
            date_parts = item[field].get("date-parts", [[]])
            if date_parts and date_parts[0]:
                parts = date_parts[0]
                try:
                    year = int(parts[0]) if len(parts) > 0 else 2025
                    month = int(parts[1]) if len(parts) > 1 else 1
                    day = int(parts[2]) if len(parts) > 2 else 1
                    return f"{year:04d}-{month:02d}-{day:02d}"
                except (ValueError, TypeError):
                    continue
    return "2025-01-01"


def _stable_paper_id(item: dict, fallback_index: int) -> str:
    doi = normalize_whitespace(str(item.get("DOI", ""))).lower()
    if doi:
        return doi

    title_raw = item.get("title", [])
    if isinstance(title_raw, list):
        title = normalize_whitespace(str(title_raw[0])) if title_raw else ""
    else:
        title = normalize_whitespace(str(title_raw))

    author = ""
    author_entries = item.get("author", [])
    if author_entries and isinstance(author_entries[0], dict):
        author = normalize_whitespace(
            f"{author_entries[0].get('given', '')} {author_entries[0].get('family', '')}"
        ).lower()

    published = _extract_date(
        item,
        ["published", "published-print", "published-online", "issued", "created", "deposited"],
    )
    url = normalize_whitespace(str(item.get("URL", ""))).lower()
    fingerprint = "||".join(part for part in [title.lower(), author, published, url] if part)
    if not fingerprint:
        fingerprint = f"crossref-item-{fallback_index}"
    digest = hashlib.sha1(fingerprint.encode("utf-8")).hexdigest()[:16]
    return f"crossref-{digest}"


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []

    for item_index, item in enumerate(items, start=1):
        doi = item.get("DOI", "").strip()
        paper_id = _stable_paper_id(item, fallback_index=item_index)

        title_raw = item.get("title", [])
        if isinstance(title_raw, list):
            title = normalize_whitespace(title_raw[0]) if title_raw else ""
        else:
            title = normalize_whitespace(str(title_raw))

        summary = _clean_abstract(item.get("abstract", ""))

        # Authors
        authors: list[str] = []
        for author in item.get("author", []):
            if isinstance(author, dict):
                given = author.get("given", "").strip()
                family = author.get("family", "").strip()
                name = f"{given} {family}".strip() or author.get("name", "").strip()
                if name:
                    authors.append(name)
        if not authors:
            authors = ["Unknown Author"]

        # Categories
        categories_raw = item.get("subject", [])
        categories = [normalize_whitespace(str(c)) for c in categories_raw if c]
        primary_category = categories[0] if categories else "Computer Science"

        published = _extract_date(item, ["published", "published-print", "published-online", "issued", "created", "deposited"])
        updated = _extract_date(item, ["deposited", "indexed"]) or published

        abs_url = item.get("URL", f"https://doi.org/{doi}" if doi else "")
        
        pdf_url = abs_url
        for link in item.get("link", []):
            if isinstance(link, dict) and link.get("content-type") == "application/pdf":
                pdf_url = link.get("URL", abs_url)
                break

        comment = str(item.get("publisher", ""))

        if title and summary and len(summary) >= 20:
            records.append(
                PaperRecord(
                    paper_id=paper_id,
                    title=title,
                    summary=summary,
                    authors=authors,
                    categories=categories,
                    primary_category=primary_category,
                    published=published,
                    updated=updated,
                    abs_url=abs_url,
                    pdf_url=pdf_url,
                    comment=comment,
                )
            )

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    url = "https://api.crossref.org/works"
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    headers = {"User-Agent": "AgenticDataPipeline/1.0 (mailto:student@example.com)"}

    payload: dict | None = None
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            if resp.status_code == 200:
                payload = resp.json()
                break
            if resp.status_code in {429, 503}:
                retry_after = resp.headers.get("Retry-After", "").strip()
                if retry_after.isdigit():
                    sleep_seconds = int(retry_after)
                else:
                    sleep_seconds = min(2 ** attempt, 16)
                time.sleep(max(1, sleep_seconds))
                continue
            if 500 <= resp.status_code < 600 and attempt < max_attempts - 1:
                time.sleep(min(2 ** attempt, 16))
                continue
            resp.raise_for_status()
        except Exception:
            if attempt == max_attempts - 1:
                break
            time.sleep(min(2 ** attempt, 16))

    if payload is None:
        if settings.paths.raw_api_response.exists():
            payload = read_json(settings.paths.raw_api_response)
        else:
            raise RuntimeError("Failed to fetch records from Crossref API and no cached response found.")

    settings.paths.raw_api_response.parent.mkdir(parents=True, exist_ok=True)
    write_json(settings.paths.raw_api_response, payload)

    records = parse_crossref_payload(payload)
    records_dict = [asdict(r) for r in records]
    write_json(settings.paths.raw_records_json, records_dict)

    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    raw_data = read_json(path)
    records: list[PaperRecord] = []
    for item in raw_data:
        records.append(PaperRecord(**item))
    return records

