from __future__ import annotations

from typing import Any
import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    row_count = len(df)
    if row_count == 0:
        results = {
            "report_name": report_name,
            "row_count": 0,
            "paper_id_not_null": False,
            "paper_id_unique": False,
            "title_not_null": False,
            "summary_not_empty": False,
            "avg_summary_chars": 0.0,
            "max_age_days": 0,
            "stale_count": 0,
            "all_passed": False,
        }
    else:
        paper_id_not_null = bool(df["paper_id"].notnull().all())
        paper_id_unique = bool(df["paper_id"].is_unique)
        title_not_null = bool((df["title"].notnull() & (df["title"].astype(str).str.strip() != "")).all())
        summary_not_empty = bool((df["summary"].notnull() & (df["summary"].astype(str).str.strip() != "")).all())
        avg_summary_chars = float(df["summary_chars"].mean()) if "summary_chars" in df.columns else float(df["summary"].astype(str).str.len().mean())
        max_age_days = int(df["age_days"].max()) if "age_days" in df.columns else 0
        stale_count = int((df["age_days"] > settings.freshness_threshold_days).sum()) if "age_days" in df.columns else 0

        all_passed = bool(
            row_count > 0
            and paper_id_not_null
            and paper_id_unique
            and title_not_null
            and summary_not_empty
        )

        results = {
            "report_name": report_name,
            "row_count": row_count,
            "paper_id_not_null": paper_id_not_null,
            "paper_id_unique": paper_id_unique,
            "title_not_null": title_not_null,
            "summary_not_empty": summary_not_empty,
            "avg_summary_chars": avg_summary_chars,
            "max_age_days": max_age_days,
            "stale_count": stale_count,
            "all_passed": all_passed,
        }

    settings.paths.quality_dir.mkdir(parents=True, exist_ok=True)
    out_file = settings.paths.quality_dir / f"{report_name}.json"
    write_json(out_file, results)
    return results


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    if df.empty:
        report = {
            "latest_published": "N/A",
            "oldest_published": "N/A",
            "freshness_threshold_days": settings.freshness_threshold_days,
            "stale_rows": 0,
            "total_rows": 0,
            "stale_percentage": 0.0,
            "is_fresh": True,
        }
    else:
        latest = str(df["published"].max())
        oldest = str(df["published"].min())
        total_rows = len(df)
        stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum()) if "age_days" in df.columns else 0
        stale_pct = float((stale_rows / total_rows) * 100) if total_rows > 0 else 0.0
        is_fresh = stale_rows == 0

        report = {
            "latest_published": latest,
            "oldest_published": oldest,
            "freshness_threshold_days": settings.freshness_threshold_days,
            "stale_rows": stale_rows,
            "total_rows": total_rows,
            "stale_percentage": stale_pct,
            "is_fresh": is_fresh,
        }

    write_json(report_path, report)
    return report

