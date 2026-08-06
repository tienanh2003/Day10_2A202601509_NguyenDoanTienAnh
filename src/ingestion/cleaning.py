from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, UTC
import pandas as pd

from core.utils import normalize_whitespace
from ingestion.crossref import PaperRecord


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
        return pd.DataFrame(
            columns=[
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
        )

    df = pd.DataFrame(rows)
    df = df.dropna(subset=["paper_id", "title", "summary"])
    df = df[(df["paper_id"].str.strip() != "") & (df["title"].str.strip() != "") & (df["summary"].str.strip() != "")]
    df = df[df["summary_chars"] >= 100]
    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    df = df.sort_values(by="published", ascending=False).reset_index(drop=True)
    return df

