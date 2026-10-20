import json
import os
import re
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.config import get_env_setting, DEFAULT_MODEL
from core.database import (
    get_settings, log_activity, create_pipeline_task, 
    update_pipeline_task, log_pipeline_action, update_campaign_status,
    get_connection, get_active_campaign, get_campaign_tasks
)

# 10 Specialized Marketing Agents Configuration
PIPELINE_AGENTS = [
    {
        "id": "kotler",
        "name": "Philip Kotler",
        "role": "TRƯỞNG PHÒNG",
        "title": "Trưởng Phòng Marketing",
        "avatar_icon": "suit",
        "description": "Điều phối chiến lược tổng thể, phân công nhiệm vụ và giám sát toàn bộ dây chuyền.",
        "badge_color": "amber",
        "order": 0
    },
    {
        "id": "holmes",
        "name": "Sherlock Holmes",
        "role": "TRINH SÁT",
        "title": "Trinh Sát Thị Trường",
        "avatar_icon": "magnifier",
        "description": "Quét thị trường, phân tích đối thủ, tìm kiếm insight và nỗi đau khách hàng.",
        "badge_color": "indigo",
        "order": 1
    },
    {
        "id": "sun_tzu",
        "name": "Tôn Tử",
        "role": "CHIẾN LƯỢC",
        "title": "Chiến Lược Gia",
        "avatar_icon": "scroll",
        "description": "Định vị thông điệp cốt lõi, lập ma trận nội dung và chọn 3 góc tiếp cận (angles).",
        "badge_color": "orange",
        "order": 2
    },
    {
        "id": "ogilvy",
        "name": "David Ogilvy",
        "role": "VIẾT",
        "title": "Vua Copywriting",
        "avatar_icon": "pen",
        "description": "Viết tiêu đề giật tít (Hook), bài bán hàng thuyết phục (AIDA) và caption đa kênh.",
        "badge_color": "emerald",
        "order": 3
    },
    {
        "id": "picasso",
        "name": "Pablo Picasso",
        "role": "ẢNH",
        "title": "Giám Đốc Mỹ Thuật",
        "avatar_icon": "palette",
        "description": "Thiết kế thị giác, tạo prompt AI vẽ ảnh (Midjourney/Flux), banner và infographic.",
        "badge_color": "purple",
        "order": 4
    },
    {
        "id": "spielberg",
        "name": "Steven Spielberg",
        "role": "VIDEO",
        "title": "Đạo Diễn Video Ngắn",
        "avatar_icon": "camera",
        "description": "Lập storyboard video 30s-45s (Reels/TikTok/Shorts), kịch bản voiceover và visual cues.",
        "badge_color": "rose",
        "order": 5
    },
    {
        "id": "zuck",
        "name": "Mark Zuckerberg",
        "role": "ĐĂNG BÀI",
        "title": "Trùm Phân Phối Đa Kênh",
        "avatar_icon": "share",
        "description": "Lên lịch phân phối đa kênh. Giữ chốt kiểm duyệt (Human-in-the-loop) trước khi đăng.",
        "badge_color": "blue",
        "order": 6
    },
    {
        "id": "brunson",
        "name": "Russell Brunson",
        "role": "EMAIL, PHỄU",
        "title": "Bậc Thầy Phễu Bán Hàng",
        "avatar_icon": "funnel",
        "description": "Thiết kế phễu bán hàng (Sales Funnel), quà tặng lead magnet và chuỗi 3 email chốt sale.",
        "badge_color": "teal",
        "order": 7
    },
    {
        "id": "robin_hood",
        "name": "Robin Hood",
        "role": "QUẢNG CÁO",
        "title": "Tối Ưu Quảng Cáo Ads",
        "avatar_icon": "target",
        "description": "Target đối tượng chuẩn xác, tối ưu ngân sách và ma trận test A/B chiến dịch quảng cáo.",
        "badge_color": "yellow",
        "order": 8
    },
    {
        "id": "buffett",
        "name": "Warren Buffett",
        "role": "SỐ LIỆU",
        "title": "Chuyên Gia Phân Tích ROI",
        "avatar_icon": "chart",
        "description": "Đo lường CPA, CTR, tỷ lệ chuyển đổi, phân tích lợi nhuận và đề xuất tối ưu vòng lặp.",
        "badge_color": "cyan",
        "order": 9
    }
]

AGENT_ORDER = ["holmes", "sun_tzu", "ogilvy", "picasso", "spielberg", "zuck", "brunson", "robin_hood", "buffett"]

def get_agent_meta(agent_id: str) -> Dict[str, Any]:
    for a in PIPELINE_AGENTS:
        if a["id"] == agent_id:
            return a
    return {
        "id": agent_id,
        "name": agent_id.capitalize(),
        "role": "THÀNH VIÊN",
        "title": "Chuyên viên Marketing",
        "avatar_icon": "robot",
        "badge_color": "slate"
    }

def get_gemini_client():
    api_key = get_env_setting("GEMINI_API_KEY") or get_settings().get("gemini_api_key", "")
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        log_activity("PIPELINE", f"Không thể khởi tạo Gemini client: {e}", level="WARNING")
        return None

def call_ai_prompt(prompt: str, system_instruction: str = "") -> Optional[str]:
    """Helper to query Gemini with fallback."""
    client = get_gemini_client()
    if not client:
        return None
    try:
        full_prompt = f"System Instruction: {system_instruction}\n\nTask: {prompt}" if system_instruction else prompt
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=full_prompt
        )
        return response.text.strip()
    except Exception as e:
        log_activity("PIPELINE", f"Gemini API lỗi ({e}), chuyển sang fallback template.", level="WARNING")
        return None

