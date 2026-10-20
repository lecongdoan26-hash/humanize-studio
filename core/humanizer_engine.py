"""
Module: Humanizer Engine (Bộ não chuẩn hóa & thổi hồn nội dung AI)
Tối ưu hóa chuyên sâu cho ngữ cảnh Tiếng Việt.
"""

import re
import math
from typing import Dict, Any, List, Optional
from core.config import get_env_setting, DEFAULT_MODEL
from core.database import get_settings, log_activity

# Danh mục các sáo ngữ đặc trưng của AI tiếng Việt (AI Clichés)
VIETNAMESE_AI_CLICHES = [
    # Mở đầu / Bối cảnh sáo mòn
    "trong kỷ nguyên số", "trong thời đại số", "trong bối cảnh hiện nay", 
    "trong bối cảnh thời đại", "trong thời đại 4.0", "hiện nay, khi mà",
    "như chúng ta đã biết", "không thể phủ nhận rằng", "chắc hẳn ai trong chúng ta",
    
    # Từ ngữ nâng tầm vô thưởng vô phạt
    "đóng vai trò quan trọng", "đóng vai trò then chốt", "đóng vai trò không thể thiếu",
    "là chìa khóa vàng", "chìa khóa vạn năng", "bức tranh toàn cảnh",
    "vô hình trung", "là một phần không thể tách rời", "không ngừng phát triển",
    "nâng cao chất lượng", "mang lại những giá trị vượt trội", "tạo nên bước ngoặt",
    "bước đệm vững chắc", "mảnh đất màu mỡ", "bước tiến vượt bậc",
    
    # Kêu gọi / Kết thúc rập khuôn
    "hãy cùng chúng tôi khám phá", "hãy cùng khám phá", "chần chừ gì nữa",
    "tóm lại", "nhìn chung lại", "nói tóm lại", "sau tất cả",
    "hy vọng bài viết này sẽ mang lại", "chúc các bạn thành công",
    
    # Cấu trúc câu nước đôi / trung lập giả tạo
    "tuy nhiên, cần lưu ý rằng", "mặt khác cũng cần", "cần cân nhắc kỹ lưỡng"
]

def audit_vietnamese_ai_text(text: str) -> Dict[str, Any]:
    """
    Quét và chẩn đoán văn bản để tìm các dấu vết của AI:
    - Tìm các từ ngữ sáo rỗng (clichés)
    - Phân tích nhịp điệu câu (sentence length variance & burstiness)
    - Đánh giá ước lượng điểm 'AI Smell' (Độ nặng mùi AI)
    """
    if not text or not text.strip():
        return {
            "ai_score": 0,
            "clichés_found": [],
            "burstiness_score": 100,
            "sentence_stats": {"total": 0, "avg_words": 0, "std_dev": 0},
            "feedback": ["Vui lòng nhập văn bản để chẩn đoán."]
        }

    raw_text = text.strip()
    lower_text = raw_text.lower()
    
    # 1. Quét tìm sáo ngữ
    found_cliches = []
    for phrase in VIETNAMESE_AI_CLICHES:
        # Tìm tất cả vị trí xuất hiện
        matches = [m.start() for m in re.finditer(re.escape(phrase), lower_text)]
        if matches:
            found_cliches.append({
                "phrase": phrase,
                "count": len(matches)
            })
            
    total_cliche_count = sum(c["count"] for c in found_cliches)

    # 2. Phân tích nhịp điệu câu (Burstiness)
    # Tách câu dựa trên dấu chấm, chấm than, hỏi chấm, xuống dòng
    sentences = [s.strip() for s in re.split(r'[.!?\n]+', raw_text) if len(s.strip()) > 3]
    total_sentences = len(sentences)
    
    sentence_lengths = [len(s.split()) for s in sentences] if sentences else [0]
    avg_words = sum(sentence_lengths) / total_sentences if total_sentences > 0 else 0
    
    if total_sentences > 1:
        variance = sum((x - avg_words) ** 2 for x in sentence_lengths) / total_sentences
        std_dev = math.sqrt(variance)
    else:
        std_dev = 0
        
    # Độ biến thiên nhịp điệu (Burstiness Score):
    # Người viết tự nhiên: std_dev thường cao (có câu ngắn 3 từ, câu dài 25 từ) -> std_dev/avg_words >= 0.5
    # AI viết: std_dev rất thấp (các câu đều tăm tắp từ 15-20 từ) -> std_dev/avg_words < 0.35
    ratio = (std_dev / avg_words) if avg_words > 0 else 0
    # Thang điểm burstiness từ 0 đến 100 (càng cao càng giống người)
    burstiness_score = min(100, int(ratio * 140))
    
    # 3. Tính điểm "Mùi AI" (AI Smell Score: 0 -> 100%)
    # Càng nhiều sáo ngữ + nhịp điệu càng đều -> điểm AI càng cao
    base_score = 30
    if total_cliche_count > 0:
        base_score += min(45, total_cliche_count * 12)
        
    if burstiness_score < 40:
        base_score += 25
    elif burstiness_score < 60:
        base_score += 15
    else:
        base_score -= 10
        
    # Kiểm tra mở đầu rập khuôn
    first_paragraph = raw_text.split("\n")[0].lower()
    if any(p in first_paragraph for p in ["trong kỷ nguyên", "trong bối cảnh", "không thể phủ nhận"]):
        base_score += 15
        
    ai_score = max(5, min(98, base_score))
    
    # 4. Đưa ra nhận xét cụ thể
    feedback = []
    if total_cliche_count > 0:
        feedback.append(f"Phát hiện {total_cliche_count} cụm từ sáo ngữ AI điển hình (như '{found_cliches[0]['phrase']}'). Cần thay bằng cách diễn đạt tự nhiên hơn.")
    else:
        feedback.append("Không phát hiện sáo ngữ AI phổ biến. Rất tốt!")
        
    if burstiness_score < 45:
        feedback.append("Độ dài các câu quá đồng đều (thiếu nhịp thở tự nhiên). Hãy ngắt bớt câu ngắn và xen kẽ câu đàm thoại.")
    else:
        feedback.append("Nhịp điệu câu có độ co giãn tốt, mang cảm giác viết của con người.")
        
    if ai_score >= 70:
        status_label = "Nguy cơ cao bị nhận diện là AI (Rất dễ flop / bị quét)"
        status_color = "red"
    elif ai_score >= 40:
        status_label = "Có mùi AI trung bình (Cần biên tập gọt giũa)"
        status_color = "yellow"
    else:
        status_label = "Tự nhiên, mang phong cách người viết thật"
        status_color = "green"

    return {
        "ai_score": ai_score,
        "status_label": status_label,
        "status_color": status_color,
        "cliches_found": found_cliches,
        "total_cliches": total_cliche_count,
        "burstiness_score": burstiness_score,
        "sentence_stats": {
            "total_sentences": total_sentences,
            "avg_words_per_sentence": round(avg_words, 1),
            "std_dev": round(std_dev, 1)
        },
        "feedback": feedback
    }


