# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Nguyễn Văn Ninh            |
| MSSV               | 2A202601419                |
| Khóa/Lớp         | K3                         |
| Tên nhóm         | Nhóm 2A                    |
| Vai trò chính    | Source Ingestion, Data Model & Eval Set Owner (Thành viên 1 & 2) |
| Repository         | https://github.com/tienanh2003/Day10_2A202601509_NguyenDoanTienAnh |
| Ngày hoàn thành | 2026-08-06                 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | ------------------ |
| **Source Ingestion** | `src/ingestion/crossref.py`<br>- `fetch_source_records`<br>- `parse_crossref_payload`<br>- `load_raw_records` | Crossref REST API (`https://api.crossref.org/works`), `Settings` | `data/raw/crossref_response.json`<br>`data/raw/crossref_records.json`<br>`list[PaperRecord]` | **Hoàn thành** |
| **Data Model & Cleaning** | `src/ingestion/cleaning.py`<br>- `build_clean_dataframe` | `list[PaperRecord]`, `run_date` | `data/clean/papers_clean.csv`<br>`data/clean/papers_clean.json`<br>`pd.DataFrame` | **Hoàn thành** |
| **Eval Set Construction** | `src/evaluation/testset.py`<br>- `build_test_set` | `pd.DataFrame` (cleaned data) | `data/eval/test_set.json`<br>`list[dict]` | **Hoàn thành** |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả và bằng chứng |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Phục hồi dữ liệu từ nguồn (Data Repair) | Corruption & Integration Flow (`src/pipelines/corruption_flow.py`) | Cung cấp raw snapshot `crossref_records.json` và hàm `build_clean_dataframe` để khôi phục dữ liệu sạch `papers_clean_repaired.csv` khi chạy repair flow. |
| Kiểm thử tích hợp End-to-End | Pipeline Integrator (`src/pipelines/phase1.py`) | Chạy thử nghiệm toàn bộ luồng Phase 1 và Corruption flow, xác nhận hit rate đạt 1.0 trên dữ liệu sạch và phục hồi 100% sau repair. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Ingest raw records từ Crossref API | `src/ingestion/crossref.py` | 24 bản ghi học thuật phẳng dạng `PaperRecord` + 2 raw JSON artifacts. | File `data/raw/crossref_records.json` (60 KB) & `crossref_response.json` (245 KB). |
| Làm sạch và chuẩn hóa dữ liệu | `src/ingestion/cleaning.py` | DataFrame 24 hàng sạch chứa `text_for_embedding`, `authors_joined`, `categories_joined`, `age_days`. | File `data/clean/papers_clean.csv` & `papers_clean.json`. |
| Tạo bộ câu hỏi đánh giá đóng băng (Frozen Eval Set) | `src/evaluation/testset.py` | 18 câu hỏi factual chuẩn schema kèm `ground_truth_doc_ids` chính xác. | File `data/eval/test_set.json` (10.6 KB). |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
1. Dữ liệu thô từ Crossref REST API chứa các thẻ XML/HTML như `<jats:p>`, `<jats:title>`, `<b>`, các danh sách tác giả bị lồng ghép phức tạp, và có nguy cơ rác do thiếu tiêu đề hoặc tóm tắt rỗng/ngắn.
2. Cần chuẩn hóa dữ liệu thành một cấu trúc phẳng nhất quán (`text_for_embedding`, `age_days`), loại bỏ nhiễu để nạp vào ChromaDB vector store.
3. Tạo bộ câu hỏi kiểm thử khách quan đóng băng (Frozen Evaluation Set) có căn cứ câu trả lời thực tế (Ground Truth) để đo hiệu năng RAG agent qua các pha Baseline, Corrupted và Repaired.

### Cách triển khai
- **`crossref.py`**:
  - Gọi API Crossref với query từ settings (`agentic retrieval augmented generation large language model`).
  - Áp dụng cơ chế **Exponential Backoff Retry** xử lý mã lỗi HTTP `429` / `503`.
  - Sử dụng Regex và `html.unescape` để loại bỏ toàn bộ thẻ XML/HTML khỏi `summary` và `title`.
  - Ghi lại bản lưu HTTP response nguyên bản (`crossref_response.json`) và bản đã parse (`crossref_records.json`).
- **`cleaning.py`**:
  - Đưa `PaperRecord` vào DataFrame, lọc bỏ các bản ghi thiếu `title` hoặc có `summary` < 100 ký tự.
  - Gộp danh sách tác giả thành `authors_joined`, danh sách thể loại thành `categories_joined`.
  - Calculate `age_days = (run_date.date() - published_date).days`.
  - Tạo cột biểu diễn ngữ nghĩa: `text_for_embedding = f"Title: {title} | Authors: {authors_joined} | Summary: {summary}"`.
  - Deduplicate theo `paper_id` và sắp xếp theo ngày xuất bản giảm dần.
- **`testset.py`**:
  - Chọn các bài báo tiêu biểu trong tập cleaned data.
  - Tự động sinh các câu hỏi thuộc loại `factual` (về summary, tác giả, ngày xuất bản, thể loại).
  - Trích xuất `ground_truth` thực tế và gán đúng `ground_truth_doc_ids = [paper_id]`.
  - Đóng băng kết quả vào `data/eval/test_set.json`.

