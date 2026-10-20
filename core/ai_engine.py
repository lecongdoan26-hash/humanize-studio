import json
import os
import re
from typing import Dict, Any, List, Optional
from core.config import get_env_setting, DEFAULT_MODEL
from core.database import get_settings, log_activity

def get_gemini_client():
    api_key = get_env_setting("GEMINI_API_KEY") or get_settings().get("gemini_api_key", "")
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        log_activity("AI_ENGINE", f"Lỗi khởi tạo Gemini client: {e}", level="ERROR")
        return None

def analyze_and_classify_lead(post_text: str, group_name: str = "") -> Dict[str, Any]:
    """
    Phân tích bài viết bằng AI để xác định xem có phải khách hàng tiềm năng không.
    Trả về dict: {is_lead, score, intent, urgency, suggested_reply}
    """
    settings = get_settings()
    business_name = settings.get("business_name", "Dịch vụ của chúng tôi")
    business_desc = settings.get("business_desc", "Giải pháp tự động hóa và marketing chuyên nghiệp")
    cta_contact = settings.get("cta_contact", "Liên hệ với chúng tôi để được tư vấn")
    ai_tone = settings.get("ai_tone", "Thân thiện, súc tích, hữu ích")
    
    client = get_gemini_client()
    
    # 1. NẾU CÓ GEMINI API KEY -> DÙNG AI CHUYÊN SÂU
    if client:
        prompt = f"""
Bạn là chuyên gia phân tích bài viết mạng xã hội (Social Listening & Lead Ingestion AI) cho doanh nghiệp:
- Tên doanh nghiệp: {business_name}
- Lĩnh vực / Sản phẩm: {business_desc}
- Thông tin liên hệ / Kêu gọi hành động (CTA): {cta_contact}
- Phong cách tư vấn: {ai_tone}

Nhiệm vụ của bạn là đọc bài đăng dưới đây từ một hội nhóm Facebook và đánh giá:
1. Người đăng bài có nhu cầu THẬT SỰ tìm kiếm/mua sắm/thuê/hỏi dịch vụ liên quan đến lĩnh vực của doanh nghiệp hay không?
(Loại bỏ ngay: bài spam bán hàng, bài tuyển dụng đa cấp, bài quảng cáo, bài tâm sự không liên quan).
2. Điểm số tiềm năng (0 đến 100): 
   - 80-100: Nhu cầu rất rõ ràng, cần gấp, hỏi địa chỉ/báo giá.
   - 50-79: Đang tham khảo hoặc có nhu cầu liên quan.
   - Dưới 50: Không phải khách tiềm năng hoặc bài đăng bán.
3. Tóm tắt ngắn gọn nhu cầu (intent) dưới 20 từ.
4. Mức độ cấp bách (urgency): "Cao", "Trung bình", "Thấp".
5. Soạn một câu bình luận (suggested_reply) trả lời cực kỳ tự nhiên, tế nhị, hữu ích, khéo léo giới thiệu giải pháp và chèn thông tin liên hệ. Không trả lời kiểu bot cứng nhắc.

--- BÀI ĐĂNG CẦN PHÂN TÍCH ---
Hội nhóm: {group_name}
Nội dung:
\"\"\"{post_text}\"\"\"

Hãy trả lời DUY NHẤT một chuỗi JSON hợp lệ không bọc trong markdown theo mẫu:
{{
  "is_lead": true hoặc false,
  "score": số điểm từ 0 đến 100,
  "intent": "Tóm tắt nhu cầu ở đây",
  "urgency": "Cao" hoặc "Trung bình" hoặc "Thấp",
  "suggested_reply": "Câu bình luận gợi ý tại đây"
}}
"""
        try:
            response = client.models.generate_content(
                model=DEFAULT_MODEL,
                contents=prompt
            )
            raw_text = response.text.strip()
            # Clean markdown code blocks if any
            clean_json = re.sub(r"^```json\s*", "", raw_text, flags=re.MULTILINE)
            clean_json = re.sub(r"\s*```$", "", clean_json, flags=re.MULTILINE)
            data = json.loads(clean_json)
            return data
        except Exception as e:
            log_activity("AI_ENGINE", f"Gemini API call thất bại ({e}), chuyển sang chế độ phân tích quy tắc dự phòng.", level="WARNING")

    # 2. CHẾ ĐỘ PHÂN TÍCH DỰ PHÒNG (Rule-based Fallback) khi chưa có API key hoặc lỗi mạng
    keywords_raw = settings.get("target_keywords", "cần tìm, cần mua, giá bao nhiêu, ai bán, cần thuê, tư vấn giúp, ib mình")
    keywords = [k.strip().lower() for k in keywords_raw.split(",") if k.strip()]
    
    post_lower = post_text.lower()
    matched_kw = [kw for kw in keywords if kw in post_lower]
    
    # Kiểm tra dấu hiệu spam/bán hàng (nếu có giá bán, tuyển sỉ, tuyển dụng...)
    spam_signals = ["tuyển dụng", "tuyển đại lý", "hoa hồng", "thu nhập thụ động", "bán gấp sỉ", "cam kết hoàn vốn"]
    is_spam = any(s in post_lower for s in spam_signals)
    
    if matched_kw and not is_spam:
        score = min(50 + len(matched_kw) * 15, 95)
        intent = f"Khách tìm kiếm dịch vụ (từ khóa: {', '.join(matched_kw[:3])})"
        urgency = "Cao" if score >= 80 else "Trung bình"
        suggested_reply = f"Chào bạn, bên mình chuyên hỗ trợ về {business_name}. {cta_contact}"
        return {
            "is_lead": True,
            "score": score,
            "intent": intent,
            "urgency": urgency,
            "suggested_reply": suggested_reply
        }
    else:
        return {
            "is_lead": False,
            "score": 20,
            "intent": "Bài chia sẻ thông thường hoặc tin bán hàng",
            "urgency": "Thấp",
            "suggested_reply": ""
        }