# ==========================================
# AGENT 1: SHERLOCK HOLMES (TRINH SÁT)
# ==========================================
def run_scout_holmes(campaign: Dict[str, Any]) -> Dict[str, Any]:
    title = campaign.get("title", "")
    goal = campaign.get("goal", "")
    product = campaign.get("product_info", "")
    audience = campaign.get("target_audience", "")
    
    prompt = f"""
Bạn là Sherlock Holmes - Trinh Sát Tình Báo Thị Trường trong Dây Chuyền Marketing AI.
Nhiệm vụ: Phân tích thám tử thị trường về sản phẩm/dịch vụ sau:
- Tên chiến dịch: {title}
- Sản phẩm/Dịch vụ: {product}
- Mục tiêu: {goal}
- Đối tượng khách hàng: {audience}

Hãy phân tích và trả về định dạng JSON hợp lệ (không kèm markdown):
{{
  "pain_points": [
    "Nỗi đau 1 của khách hàng khi chưa có giải pháp này",
    "Nỗi đau 2",
    "Nỗi đau 3"
  ],
  "competitor_blindspots": [
    "Điểm yếu 1 mà các đối thủ ngoài kia đang mắc phải",
    "Điểm yếu 2"
  ],
  "trending_hooks": [
    "Góc khơi gợi tò mò 1 (dạng câu hỏi hoặc sự thật bất ngờ)",
    "Góc khơi gợi tò mò 2",
    "Góc khơi gợi tò mò 3"
  ],
  "intelligence_summary": "Đoạn tóm tắt ngắn dưới 80 từ về insight cốt lõi cho Tôn Tử lên chiến lược."
}}
"""
    raw_ai = call_ai_prompt(prompt, "Bạn là thám tử Sherlock Holmes phân tích thị trường cực kỳ sắc sảo.")
    if raw_ai:
        try:
            clean = re.sub(r"^```json\s*", "", raw_ai, flags=re.MULTILINE)
            clean = re.sub(r"\s*```$", "", clean, flags=re.MULTILINE)
            data = json.loads(clean)
            return data
        except:
            pass

    # Intelligent fallback
    return {
        "pain_points": [
            f"Mất quá nhiều thời gian làm thủ công và thiếu quy trình rõ ràng khi triển khai {product or 'marketing'}.",
            "Chi phí thuê nhân sự hoặc chạy quảng cáo đắt đỏ nhưng tỷ lệ ra đơn hoặc chuyển đổi thấp.",
            "Không biết cách viết bài thu hút, đăng bài bị trôi và đối thủ cạnh tranh ngày càng mạnh."
        ],
        "competitor_blindspots": [
            "Đối thủ chủ yếu quảng cáo spam chung chung, không giải quyết đúng nút thắt tâm lý của khách.",
            "Thiếu hệ thống chăm sóc tự động, khách hỏi xong thường bị bỏ quên hoặc phản hồi quá trễ."
        ],
        "trending_hooks": [
            f"Bí mật tại sao 90% người làm {product or 'kinh doanh'} thất bại vì thiếu tự động hóa?",
            f"Chiến lược tạo phễu thu hút khách hàng tiềm năng 24/7 chỉ với 1 cú click.",
            "Cách các top doanh nghiệp tinh gọn chi phí vận hành gấp 5 lần bằng quy trình chuẩn."
        ],
        "intelligence_summary": f"Khách hàng mục tiêu ({audience or 'chủ doanh nghiệp/shop'}) đang bị quá tải thời gian và áp lực chi phí. Insight cốt lõi: Họ không mua tính năng phức tạp, họ mua sự AN TÂM, TỰ ĐỘNG HÓA và KẾT QUẢ ĐO LƯỜNG ĐƯỢC."
    }

# ==========================================
# AGENT 2: TÔN TỬ (CHIẾN LƯỢC)
# ==========================================
def run_strategist_sun_tzu(campaign: Dict[str, Any], scout_data: Dict[str, Any]) -> Dict[str, Any]:
    summary = scout_data.get("intelligence_summary", "")
    pains = scout_data.get("pain_points", [])
    
    prompt = f"""
Bạn là Tôn Tử - Chiến Lược Gia Quân Sự Bậc Thầy trong Dây Chuyền Marketing AI.
Dựa trên báo cáo trinh sát từ Sherlock Holmes:
- Tóm tắt trinh sát: {summary}
- Nỗi đau khách: {pains}
- Sản phẩm: {campaign.get('product_info', '')}

Hãy hoạch định chiến lược và trả về JSON hợp lệ:
{{
  "core_value_proposition": "Định vị giá trị cốt lõi đánh trúng tâm lý",
  "strategic_angles": [
    {{
      "name": "Góc đánh 1: Trực diện nỗi đau (Pain-Agitate)",
      "hook_concept": "Ý tưởng tiếp cận chính",
      "target_emotion": "Cảm xúc kích hoạt (Lo lắng, sốt ruột)"
    }},
    {{
      "name": "Góc đánh 2: Khát vọng & Tự do (Gain-Aspiration)",
      "hook_concept": "Ý tưởng tiếp cận hướng tới kết quả mong ước",
      "target_emotion": "Khao khát bứt phá, dẫn đầu"
    }},
    {{
      "name": "Góc đánh 3: Bằng chứng thực tế (Social Proof & Case Study)",
      "hook_concept": "Ý tưởng dựa trên câu chuyện chuyển đổi thật",
      "target_emotion": "Sự tin cậy, an tâm tuyệt đối"
    }}
  ],
  "content_matrix": "Chiến lược phân bổ 3 bài trong tuần để chuyển đổi phễu.",
  "order_to_ogilvy": "Chỉ thị dứt khoát cho David Ogilvy về phong cách viết bài cần áp dụng."
}}
"""
    raw_ai = call_ai_prompt(prompt, "Bạn là Tôn Tử với tư duy chiến lược 'Biết người biết ta, trăm trận trăm thắng'.")
    if raw_ai:
        try:
            clean = re.sub(r"^```json\s*", "", raw_ai, flags=re.MULTILINE)
            clean = re.sub(r"\s*```$", "", clean, flags=re.MULTILINE)
            return json.loads(clean)
        except:
            pass

    return {
        "core_value_proposition": f"Giải pháp tối ưu chuyển đổi và giải phóng sức lao động cho {campaign.get('target_audience', 'khách hàng')} với hiệu quả vượt trội.",
        "strategic_angles": [
            {
                "name": "Góc 1: Đánh thẳng vào nỗi đau mất tiền & kiệt sức",
                "hook_concept": "Mỗi ngày trôi qua làm việc thủ công là một ngày đối thủ đang bỏ xa bạn.",
                "target_emotion": "Sốt ruột, nhận ra vấn đề khẩn cấp"
            },
            {
                "name": "Góc 2: Vẽ ra bức tranh tự động hóa thảnh thơi",
                "hook_concept": "Tưởng tượng hệ thống làm việc liên tục 24/7 mang khách hàng về ngay cả khi bạn đang ngủ.",
                "target_emotion": "Hào hứng, khao khát tự do vận hành"
            },
            {
                "name": "Góc 3: Bằng chứng người thật việc thật",
                "hook_concept": "Case study thực tế: Tăng 300% tương tác và tiết kiệm 15 giờ mỗi tuần.",
                "target_emotion": "Tin tưởng, thuyết phục logic"
            }
        ],
        "content_matrix": "Bài 1: Nêu vấn đề & đánh thức nhu cầu -> Bài 2: Chia sẻ bí quyết chuyên gia & phương pháp -> Bài 3: Ra mắt ưu đãi & chốt đơn.",
        "order_to_ogilvy": "David Ogilvy, hãy dùng Góc đánh 1 và 2 làm chủ đạo: Mở đầu bằng một câu Hook chấn động, giãi bày sự đồng cảm và kết thúc bằng lời kêu gọi hành động dứt khoát!"
    }

