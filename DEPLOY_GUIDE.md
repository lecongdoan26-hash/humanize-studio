# 🌐 Hướng Dẫn Triển Khai Klaro AI Lên Máy Chủ Đám Mây (Cloud Deployment)

Tài liệu này hướng dẫn bạn cách đưa phần mềm **Klaro AI** từ máy tính cá nhân lên mạng Internet để:
- Chạy tự động 24/7 không cần mở máy tính cá nhân.
- Truy cập từ bất kỳ đâu (điện thoại, máy tính bảng, laptop).
- Cho nhiều nhân viên hoặc khách hàng cùng truy cập qua link website riêng.

---

## 🛠️ YÊU CẦU CẤU HÌNH MÁY CHỦ (SERVER SPEC)

Do phần mềm sử dụng trình duyệt ngầm **Playwright Chromium** để cào nhóm và tự động hóa Facebook, cấu hình tối thiểu khuyến nghị:
- **Hệ điều hành:** Ubuntu 22.04 LTS hoặc Ubuntu 24.04 LTS (hoặc Windows Server).
- **CPU:** 2 vCPU trở lên.
- **RAM:** 4 GB RAM (tối thiểu 2GB).
- **Dung lượng ổ cứng:** 25 GB SSD trở lên.
- **Chi phí thuê:** Khoảng 120.000đ – 250.000đ/tháng (Tại Vietnix, TinoHost, AZDIGI, Hetzner, Vultr hoặc DigitalOcean).

---

## 🚀 CÁCH 1: TRIỂN KHAI BẰNG DOCKER (KHUYÊN DÙNG — CHUẨN DOANH NGHIỆP)

Docker giúp đóng gói toàn bộ môi trường Linux, Python và Chromium vào một container độc lập, không sợ thiếu thư viện hay lỗi môi trường.

### Bước 1: Cài đặt Docker trên VPS (Chỉ làm 1 lần)
Kết nối vào VPS qua SSH (dùng PuTTY hoặc Terminal) và chạy lệnh:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### Bước 2: Tải mã nguồn Klaro AI lên VPS
Bạn có thể nén thư mục `DOAN MKT AI` thành file `.zip` và tải lên VPS qua phần mềm **FileZilla** hoặc **WinSCP**, sau đó giải nén vào thư mục `/home/klaro`:
```bash
mkdir -p /home/klaro
cd /home/klaro
# Sau khi copy code vào đây
```

### Bước 3: Khởi động hệ thống chỉ với 1 câu lệnh
Tại thư mục chứa mã nguồn trên VPS, chạy lệnh:
```bash
docker compose up -d --build
```
Hệ thống sẽ tự động tải các gói phụ thuộc, cài đặt Chromium headless và chạy ngầm máy chủ Klaro AI.

Bây giờ bạn có thể truy cập website qua địa chỉ: `http://IP_CUA_VPS:8000`

---

## 🔒 CÁCH GẮN TÊN MIỀN RIÊNG & BẢO MẬT SSL (HTTPS)

Để website có link đẹp như: `https://app.yourdomain.com`:

### 1. Trỏ DNS tên miền
- Đăng nhập vào nhà quản lý tên miền (Cloudflare, Namecheap, PA Vietnam...).
- Tạo bản ghi **A record**:
  - Tên: `app` (hoặc `@` nếu muốn dùng tên miền chính).
  - Giá trị: Nhập địa chỉ `IP của VPS`.

### 2. Cài Nginx và Chứng chỉ SSL miễn phí (Certbot) trên VPS:
```bash
sudo apt update && sudo apt install -y nginx certbot python3-certbot-nginx

# Tạo cấu hình Nginx
sudo nano /etc/nginx/sites-available/klaro
```
Dán cấu hình sau (thay `app.yourdomain.com` bằng tên miền của bạn):
```nginx
server {
    server_name app.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Kích hoạt cấu hình và lấy SSL HTTPS tự động:
```bash
sudo ln -s /etc/nginx/sites-available/klaro /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d app.yourdomain.com
```

---

## ⚡ CÁCH 2: DÙNG CLOUDFLARE TUNNEL (MIỄN PHÍ — TEST ONLINE NGAY BÂY GIỜ)

Nếu bạn chưa muốn mua VPS ngay mà muốn đưa máy tính hiện tại thành link website công khai trên Internet để test thử từ điện thoại:

1. Tải công cụ **cloudflared** miễn phí từ Cloudflare.
2. Mở PowerShell trong thư mục dự án và chạy:
   ```bash
   winget install Cloudflare.cloudflared
   cloudflared tunnel --url http://localhost:8000
   ```
3. Cloudflare sẽ tạo cho bạn một đường link HTTPS công khai (ví dụ: `https://random-name.trycloudflare.com`). Bạn có thể gửi link này cho bạn bè hoặc mở trên điện thoại để trải nghiệm ngay lập tức!
