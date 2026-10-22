# RMIT Hackathon 2026 - Multilingual AI Protector

> **Security × Generative AI × Low-Resource Languages**  
> Kaggle Competition: [RMIT HACKATHON 2026](https://www.kaggle.com/competitions/rmit-hackathon-2026)  
> Website: [https://rmit-hackathon.com/](https://rmit-hackathon.com/)

---

## 📌 Tổng Quan Cuộc Thi

- **Mục tiêu:** Xây dựng mô hình phân loại đa lớp đa ngôn ngữ (**Multilingual Multi-class Prompt-Attack Classification**) đóng vai trò làm bộ lọc an toàn (**AI Protector**), phát hiện các tấn công prompt injection và jailbreak bằng các ngôn ngữ ngoài tiếng Anh (Bồ Đào Nha, Pháp, Ý) và tiếng Anh.
- **Thách thức:** Challenge 1 diễn ra trên Kaggle Leaderboard (các challenge khác trên RMIT RACE Cloud).
- **Metric Đánh giá:** **Macro-averaged F1 score** trên 3 nhãn phân loại.
- **Giới hạn nộp bài:** Tối đa **6 lần submit**.

---

## 📂 Cấu Trúc Tài Liệu Chi Tiết

Tất cả các tài liệu ghi chú chi tiết về cuộc thi được lưu trữ trong thư mục `docs/`:

| Tài liệu                                                                                                                                               | Nội dung chính                                                                                                                  |
| :----------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------ |
| 🎯 [TOP1_PLAN.md](file:///d:/CODE%20PLAYGROUND/Projects/Competitions/RMIT-Hackathon-2026/challenge-1/TOP1_PLAN.md)                                     | **Kế hoạch tác chiến Top-1:** Chiến lược North Star, phân công 4 TV, backlog thí nghiệm ROI, ngân sách 6 lượt submit & rủi ro   |
| 📄 [docs/01_overview.md](file:///d:/CODE%20PLAYGROUND/Projects/Competitions/RMIT-Hackathon-2026/challenge-1/docs/01_overview.md)                       | Thể lệ cuộc thi, quy chuẩn đặt tên notebook/kernel, nền tảng, mốc thời gian, tài nguyên hỗ trợ                                  |
| 📊 [docs/02_data_and_metric.md](file:///d:/CODE%20PLAYGROUND/Projects/Competitions/RMIT-Hackathon-2026/challenge-1/docs/02_data_and_metric.md)         | Phân tích tập dữ liệu (`train.csv`, `test.csv`), các nhãn, phân bố mất cân bằng dữ liệu, metric Macro-F1 & định dạng submission |
| 🤖 [docs/03_models_and_baseline.md](file:///d:/CODE%20PLAYGROUND/Projects/Competitions/RMIT-Hackathon-2026/challenge-1/docs/03_models_and_baseline.md) | Danh sách 10 mô hình pretrained được phép sử dụng (Encoder, Safety-tuned, LLM), lưu ý kỹ thuật & phương pháp huấn luyện         |

---

## ⚡ Tóm Tắt Nhanh (Cheat Sheet)

### 1. Phân loại 3 lớp (3 Classes)

- `BENIGN`: Yêu cầu thông thường, an toàn (~62% tập train).
- `JAILBREAK`: Cố gắng qua mặt hoặc phá vỡ hàng rào an toàn của mô hình (~31% tập train).
- `PROMPT_INJECTION`: Cố gắng chiếm quyền điều khiển chỉ dẫn hệ thống của mô hình (~7% tập train).

### 2. Dữ liệu & Ngôn ngữ

- **Kích thước:** `train.csv` (14,000 dòng), `test.csv` (6,000 dòng).
- **Ngôn ngữ:** `pt` (Portuguese), `fr` (French), `it` (Italian), `en` (English).

### 3. Quy chuẩn đặt tên Notebook

```text
<university>_<campus>_<team>_C<challenge>
```

- `<university>` & `<campus>`: Chỉ gồm chữ cái (`SGS`, `HNI`, `MEL`, `MYS`).
- `<team>`: Chữ cái, số, gạch dưới `_`, gạch ngang `-`.
- `<challenge>`: `1`
- _Ví dụ:_ `RMIT_SGS_a_C1`, `RMIT_HNI_beautiful_C1`, `Taylor_MYS_sunny_C1`.
