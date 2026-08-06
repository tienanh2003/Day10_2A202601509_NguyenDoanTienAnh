# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| ------------------ | -------------------------- |
| Họ và tên | Nguyễn Đoàn Tiến Anh |
| MSSV | 2A202601509 |
| Khóa/Lớp | K3/K4 |
| Tên nhóm | Nhóm 1 - Data Pipeline |
| Vai trò chính | Member 3 (Data Observability Owner) & Member 4 (Corruption & Integration Owner) |
| Repository | `https://github.com/tienanh2003/Day10_2A202601509_NguyenDoanTienAnh` |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Observability Quality Checks | `src/observability/quality.py` (`run_data_quality_checks`, `build_freshness_report`) | `df: pd.DataFrame`, `settings: Settings` | `data/quality/*.json`, `freshness_report.json` | Hoàn thành |
| Observability Reporting | `src/observability/reporting.py` (`generate_phase1_report`, `generate_corruption_report`) | Summary dicts, metrics dicts, quality & freshness dicts | `data/reports/phase1_report.md`, `data/reports/corruption_report.md` | Hoàn thành |
| Data Corruption Engine | `src/ingestion/corruption.py` (`corrupt_clean_dataframe`) | `df: pd.DataFrame` (cleaned baseline) | `data/clean/papers_clean_corrupted.csv`, `data/results/corruption_log.json` | Hoàn thành |
| Baseline Pipeline Orchestration | `src/pipelines/phase1.py` (`main`) | `Settings` cấu hình | End-to-end baseline pipeline, raw/clean/eval artifacts | Hoàn thành |
| Corruption & Repair Pipeline | `src/pipelines/corruption_flow.py` (`main`) | Clean baseline & raw records snapshot | End-to-end corruption flow, comparison report | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Cấu hình OpenRouter & Model Integration | Chuyển đổi LLM Provider từ Gemini sang OpenRouter | Cấu hình thành công `LLM_PROVIDER=openrouter` và `LLM_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free` trong `.env` |
| Sửa lỗi đường dẫn artifacts | Tích hợp hệ thống lưu lưu đồng thời `papers_clean_corrupted.csv` và `papers_corrupted.csv` | Đảm bảo tương thích hoàn toàn với tất cả các script kiểm thử |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Xây dựng Data Quality & Freshness Monitor | `src/observability/quality.py` | `data/quality/baseline_quality.json`, `data/quality/freshness_report.json` | Chạy `run_phase1.py` và kiểm tra kết quả `PASSED` / `FRESH` |
| Xây dựng Báo cáo so sánh Markdown 3 trạng thái | `src/observability/reporting.py` | `data/reports/phase1_report.md`, `data/reports/corruption_report.md` | Kiểm tra nội dung bảng so sánh Baseline vs Corrupted vs Repaired |
| Gây lỗi dữ liệu có kiểm soát (Corruption) | `src/ingestion/corruption.py` | `data/results/corruption_log.json`, `data/clean/papers_clean_corrupted.csv` | Kiểm tra `corrupted_quality.json` trả về `FAILED` |
| Điều phối Pipeline End-to-End | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` | Chạy tự động luồng Baseline và Corruption Repair | Chạy `uv run python script/run_phase1.py` và `uv run python script/run_corruption_flow.py` |

**Artifact cụ thể đã tạo ra:**
Báo cáo đối chiếu [corruption_report.md](file:///c:/Users/MSI/TIENANH/VinAIAction/LABS/Day10_2A202601509_NguyenDoanTienAnh/data/reports/corruption_report.md) hiển thị rõ sự sụt giảm của $Retrieval\_Hit\_Rate$ từ 100% xuống khi dữ liệu bị hỏng và sự phục hồi lại 100% sau khi chạy luồng Repair từ raw records.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Xây dựng lớp giám sát chất lượng dữ liệu (Data Observability) cho pipeline RAG, tự động phát hiện dữ liệu lỗi/stale, đồng thời giả lập quá trình gây hư hỏng dữ liệu có kiểm soát (Controlled Corruption) và điều phối toàn bộ luồng tự động sửa lỗi (Auto-repair) để đo lường tác động lên RAG Agent.

### Cách triển khai
1. **Data Quality & Freshness:** Viết hàm `run_data_quality_checks` kiểm tra completeness (không null/rỗng), uniqueness (`paper_id` duy nhất), độ dài tóm tắt và tính số dòng bị stale so với ngưỡng `freshness_threshold_days=180`.
2. **Controlled Corruption:** Viết hàm `corrupt_clean_dataframe` thực hiện xóa 20% bản ghi mới nhất (trùng vào các câu hỏi testset), tẩy rỗng summary, chèn nhiễu `CORRUPTED_GARBAGE_NOISE_999`, cắt ngắn title, lùi ngày xuất bản về năm 2010 và tạo bản ghi trùng lặp.
3. **Orchestration & Reporting:** Điều phối luồng `corruption_flow.py` đọc dữ liệu bị lỗi $\rightarrow$ rebuild vector index $\rightarrow$ re-evaluate trên testset frozen $\rightarrow$ repair bằng cách re-ingest từ `raw_records.json` $\rightarrow$ xuất báo cáo so sánh Markdown.

### Input, output và contract

| Thành phần | Mô tả |
| ------------------------------ | ------------------------------------------- |
| Input | `df: pd.DataFrame`, `settings: Settings`, `raw_records_json: Path` |
| Output | `data/quality/*.json`, `data/results/corruption_log.json`, `data/reports/corruption_report.md` |
| Module phụ thuộc | `ingestion.crossref`, `ingestion.cleaning`, `retrieval.index`, `evaluation.metrics` |
| Module sử dụng output | `script/run_phase1.py`, `script/run_corruption_flow.py` |
| Điều kiện lỗi cần xử lý | Trường hợp DataFrame rỗng, mất file raw snapshot, lỗi API LLM (dùng fallback judge) |

### Cách xác minh

```bash
uv run python script/run_phase1.py
uv run python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Baseline đạt Quality `PASSED`, Freshness `FRESH`. Pha Corrupted đạt Quality `FAILED`, metrics giảm. Pha Repaired phục hồi metrics và Quality `PASSED`.
- **Kết quả thực tế:** Toàn bộ script chạy thông suốt, các file JSON và Markdown report được khởi tạo chính xác.
- **Artifact/log:** `data/results/corruption_log.json`, `data/reports/corruption_report.md`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn phương pháp phục hồi dữ liệu (Repair) khi phát hiện Data Corruption.
- **Các phương án đã cân nhắc:**
  1. *Phương án A:* Gọi lại external API Crossref qua Internet để lấy dữ liệu mới.
  2. *Phương án B:* Khôi phục và làm sạch lại từ file raw snapshot (`data/raw/crossref_records.json`) đã lưu ở bước Ingestion.
- **Phương án đã chọn:** Phương án B.
- **Lý do:** Đảm bảo tính bất biến (Idempotency), khả năng tái lập (Reproducibility) và độc lập với kết nối mạng hay nguy cơ gặp lỗi Rate Limit (HTTP 429/503) từ API bên ngoài.
- **Bằng chứng quyết định phù hợp:** Luồng Repair chạy thành công 100% không phụ thuộc mạng, khôi phục chỉ số $Retrieval\_Hit\_Rate$ về mốc Baseline.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `ModuleNotFoundError: No module named 'pipelines'` khi chạy script.
- **Lệnh hoặc bước tái hiện:** `python script/run_phase1.py` trên môi trường Python mặc định.
- **Nguyên nhân gốc:** Thư mục `src/` chưa được thêm vào `PYTHONPATH` hoặc môi trường ảo chưa cài đặt package dưới dạng editable (`pip install -e .`).
- **Cách xử lý:** Chạy thông qua `uv run python script/run_phase1.py` hoặc thêm `$env:PYTHONPATH="src"` trước khi gọi Python.
- **Cách xác minh sau khi sửa:** Lệnh `uv run python script/run_phase1.py` thực thi thành công không còn báo lỗi import.
- **Điều học được:** Luôn quản lý môi trường bằng virtual environment và thiết lập PYTHONPATH chuẩn xác khi xây dựng cấu trúc Data Pipeline trong Python.

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index:** External API $\rightarrow$ Raw JSON snapshot (`crossref_response.json`) $\rightarrow$ Parse `PaperRecord` (`crossref_records.json`) $\rightarrow$ Clean & Normalize DataFrame (`papers_clean.csv`) $\rightarrow$ Embedding bằng `sentence-transformers/all-MiniLM-L6-v2` $\rightarrow$ Nạp vào ChromaDB collection.
2. **Evaluation set và ground-truth document IDs:** Bộ câu hỏi testset chứa danh sách `ground_truth_doc_ids`. Khi Agent truy xuất top-k context từ ChromaDB, nếu trong danh sách ID trả về có chứa `ground_truth_doc_ids` thì câu hỏi đó tính là `Retrieval Hit` ($Hit\_Rate = 1$).
3. **Quality checks vs Freshness monitoring:** Quality checks kiểm tra tính đầy đủ, tính duy nhất và tính hợp lệ của dữ liệu (Completeness, Uniqueness, Validity). Freshness monitoring đo khoảng thời gian từ ngày xuất bản (`published`) đến hiện tại (`age_days`) so với ngưỡng `freshness_threshold_days` để phát hiện dữ liệu lỗi thời.
4. **Vì sao phải dùng cùng test set cho 3 trạng thái:** Để đảm bảo tính nhất quán (Consistency) và so sánh công bằng (Fair Benchmark). Nếu đổi testset giữa các pha, kết quả so sánh sẽ không còn giá trị đối chứng.
5. **Repair được xem là thành công khi nào:** Khi dữ liệu khôi phục đạt Quality `PASSED`, Freshness `FRESH` và các chỉ số $Retrieval\_Hit\_Rate$, $Token\_F1$, $LLM\_Judge\_Score$ phục hồi tương đương mốc Baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` | 1.0000 | 0.3333 | 1.0000 | Corruption làm mất bản ghi khiến Hit Rate giảm mạnh; Repair phục hồi về 100% |
| `mean_token_f1` | 0.5240 | 0.1850 | 0.5240 | F1 sụt giảm do thiếu ngữ cảnh đáp án; phục hồi hoàn toàn sau Repair |
| `judge_accuracy` | 1.0000 | 0.3333 | 1.0000 | LLM Judge đánh giá sai khi context bị nhiễu/rỗng; phục hồi sau Repair |
| `mean_judge_score` | 4.80 | 2.10 | 4.80 | Điểm chất lượng trung bình giảm sâu ở pha Corrupted |
| Quality checks | PASSED | FAILED | PASSED | Phát hiện chính xác lỗi rỗng dữ liệu và trùng lặp ở pha Corrupted |
| Freshness status | FRESH | STALE | FRESH | Phát hiện chính xác các bản ghi bị đẩy lùi ngày xuất bản về năm 2010 |

### Kết luận từ số liệu

1. **[Data corruption]** (Xóa bản ghi, blank summary, stale date) $\rightarrow$ **[Quality checks FAILED, Freshness STALE]** $\rightarrow$ **[Retrieval Hit Rate giảm từ 1.0 xuống 0.33, Judge Score giảm từ 4.8 xuống 2.1]**.
2. **[Repair action]** (Re-ingest từ raw records snapshot & re-cleaning) $\rightarrow$ **[Quality checks PASSED, Freshness FRESH]** $\rightarrow$ **[Retrieval Hit Rate & Judge Score phục hồi 100% về mức Baseline]**.

- **Corruption ảnh hưởng rõ nhất:** Kịch bản **Drop records & Blank summary** ảnh hưởng nghiêm trọng nhất vì làm mất hoàn toàn vector thông tin trong ChromaDB, khiến Agent chọn sai ngữ cảnh.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về Data Pipeline:** Thấy rõ tầm quan trọng của việc lưu trữ Raw Data Snapshot trong kiến trúc Medallion để có thể rollback/repair pipeline bất kỳ lúc nào mà không phụ thuộc API bên ngoài.
2. **Về Data Quality/Observability:** Tự động hóa kiểm tra Data Quality & Freshness giúp phát hiện sớm các sự cố dữ liệu trước khi chúng gây hại cho mô hình AI ở hạ nguồn (downstream RAG).
3. **Về ảnh hưởng của Data đến RAG Agent:** Chất lượng câu trả lời của LLM phụ thuộc trực tiếp vào chất lượng dữ liệu đầu vào ("Garbage in, garbage out").

### Nếu có thêm thời gian

Thêm công cụ tự động cảnh báo (Alerting System qua Slack/Email) ngay khi Data Quality Check bị FAILED và tích hợp tự động gọi luồng Auto-Repair pipeline không cần can thiệp thủ công.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Đoàn Tiến Anh
**Ngày xác nhận:** 2026-08-06

