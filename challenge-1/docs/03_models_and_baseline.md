# 03. Mô Hình Được Phép & Định Hướng Kỹ Thuật (Models & Guidelines)

## 1. Quy Định Bắt Buộc Về Mô Hình

> ⚠️ **Quy tắc bắt buộc:**
>
> - Thí sinh **bắt buộc** phải xây dựng giải pháp dựa trên **MỘT trong các mô hình được phê duyệt** dưới đây.
> - Các mô hình này đều có giấy phép mã nguồn mở an toàn và được ban tổ chức cung cấp sẵn dưới dạng Kaggle Dataset / Model.
> - **KHÔNG ĐƯỢC PHÉP SỬ DỤNG BẤT KỲ PRETRAINED BACKBONE NÀO KHÁC NGOÀI DANH SÁCH.**
> - **Bắt buộc khai báo tên mô hình đã chọn ở ngay đầu Notebook.**

---

## 2. Danh Sách 10 Mô Hình Được Cấp Phép (Approved Models)

Các mô hình có sẵn trong tab **Models** trên Kaggle (do tác giả `aisuko` đăng tải):

|  STT   | Tên Mô Hình                                      |         Thể Loại         | Đặc Điểm & Địa Chỉ Kaggle Model                                                                                                                            |
| :----: | :----------------------------------------------- | :----------------------: | :--------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1**  | `distilbert/distilbert-base-multilingual-cased`  |         Encoder          | Mô hình nhỏ gọn, tốc độ suy luận cực nhanh, hỗ trợ đa ngôn ngữ.<br>🔗 `aisuko/distilbert-base-multilingual-cased/Transformers/default`                     |
| **2**  | `jhu-clp/mmbert-small`                           |         Encoder          | Biến thể mBERT kích thước nhỏ, tối ưu tài nguyên.<br>🔗 `aisuko/mmbert-small/Transformers/default`                                                         |
| **3**  | `jhu-clp/mmbert-base`                            |         Encoder          | mBERT chuẩn từ JHU-CLP.<br>🔗 `aisuko/mmbert-base/Transformers/default`                                                                                    |
| **4**  | `FacebookAI/xlm-roberta-base`                    |         Encoder          | Mô hình đa ngôn ngữ rất mạnh mẽ và ổn định cho các tác vụ phân loại.<br>🔗 `aisuko/xlm-roberta-base/Transformers/default`                                  |
| **5**  | `FacebookAI/xlm-roberta-large`                   |         Encoder          | Bản Large của XLM-RoBERTa, khả năng biểu diễn ngữ nghĩa vượt trội.<br>🔗 `aisuko/xlm-roberta-large/Transformers/default`                                   |
| **6**  | `google/rembert`                                 |         Encoder          | Replaced Embedding mBERT từ Google, mở rộng vốn từ vựng đa ngôn ngữ.<br>🔗 `aisuko/rembert/Transformers/default`                                           |
| **7**  | `protectai/deberta-v3-base-prompt-injection-v2`  | Encoder _(Safety-tuned)_ | **Đã được huấn luyện chuyên sâu cho bài toán Prompt Injection.** Cực kỳ tiềm năng.<br>🔗 `aisuko/deberta-v3-base-prompt-injection-v2/Transformers/default` |
| **8**  | `patronus-studio/wolf-defender-prompt-injection` | Encoder _(Safety-tuned)_ | **Đã được tinh chỉnh chuyên môn để bảo vệ và phòng thủ LLM.**<br>🔗 `aisuko/wolf-defender-prompt-injection/Transformers/default`                           |
| **9**  | `ibm-granite/granite-3.3-2b-instruct`            |           LLM            | LLM kích thước nhỏ 2B parameters, có thể fine-tune hiệu quả với LoRA.<br>🔗 `aisuko/granite-3.3-2b-instruct/Transformers/default`                          |
| **10** | `mistralai/Mistral-7B-Instruct-v0.3`             |           LLM            | LLM 7B mạnh mẽ, cần QLoRA / 4-bit quantization để fine-tune trên Kaggle GPU.<br>🔗 `aisuko/mistral-7b-instruct-v0.3/Transformers/default`                  |

---

## 3. Các Hướng Tiếp Cận & Khuyến Nghị Kỹ Thuật

Ban tổ chức đã đưa ra các gợi ý kỹ thuật cốt lõi cần lưu ý:

### 3.1. Nhánh Kiến Trúc (Architecture Routes)

1. **Hướng tiếp cận Encoder (Encoder Route):**
   - Sử dụng Hugging Face `AutoModelForSequenceClassification` với `num_labels=3`.
   - Các mô hình như `xlm-roberta-base/large` hoặc 2 mô hình đã safety-tuned (`protectai/deberta-v3...` và `patronus-studio/wolf...`) là ứng cử viên sáng giá hàng đầu.
2. **Hướng tiếp cận LLM (LLM Route):**
   - Sử dụng LoRA / QLoRA fine-tuning trên `granite-3.3-2b-instruct` hoặc `Mistral-7B-Instruct-v0.3`.
   - Có thể xây dựng một constrained classification head hoặc trích xuất log-probabilities của 3 token nhãn tương ứng.

### 3.2. Chiến Lược Xử Lý Mất Cân Bằng Dữ Liệu (Class Imbalance)

- Vì nhãn `PROMPT_INJECTION` chỉ chiếm ~7% nhưng đóng góp 33.3% điểm Macro-F1:
  - **Class Weights:** Truyền `class_weights` vào `nn.CrossEntropyLoss` (tỷ lệ nghịch với tần suất xuất hiện).
  - **Loss Functions nâng cao:** Sử dụng **Focal Loss** để tập trung vào các mẫu khó phân loại.
  - **Resampling / Oversampling:** Tăng cường lấy mẫu cho lớp thiểu số hoặc kỹ thuật dữ liệu.

### 3.3. Tận Dụng Cột Ngôn Ngữ (`language`)

- Hiệu năng phân loại giữa các ngôn ngữ (`pt`, `fr`, `it`, `en`) không đồng đều.
- Có thể đưa token tiền tố ngôn ngữ vào prompt (ví dụ: `[LANG: fr] <text>`) hoặc thiết kế nhánh phân loại phụ theo ngôn ngữ.

### 3.4. Tránh Overfitting & Tối Ưu Validation

- **Số lần submit rất hạn chế (chỉ 6 lần):** Không thể thử nghiệm trực tiếp trên Public Leaderboard.
- Cần xây dựng chiến lược **Stratified K-Fold Cross-Validation** (chia fold đảm bảo đồng đều cả phân bố nhãn `label` và ngôn ngữ `language`).
- Tập trung vào tính tổng quát hóa (robust generalisation) thay vì cố overfit theo một vài mẫu cụ thể.
