# 🚀 Klaro AI — Hệ Điều Hành Marketing & Săn Khách Tự Động (AI Marketing OS)

Hệ thống Marketing tự động lấy cảm hứng từ Orbitama, kết hợp giữa **Tự động hóa trình duyệt (Playwright)** và **Trí tuệ nhân tạo (Google Gemini AI)** nhằm tối ưu hóa quy trình tìm kiếm khách hàng tiềm năng, phân tích nhu cầu và đăng bài đa tài khoản trên Facebook.

---

## 🌟 Các Tính Năng Đã Xây Dựng

1. **⚡ Dây Chuyền Phòng Marketing (10 AI Agents Assembly Line — Lấy cảm hứng từ AgentBoss):**
   - **Cơ chế cốt lõi:** Mô hình Multi-Agent khép kín với triết lý *"Việc chảy từ tay ai sang tay ai"*.
   - **👑 Trưởng phòng Philip Kotler:** Nhận đề bài chiến dịch từ Boss, điều phối tổng thể và phân công nhiệm vụ.
   - **🕵️ Sherlock Holmes (Trinh sát):** Bóc tách insight thị trường, tìm kiếm 3 nỗi đau cốt lõi và trending hooks.
   - **⚔️ Tôn Tử (Chiến lược):** Hoạch định 3 góc đánh chiến lược, ma trận nội dung và chỉ thị viết bài.
   - **✍️ David Ogilvy (Viết):** Viết bài bán hàng chuyển đổi cao (Hook - Story - Offer - CTA) cùng 3 biến thể tiêu đề.
   - **🎨 Pablo Picasso (Ảnh):** Thiết kế visual concept, tạo Prompt Midjourney/Flux chi tiết và cấu trúc banner.
   - **🎬 Steven Spielberg (Video):** Dựng kịch bản video ngắn 35s (Hook - Problem - Solution - CTA) kèm voiceover & SFX.
   - **📢 Mark Zuckerberg (Đăng bài):** Lên kế hoạch phân phối đa kênh, **có cổng dừng `1 chờ duyệt`** để Boss phê duyệt an toàn trước khi đăng.
   - **📧 Russell Brunson (Email, Phễu):** Tạo quà tặng mồi (Lead Magnet) và chuỗi 3 email nuôi dưỡng tự động.
   - **🎯 Robin Hood (Quảng cáo):** Thiết lập tệp đối tượng nhắm mục tiêu (Target Interests) và phân bổ ngân sách 70-20-10.
   - **📊 Warren Buffett (Số liệu):** Thẩm định tài chính, dự phóng CTR, CPA, ROI 380% và gửi khuyến nghị về cho Kotler.
   - **Giao diện trực quan:** Hiển thị sơ đồ dây chuyền serpentine với đường nối phát sáng động khi giao việc và Avatar Robot chibi sắc nét!

2. **AI Lead Hunter (Săn khách tiềm năng thông minh):**
   - Đọc hiểu bài đăng từ các nhóm Facebook.
   - Sử dụng AI để bóc tách nhu cầu thực tế, loại bỏ 100% bài spam/bán hàng/tuyển dụng vô nghĩa.
   - Chấm điểm tiềm năng (Lead Score 0-100), phân loại mức độ cấp bách và tóm tắt nhu cầu khách hàng.
   - Tự động sinh câu trả lời tư vấn (Suggested Reply) cá nhân hóa, kèm thông tin liên hệ/CTA của bạn.

3. **Content Studio & AI Spin:**
   - Soạn bài đăng gốc một lần.
   - AI tự động nhân bản thành 3 biến thể nội dung khác nhau về từ ngữ, icon, cấu trúc câu để tránh thuật toán phạt trùng lặp khi đăng nhiều nick.

4. **Multi-Account Session Guard:**
   - Đăng nhập Facebook trực tiếp trên trình duyệt Chromium thực tế để người dùng xác thực an toàn (vượt 2FA, Captcha).
   - Tự động trích xuất Cookie và Local Storage để lưu trữ phiên (`data/fb_profiles/`), không bao giờ lưu lộ mật khẩu.

5. **Web Dashboard Trực Quan (AgentBoss & Dark-mode UI):**
   - Giao diện Dark-mode hiện đại, hiển thị sơ đồ dây chuyền phòng ban, biểu đồ thống kê, danh sách Lead CRM, nhật ký hoạt động thời gian thực.
   - Chạy hoàn toàn trên máy cục bộ (Localhost) an toàn và riêng tư.

---

## 🛠️ Cấu Trúc Dự Án

```
DOAN MKT AI/
│
├── core/
│   ├── config.py           # Quản lý đường dẫn, cấu hình .env
│   ├── database.py         # Cơ sở dữ liệu SQLite cục bộ (mkt_system.db)
│   ├── ai_engine.py        # Bộ não AI Gemini & Thuật toán lọc bài viết
│   └── fb_automation.py    # Playwright điều khiển trình duyệt cào nhóm & đăng bài
│
├── web/
│   ├── templates/
│   │   └── index.html      # Giao diện Web Dashboard (Tailwind CSS)
│   └── app.py              # Máy chủ FastAPI & REST APIs
│
├── data/
│   ├── fb_profiles/        # Nơi lưu trữ session/cookie của các nick Facebook
│   └── mkt_system.db       # Dữ liệu khách hàng, tài khoản, nhóm
│
├── Chay_Phan_Mem.bat       # Phím tắt 1-click khởi động phần mềm trên Windows
├── run.py                  # Script khởi chạy hệ thống
└── README.md
```

---

## 🚀 Hướng Dẫn Sử Dụng

### Cách 1: Chạy bằng file Batch (Nhanh nhất)
- Nhấp đúp chuột vào file `Chay_Phan_Mem.bat` trong thư mục dự án.
- Trình duyệt sẽ tự động mở trang quản trị: **`http://127.0.0.1:8000`**.

### Cách 2: Chạy bằng dòng lệnh Terminal
```bash
python run.py
```
Sau đó mở trình duyệt truy cập: `http://127.0.0.1:8000`

---

## ⚙️ Cài đặt Khuyên Dùng

1. Vào tab **⚙️ Cài đặt & AI** trên giao diện:
   - Dán mã **Google Gemini API Key** (lấy miễn phí tại [aistudio.google.com](https://aistudio.google.com/)).
   - Điền tên doanh nghiệp, sản phẩm/dịch vụ bạn muốn bán và thông tin liên hệ (Zalo, SĐT).
2. Vào tab **👥 Tài khoản FB**:
   - Bấm **Thêm & Đăng Nhập Nick Mới** để kết nối tài khoản Facebook phụ của bạn.
3. Vào tab **🎯 Săn khách AI**:
   - Bấm **Kích Hoạt Quét Nhóm Mới** để cào bài viết và xem AI bóc tách khách hàng trực tiếp!
