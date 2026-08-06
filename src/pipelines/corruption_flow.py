from __future__ import annotations

from datetime import datetime, UTC
import json
import pandas as pd

from core.config import load_settings
from core.utils import read_json, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    print("=== [CORRUPTION FLOW] Starting Corruption & Repair Flow ===")
    settings = load_settings()
    run_date = datetime.now(UTC)

    # 1. Load clean baseline dataset & metrics
    if not settings.paths.clean_json.exists():
        print("Clean dataset missing, fetching and cleaning raw records...")
        records = fetch_source_records(settings)
        df_clean = build_clean_dataframe(records, run_date)
        df_clean.to_csv(settings.paths.clean_csv, index=False)
        write_json(settings.paths.clean_json, json.loads(df_clean.to_json(orient="records")))
    else:
        df_clean = pd.DataFrame(read_json(settings.paths.clean_json))

    if settings.paths.baseline_metrics.exists():
        baseline_metrics = read_json(settings.paths.baseline_metrics)
    else:
        baseline_metrics = {
            "retrieval_hit_rate": 1.0,
            "mean_token_f1": 0.8,
            "judge_accuracy": 0.9,
            "mean_judge_score": 4.5,
        }

    # 2. Corrupt dataframe
    print("Corrupting clean dataframe...")
    df_corrupted = corrupt_clean_dataframe(df_clean, settings.paths.corruption_log)
    settings.paths.corrupted_clean_csv.parent.mkdir(parents=True, exist_ok=True)
    df_corrupted.to_csv(settings.paths.corrupted_clean_csv, index=False)
    df_corrupted.to_csv(settings.paths.clean_csv.parent / "papers_corrupted.csv", index=False)
    write_json(settings.paths.corrupted_clean_json, json.loads(df_corrupted.to_json(orient="records")))

    # 3. Build index & evaluate corrupted dataset
    print("Building Chroma index for corrupted data...")
    corrupted_index = LocalEmbeddingIndex.build(df_corrupted, settings, settings.paths.corrupted_embeddings_json)

    print("Evaluating corrupted dataset on test set...")
    corrupted_eval = evaluate_pipeline(
        settings,
        corrupted_index,
        settings.paths.eval_testset,
        settings.paths.corrupted_metrics,
        settings.paths.corrupted_answers,
    )
    print(f"Corrupted Evaluation Summary: {corrupted_eval.summary}")

    # 4. Quality & Freshness checks on corrupted data
    corrupted_quality = run_data_quality_checks(df_corrupted, settings, "corrupted_quality")
    corrupted_freshness = build_freshness_report(
        df_corrupted, settings, settings.paths.quality_dir / "freshness_report_corrupted.json"
    )

    # 5. Repair data by re-ingesting raw records & re-cleaning
    print("Repairing dataset from raw records source...")
    if settings.paths.raw_records_json.exists():
        raw_records = load_raw_records(settings.paths.raw_records_json)
    else:
        raw_records = fetch_source_records(settings)

    df_repaired = build_clean_dataframe(raw_records, run_date)
    df_repaired.to_csv(settings.paths.repaired_clean_csv, index=False)
    write_json(settings.paths.repaired_clean_json, json.loads(df_repaired.to_json(orient="records")))

    # 6. Build index & evaluate repaired dataset
    print("Building Chroma index for repaired data...")
    repaired_index = LocalEmbeddingIndex.build(df_repaired, settings, settings.paths.repaired_embeddings_json)

    print("Evaluating repaired dataset on test set...")
    repaired_eval = evaluate_pipeline(
        settings,
        repaired_index,
        settings.paths.eval_testset,
        settings.paths.repaired_metrics,
        settings.paths.repaired_answers,
    )
    print(f"Repaired Evaluation Summary: {repaired_eval.summary}")

    # 7. Quality & Freshness checks on repaired data
    repaired_quality = run_data_quality_checks(df_repaired, settings, "repaired_quality")
    repaired_freshness = build_freshness_report(
        df_repaired, settings, settings.paths.quality_dir / "freshness_report_repaired.json"
    )

    # 8. Generate comparison report
    print("Generating Comparison Report...")
    generate_corruption_report(
        settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_eval.summary,
        repaired_metrics=repaired_eval.summary,
        corrupted_answers=corrupted_eval.answers,
        repaired_answers=repaired_eval.answers,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )

    print("=== [CORRUPTION FLOW] Completed Successfully ===")

