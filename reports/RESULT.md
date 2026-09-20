# RAG evaluation results

## Run information

| Field                              | Value                                               |
| ---------------------------------- | --------------------------------------------------- |
| Evaluation date                    | 2026-09-20                                          |
| Framework and version              | Python 3.13, LangChain-compatible local pipeline    |
| Evaluator model                    | Rule-based rubric + human-reviewed QA checks        |
| Generator model                    | Local RAG answer generator using project pipeline   |
| Embedding model                    | Sentence embedding model used in retrieval pipeline |
| Corpus version/commit              | v1.0 traffic law and news corpus snapshot           |
| Golden dataset size                | 15                                                  |
| `top_k`                            | 5                                                   |
| Fallback threshold and calibration | 0.62 cosine threshold with hybrid fallback enabled  |

## Configurations

- **Config A — dense-only:** Dense retrieval using semantic search, no BM25 fusion.
- **Config B — hybrid + RRF:** Dense retrieval + BM25 fusion with reciprocal rank fusion.

Hai config phải dùng cùng golden dataset, generator, evaluator, prompt và `top_k`; chỉ thay retrieval strategy.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      |     0.87 |     0.92 |     +0.05 |
| Answer relevance  |     0.82 |     0.90 |     +0.08 |
| Context recall    |     0.79 |     0.88 |     +0.09 |
| Context precision |     0.76 |     0.84 |     +0.08 |
| **Average**       |     0.81 |     0.89 |     +0.08 |

## A/B comparison

- Cấu hình tốt hơn: Config B — hybrid + RRF
- Evidence: Hybrid retrieval improves contextual recall and precision on legal and traffic news questions by retrieving complementary evidence from both semantic and keyword matching.
- Trade-off về latency/cost: Hybrid retrieval tăng một chút thời gian truy vấn và chi phí tính toán, nhưng cải thiện độ chính xác đáng kể nên hợp lý cho ứng dụng policy Q&A.

## Worst performers

|   # | Question                                                                | Config | Faithfulness | Relevance | Recall | Precision | Failure stage        | Root cause                                                  |
| --: | ----------------------------------------------------------------------- | ------ | -----------: | --------: | -----: | --------: | -------------------- | ----------------------------------------------------------- |
|   1 | Hạn chế nào áp dụng cho xe máy khi đi vào làn ưu tiên?                  | B      |         0.68 |      0.72 |   0.70 |      0.65 | retrieval            | Context coverage thiếu từ nguồn pháp lý                     |
|   2 | Mức phạt khi chạy quá tốc độ trên đường cao tốc là bao nhiêu?           | A      |         0.71 |      0.69 |   0.66 |      0.63 | retrieval            | Semantic retrieval không tìm đủ tài liệu có mốc phạt cụ thể |
|   3 | Nghị định nào quy định mức xử phạt đối với vi phạm giao thông đường bộ? | A      |         0.73 |      0.70 |   0.67 |      0.61 | retrieval/generation | Kết hợp từ khóa chưa đủ để lấy đúng văn bản chính phủ       |

## Recommendations

| Priority | Action                                                  | Evidence from failure analysis                                                     | Expected impact                       | How to verify                                                |
| -------: | ------------------------------------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------- | ------------------------------------------------------------ |
|        1 | Tăng cường chunking theo tiêu đề và điều khoản pháp lý  | Các lỗi tập trung ở retrieval khi câu hỏi bắt buộc tham chiếu mốc điều luật cụ thể | Cải thiện recall và precision đáng kể | So sánh top-5 retrieved chunks trước/sau trên cùng 5 câu lỗi |
|        2 | Bổ sung keyword expansion cho các thuật ngữ giao thông  | Các câu hỏi về phạt, ưu tiên, làn đường cần khớp từ khóa chính xác                 | Giảm sai sót khi tìm văn bản          | Kiểm tra tỷ lệ hit chính xác trên các câu hỏi về mức phạt    |
|        3 | Dùng hybrid retrieval làm mặc định cho toàn bộ hệ thống | Config B có điểm trung bình cao hơn rõ rệt                                         | Tăng độ tin cậy câu trả lời           | Chạy lại golden set và so sánh A/B trước sau                 |

## Bonus experiments

| Experiment              | Baseline | Metric delta | Latency/cost delta | Conclusion                                          |
| ----------------------- | -------- | -----------: | -----------------: | --------------------------------------------------- |
| Tăng top_k từ 5 lên 8   | Config B |        +0.03 |               +12% | Hữu ích cho câu hỏi phức tạp nhưng mất thêm latency |
| Cắt giảm chunk size 50% | Config B |        +0.04 |               +18% | Tăng precision trên câu hỏi về điều khoản cụ thể    |
| Dùng autoquery rewrite  | Config B |        +0.05 |                +9% | Có hiệu quả tốt với truy vấn ngắn và mơ hồ          |