# ==========================================
# AGENT 3: DAVID OGILVY (VIẾT)
# ==========================================
def run_writer_ogilvy(campaign: Dict[str, Any], strategy_data: Dict[str, Any]) -> Dict[str, Any]:
    angle = strategy_data.get("strategic_angles", [{}])[0]
    order = strategy_data.get("order_to_ogilvy", "")
    product = campaign.get("product_info", "Dịch vụ của chúng tôi")
    
    prompt = f"""
Bạn là David Ogilvy - Phù thủy Quảng cáo huyền thoại trong Dây Chuyền Marketing AI.
Chỉ thị từ Tôn Tử: {order}
Góc chiến lược: {angle.get('name', '')} - {angle.get('hook_concept', '')}
Sản phẩm: {product}
Mục tiêu: {campaign.get('goal', '')}

Hãy viết một bài đăng Facebook chuyển đổi cao theo công thức kinh điển (Hook - Problem - Agitate - Solution - Offer - CTA).
Trả về JSON hợp lệ:
{{
  "headline": "Tiêu đề giật tít cực mạnh",
  "full_post": "Nội dung bài viết hoàn chỉnh có icon, ngắt dòng đẹp mắt và CTA rõ ràng",
  "call_to_action": "Câu kêu gọi hành động cụ thể",
  "hashtags": ["#marketing", "#tudonghoa", "#tangdoanhso"],
  "variants": [
    "Biến thể tiêu đề ngắn 1",
    "Biến thể tiêu đề ngắn 2",
    "Biến thể tiêu đề ngắn 3"
  ]
}}
"""
    raw_ai = call_ai_prompt(prompt, "Bạn là David Ogilvy viết copy sắc sảo, bán hàng không lối thoát.")
    if raw_ai:
        try:
            clean = re.sub(r"^```json\s*", "", raw_ai, flags=re.MULTILINE)
            clean = re.sub(r"\s*```$", "", clean, flags=re.MULTILINE)
            return json.loads(clean)
        except:
            pass

    return {
        "headline": f"🔥 NẾU BẠN VẪN ĐANG LÀM THEO CÁCH CŨ, BẠN ĐANG MẤT ĐI 80% KHÁCH HÀNG MỖI NGÀY!",
        "full_post": f"""🔥 NẾU BẠN VẪN ĐANG LÀM THEO CÁCH CŨ, BẠN ĐANG MẤT ĐI 80% KHÁCH HÀNG MỖI NGÀY!

Có bao giờ bạn rơi vào tình trạng:
❌ Bỏ cả ngày ngồi đăng bài, trả lời tin nhắn nhưng đơn về lẹt đẹt?
❌ Thuê nhân sự thì tốn kém, đào tạo xong lại nghỉ việc?
❌ Chi tiền chạy quảng cáo thì giá tin nhắn ngày một đắt đỏ?

Sự thật là: Những doanh nghiệp thành công nhất KHÔNG làm việc chăm chỉ hơn bạn, họ làm việc với HỆ THỐNG THÔNG MINH HƠN.

Đó là lý do chúng tôi phát triển giải pháp:
✨ {product} ✨

Giúp bạn:
👉 Tự động hóa quy trình tìm kiếm & chăm sóc khách hàng mục tiêu 24/7.
👉 X3 năng suất làm việc của toàn bộ đội ngũ.
👉 Tiết kiệm ít nhất 15-20 triệu chi phí vận hành mỗi tháng.

🎁 ĐẶC BIỆT: Dành riêng cho 10 người nhanh tay nhất hôm nay — Tặng ngay gói trải nghiệm và bản đồ tự động hóa chi tiết!

👇 Comment ngay 'NHẬN' hoặc để lại tin nhắn để chuyên gia hỗ trợ bạn ngay trong hôm nay!""",
        "call_to_action": "Bình luận 'NHẬN' hoặc Inbox trực tiếp để nhận bản demo miễn phí!",
        "hashtags": ["#DoanhNghiep", "#TuDongHoa", "#MarketingAI", "#TangTruongDoanhSo"],
        "variants": [
            "Bí quyết sở hữu phòng marketing tự động vận hành cả khi bạn ngủ",
            "Đừng để đối thủ vượt mặt chỉ vì bạn vẫn đang làm thủ công!",
            "Tối ưu 80% chi phí marketing ngay trong tháng này bằng giải pháp mới"
        ]
    }

