# RMIT Hackathon 2026 · Challenge 1: Top-1 Execution Plan

## Multilingual Prompt-Attack Classification

> **Khung thời gian:** Từ 10:30 ngày 22/10 đến trước 12:00 ngày 23/10  
> **Trọng tâm:** Macro-F1, lớp `PROMPT_INJECTION` (PI) hiếm, long prompts và tối ưu ngân sách 6 lượt submit.

---

### 📊 Chỉ Số Cốt Lõi (Key Metrics)

|     👥 Thành Viên     |   🎯 Lượt Submit Tối Đa   |  ⚠️ Tỷ Lệ `PROMPT_INJECTION`  |     ⚖️ Trọng Số Mỗi Lớp      |
| :-------------------: | :-----------------------: | :---------------------------: | :--------------------------: |
| **4** (Owner rõ ràng) | **6** (Ngân sách cố định) | **7%** (Cực hiếm trong train) | **1/3** (Macro-F1 bình đẳng) |

---

## 1. Chiến Lược (Strategy)

> 💡 **Luận điểm thắng cuộc:**  
> Không cố thắng bằng một backbone đơn lẻ. Hãy thắng bằng **validation chống leakage**, **xử lý long-context đúng cách**, và **fusion phân cấp** tận dụng safety prior để tách `BENIGN` khỏi `ATTACK`, sau đó mới tách `JAILBREAK` khỏi `PROMPT_INJECTION`.

### 1.1. North Star: Tối đa Macro-F1 thật, không tối đa “OOF đẹp”

Chọn mô hình theo 4 tiêu chí cốt lõi:

1. **Group-OOF Macro-F1**
2. **F1 riêng của `PROMPT_INJECTION`**
3. **Worst-language F1** (hiệu năng ngôn ngữ thấp nhất)
4. **Độ lệch (variance) giữa các fold**

_(Lưu ý: Public Leaderboard chỉ là tín hiệu phụ vì toàn đội có đúng 6 lượt submit)._

### 1.2. Kiến Trúc Khuyến Nghị (Architecture Recommendation)

- **Nhánh trực tiếp (Direct Branch):** Ensemble xác suất 3 lớp từ `XLM-R` + `DeBERTa`/`Wolf Defender`.
- **Nhánh phân cấp (Hierarchical Branch):**
  - Safety detector ước lượng $P(\text{ATTACK})$ và $P(\text{BENIGN})$.
  - `XLM-R` hoặc classifier chuyên biệt ước lượng $P(\text{PI} \mid \text{ATTACK})$.
  - Công thức:
    $$P(\text{B}) = 1 - P(\text{A})$$
    $$P(\text{J}) = P(\text{A}) \cdot [1 - P(\text{PI} \mid \text{A})]$$
    $$P(\text{PI}) = P(\text{A}) \cdot P(\text{PI} \mid \text{A})$$
- **Hiệu chỉnh:** Calibrate nhiệt độ (temperature calibration) từng nhánh trên OOF trước khi blend.

### 1.3. ⚡ Ba Việc Phải Sửa Ngay (P0)

1. **Head–Tail ở cấp Token hoặc Multi-window:** Tránh mất phần đuôi prompt dài (vốn có thể lên tới 18,550 ký tự); tiền xử lý cắt xén thô sơ hiện tại dễ bỏ lọt attack vectors ở cuối prompt.
2. **Bỏ “per-language threshold” fit/chấm trên cùng OOF:** Sử dụng **nested cross-fitting** hoặc holdout cứng để tránh overfit threshold.
3. **Group các bản dịch/template/near-duplicate:** Gom nhóm trước khi chia fold để đo chính xác **leakage gap** giữa random-CV và group-CV.

### 1.4. Nhịp Thi Đấu Còn Lại (Timeline)

