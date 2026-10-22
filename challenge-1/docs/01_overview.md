# 01. Tổng Quan Cuộc Thi - RMIT Hackathon 2026

## 1. Thông Tin Cơ Bản

- **Tên cuộc thi:** RMIT HACKATHON 2026
- **Chủ đề:** Security × Generative AI × Low-Resource Languages
- **Thời gian diễn ra:** 22 – 23 Tháng 10, 2026
- **Phạm vi khu vực:** Australia – Vietnam – Malaysia
- **Host:** Bowen (Kaggle Community Prediction Competition)
- **Đơn vị phối hợp & Tài trợ:**
  - RMIT School of Computing Technologies
  - Taylor's University
  - Tide
  - DesignLive
  - Katalon
- **Kênh thông tin chính thức:**
  - Kaggle: [https://www.kaggle.com/competitions/rmit-hackathon-2026](https://www.kaggle.com/competitions/rmit-hackathon-2026)
  - Trang web chính thức: [https://rmit-hackathon.com/](https://rmit-hackathon.com/)

---

## 2. Bối Cảnh & Thách Thức (Challenge 1)

### Bối cảnh bài toán:

Các bộ lọc an toàn (Safety filters / Guardrails) hiện nay hầu hết được huấn luyện trên dữ liệu tiếng Anh (`en`). Khi đối mặt với các ngôn ngữ khác như tiếng Bồ Đào Nha (`pt`), tiếng Pháp (`fr`), và tiếng Ý (`it`), các mô hình phòng thủ thường suy giảm hiệu năng nghiêm trọng. Mặc dù các ngôn ngữ này là tài nguyên cao (high-resource) trong các bài toán NLP thông thường, nhưng chúng lại là **nguồn tài nguyên thấp (low-resource) trong lĩnh vực AI Safety**.

### Nhiệm vụ:

Đóng vai trò là một **AI Protector** (Bộ phòng thủ AI): Phân loại từng văn bản prompt đầu vào thành 1 trong 3 nhóm bảo mật:

1. `BENIGN`: Prompt an toàn, hợp lệ.
2. `JAILBREAK`: Prompt tìm cách bẻ khóa, ép mô hình vi phạm nguyên tắc an toàn.
3. `PROMPT_INJECTION`: Prompt cố tình chèn chỉ dẫn để chiếm quyền điều khiển LLM.

---

## 3. Hệ Thống Nền Tảng & Quy Tắc Nộp Bài

### Nền tảng dự thi:

- **Challenge 1:** Triển khai và chấm điểm thông qua hệ thống Leaderboard của Kaggle.
- **Các Challenge khác:** Được xử lý trên hệ thống RMIT RACE Cloud.

### Quy định đặt tên Notebook / Kernel:

Quy chuẩn bắt buộc:

```text
<university>_<campus>_<team>_C<challenge>
```

Trong đó:

- `<university>`: Tên trường đại học (chỉ dùng ký tự chữ cái).
- `<campus>`: Thuộc tập hợp `{SGS, HNI, MEL, MYS}` (chỉ dùng ký tự chữ cái).
  - `SGS`: Saigon South campus
  - `HNI`: Hanoi campus
  - `MEL`: Melbourne campus
  - `MYS`: Malaysia campus
- `<team>`: Tên nhóm (chỉ gồm ký tự chữ cái, số, dấu gạch dưới `_`, hoặc dấu gạch ngang `-`).
- `<challenge>`: Giá trị thuộc `{1}` cho bài thi này.

**Ví dụ hợp lệ:**

- `RMIT_SGS_a_C1`
- `RMIT_HNI_beautiful_C1`
- `Taylor_MYS_sunny_C1`
- `RMIT_MEL_beautiful_C1`

### Giới hạn số lần nộp (Submission Limits):

- **Tối đa 6 lần nộp bài** (6 submission attempts). Cần tính toán kỹ lưỡng chiến lược validation và testing trước khi nộp.
- **Tiêu chí điểm Challenge 1:** Đạt điểm trọn vẹn phần Challenge 1 ngay khi nộp thành công kết quả hợp lệ đầu tiên (valid result), sau đó tiếp tục cải thiện thứ hạng trên leaderboard.

---

## 4. Trích Dẫn Cuộc Thi (Citation)

```text
Aikris, Bao Thien, Bowen, gg_, HundredPlus, Nguyen Hieu Thao, Nhat-Quang Tran, Patrick Taylor, and Vinh.
RMIT HACKATHON 2026. https://www.kaggle.com/competitions/rmit-hackathon-2026, 2026. Kaggle.
```
