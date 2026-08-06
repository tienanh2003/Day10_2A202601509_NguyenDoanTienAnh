# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
| ------------------ | -------------------------- |
| Khóa/Lớp | K3/K4 |
| Tên nhóm | Nhóm 1 - Data Pipeline |
| Repository | `https://github.com/tienanh2003/Day10_2A202601509_NguyenDoanTienAnh` |
| Ngày hoàn thành | 2026-08-06 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Nguyễn Đoàn Tiến Anh | 2A202601509 | Member 3 & 4 (Data Observability, Corruption & Integration Owner) | `quality.py`, `reporting.py`, `corruption.py`, `phase1.py`, `corruption_flow.py` |
| 2 | Nguyễn Văn Ninh | 2A202601419 | Member 1 & 2 (Source Ingestion, Data Model & Eval Set Owner) | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py`, `src/evaluation/testset.py` |

## 2. Tóm tắt kết quả

Nhóm đã hoàn thành 100% yêu cầu bài lab xây dựng Data Pipeline và Data Observability cho RAG Agent. 

- **Baseline Pipeline:** Đã thu thập dữ liệu thô từ Crossref API (`crossref_response.json`, `crossref_records.json`), làm sạch và chuẩn hóa dữ liệu (`papers_clean.csv`), khởi tạo cơ sở dữ liệu vector ChromaDB, đóng băng bộ câu hỏi đánh giá `test_set.json` và tạo báo cáo `phase1_report.md`. Kết quả baseline đạt $Retrieval\_Hit\_Rate = 1.0$, Quality checks `PASSED` và Freshness status `FRESH`.
- **Corruption & Repair Flow:** Thực hiện giả lập lỗi dữ liệu có kiểm soát (xóa bản ghi, tẩy rỗng summary, chèn nhiễu, lùi ngày xuất bản, nhân bản dữ liệu). Ở pha Corrupted, chỉ số $Retrieval\_Hit\_Rate$ sụt giảm xuống `0.33` và Quality check bị `FAILED`. Sau khi chạy luồng Repair tự động khôi phục dữ liệu từ Raw Records Snapshot, hệ thống đã khôi phục lại 100% chỉ số $Retrieval\_Hit\_Rate$, khôi phục Quality về `PASSED` và Freshness về `FRESH`.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API (https://api.crossref.org/works)
    -> raw response (crossref_response.json) / raw records (crossref_records.json)
    -> cleaning & data modeling (papers_clean.csv, papers_clean.json)
    -> embedding (sentence-transformers/all-MiniLM-L6-v2) + ChromaDB index
    -> evaluation baseline (test_set.json frozen)
    -> quality/freshness reports (baseline_quality.json, freshness_report.json)
    -> corruption (papers_clean_corrupted.csv, corruption_log.json)
    -> re-index & re-evaluate corrupted pipeline
    -> repair từ raw records snapshot (crossref_records.json)
    -> comparison report (corruption_report.md)
```

### Trách nhiệm của từng khối

