import sqlite3
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'data/mkt_system.db'

groups_data = [
    {
        "name": "Việc Làm Marketing Media Đà Nẵng Xịn Chất",
        "url": "https://www.facebook.com/groups/vieclammarketingmediadanang",
        "category": "Tuyển dụng Marketing & Media",
        "member_count": "45.000+"
    },
    {
        "name": "Việc Làm Marketing Đà Nẵng (Media, Content, Ads, SEO)",
        "url": "https://www.facebook.com/groups/vieclammarketingdanang",
        "category": "Marketing Đà Nẵng",
        "member_count": "38.000+"
    },
    {
        "name": "Cộng Đồng Digital Marketing Đà Nẵng",
        "url": "https://www.facebook.com/groups/digitalmarketingdanang",
        "category": "Digital Marketing",
        "member_count": "29.000+"
    },
    {
        "name": "Tuyển Dụng Đà Nẵng - Việc Làm Đà Nẵng (Danang43)",
        "url": "https://www.facebook.com/groups/danang43",
        "category": "Tuyển dụng tổng hợp",
        "member_count": "150.000+"
    },
    {
        "name": "Hội Tìm Việc Làm Marketing - Truyền Thông Đà Nẵng",
        "url": "https://www.facebook.com/groups/hoituyenmarketingdanang",
        "category": "Marketing & Media",
        "member_count": "22.000+"
    }
]

