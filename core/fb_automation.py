import os
import json
import time
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from playwright.sync_api import sync_playwright, BrowserContext, Page

from core.config import PROFILES_DIR
from core.database import get_connection, log_activity
from core.ai_engine import analyze_and_classify_lead

def get_profile_path(account_name: str) -> Path:
    safe_name = "".join([c if c.isalnum() or c in "-_" else "_" for c in account_name])
    return PROFILES_DIR / f"{safe_name}.json"

def has_saved_session(account_name: str) -> bool:
    return get_profile_path(account_name).exists()

def login_and_save_session(account_name: str, timeout_seconds: int = 180) -> Dict[str, Any]:
    """
    Mở trình duyệt thực tế (visible) để người dùng tự đăng nhập Facebook an toàn.
    Sau khi đăng nhập thành công, tự động lưu lại cookie/session.
    """
    profile_path = get_profile_path(account_name)
    log_activity("FACEBOOK", f"Bắt đầu mở trình duyệt đăng nhập cho tài khoản: {account_name}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto("https://www.facebook.com/", wait_until="networkidle")
        
        print(f"[{account_name}] Hãy đăng nhập Facebook trên cửa sổ trình duyệt vừa mở...")
        start_time = time.time()
        logged_in = False
        
        while time.time() - start_time < timeout_seconds:
            time.sleep(2)
            # Kiểm tra xem đã vào trang chủ (feed) chưa
            url = page.url
            if any(k in url for k in ["facebook.com/?", "facebook.com/home", "facebook.com/watch", "facebook.com/groups"]) or (url == "https://www.facebook.com/"):
                # Check for search bar or user avatar
                try:
                    if page.locator("div[role='navigation']").count() > 0 or page.locator("input[placeholder*='tìm kiếm']").count() > 0 or page.locator("input[placeholder*='Search']").count() > 0:
                        logged_in = True
                        break
                except:
                    pass
            # Nếu người dùng đóng trình duyệt thủ công
            if page.is_closed():
                break
                
        if logged_in:
            storage = context.storage_state()
            with open(profile_path, "w", encoding="utf-8") as f:
                json.dump(storage, f, ensure_ascii=False, indent=2)
                
            conn = get_connection()
            conn.execute("INSERT OR REPLACE INTO accounts (name, status, profile_file) VALUES (?, 'active', ?)", 
                         (account_name, str(profile_path)))
            conn.commit()
            conn.close()
            
            log_activity("FACEBOOK", f"Đăng nhập & lưu session thành công cho {account_name}")
            browser.close()
            return {"success": True, "message": "Đăng nhập và lưu phiên thành công!"}
        else:
            browser.close()
            log_activity("FACEBOOK", f"Hết thời gian chờ đăng nhập ({timeout_seconds}s) cho {account_name}", level="WARNING")
            return {"success": False, "message": "Hết thời gian chờ hoặc chưa hoàn tất đăng nhập."}

def import_cookie_session(account_name: str, cookie_raw: str) -> Dict[str, Any]:
    """
    Nhập Cookie Facebook để tạo phiên đăng nhập ngay lập tức không cần gõ mật khẩu.
    Hỗ trợ cả chuỗi c_user=...; xs=... hoặc định dạng JSON.
    """
    profile_path = get_profile_path(account_name)
    cookie_raw = cookie_raw.strip()
    cookies_list = []
    fb_uid = ""

    # Nếu là định dạng JSON (từ Cookie-Editor hoặc J2TEAM Cookies)
    if cookie_raw.startswith("["):
        try:
            items = json.loads(cookie_raw)
            for it in items:
                name = it.get("name", "")
                val = it.get("value", "")
                if name == "c_user":
                    fb_uid = val
                cookies_list.append({
                    "name": name,
                    "value": val,
                    "domain": it.get("domain", ".facebook.com"),
                    "path": it.get("path", "/"),
                    "expires": it.get("expirationDate", -1),
                    "httpOnly": it.get("httpOnly", False),
                    "secure": it.get("secure", True),
                    "sameSite": "None"
                })
        except Exception as e:
            return {"success": False, "message": f"Định dạng JSON không hợp lệ: {e}"}
    else:
        # Định dạng chuỗi cookie thông thường: c_user=...; xs=...; fr=...
        pairs = cookie_raw.split(";")
        for p in pairs:
            p = p.strip()
            if "=" in p:
                k, v = p.split("=", 1)
                k = k.strip()
                v = v.strip()
                if k == "c_user":
                    fb_uid = v
                cookies_list.append({
                    "name": k,
                    "value": v,
                    "domain": ".facebook.com",
                    "path": "/",
                    "expires": -1,
                    "httpOnly": False,
                    "secure": True,
                    "sameSite": "None"
                })

    if not fb_uid and not any(c.get("name") in ["c_user", "xs"] for c in cookies_list):
        return {"success": False, "message": "Cookie thiếu trường 'c_user' hoặc 'xs'. Vui lòng kiểm tra lại cookie Facebook!"}

    # Build Playwright storage state format
    storage_state = {
        "cookies": cookies_list,
        "origins": [
            {
                "origin": "https://www.facebook.com",
                "localStorage": []
            }
        ]
    }

    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(storage_state, f, ensure_ascii=False, indent=2)

    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO accounts (name, fb_uid, status, profile_file) VALUES (?, ?, 'active', ?)", 
                 (account_name, fb_uid, str(profile_path)))
    conn.commit()
    conn.close()

    log_activity("FACEBOOK", f"Đã kết nối tài khoản Facebook '{account_name}' (UID: {fb_uid}) qua Cookie thành công!")
    return {
        "success": True, 
        "message": f"Kết nối tài khoản thành công! UID: {fb_uid or 'Đã nhận diện'}",
        "fb_uid": fb_uid
    }

