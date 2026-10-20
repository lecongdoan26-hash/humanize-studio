# HƯỚNG DẪN VẬN HÀNH & TRIỂN KHAI CÔNG CỤ "HUMANIZE AI VIỆT NAM"
*Hệ thống Chuẩn hóa & Thổi hồn nội dung AI thành văn phong Người Thật*

---

## 🌟 TỔNG QUAN HỆ THỐNG ĐÃ HOÀN THÀNH

Chúng ta đã hoàn thiện toàn bộ kiến trúc 4 bước cho công cụ này:

1. **Bước 1: Quản lý API Key**
   - Hỗ trợ nhập Google Gemini API Key trực tiếp trên giao diện Web (lưu vào localStorage an toàn).
   - Hỗ trợ cấu hình `GEMINI_API_KEY` trong file `.env` của server.

2. **Bước 2: Bộ não xử lý (Core Engine - `core/humanizer_engine.py`)**
   - **AI Cliché Detector:** Tự động phát hiện hàng loạt sáo ngữ AI tiếng Việt điển hình (*"trong kỷ nguyên số", "đóng vai trò quan trọng", "chìa khóa vàng", "bức tranh toàn cảnh"...*).
   - **Burstiness Analyzer:** Đo lường độ biến thiên chiều dài câu để đánh giá nhịp điệu bài viết.
   - **3 Chế độ chuyên biệt:**
     - 🎓 **Luận văn & Đồ án:** Lập luận phản biện logic, câu từ học thuật chuẩn mực, chống bịa số liệu/trích dẫn ảo (anti-hallucination).
     - 📱 **Content Marketing & Social:** Bẻ câu ngắn, tạo 2 câu Hook đâm trúng pain point, nhịp điệu đàm thoại bắt trend, xóa emoji thừa.
     - 🌐 **Blog & Web SEO:** Tối ưu Search Intent ngay đầu bài, bổ sung góc nhìn thực chiến chuẩn Google E-E-A-T.
   - **3 Mức độ can thiệp:** Nhẹ nhàng (Light), Cân bằng (Balanced), Lột xác toàn diện (Creative).

3. **Bước 3: Giao diện Web SaaS (`web/templates/humanizer.html` & `web/app.py`)**
   - Thiết kế Dark Mode Glassmorphism hiện đại, chuyên nghiệp.
   - Thang đo **AI Flop Meter** (Độ nặng mùi AI & Nhịp điệu câu).
   - Bảng so sánh Before vs After trực quan.
   - Nút 1-Click Copy kết quả, tải file `.txt`, nút thử nhanh văn bản mẫu.
   - Đã tích hợp trực tiếp vào router: `http://localhost:8000/humanizer` và thanh điều hướng của hệ thống Marketing.

4. **Bước 4: Triển khai (Deploy) đưa lên Internet cho khách hàng dùng**

---

## 🚀 HƯỚNG DẪN CHẠY THỬ NGHIỆM TRÊN MÁY (LOCAL)

### Cách 1: Chạy bằng file Batch có sẵn
- Nhấp đúp chuột vào file **`Chay_Phan_Mem.bat`** trong thư mục dự án.

### Cách 2: Chạy bằng dòng lệnh Terminal
```powershell
python run.py
```
Sau đó mở trình duyệt truy cập:
*   Công cụ Humanize AI: **`http://localhost:8000/humanizer`**
*   Trang chủ Marketing Agent: **`http://localhost:8000/`**

---

## 🔑 HƯỚNG DẪN LẤY GEMINI API KEY MIỄN PHÍ (Trong 1 phút)

1. Truy cập: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Đăng nhập bằng tài khoản Google (Gmail) của bạn.
3. Bấm nút xanh **"Create API key"** -> Chọn **"Create key in new project"**.
4. Copy chuỗi ký tự vừa tạo (bắt đầu bằng `AIzaSy...`).
5. Dán vào ô cài đặt API Key trên trang web công cụ hoặc ghi vào file `.env`:
   ```env
   GEMINI_API_KEY=AIzaSy...chuỗi_key_của_bạn...
   ```

---

## 🌐 HƯỚNG DẪN TRIỂN KHAI ĐỂ LÀM DỊCH VỤ CHO NGƯỜI KHÁC DÙNG (DEPLOY)

Để người khác ở bất kỳ đâu cũng có thể truy cập qua link web và sử dụng, bạn có 2 cách cực kỳ phổ biến sau:

### Cách A: Triển khai miễn phí lên Cloud Render.com (Khuyên dùng - Ổn định nhất)
1. **Đưa mã nguồn lên GitHub:**
   - Tạo một repository mới trên GitHub (ví dụ: `humanize-ai-vietnam`).
   - Đẩy toàn bộ thư mục code này lên GitHub.
2. **Đăng ký Render.com:**
   - Truy cập [https://render.com](https://render.com) và đăng nhập bằng GitHub.
   - Chọn **New +** $\rightarrow$ **Web Service**.
   - Kết nối với Repository GitHub của bạn.
3. **Cấu hình thông số trên Render:**
   - **Name:** `humanize-ai` (hoặc tên bạn thích).
   - **Environment:** `Python 3`.
   - **Build Command:** `pip install -r requirements.txt`.
   - **Start Command:** `uvicorn web.app:app --host 0.0.0.0 --port $PORT`.
4. **Thêm biến môi trường:**
   - Vào mục **Environment Variables** $\rightarrow$ Thêm key:
     - `GEMINI_API_KEY` = *dán key Gemini của bạn vào đây*.
5. Bấm **Deploy Web Service**:
   - Sau 2-3 phút, Render sẽ cấp cho bạn một đường link công khai dạng:
     `https://humanize-ai.onrender.com/humanizer`
   - Bạn có thể gửi link này cho bạn bè, khách hàng, giảng viên chấm bài dùng thử ngay lập tức!

---

### Cách B: Chia sẻ nhanh link trực tiếp từ máy của bạn (Demo ngay không cần upload)
Nếu bạn muốn demo cho khách hàng hoặc bạn bè xem ngay bây giờ mà chưa kịp đẩy lên GitHub:
1. Chạy phần mềm trên máy: `python run.py`.
2. Mở thêm 1 cửa sổ PowerShell mới và dùng công cụ Cloudflare Tunnel miễn phí (không cần đăng ký):
   ```powershell
   winget install --id Cloudflare.cloudflared
   cloudflared tunnel --url http://localhost:8000
   ```
3. Cloudflare sẽ tạo cho bạn một đường link bí mật HTTPS dạng:
   `https://random-name.trycloudflare.com/humanizer`
4. Bất kỳ ai mở link đó trên điện thoại hay máy tính đều dùng được web của bạn!
