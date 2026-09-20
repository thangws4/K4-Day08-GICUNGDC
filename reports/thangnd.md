# Individual contribution report

## Thông tin

- Họ và tên: _(điền)_
- Mã học viên: _(điền)_
- Nhóm: _(điền)_
- Repository/branch: https://github.com/thangws4/K4-L3A-RAG-Pipeline — branch `thangnd`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 1 — thu thập văn bản pháp luật | Khai `SOURCES` 6 văn bản, viết resolver bóc link PDF từ trang Công báo, kiểm text layer và dấu "Xem tiếp Công báo", ghi manifest nguồn | `src/task1_collect_legal_docs.py`, `data/landing/legal/sources.json`, commit `14319eb`, `6aa4710`, `5b89001` | Done |
| Task 2 — crawl tin bài | 5 URL baochinhphu.vn, giới hạn crawl vào selector thân bài, chặn bài < 500 ký tự | `src/task2_crawl_news.py`, `data/landing/news/article_01..05.json` | Done |
| Task 3 — chuẩn hóa Markdown | MarkItDown + bỏ header Công báo lặp mỗi trang + nối dòng bị PDF ngắt giữa câu; header metadata để truy ngược về file landing và URL gốc | `src/task3_convert_markdown.py`, `data/standardized/**` | Done |
| Task 4 — chunk, embed, index | `load_documents` parse header thay vì suy từ tên file; cắt theo ranh giới `Điều` và gắn lại tiêu đề điều cha; bge-m3 + ChromaDB cosine; dọn chunk mồ côi khi corpus đổi | `src/task4_chunking_indexing.py` | Done |
| Chatbot UI | `app.py` hoàn chỉnh (answer, nguồn, điểm, retrieval method, safe refusal, không sập khi provider lỗi) + design system | `app.py`, `assets/design-system.css`, `assets/citation.js`, `.streamlit/config.toml` | Done |
| Sửa lỗi Task 10 | Giữ reference `genai.Client()` để client không bị GC trước khi request gửi đi | `src/task10_generation.py` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Thay toàn bộ PDF "signed" trên datafiles.chinhphu.vn bằng bản đăng Công báo, và tải đủ mọi phần của mỗi văn bản.
   **Lý do/evidence:** pdfplumber trích được **0 ký tự** từ 4/5 file ban đầu (bản scan ảnh) — convert nguyên trạng sẽ ra Markdown rỗng, RAG không có gì để retrieve. Sau khi đổi nguồn lại phát hiện văn bản bị cắt: Luật 36/2024/QH15 có 89 điều nhưng file phần 1 chỉ tới **Điều 23**, kết thúc bằng dòng "(Xem tiếp Công báo số 979 + 980)".
   **Trade-off:** Mất bản có chữ ký số; phải scrape HTML trang Công báo nên sẽ hỏng nếu trang đổi layout; một văn bản bị chia thành nhiều file (NĐ 158 thành 3 phần), citation phải ghi kèm "phần k/n".

2. **Quyết định:** Chunk theo ranh giới `Điều` và gắn lại tiêu đề điều cha vào đầu mỗi chunk.
   **Lý do/evidence:** Câu hỏi "mức phạt nồng độ cồn với ô tô", chunk retrieve được chứa đúng khoản phạt nhưng bắt đầu giữa câu, mất mệnh đề "đối với người điều khiển **xe ô tô**" nằm ở chunk trước — LLM từ chối trả lời. Nguy hiểm hơn: chunk cũ đưa ra mức **6–8 triệu** (của xe mô tô) trong khi mức đúng cho ô tô là **18–20 triệu** (Điều 6 khoản 9 NĐ 168/2024).
   **Trade-off:** Số chunk tăng 4.245 → 4.937 (+16%), thời gian embed và dung lượng index tăng tương ứng; tiêu đề lặp lại ở 89% chunk làm loãng một phần tín hiệu embedding của thân chunk; mỗi lần đổi chiến lược chunk phải re-index lại ~30–45 phút trên CPU.

## Kiểm thử và kết quả

- **Test tôi đã dùng:** `pytest tests/test_contracts.py -q` → 15 passed. `pytest tests/test_acceptance.py -q` → 3 passed (dữ liệu), 2 failed (`golden_dataset.json` và `RESULT.md` thuộc phase evaluation, chưa làm). Smoke test pipeline thật: `semantic_search` / `lexical_search` / `retrieve` / `generate_with_citation` qua Gemini. `AppTest` headless cho `app.py`. Test escaping với payload `<img src=x onerror=alert(1)>` và URL `javascript:` cho thẻ nguồn.
- **Kết quả trước/sau:** corpus legal 4/5 file 0 ký tự → 6 văn bản đều có text (175 MB scan → 20 MB); Luật 36 phủ tới Điều 23 → Điều 89; tin bài 10.471 → 3.016 ký tự/bài sau khi bỏ menu và footer; chunk mang tiêu đề điều luật 0% → 89%.
- **Lỗi đã phát hiện và cách xử lý:** (1) PDF scan không text layer → đổi nguồn, thêm cảnh báo tự động khi tải. (2) Văn bản bị cắt theo số Công báo → tải đủ phần, guard phát hiện dòng "Xem tiếp". (3) `genai.Client()` làm biến tạm bị garbage collect trước khi request gửi → `RuntimeError: client has been closed`, sửa bằng giữ reference. (4) `print` tiếng Việt crash trên console cp1252 → reconfigure stdout UTF-8. (5) Threshold fallback 0.3 không tách được out-of-domain (query "học phí đại học" vẫn đạt dense 0.434 trong khi in-domain 0.745) — đã báo nhóm, thuộc Task 9.

## Điều còn hạn chế

- **Hạn chế cụ thể:** Corpus thiếu Nghị định 238/2026/NĐ-CP và 236/2026/NĐ-CP, là hai văn bản mà tin bài trong chính corpus dẫn chiếu 7 lượt. Câu hỏi về quy định có hiệu lực từ 2026 sẽ được trả lời dựa trên bản chưa sửa đổi, hoặc sinh mâu thuẫn giữa nhánh tin bài và nhánh văn bản luật.
- **Nếu có thêm thời gian:** bổ sung hai nghị định đó rồi đo lại context recall. Sau đó thay cách gắn tiêu đề điều luật — hiện đang lặp text vào thân chunk, nên chuyển sang lưu số điều trong metadata và chỉ ghép lại lúc format context, để không làm loãng embedding.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: _(điền)_
