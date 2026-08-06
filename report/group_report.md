# Group Report — Day 10: Data Pipeline & Data Observability

> Dùng mẫu này cho báo cáo chung của nhóm 3–5 thành viên. Thay toàn bộ nội dung trong dấu `[ ]` bằng thông tin và kết quả thực tế. Xóa các dòng hướng dẫn không còn cần thiết trước khi nộp.

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | [K3 hoặc K4]              |
| Tên nhóm         | [Tên hoặc mã nhóm]     |
| Repository         | [Đường dẫn repository] |
| Ngày hoàn thành | [YYYY-MM-DD]               |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Nguyễn Văn Ninh | 2A202601509 | Source Ingestion, Data Model & Eval Set Owner | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py`, `src/evaluation/testset.py` |
| 2 | [Họ tên] | [MSSV] | [Vai trò] | [File, hàm hoặc artifact] |
| 3 | [Họ tên] | [MSSV] | [Vai trò] | [File, hàm hoặc artifact] |
| 4 | [Nếu có] | [MSSV] | [Vai trò] | [File, hàm hoặc artifact] |
| 5 | [Nếu có] | [MSSV] | [Vai trò] | [File, hàm hoặc artifact] |

## 2. Tóm tắt kết quả

Viết từ 150–250 từ, trả lời ngắn gọn:

- Nhóm đã hoàn thành những phần nào?
- Baseline pipeline đã tạo ra các artifact nào?
- Corruption nào ảnh hưởng rõ nhất đến data quality hoặc agent?
- Repair đã phục hồi được chỉ số nào?
- Blocker hoặc giới hạn quan trọng nhất còn lại là gì?

**Tóm tắt của nhóm:**

[Viết phần tóm tắt tại đây.]

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

Điều chỉnh sơ đồ dưới đây nếu cách triển khai thực tế của nhóm khác starter:

```text
Crossref API
    -> raw response/raw records
    -> cleaning và data modeling
    -> embedding + ChromaDB index
    -> evaluation baseline
    -> quality/freshness reports
    -> corruption
    -> re-index và re-evaluate
    -> repair từ dữ liệu nguồn
    -> comparison report
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Crossref REST API | Fetch API (Retry 429/503), parse payload, clean XML | `data/raw/crossref_response.json`<br>`data/raw/crossref_records.json` | Nguyễn Văn Ninh |
| Cleaning          | `crossref_records.json` | Normalize text, filter summary < 100, authors_joined, age_days, text_for_embedding | `data/clean/papers_clean.csv`<br>`data/clean/papers_clean.json` | Nguyễn Văn Ninh |
| Embedding/index   | Clean data | MiniLM embedding, ChromaDB vector store | `data/embeddings/`, `chroma/` | [Thành viên] |
| Evaluation        | Clean data | Generate frozen testset, evaluate hit_rate & token_f1 | `data/eval/test_set.json`<br>`data/results/` | Nguyễn Văn Ninh |
| Observability     | Clean/corrupted data | Completeness, uniqueness & freshness checks | `data/quality/` | [Thành viên] |
| Corruption/repair | Clean/raw data | Simulate corruption, re-ingest raw records for repair | `data/results/corruption_log.json` | [Thành viên] |
| Orchestration     | All modules | Orchestrate Phase 1 & Corruption Flow | `data/reports/` | [Thành viên] |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | [Giá trị]         |
| `LLM_MODEL`                | [Giá trị]         |
| Embedding model              | sentence-transformers/all-MiniLM-L6-v2 |
| Số lượng Crossref records | 24 records |
| Retrieval`top_k`           | 4 |
| Freshness threshold          | 180 days |
| Random seed, nếu có        | N/A |

Không dán nội dung API key hoặc file `.env` vào báo cáo.

### Lệnh cài đặt

Chỉ giữ lại cách nhóm đã dùng.

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

Hoặc với môi trường `pip` đã kích hoạt:

```bash
python script/run_phase1.py
```

Corruption flow:

```bash
uv run python script/run_corruption_flow.py
```

Hoặc với môi trường `pip` đã kích hoạt:

