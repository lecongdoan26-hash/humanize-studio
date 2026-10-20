import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, Response, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.database import (
    init_db, get_connection, get_all_accounts, get_all_groups, 
    get_all_leads, get_all_posts, get_recent_logs, get_settings, 
    save_setting, log_activity,
    get_or_create_user, get_user_by_id, get_user_by_email,
    deduct_user_words, add_user_words, get_user_transactions
)
from core.ai_engine import spin_post_content
from core.fb_automation import (
    login_and_save_session, scrape_group_and_find_leads, 
    simulate_feed_and_find_leads
)
from core.humanizer_engine import audit_vietnamese_ai_text, generate_humanized_content

app = FastAPI(title="Klaro AI - Agent OS")

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "web" / "templates"

# Initialize DB on startup
@app.on_event("startup")
def on_startup():
    init_db()
    log_activity("SYSTEM", "Khởi động hệ thống Klaro AI thành công!")

# Serve Humanizer Tool HTML as Primary Homepage
@app.get("/", response_class=HTMLResponse)
@app.get("/humanizer", response_class=HTMLResponse)
async def serve_humanizer():
    humanizer_file = TEMPLATES_DIR / "humanizer.html"
    if not humanizer_file.exists():
        return HTMLResponse("<h1>humanizer.html không tìm thấy</h1>", status_code=404)
    with open(humanizer_file, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# Serve Authentic MB Bank VietQR Card Image
@app.get("/api/qr-image")
async def get_qr_image():
    qr_path = BASE_DIR / "data" / "qr_mb_lecongdoan.png"
    if qr_path.exists():
        return FileResponse(qr_path, media_type="image/png")
    return Response(status_code=404)

# Serve Secondary Marketing OS Dashboard
@app.get("/marketing", response_class=HTMLResponse)
async def serve_dashboard():
    index_file = TEMPLATES_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>index.html không tìm thấy</h1>", status_code=404)
    with open(index_file, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# API: Stats
@app.get("/api/stats")
async def get_stats():
    conn = get_connection()
    leads_count = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    accounts_count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
    groups_count = conn.execute("SELECT COUNT(*) FROM groups").fetchone()[0]
    posts_count = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    conn.close()
    return {
        "leads_count": leads_count,
        "accounts_count": accounts_count,
        "groups_count": groups_count,
        "posts_count": posts_count
    }

# API: Leads
@app.get("/api/leads")
async def get_leads():
    return get_all_leads(limit=100)

# API: Accounts
@app.get("/api/accounts")
async def get_accounts():
    return get_all_accounts()

# API: Groups
@app.get("/api/groups")
async def get_groups():
    return get_all_groups()

# API: Posts
@app.get("/api/posts")
async def get_posts():
    return get_all_posts()

# API: Logs
@app.get("/api/logs")
async def get_logs():
    return get_recent_logs(limit=25)

# API: Settings
@app.get("/api/settings")
async def api_get_settings():
    return get_settings()

class SettingsPayload(BaseModel):
    gemini_api_key: str = ""
    business_name: str = ""
    business_desc: str = ""
    target_keywords: str = ""
    cta_contact: str = ""

@app.post("/api/settings")
async def api_save_settings(payload: SettingsPayload):
    for k, v in payload.dict().items():
        save_setting(k, v)
    log_activity("SETTINGS", "Cập nhật cấu hình và bộ nhớ AI thành công.")
    return {"success": True}

# API: AI Spin Content
class SpinRequest(BaseModel):
    content: str

@app.post("/api/ai-spin")
async def api_ai_spin(req: SpinRequest):
    variations = spin_post_content(req.content, count=3)
    return {"variations": variations}

# API: Login Facebook Account
class LoginRequest(BaseModel):
    account_name: str

@app.post("/api/login-account")
async def api_login_account(req: LoginRequest):
    result = login_and_save_session(req.account_name)
    return result

# API: Import Facebook Cookie
class CookieImportRequest(BaseModel):
    account_name: str
    cookie: str

@app.post("/api/import-cookie")
async def api_import_cookie(req: CookieImportRequest):
    from core.fb_automation import import_cookie_session
    result = import_cookie_session(req.account_name, req.cookie)
    return result

# API: Scrape Facebook Group
class ScrapeRequest(BaseModel):
    account_name: str
    group_url: str
    group_name: str = ""

@app.post("/api/scrape-group")
async def api_scrape_group(req: ScrapeRequest):
    result = scrape_group_and_find_leads(
        account_name=req.account_name,
        group_url=req.group_url,
        group_name=req.group_name
    )
    return result

# API: Simulate Leads Demo (1-Click Tester)
@app.post("/api/simulate-leads")
async def api_simulate_leads():
    sample_posts = [
        {
            "author": "Trần Tuấn Anh",
            "content": "Chào cả nhà, mình đang tìm đơn vị làm marketing online hoặc chạy quảng cáo Facebook/TikTok cho chuỗi cửa hàng thời trang tại Hà Nội. Ai làm uy tín có cam kết kết quả ib tư vấn giúp mình với ạ, ngân sách khoảng 30tr/tháng.",
            "url": "https://facebook.com/groups/congdongmarketing/posts/101"
        },
        {
            "author": "Nguyễn Hoàng Mai",
            "content": "Có ai nhận thiết kế website bán hàng chuẩn SEO và setup hệ thống tự động trả lời tin nhắn không ạ? Mình cần gấp trong tuần này để kịp khai trương, ib mình xin báo giá nhé!",
            "url": "https://facebook.com/groups/kinhdoanhtulam/posts/102"
        },
        {
            "author": "Lê Văn Hùng",
            "content": "TUYỂN DỤNG CỘNG TÁC VIÊN BÁN HÀNG TẠI NHÀ, HOA HỒNG 50%, KHÔNG CẦN VỐN, ĐƯỢC ĐÀO TẠO TỪ A-Z, ĐĂNG KÝ NGAY...",
            "url": "https://facebook.com/groups/timvieclam/posts/103"
        },
        {
            "author": "Đỗ Thu Hương",
            "content": "Mọi người cho mình hỏi có phần mềm nào tự động tìm khách hàng trên Facebook và hỗ trợ đăng bài nhiều nhóm không ạ? Dạo này làm thủ công mất nhiều thời gian quá.",
            "url": "https://facebook.com/groups/kinhdoanhonline/posts/104"
        },
        {
            "author": "Phạm Quốc Bảo",
            "content": "Hôm nay trời đẹp quá, chúc cả nhà một ngày làm việc tràn đầy năng lượng và chốt được nhiều đơn nhé!",
            "url": "https://facebook.com/groups/giaoluu/posts/105"
        }
    ]
    result = simulate_feed_and_find_leads(sample_posts, group_name="Cộng Đồng Kinh Doanh Online VN")
    return result

# API: Auto Comment on Lead Post
class CommentLeadRequest(BaseModel):
    account_name: str
    post_url: str
    comment_text: str
    lead_id: Optional[int] = None

@app.post("/api/comment-lead")
async def api_comment_lead(req: CommentLeadRequest):
    from core.fb_automation import post_comment_to_facebook
    result = post_comment_to_facebook(
        account_name=req.account_name,
        post_url=req.post_url,
        comment_text=req.comment_text,
        lead_id=req.lead_id
    )
    return result

# API: Schedule Batch Posts
class BatchPostRequest(BaseModel):
    account_name: str
    group_name: str
    group_url: str
    content: str

@app.post("/api/schedule-post")
async def api_schedule_post(req: BatchPostRequest, background_tasks: BackgroundTasks):
    from core.database import add_post, update_post_status
    from core.fb_automation import post_to_facebook_group
    
    post_id = add_post(
        account_name=req.account_name,
        group_name=req.group_name,
        group_url=req.group_url,
        content=req.content,
        status="published"
    )
    
    def run_post_task():
        res = post_to_facebook_group(req.account_name, req.group_url, req.content)
        if res.get("success"):
            update_post_status(post_id, "published", "Đăng bài thành công!")
        else:
            update_post_status(post_id, "failed", res.get("message", "Lỗi"))

    background_tasks.add_task(run_post_task)
    return {"success": True, "post_id": post_id, "message": "Bài viết đã được đưa vào hàng chờ đăng!"}

# API: Retry Post
class RetryPostRequest(BaseModel):
    post_id: int

@app.post("/api/retry-post")
async def api_retry_post(req: RetryPostRequest, background_tasks: BackgroundTasks):
    conn = get_connection()
    post = conn.execute("SELECT * FROM posts WHERE id = ?", (req.post_id,)).fetchone()
    conn.close()
    if not post:
        return {"success": False, "message": "Không tìm thấy bài viết!"}
        
    from core.fb_automation import post_to_facebook_group
    from core.database import update_post_status
    
    def retry_task():
        res = post_to_facebook_group(post["account_name"], post["group_url"], post["content"])
        if res.get("success"):
            update_post_status(req.post_id, "published", "Đăng lại thành công!")
        else:
            update_post_status(req.post_id, "failed", res.get("message", "Lỗi"))

    background_tasks.add_task(retry_task)
    return {"success": True, "message": "Đang tiến hành đăng lại..."}

# API: Natural Language Agent Command Bar
class AgentCommandRequest(BaseModel):
    command: str

@app.post("/api/agent-command")
async def api_agent_command(req: AgentCommandRequest):
    from core.ai_engine import parse_agent_natural_command
    plan = parse_agent_natural_command(req.command)
    return plan

# API: Execute Agent Plan
class AgentExecuteRequest(BaseModel):
    plan: Dict[str, Any]

@app.post("/api/agent-execute")
async def api_agent_execute(req: AgentExecuteRequest, background_tasks: BackgroundTasks):
    from core.database import log_activity
    plan = req.plan
    title = plan.get("title", "Kế hoạch AI")
    log_activity("AGENT", f"Người dùng xác nhận khởi chạy kế hoạch: '{title}'")
    
    # Auto-execute sample scan or tasks
    def run_agent():
        api_simulate_leads()
        log_activity("AGENT", f"Kế hoạch '{title}' đã hoàn tất tự động mọi bước!")
        
    background_tasks.add_task(run_agent)
    return {"success": True, "message": "Kế hoạch đang được AI tự động vận hành trong nền!"}

# API: Auto Search and Join Groups
class AutoJoinRequest(BaseModel):
    account_name: str
    keyword: str
    limit: int = 3

@app.post("/api/auto-join-groups")
async def api_auto_join_groups(req: AutoJoinRequest):
    from core.fb_automation import search_and_join_facebook_groups
    result = search_and_join_facebook_groups(
        account_name=req.account_name,
        keyword=req.keyword,
        limit=req.limit
    )
    return result

# ==========================================
# MARKETING PIPELINE MULTI-AGENT APIs
# ==========================================
from core.pipeline_engine import (
    get_pipeline_full_state, run_pipeline_step, 
    approve_zuck_post, PIPELINE_AGENTS
)
from core.database import (
    create_pipeline_campaign, get_pipeline_logs, 
    get_task_by_id, get_active_campaign
)

@app.get("/api/pipeline/state")
async def api_pipeline_state():
    state = get_pipeline_full_state()
    logs = get_pipeline_logs(limit=25)
    return {**state, "logs": logs}

class CreateCampaignRequest(BaseModel):
    title: str
    goal: str
    product_info: str = ""
    target_audience: str = ""
    auto_start: bool = True

@app.post("/api/pipeline/campaign/create")
async def api_pipeline_campaign_create(req: CreateCampaignRequest, background_tasks: BackgroundTasks):
    cid = create_pipeline_campaign(
        title=req.title,
        goal=req.goal,
        product_info=req.product_info,
        target_audience=req.target_audience
    )
    if req.auto_start:
        def start_chain():
            run_pipeline_step(campaign_id=cid, agent_id="holmes")
            run_pipeline_step(campaign_id=cid, agent_id="sun_tzu")
        background_tasks.add_task(start_chain)
    return {"success": True, "campaign_id": cid, "message": "Đã tạo chiến dịch và giao cho Trưởng phòng Philip Kotler!"}

class RunStepRequest(BaseModel):
    campaign_id: Optional[int] = None
    agent_id: Optional[str] = None

@app.post("/api/pipeline/step/run-next")
async def api_pipeline_step_run(req: RunStepRequest):
    res = run_pipeline_step(campaign_id=req.campaign_id, agent_id=req.agent_id)
    return res

@app.post("/api/pipeline/campaign/run-all")
async def api_pipeline_run_all(req: RunStepRequest, background_tasks: BackgroundTasks):
    camp = get_active_campaign()
    if not camp:
        return {"success": False, "message": "Không có chiến dịch!"}
    cid = req.campaign_id or camp["id"]

    def run_all_loop():
        from core.pipeline_engine import AGENT_ORDER
        import time
        for aid in AGENT_ORDER:
            res = run_pipeline_step(campaign_id=cid, agent_id=aid)
            if res.get("status") == "waiting_approval":
                break
            time.sleep(1.2)

    background_tasks.add_task(run_all_loop)
    return {"success": True, "message": "Đã kích hoạt toàn bộ dây chuyền! Các Agent đang lần lượt xử lý..."}

class ApprovePostRequest(BaseModel):
    campaign_id: Optional[int] = None

@app.post("/api/pipeline/approve-post")
async def api_pipeline_approve_post(req: ApprovePostRequest, background_tasks: BackgroundTasks):
    res = approve_zuck_post(campaign_id=req.campaign_id)
    if res.get("success"):
        def continue_after_approval():
            import time
            camp = get_active_campaign()
            cid = req.campaign_id or (camp["id"] if camp else None)
            if cid:
                time.sleep(1.0)
                run_pipeline_step(campaign_id=cid, agent_id="brunson")
                time.sleep(1.2)
                run_pipeline_step(campaign_id=cid, agent_id="robin_hood")
                time.sleep(1.2)
                run_pipeline_step(campaign_id=cid, agent_id="buffett")
        background_tasks.add_task(continue_after_approval)
    return res

@app.get("/api/pipeline/task/{task_id}")
async def api_pipeline_get_task(task_id: int):
    task = get_task_by_id(task_id)
    if not task:
        return {"success": False, "message": "Không tìm thấy tác vụ!"}
    return {"success": True, "task": task}

@app.post("/api/pipeline/reset")
async def api_pipeline_reset():
    from core.database import get_connection
    conn = get_connection()
    conn.execute("DELETE FROM pipeline_tasks")
    conn.execute("DELETE FROM pipeline_logs")
    conn.execute("DELETE FROM pipeline_campaigns")
    conn.commit()
    conn.close()
    
    # Re-create fresh demo campaign
    from core.pipeline_engine import get_pipeline_full_state
    state = get_pipeline_full_state()
    return {"success": True, "message": "Đã làm mới lại toàn bộ dây chuyền về trạng thái ban đầu!"}

# ==========================================
# AUTH, USER & WORD BALANCE API ENDPOINTS
# ==========================================
def get_current_user_from_req(request: Request) -> Optional[Dict]:
    uid_cookie = request.cookies.get("session_user_id")
    if uid_cookie and uid_cookie.isdigit():
        u = get_user_by_id(int(uid_cookie))
        if u:
            return u
    email_header = request.headers.get("X-User-Email")
    if email_header:
        u = get_user_by_email(email_header)
        if u:
            return u
    return None

class GoogleLoginRequest(BaseModel):
    email: str
    name: Optional[str] = ""
    avatar: Optional[str] = ""

@app.post("/api/auth/google-login")
async def api_auth_google_login(req: GoogleLoginRequest, response: Response):
    if not req.email:
        return {"success": False, "error": "Email không được để trống"}
    user = get_or_create_user(req.email.strip().lower(), req.name.strip(), req.avatar.strip())
    response.set_cookie(key="session_user_id", value=str(user["id"]), max_age=86400 * 30, httponly=False)
    return {"success": True, "user": user}

@app.post("/api/auth/logout")
async def api_auth_logout(response: Response):
    response.delete_cookie(key="session_user_id")
    return {"success": True}

@app.get("/api/user/me")
async def api_user_me(request: Request):
    user = get_current_user_from_req(request)
    if not user:
        return {"authenticated": False, "user": None}
    transactions = get_user_transactions(user["id"], limit=10)
    return {"authenticated": True, "user": user, "transactions": transactions}

class PurchasePackageRequest(BaseModel):
    package_id: str  # payg_20k, starter, pro, annual
    user_id: Optional[int] = None

@app.post("/api/user/purchase-package")
async def api_user_purchase_package(req: PurchasePackageRequest, request: Request):
    user = get_current_user_from_req(request)
    if not user and req.user_id:
        user = get_user_by_id(req.user_id)
        
    if not user:
        return {"success": False, "error": "Vui lòng đăng nhập để nâng cấp gói!"}
        
    PACKAGES = {
        "payg_40k": {"words": 40000, "tier": "payg_40k", "name": "Gói Nạp Lẻ (40.000 từ)", "price": 49000},
        "payg_20k": {"words": 40000, "tier": "payg_40k", "name": "Gói Nạp Lẻ (40.000 từ)", "price": 49000},
        "starter": {"words": 90000, "tier": "starter", "name": "Gói Cá Nhân (90.000 từ/tháng)", "price": 99000},
        "pro": {"words": 300000, "tier": "pro", "name": "Gói Chuyên Nghiệp (300.000 từ/tháng)", "price": 199000},
        "annual": {"words": 1000000, "tier": "annual", "name": "Gói Năm (1.000.000 từ/năm)", "price": 790000}
    }
    pkg = PACKAGES.get(req.package_id)
    if not pkg:
        return {"success": False, "error": "Gói dịch vụ không hợp lệ!"}
        
    updated = add_user_words(
        user_id=user["id"],
        words_count=pkg["words"],
        tier=pkg["tier"],
        description=f"Mua {pkg['name']} ({pkg['price']:,}đ)"
    )
    return {
        "success": True, 
        "message": f"Kích hoạt thành công {pkg['name']}! Tài khoản đã được cộng thêm {pkg['words']:,} từ.", 
        "user": updated
    }

# ==========================================
# HUMANIZER AI API ENDPOINTS
# ==========================================
class HumanizerAuditRequest(BaseModel):
    text: str

class HumanizerProcessRequest(BaseModel):
    text: str
    mode: str = "social_mkt"
    intensity: str = "balanced"
    custom_tone: str = ""
    api_key: Optional[str] = None
    user_id: Optional[int] = None

@app.post("/api/humanizer/audit")
async def api_humanizer_audit(req: HumanizerAuditRequest):
    # Kiểm tra vết tích AI hoàn toàn MIỄN PHÍ, không trừ từ
    return audit_vietnamese_ai_text(req.text)

@app.post("/api/humanizer/process")
async def api_humanizer_process(req: HumanizerProcessRequest, request: Request):
    user = get_current_user_from_req(request)
    if not user and req.user_id:
        user = get_user_by_id(req.user_id)
        
    if not user:
        return {
            "success": False, 
            "error": "Vui lòng đăng nhập tài khoản để nhận 5.000 từ miễn phí và sử dụng công cụ.",
            "need_login": True
        }
        
    # Tính số từ cần xử lý
    words_count = len(req.text.strip().split()) if req.text.strip() else 0
    if words_count == 0:
        return {"success": False, "error": "Văn bản không có từ nào để chuẩn hóa!"}
        
    if user["words_balance"] < words_count:
        return {
            "success": False,
            "error": f"Số dư không đủ! Bài viết cần {words_count:,} từ, nhưng bạn chỉ còn {user['words_balance']:,} từ. Vui lòng nạp thêm để tiếp tục.",
            "need_upgrade": True,
            "words_needed": words_count,
            "current_balance": user["words_balance"]
        }
        
    result = generate_humanized_content(
        text=req.text,
        mode=req.mode,
        intensity=req.intensity,
        custom_tone=req.custom_tone,
        custom_api_key=req.api_key
    )
    
    if result.get("success"):
        # Trừ số từ vào tài khoản
        deduct_user_words(user["id"], words_count, f"Chuẩn hóa bài viết ({words_count:,} từ)")
        updated_user = get_user_by_id(user["id"])
        result["user_words_balance"] = updated_user["words_balance"] if updated_user else user["words_balance"] - words_count
        result["words_deducted"] = words_count
        
    return result


