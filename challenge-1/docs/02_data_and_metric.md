# 02. Dữ Liệu & Đánh Giá (Data & Metric)

## 1. Thông Số Tập Dữ Liệu

- **Tổng dung lượng:** ~10.82 MB
- **Định dạng:** CSV files
- **Bản quyền:** CC BY-NC-SA 4.0
- **Số lượng file:** 3 files chính

| Tên File                | Số lượng dòng | Các cột                           | Mục đích                      |
| :---------------------- | :------------ | :-------------------------------- | :---------------------------- |
| `train.csv`             | 14,000        | `id`, `text`, `language`, `label` | Tập huấn luyện có gán nhãn    |
| `test.csv`              | 6,000         | `id`, `text`, `language`          | Tập kiểm tra cần dự đoán nhãn |
| `sample_submission.csv` | 6,000         | `id`, `label`                     | Mẫu file nộp lên hệ thống     |

---

## 2. Mô Tả Chi Tiết Các Cột

- **`id`** _(string)_: Mã định danh duy nhất cho từng prompt (ví dụ: `t000006`).
- **`text`** _(string)_: Nội dung đoạn prompt cần phân loại.
  - Chiều dài: dao động từ **10 đến 18,550 ký tự**.
  - Trung vị (median length): **294 ký tự**.
  - _Lưu ý:_ Một số prompt có độ dài rất lớn (lên tới 18,550 ký tự), cần có chiến lược xử lý độ dài max sequence length (ví dụ 512, 1024 hoặc sliding window/truncation) phù hợp khi đưa vào Transformer.
- **`language`** _(string)_: Mã ngôn ngữ của prompt. Bao gồm 4 ngôn ngữ:
  - `pt`: Tiếng Bồ Đào Nha (Portuguese)
  - `fr`: Tiếng Pháp (French)
  - `it`: Tiếng Ý (Italian)
  - `en`: Tiếng Anh (English)
- **`label`** _(string - chỉ có trong `train.csv`)_: Nhãn phân loại bảo mật.

---

## 3. Ý Nghĩa & Phân Bố Nhãn (Class Distribution)

Dữ liệu có sự **mất cân bằng nghiêm trọng (severe imbalance)**:

| Nhãn (`label`)     | Ý nghĩa nghiệp vụ                                                       | Tỷ lệ trong tập Train |
| :----------------- | :---------------------------------------------------------------------- | :-------------------- |
| `BENIGN`           | Yêu cầu thông thường của người dùng, hoàn toàn an toàn và hợp lệ        | **~62%**              |
| `JAILBREAK`        | Nỗ lực trò chuyện hoặc bẫy logic nhằm ép mô hình phá bỏ rào cản an toàn | **~31%**              |
| `PROMPT_INJECTION` | Nỗ lực chèn mã/câu lệnh can thiệp vào chỉ dẫn hệ thống (System Prompt)  | **~7%** _(Rất hiếm)_  |

> ⚠️ **Cảnh báo quan trọng:**
> Nếu mô hình dự đoán toàn bộ là `BENIGN` (majority baseline), điểm F1 đạt được chỉ vào khoảng **~0.26**. Cần đặc biệt chú trọng lớp thiểu số `PROMPT_INJECTION`.

---

## 4. Thước Đo Đánh Giá: Macro-Averaged F1 Score

### Cách tính:

Điểm số đánh giá trên Leaderboard được tính bằng **Macro F1 Score** trung bình trên cả 3 lớp:

$$\text{Macro-F1} = \frac{F1_{\text{BENIGN}} + F1_{\text{JAILBREAK}} + F1_{\text{PROMPT\_INJECTION}}}{3}$$

### Ý nghĩa chiến lược:

1. **Trọng số bình đẳng:** Mỗi lớp chiếm chính xác $\frac{1}{3}$ (33.33%) tổng điểm, bất kể kích thước mẫu.
2. **Giá trị của lớp hiếm:** Lớp `PROMPT_INJECTION` chỉ chiếm 7% dữ liệu nhưng quyết định 33.33% điểm số. Nếu mô hình bỏ sót hoặc dự đoán sai nhiều ở lớp này, điểm Macro-F1 sẽ sụt giảm nghiêm trọng.
3. **Thang điểm:**
   - Dự đoán ngây thơ (toàn bộ `BENIGN`): **~0.26**
   - Điểm tối đa: **1.00**

---

## 5. Quy Chuẩn File Submission

- File xuất ra định dạng `.csv`.
- Đúng **6,000 dòng dữ liệu** kèm theo **1 dòng header**: `id,label`.
- Cột `id` phải khớp chính xác thứ tự và giá trị với `test.csv`.
- Cột `label` chỉ được nhận một trong 3 chuỗi: `BENIGN`, `JAILBREAK`, hoặc `PROMPT_INJECTION`.

**Ví dụ định dạng file nộp:**

```csv
id,label
t000006,BENIGN
t000007,PROMPT_INJECTION
t000008,JAILBREAK
t000009,BENIGN
```
