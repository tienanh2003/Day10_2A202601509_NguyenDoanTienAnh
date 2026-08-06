from __future__ import annotations

import pandas as pd
from core.utils import write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    if df.empty:
        write_json(output_log_path, {"status": "empty_dataframe"})
        return df.copy()

    corrupted = df.copy()
    initial_count = len(corrupted)

    # 1. Drop top 20% records (latest records)
    drop_count = max(1, int(initial_count * 0.2))
    corrupted = corrupted.iloc[drop_count:].reset_index(drop=True)
    curr_count = len(corrupted)

    # 2. Blank summary on ~20% of remaining rows
    blank_indices = list(range(0, curr_count, 5))
    corrupted.loc[blank_indices, "summary"] = ""
    corrupted.loc[blank_indices, "summary_chars"] = 0

    # 3. Inject noise into summary on ~20% of rows
    noise_indices = list(range(1, curr_count, 5))
    corrupted.loc[noise_indices, "summary"] = "CORRUPTED_GARBAGE_NOISE_999 " + corrupted.loc[noise_indices, "summary"].astype(str)
    corrupted.loc[noise_indices, "summary_chars"] = corrupted.loc[noise_indices, "summary"].astype(str).str.len()

    # 4. Truncate title on ~20% of rows
    trunc_indices = list(range(2, curr_count, 5))
    corrupted.loc[trunc_indices, "title"] = corrupted.loc[trunc_indices, "title"].astype(str).str.slice(0, 15) + "..."

    # 5. Stale date on ~20% of rows
    stale_indices = list(range(3, curr_count, 5))
    corrupted.loc[stale_indices, "published"] = "2010-01-01"
    corrupted.loc[stale_indices, "age_days"] = 5000

    # 6. Add duplicate rows
    dup_rows = corrupted.iloc[: min(2, curr_count)].copy()
    corrupted = pd.concat([corrupted, dup_rows], ignore_index=True)

    # 7. Rebuild text_for_embedding
    corrupted["text_for_embedding"] = (
        "Title: " + corrupted["title"].astype(str) + "\n" +
        "Authors: " + corrupted["authors_joined"].astype(str) + "\n" +
        "Categories: " + corrupted["categories_joined"].astype(str) + "\n" +
        "Published: " + corrupted["published"].astype(str) + "\n" +
        "Summary: " + corrupted["summary"].astype(str)
    )

    log_data = {
        "initial_rows": initial_count,
        "rows_dropped": drop_count,
        "summaries_blanked": len(blank_indices),
        "noise_injected": len(noise_indices),
        "titles_truncated": len(trunc_indices),
        "dates_staled": len(stale_indices),
        "duplicates_added": len(dup_rows),
        "final_rows": len(corrupted),
    }

    write_json(output_log_path, log_data)
    return corrupted