# ==========================================
# AGENT 4: PABLO PICASSO (ẢNH)
# ==========================================
def run_artist_picasso(campaign: Dict[str, Any], writer_data: Dict[str, Any]) -> Dict[str, Any]:
    headline = writer_data.get("headline", "")
    
    prompt = f"""
Bạn là Pablo Picasso - Giám Đốc Mỹ Thuật & Visual AI trong Dây Chuyền Marketing.
Dựa vào bài viết: "{headline}"
Sản phẩm: {campaign.get('product_info', '')}

Hãy thiết kế concept hình ảnh quảng cáo và prompt AI (cho Midjourney/Flux) đỉnh cao.
Trả về JSON hợp lệ:
{{
  "visual_concept": "Ý tưởng thị giác chủ đạo của bức ảnh/banner",
  "midjourney_prompt": "Prompt tiếng Anh chuyên nghiệp, siêu chi tiết cho Midjourney v6/Flux kèm --ar 16:9 --style raw",
  "color_palette": ["Mã màu chính 1", "Mã màu 2", "Mã màu 3"],
  "text_on_image": "Chữ nổi bật trên ảnh (dưới 8 từ, font to, tương phản cao)",
  "layout_recommendation": "Gợi ý bố cục: Ảnh bên trái, text bên phải, nút CTA nổi bật."
}}
"""
    raw_ai = call_ai_prompt(prompt, "Bạn là nghệ sĩ thị giác thiên tài Pablo Picasso thiết kế banner quảng cáo bắt mắt.")
    if raw_ai:
        try:
            clean = re.sub(r"^```json\s*", "", raw_ai, flags=re.MULTILINE)
            clean = re.sub(r"\s*```$", "", clean, flags=re.MULTILINE)
            return json.loads(clean)
        except:
            pass

    return {
        "visual_concept": "Hình ảnh tương phản mạnh mẽ giữa một không gian làm việc công nghệ tương lai hiện đại, ánh sáng neon cam - xanh navy, tạo cảm giác chuyên nghiệp và bứt phá.",
        "midjourney_prompt": f"Futuristic high-tech marketing command center, holographic AI multi-agent workflow glowing with neon orange and deep navy blue lights, cinematic lighting, ultra-realistic 8k octane render, minimalist clean layout, premium corporate SaaS dashboard atmosphere --ar 16:9 --style raw --v 6.0",
        "color_palette": ["#ff6b00 (Cam chủ đạo)", "#0f172a (Xanh Navy đậm)", "#10b981 (Xanh lục thành công)"],
        "text_on_image": "TỰ ĐỘNG HÓA MARKETING 4.0 — TĂNG TỐC DOANH SỐ",
        "layout_recommendation": "Tỉ lệ 16:9 hoặc 1:1, ảnh robot 3D bên phải, dòng tít lớn tương phản trắng/cam bên trái, có logo công ty ở góc trên."
    }

# ==========================================
# AGENT 5: STEVEN SPIELBERG (VIDEO)
# ==========================================
def run_director_spielberg(campaign: Dict[str, Any], writer_data: Dict[str, Any], artist_data: Dict[str, Any]) -> Dict[str, Any]:
    headline = writer_data.get("headline", "")
    
    prompt = f"""
Bạn là Steven Spielberg - Đạo Diễn Video Ngắn hàng đầu trong Dây Chuyền Marketing.
Hãy dàn dựng kịch bản Video ngắn 30-45 giây (TikTok/Reels/Shorts) từ bài viết: "{headline}"
Trả về JSON hợp lệ:
{{
  "video_title": "Tên kịch bản video giật gân",
  "target_duration": "35 giây",
  "bgm_soundtrack": "Tên phong cách nhạc nền (vd: Upbeat Modern Vlog / Cyberpunk Pulse)",
  "scenes": [
    {{
      "time": "00:00 - 00:03",
      "stage": "HOOK (Giữ chân 3 giây đầu)",
      "visual": "Mô tả hình ảnh quay/hiệu ứng trên màn hình",
      "voiceover": "Lời thoại nhân vật hoặc AI Voice",
      "sfx": "Âm thanh hiệu ứng (Whoosh, Ding)"
    }},
    {{
      "time": "00:03 - 00:15",
      "stage": "PROBLEM (Khoét sâu nỗi đau)",
      "visual": "Cảnh quay vấn đề",
      "voiceover": "Lời thoại bộc lộ sự đồng cảm",
      "sfx": "Glitch sound"
    }},
    {{
      "time": "00:15 - 00:28",
      "stage": "SOLUTION (Trình diễn giải pháp)",
      "visual": "Cảnh quay giao diện hệ thống hoạt động mượt mà",
      "voiceover": "Lời thoại giới thiệu giải pháp bứt phá",
      "sfx": "Chime pop"
    }},
    {{
      "time": "00:28 - 00:35",
      "stage": "CTA (Kêu gọi hành động)",
      "visual": "Chữ CTA xuất hiện kèm mũi tên chỉ xuống",
      "voiceover": "Lời thoại chốt hạ dứt khoát",
      "sfx": "UI Bell Ding"
    }}
  ]
}}
"""
    raw_ai = call_ai_prompt(prompt, "Bạn là đạo diễn Steven Spielberg chuyên tạo video viral giữ chân người xem 100%.")
    if raw_ai:
        try:
            clean = re.sub(r"^```json\s*", "", raw_ai, flags=re.MULTILINE)
            clean = re.sub(r"\s*```$", "", clean, flags=re.MULTILINE)
            return json.loads(clean)
        except:
            pass

    return {
        "video_title": "Bí mật phòng Marketing tự động vận hành trong 35 giây",
        "target_duration": "35 giây",
        "bgm_soundtrack": "Upbeat Tech Phonk / Modern Lo-Fi Synth",
        "scenes": [
            {
                "time": "00:00 - 00:03",
                "stage": "HOOK (Chặn ngón tay lướt)",
                "visual": "Zoom cận cảnh vào màn hình điện thoại đang nhảy thông báo đơn hàng liên tục, biểu cảm kinh ngạc.",
                "voiceover": "Đừng bao giờ thuê thêm nhân sự marketing nếu bạn chưa xem hết video này!",
                "sfx": "Fast Swoosh + Camera Click"
            },
            {
                "time": "00:03 - 00:15",
                "stage": "PROBLEM (Nỗi đau thực tế)",
                "visual": "Cảnh làm việc đêm muộn mệt mỏi, đống giấy tờ và biểu đồ chi phí đỏ lòm.",
                "voiceover": "Bạn bỏ 15 tiếng mỗi ngày đăng bài, trả lời inbox thủ công nhưng cuối tháng vẫn đau đầu vì chi phí quá cao?",
                "sfx": "Low Hum + Warning Glitch"
            },
            {
                "time": "00:15 - 00:28",
                "stage": "SOLUTION (Trình diễn công nghệ)",
                "visual": "Chuyển cảnh nhanh sang dây chuyền AI: Robot tự cào khách, tự viết bài, tự đăng bài mượt mà.",
                "voiceover": "Đây là cách các chủ shop thông minh để cả một đội ngũ AI làm việc 24/7 thay mình chỉ với 1 cú click!",
                "sfx": "Sci-Fi Energy Rise + UI Chime"
            },
            {
                "time": "00:28 - 00:35",
                "stage": "CTA (Kêu gọi chốt hạ)",
                "visual": "Popup quà tặng miễn phí nảy lên kèm nút chỉ vào link bio.",
                "voiceover": "Bình luận ngay bên dưới hoặc bấm link ở bio để nhận bản quyền dùng thử miễn phí hôm nay nhé!",
                "sfx": "UI Success Ding Pop"
            }
        ]
    }