| Cửa Sổ Thời Gian         | Mục Tiêu Chính                                                                | Điểm Chốt (Deliverables)                                             |
| :----------------------- | :---------------------------------------------------------------------------- | :------------------------------------------------------------------- |
| **10:30 – 12:00, 22/10** | Audit dữ liệu + Chuẩn hóa artifact + Sửa P0                                   | Một split chung, thống nhất thứ tự `id` và nhãn `label`              |
| **12:00 – 16:00**        | 3 nhánh model chạy song song                                                  | Mỗi nhánh trả về OOF/test probabilities, metrics theo class/language |
| **16:00 – 18:00**        | Calibrate, blend, nộp S2 – S3                                                 | Khóa các ứng viên tốt nhất để chạy full-fold qua đêm                 |
| **Overnight**            | Full folds/seed cho champion, Wolf long-context hoặc XLM-large (có điều kiện) | Giữ vững kỷ luật, không đổi sang pipeline chưa được test             |
| **08:00 – 10:30, 23/10** | Phân tích kết quả qua đêm, hard-error review, nộp S4 – S5                     | Freeze code toàn bộ lúc 10:30                                        |
| **10:30 – 11:30**        | Kiểm tra validator, quy chuẩn đặt tên notebook, nộp S6 nếu cần                | Không vi chỉnh mù vào phút chót                                      |

> 📌 **Điều kiện top 1 thực tế:**  
> Kế hoạch này tối đa hóa xác suất chiến thắng bằng cách **triệt tiêu rủi ro validation**, **khai thác tính đa dạng giữa các mô hình (model diversity)** và **bảo toàn nghiêm ngặt từng lượt submit**.

---

## 2. Phân Công 4 Thành Viên (Team)

> ⚠️ Mỗi owner chịu trách nhiệm cả **OOF probabilities** và **test probabilities**. Tuyệt đối không bàn giao file nhãn cứng đơn lẻ vì ensemble cần ma trận xác suất đã căn chuẩn thứ tự `id` và nhãn.

| Thành Viên                 | Nhánh Đảm Nhận                      | Nhiệm Vụ Cụ Thể                                                                                                      | Definition of Done (DoD)                                                        |
| :------------------------- | :---------------------------------- | :------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------ |
| **TV1 — XLM-R owner**      | `XLM-R base` đang chạy              | Sửa token-level head–tail; baseline CE vs weighted CE; xuất OOF/test probabilities và error slices.                  | **14:00:** OOF 5-fold (hoặc 3-fold) hoàn chỉnh + artifacts chuẩn hóa            |
| **TV2 — Safety owner**     | `DeBERTa-v3` safety-tuned đang chạy | So sánh direct 3-class với binary `ATTACK`/`BENIGN`; lưu checkpoint binary để dựng hierarchical gate.                | **15:00:** Direct + binary-gate probabilities, confusion matrix chi tiết        |
| **TV3 — Data/robustness**  | `Wolf Defender` + Forensic          | Audit duplicate/template/source; dựng group split; chạy Wolf Defender ưu tiên context dài (1024/2048), multi-window. | **16:00:** Leakage report + Wolf OOF/test; rule-based slices                    |
| **TV4 — Ensemble captain** | Validation, Blending & Submit       | Khóa schema artifacts; temperature calibration; direct blend + hierarchical blend; quản trị 6 lượt submit.           | **Mỗi 90 phút:** Leaderboard ledger; **11:15 ngày 23/10:** Chốt phương án final |

### Hợp Đồng Artifact & Quyền Quyết Định

- **Hợp đồng artifact:** Mỗi run bắt buộc có `run_id`, file config, fold indices, `oof_probs.npy`, `test_probs.npy`, `val_ids.npy`, label order, per-fold/per-class/per-language F1 và prediction distribution.
- **Quyền quyết định:**
  - **TV4:** Có thẩm quyền tối cao khóa ensemble và quản lý submit ledger.
  - **TV3:** Có quyền phủ quyết (veto) mô hình nếu phát hiện leakage gap lớn hoặc chia fold sai quy cách.
  - **Owner model:** Không tự ý lấy submission quota để nộp thử nhánh riêng rẽ.

---

## 3. Backlog Thí Nghiệm Theo ROI (Experiments)

> 🎯 Chạy các hạng mục **P0** trước.  
> Các phương án LLM (Mistral/Granite QLoRA) **không nằm trên critical path** do thời gian tuning và calibration quá lớn so với cửa sổ thời gian của hackathon; tập trung toàn lực cho **Encoder Ensemble**.