| Khối | Input | Xử lý chính | Output/artifact | Owner |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion | Crossref REST API | Fetch API (Retry 429/503), parse payload, clean XML | `data/raw/crossref_response.json`<br>`data/raw/crossref_records.json` | Nguyễn Văn Ninh |
| Cleaning | `crossref_records.json` | Normalize text, filter summary < 100, authors_joined, age_days, text_for_embedding | `data/clean/papers_clean.csv`<br>`data/clean/papers_clean.json` | Nguyễn Văn Ninh |
| Embedding/index | `papers_clean.csv` | MiniLM 384d embedding, ChromaDB PersistentClient | `data/chroma/`, `data/embeddings/` | Nguyễn Văn Ninh |
| Evaluation | Clean DF & Chroma index | Frozen testset generator, LLM Judge (OpenRouter) | `data/eval/test_set.json`, `data/results/` | Nguyễn Văn Ninh |
| Observability | Clean DF, Settings | Completeness, uniqueness, freshness checks & markdown report | `data/quality/`, `data/reports/` | Nguyễn Đoàn Tiến Anh |
| Corruption/repair | Clean DF & Raw Snapshot | Corrupt DF (drop, blank, noise) & Repair from raw snapshot | `data/clean/papers_clean_corrupted.csv`, `data/results/corruption_log.json` | Nguyễn Đoàn Tiến Anh |
| Orchestration | Settings & Pipelines | Run Phase 1 baseline & Corruption Repair flow end-to-end | `script/run_phase1.py`, `script/run_corruption_flow.py` | Nguyễn Đoàn Tiến Anh |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER` | `openrouter` |
| `LLM_MODEL` | `nvidia/nemotron-3-ultra-550b-a55b:free` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24 records |
| Retrieval `top_k` | 4 |
| Freshness threshold | 180 days |

### Lệnh cài đặt

```bash
uv sync
```

Hoặc:

```bash
python -m pip install -e .
```

### Lệnh chạy

Baseline:

```bash
uv run python script/run_phase1.py
```

Corruption flow:

```bash
uv run python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh | Trạng thái | Thời điểm chạy gần nhất | Bằng chứng |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công | 2026-08-06 | `data/reports/phase1_report.md` |
| Corruption flow | Thành công | 2026-08-06 | `data/reports/corruption_report.md` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính | Giá trị |
| --------------------------- | ------------------------------------- |
| Source | Crossref REST API (`https://api.crossref.org/works`) |
| Query/filter | `query="agentic retrieval augmented generation"`, `filter="from-pub-date:...,has-abstract:true"` |
| Thời điểm lấy dữ liệu | 2026-08-06 |
| Số record nhận được | 24 records |
| Cơ chế retry/backoff | Retry 3-4 lần với timeout 15s, sleep backoff, fallback đọc snapshot local |

### Raw và clean schema

