import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from core.config import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Accounts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        fb_uid TEXT,
        status TEXT DEFAULT 'idle', -- active, idle, checkpoint, error
        profile_file TEXT,
        proxy TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 2. Groups Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        url TEXT UNIQUE NOT NULL,
        category TEXT DEFAULT 'Chung',
        member_count TEXT DEFAULT '',
        is_joined INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 3. Leads Table (Khách hàng tiềm năng)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_name TEXT,
        author_name TEXT,
        author_url TEXT,
        post_url TEXT UNIQUE,
        post_content TEXT,
        ai_score INTEGER DEFAULT 0, -- 0 to 100
        ai_intent TEXT,             -- Tóm tắt nhu cầu
        ai_urgency TEXT,            -- Thấp / Trung bình / Cao
        ai_suggested_reply TEXT,    -- Câu trả lời AI gợi ý
        status TEXT DEFAULT 'new',  -- new, contacted, ignored
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 4. Posts Table (Bài đăng)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_name TEXT,
        group_name TEXT,
        group_url TEXT,
        content TEXT NOT NULL,
        status TEXT DEFAULT 'draft', -- draft, scheduled, published, failed
        scheduled_time DATETIME,
        published_time DATETIME,
        log TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Auto-migration for existing DBs
    try:
        cursor.execute("ALTER TABLE posts ADD COLUMN group_url TEXT")
    except:
        pass
    
    # 5. Content Library (Thư viện nội dung bài đăng)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS content_library (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        tags TEXT DEFAULT '',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 6. Settings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    
    # 7. Activity Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        level TEXT DEFAULT 'INFO',
        module TEXT,
        message TEXT
    )
    """)
    
    # 8. Marketing Pipeline Campaigns
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pipeline_campaigns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        goal TEXT,
        product_info TEXT,
        target_audience TEXT,
        status TEXT DEFAULT 'running', -- idle, running, waiting_approval, completed
        current_agent_id TEXT DEFAULT 'holmes',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 9. Pipeline Agent Tasks
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pipeline_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id INTEGER NOT NULL,
        agent_id TEXT NOT NULL,
        agent_name TEXT NOT NULL,
        agent_role TEXT NOT NULL,
        status TEXT DEFAULT 'pending', -- pending, running, waiting_approval, completed, failed
        input_data TEXT,
        output_data TEXT,
        summary TEXT,
        started_at DATETIME,
        completed_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 10. Pipeline Handover Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pipeline_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id INTEGER,
        from_agent TEXT,
        to_agent TEXT,
        action TEXT NOT NULL,
        details TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 11. Users Table (Quản lý người dùng & Số dư từ)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT,
        avatar TEXT,
        words_balance INTEGER DEFAULT 5000,
        words_used INTEGER DEFAULT 0,
        tier TEXT DEFAULT 'free', -- free, payg_40k, starter, pro, annual
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 12. Word Transactions Table (Lịch sử biến động số từ)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS word_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount INTEGER NOT NULL, -- Số từ cộng (+) hoặc trừ (-)
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Insert default settings if not exists
    default_settings = [
        ("business_name", "Dịch vụ của tôi"),
        ("business_desc", "Cung cấp giải pháp bán hàng và marketing tự động hóa toàn diện."),
        ("target_keywords", "cần tìm, cần mua, giá bao nhiêu, ai bán, cần thuê, tư vấn giúp, ib mình"),
        ("ai_tone", "Chuyên nghiệp, thân thiện, súc tích và khéo léo"),
        ("cta_contact", "Nhắn tin qua Facebook hoặc liên hệ Zalo: 098xxxxxxx để nhận tư vấn chi tiết ạ!")
    ]
    for key, val in default_settings:
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))
        
    conn.commit()
    conn.close()

def log_activity(module: str, message: str, level: str = "INFO"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO activity_logs (module, message, level) VALUES (?, ?, ?)", (module, message, level))
    conn.commit()
    conn.close()

# Helper queries
def get_all_accounts() -> List[Dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM accounts ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_groups() -> List[Dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM groups ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_group(name: str, url: str, category: str = "Chung", member_count: str = "") -> bool:
    conn = get_connection()
    try:
        conn.execute("INSERT OR REPLACE INTO groups (name, url, category, member_count) VALUES (?, ?, ?, ?)",
                     (name, url, category, member_count))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def get_all_leads(limit: int = 100) -> List[Dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM leads ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_lead_status(lead_id: int, status: str):
    conn = get_connection()
    conn.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))
    conn.commit()
    conn.close()

def get_all_posts() -> List[Dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_post(account_name: str, group_name: str, group_url: str, content: str, status: str = "scheduled") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO posts (account_name, group_name, group_url, content, status, scheduled_time)
    VALUES (?, ?, ?, ?, ?, datetime('now'))
    """, (account_name, group_name, group_url, content, status))
    post_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return post_id