|  Tier  | Thử Nghiệm              | Thiết Kế Thử Nghiệm                                                                                                                                       |    Trạng Thái     | Tiêu Chí Giữ Lại (Gate)                                                                    |
| :----: | :---------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------: | :----------------------------------------------------------------------------------------- |
| **P0** | **Validation truth**    | `StratifiedGroupKFold` theo `language × label` + cụm near-duplicate; giữ 1 random split để đo leakage gap                                                 |     Bắt buộc      | **Không submit nếu chỉ dựa vào random-CV**                                                 |
| **P0** | **Long prompt**         | Token-level head/middle/tail windows; max attack score + mean subtype score                                                                               |     Bắt buộc      | Vượt trội rõ rệt so với truncation thô 384 token                                           |
| **A**  | **XLM-R base**          | CE vs Weighted CE (exponent 0.3–0.5); `max_len` 384/512; 3 seeds chỉ chạy cho champion                                                                    |     Đang chạy     | Đánh giá theo group-CV mean và worst-language                                              |
| **B**  | **DeBERTa safety**      | Direct 3-class song song với Binary `ATTACK`/`BENIGN`                                                                                                     |     Đang chạy     | Binary gate phải tăng recall của PI mà không hy sinh precision của `BENIGN`                |
| **C**  | **Wolf Defender**       | Binary safety prior + direct 3-class; mở rộng context 1024/2048 nếu đủ VRAM                                                                               |    Ưu tiên cao    | Error correlation thấp với `XLM-R`                                                         |
| **D**  | **Hierarchical fusion** | Phân cấp xác suất: $P(\text{B})=1-P(\text{A})$; $P(\text{J})=P(\text{A})[1-P(\text{PI}\mid\text{A})]$; $P(\text{PI})=P(\text{A})P(\text{PI}\mid\text{A})$ |    Ưu tiên cao    | Tăng $\ge +0.005$ group-OOF hoặc cải thiện phân biệt rõ `PI` $\leftrightarrow$ `JAILBREAK` |
| **E**  | **Sparse/structural**   | Char TF-IDF + đếm đặc trưng tấn công (role spoofing, override, encoding, homoglyph, length)                                                               |   Có điều kiện    | Chỉ dùng nếu rules cho phép auxiliary non-backbone và tăng group-OOF                       |
| **F**  | **XLM-R large**         | Test nhanh 1 split trước, chỉ chạy full CV nếu vượt trội rõ rệt bản base                                                                                  | Mở rộng (Stretch) | Tăng $\ge +0.008$ trên hard holdout trước 17:00                                            |

> ⚠️ **Quy tắc Ablation tối thiểu:**  
> Không dùng đồng thời: Sampler cân bằng + Class weight mạnh + Focal Loss. Phải so sánh độc lập giữa CrossEntropy tiêu chuẩn, Weighted CrossEntropy nhẹ và Focal Loss. Focal Loss thường làm lệch calibration xác suất, chỉ giữ lại nếu Macro-F1 trên hard split tăng ổn định.

---

## 4. Ngân Sách 6 Lượt Submit (Submit Plan)

|  Lượt  | Deadline Nội Bộ | Ứng Viên Nộp                      | Mục Đích Chiến Lược                                                              | Điều Kiện Bắt Buộc                                                     |
| :----: | :-------------: | :-------------------------------- | :------------------------------------------------------------------------------- | :--------------------------------------------------------------------- |
| **S1** | **22/10 14:00** | Champion Single Model             | Có kết quả hợp lệ sớm nhất (ăn trọn điểm Challenge 1) & lấy mốc LB chuẩn         | Phải vượt qua notebook validator nội bộ                                |
| **S2** | **22/10 16:00** | Safety Model khác họ              | Đo lường mức độ bổ sung giữa dòng Safety-tuned và general Encoder                | File dự đoán phải có khác biệt có ý nghĩa thống kê so với S1           |
| **S3** | **22/10 17:30** | Calibrated 2–3 Model Blend        | Ứng viên tốt nhất cuối ngày thi thứ nhất                                         | Trọng số ensemble khóa từ OOF, không dò đoán trên LB                   |
| **S4** | **23/10 09:00** | Overnight Champion / Hierarchical | Tận dụng kết quả huấn luyện context dài và group-CV qua đêm                      | Chỉ nộp khi vượt qua gate kiểm định nội bộ                             |
| **S5** | **23/10 10:30** | Robust Final Ensemble             | Chọn theo tiêu chí: Mean CV cao + Worst-fold an toàn + F1 của PI cao             | Kiểm tra kỹ phân bố dự đoán (distribution shift) so với tập train/test |
| **S6** | **23/10 11:15** | Reserve / Fallback                | Dự phòng khôi phục hoặc nộp phương án tối ưu cuối cùng nếu có chứng cớ vững chắc | Giữ lại nếu S5 đã hoàn toàn ổn định                                    |