# ==========================================
# AGENT 6: MARK ZUCKERBERG (ĐĂNG BÀI & PHÂN PHỐI)
# ==========================================
def run_publisher_zuck(campaign: Dict[str, Any], writer_data: Dict[str, Any], artist_data: Dict[str, Any], video_data: Dict[str, Any]) -> Dict[str, Any]:
    # Returns publication payload and requires Boss approval!
    return {
        "channels": [
            {"channel": "Facebook Trang Cá Nhân", "status": "Sẵn sàng", "schedule": "Ngay sau khi duyệt"},
            {"channel": "Hội Nhóm Facebook Mục Tiêu", "status": "Sẵn sàng", "schedule": "Giãn cách 15 phút/nhóm"},
            {"channel": "Fanpage Doanh Nghiệp", "status": "Sẵn sàng", "schedule": "19:30 Khung giờ vàng"},
            {"channel": "TikTok / Reels", "status": "Chờ video render", "schedule": "20:00"}
        ],
        "approval_ticket": {
            "title": writer_data.get("headline", "Bài đăng chiến dịch mới"),
            "content_preview": writer_data.get("full_post", "")[:350] + "...",
            "full_content": writer_data.get("full_post", ""),
            "image_spec": artist_data.get("visual_concept", ""),
            "video_title": video_data.get("video_title", ""),
            "status": "waiting_approval",
            "message": "Nội dung & Visual đã sản xuất xong 100%. Đang chờ Sếp bấm Phê Duyệt để tự động phân phối!"
        },
        "anti_spam_guard": "Kích hoạt giãn cách đăng bài ngẫu nhiên 120s - 300s để bảo vệ an toàn nick."
    }

# ==========================================
# AGENT 7: RUSSELL BRUNSON (EMAIL, PHỄU)
# ==========================================
def run_funnel_brunson(campaign: Dict[str, Any], writer_data: Dict[str, Any]) -> Dict[str, Any]:
    headline = writer_data.get("headline", "")
    product = campaign.get("product_info", "Sản phẩm")
    
    prompt = f"""
Bạn là Russell Brunson - Bậc Thầy Phễu Bán Hàng (ClickFunnels) trong Dây Chuyền Marketing.
Hãy xây dựng cấu trúc phễu thu lead và chuỗi 3 email nuôi dưỡng cho sản phẩm: {product}
Chủ đề: {headline}
Trả về JSON hợp lệ:
{{
  "lead_magnet": {{
    "name": "Tên mồi câu thu hút (Ebook, Checklist, Khóa học ngắn)",
    "hook": "Lý do khách hàng sẵn sàng để lại Email/SĐT để nhận ngay"
  }},
  "landing_page_headline": "Tiêu đề trang đích trang web gom khách",
  "email_sequence": [
    {{
      "day": "Email 1 (Gửi ngay lập tức)",
      "subject": "Tiêu đề Email 1 gây tò mò",
      "preview": "Tóm tắt nội dung gửi quà tặng và lời chào đón thân tình"
    }},
    {{
      "day": "Email 2 (Gửi sau 24h)",
      "subject": "Tiêu đề Email 2 bẻ gãy lầm tưởng",
      "preview": "Chia sẻ câu chuyện sai lầm phổ biến và cách giải quyết"
    }},
    {{
      "day": "Email 3 (Gửi sau 48h)",
      "subject": "Tiêu đề Email 3 ưu đãi khẩn cấp",
      "preview": "Giới thiệu ưu đãi giới hạn thời gian và kêu gọi đặt lịch/mua hàng"
    }}
  ]
}}
"""
    raw_ai = call_ai_prompt(prompt, "Bạn là bậc thầy phễu Russell Brunson với phong cách Soap Opera Sequence.")
    if raw_ai:
        try:
            clean = re.sub(r"^```json\s*", "", raw_ai, flags=re.MULTILINE)
            clean = re.sub(r"\s*```$", "", clean, flags=re.MULTILINE)
            return json.loads(clean)
        except:
            pass

    return {
        "lead_magnet": {
            "name": f"Bộ Bí Quyết 7 Bước Tự Động Hóa Vận Hành Cho {campaign.get('target_audience', 'Doanh Nghiệp')}",
            "hook": "Bản checklist PDF ngắn gọn, thực chiến 100% giúp tiết kiệm ngay 50% thời gian trong tuần đầu."
        },
        "landing_page_headline": f"Khám Phá Cách Xây Dựng Cỗ Máy Thu Hút Khách Hàng Tự Động Chỉ Với Một Nhân Sự!",
        "email_sequence": [
            {
                "day": "Email 1 (Gửi ngay)",
                "subject": "🎁 Quà tặng của bạn đây + Một bí mật nhỏ tôi chưa từng kể...",
                "preview": "Gửi link tải tài liệu, đồng thời giới thiệu câu chuyện xuất phát điểm đầy trăn trở."
            },
            {
                "day": "Email 2 (Sau 24 giờ)",
                "subject": "⚠️ Lý do khiến 95% mọi người thất bại khi tìm khách hàng mới?",
                "preview": "Chỉ ra sai lầm khi làm thủ công đơn lẻ và giải thích tại sao cần tư duy dây chuyền hệ thống."
            },
            {
                "day": "Email 3 (Sau 48 giờ)",
                "subject": "⏰ Chỉ còn 24 giờ cuối để nhận ưu đãi đồng hành đặc biệt!",
                "preview": "Đưa ra lời mời tham gia giải pháp chính thức kèm cam kết hoàn tiền 100% nếu không hiệu quả."
            }
        ]
    }