| Trường | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id` | String | Có | Mã DOI hoặc ID duy nhất của bài báo | Fallback sinh ID theo định dạng `crossref_xxxx` / safe_slug |
| `title` | String | Có | Tiêu đề bài báo khoa học | Strip HTML/XML tags, drop hàng nếu thiếu |
| `summary` | String | Có | Tóm tắt bài báo (Abstract) | Strip `<jats:p>` XML tags, drop hàng nếu < 100 chars |
| `authors` | List[String] | Không | Danh sách tác giả | Gộp thành `authors_joined`, gán `"Unknown Author"` nếu thiếu |
| `published` | String | Có | Ngày xuất bản YYYY-MM-DD | Parse date-parts, mặc định `"2025-01-01"` |
| `age_days` | Integer | Có | Số ngày từ lúc xuất bản đến hiện tại | Tính `max(0, (run_date - published_date).days)` |
| `text_for_embedding` | String | Có | Chuỗi ngữ nghĩa dán nhãn cho ChromaDB | Combine: `Title: ... \| Authors: ... \| Summary: ...` |

### Quy tắc cleaning

| Quy tắc | Quality dimension liên quan | Số record bị tác động | Cách xác minh |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Loại bỏ record có summary < 100 ký tự | Completeness / Validity | 0 (API filter `has-abstract:true`) | Kiểm tra `summary_chars` trong `papers_clean.csv` |
| Làm sạch các thẻ XML/HTML (`<jats:p>`, `<b>`, v.v.) | Validity / Uniqueness | 24 records | Kiểm tra chuỗi text không chứa ký tự `<...>` |
| Deduplicate theo `paper_id` | Uniqueness | 0 (các DOI đều unique) | Check `df.duplicated(subset=['paper_id'])` = 0 |

Giải thích cách tạo `text_for_embedding`, document ID và `age_days`:

- `paper_id`: Sử dụng mã DOI trực tiếp từ Crossref (hoặc slug hóa title nếu thiếu DOI) để làm ID định danh duy nhất không đổi.
- `text_for_embedding`: Kết hợp thông tin dạng `Title: {title} | Authors: {authors_joined} | Summary: {summary}` để tạo ngữ nghĩa đầy đủ nhất cho mô hình vector MiniLM.
- `age_days`: Tính bằng `(run_date.date() - published_date).days` để đo số ngày tính từ khi bài báo được xuất bản.

## 6. Evaluation setup

| Thành phần | Cấu hình thực tế |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi | 18 câu hỏi |
| Các `question_type` | `factual` (vấn đáp về summary, authors, date, categories) |
| Ground-truth document ID | List `[paper_id]` chứa thông tin đáp án |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store/collection | ChromaDB PersistentClient (`papers-baseline`, `papers-corrupted`, `papers-repaired`) |
| Retrieval `top_k` | 4 |
| LLM provider/model | OpenRouter / `nvidia/nemotron-3-ultra-550b-a55b:free` |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:

Giữ nguyên duy nhất một bộ câu hỏi đánh giá (Frozen Eval Set) đóng vai trò là hằng số kiểm thử. Việc này đảm bảo tính công bằng của thí nghiệm (controlled experiment), giúp đo lường chính xác tác động của sự thay đổi chất lượng dữ liệu lên hiệu năng tìm kiếm và trả lời của RAG Agent.

## 7. Kết quả baseline

### Artifact checklist

| Artifact | Đường dẫn thực tế | Trạng thái | Ghi chú |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records | `data/raw/` | Có | `crossref_response.json`, `crossref_records.json` |
| Cleaned dataset | `data/clean/` | Có | `papers_clean.csv`, `papers_clean.json` |
| Embedding manifest/index | `data/embeddings/` | Có | `papers_embeddings.json` |
| Evaluation set | `data/eval/` | Có | `test_set.json` |
| Baseline metrics | `data/results/baseline_metrics.json` | Có | Baseline retrieval_hit_rate = 1.0 |
| Quality/freshness | `data/quality/` | Có | `freshness_report.json` |
| Baseline report | `data/reports/phase1_report.md` | Có | Báo cáo baseline hoàn chỉnh |

### Baseline metrics

| Metric | Giá trị | Diễn giải |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` | 1.0000 | Retriever tìm đúng 100% ngữ cảnh đáp án từ ChromaDB |
| `mean_token_f1` | 0.5240 | Mức độ khớp từ vựng chính xác giữa đáp án sinh ra và Ground Truth |
| `judge_accuracy` | 1.0000 | 100% câu trả lời được LLM Judge đánh giá đạt yêu cầu ngữ nghĩa |
| `mean_judge_score` | 4.80 / 5.0 | Điểm đánh giá trung bình của LLM Judge |

## 8. Data quality và freshness

### Quality checks

| Check | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| `row_count` | Completeness | > 0 rows | PASSED (24 rows) | `baseline_quality.json` |
| `paper_id_unique` | Uniqueness | True | PASSED (100% Unique) | `baseline_quality.json` |
| `title_not_null` | Completeness | True | PASSED (Non-null) | `baseline_quality.json` |
| `summary_not_empty` | Completeness | True | PASSED (>= 100 chars) | `baseline_quality.json` |

### Freshness

| Thuộc tính | Giá trị |
| -------------------------- | ----------------------------------- |
| Ngưỡng freshness | 180 ngày |
| Trạng thái baseline | FRESH |
| Lý do | 100% số bản ghi có ngày xuất bản trong vòng 180 ngày |

## 9. Corruption scenarios và repair

| Corruption | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| Drop records | Xóa 20% bài báo mới nhất | 5 rows | Hit Rate sụt giảm | Hit Rate giảm từ 1.0 về 0.33 | Re-ingest từ raw snapshot |
| Blank summary | Tẩy rỗng nội dung summary | 4 rows | Summary non-empty FAIL | ChromaDB vector bị lệch | Re-cleaning từ raw snapshot |
| Stale date | Lùi ngày xuất bản về năm 2010 | 4 rows | Freshness STALE | Freshness chuyển sang STALE | Reset published date tu snapshot |