> 📋 **Quy định Submit Ledger:**  
> Bắt buộc ghi chép chi tiết: Commit/config hash, OOF score (group vs random), per-class F1, tỷ lệ dự đoán test, số lượng mẫu đổi nhãn so với lần trước và điểm Public LB. Tuyệt đối không dùng 6 lượt submit để dò threshold.

---

## 5. Quản Trị Rủi Ro & Quy Tắc Dừng (Risk Register & Stop Rules)

| Rủi Ro Nhận Diện                          | Dấu Hiệu Cảnh Báo                                                             | Hành Động Xử Lý Ngay                                                                          |
| :---------------------------------------- | :---------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------- |
| **Leakage do template / bản dịch**        | Random-CV cao hơn Group-CV $> 0.015$                                          | Lấy Group-CV làm chuẩn duy nhất; cluster split; kiểm tra trùng lặp train–test                 |
| **Mất attack vector ở cuối prompt**       | F1 giảm mạnh ở nhóm văn bản có length $> 512$ tokens                          | Áp dụng token sliding windows (head/middle/tail); lấy max attack logits                       |
| **Recall của PI cao nhưng Precision sụp** | Tỷ lệ nhãn `PROMPT_INJECTION` trên test vượt xa prior (~7%) mà không có cơ sở | Giảm class weight; calibrate lại xác suất; soi xét hard negatives chứa từ khóa system/prompt  |
| **Safety model bị lệch ngôn ngữ**         | Worst-language thấp bất thường ở `fr`, `pt` hoặc `it`                         | Giảm trọng số của safety model ở ngôn ngữ đó hoặc chỉ để model làm binary gate                |
| **OOF threshold bị overfit**              | Điểm số chỉ tăng khi fit và chấm trên cùng một tập OOF                        | Chuyển sang nested cross-fitting; kiểm tra độc lập trên seed thứ 2 hoặc holdout cứng          |
| **Hạn chế tài nguyên GPU / Hết giờ**      | Full 5-fold không thể hoàn thành trước 16:00                                  | Chạy 3 fold chung trước; chỉ chạy full 5 fold cho mô hình vô địch; hủy bỏ nhánh LLM 7B        |
| **Vi phạm quy chế cuộc thi**              | Sử dụng model hoặc auxiliary data ngoài danh mục phê duyệt                    | Loại bỏ ngay khỏi pipeline submit; chỉ dùng **10 pretrained backbones** được Kaggle BTC duyệt |

---

## 6. Nguồn Nghiên Cứu & Liên Kết Nhanh

### Tài liệu tham khảo:

- [RMIT Hackathon 2026 Website](https://rmit-hackathon.com/) — Lịch thi đấu và thể lệ chính thức.
- [Patronus Studio Wolf Defender Model Card](https://huggingface.co/patronus-studio/wolf-defender-prompt-injection) — Context 2048, kỹ thuật data augmentation (obfuscation/translation) và benchmark an toàn.
- [ProtectAI DeBERTa-v3 Model Card](https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2) — Bộ phân loại an toàn chuyên biệt tiếng Anh.
- [PMLR 2026: Prompt Injection Detection is Regime-Dependent](https://proceedings.mlr.press/v348/akinrele26a.html) — Phân tích structural signals, threshold sensitivity và OOD evaluation.

### Notebooks & Docs trong Workspace:

- 📓 [challenge-1/notebooks/tony-rmit-sgs-stressnotfound-c1.ipynb](file:///d:/CODE%20PLAYGROUND/Projects/Competitions/RMIT-Hackathon-2026/challenge-1/notebooks/tony-rmit-sgs-stressnotfound-c1.ipynb) — Ensemble notebook
- 📓 [challenge-1/Tai/multilingual_prompt_attack_classification.ipynb](file:///d:/CODE%20PLAYGROUND/Projects/Competitions/RMIT-Hackathon-2026/challenge-1/Tai/multilingual_prompt_attack_classification.ipynb) — XLM-R notebook
- 📄 [challenge-1/docs/03_models_and_baseline.md](file:///d:/CODE%20PLAYGROUND/Projects/Competitions/RMIT-Hackathon-2026/challenge-1/docs/03_models_and_baseline.md) — 10 mô hình được duyệt