# ==========================================
# AGENT 8: ROBIN HOOD (QUẢNG CÁO)
# ==========================================
def run_ads_robin_hood(campaign: Dict[str, Any], writer_data: Dict[str, Any], audience: str) -> Dict[str, Any]:
    prompt = f"""
Bạn là Robin Hood - Chuyên Gia Tối Ưu Quảng Cáo Facebook & TikTok Ads.
Sản phẩm: {campaign.get('product_info', '')}
Đối tượng mục tiêu: {audience}
Thông điệp: {writer_data.get('headline', '')}

Hãy thiết lập ma trận chiến dịch quảng cáo tối ưu ngân sách.
Trả về JSON hợp lệ:
{{
  "campaign_objective": "Mục tiêu (Tin nhắn / Lượt chuyển đổi / Khách hàng tiềm năng)",
  "target_interests": ["Sở thích 1", "Sở thích 2", "Sở thích 3", "Hành vi"],
  "demographics": {{
    "age": "24 - 45",
    "gender": "Tất cả hoặc Nam/Nữ",
    "locations": "Toàn quốc hoặc các thành phố lớn"
  }},
  "budget_allocation": {{
    "test_phase": "20% ngân sách (Test 3 tệp)",
    "scaling_phase": "70% ngân sách (Đổ vào ad set chiến thắng)",
    "retargeting": "10% ngân sách (Bám đuổi người đã tương tác)"
  }},
  "ab_test_matrix": [
    "Test A: Video Spielberg vs Test B: Ảnh Picasso",
    "Test Headline giật tít vs Headline chia sẻ giá trị"
  ]
}}
"""
    raw_ai = call_ai_prompt(prompt, "Bạn là Robin Hood cướp traffic rẻ về cho thân chủ bằng kỹ thuật ads siêu đẳng.")
    if raw_ai:
        try:
            clean = re.sub(r"^```json\s*", "", raw_ai, flags=re.MULTILINE)
            clean = re.sub(r"\s*```$", "", clean, flags=re.MULTILINE)
            return json.loads(clean)
        except:
            pass

    return {
        "campaign_objective": "Tối ưu hóa Lượt chuyển đổi & Tin nhắn Messenger chất lượng cao",
        "target_interests": [
            "Quản trị kinh doanh", "Bán lẻ online", "Phần mềm dịch vụ (SaaS)", 
            "Chủ sở hữu trang doanh nghiệp", "Kinh doanh tự do"
        ],
        "demographics": {
            "age": "24 - 45 tuổi",
            "gender": "Tất cả",
            "locations": "Hà Nội, TP. Hồ Chí Minh, Đà Nẵng và các đô thị lớn"
        },
        "budget_allocation": {
            "test_phase": "20% ngân sách (Chạy test 3 nhóm quảng cáo với 3 góc thông điệp)",
            "scaling_phase": "70% ngân sách (Gia tăng ngân sách cho tệp có giá lead thấp nhất)",
            "retargeting": "10% ngân sách (Quét lại những người đã xem trên 50% video hoặc bấm vào bài viết)"
        },
        "ab_test_matrix": [
            "Biến thể A: Video Storyboard của Spielberg (Tập trung cảm xúc)",
            "Biến thể B: Ảnh Banner Visual của Picasso (Tập trung tính năng và CTA)"
        ]
    }

# ==========================================
# AGENT 9: WARREN BUFFETT (SỐ LIỆU & ROI)
# ==========================================
def run_analyst_buffett(campaign: Dict[str, Any], ads_data: Dict[str, Any]) -> Dict[str, Any]:
    prompt = f"""
Bạn là Warren Buffett - Bậc Thầy Thẩm Định Tài Chính & Dữ Liệu ROI trong Marketing.
Hãy phân tích dự báo các chỉ số tài chính và tỷ lệ hoàn vốn cho chiến dịch:
- Tên chiến dịch: {campaign.get('title', '')}
- Mục tiêu: {campaign.get('goal', '')}
- Quảng cáo: {ads_data.get('campaign_objective', '')}

Trả về JSON hợp lệ:
{{
  "projected_reach": "25,000 - 40,000 lượt tiếp cận",
  "projected_ctr": "3.5% - 5.2% (Tỉ lệ click cao nhờ nội dung chuẩn Ogilvy)",
  "projected_cpa": "35,000đ - 55,000đ / Khách hàng tiềm năng chất lượng",
  "projected_roi": "320% - 450% Lợi nhuận gộp",
  "key_findings": [
    "Nội dung tập trung vào nỗi đau tiết kiệm thời gian sẽ có tỷ lệ giữ chân cao nhất.",
    "Chi phí trên mỗi lead giảm khoảng 40% so với phương pháp đăng bài đại trà cũ."
  ],
  "recommendations_for_kotler": "Lời khuyên chiến lược gửi Trưởng phòng Philip Kotler cho chu kỳ tuần tiếp theo."
}}
"""
    raw_ai = call_ai_prompt(prompt, "Bạn là nhà đầu tư đại tài Warren Buffett tính toán từng đồng hiệu quả chi phí.")
    if raw_ai:
        try:
            clean = re.sub(r"^```json\s*", "", raw_ai, flags=re.MULTILINE)
            clean = re.sub(r"\s*```$", "", clean, flags=re.MULTILINE)
            return json.loads(clean)
        except:
            pass

    return {
        "projected_reach": "30,000 - 50,000 lượt hiển thị mục tiêu",
        "projected_ctr": "4.2% (Vượt 1.8 lần so với trung bình ngành)",
        "projected_cpa": "42,000đ / Lead đủ điều kiện tư vấn",
        "projected_roi": "380% Tỷ suất hoàn vốn",
        "key_findings": [
            "Chiến lược kết hợp Video Spielberg (chặn lướt) + Chốt đơn Ogilvy tạo ra phễu chuyển đổi khép kín.",
            "Tự động hóa giúp giảm thiểu 85% thời gian phản hồi tin nhắn của khách hàng."
        ],
        "recommendations_for_kotler": "Kính gửi Trưởng phòng Philip Kotler: Toàn bộ dây chuyền vận hành nhịp nhàng. Đề xuất tăng 30% ngân sách cho kênh Video ngắn và mở rộng thêm 2 tệp đối tượng vào tuần tới!"
    }

# ==========================================
# MASTER PIPELINE ORCHESTRATOR
# ==========================================

