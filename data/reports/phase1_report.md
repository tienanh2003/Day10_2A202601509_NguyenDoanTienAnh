# Phase 1 Baseline Data Pipeline & Evaluation Report

## 1. Source Summary
- **Total Raw Records:** 24
- **Cleaned Records:** 24

## 2. Baseline Evaluation Metrics
- **Evaluation Samples:** 24
- **Retrieval Hit Rate:** 1.0000 (100.00%)
- **Mean Token F1:** 0.8190
- **LLM Judge Accuracy:** 1.0000 (100.00%)
- **Mean LLM Judge Score:** 4.96 / 5.0

## 3. Data Quality Checks
- **Quality Status:** PASSED
- **Row Count:** 24
- **paper_id Unique & Non-Null:** True
- **Duplicate paper_id Count:** 0
- **Title Non-Null:** True
- **Summary Non-Empty:** True
- **Authors Non-Empty:** True
- **Categories Non-Empty:** True
- **Average Summary Length:** 1727.4 chars
- **Latest Source Update:** 2026-08-05
- **Oldest Source Update:** 2026-02-13

## 4. Freshness Monitoring
- **Latest Publication Date:** 2026-08-01
- **Oldest Publication Date:** 2026-02-13
- **Freshness Threshold:** 180 days
- **Stale Rows Count:** 0
- **Freshness Status:** FRESH

## 5. Evaluation Samples
- **q1** Tóm tắt chính của bài báo 'SafeRAG: A Large-Language-Model-Based Multistage Retrieval-Augmented Framework for Oil and Gas Safety Report Generation' là gì? -> retrieved=['10.2118/234689-pa', '10.55041/isjem07213', '10.21203/rs.3.rs-9770645/v1', '10.1111/exsy.70341']
- **q2** Tác giả của bài báo 'SafeRAG: A Large-Language-Model-Based Multistage Retrieval-Augmented Framework for Oil and Gas Safety Report Generation' là ai? -> retrieved=['10.2118/234689-pa', '10.55041/isjem07213', '10.63646/kpqm1958', '10.20944/preprints202604.0339.v1']
- **q3** Bài báo 'SafeRAG: A Large-Language-Model-Based Multistage Retrieval-Augmented Framework for Oil and Gas Safety Report Generation' được xuất bản vào ngày nào? -> retrieved=['10.2118/234689-pa', '10.55041/isjem07213', '10.21203/rs.3.rs-9770645/v1', '10.20944/preprints202604.0339.v1']
- **q4** Bài báo 'SafeRAG: A Large-Language-Model-Based Multistage Retrieval-Augmented Framework for Oil and Gas Safety Report Generation' thuộc các chủ đề nào? -> retrieved=['10.2118/234689-pa', '10.55041/isjem07213', '10.21203/rs.3.rs-9770645/v1', '10.20944/preprints202604.0339.v1']
- **q5** Tóm tắt chính của bài báo 'Hi‐ RAG : A Hierarchical Retrieval‐Augmented Generation Framework for Scalable and Generalisable Tool Selection in Large Language Model Agents' là gì? -> retrieved=['10.1111/exsy.70341', '10.63646/kpqm1958', '10.32473/flairs.39.1.141782', '10.55041/isjem07213']