```bash
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công | 2026-08-06 | `data/reports/phase1_report.md` |
| Corruption flow   | Thành công | 2026-08-06 | `data/reports/corruption_report.md` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | Crossref REST API (`https://api.crossref.org/works`) |
| Query/filter                | `query=agentic retrieval augmented generation...`, `filter=from-pub-date:...,has-abstract:true` |
| Thời điểm lấy dữ liệu | 2026-08-06 |
| Số record nhận được    | 24 records |
| Cơ chế retry/backoff      | Exponential Backoff Retry (max 4 attempts, backoff factor 1.5) xử lý lỗi HTTP `429`/`503` |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id` | String | Có | Stable Unique Identifier (DOI hoặc slug) | Tự động sinh `safe_slug` nếu thiếu DOI |
| `title` | String | Có | Tiêu đề bài báo học thuật | Strip HTML/XML, bỏ record nếu rỗng |
| `summary` | String | Có | Tóm tắt bài báo (abstract) | Strip HTML/XML `<jats:p>`, bỏ record nếu < 100 chars |
| `authors` | List[String] | Có | Danh sách tên tác giả | Gộp thành `authors_joined = ", ".join(authors)` |
| `categories` | List[String] | Có | Danh sách thể loại/chủ đề | Gộp thành `categories_joined = ", ".join(categories)` |
| `published` | String (YYYY-MM-DD) | Có | Ngày xuất bản chính thức | Format YYYY-MM-DD, dùng để tính `age_days` |
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

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | 18 câu hỏi |
| Các `question_type`                    | `factual` (vấn đáp về summary, authors, date, categories) |
| Ground-truth document ID                 | Lấy trực tiếp từ `paper_id` của clean paper chứa đáp án chuẩn |
| Embedding model                          | sentence-transformers/all-MiniLM-L6-v2 |
| Vector store/collection                  | ChromaDB (`papers-baseline`, `papers-corrupted`, `papers-repaired`) |
| Retrieval `top_k`                       | 4 |
| LLM provider/model                       | gemini (gemini-2.5-flash) |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:

Giữ nguyên duy nhất một bộ câu hỏi đánh giá (Frozen Eval Set) đóng vai trò là hằng số kiểm thử. Việc này đảm bảo tính công bằng của thí nghiệm (controlled experiment), giúp đo lường chính xác tác động của sự thay đổi chất lượng dữ liệu lên hiệu năng tìm kiếm và trả lời của RAG Agent.

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | Có | `crossref_response.json` (245 KB), `crossref_records.json` (60 KB) |
| Cleaned dataset          | `data/clean/`                        | Có | `papers_clean.csv` (100 KB), `papers_clean.json` (115 KB) |
| Embedding manifest/index | `data/embeddings/`                   | Có | `papers_embeddings.json` |
| Evaluation set           | `data/eval/`                         | Có | `test_set.json` (10.6 KB) |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có | Baseline retrieval_hit_rate = 1.0 |
| Quality/freshness        | `data/quality/`                      | Có | `freshness_report.json` |
| Baseline report          | `data/reports/phase1_report.md`      | Có | Báo cáo baseline hoàn chỉnh |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` |     1.0 | Đạt 100% khả năng tìm trúng văn bản chứa đáp án |
| `mean_token_f1`      |     0.0920 | Mức tương đồng từ vựng với Ground Truth |
| `judge_accuracy`     |     0.0 | Đánh giá heuristic fallback |
| `mean_judge_score`   |     1.0 | Điểm judge heuristic |
| Ragas, nếu me          | N/A | Bỏ qua pass Ragas chậm (cần `RUN_RAGAS=1`) |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| `completeness_check` | Completeness | Null rate < 5% | PASS (0% null) | `data/quality/` |
| `uniqueness_check` | Uniqueness | Paper ID duplicates = 0 | PASS (Unique = 100%) | `data/quality/` |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | Cleaned dataset (`published` date) |
| Timestamp mới nhất       | 2026-08-06 |
| Ngưỡng freshness         | 180 days |
| Trạng thái baseline      | Fresh |
| Lý do                     | Ngày xuất bản gần nhất nằm trong khoảng 180 ngày so với thời điểm chạy |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| Blank Summary      | Gán summary thành rỗng | 4 records | Completeness FAIL | Hit rate giảm | Re-ingest từ raw records snapshot |
| Stale Date         | Đổi ngày `published` về năm 2000 | 4 records | Freshness STALE | Freshness chuyển sang STALE | Re-clean ngày từ raw snapshot |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Ghi chép chi tiết danh sách ID bản ghi bị tác động và loại corruption.

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:

Repair không sửa tay trên dữ liệu corrupted mà luôn nạp lại từ snapshot nguồn đáng tin cậy (`data/raw/crossref_records.json`) và thực thi lại toàn bộ quy tắc cleaning chuẩn.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   |     1.00 |    0.7778 |     1.00 |                  -0.2222 | +0.2222 (100%) | Hit rate giảm 22.2% khi data bị hỏng, phục hồi hoàn toàn sau repair |
| `mean_token_f1`        |   0.0920 |    0.0827 |   0.0920 |                  -0.0093 | +0.0093 (100%) | F1 token giảm khi summary rỗng/noise và phục hồi lại mốc baseline |
| `judge_accuracy`       |     0.00 |      0.00 |     0.00 |                     0.00 |           0.00 | Heuristic fallback |
| `mean_judge_score`     |     1.00 |      1.00 |     1.00 |                     0.00 |           0.00 | Heuristic score |
| Quality checks pass/fail |     PASS |      FAIL |     PASS |                     FAIL |           PASS | Corrupted làm trượt Quality gate, Repaired đạt PASS |
| Freshness status         |    Fresh |     Stale |    Fresh |                    Stale |          Fresh | Phục hồi trạng thái tươi mới về Fresh |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:

1. [Corruption/data change] → [quality/freshness signal] → [retrieval/answer metric].
2. [Repair action] → [quality/freshness recovery] → [agent metric recovery hoặc lý do chưa recovery].

Không kết luận corruption “có tác động” nếu số liệu không cho thấy thay đổi. Nếu kết quả khác kỳ vọng, mô tả giả thuyết và cách nhóm đã kiểm tra.

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:

- **Triệu chứng:** [Lỗi hoặc kết quả sai.]
- **Nguyên nhân:** [Root cause.]
- **Cách xử lý:** [Thay đổi đã thực hiện.]
- **Cách xác minh:** [Lệnh và artifact.]

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| [Giới hạn]          | [Ảnh hưởng] | [Đề xuất]                              |
| [Giới hạn]          | [Ảnh hưởng] | [Đề xuất]                              |

## 13. Checklist trước khi nộp

- [ ] Thông tin nhóm và repository chính xác.
- [ ] Phân công khớp với module, artifact và kết quả thực tế.
- [ ] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [ ] Baseline, corrupted và repaired dùng cùng evaluation set.
- [ ] Bảng metrics khớp với các file trong `data/results/`.
- [ ] Quality/freshness conclusions khớp với `data/quality/`.
- [ ] Các đường dẫn báo cáo và artifact truy cập được.
- [ ] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [ ] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