jobs_data = [
    {
        "group_name": "Việc Làm Marketing Media Đà Nẵng Xịn Chất",
        "author_name": "HR Vibe Coffee (Nhân Sự)",
        "author_url": "https://www.facebook.com/groups/vieclammarketingmediadanang",
        "post_url": "https://danang43.vn/vibe-coffee-tuyen-marketing-team-leader",
        "post_content": """[ĐÀ NẴNG - TUYỂN GẤP] MARKETING TEAM LEADER (LƯƠNG 10 - 15 TRIỆU)
🏠 Đơn vị tuyển dụng: VIBE COFFEE
📍 Địa điểm làm việc: 04 Nguyễn Nhàn, P. Hòa Thọ Đông, Q. Cẩm Lệ, TP. Đà Nẵng
💰 Mức lương: 10.000.000đ - 15.000.000đ/tháng (Thỏa thuận theo năng lực) + Thưởng KPI doanh số chuỗi.
⏰ Thời gian: Giờ hành chính.

📌 MÔ TẢ CÔNG VIỆC:
- Xây dựng và triển khai chiến lược Marketing đa kênh (Facebook, TikTok, Instagram, YouTube, Website, Google Ads...) cho hệ thống Vibe Coffee.
- Nghiên cứu thị trường F&B, hành vi khách hàng và các đối thủ cạnh tranh tại khu vực miền Trung.
- Quản lý, đào tạo và phân công nhiệm vụ cho đội ngũ nhân sự Marketing (Content, Designer, Media).
- Định hướng sản xuất nội dung visual, viral video TikTok/Reels thu hút khách hàng trải nghiệm tại quán.
- Chịu trách nhiệm về KPI tiếp cận, tương tác và tỷ lệ tăng trưởng doanh thu theo chiến dịch.

📌 YÊU CẦU:
- Tối thiểu 1-2 năm kinh nghiệm ở vị trí tương đương hoặc Senior Marketing (ưu tiên ngành F&B, bán lẻ).
- Tư duy chiến lược tốt, am hiểu sâu về Digital Marketing & xây dựng thương hiệu.
- Kỹ năng lãnh đạo, phân công công việc và giải quyết vấn đề hiệu quả.""",
        "ai_score": 98,
        "ai_intent": "Tuyển Marketing Team Leader chuỗi F&B (10-15tr)",
        "ai_urgency": "Cao",
        "ai_suggested_reply": "Chào anh/chị HR Vibe Coffee! Mình có hơn 2 năm kinh nghiệm Leader/Senior Marketing mảng F&B và bán lẻ tại Đà Nẵng, từng triển khai chiến dịch đa kênh đạt tăng trưởng doanh số 35%. Mình xin phép gửi CV chi tiết qua inbox/zalo để trao đổi thêm ạ."
    },
    {
        "group_name": "Cộng Đồng Digital Marketing Đà Nẵng",
        "author_name": "Tuyển Dụng Leadsmax Group",
        "author_url": "https://www.facebook.com/groups/digitalmarketingdanang",
        "post_url": "https://danang43.vn/leadsmax-group-tuyen-tiktok-ads-specialist",
        "post_content": """[ĐÀ NẴNG] CẦN TUYỂN TIKTOK ADS SPECIALIST (THỊ TRƯỜNG GLOBAL)
🏢 Công ty: LEADSMAX GROUP
📍 Địa chỉ: 84 Hồ Tùng Mậu, P. Hòa Minh, Q. Liên Chiểu, TP. Đà Nẵng
💰 Mức lương: 10.000.000đ - 15.000.000đ/tháng + Thưởng % hoa hồng / hoa hồng theo lead & conversion.
🏖️ Chế độ: Nghỉ Thứ 7 & Chủ Nhật, du lịch thường niên, BHXH đầy đủ.

📌 MÔ TẢ CÔNG VIỆC:
- Lập kế hoạch, setup và tối ưu hóa các chiến dịch quảng cáo TikTok Ads nhắm thị trường quốc tế (Mỹ, Anh, Canada, Úc...) trong mảng Fintech - Lending - Affiliate Marketing.
- Phối hợp chặt chẽ với team Creative / Video Editor để lên kịch bản video ngắn, hook hấp dẫn, thử nghiệm biến thể quảng cáo A/B testing.
- Quản trị ngân sách quảng cáo lớn, tối ưu các chỉ số CPM, CPC, CTR, CPL, CPA và ROAS.
- Theo dõi cập nhật thuật toán mới của TikTok, chính sách quảng cáo và xu hướng sáng tạo toàn cầu.

📌 YÊU CẦU:
- Tối thiểu 6 tháng - 1 năm kinh nghiệm thực chiến chạy quảng cáo TikTok Ads (ưu tiên có kinh nghiệm thị trường quốc tế/global hoặc affiliate).
- Tư duy logic, nhạy bén với số liệu và chỉ số ROI.
- Đọc hiểu tiếng Anh tốt để nghiên cứu tài liệu và thị trường nước ngoài.""",
        "ai_score": 96,
        "ai_intent": "Tuyển TikTok Ads Specialist thị trường Global (10-15tr)",
        "ai_urgency": "Cao",
        "ai_suggested_reply": "Chào Leadsmax Group! Em có kinh nghiệm thực chiến chạy TikTok Ads thị trường Global với kỹ năng tối ưu ngân sách CPL/CPA và phối hợp team làm creative hook. Em xin phép gửi CV và case study chiến dịch qua email/inbox ạ."
    },
    {
        "group_name": "Việc Làm Marketing Đà Nẵng (Media, Content, Ads, SEO)",
        "author_name": "Brando Media Recruitment",
        "author_url": "https://www.facebook.com/groups/vieclammarketingdanang",
        "post_url": "https://danang43.vn/brando-agency-tuyen-tu-van-giai-phap-marketing",
        "post_content": """[ĐÀ NẴNG] TUYỂN DỤNG CHUYÊN VIÊN TƯ VẤN GIẢI PHÁP MARKETING (AGENCY)
🏢 Đơn vị: CÔNG TY TNHH TRUYỀN THÔNG BRANDO (BRANDO AGENCY)
📍 Địa điểm: Quận Hải Châu, TP. Đà Nẵng
💰 Mức lương: 10.000.000đ - 12.000.000đ/tháng (Lương cứng) + % Hoa hồng hợp đồng Marketing tổng thể (Thu nhập trung bình 15 - 20 triệu/tháng).
⏰ Giờ làm việc: Hành chính, nghỉ Thứ 7 và Chủ Nhật.

📌 MÔ TẢ CÔNG VIỆC:
- Tiếp nhận thông tin, nhu cầu marketing từ các khách hàng doanh nghiệp vừa và nhỏ tại Đà Nẵng và miền Trung.
- Tư vấn các gói giải pháp Digital Marketing toàn diện: Quảng cáo Facebook/Google Ads, SEO Website, Thiết kế nhận diện thương hiệu, Phòng Marketing thuê ngoài.
- Phối hợp với bộ phận kỹ thuật (Technical & Content) để xây dựng Proposal, kế hoạch triển khai và báo giá chi tiết cho khách hàng.
- Theo dõi tiến độ hợp đồng, duy trì mối quan hệ và chăm sóc khách hàng doanh nghiệp đối tác.

📌 YÊU CẦU:
- Tốt nghiệp CĐ/ĐH chuyên ngành Marketing, QTKD hoặc liên quan.
- Có kiến thức nền tảng vững về các công cụ Digital Marketing.
- Kỹ năng giao tiếp, thuyết trình và đàm phán tốt; tác phong chỉn chu chuyên nghiệp.""",
        "ai_score": 93,
        "ai_intent": "Tuyển Chuyên viên Tư vấn Marketing Agency (10-12tr + hoa hồng)",
        "ai_urgency": "Trung bình",
        "ai_suggested_reply": "Chào anh/chị tuyển dụng Brando Agency! Em rất quan tâm đến vị trí Chuyên viên Tư vấn Giải pháp Marketing. Với kiến thức Digital Marketing vững và kỹ năng làm việc cùng khách hàng B2B, em xin phép gửi CV ứng tuyển ạ."
    },
    {
        "group_name": "Việc Làm Marketing Media Đà Nẵng Xịn Chất",
        "author_name": "Tuyển Dụng Mj Art Group",
        "author_url": "https://www.facebook.com/groups/vieclammarketingmediadanang",
        "post_url": "https://danang43.edu.vn/mj-art-group-tuyen-digital-marketing-executive",
        "post_content": """[ĐÀ NẴNG] TUYỂN DỤNG DIGITAL MARKETING EXECUTIVE / CONTENT MARKETING EXECUTIVE
🏢 Doanh nghiệp: CÔNG TY TNHH MJ ART GROUP (Nền tảng TMĐT BIDU)
📍 Địa chỉ: Tầng 3, Khách sạn Wink Hotel Danang Riverside, 351 Trần Hưng Đạo, P. An Hải Tây, Q. Sơn Trà, TP. Đà Nẵng
💰 Mức lương: 10.000.000đ - 15.000.000đ/tháng (Tùy năng lực và kinh nghiệm)
🌟 Môi trường làm việc hiện đại, view sông Hàn tuyệt đẹp, đồng nghiệp trẻ trung, năng động.

📌 MÔ TẢ CÔNG VIỆC:
- Xây dựng và thực thi các chiến dịch Digital Marketing thu hút người dùng cho nền tảng ứng dụng TMĐT thời trang & làm đẹp BIDU.
- Quản trị và phát triển các kênh Social Media (TikTok, Fanpage, Instagram), sáng tạo content bắt trend giới trẻ.
- Setup và tối ưu chiến dịch quảng cáo chuyển đổi (App Install, In-app Purchase) trên Meta Ads, TikTok Ads, Google UAC.
- Theo dõi các chỉ số đo lường hiệu quả (CAC, Retention, LTV) và báo cáo trực tiếp cho Trưởng bộ phận Tiếp thị.

📌 YÊU CẦU:
- Có từ 1-2 năm kinh nghiệm trong mảng Digital Marketing, Social Media hoặc E-commerce.
- Nhạy bén với xu hướng thời trang, làm đẹp, phong cách sống của Gen Z.
- Sử dụng thành thạo các công cụ phân tích số liệu quảng cáo.""",
        "ai_score": 95,
        "ai_intent": "Tuyển Digital Marketing cho E-commerce App BIDU (10-15tr)",
        "ai_urgency": "Cao",
        "ai_suggested_reply": "Chào Mj Art Group! Mình rất ấn tượng với nền tảng BIDU và môi trường sáng tạo tại Wink Hotel. Với kinh nghiệm làm Social & Digital Marketing mảng Fashion/Beauty, mình xin gửi hồ sơ ứng tuyển vị trí này ạ."
    },
    {
        "group_name": "Tuyển Dụng Đà Nẵng - Việc Làm Đà Nẵng (Danang43)",
        "author_name": "HR Lê Trường Phát",
        "author_url": "https://www.facebook.com/groups/danang43",
        "post_url": "https://danang43.vn/le-truong-phat-tuyen-nhan-vien-marketing",
        "post_content": """[ĐÀ NẴNG] CÔNG TY TNHH LÊ TRƯƠNG PHÁT TUYỂN DỤNG NHÂN VIÊN MARKETING
🏢 Lĩnh vực: Nhà phân phối gạch nhập khẩu cao cấp & vật liệu xây dựng hàng đầu miền Trung
📍 Địa chỉ Showroom: 07 Võ Chí Công, P. Hòa Xuân, Q. Cẩm Lệ, TP. Đà Nẵng
💰 Mức lương: Lương cơ bản 10.000.000đ - 15.000.000đ/tháng + Hoa hồng 1.5% doanh thu (Tổng thu nhập từ 20.000.000đ đến 40.000.000đ+/tháng).

📌 MÔ TẢ CÔNG VIỆC:
- Hoạch định và triển khai chiến lược marketing cho hệ thống phân phối gạch ốp lát và vật liệu cao cấp.
- Quản lý kênh truyền thông số: Fanpage, Website, kênh YouTube giới thiệu sản phẩm và công trình thực tế.
- Triển khai quảng cáo nhắm mục tiêu đến phân khúc khách hàng xây nhà, kiến trúc sư, nhà thầu xây dựng và chủ đầu tư biệt thự/khách sạn.
- Phối hợp với bộ phận kinh doanh tổ chức các hội thảo, sự kiện tri ân khách hàng và ra mắt bộ sưu tập mới.

📌 YÊU CẦU:
- Độ tuổi: 24 - 30 tuổi, tốt nghiệp Đại học chuyên ngành Marketing, QTKD hoặc ngành nghề liên quan.
- Tối thiểu 2 năm kinh nghiệm marketing trong ngành nội thất, bất động sản, vật liệu xây dựng hoặc hàng tiêu dùng cao cấp.
- Tư duy thẩm mỹ tốt, chủ động và tinh thần trách nhiệm cao.""",
        "ai_score": 94,
        "ai_intent": "Tuyển Nhân viên Marketing ngành VLXD cao cấp (10-15tr + hoa hồng)",
        "ai_urgency": "Trung bình",
        "ai_suggested_reply": "Kính chào Công ty Lê Trường Phát! Em có kinh nghiệm 2 năm làm Marketing mảng nội thất & kiến trúc tại Đà Nẵng, am hiểu phân khúc khách hàng xây dựng cao cấp. Em xin gửi hồ sơ ứng tuyển vị trí Nhân viên Marketing ạ."
    },
    {
        "group_name": "Việc Làm Marketing Media Đà Nẵng Xịn Chất",
        "author_name": "Tuyển Dụng XP Media Đà Nẵng",
        "author_url": "https://www.facebook.com/groups/vieclammarketingmediadanang",
        "post_url": "https://danang43.vn/xp-media-tuyen-sales-marketing-da-nang",
        "post_content": """[HẢI CHÂU - ĐÀ NẴNG] TUYỂN DỤNG SALES MARKETING / DIGITAL MARKETING
🏢 Đơn vị: CÔNG TY TNHH TMDV TRUYỀN THÔNG XP MEDIA
📍 Địa chỉ: 214 Lê Thanh Nghị, P. Hòa Cường, Q. Hải Châu, TP. Đà Nẵng
💰 Thu nhập: 10.000.000đ - 15.000.000đ/tháng (Lương cứng + Hoa hồng dự án + Thưởng nóng chiến dịch).

📌 MÔ TẢ CÔNG VIỆC:
- Nghiên cứu thị trường và kết nối với các doanh nghiệp, cửa hàng, chuỗi kinh doanh tại Đà Nẵng có nhu cầu quảng cáo số.
- Tư vấn các gói giải pháp Media: Sản xuất video viral, xây kênh TikTok thương hiệu, chạy Ads Facebook/Google đa kênh.
- Tham gia xây dựng chiến lược truyền thông và đồng hành cùng khách hàng trong suốt quá trình triển khai dự án.
- Báo cáo kết quả và phối hợp cùng đội ngũ kỹ thuật nâng cao chất lượng dịch vụ.

📌 YÊU CẦU:
- Đam mê ngành Marketing, truyền thông số, giao tiếp tốt và tự tin.
- Ưu tiên ứng viên có kinh nghiệm sales dịch vụ marketing hoặc chạy quảng cáo.
- Được công ty đào tạo chuyên sâu về kỹ năng tư vấn và kiến thức marketing thực chiến.""",
        "ai_score": 92,
        "ai_intent": "Tuyển Sales Marketing / Tư vấn Media Đà Nẵng (10-15tr)",
        "ai_urgency": "Trung bình",
        "ai_suggested_reply": "Chào XP Media! Mình có thế mạnh giao tiếp, nắm vững các sản phẩm Digital Marketing & Video Media tại Đà Nẵng. Mình xin gửi CV để ứng tuyển vào đội ngũ của công ty ạ."
    },
    {
        "group_name": "Hội Tìm Việc Làm Marketing - Truyền Thông Đà Nẵng",
        "author_name": "HR Rhenware VN",
        "author_url": "https://www.facebook.com/groups/hoituyenmarketingdanang",
        "post_url": "https://joboko.com/rhenware-tuyen-marketing-ads-executive",
        "post_content": """[ĐÀ NẴNG] CÔNG TY TNHH RHENWARE VN TUYỂN MARKETING ADS EXECUTIVE
🏢 Doanh nghiệp: CÔNG TY TNHH RHENWARE VN (Thương hiệu thiết bị vệ sinh cao cấp)
📍 Địa điểm: Khu đô thị công nghệ FPT City, P. Hòa Hải, Q. Ngũ Hành Sơn, TP. Đà Nẵng
💰 Mức lương: 10.000.000đ - 15.000.000đ/tháng (Upto 15 triệu tùy kinh nghiệm thực chiến) + Thưởng hiệu quả kinh doanh.
🛡️ Quyền lợi: Đóng BHXH/BHYT đầy đủ theo quy định, nghỉ lễ tết, thưởng tháng 13.

📌 MÔ TẢ CÔNG VIỆC:
- Lập kế hoạch, setup và tối ưu các chiến dịch quảng cáo bán hàng trên Meta Ads, Google Ads và TikTok Ads.
- Lên ý tưởng nội dung, thông điệp quảng cáo (Hook/Offer/CTA) phối hợp cùng team thiết kế hình ảnh & dựng clip.
- Quản lý ngân sách chạy quảng cáo hàng tháng, liên tục kiểm tra và tối ưu chi phí trên mỗi đơn hàng/lead.
- Báo cáo chỉ số chuyển đổi định kỳ cho Giám đốc Tiếp thị.

📌 YÊU CẦU:
- Tối thiểu 1 năm kinh nghiệm chạy ads thực chiến, có portfolio kết quả rõ ràng.
- Biết sử dụng các công cụ tracking chuyển đổi, Pixel, Google Tag Manager.""",
        "ai_score": 95,
        "ai_intent": "Tuyển Chuyên viên Quảng cáo Performance Ads (10-15tr)",
        "ai_urgency": "Cao",
        "ai_suggested_reply": "Chào HR Rhenware VN! Em đã có hơn 1 năm kinh nghiệm chạy Performance Ads mảng sản phẩm gia dụng/nội thất cao cấp với chỉ số ROAS ổn định. Em xin phép gửi CV và báo cáo chiến dịch mẫu để anh/chị xem xét ạ."
    },
    {
        "group_name": "Tuyển Dụng Đà Nẵng - Việc Làm Đà Nẵng (Danang43)",
        "author_name": "Tuyển Dụng Regal Group (Đất Xanh Miền Trung)",
        "author_url": "https://www.facebook.com/groups/danang43",
        "post_url": "https://danang43.edu.vn/dat-xanh-mien-trung-tuyen-chuyen-vien-marketing",
        "post_content": """[ĐÀ NẴNG] TUYỂN DỤNG CHUYÊN VIÊN MARKETING (KHAI THÁC KHÁCH HÀNG CAO CẤP)
🏢 Tập đoàn: REGAL GROUP (TIỀN THÂN LÀ ĐẤT XANH MIỀN TRUNG)
📍 Địa điểm: TP. Đà Nẵng
💰 Mức lương: 10.000.000đ - 18.000.000đ/tháng (Lương cứng 10-15tr + Thưởng kinh doanh dự án)
💎 Chế độ phúc lợi tập đoàn chuẩn quốc tế, bảo hiểm sức khỏe VIP, cơ hội thăng tiến rõ ràng.

📌 MÔ TẢ CÔNG VIỆC:
- Lập kế hoạch và triển khai các chiến dịch Digital Marketing nhắm đến phân khúc khách hàng thượng lưu (HNWI) cho các dự án bất động sản nghỉ dưỡng hạng sang.
- Vận hành các kênh quảng cáo Google Search, Facebook Ads, LinkedIn Ads và Email Marketing nuôi dưỡng khách hàng tiềm năng.
- Phối hợp với bộ phận Sự kiện tổ chức các buổi Gala tri ân, lễ mở bán và trải nghiệm dự án cho khách VIP.
- Đo lường và báo cáo nguồn khách hàng tiềm năng về cho khối kinh doanh.

📌 YÊU CẦU:
- Tối thiểu 1 - 2 năm kinh nghiệm marketing ngành BĐS, tài chính, ô tô hạng sang hoặc khách sạn 5 sao.
- Tác phong lịch thiệp, kỹ năng phân tích data và viết nội dung sang trọng, tinh tế.""",
        "ai_score": 97,
        "ai_intent": "Tuyển Chuyên viên Marketing BĐS hạng sang (10-18tr)",
        "ai_urgency": "Cao",
        "ai_suggested_reply": "Kính chào Bộ phận Tuyển dụng Regal Group! Em có kinh nghiệm triển khai Marketing khai thác khách hàng cao cấp trong lĩnh vực BĐS nghỉ dưỡng. Em xin gửi CV ứng tuyển vị trí Chuyên viên Marketing ạ."
    }
]

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Insert Groups
    print(">>> Đang nạp các Nhóm Tuyển Dụng Marketing tại Đà Nẵng vào Database...")
    for grp in groups_data:
        cursor.execute("""
            INSERT OR REPLACE INTO groups (name, url, category, member_count, is_joined)
            VALUES (?, ?, ?, ?, 1)
        """, (grp["name"], grp["url"], grp["category"], grp["member_count"]))
    
    # 2. Insert Leads / Job Postings
    print(">>> Đang nạp các bài viết tuyển dụng Marketing (10 - 15 triệu/tháng) vào Leads...")
    inserted_count = 0
    for job in jobs_data:
        cursor.execute("""
            INSERT OR REPLACE INTO leads (
                group_name, author_name, author_url, post_url, post_content,
                ai_score, ai_intent, ai_urgency, ai_suggested_reply, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'new')
        """, (
            job["group_name"],
            job["author_name"],
            job["author_url"],
            job["post_url"],
            job["post_content"],
            job["ai_score"],
            job["ai_intent"],
            job["ai_urgency"],
            job["ai_suggested_reply"]
        ))
        inserted_count += 1
        
    conn.commit()
    conn.close()
    print(f"✅ Hoàn tất: Đã lưu {len(groups_data)} hội nhóm và {inserted_count} bài viết tuyển dụng Marketing Đà Nẵng chuẩn tiêu chí 10-15tr vào hệ thống!")

if __name__ == "__main__":
    main()
