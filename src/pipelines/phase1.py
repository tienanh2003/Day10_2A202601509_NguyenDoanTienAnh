from __future__ import annotations

from datetime import datetime, UTC

from core.config import load_settings
from core.utils import write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe, build_clean_filter_log, build_raw_to_clean_validation_sample
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    print("=== [PHASE 1] Starting Baseline Pipeline ===")
    settings = load_settings()
    run_date = datetime.now(UTC)

    # 1. Fetch / load raw records
    if settings.refresh_source or not settings.paths.raw_records_json.exists():
        print("Fetching raw records from source...")
        records = fetch_source_records(settings)
    else:
        print("Loading raw records from snapshot...")
        records = load_raw_records(settings.paths.raw_records_json)

    print(f"Ingested {len(records)} raw records.")

    # 2. Clean data
    df_clean = build_clean_dataframe(records, run_date)
    print(f"Cleaned dataset contains {len(df_clean)} rows.")

    settings.paths.clean_csv.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(settings.paths.clean_csv, index=False)
    write_json(settings.paths.clean_json, df_clean.to_dict(orient="records"))
    write_json(settings.paths.clean_filter_log, build_clean_filter_log(records, run_date))
    write_json(
        settings.paths.raw_clean_validation_sample,
        build_raw_to_clean_validation_sample(records, df_clean),
    )

    # 3. Build vector index
    print("Building baseline Chroma vector index...")
    index = LocalEmbeddingIndex.build(df_clean, settings, settings.paths.embeddings_json)
    write_json(settings.paths.retrieval_smoke_checks, index.build_smoke_checks())

    # 4. Build or load evaluation set
    print("Building evaluation test set...")
    build_test_set(df_clean, settings.paths.eval_testset)

    # 5. Evaluate baseline
    print("Evaluating baseline RAG pipeline...")
    eval_bundle = evaluate_pipeline(
        settings,
        index,
        settings.paths.eval_testset,
        settings.paths.baseline_metrics,
        settings.paths.baseline_answers,
    )
    print(f"Baseline Summary: {eval_bundle.summary}")

    # 6. Quality & Freshness checks
    print("Running Data Quality & Freshness checks...")
    quality = run_data_quality_checks(df_clean, settings, "baseline_quality")
    freshness = build_freshness_report(df_clean, settings, settings.paths.freshness_report)

    # 7. Generate markdown report
    print("Generating Phase 1 Markdown report...")
    generate_phase1_report(
        settings.paths.baseline_report,
        source_summary={"total_records": len(records), "clean_records": len(df_clean)},
        metrics=eval_bundle.summary,
        answers=eval_bundle.answers,
        quality=quality,
        freshness=freshness,
    )

    print("=== [PHASE 1] Baseline Pipeline Completed Successfully ===")