def get_pipeline_full_state() -> Dict[str, Any]:
    """Returns the full state of all 10 agents, active campaign, tasks and connections."""
    active_campaign = get_active_campaign()
    if not active_campaign:
        # Create a default campaign if none exists
        from core.database import create_pipeline_campaign
        cid = create_pipeline_campaign(
            title="Chiến Dịch Tự Động Hóa Tuyển Sinh & Tìm Khách AI",
            goal="Tìm kiếm 50 khách hàng tiềm năng & tự động hóa đăng bài",
            product_info="Hệ thống AI Marketing Tự Động Đa Kênh",
            target_audience="Chủ shop online, doanh nghiệp vừa và nhỏ, người làm marketing"
        )
        active_campaign = get_active_campaign()

    campaign_id = active_campaign["id"]
    tasks = get_campaign_tasks(campaign_id)
    task_map = {t["agent_id"]: t for t in tasks}

    # Build agent status list
    agents_state = []
    
    # 0. Philip Kotler (Trưởng phòng)
    kotler_active_tasks = sum(1 for t in tasks if t["status"] in ("running", "pending"))
    agents_state.append({
        **PIPELINE_AGENTS[0],
        "status": "Đang chạy" if active_campaign.get("status") != "idle" else "Tạm dừng",
        "is_running": True,
        "active_tasks_count": kotler_active_tasks,
        "waiting_approval_count": 0,
        "task_data": None
    })

    current_agent_id = active_campaign.get("current_agent_id", "holmes")
    campaign_status = active_campaign.get("status", "running")

    for agent_def in PIPELINE_AGENTS[1:]:
        aid = agent_def["id"]
        t = task_map.get(aid)
        
        status_text = "Sắp vào nhóm"
        active_count = 0
        waiting_approval = 0
        
        if t:
            if t["status"] == "completed":
                status_text = "Đã hoàn thành"
            elif t["status"] == "waiting_approval":
                status_text = "Chờ duyệt"
                waiting_approval = 1
            elif t["status"] == "running":
                status_text = "Đang chạy"
                active_count = 1
        elif aid == current_agent_id and campaign_status == "running":
            status_text = "Đang chạy"
            active_count = 1

        agents_state.append({
            **agent_def,
            "status": status_text,
            "is_running": (status_text == "Đang chạy"),
            "active_tasks_count": active_count,
            "waiting_approval_count": waiting_approval,
            "task_data": t
        })

    # Compute connection lines state
    connections = []
    # From Kotler to Holmes (vertical)
    connections.append({
        "from": "kotler",
        "to": "holmes",
        "active": True
    })

    # Row 1 chain: holmes -> sun_tzu -> ogilvy -> picasso -> spielberg
    row1 = ["holmes", "sun_tzu", "ogilvy", "picasso", "spielberg"]
    for i in range(len(row1) - 1):
        f = row1[i]
        t = row1[i + 1]
        is_active = (task_map.get(f) is not None)
        connections.append({"from": f, "to": t, "active": is_active})

    # Down from spielberg to zuck
    connections.append({
        "from": "spielberg",
        "to": "zuck",
        "active": (task_map.get("spielberg") is not None)
    })

    # Row 2 chain: zuck -> brunson -> robin_hood -> buffett
    row2 = ["zuck", "brunson", "robin_hood", "buffett"]
    for i in range(len(row2) - 1):
        f = row2[i]
        t = row2[i + 1]
        is_active = (task_map.get(f) is not None and task_map.get(f, {}).get("status") == "completed")
        connections.append({"from": f, "to": t, "active": is_active})

    return {
        "campaign": active_campaign,
        "agents": agents_state,
        "connections": connections,
        "tasks": tasks
    }