def spin_post_content(base_content: str, count: int = 3) -> List[str]:
    """
    Dùng AI để tạo các biến thể nội dung bài đăng khác nhau nhằm tránh trùng lặp.
    """
    client = get_gemini_client()
    if client:
        prompt = f"""
Bạn là chuyên gia Copywriting. Hãy viết lại bài đăng dưới đây thành {count} biến thể khác nhau về cách diễn đạt, cấu trúc câu và icon, nhưng giữ nguyên thông điệp chính và thông tin liên hệ.
Mỗi biến thể phù hợp để đăng lên các nhóm Facebook khác nhau nhằm không bị Facebook tính là spam trùng lặp.

--- BÀI GỐC ---
{base_content}

Trả về DUY NHẤT một chuỗi JSON dạng mảng danh sách các bài viết:
["Nội dung biến thể 1", "Nội dung biến thể 2", "Nội dung biến thể 3"]
"""
        try:
            response = client.models.generate_content(
                model=DEFAULT_MODEL,
                contents=prompt
            )
            raw = response.text.strip()
            clean_json = re.sub(r"^```json\s*", "", raw, flags=re.MULTILINE)
            clean_json = re.sub(r"\s*```$", "", clean_json, flags=re.MULTILINE)
            return json.loads(clean_json)
        except Exception as e:
            log_activity("AI_ENGINE", f"Lỗi spin bài viết bằng Gemini: {e}", level="WARNING")
            
    # Fallback spin
    variations = [base_content]
    for i in range(1, count):
        variations.append(f"【Thông báo {i}】\n{base_content}\n\n#marketing #tudonghoa")
    return variations

