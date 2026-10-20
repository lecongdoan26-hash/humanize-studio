"""
Module: Humanizer Engine (Bộ não chuẩn hóa & thổi hồn nội dung AI)
Tối ưu hóa chuyên sâu cho ngữ cảnh Tiếng Việt.
"""

import re
import math
from typing import Dict, Any, List, Optional
from core.config import get_env_setting, DEFAULT_MODEL, FALLBACK_MODELS
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


def markdown_to_clean_text(md: str) -> str:
    """
    Loại bỏ triệt để các ký tự markdown (#, **, *, ---, `) để trả về văn bản sạch 100%.
    Người dùng chỉ việc copy về dán thẳng vào ứng dụng không hỗ trợ markdown.
    """
    if not md:
        return ""
    lines = md.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped in ["---", "***", "___"]:
            cleaned_lines.append("")
            continue
        # Bỏ dấu # ở đầu dòng
        line = re.sub(r"^#{1,6}\s*", "", line)
        # Bỏ in đậm **...** và __...__
        line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
        line = re.sub(r"__(.*?)__", r"\1", line)
        # Bỏ in nghiêng *...*
        line = re.sub(r"(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)", r"\1", line)
        # Bỏ dấu trích dẫn >
        line = re.sub(r"^>\s*", "", line)
        # Bỏ inline code `
        line = re.sub(r"`(.*?)`", r"\1", line)
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def markdown_to_rich_html(md: str) -> str:
    """
    Chuyển đổi Markdown sang Semantic HTML chuẩn (kèm inline style tối ưu cho Word & Google Docs & CMS).
    Hỗ trợ H1, H2, H3, in đậm, danh sách gạch đầu dòng, meta description box.
    """
    if not md:
        return ""
    
    html_lines = []
    in_ul = False
    in_ol = False
    
    def close_lists():
        nonlocal in_ul, in_ol
        res = []
        if in_ul:
            res.append("</ul>")
            in_ul = False
        if in_ol:
            res.append("</ol>")
            in_ol = False
        return res

    for raw_line in md.split("\n"):
        line = raw_line.rstrip()
        stripped = line.strip()
        
        if not stripped:
            html_lines.extend(close_lists())
            continue

        # Đường kẻ ngang
        if stripped in ["---", "***", "___"]:
            html_lines.extend(close_lists())
            html_lines.append("<hr style='border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;'/>")
            continue

        # Thẻ H1
        if stripped.startswith("# "):
            html_lines.extend(close_lists())
            content = stripped[2:].strip()
            content = re.sub(r"\*\*(.*?)\*\*", r"\1", content)
            html_lines.append(f"<h1 style='font-size: 24px; font-weight: 800; color: #0f172a; margin-top: 16px; margin-bottom: 12px; line-height: 1.3;'>{content}</h1>")
            continue

        # Thẻ H2
        if stripped.startswith("## "):
            html_lines.extend(close_lists())
            content = stripped[3:].strip()
            content = re.sub(r"\*\*(.*?)\*\*", r"\1", content)
            html_lines.append(f"<h2 style='font-size: 19px; font-weight: 700; color: #1e293b; margin-top: 24px; margin-bottom: 10px; line-height: 1.35;'>{content}</h2>")
            continue

        # Thẻ H3
        if stripped.startswith("### "):
            html_lines.extend(close_lists())
            content = stripped[4:].strip()
            content = re.sub(r"\*\*(.*?)\*\*", r"\1", content)
            html_lines.append(f"<h3 style='font-size: 16px; font-weight: 600; color: #334155; margin-top: 18px; margin-bottom: 8px;'>{content}</h3>")
            continue

        # Thẻ H4
        if stripped.startswith("#### "):
            html_lines.extend(close_lists())
            content = stripped[5:].strip()
            content = re.sub(r"\*\*(.*?)\*\*", r"\1", content)
            html_lines.append(f"<h4 style='font-size: 15px; font-weight: 600; color: #475569; margin-top: 14px; margin-bottom: 6px;'>{content}</h4>")
            continue

        # Meta Description Callout Box
        if stripped.lower().startswith("**meta description:**") or stripped.lower().startswith("meta description:"):
            html_lines.extend(close_lists())
            desc_body = re.sub(r"^\*{0,2}Meta Description:\*{0,2}\s*", "", stripped, flags=re.IGNORECASE)
            desc_body = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", desc_body)
            html_lines.append(f"<div style='background-color: #f0fdf4; border-left: 4px solid #16a34a; padding: 12px 16px; border-radius: 6px; margin: 16px 0; color: #166534; font-size: 14px;'><strong>Meta Description Chuẩn SEO:</strong> {desc_body}</div>")
            continue

        # Danh sách gạch đầu dòng (- hoặc *)
        if re.match(r"^[-*]\s+", stripped):
            if in_ol:
                html_lines.extend(close_lists())
            if not in_ul:
                html_lines.append("<ul style='padding-left: 20px; margin: 10px 0;'>")
                in_ul = True
            item_text = re.sub(r"^[-*]\s+", "", stripped)
            item_text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", item_text)
            item_text = re.sub(r"(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)", r"<em>\1</em>", item_text)
            html_lines.append(f"<li style='margin-bottom: 6px; color: #334155; line-height: 1.6;'>{item_text}</li>")
            continue

        # Danh sách số (1., 2...)
        num_match = re.match(r"^(\d+)\.\s+(.*)", stripped)
        if num_match:
            if in_ul:
                html_lines.extend(close_lists())
            if not in_ol:
                html_lines.append("<ol style='padding-left: 20px; margin: 10px 0;'>")
                in_ol = True
            item_text = num_match.group(2)
            item_text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", item_text)
            item_text = re.sub(r"(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)", r"<em>\1</em>", item_text)
            html_lines.append(f"<li style='margin-bottom: 6px; color: #334155; line-height: 1.6;'>{item_text}</li>")
            continue

        # Đoạn văn thông thường
        html_lines.extend(close_lists())
        para_text = stripped
        para_text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", para_text)
        para_text = re.sub(r"(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)", r"<em>\1</em>", para_text)
        html_lines.append(f"<p style='margin-bottom: 12px; color: #334155; line-height: 1.7; font-size: 15px;'>{para_text}</p>")

    html_lines.extend(close_lists())
    return "\n".join(html_lines)


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

    # Định nghĩa cấu hình chỉ đạo chuyên sâu cho từng Chế độ
    mode_instructions = {
        "blog_seo": """
MỤC TIÊU: Chuẩn hóa bài viết Blog / Website chuẩn Google E-E-A-T (Trải nghiệm - Chuyên môn - Đáng tin cậy) và tối ưu SEO Onpage hàng đầu.

QUY TẮC BỐ CỤC BÀI VIẾT BLOG WEBSITE CHUẨN SEO BẮT BUỘC:
1. TIÊU ĐỀ BÀI VIẾT (THẺ H1):
   - Đặt ở dòng đầu tiên, bắt đầu bằng '# [Tiêu đề bài viết H1]'.
   - Độ dài: 55-65 ký tự, hấp dẫn, chứa từ khóa chính ngay đầu, kích thích tỷ lệ click (CTR).
   - Chỉ có DUY NHẤT 1 thẻ H1 trong toàn bộ bài viết.
2. THẺ META DESCRIPTION:
   - Dòng tiếp theo: '**Meta Description:** [Đoạn tóm tắt 150-160 ký tự cuốn hút, chứa từ khóa chính/phụ và lời kêu gọi hành động]'.
3. ĐOẠN SAPO / MỞ BÀI (SEARCH INTENT HOOK):
   - 2-3 câu ngắn, trả lời ngay thắc mắc cốt lõi của người tìm kiếm (Search Intent), nêu rõ vấn đề thực tế và giải pháp bài viết cung cấp.
4. CÁC ĐỀ MỤC THÂN BÀI (THẺ H2 VÀ H3 PHÂN CẤP CHUẨN):
   - Sử dụng '## [Tiêu đề mục lớn H2]' cho các luận điểm chính (Đặc điểm, Bảng thông số, Hướng dẫn thi công, Tiêu chuẩn kỹ thuật, Báo giá...).
   - Sử dụng '### [Tiêu đề mục nhỏ H3]' cho các chi tiết kỹ thuật hoặc giải pháp cụ thể bên trong H2.
   - Các đoạn văn ngắn từ 2-4 câu để người đọc dễ theo dõi, thoáng mắt.
   - Sử dụng danh sách gạch đầu dòng '- ' cho các ưu điểm, tính năng, lưu ý.
   - In đậm '**từ khóa quan trọng**' và các thông số kỹ thuật cốt lõi một cách tự nhiên.
5. GÓC NHÌN CHUYÊN GIA / KINH NGHIỆM THỰC CHIẾN (E-E-A-T):
   - Thêm phần kinh nghiệm thực tế, các lỗi hay gặp khi thi công/sử dụng và cách phòng tránh để bài viết có giá trị vượt trội so với bài AI thông thường.
6. KẾT LUẬN & KÊU GỌI HÀNH ĐỘNG (CTA):
   - Đề mục H2: '## Kết Luận & Tư Vấn Báo Giá' tóm tắt giá trị và kêu gọi độc giả liên hệ.
7. CÂU HỎI THƯỜNG GẶP (FAQ CHUẨN SEO SCHEMA):
   - Đề mục H2: '## Câu Hỏi Thường Gặp Về [Chủ Đề]' kèm 2-3 câu hỏi dạng H3 và câu trả lời súc tích.
""",
        "social_mkt": """
MỤC TIÊU: Chuẩn hóa bài viết Content Marketing / Facebook / Threads / Mạng xã hội chuyên nghiệp.

QUY TẮC ĐỊNH DẠNG MẠNG XÃ HỘI:
- TUYỆT ĐỐI KHÔNG dùng dấu thăng '# ' hay '## ' làm tiêu đề (vì trên Facebook/Threads/TikTok dấu # sẽ biến thành hashtag rác làm hỏng bài viết).
- Tiêu đề chính và các đề mục phụ viết HOA TOÀN BỘ hoặc in đậm '**...**' nổi bật.

BỐ CỤC CHUẨN MARKETING VIRAL & CHUYỂN ĐỔI:
1. HEADLINE HOOK (1-2 DÒNG ĐẦU TIÊN):
   - Viết HOA toàn bộ, có emoji đắt giá ở đầu (ví dụ: 🔥, ❌, ⚠️, 💡).
   - Đâm trúng nỗi đau (Pain Point), sự tò mò hoặc cảnh báo sai lầm tốn tiền để độc giả bấm "Xem thêm...".
   - Tuyệt đối không mở bài rập khuôn sáo rỗng: "Trong kỷ nguyên số...", "Hôm nay mình xin chia sẻ...".
2. CẦU NỐI ĐỒNG CẢM & KHƠI GỢI VẤN ĐỀ (AGITATION):
   - 2-3 câu ngắn ngắt dòng thoáng đãng, đánh trúng tâm lý bực mình hoặc mong muốn của khách hàng.
   - Nhịp điệu câu bật nhả tự nhiên, đọc lên có cảm xúc của người nói chuyện thật.
3. GIẢI PHÁP & LỢI ÍCH CỐT LÕI (CORE VALUE):
   - Trình bày dạng gạch đầu dòng kèm emoji tinh tế đầu dòng (ví dụ: 👉, ✔️, ⚡).
   - Nêu rõ lợi ích khách hàng nhận được (tiết kiệm chi phí, bền đẹp, thẩm mỹ cao), không chỉ liệt kê thông số khô khan.
4. LỜI KÊU GỌI HÀNH ĐỘNG DỨT KHOÁT (CALL TO ACTION - CTA):
   - 1 câu CTA rõ ràng: "Nhắn tin cho xưởng để nhận bảng giá sỉ", "Để lại bình luận...", "Gọi ngay hotline...".
5. THÔNG TIN LIÊN HỆ & BỘ HASHTAG NGÀNH:
   - Thông tin xưởng/hotline/website gọn gàng.
   - 3-5 hashtag thương hiệu và ngành hàng ở dòng cuối cùng (ví dụ: #NoiThatGiaXuong #VitInox304).
""",
        "academic": """
MỤC TIÊU: Chuẩn hóa bài viết Học thuật / Luận văn / Tiểu luận nghiên cứu khoa học chuẩn mực.

QUY TẮC ĐỊNH DẠNG HỌC THUẬT:
- Dùng hệ thống số đề mục chuẩn khoa học: 1. -> 1.1. -> 1.1.1. -> 2. -> 2.1...
- Các đề mục in đậm '**1. TÊN ĐỀ MỤC**', TUYỆT ĐỐI KHÔNG dùng dấu thăng '# ' và KHÔNG dùng emoji.
- Không tự bịa nguồn trích dẫn hoặc số liệu ảo (chống Hallucination).

BỐ CỤC CHUẨN LUẬN VĂN KHOA HỌC:
1. TIÊU ĐỀ ĐỀ TÀI NGHIÊN CỨU:
   - Viết hoa toàn bộ, trang trọng, cô đọng, thể hiện chính xác đối tượng và phạm vi nghiên cứu.
2. 1. ĐẶT VẤN ĐỀ VÀ TÍNH CẤP THIẾT CỦA ĐỀ TÀI:
   - Bối cảnh nghiên cứu, khoảng trống tri thức, mục tiêu và ý nghĩa thực tiễn của đề tài.
3. 2. CƠ SỞ LÝ LUẬN VÀ TỔNG QUAN TÀI LIỆU NGHIÊN CỨU:
   - Hệ thống hóa các khái niệm nền tảng, cơ sở lý thuyết và các nghiên cứu tiêu biểu đi trước.
4. 3. NỘI DUNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU (PHÂN TÍCH THỰC TRẠNG):
   - Đánh số mục phân cấp 3.1, 3.2 khoa học; phân tích logic chặt chẽ, luận cứ xác đáng, có tính phản biện.
5. 4. ĐÁNH GIÁ VÀ THẢO LUẬN KẾT QUẢ:
   - Đánh giá những ưu điểm, hạn chế và nguyên nhân cốt lõi.
6. 5. KẾT LUẬN VÀ HỆ THỐNG GIẢI PHÁP / ĐỀ XUẤT KHUYẾN NGHỊ:
   - Đưa ra các khuyến nghị khả thi, gắn liền với thực tiễn và định hướng phát triển tiếp theo.
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

    candidate_models = [DEFAULT_MODEL] + [m for m in FALLBACK_MODELS if m != DEFAULT_MODEL]
    humanized_text = ""
    last_error = None

    for target_model in candidate_models:
        try:
            response = client.models.generate_content(
                model=target_model,
                contents=prompt,
            )
            if response and response.text:
                humanized_text = response.text.strip()
                break
        except Exception as err:
            last_error = err
            log_activity("HUMANIZER", f"Thử model {target_model} thất bại ({err}), chuyển sang model tiếp theo.", level="WARNING")
            continue

    if not humanized_text:
        log_activity("HUMANIZER", f"Tất cả các model Gemini đều thất bại: {last_error}", level="ERROR")
        return {
            "success": False,
            "error": f"Lỗi xử lý AI: {str(last_error)}"
        }

    # Chẩn đoán lại bài viết sau khi chuẩn hóa để so sánh
    audit_before = audit_vietnamese_ai_text(text)
    audit_after = audit_vietnamese_ai_text(humanized_text)
    
    # Chuyển đổi sang phiên bản văn bản sạch (đã gọt sạch #, **) và HTML định dạng chuẩn
    clean_text = markdown_to_clean_text(humanized_text)
    humanized_html = markdown_to_rich_html(humanized_text)
    
    return {
        "success": True,
        "original_text": text,
        "humanized_text": humanized_text,
        "clean_text": clean_text,
        "humanized_html": humanized_html,
        "audit_before": audit_before,
        "audit_after": audit_after,
        "mode": mode,
        "intensity": intensity
    }
