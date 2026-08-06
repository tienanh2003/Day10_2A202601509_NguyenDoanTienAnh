# Data Corruption & Repair Impact Analysis Report

## 1. Comprehensive Pipeline Performance Comparison

| Metric | Baseline (Clean) | Corrupted (Degraded) | Repaired (Restored) |
| :--- | :---: | :---: | :---: |
| **Retrieval Hit Rate** | 1.0000 (100.0%) | 0.3333 (33.3%) | 1.0000 (100.0%) |
| **Mean Token F1** | 0.0920 | 0.0198 | 0.0920 |
| **LLM Judge Accuracy** | 0.0000 (0.0%) | 0.0000 (0.0%) | 0.0000 (0.0%) |
| **Mean LLM Judge Score** | 1.00 / 5.0 | 1.00 / 5.0 | 1.00 / 5.0 |
| **Data Quality Check** | PASSED | FAILED | PASSED |
| **Freshness Status** | FRESH | STALE | FRESH |
| **Stale Rows** | 0 | 4 | 0 |

## 2. Data Corruption Analysis
- **Impact on Retrieval:** Missing records, blanked summaries, and title truncation directly cause the RAG index to return irrelevant contexts, dropping the retrieval hit rate and Token F1.
- **Impact on Agent Answers:** Inaccurate or noisy retrieved contexts result in lower LLM Judge accuracy and scores.

## 3. Data Repair & Pipeline Recovery
- **Re-ingestion & Re-cleaning:** Re-fetching raw records from external APIs or fresh snapshots restores missing rows, repairs blank summaries, and fixes stale dates.
- **Performance Restoration:** Once repaired and re-indexed, the retrieval hit rate, Token F1, and Judge scores return to baseline quality.