def parse_agent_natural_command(user_command: str) -> Dict[str, Any]:
    """
    Phân tích câu lệnh bằng ngôn ngữ tự nhiên của người dùng và lập kế hoạch thực thi (Action Plan).
    Giống tính năng Trợ lý Agent trong Orbitama.
    """
    client = get_gemini_client()
    if client:
        prompt = f"""
Bạn là Tổng chỉ huy AI Marketing Agent. Người dùng vừa giao việc bằng ngôn ngữ tự nhiên:
\"\"\"{user_command}\"\"\"

Hãy phân tích mục tiêu của người dùng và lập ra một Kế hoạch hành động từng bước (Action Plan).
Các loại hành động có thể bao gồm:
- scrape: Quét bài viết từ nhóm Facebook
- filter: AI đọc hiểu và lọc ra các bài có nhu cầu thật sự
- comment: Soạn thảo và tự động bình luận tiếp cận khách
- post: Lên lịch đăng bài tự động đa nhóm
- join: Tìm kiếm và xin gia nhập nhóm mới

Trả về DUY NHẤT một chuỗi JSON hợp lệ theo định dạng:
{{
  "title": "Tên kế hoạch ngắn gọn",
  "summary": "Tóm tắt mục tiêu kế hoạch",
  "primary_action": "scrape" hoặc "post" hoặc "comment" hoặc "join",
  "steps": [
    {{"id": 1, "name": "Tên bước 1", "desc": "Mô tả chi tiết việc làm"}},
    {{"id": 2, "name": "Tên bước 2", "desc": "Mô tả chi tiết việc làm"}},
    {{"id": 3, "name": "Tên bước 3", "desc": "Mô tả chi tiết việc làm"}}
  ],
  "target_keyword": "từ khóa trích xuất nếu có",
  "estimated_time": "1 - 3 phút"
}}
"""
        try:
            response = client.models.generate_content(
                model=DEFAULT_MODEL,
                contents=prompt
            )
            raw = response.text.strip()
            clean_json = re.sub(r"^```json\s*", "", raw, flags=re.MULTILINE)
            clean_json = re.sub(r"\s*```$", "", clean_json, flags=re.MULTILINE)
            return json.loads(clean_json)
        except Exception as e:
            log_activity("AI_ENGINE", f"Lỗi Gemini lập kế hoạch: {e}", level="WARNING")

    # Fallback plan
    cmd_lower = user_command.lower()
    if "đăng" in cmd_lower or "post" in cmd_lower:
        return {
            "title": "Kế hoạch Đăng bài đa nhóm tự động",
            "summary": f"Chuẩn bị nội dung và phân phối tự động theo yêu cầu: '{user_command}'",
            "primary_action": "post",
            "steps": [
                {"id": 1, "name": "Chuẩn bị nội dung & Spin", "desc": "AI tạo biến thể bài đăng để tránh trùng lặp"},
                {"id": 2, "name": "Chọn tài khoản và nhóm", "desc": "Điều phối nick và xếp lịch giãn cách an toàn"},
                {"id": 3, "name": "Phân phối bài đăng", "desc": "Tiến hành đăng bài vào các nhóm chỉ định"}
            ],
            "target_keyword": "marketing",
            "estimated_time": "2 phút"
        }
    else:
        return {
            "title": "Kế hoạch Săn khách tiềm năng từ Nhóm",
            "summary": f"Khai thác và phân tích cơ hội từ nhóm theo lệnh: '{user_command}'",
            "primary_action": "scrape",
            "steps": [
                {"id": 1, "name": "Quét bài viết nhóm mục tiêu", "desc": "Lấy danh sách các thảo luận và bài đăng mới nhất"},
                {"id": 2, "name": "AI Lọc bài có nhu cầu thật", "desc": "Đọc hiểu ngữ cảnh, loại bỏ spam, chấm điểm Lead"},
                {"id": 3, "name": "Soạn sẵn câu trả lời & Tiếp cận", "desc": "Chuẩn bị phản hồi tư vấn sát nhu cầu từng khách"}
            ],
            "target_keyword": "tìm kiếm",
            "estimated_time": "1 - 2 phút"
        }