Corruption log:
- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Ghi chép chi tiết danh sách ID bản ghi bị tác động và loại corruption.

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:
Repair không sửa tay trên dữ liệu corrupted mà luôn nạp lại từ snapshot nguồn đáng tin cậy (`data/raw/crossref_records.json`) và thực thi lại toàn bộ quy tắc cleaning chuẩn.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   |     1.00 |    0.3333 |     1.00 |                  -0.6667 | +0.6667 (100%) | Hit rate giảm 66.7% khi data bị hỏng, phục hồi hoàn toàn 100% sau repair |
| `mean_token_f1`        |   0.0920 |    0.0198 |   0.0920 |                  -0.0722 | +0.0722 (100%) | F1 token giảm mạnh khi summary rỗng/noise và phục hồi lại mốc baseline |
| `judge_accuracy`       |     1.00 |    0.2778 |     1.00 |                  -0.7222 | +0.7222 (100%) | Độ chính xác trả lời sụt từ 100% xuống 27.8% và phục hồi 100% sau repair |
| `mean_judge_score`     |     4.28 |      1.83 |     4.28 |                  -2.4500 | +2.4500 (100%) | Điểm đánh giá chất lượng trung bình khôi phục từ 1.83/5 lên 4.28/5 |
| Quality checks pass/fail |     PASS |      FAIL |     PASS |                     FAIL |           PASS | Corrupted làm trượt Quality gate, Repaired đạt PASS |
| Freshness status         |    Fresh |     Stale |    Fresh |                    Stale |          Fresh | Phục hồi trạng thái tươi mới về Fresh |

```text
Visualization So sánh Metrics giữa 3 Trạng thái Pipeline:

Retrieval Hit Rate:
  Baseline  : [████████████████████] 100.0%
  Corrupted : [███████░░░░░░░░░░░░░]  33.3%
  Repaired  : [████████████████████] 100.0%

Agent Judge Accuracy:
  Baseline  : [████████████████████] 100.0%
  Corrupted : [█████░░░░░░░░░░░░░░░]  27.8%
  Repaired  : [████████████████████] 100.0%
```

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:

1. **[Data corruption]** (Blank summary, Stale publication date, Duplicate records) ➔ **[Quality Gate FAIL & Freshness STALE]** ➔ **[Retrieval Hit Rate giảm từ 1.00 xuống 0.3333, LLM Judge Accuracy sụt từ 1.00 xuống 0.2778]**.
2. **[Repair action]** (Re-ingest từ `crossref_records.json` thô & Re-clean) ➔ **[Quality Gate PASS & Freshness FRESH]** ➔ **[Retrieval Hit Rate và LLM Judge Accuracy phục hồi hoàn toàn về 1.00]**.

Không kết luận corruption “có tác động” nếu số liệu không cho thấy thay đổi. Nếu kết quả khác kỳ vọng, mô tả giả thuyết và cách nhóm đã kiểm tra.

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:

- **Triệu chứng:** Kết nối Crossref API bị rate limit HTTP 429 khi gửi request dồn dập.
- **Nguyên nhân:** Public API của Crossref hạn chế tần suất request không có header định danh.
- **Cách xử lý:** Thêm User-Agent header, triển khai Retry Exponential Backoff và cơ chế cache local raw snapshot.
- **Cách xác minh:** Ingest 24 bản ghi mượt mà, lưu `data/raw/crossref_response.json`.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Phụ thuộc mạng khi fetch Crossref | Có thể timeout | Luôn ưu tiên dùng cached raw snapshot local |
| Token F1 thấp do cách diễn đạt | Đánh giá chưa phản ánh đúng ngữ nghĩa | Sử dụng LLM Judge hoặc Ragas làm thước đo chính |

## 12. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
