from __future__ import annotations

from typing import Any
import pandas as pd

from core.utils import write_json


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    if df.empty:
        raise ValueError("Cannot build test set from an empty DataFrame.")

    sample_size = min(6, len(df))
    sample_df = df.iloc[:sample_size]

    test_set: list[dict[str, Any]] = []
    sample_idx = 1

    for _, row in sample_df.iterrows():
        paper_id = str(row["paper_id"])
        title = str(row["title"])
        summary = str(row["summary"])
        authors_joined = str(row["authors_joined"])
        published = str(row["published"])

        # Summary question
        test_set.append(
            {
                "id": f"q{sample_idx}",
                "question_type": "factual",
                "question": f"Tóm tắt chính của bài báo '{title}' là gì?",
                "ground_truth": summary,
                "ground_truth_doc_ids": [paper_id],
            }
        )
        sample_idx += 1

        # Authors question
        test_set.append(
            {
                "id": f"q{sample_idx}",
                "question_type": "factual",
                "question": f"Tác giả của bài báo '{title}' là ai?",
                "ground_truth": authors_joined,
                "ground_truth_doc_ids": [paper_id],
            }
        )
        sample_idx += 1

        # Date question
        test_set.append(
            {
                "id": f"q{sample_idx}",
                "question_type": "factual",
                "question": f"Bài báo '{title}' được xuất bản vào ngày nào?",
                "ground_truth": published,
                "ground_truth_doc_ids": [paper_id],
            }
        )
        sample_idx += 1

    write_json(output_path, test_set)
    return test_set