def update_post_status(post_id: int, status: str, log: str = ""):
    conn = get_connection()
    conn.execute("""
    UPDATE posts 
    SET status = ?, log = ?, published_time = CASE WHEN ? = 'published' THEN datetime('now') ELSE published_time END
    WHERE id = ?
    """, (status, log, status, post_id))
    conn.commit()
    conn.close()

def get_recent_logs(limit: int = 30) -> List[Dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_settings() -> Dict[str, str]:
    conn = get_connection()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}

def save_setting(key: str, value: str):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

# --- MARKETING PIPELINE HELPERS ---

def create_pipeline_campaign(title: str, goal: str, product_info: str = "", target_audience: str = "") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO pipeline_campaigns (title, goal, product_info, target_audience, status, current_agent_id)
    VALUES (?, ?, ?, ?, 'running', 'holmes')
    """, (title, goal, product_info, target_audience))
    campaign_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return campaign_id

def get_active_campaign() -> Optional[Dict]:
    conn = get_connection()
    row = conn.execute("""
    SELECT * FROM pipeline_campaigns 
    WHERE status IN ('running', 'waiting_approval') 
    ORDER BY id DESC LIMIT 1
    """).fetchone()
    if not row:
        # Fallback to the latest campaign if any
        row = conn.execute("SELECT * FROM pipeline_campaigns ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_campaigns() -> List[Dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM pipeline_campaigns ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_campaign_status(campaign_id: int, status: str, current_agent_id: str = None):
    conn = get_connection()
    if current_agent_id:
        conn.execute("""
        UPDATE pipeline_campaigns 
        SET status = ?, current_agent_id = ?, updated_at = datetime('now')
        WHERE id = ?
        """, (status, current_agent_id, campaign_id))
    else:
        conn.execute("""
        UPDATE pipeline_campaigns 
        SET status = ?, updated_at = datetime('now')
        WHERE id = ?
        """, (status, campaign_id))
    conn.commit()
    conn.close()

def create_pipeline_task(campaign_id: int, agent_id: str, agent_name: str, agent_role: str, input_data: Any, status: str = "pending") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    input_str = json.dumps(input_data, ensure_ascii=False) if not isinstance(input_data, str) else input_data
    cursor.execute("""
    INSERT INTO pipeline_tasks (campaign_id, agent_id, agent_name, agent_role, status, input_data, started_at)
    VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
    """, (campaign_id, agent_id, agent_name, agent_role, status, input_str))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id

def update_pipeline_task(task_id: int, status: str, output_data: Any = None, summary: str = ""):
    conn = get_connection()
    output_str = json.dumps(output_data, ensure_ascii=False) if (output_data is not None and not isinstance(output_data, str)) else output_data
    if status == "completed":
        conn.execute("""
        UPDATE pipeline_tasks
        SET status = ?, output_data = COALESCE(?, output_data), summary = COALESCE(?, summary), completed_at = datetime('now')
        WHERE id = ?
        """, (status, output_str, summary, task_id))
    else:
        conn.execute("""
        UPDATE pipeline_tasks
        SET status = ?, output_data = COALESCE(?, output_data), summary = COALESCE(?, summary)
        WHERE id = ?
        """, (status, output_str, summary, task_id))
    conn.commit()
    conn.close()

def get_campaign_tasks(campaign_id: int) -> List[Dict]:
    conn = get_connection()
    rows = conn.execute("""
    SELECT * FROM pipeline_tasks WHERE campaign_id = ? ORDER BY id ASC
    """, (campaign_id,)).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["input_data"] = json.loads(d["input_data"]) if d["input_data"] else {}
        except:
            pass
        try:
            d["output_data"] = json.loads(d["output_data"]) if d["output_data"] else {}
        except:
            pass
        result.append(d)
    return result

def get_task_by_id(task_id: int) -> Optional[Dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM pipeline_tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    try:
        d["input_data"] = json.loads(d["input_data"]) if d["input_data"] else {}
    except:
        pass
    try:
        d["output_data"] = json.loads(d["output_data"]) if d["output_data"] else {}
    except:
        pass
    return d

def log_pipeline_action(campaign_id: int, from_agent: str, to_agent: str, action: str, details: str = ""):
    conn = get_connection()
    conn.execute("""
    INSERT INTO pipeline_logs (campaign_id, from_agent, to_agent, action, details)
    VALUES (?, ?, ?, ?, ?)
    """, (campaign_id, from_agent, to_agent, action, details))
    conn.commit()
    conn.close()

def get_pipeline_logs(campaign_id: Optional[int] = None, limit: int = 50) -> List[Dict]:
    conn = get_connection()
    if campaign_id:
        rows = conn.execute("""
        SELECT * FROM pipeline_logs WHERE campaign_id = ? ORDER BY id DESC LIMIT ?
        """, (campaign_id, limit)).fetchall()
    else:
        rows = conn.execute("""
        SELECT * FROM pipeline_logs ORDER BY id DESC LIMIT ?
        """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ==========================================
# USER & WORD BALANCE FUNCTIONS
# ==========================================
def get_or_create_user(email: str, name: str = "", avatar: str = "") -> Dict:
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if user:
        conn.close()
        return dict(user)
    
    # New user: bonus 5000 words!
    cursor = conn.cursor()
    display_name = name or email.split("@")[0]
    cursor.execute("""
    INSERT INTO users (email, name, avatar, words_balance, words_used, tier)
    VALUES (?, ?, ?, 5000, 0, 'free')
    """, (email, display_name, avatar))
    user_id = cursor.lastrowid

    # Log bonus transaction
    cursor.execute("""
    INSERT INTO word_transactions (user_id, amount, description)
    VALUES (?, 5000, 'Tặng quà chào mừng thành viên mới (+5.000 từ)')
    """, (user_id,))
    conn.commit()
    new_user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(new_user)

def get_user_by_id(user_id: int) -> Optional[Dict]:
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_email(email: str) -> Optional[Dict]:
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return dict(user) if user else None

def deduct_user_words(user_id: int, words_count: int, description: str = "") -> bool:
    conn = get_connection()
    user = conn.execute("SELECT words_balance, words_used FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return False
    
    current_balance = user["words_balance"]
    if current_balance < words_count:
        conn.close()
        return False
    
    new_balance = current_balance - words_count
    new_used = user["words_used"] + words_count
    
    conn.execute("""
    UPDATE users SET words_balance = ?, words_used = ? WHERE id = ?
    """, (new_balance, new_used, user_id))
    
    conn.execute("""
    INSERT INTO word_transactions (user_id, amount, description)
    VALUES (?, ?, ?)
    """, (user_id, -words_count, description or f"Chuẩn hóa nội dung ({words_count} từ)"))
    
    conn.commit()
    conn.close()
    return True

def add_user_words(user_id: int, words_count: int, tier: str = "", description: str = "") -> Optional[Dict]:
    conn = get_connection()
    user = conn.execute("SELECT words_balance FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return None
    
    new_balance = user["words_balance"] + words_count
    if tier:
        conn.execute("UPDATE users SET words_balance = ?, tier = ? WHERE id = ?", (new_balance, tier, user_id))
    else:
        conn.execute("UPDATE users SET words_balance = ? WHERE id = ?", (new_balance, user_id))
        
    conn.execute("""
    INSERT INTO word_transactions (user_id, amount, description)
    VALUES (?, ?, ?)
    """, (user_id, words_count, description or f"Nạp gói từ (+{words_count:,} từ)"))
    conn.commit()
    
    updated = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(updated) if updated else None

def get_user_transactions(user_id: int, limit: int = 15) -> List[Dict]:
    conn = get_connection()
    rows = conn.execute("""
    SELECT * FROM word_transactions WHERE user_id = ? ORDER BY id DESC LIMIT ?
    """, (user_id, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