def run_pipeline_step(campaign_id: Optional[int] = None, agent_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes the next step in the pipeline or a specific agent step.
    Passes output of previous agent to the next agent.
    """
    if not campaign_id:
        camp = get_active_campaign()
        if not camp:
            return {"success": False, "message": "Không có chiến dịch nào đang hoạt động!"}
        campaign_id = camp["id"]
    else:
        conn = get_connection()
        camp = conn.execute("SELECT * FROM pipeline_campaigns WHERE id = ?", (campaign_id,)).fetchone()
        conn.close()
        if not camp:
            return {"success": False, "message": "Không tìm thấy chiến dịch!"}
        camp = dict(camp)

    tasks = get_campaign_tasks(campaign_id)
    task_map = {t["agent_id"]: t for t in tasks}

    # Determine which agent to run
    target_agent = agent_id
    if not target_agent:
        for aid in AGENT_ORDER:
            t = task_map.get(aid)
            if not t or t["status"] in ("pending", "running"):
                target_agent = aid
                break
            if t["status"] == "waiting_approval":
                return {
                    "success": True, 
                    "agent_id": aid, 
                    "status": "waiting_approval",
                    "message": f"Nhiệm vụ đang dừng tại '{t['agent_name']}' để chờ Boss phê duyệt!"
                }

    if not target_agent:
        update_campaign_status(campaign_id, "completed")
        log_pipeline_action(campaign_id, "buffett", "kotler", "Báo cáo tổng kết", "Chiến dịch đã hoàn tất toàn bộ dây chuyền xuất sắc!")
        return {"success": True, "completed": True, "message": "Chiến dịch đã hoàn tất toàn bộ dây chuyền!"}

    meta = get_agent_meta(target_agent)
    
    # 1. Create or get task
    existing_task = task_map.get(target_agent)
    if existing_task:
        task_id = existing_task["id"]
    else:
        task_id = create_pipeline_task(
            campaign_id=campaign_id,
            agent_id=target_agent,
            agent_name=meta["name"],
            agent_role=meta["role"],
            input_data={"campaign_title": camp["title"]},
            status="running"
        )

    update_pipeline_task(task_id, "running")
    update_campaign_status(campaign_id, "running", current_agent_id=target_agent)
    
    output_result = {}
    summary_text = ""

    # Execute specific agent logic
    if target_agent == "holmes":
        log_pipeline_action(campaign_id, "kotler", "holmes", "Giao việc trinh sát", "Phát lệnh quét insight thị trường & đối thủ")
        output_result = run_scout_holmes(camp)
        summary_text = f"Đã phát hiện {len(output_result.get('pain_points', []))} nỗi đau cốt lõi và 3 góc tiếp cận xu hướng."
        update_pipeline_task(task_id, "completed", output_data=output_result, summary=summary_text)
        log_pipeline_action(campaign_id, "holmes", "sun_tzu", "Bàn giao hồ sơ trinh sát", summary_text)

    elif target_agent == "sun_tzu":
        holmes_task = task_map.get("holmes")
        holmes_data = holmes_task.get("output_data", {}) if holmes_task else run_scout_holmes(camp)
        output_result = run_strategist_sun_tzu(camp, holmes_data)
        summary_text = f"Đã xác lập 3 góc đánh chiến lược & chỉ thị phong cách viết bài cho David Ogilvy."
        update_pipeline_task(task_id, "completed", output_data=output_result, summary=summary_text)
        log_pipeline_action(campaign_id, "sun_tzu", "ogilvy", "Bàn giao kế hoạch chiến lược", summary_text)

    elif target_agent == "ogilvy":
        sun_tzu_task = task_map.get("sun_tzu")
        sun_tzu_data = sun_tzu_task.get("output_data", {}) if sun_tzu_task else {}
        output_result = run_writer_ogilvy(camp, sun_tzu_data)
        summary_text = f"Đã hoàn thành bài viết chuyển đổi cao với tiêu đề: '{output_result.get('headline', '')[:40]}...'"
        update_pipeline_task(task_id, "completed", output_data=output_result, summary=summary_text)
        log_pipeline_action(campaign_id, "ogilvy", "picasso", "Bàn giao bài viết hoàn chỉnh", summary_text)

    elif target_agent == "picasso":
        ogilvy_task = task_map.get("ogilvy")
        ogilvy_data = ogilvy_task.get("output_data", {}) if ogilvy_task else {}
        output_result = run_artist_picasso(camp, ogilvy_data)
        summary_text = f"Đã thiết kế concept visual và prompt Midjourney/Flux chất lượng cao."
        update_pipeline_task(task_id, "completed", output_data=output_result, summary=summary_text)
        log_pipeline_action(campaign_id, "picasso", "spielberg", "Bàn giao concept thị giác", summary_text)

    elif target_agent == "spielberg":
        ogilvy_task = task_map.get("ogilvy")
        ogilvy_data = ogilvy_task.get("output_data", {}) if ogilvy_task else {}
        picasso_task = task_map.get("picasso")
        picasso_data = picasso_task.get("output_data", {}) if picasso_task else {}
        output_result = run_director_spielberg(camp, ogilvy_data, picasso_data)
        summary_text = f"Đã dựng storyboard video 35s gồm 4 phân cảnh (Hook - Problem - Solution - CTA)."
        update_pipeline_task(task_id, "completed", output_data=output_result, summary=summary_text)
        log_pipeline_action(campaign_id, "spielberg", "zuck", "Bàn giao kịch bản video", summary_text)

    elif target_agent == "zuck":
        ogilvy_data = task_map.get("ogilvy", {}).get("output_data", {})
        picasso_data = task_map.get("picasso", {}).get("output_data", {})
        video_data = task_map.get("spielberg", {}).get("output_data", {})
        output_result = run_publisher_zuck(camp, ogilvy_data, picasso_data, video_data)
        summary_text = "Nội dung & media đã sẵn sàng. Dừng lại tại trạm chờ Boss phê duyệt trước khi đăng bài."
        # Crucial: Pause for approval!
        update_pipeline_task(task_id, "waiting_approval", output_data=output_result, summary=summary_text)
        update_campaign_status(campaign_id, "waiting_approval", current_agent_id="zuck")
        log_pipeline_action(campaign_id, "zuck", "BOSS", "Gửi phiếu phê duyệt đăng bài", "Chờ Boss xem xét và bấm Phê Duyệt")
        return {
            "success": True, 
            "task_id": task_id, 
            "agent_id": "zuck",
            "status": "waiting_approval",
            "summary": summary_text,
            "output": output_result
        }

    elif target_agent == "brunson":
        ogilvy_data = task_map.get("ogilvy", {}).get("output_data", {})
        output_result = run_funnel_brunson(camp, ogilvy_data)
        summary_text = f"Đã thiết lập phễu quà tặng mồi & chuỗi 3 email nuôi dưỡng khách hàng."
        update_pipeline_task(task_id, "completed", output_data=output_result, summary=summary_text)
        log_pipeline_action(campaign_id, "brunson", "robin_hood", "Bàn giao phễu thu lead", summary_text)

    elif target_agent == "robin_hood":
        ogilvy_data = task_map.get("ogilvy", {}).get("output_data", {})
        output_result = run_ads_robin_hood(camp, ogilvy_data, camp.get("target_audience", ""))
        summary_text = f"Đã lên cấu hình Ads tối ưu, chia tỷ lệ ngân sách 70-20-10 và ma trận A/B test."
        update_pipeline_task(task_id, "completed", output_data=output_result, summary=summary_text)
        log_pipeline_action(campaign_id, "robin_hood", "buffett", "Bàn giao cấu hình quảng cáo", summary_text)

    elif target_agent == "buffett":
        robin_data = task_map.get("robin_hood", {}).get("output_data", {})
        output_result = run_analyst_buffett(camp, robin_data)
        summary_text = f"Dự báo ROI đạt {output_result.get('projected_roi', '380%')}, CPA dự kiến {output_result.get('projected_cpa', '')}."
        update_pipeline_task(task_id, "completed", output_data=output_result, summary=summary_text)
        update_campaign_status(campaign_id, "completed", current_agent_id="kotler")
        log_pipeline_action(campaign_id, "buffett", "kotler", "Báo cáo tài chính & kết quả", summary_text)

    return {
        "success": True,
        "task_id": task_id,
        "agent_id": target_agent,
        "status": "completed",
        "summary": summary_text,
        "output": output_result
    }

def approve_zuck_post(campaign_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Called when Boss clicks 'Phê duyệt' on Mark Zuckerberg's card.
    Marks task as completed and resumes the pipeline!
    """
    if not campaign_id:
        camp = get_active_campaign()
        if not camp:
            return {"success": False, "message": "Không tìm thấy chiến dịch!"}
        campaign_id = camp["id"]

    tasks = get_campaign_tasks(campaign_id)
    zuck_task = next((t for t in tasks if t["agent_id"] == "zuck"), None)
    if not zuck_task:
        return {"success": False, "message": "Chưa có tác vụ đăng bài của Mark Zuckerberg!"}

    # Mark completed
    update_pipeline_task(zuck_task["id"], "completed", summary="Sếp đã phê duyệt! Bài viết đã được lên lịch phân phối thành công.")
    update_campaign_status(campaign_id, "running", current_agent_id="brunson")
    log_pipeline_action(campaign_id, "BOSS", "zuck", "Phê duyệt đăng bài", "Boss đã duyệt bài viết và cho phép phân phối.")
    log_pipeline_action(campaign_id, "zuck", "brunson", "Chuyển giao sau khi đăng", "Kích hoạt tiếp phễu Email & Chuyển đổi.")
    
    return {"success": True, "message": "Đã phê duyệt thành công! Dây chuyền tiếp tục chuyển sang Russell Brunson (Email, Phễu)."}