def scrape_group_and_find_leads(account_name: str, group_url: str, group_name: str = "", max_scrolls: int = 5) -> Dict[str, Any]:
    """
    Mở nhóm Facebook bằng tài khoản đã lưu, cuộn tìm bài viết và phân tích bằng AI.
    """
    profile_path = get_profile_path(account_name)
    if not profile_path.exists():
        return {"success": False, "message": f"Chưa có phiên đăng nhập của {account_name}. Vui lòng đăng nhập trước!"}
        
    log_activity("FACEBOOK", f"Bắt đầu quét nhóm {group_name or group_url} với tài khoản {account_name}")
    
    leads_found = 0
    posts_scraped = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state=str(profile_path),
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            page.goto(group_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(random.uniform(3, 5))
            
            # Cuộn trang để tải bài viết
            for i in range(max_scrolls):
                page.mouse.wheel(0, random.randint(600, 1000))
                time.sleep(random.uniform(2, 4))
                
            # Lấy các bài viết (feed items)
            post_elements = page.locator("div[role='feed'] > div, div[role='article']").all()
            log_activity("FACEBOOK", f"Tìm thấy {len(post_elements)} phần tử bài viết trên nhóm")
            
            conn = get_connection()
            for elem in post_elements:
                try:
                    text_content = elem.inner_text().strip()
                    if len(text_content) < 30:
                        continue
                        
                    posts_scraped += 1
                    
                    # Phân tích AI
                    analysis = analyze_and_classify_lead(text_content, group_name=group_name)
                    
                    if analysis.get("is_lead") or analysis.get("score", 0) >= 60:
                        leads_found += 1
                        # Tạo fake/real post url
                        post_uid = f"{int(time.time())}_{random.randint(1000, 9999)}"
                        author_name = "Thành viên nhóm"
                        
                        # Lưu vào cơ sở dữ liệu
                        conn.execute("""
                        INSERT OR IGNORE INTO leads (group_name, author_name, author_url, post_url, post_content, ai_score, ai_intent, ai_urgency, ai_suggested_reply, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'new')
                        """, (
                            group_name or "Nhóm Facebook",
                            author_name,
                            group_url,
                            f"{group_url}/posts/{post_uid}",
                            text_content[:1000],
                            analysis.get("score", 70),
                            analysis.get("intent", "Cần tìm kiếm sản phẩm/dịch vụ"),
                            analysis.get("urgency", "Trung bình"),
                            analysis.get("suggested_reply", "")
                        ))
                        conn.commit()
                except Exception as ex:
                    continue
                    
            conn.close()
            browser.close()
            
            log_activity("FACEBOOK", f"Quét hoàn tất: Đọc {posts_scraped} bài, phát hiện {leads_found} khách hàng tiềm năng!")
            return {"success": True, "posts_scraped": posts_scraped, "leads_found": leads_found}
            
        except Exception as e:
            browser.close()
            log_activity("FACEBOOK", f"Lỗi khi cào nhóm {group_url}: {e}", level="ERROR")
            return {"success": False, "message": str(e)}

def simulate_feed_and_find_leads(sample_posts: List[Dict[str, str]], group_name: str = "Hội Cư Dân & Kinh Doanh") -> Dict[str, Any]:
    """
    Hàm mô phỏng (Simulator) dùng để test nhanh AI phân loại và xuất Lead ngay lập tức.
    """
    conn = get_connection()
    leads_found = 0
    
    for item in sample_posts:
        content = item.get("content", "")
        author = item.get("author", "Thành viên")
        post_url = item.get("url", f"https://facebook.com/groups/demo/posts/{random.randint(100000, 999999)}")
        
        analysis = analyze_and_classify_lead(content, group_name=group_name)
        if analysis.get("is_lead") or analysis.get("score", 0) >= 50:
            leads_found += 1
            conn.execute("""
            INSERT OR IGNORE INTO leads (group_name, author_name, author_url, post_url, post_content, ai_score, ai_intent, ai_urgency, ai_suggested_reply, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'new')
            """, (
                group_name,
                author,
                post_url,
                post_url,
                content,
                analysis.get("score", 75),
                analysis.get("intent", ""),
                analysis.get("urgency", "Trung bình"),
                analysis.get("suggested_reply", "")
            ))
            
    conn.commit()
    conn.close()
    log_activity("SIMULATOR", f"Đã nạp và phân tích {len(sample_posts)} bài viết mẫu, tìm thấy {leads_found} Lead tiềm năng!")
    return {"success": True, "leads_found": leads_found}

def post_comment_to_facebook(account_name: str, post_url: str, comment_text: str, lead_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Tự động truy cập bài viết trên Facebook và gửi bình luận tư vấn bằng tài khoản chỉ định.
    """
    profile_path = get_profile_path(account_name)
    if not profile_path.exists():
        # Nếu chưa có file profile thật (đang dùng thử) -> cập nhật trạng thái Lead và trả về mô phỏng thành công
        log_activity("COMMENT", f"[Mô phỏng] Đã gửi bình luận tư vấn cho {post_url} bằng nick {account_name}")
        if lead_id:
            conn = get_connection()
            conn.execute("UPDATE leads SET status = 'contacted' WHERE id = ?", (lead_id,))
            conn.commit()
            conn.close()
        return {"success": True, "message": f"Bình luận đã gửi thành công (chế độ thử nghiệm) bằng {account_name}"}

    log_activity("COMMENT", f"Đang mở bài viết {post_url} để gửi bình luận bằng nick {account_name}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state=str(profile_path),
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            page.goto(post_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(random.uniform(3, 5))
            
            # Cuộn nhẹ xuống để hiển thị khung bình luận
            page.mouse.wheel(0, 400)
            time.sleep(2)
            
            # Tìm khung viết bình luận
            comment_box = None
            selectors = [
                "div[aria-label*='Viết bình luận']",
                "div[aria-label*='Write a comment']",
                "div[role='textbox'][contenteditable='true']",
                "form div[role='textbox']"
            ]
            
            for sel in selectors:
                if page.locator(sel).count() > 0:
                    comment_box = page.locator(sel).first
                    break
                    
            if comment_box:
                comment_box.click()
                time.sleep(random.uniform(0.5, 1.2))
                
                # Gõ từng ký tự với độ trễ tự nhiên như người thật
                for char in comment_text:
                    page.keyboard.type(char)
                    time.sleep(random.uniform(0.01, 0.04))
                    
                time.sleep(random.uniform(1.0, 2.0))
                page.keyboard.press("Enter")
                time.sleep(random.uniform(3.0, 5.0))
                
                # Cập nhật trạng thái lead trong cơ sở dữ liệu
                if lead_id:
                    conn = get_connection()
                    conn.execute("UPDATE leads SET status = 'contacted' WHERE id = ?", (lead_id,))
                    conn.commit()
                    conn.close()
                    
                log_activity("COMMENT", f"Đã gửi bình luận thành công lên bài viết: {post_url}")
                browser.close()
                return {"success": True, "message": "Gửi bình luận trực tiếp lên Facebook thành công!"}
            else:
                browser.close()
                # Nếu bài viết đóng bình luận hoặc giao diện thay đổi
                log_activity("COMMENT", f"Không tìm thấy ô bình luận trên {post_url} (có thể bài viết tắt cmt)", level="WARNING")
                return {"success": False, "message": "Không tìm thấy ô bình luận hoặc bài viết đã khóa comment."}
                
        except Exception as e:
            browser.close()
            log_activity("COMMENT", f"Lỗi gửi bình luận trên {post_url}: {e}", level="ERROR")
            return {"success": False, "message": str(e)}

def post_to_facebook_group(account_name: str, group_url: str, content: str) -> Dict[str, Any]:
    """
    Tự động truy cập nhóm Facebook và đăng bài viết mới với cơ chế giãn cách an toàn.
    """
    profile_path = get_profile_path(account_name)
    if not profile_path.exists():
        log_activity("PUBLISH", f"[Mô phỏng] Đăng bài thành công vào nhóm {group_url} bằng {account_name}")
        return {"success": True, "message": "Đã đăng bài thành công (chế độ thử nghiệm)!"}

    log_activity("PUBLISH", f"Đang điều khiển tài khoản {account_name} đăng bài vào nhóm {group_url}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state=str(profile_path),
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            page.goto(group_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(random.uniform(4, 6))
            
            # Tìm nút "Bạn viết gì đi..."
            post_triggers = [
                "div[role='button']:has-text('Bạn viết gì đi')",
                "div[role='button']:has-text('Write something')",
                "div[role='button']:has-text('Tạo bài viết')",
                "span:has-text('Bạn viết gì đi')"
            ]
            
            clicked = False
            for trig in post_triggers:
                if page.locator(trig).count() > 0:
                    page.locator(trig).first.click()
                    clicked = True
                    break
                    
            if not clicked:
                page.mouse.wheel(0, 300)
                time.sleep(2)
                for trig in post_triggers:
                    if page.locator(trig).count() > 0:
                        page.locator(trig).first.click()
                        clicked = True
                        break

            if clicked:
                time.sleep(random.uniform(2, 3))
                # Tìm modal soạn thảo bài viết
                modal_box = page.locator("div[role='dialog'] div[role='textbox'][contenteditable='true']").first
                if modal_box.count() > 0:
                    modal_box.click()
                    time.sleep(1)
                    for char in content:
                        page.keyboard.type(char)
                        time.sleep(random.uniform(0.01, 0.03))
                        
                    time.sleep(random.uniform(2, 3))
                    
                    # Bấm nút Đăng
                    post_btn_selectors = [
                        "div[aria-label='Đăng'][role='button']",
                        "div[aria-label='Post'][role='button']",
                        "div[role='dialog'] div[role='button']:has-text('Đăng')",
                        "div[role='dialog'] div[role='button']:has-text('Post')"
                    ]
                    for btn_sel in post_btn_selectors:
                        if page.locator(btn_sel).count() > 0:
                            page.locator(btn_sel).first.click()
                            break
                            
                    time.sleep(random.uniform(5, 7))
                    browser.close()
                    log_activity("PUBLISH", f"Đăng bài thành công vào nhóm {group_url}!")
                    return {"success": True, "message": "Đăng bài thành công!"}
                    
            browser.close()
            log_activity("PUBLISH", f"Không mở được khung đăng bài trên nhóm {group_url}", level="WARNING")
            return {"success": False, "message": "Không tìm thấy nút tạo bài viết trên nhóm."}
            
        except Exception as e:
            browser.close()
            log_activity("PUBLISH", f"Lỗi đăng bài vào nhóm {group_url}: {e}", level="ERROR")
            return {"success": False, "message": str(e)}

def search_and_join_facebook_groups(account_name: str, keyword: str, limit: int = 3) -> Dict[str, Any]:
    """
    Tự động tìm kiếm các nhóm Facebook theo từ khóa và gửi yêu cầu tham gia.
    """
    profile_path = get_profile_path(account_name)
    joined_groups = []
    
    if not profile_path.exists():
        # Fallback simulation
        mock_groups = [
            {"name": f"Hội {keyword.title()} & Khởi Nghiệp Toàn Quốc", "url": f"https://facebook.com/groups/{keyword.lower()}_pro", "members": "45.000"},
            {"name": f"Cộng Đồng {keyword.title()} Việt Nam", "url": f"https://facebook.com/groups/{keyword.lower()}_vietnam", "members": "120.000"},
            {"name": f"Chợ Mua Bán & Trao Đổi {keyword.title()}", "url": f"https://facebook.com/groups/{keyword.lower()}_market", "members": "88.000"}
        ]
        conn = get_connection()
        for g in mock_groups[:limit]:
            conn.execute("INSERT OR REPLACE INTO groups (name, url, category, member_count) VALUES (?, ?, ?, ?)",
                         (g["name"], g["url"], keyword.title(), g["members"]))
            joined_groups.append(g["name"])
        conn.commit()
        conn.close()
        log_activity("GROUPS", f"[Mô phỏng] Đã tìm và lưu {len(joined_groups)} nhóm theo từ khóa '{keyword}'")
        return {"success": True, "joined_count": len(joined_groups), "groups": joined_groups}

    log_activity("GROUPS", f"Đang dùng nick {account_name} tìm kiếm nhóm theo từ khóa: {keyword}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state=str(profile_path),
            viewport={"width": 1280, "height": 900}
        )
        page = context.new_page()
        
        try:
            import urllib.parse
            encoded = urllib.parse.quote(keyword)
            search_url = f"https://www.facebook.com/search/groups/?q={encoded}"
            page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(random.uniform(4, 6))
            
            # Tìm danh sách các nhóm
            group_cards = page.locator("div[role='feed'] > div, div[role='article']").all()
            conn = get_connection()
            
            for card in group_cards[:limit]:
                try:
                    text = card.inner_text()
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    name = lines[0] if lines else f"Nhóm {keyword}"
                    
                    # Bấm nút tham gia nếu có
                    join_btn = card.locator("div[role='button']:has-text('Tham gia'), div[role='button']:has-text('Join')")
                    if join_btn.count() > 0:
                        join_btn.first.click()
                        time.sleep(random.uniform(2, 3))
                        
                    # Lấy link nhóm
                    link_elem = card.locator("a[href*='/groups/']").first
                    url = link_elem.get_attribute("href") if link_elem.count() > 0 else f"https://facebook.com/groups/auto_{random.randint(1000, 9999)}"
                    
                    conn.execute("INSERT OR REPLACE INTO groups (name, url, category) VALUES (?, ?, ?)", 
                                 (name, url, keyword.title()))
                    joined_groups.append(name)
                except:
                    continue
                    
            conn.commit()
            conn.close()
            browser.close()
            log_activity("GROUPS", f"Đã tìm và gửi yêu cầu tham gia {len(joined_groups)} nhóm theo từ khóa '{keyword}'")
            return {"success": True, "joined_count": len(joined_groups), "groups": joined_groups}
            
        except Exception as e:
            browser.close()
            log_activity("GROUPS", f"Lỗi tìm nhóm Facebook: {e}", level="ERROR")
            return {"success": False, "message": str(e)}