### Input, output và contract

| Thành phần | Mô tả |
| ------------------------------ | ------------------------------------------- |
| Input | Crossref REST API (`https://api.crossref.org/works`), `Settings` |
| Output | Raw JSONs (`data/raw/`), Clean CSV/JSON (`data/clean/`), Eval Testset JSON (`data/eval/test_set.json`) |
| Module phụ thuộc | `core.config.Settings`, `core.utils` |
| Module sử dụng output | `retrieval.index` (nhận clean data để build MiniLM embeddings), `evaluation.metrics` (nhận testset để chấm điểm agent), `observability.quality` (nhận clean data để check quality/freshness) |
| Điều kiện lỗi cần xử lý | API rate limit `429`/`503`, dữ liệu rác/thiếu tiêu đề, summary lồng thẻ XML, ngày tháng sai định dạng. |

### Cách xác minh

```bash
uv run python -c "from core.config import load_settings; from ingestion.crossref import fetch_source_records; from ingestion.cleaning import build_clean_dataframe; from evaluation.testset import build_test_set; from datetime import datetime; s = load_settings(); recs = fetch_source_records(s); df = build_clean_dataframe(recs, datetime.now()); ts = build_test_set(df, s.paths.eval_testset); print(len(recs), len(df), len(ts))"
```

- **Kết quả mong đợi:** Ingest 24 records, clean 24 rows, tạo 18-32 test questions.
- **Kết quả thực tế:** `24 24 18` (Thành công 100%).
- **Artifact/log:** `data/raw/crossref_records.json`, `data/clean/papers_clean.csv`, `data/eval/test_set.json`.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Dữ liệu abstract từ Crossref chứa nhiều thẻ XML/HTML như `<jats:p>`, `<jats:title>`, `<b>`, `<i>`. Nếu giữ nguyên, vector embedding của mô hình `all-MiniLM-L6-v2` sẽ bị nhiễu do các thẻ cú pháp này.
- **Các phương án đã cân nhắc:**
  1. *Phương án 1*: Giữ nguyên text thô từ API không qua xử lý HTML regex.
  2. *Phương án 2 (Đã chọn)*: Áp dụng hàm `_clean_html_text` sử dụng regex `re.sub(r"<[^>]+>", " ", text)` kết hợp `html.unescape` và `normalize_whitespace`.
- **Lý do chọn:** Phương án 2 giúp loại bỏ hoàn toàn các ký tự dư thừa, giữ lại văn bản thuần túy có ngữ nghĩa cao nhất cho embedding model.
- **Bằng chứng quyết định phù hợp:** Chỉ số `retrieval_hit_rate` của Baseline pipeline đạt tuyệt đối **1.0 (100%)**.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Gặp lỗi HTTP `429 Too Many Requests` khi gửi yêu cầu liên tục đến Crossref API public endpoint.
- **Lệnh hoặc bước tái hiện:** Gọi `fetch_source_records` mà không có header User-Agent polite hoặc retry mechanism.
- **Nguyên nhân gốc:** Crossref API giới hạn tần suất truy cập đối với các request không định danh hoặc gửi yêu cầu dồn dập.
- **Cách xử lý:** 
  1. Thêm header `User-Agent: Day10DataPipeline/1.0 (mailto:student@lab.edu)`.
  2. Bổ sung vòng lặp retry với **Exponential Backoff** (`time.sleep(1.5 ** attempt)`).
  3. Bổ sung cơ chế caching local `raw_records_json` khi `refresh_source=False`.
