# Challenge 2 — UNLOCKED: Build with TideCloak

> Tài liệu tổng hợp thông tin RMIT Hackathon 2026 — Challenge 2.  
> Cập nhật: 22/10/2026 (UTC+7).

## 1. Tổng quan cuộc thi

- **Tên sự kiện:** RMIT Hackathon 2026
- **Thời gian:** 22–23/10/2026
  - Ngày 1: 08:00–18:00, 22/10/2026
  - Ngày 2: 08:00–12:00, 23/10/2026
- **Khu vực:** Australia, Việt Nam và Malaysia
- **Ngôn ngữ:** Tiếng Anh
- **Hình thức:** Thi trực tiếp; tất cả thành viên phải có mặt tại cùng một địa điểm thi.
- **Quy mô đội:** 4 sinh viên đang theo học bậc đại học hoặc sau đại học.
- **Chủ đề chung:** Security × Generative AI × Low-Resource Languages.
- **Đơn vị/đối tác xuất hiện tại sự kiện:** RMIT University, Taylor's University, Tide, DesignLive, Katalon và Orange Logic Vietnam.

Các địa điểm thi được công bố:

- RMIT University — Saigon South, TP. Hồ Chí Minh
- RMIT University — Hanoi
- RMIT University — Melbourne
- Taylor's University Lakeside Campus — Malaysia

## 2. Challenge 2

- **Tên challenge:** UNLOCKED
- **Đơn vị ra đề:** Tide
- **Công nghệ bắt buộc:** TideCloak
- **Câu hỏi định hướng:** Nếu niềm tin không còn là nút thắt, bạn sẽ xây dựng điều gì?

### Nhiệm vụ

Chọn một khả năng hoặc trải nghiệm hữu ích hiện đang bị cản trở bởi vấn đề về niềm tin, quyền riêng tư hoặc bảo mật. Xây dựng một **prototype nhỏ nhưng hoạt động được**, có tích hợp TideCloak, để chứng minh một khả năng mới.

Giải pháp cần thể hiện rằng không một quản trị viên, tổ chức hay AI đơn lẻ nào có thể tự ý vượt qua các quy tắc bảo vệ dữ liệu và quyết định của người dùng. Phần demo phải giải thích được việc loại bỏ quyền kiểm soát đơn phương đã làm cho ý tưởng trở nên khả thi như thế nào.

Không yêu cầu kinh nghiệm trước về an ninh mạng hoặc mật mã. Ban tổ chức không kỳ vọng một sản phẩm hoàn chỉnh; đội thi nên tập trung vào **một minh chứng thuyết phục và chạy được**.

## 3. TideCloak và Emergent Authority

### TideCloak

TideCloak là hệ thống có thể tích hợp vào ứng dụng để cung cấp:

- Xác thực người dùng;
- Phân quyền;
- Bảo vệ dữ liệu;
- Mã hóa đầu cuối theo phiên;
- Các cơ chế quản trị và phê duyệt nhiều bên khi phù hợp với bài toán.

Challenge không hướng tới một màn hình đăng nhập đơn thuần, một công cụ bảo mật chung chung hay một dashboard phân quyền. TideCloak phải **thay đổi đáng kể điều mà sản phẩm có thể thực hiện một cách đáng tin cậy**.

### Emergent Authority

Trong hệ thống truyền thống, thường có một cá nhân hoặc hệ thống cuối cùng nắm quyền mở khóa dữ liệu, phê duyệt truy cập hoặc thay đổi luật. Với **Emergent Authority**, không bên nào giữ toàn bộ quyền lực đó một mình. Quyền thực hiện một thao tác chỉ xuất hiện khi danh tính, chính sách và các phê duyệt cần thiết đồng thời thỏa mãn.

Các node độc lập trong mạng Tide phối hợp để thực hiện thao tác được bảo vệ. Không node, máy chủ ứng dụng hay quản trị viên đơn lẻ nào có đủ thẩm quyền để tự thực hiện thao tác, và ứng dụng không cần giữ một master key có thể tái sử dụng.

## 4. Quy trình đề xuất

1. **Chọn một khả năng:** Xác định điều hữu ích đang bị giới hạn bởi rào cản về niềm tin, quyền riêng tư hoặc bảo mật.
2. **Kết nối coding agent:** Thêm MCP server của Tide vào coding agent tương thích MCP như Claude Code, Cursor hoặc VS Code.
3. **Xây dựng với TideCloak:** Mô tả ứng dụng và quy tắc truy cập; có thể dùng dữ liệu tổng hợp và mock các hệ thống bên ngoài.
4. **Demo và nộp bài:** Cho thấy khả năng mới hoạt động, vai trò thực tế của TideCloak, sau đó chuẩn bị video và repository.

