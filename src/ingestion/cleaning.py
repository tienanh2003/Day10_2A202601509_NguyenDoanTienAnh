from __future__ import annotations

from datetime import datetime
import pandas as pd

from core.utils import normalize_whitespace
from ingestion.crossref import PaperRecord


CLEAN_COLUMNS = [
    "paper_id",
    "title",
    "summary",
    "authors",
    "categories",
    "primary_category",
    "published",
    "updated",
    "abs_url",
    "pdf_url",
    "comment",
    "authors_joined",
    "categories_joined",
    "summary_chars",
    "text_for_embedding",
    "age_days",
]


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    rows = []
    current_date = run_date.date() if isinstance(run_date, datetime) else run_date

    for r in records:
        title = normalize_whitespace(r.title)
        summary = normalize_whitespace(r.summary)
        authors = [normalize_whitespace(a) for a in r.authors if a]
        categories = [normalize_whitespace(c) for c in r.categories if c]
        authors_joined = ", ".join(authors) if authors else "Unknown Author"
        categories_joined = ", ".join(categories) if categories else "Uncategorized"

        published_str = r.published.strip() or "2025-01-01"
        try:
            pub_date = datetime.strptime(published_str, "%Y-%m-%d").date()
        except ValueError:
            pub_date = current_date

        age_days = max(0, (current_date - pub_date).days)
        summary_chars = len(summary)

        text_for_embedding = (
            f"Title: {title} | "
            f"Authors: {authors_joined} | "
            f"Categories: {categories_joined} | "
            f"Published: {published_str} | "
            f"Summary: {summary}"
        )

        rows.append(
            {
                "paper_id": r.paper_id.strip(),
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": r.primary_category or (categories[0] if categories else "Uncategorized"),
                "published": published_str,
                "updated": r.updated.strip() or published_str,
                "abs_url": r.abs_url,
                "pdf_url": r.pdf_url,
                "comment": r.comment,
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": summary_chars,
                "text_for_embedding": text_for_embedding,
                "age_days": age_days,
            }
        )

    if not rows:
        return pd.DataFrame(columns=CLEAN_COLUMNS)

    df = pd.DataFrame(rows)
    df = df.dropna(subset=["paper_id", "title", "summary"])
    df = df[(df["paper_id"].str.strip() != "") & (df["title"].str.strip() != "") & (df["summary"].str.strip() != "")]
    df = df[df["summary_chars"] >= 100]
    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    df = df.sort_values(by="published", ascending=False).reset_index(drop=True)
    return df


def build_clean_filter_log(records: list[PaperRecord], run_date: datetime, sample_size: int = 5) -> dict:
    rows = []
    current_date = run_date.date() if isinstance(run_date, datetime) else run_date

    for r in records:
        title = normalize_whitespace(r.title)
        summary = normalize_whitespace(r.summary)
        authors = [normalize_whitespace(a) for a in r.authors if a]
        categories = [normalize_whitespace(c) for c in r.categories if c]
        authors_joined = ", ".join(authors) if authors else "Unknown Author"
        categories_joined = ", ".join(categories) if categories else "Uncategorized"

        published_str = r.published.strip() or "2025-01-01"
        try:
            pub_date = datetime.strptime(published_str, "%Y-%m-%d").date()
        except ValueError:
            pub_date = current_date

        age_days = max(0, (current_date - pub_date).days)
        summary_chars = len(summary)
        text_for_embedding = (
            f"Title: {title} | "
            f"Authors: {authors_joined} | "
            f"Categories: {categories_joined} | "
            f"Published: {published_str} | "
            f"Summary: {summary}"
        )
        rows.append(
            {
                "paper_id": r.paper_id.strip(),
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": r.primary_category or (categories[0] if categories else "Uncategorized"),
                "published": published_str,
                "updated": r.updated.strip() or published_str,
                "abs_url": r.abs_url,
                "pdf_url": r.pdf_url,
                "comment": r.comment,
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": summary_chars,
                "text_for_embedding": text_for_embedding,
                "age_days": age_days,
            }
        )

    raw_count = len(rows)
    if not rows:
        return {
            "raw_record_count": 0,
            "clean_record_count": 0,
            "drop_counts": {
                "missing_required_fields": 0,
                "summary_too_short": 0,
                "duplicate_paper_id": 0,
            },
            "drop_samples": {
                "missing_required_fields": [],
                "summary_too_short": [],
                "duplicate_paper_id": [],
            },
        }

    df = pd.DataFrame(rows)
    required_mask = (
        df["paper_id"].notna()
        & df["title"].notna()
        & df["summary"].notna()
        & (df["paper_id"].astype(str).str.strip() != "")
        & (df["title"].astype(str).str.strip() != "")
        & (df["summary"].astype(str).str.strip() != "")
    )
    missing_required = df.loc[~required_mask, ["paper_id", "title", "summary_chars"]].head(sample_size)

    df_required = df.loc[required_mask].copy()
    summary_mask = df_required["summary_chars"] >= 100
    summary_too_short = df_required.loc[~summary_mask, ["paper_id", "title", "summary_chars"]].head(sample_size)

    df_summary = df_required.loc[summary_mask].copy()
    duplicate_mask = df_summary.duplicated(subset=["paper_id"], keep="first")
    duplicate_rows = df_summary.loc[duplicate_mask, ["paper_id", "title", "published"]].head(sample_size)

    df_clean = df_summary.loc[~duplicate_mask].copy()

    return {
        "raw_record_count": raw_count,
        "clean_record_count": int(len(df_clean)),
        "drop_counts": {
            "missing_required_fields": int((~required_mask).sum()),
            "summary_too_short": int((~summary_mask).sum()),
            "duplicate_paper_id": int(duplicate_mask.sum()),
        },
        "drop_samples": {
            "missing_required_fields": missing_required.to_dict(orient="records"),
            "summary_too_short": summary_too_short.to_dict(orient="records"),
            "duplicate_paper_id": duplicate_rows.to_dict(orient="records"),
        },
    }


def build_raw_to_clean_validation_sample(records: list[PaperRecord], df: pd.DataFrame, sample_size: int = 3) -> list[dict]:
    clean_by_paper_id = {
        str(row["paper_id"]): row
        for row in df.head(max(sample_size, 1)).to_dict(orient="records")
    }
    samples: list[dict] = []
    for record in records:
        if record.paper_id not in clean_by_paper_id:
            continue
        clean_row = clean_by_paper_id[record.paper_id]
        samples.append(
            {
                "paper_id": record.paper_id,
                "raw": {
                    "title": record.title,
                    "summary": record.summary,
                    "authors": record.authors,
                    "categories": record.categories,
                    "published": record.published,
                    "updated": record.updated,
                    "abs_url": record.abs_url,
                },
                "clean": {
                    "title": clean_row["title"],
                    "summary_chars": clean_row["summary_chars"],
                    "authors_joined": clean_row["authors_joined"],
                    "categories_joined": clean_row["categories_joined"],
                    "published": clean_row["published"],
                    "age_days": clean_row["age_days"],
                    "text_for_embedding_preview": str(clean_row["text_for_embedding"])[:240],
                },
            }
        )
        if len(samples) >= sample_size:
            break
    return samples