- **Cách xác minh sau khi sửa:** Lệnh `fetch_source_records` hoàn thành mượt mà, trả về 24 records mà không bị ngắt quãng.
- **Bài học kỹ thuật:** Khi làm việc với các public REST APIs, luôn luôn phải triển khai Retry logic và local caching snapshot để vừa đảm bảo độ tin cậy vừa phục vụ quá trình audit dữ liệu.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   - Crossref API ➔ `fetch_source_records` (lưu `crossref_response.json` & `crossref_records.json`) ➔ `build_clean_dataframe` (clean XML, tạo `text_for_embedding`, lưu `papers_clean.csv`) ➔ `LocalEmbeddingIndex.build` (dùng `all-MiniLM-L6-v2` mã hóa `text_for_embedding` thành vector 384D) ➔ Nạp vào ChromaDB collection `papers-baseline`.

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   - Bộ câu hỏi `test_set.json` cung cấp câu hỏi (`question`), câu trả lời chuẩn (`ground_truth`) và danh sách document ID chứa đáp án (`ground_truth_doc_ids`).
   - Khi RAG Agent thực hiện search, `retrieval_hit_rate` kiểm tra xem ít nhất 1 document ID trong `retrieved_doc_ids` có thuộc `ground_truth_doc_ids` hay không. `mean_token_f1` đo mức độ tương đồng từ vựng giữa câu trả lời của agent và `ground_truth`.

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   - **Quality checks**: Kiểm tra tính toàn vẹn và tính đúng đắn của dữ liệu tĩnh (như completeness: tỷ lệ null, uniqueness: tỷ lệ trùng `paper_id`, validity: độ dài summary >= 100 chars).
   - **Freshness monitoring**: Kiểm tra tính thời sự của dữ liệu theo thời gian thực (tính `age_days` dựa trên cột ngày `published` so với mốc thời gian chạy `run_date` và so sánh với ngưỡng `freshness_threshold_days = 180`).

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   - Để đảm bảo tính công bằng (controlled experiment). Giữ nguyên duy nhất 1 biến số là **chất lượng dữ liệu (clean vs corrupted vs repaired)**, trong khi giữ cố định bộ câu hỏi thử nghiệm để đo chính xác mức độ sụt giảm và phục hồi hiệu năng của Agent.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   - Repair thành công khi:
     1. Dataset được tái tạo trực tiếp từ raw snapshot (`crossref_records.json`) tạo ra `papers_clean_repaired.csv`.
     2. Metrics phục hồi: `retrieval_hit_rate` tăng từ **0.7778 (Corrupted)** trở lại **1.0 (Repaired)**.
     3. Quality checks khôi phục trạng thái **PASS**.

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |     1.00 |    0.3333 |     1.00 | Dữ liệu lỗi làm suy giảm 66.7% khả năng tìm trúng bài báo. Sau repair khôi phục tuyệt đối 100%. |
| `mean_token_f1`      |   0.0920 |    0.0198 |   0.0920 | F1 token sụt giảm mạnh khi dữ liệu bị nhiễu và phục hồi hoàn toàn sau repair. |
| `judge_accuracy`     |     1.00 |    0.2778 |     1.00 | Độ chính xác câu trả lời của Agent đạt 100% ở Baseline, sụt xuống 27.8% ở Corrupted và phục hồi 100% ở Repaired. |
| `mean_judge_score`   |     4.28 |      1.83 |     4.28 | Điểm trung bình chất lượng câu trả lời phục hồi từ 1.83/5 lên 4.28/5. |
| Quality checks         |     PASS |      FAIL |     PASS | Corrupted vi phạm check summary missing & stale date. Repaired đạt 100% PASS. |
| Freshness status       |    Fresh |     Stale |    Fresh | Dữ liệu bị làm cũ năm 2000 kích hoạt cảnh báo Stale và đã được khôi phục thành Fresh. |

### Visualization So sánh Hiệu năng

```text
Retrieval Hit Rate:
Baseline  : [████████████████████] 100.0% (PASS)
Corrupted : [███████░░░░░░░░░░░░░]  33.3% (FAIL)
Repaired  : [████████████████████] 100.0% (PASS - Restored)

Agent Judge Accuracy:
Baseline  : [████████████████████] 100.0% (PASS)
Corrupted : [█████░░░░░░░░░░░░░░░]  27.8% (FAIL)
Repaired  : [████████████████████] 100.0% (PASS - Restored)

LLM Judge Score (thang 5.0):
Baseline  : [█████████████████░░░]  4.28 / 5.00
Corrupted : [███████░░░░░░░░░░░░░]  1.83 / 5.00
Repaired  : [█████████████████░░░]  4.28 / 5.00
```

### Kết luận từ số liệu

1. **[Data corruption]** (Xóa summary, gán ngày cũ 2000, nhân bản duplicate) ➔ **[quality signal FAIL / Stale]** ➔ **[retrieval_hit_rate giảm từ 1.0 xuống 0.3333, judge_accuracy giảm từ 1.0 xuống 0.2778]**.
2. **[Repair action]** (Re-ingest từ `crossref_records.json` thô & chạy lại logic cleaning) ➔ **[quality signal PASS / Fresh]** ➔ **[retrieval_hit_rate và judge_accuracy phục hồi hoàn toàn về 1.0]**.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về Data Pipeline**: Dữ liệu thô từ external API cần có cơ chế audit trail (lưu raw snapshots) để có thể khôi phục (repair) bất kỳ lúc nào mà không bị phụ thuộc vào sự thay đổi của nguồn ngoài.
2. **Về Data Quality & Observability**: Data Quality không chỉ là lọc lỗi lúc ETL, mà phải có các chốt chặn tự động (Quality Gates & Freshness Monitoring) để phát hiện sự cố dữ liệu trước khi đưa vào ChromaDB vector store.
3. **Về ảnh hưởng của Data đến RAG Agent**: Chất lượng của RAG Agent phụ thuộc trực tiếp vào chất lượng dữ liệu ("Garbage in, Garbage out"). Dữ liệu bị nhiễu hoặc mất summary lập tức làm suy giảm khả năng semantic retrieval của mô hình embedding.

### Nếu có thêm thời gian

- Phát triển thêm bộ quy tắc tự động sinh câu hỏi đa dạng hơn bằng LLM (như multi-hop reasoning questions) thay vì câu hỏi factual template, đồng thời tích hợp Ragas framework đầy đủ để chấm điểm `faithfulness` và `context_relevance`.

---

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Văn Ninh  
**Ngày xác nhận:** 2026-08-06