Nếu không dùng được MCP, có thể bắt đầu từ **TideCloak Quickstart**, vốn cung cấp một template đã tích hợp TideCloak.

## 5. Yêu cầu nộp bài

Nộp **một đường dẫn GitHub repository công khai** qua Google Form:

- Form nộp bài: <https://forms.gle/HRHYjnqB86j1LFS97>
- Repository phải để ở chế độ **public**.
- Repository phải chứa:
  - Toàn bộ source code của prototype hoạt động được và đã tích hợp TideCloak;
  - File `README.md`;
  - Video demo định dạng `.mp4`.
- Tên nhóm trên biểu mẫu theo mẫu:

```text
<university>_<campus>_<team>_C2
```

Ví dụ:

```text
RMIT_SGS_MyTeam_C2
```

Mã campus được dùng trong hướng dẫn cuộc thi:

- `SGS`: Saigon South
- `HNI`: Hanoi
- `MEL`: Melbourne
- `MYS`: Malaysia

### Deadline

- **Việt Nam:** 18:00, thứ Năm 22/10/2026 (UTC+7)
- **Malaysia:** 18:00, thứ Năm 22/10/2026 (UTC+8)
- **Melbourne:** 10:00, thứ Sáu 23/10/2026 (AEDT, UTC+11)

Ba mốc trên tương ứng với cùng một thời điểm tuyệt đối.

## 6. Yêu cầu đối với README

Đặt phần **Project overview** ở đầu `README.md`, bắt đầu bằng mô tả dự án trong một câu, sau đó trả lời năm nội dung tương ứng với tiêu chí chấm:

1. **Vision & originality:** Sản phẩm, dịch vụ, trải nghiệm hoặc cách làm việc mới là gì? Điểm khác biệt của ý tưởng là gì?
2. **Trust constraint insight:** Vấn đề nào hiện khó, rủi ro hoặc bất khả thi vì rào cản niềm tin, quyền riêng tư hay bảo mật? Khi gỡ bỏ rào cản đó thì điều gì trở nên khả thi?
3. **Value & impact:** Ai được hưởng lợi, cuộc sống hoặc công việc của họ được cải thiện như thế nào? Nêu một ví dụ cụ thể.
4. **Why TideCloak matters:** Ứng dụng sử dụng TideCloak như thế nào và việc tích hợp này giúp hiện thực hóa ý tưởng ra sao?
5. **Prototype & storytelling:** Prototype hiện chứng minh được điều gì? Tương tác quan trọng nào ban giám khảo cần chú ý?

Quy định trình bày:

- Phần Project overview không quá **300 từ**;
- Có thể dùng đoạn văn ngắn hoặc bullet points;
- Hướng dẫn cài đặt/chạy ứng dụng đặt trong mục **Setup** riêng;
- Có thể sử dụng badge “Built with TideCloak” theo template chính thức.

## 7. Yêu cầu đối với video demo

- Thời lượng: **2 phút**;
- Định dạng: `.mp4`;
- Dung lượng: dưới **100 MB** để phù hợp giới hạn file của GitHub;
- Lưu trực tiếp trong GitHub repository.

Cấu trúc video được đề xuất:

1. **The possibility:** Đội đã chọn xây dựng điều gì?
2. **The constraint:** Vấn đề niềm tin nào đang cản trở điều đó?
3. **The prototype:** Cho thấy prototype hoạt động và vai trò của TideCloak.
4. **What changes:** Điều gì nay đã trở nên khả thi cho người dùng?

## 8. Tiêu chí chấm điểm

### Vision & originality — 25%

Một câu trả lời mới mẻ và tham vọng cho challenge.

### Trust constraint insight — 20%

Chỉ rõ rào cản hiện tại liên quan đến niềm tin, quyền riêng tư, quyền lưu giữ hoặc thẩm quyền.

### Value & impact — 20%

Tạo ra giá trị có ý nghĩa cho con người, tổ chức hoặc xã hội.

### Why TideCloak matters — 20%

Chứng minh TideCloak thực sự thay đổi khả năng mà sản phẩm có thể cung cấp một cách đáng tin cậy.

### Prototype & storytelling — 15%

Trình bày ý tưởng dễ hiểu và cho thấy prototype hoạt động.

Ban giám khảo sẽ đọc phần Project overview trong README cùng với video demo.

## 9. Gợi ý ý tưởng từ ban tổ chức

Đây chỉ là nguồn cảm hứng, không phải các track bắt buộc:

