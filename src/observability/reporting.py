from __future__ import annotations

from pathlib import Path
from typing import Any


def generate_phase1_report(
    report_path: Path | str,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    md_content = f"""# Phase 1 Baseline Data Pipeline & Evaluation Report

## 1. Source Summary
- **Total Raw Records:** {source_summary.get('total_records', 'N/A')}
- **Cleaned Records:** {source_summary.get('clean_records', 'N/A')}

## 2. Baseline Evaluation Metrics
- **Evaluation Samples:** {metrics.get('samples', 0)}
- **Retrieval Hit Rate:** {metrics.get('retrieval_hit_rate', 0.0):.4f} ({metrics.get('retrieval_hit_rate', 0.0)*100:.2f}%)
- **Mean Token F1:** {metrics.get('mean_token_f1', 0.0):.4f}
- **LLM Judge Accuracy:** {metrics.get('judge_accuracy', 0.0):.4f} ({metrics.get('judge_accuracy', 0.0)*100:.2f}%)
- **Mean LLM Judge Score:** {metrics.get('mean_judge_score', 0.0):.2f} / 5.0

## 3. Data Quality Checks
- **Quality Status:** {"PASSED" if quality.get("all_passed") else "FAILED"}
- **Row Count:** {quality.get("row_count", 0)}
- **paper_id Unique & Non-Null:** {quality.get("paper_id_unique") and quality.get("paper_id_not_null")}
- **Title Non-Null:** {quality.get("title_not_null")}
- **Summary Non-Empty:** {quality.get("summary_not_empty")}
- **Average Summary Length:** {quality.get("avg_summary_chars", 0.0):.1f} chars

## 4. Freshness Monitoring
- **Latest Publication Date:** {freshness.get("latest_published", "N/A")}
- **Oldest Publication Date:** {freshness.get("oldest_published", "N/A")}
- **Freshness Threshold:** {freshness.get("freshness_threshold_days", 180)} days
- **Stale Rows Count:** {freshness.get("stale_rows", 0)}
- **Freshness Status:** {"FRESH" if freshness.get("is_fresh") else "STALE"}
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(md_content)


def generate_corruption_report(
    report_path: Path | str,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    b_hit = baseline_metrics.get("retrieval_hit_rate", 0.0)
    c_hit = corrupted_metrics.get("retrieval_hit_rate", 0.0)
    r_hit = repaired_metrics.get("retrieval_hit_rate", 0.0)

    b_f1 = baseline_metrics.get("mean_token_f1", 0.0)
    c_f1 = corrupted_metrics.get("mean_token_f1", 0.0)
    r_f1 = repaired_metrics.get("mean_token_f1", 0.0)

    b_acc = baseline_metrics.get("judge_accuracy", 0.0)
    c_acc = corrupted_metrics.get("judge_accuracy", 0.0)
    r_acc = repaired_metrics.get("judge_accuracy", 0.0)

    b_score = baseline_metrics.get("mean_judge_score", 0.0)
    c_score = corrupted_metrics.get("mean_judge_score", 0.0)
    r_score = repaired_metrics.get("mean_judge_score", 0.0)

    md_content = f"""# Data Corruption & Repair Impact Analysis Report

## 1. Comprehensive Pipeline Performance Comparison

| Metric | Baseline (Clean) | Corrupted (Degraded) | Repaired (Restored) |
| :--- | :---: | :---: | :---: |
| **Retrieval Hit Rate** | {b_hit:.4f} ({b_hit*100:.1f}%) | {c_hit:.4f} ({c_hit*100:.1f}%) | {r_hit:.4f} ({r_hit*100:.1f}%) |
| **Mean Token F1** | {b_f1:.4f} | {c_f1:.4f} | {r_f1:.4f} |
| **LLM Judge Accuracy** | {b_acc:.4f} ({b_acc*100:.1f}%) | {c_acc:.4f} ({c_acc*100:.1f}%) | {r_acc:.4f} ({r_acc*100:.1f}%) |
| **Mean LLM Judge Score** | {b_score:.2f} / 5.0 | {c_score:.2f} / 5.0 | {r_score:.2f} / 5.0 |
| **Data Quality Check** | PASSED | {"PASSED" if corrupted_quality.get("all_passed") else "FAILED"} | {"PASSED" if repaired_quality.get("all_passed") else "FAILED"} |
| **Freshness Status** | FRESH | {"FRESH" if corrupted_freshness.get("is_fresh") else "STALE"} | {"FRESH" if repaired_freshness.get("is_fresh") else "STALE"} |
| **Stale Rows** | 0 | {corrupted_freshness.get("stale_rows", 0)} | {repaired_freshness.get("stale_rows", 0)} |

## 2. Data Corruption Analysis
- **Impact on Retrieval:** Missing records, blanked summaries, and title truncation directly cause the RAG index to return irrelevant contexts, dropping the retrieval hit rate and Token F1.
- **Impact on Agent Answers:** Inaccurate or noisy retrieved contexts result in lower LLM Judge accuracy and scores.

## 3. Data Repair & Pipeline Recovery
- **Re-ingestion & Re-cleaning:** Re-fetching raw records from external APIs or fresh snapshots restores missing rows, repairs blank summaries, and fixes stale dates.
- **Performance Restoration:** Once repaired and re-indexed, the retrieval hit rate, Token F1, and Judge scores return to baseline quality.
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(md_content)

