import sys
import os

if sys.platform.startswith('win'):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

from core.database import init_db
init_db()

from core.fb_automation import login_and_save_session, import_cookie_session

print("=" * 60)
print("     🔗 KẾT NỐI TÀI KHOẢN FACEBOOK - KLARO AI")
print("=" * 60)
acc_name = input("Nhập tên gợi nhớ cho nick (VD: Nick_Chinh, Nick_01): ").strip()
if not acc_name:
    acc_name = "Nick_Facebook_01"

print("\nChọn phương thức kết nối:")
print("1. Mở cửa sổ trình duyệt để tự đăng nhập Facebook")
print("2. Dán chuỗi Cookie Facebook (Nhanh trong 3 giây)")
choice = input("Nhập lựa chọn của bạn (1 hoặc 2): ").strip()

if choice == "2":
    print("\nNhập hoặc dán chuỗi Cookie Facebook:")
    cookie_str = input().strip()
    if cookie_str:
        res = import_cookie_session(acc_name, cookie_str)
        print("\n=>", res.get("message"))
    else:
        print("\n=> Chưa nhập cookie!")
else:
    print(f"\nĐang khởi động trình duyệt cho '{acc_name}'...")
    print("Vui lòng đăng nhập Facebook trên cửa sổ Chromium vừa mở.")
    print("Hệ thống sẽ tự động lưu phiên (Session) khi bạn vào Bảng tin!")
    res = login_and_save_session(acc_name, timeout_seconds=240)
    print("\n=>", res.get("message"))

print("=" * 60)
input("Nhấn phím Enter để đóng cửa sổ...")
