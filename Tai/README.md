# 🛡️ Multilingual Prompt-Attack Classification — RMIT Hackathon 2026

Thư mục này chứa toàn bộ tài nguyên huấn luyện và nộp bài cho cuộc thi **Multilingual Prompt-Attack Classification** (RMIT Hackathon 2026).

---

## 📂 Danh mục File

| File | Mô tả |
| :--- | :--- |
| [`multilingual_prompt_attack_classification.ipynb`](file:///d:/PARA%20Method/Project/RMIT-Hackathon-2026/Tai/multilingual_prompt_attack_classification.ipynb) | Kaggle Notebook hoàn chỉnh (26 cells): EDA, XLM-RoBERTa fine-tuning, Weighted Cross-Entropy Loss, Threshold Bias Tuning, tạo `submission.csv`. |
| [`create_notebook.py`](file:///d:/PARA%20Method/Project/RMIT-Hackathon-2026/Tai/create_notebook.py) | Python generator script dùng để biên soạn và cập nhật tự động file notebook. |

---

## 🚀 Hướng dẫn chạy trên Kaggle

1. **Tạo Notebook mới trên Kaggle:**
   - Vào [Kaggle Code](https://www.kaggle.com/code) -> Click **New Notebook**.
   - Chọn File -> **Upload Notebook** -> Chọn file [`multilingual_prompt_attack_classification.ipynb`](file:///d:/PARA%20Method/Project/RMIT-Hackathon-2026/Tai/multilingual_prompt_attack_classification.ipynb).

2. **Thêm Dataset:**
   - Ở thanh công cụ bên phải, click **Add Input** -> Search: `dangthtai/rmit-hackathon-2026-dataset`.
   - Notebook được viết kèm hàm tìm kiếm đường dẫn thông minh (`locate_dataset_files`), tự động nhận diện dữ liệu trong `/kaggle/input/rmit-hackathon-2026-dataset`.

3. **Cấu hình phần cứng (Notebook Settings):**
   - **Accelerator:** GPU P100 hoặc GPU T4 x2.
   - **Internet:** On (để tự động tải backbone `FacebookAI/xlm-roberta-base`). Nếu chạy Offline, notebook hỗ trợ nhận diện model nếu bạn add model weights vào Kaggle Input.
   - **Persistence:** No persistence hoặc Variables only.

4. **Chạy toàn bộ (Run All):**
   - Sau khi huấn luyện xong, file kết quả sẽ được lưu tại `/kaggle/working/submission.csv` và tự động pass qua 5 bước kiểm tra toàn vẹn dữ liệu (assertion tests).

---

## 🧠 Tóm tắt Kiến trúc & Kỹ thuật cốt lõi

1. **Backbone:** `FacebookAI/xlm-roberta-base` — Khả năng biểu diễn mạnh mẽ trên các ngôn ngữ Latin (English, French, Portuguese, Italian), không cần bước dịch trung gian (tránh phá hỏng cấu trúc prompt injection/jailbreak).
2. **Xử lý mất cân bằng (Imbalance):**
   - Tỷ lệ: `BENIGN` ~62%, `JAILBREAK` ~31%, `PROMPT_INJECTION` ~7%.
   - Trọng số căn bậc hai nghịch đảo (Inverse Sqrt Frequency):
     $$w_c \propto \frac{1}{\sqrt{n_c}}$$
     Giúp mô hình phạt nặng hơn khi bỏ sót `PROMPT_INJECTION` mà không gây ra false positive tràn lan cho `BENIGN`.
3. **Phân chia dữ liệu:** Stratified Split 80/20 bảo toàn tỷ lệ nhãn và ngôn ngữ.
4. **Early Stopping:** Dừng theo dõi dựa trên metric **Macro-F1** (patience = 2).
5. **Post-Processing (Logit Bias Tuning):**
   - Tối ưu vector bias $\mathbf{b} = [b_0, b_1, b_2]$ trên logits tập Validation:
     $$\hat{y} = \arg\max_c (z_c + b_c)$$
   - Tối đa hóa trực tiếp điểm Macro-F1 trước khi áp dụng lên tập Test.
6. **Kiểm tra Submission:** 
   - Đủ 6.000 dòng.
   - Trùng khớp 100% ID và thứ tự với `test.csv`.
   - Không chứa bất kỳ giá trị NaN/Null.