def get_humanizer_client(custom_api_key: Optional[str] = None):
    """Khởi tạo Gemini Client từ key tùy chỉnh hoặc .env"""
    api_key = custom_api_key or get_env_setting("GEMINI_API_KEY") or get_settings().get("gemini_api_key", "")
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        log_activity("HUMANIZER", f"Lỗi khởi tạo Gemini client: {e}", level="ERROR")
        return None


def generate_humanized_content(
    text: str,
    mode: str = "social_mkt",
    intensity: str = "balanced",
    custom_tone: str = "",
    custom_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Thực hiện chuẩn hóa văn bản AI thành văn phong người viết thật.
    Modes:
      - 'academic': Luận văn, tiểu luận, nghiên cứu học thuật
      - 'social_mkt': Content Marketing, bài đăng Facebook/TikTok/Threads
      - 'blog_seo': Bài viết Blog, website, chuẩn E-E-A-T
    """
    if not text or not text.strip():
        return {"success": False, "error": "Văn bản trống."}

    client = get_humanizer_client(custom_api_key)
    if not client:
        return {
            "success": False,
            "error": "Chưa có Gemini API Key. Vui lòng nhập API Key để kích hoạt bộ não AI."
        }

    # Định nghĩa cấu hình chỉ đạo cho từng Chế độ
    mode_instructions = {
        "academic": """
MỤC TIÊU: Chuẩn hóa bài viết học thuật / luận văn / tiểu luận nghiên cứu.
QUY TẮC CỐT LÕI:
1. KHÔNG tự bịa nguồn trích dẫn hoặc số liệu ảo (chống Hallucination).
2. XÓA BỎ các sáo ngữ rập khuôn: "không thể phủ nhận rằng", "bước đệm vững chắc", "như một tất yếu".
3. Dùng câu văn học thuật tiếng Việt chuẩn mực, mạch lạc, có tính phản biện logic sắc bén.
4. Diễn đạt có chiều sâu chuyên ngành, lập luận chặt chẽ thay vì liệt kê gạch đầu dòng hời hợt.
""",
        "social_mkt": """
MỤC TIÊU: Chuẩn hóa bài viết Content Marketing / Facebook / Threads / Mạng xã hội.
QUY TẮC CỐT LÕI:
1. 2 CÂU ĐẦU TIÊN CỰC KỲ QUAN TRỌNG: Tạo Hook mạnh mẽ, đâm trúng nỗi đau (pain point) hoặc sự tò mò. Tuyệt đối không mở đầu bằng: "Trong kỷ nguyên số...", "Bạn có biết...", "Hôm nay mình chia sẻ...".
2. NHỊP ĐIỆU CÂU BẬT NHẢ (BURSTINESS): Xen kẽ câu cực ngắn và câu vừa phải. Đọc lên phải có nhạc tính và nhịp thở của người nói chuyện thật.
3. TIẾNG VIỆT ĐỜI THƯỜNG: Dùng từ ngữ tự nhiên, gần gũi, dí dỏm hoặc sâu sắc. Cắt tỉa bớt các icon emoji thừa thãi đầu mỗi dòng.
4. TẬP TRUNG VÀO INSIGHT NGẦM: Nói điều khách hàng cảm thấy nhưng chưa bao giờ tự diễn đạt thành lời.
""",
        "blog_seo": """
MỤC TIÊU: Chuẩn hóa bài viết Blog Website chuẩn Google E-E-A-T (Trải nghiệm - Chuyên môn - Đáng tin cậy).
QUY TẮC CỐT LÕI:
1. VÀO THẲNG SEARCH INTENT: Mở bài trả lời ngay thắc mắc chính của người tìm kiếm trong 3-4 câu đầu, không dài dòng triết lý.
2. THÊM YẾU TỐ TRẢI NGHIỆM THẬT (FIRSTHAND EXPERIENCE): Đưa vào các mẹo thực tế, các lỗi hay gặp (troubleshooting), góc nhìn chuyên gia thực chiến.
3. CẤU TRÚC TỰ NHIÊN: Tiêu đề H2, H3 hấp dẫn, không rập khuôn kiểu từ điển/sách giáo khoa.
4. XÓA BỎ NỘI DUNG RỖNG (FLUFF CONTENT): Mọi đoạn văn đều phải mang lại giá trị thông tin thực tế.
"""
    }

    selected_instruction = mode_instructions.get(mode, mode_instructions["social_mkt"])

    intensity_instruction = ""
    if intensity == "light":
        intensity_instruction = "MỨC ĐỘ CAN THIỆP NHẸ (Light): Giữ lại 80% từ ngữ và cấu trúc gốc, chỉ gọt tỉa các sáo ngữ AI, bẻ nhỏ câu quá dài và làm câu văn mượt mà hơn."
    elif intensity == "creative":
        intensity_instruction = "MỨC ĐỘ LỘT XÁC TOÀN DIỆN (Deep Re-write): Tái cấu trúc hoàn toàn, viết lại như một chuyên gia hàng đầu giàu kinh nghiệm thực chiến với giọng văn cực kỳ cuốn hút, độc đáo."
    else:
        intensity_instruction = "MỨC ĐỘ CÂN BẰNG (Balanced): Giữ trọn vẹn thông điệp gốc, nhưng viết lại câu từ tự nhiên, thổi hồn cảm xúc và nhịp điệu sinh động của con người."

    tone_prompt = f"- Phong cách / Giọng văn mong muốn: {custom_tone}" if custom_tone else "- Phong cách: Tự nhiên, chân thật, giàu cảm xúc và đáng tin cậy."

    prompt = f"""
Bạn là Chuyên gia Biên tập Nội dung & Ngôn ngữ học Tiếng Việt hàng đầu (Human Content Stylist).
Nhiệm vụ của bạn là nhận một văn bản thô do AI viết (đang bị cứng nhắc, rập khuôn, lộ mùi máy móc) và CHUẨN HÓA THÀNH PHIÊN BẢN DO CON NGƯỜI VIẾT THẬT SỰ.

--- HƯỚNG DẪN CHUYÊN BIỆT CHO CHẾ ĐỘ ---
{selected_instruction}

--- MỨC ĐỘ CAN THIỆP ---
{intensity_instruction}
{tone_prompt}

--- CÁC TỪ TUYỆT ĐỐI KHÔNG ĐƯỢC DÙNG (AI Clichés cấm) ---
Không được dùng các từ: "trong kỷ nguyên số", "đóng vai trò quan trọng", "không thể phủ nhận rằng", "bức tranh toàn cảnh", "chìa khóa vàng", "hãy cùng khám phá", "vô hình trung", "tóm lại", "nhìn chung lại".

--- VĂN BẢN AI CẦN CHUẨN HÓA ---
\"\"\"{text}\"\"\"

YÊU CẦU ĐẦU RA:
Trả về văn bản đã chuẩn hóa hoàn chỉnh bằng Tiếng Việt. 
Không thêm lời giải thích mào đầu (như "Dưới đây là bài viết..."), không để trong khối code markdown backtick, chỉ trả về nội dung hoàn thiện nhất.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        humanized_text = response.text.strip()
        
        # Chẩn đoán lại bài viết sau khi chuẩn hóa để so sánh
        audit_before = audit_vietnamese_ai_text(text)
        audit_after = audit_vietnamese_ai_text(humanized_text)
        
        return {
            "success": True,
            "original_text": text,
            "humanized_text": humanized_text,
            "audit_before": audit_before,
            "audit_after": audit_after,
            "mode": mode,
            "intensity": intensity
        }
    except Exception as e:
        log_activity("HUMANIZER", f"Lỗi khi xử lý bằng Gemini: {e}", level="ERROR")
        return {
            "success": False,
            "error": f"Lỗi xử lý AI: {str(e)}"
        }