- **Care Passport:** Bệnh nhân chỉ chia sẻ từng hồ sơ sức khỏe với đúng bác sĩ cần truy cập.
- **Research Consent Vault:** Người tham gia nghiên cứu kiểm soát dữ liệu và có thể thu hồi quyền truy cập trong tương lai.
- **Rental Application Passport:** Tái sử dụng hồ sơ thuê nhà nhưng chỉ tiết lộ tài liệu cần thiết cho từng bên.
- **Blind Portfolio Review:** Ẩn danh tính trong giai đoạn đánh giá đầu và chỉ mở khi đúng vai trò, đúng giai đoạn.
- **Unreleased:** Chia sẻ tác phẩm chưa phát hành với từng cộng tác viên mà nền tảng không có quyền đọc toàn bộ.
- **Supplier Evidence Exchange:** Chia sẻ các gói bằng chứng tuân thủ khác nhau cho khách hàng và kiểm toán viên.
- **Matter Room:** Phân quyền tài liệu vụ việc cho khách hàng, luật sư, chuyên gia và đối tác.
- **Dual-Control Expense Desk:** Yêu cầu nhiều phê duyệt cho khoản chi lớn và ngăn một admin tự nâng quyền.
- **Guild Treasury:** Quản lý tài sản cộng đồng mà không trao toàn quyền cho một moderator.
- **Coalition Intel Exchange:** Chia sẻ báo cáo tổng hợp giữa các cơ quan giả lập theo quy tắc phát hành.
- **CreatorVault:** Mở nội dung mã hóa theo quyền lợi thuê bao hoặc giao dịch giả lập.
- **Community Ballot:** Bỏ phiếu riêng tư, chống bỏ phiếu trùng và yêu cầu quản trị nhiều bên cho thay đổi nhạy cảm.

Với các kịch bản y tế, tài chính, chính phủ hoặc dữ liệu nhạy cảm, nên sử dụng dữ liệu tổng hợp. Việc thu hồi quyền chỉ ngăn các lần truy cập được cấp phép trong tương lai; nó không thể thu hồi nội dung mà người nhận đã xem hoặc sao chép.

## 10. Checklist trước khi nộp

- [ ] Prototype chạy được và TideCloak đã được tích hợp thực tế.
- [ ] Demo thể hiện một khả năng mới, không chỉ là đăng nhập/phân quyền thông thường.
- [ ] Dùng dữ liệu tổng hợp hoặc mock khi có dữ liệu nhạy cảm.
- [ ] Repository ở chế độ public.
- [ ] Source code đầy đủ và có hướng dẫn Setup chạy được.
- [ ] Project overview nằm ở đầu README và không quá 300 từ.
- [ ] README trả lời đủ năm tiêu chí chấm điểm.
- [ ] Video `.mp4` dài tối đa 2 phút và dưới 100 MB.
- [ ] Video được lưu trong repository.
- [ ] Tên nhóm đúng mẫu `<university>_<campus>_<team>_C2`.
- [ ] Nộp đúng GitHub URL qua Google Form trước deadline tại địa điểm thi.

## 11. Tài nguyên chính thức

- Challenge 2 — UNLOCKED: <https://tide.org/unlocked>
- TideCloak overview: <https://tide.org/tidecloak>
- TideCloak documentation: <https://docs.tide.org/>
- Tide coding-agent plugins/MCP: <https://tide.org/agent-plugins>
- TideCloak Quickstart: <https://docs.tide.org/get-started/Tidecloak%20Quickstart>
- Emergent Authority: <https://tide.org/blog/emergent-authority-beyond-cybersecurity>
- Tide Discord: <https://discord.gg/XBMd9ny2q5>
- Trang RMIT Hackathon 2026: <https://rmit-hackathon.com/>
- Form nộp Challenge 2: <https://forms.gle/HRHYjnqB86j1LFS97>
- Video giới thiệu UNLOCKED: <https://youtu.be/gHlev6-kB3I>
- Video hướng dẫn Tide MCP với Claude Code trong VS Code: <https://youtu.be/z0o-B3258Cg>

## 12. Nguồn và ghi chú

Tài liệu này được tổng hợp từ:

1. Trang chính thức Challenge 2 của Tide và dữ liệu cấu hình công khai của trang, truy cập ngày 22/10/2026.
2. Trang chính thức RMIT Hackathon 2026, truy cập ngày 22/10/2026.
3. Slide “Submission guidelines” tại sự kiện do người dùng cung cấp, dùng để đối chiếu quy tắc đặt tên nhóm, thành phần repository và deadline tại Việt Nam.

Nếu có khác biệt giữa tài liệu này và thông báo mới của ban tổ chức, ưu tiên nội dung trên trang UNLOCKED, biểu mẫu nộp bài và thông báo trực tiếp tại địa điểm thi.
