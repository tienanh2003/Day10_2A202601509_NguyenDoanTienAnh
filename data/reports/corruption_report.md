# Data Corruption & Repair Impact Analysis Report

## 1. Comprehensive Pipeline Performance Comparison

| Metric | Baseline (Clean) | Corrupted (Degraded) | Repaired (Restored) |
| :--- | :---: | :---: | :---: |
| **Retrieval Hit Rate** | 1.0000 (100.0%) | 0.3333 (33.3%) | 1.0000 (100.0%) |
| **Mean Token F1** | 0.8190 | 0.4315 | 0.8190 |
| **LLM Judge Accuracy** | 1.0000 (100.0%) | 0.5417 (54.2%) | 1.0000 (100.0%) |
| **Mean LLM Judge Score** | 4.96 / 5.0 | 3.04 / 5.0 | 4.96 / 5.0 |
| **Data Quality Check** | PASSED | FAILED | PASSED |
| **Freshness Status** | FRESH | STALE | FRESH |
| **Stale Rows** | 0 | 4 | 0 |

## 2. Data Corruption Analysis
- **Retrieval Hit Rate delta vs baseline:** -0.6667
- **Mean Token F1 delta vs baseline:** -0.3875
- **Judge Accuracy delta vs baseline:** -0.4583
- **Duplicate paper_id Count:** 2
- **Stale Rows Count:** 4

## 3. Data Repair & Pipeline Recovery
- **Retrieval Hit Rate recovery vs corrupted:** 0.6667
- **Mean Token F1 recovery vs corrupted:** 0.3875
- **Judge Accuracy recovery vs corrupted:** 0.4583
- **Re-ingestion & Re-cleaning:** Re-fetching raw records from external APIs or fresh snapshots restores missing rows, repairs blank summaries, and fixes stale dates.

## 4. Example Regressions
- **q1** Tóm tắt chính của bài báo 'SafeRAG: A Large-Language-Model-Based Multistage Retrieval-Augmented Framework for Oil and Gas Safety Report Generation' là gì? | retrieved_hit=False | answer=Abstract - This work focuses on the two crucial bottlenecks in Retrieval-Augmented Generation (RAG): high inference latency and expensive computation cost.
- **q2** Tác giả của bài báo 'SafeRAG: A Large-Language-Model-Based Multistage Retrieval-Augmented Framework for Oil and Gas Safety Report Generation' là ai? | retrieved_hit=False | answer=Ruotong Wang, Nyutian Long, Shunqi Liu, Yuxi Wang, Zhen Qi, Huajun Zhang
- **q3** Bài báo 'SafeRAG: A Large-Language-Model-Based Multistage Retrieval-Augmented Framework for Oil and Gas Safety Report Generation' được xuất bản vào ngày nào? | retrieved_hit=False | answer=2026-05-06

## 5. Example Recoveries
- **q1** Tóm tắt chính của bài báo 'SafeRAG: A Large-Language-Model-Based Multistage Retrieval-Augmented Framework for Oil and Gas Safety Report Generation' là gì? | retrieved_hit=True | answer=Summary In high-risk industrial settings, leveraging large language models (LLMs) for automated accident analysis and generating safety reports has emerged as a
- **q2** Tác giả của bài báo 'SafeRAG: A Large-Language-Model-Based Multistage Retrieval-Augmented Framework for Oil and Gas Safety Report Generation' là ai? | retrieved_hit=True | answer=Qianwen Cao, Chiyu Zhang, Junxiong Ning, Gongru Li
- **q3** Bài báo 'SafeRAG: A Large-Language-Model-Based Multistage Retrieval-Augmented Framework for Oil and Gas Safety Report Generation' được xuất bản vào ngày nào? | retrieved_hit=True | answer=2026-08-01
