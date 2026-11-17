import os
import pymupdf as fitz
from docx import Document
from pptx import Presentation

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'pptx', 'ppt', 'mp4', 'webm', 'ogg', 'mov'}
VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg', 'mov'}
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in IMAGE_EXTENSIONS

def format_file_size(size_in_bytes):
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    else:
        return f"{size_in_bytes / (1024 * 1024):.1f} MB"

def parse_docx_to_html(file_path):
    """
    Parse a .docx document into clean, readable HTML elements
    """
    try:
        doc = Document(file_path)
        html_parts = []
        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue
            if p.style.name.startswith('Heading 1'):
                html_parts.append(f"<h2 class='clay-heading-1'>{text}</h2>")
            elif p.style.name.startswith('Heading 2'):
                html_parts.append(f"<h3 class='clay-heading-2'>{text}</h3>")
            elif p.style.name.startswith('Heading 3'):
                html_parts.append(f"<h4 class='clay-heading-3'>{text}</h4>")
            elif p.style.name.startswith('List'):
                html_parts.append(f"<li class='clay-list-item'>{text}</li>")
            else:
                html_parts.append(f"<p class='clay-paragraph'>{text}</p>")
                
        # Parse tables if any
        for table in doc.tables:
            html_parts.append("<div class='clay-table-wrapper'><table class='clay-doc-table'>")
            for i, row in enumerate(table.rows):
                html_parts.append("<tr>")
                for cell in row.cells:
                    tag = "th" if i == 0 else "td"
                    html_parts.append(f"<{tag}>{cell.text.strip()}</{tag}>")
                html_parts.append("</tr>")
            html_parts.append("</table></div>")
            
        return "".join(html_parts) if html_parts else "<p class='clay-paragraph italic'>Tài liệu không có nội dung văn bản.</p>"
    except Exception as e:
        return f"<div class='clay-alert-box'>Không thể đọc nội dung DOCX: {str(e)}</div>"

def parse_pptx_slides(file_path):
    """
    Parse a .pptx presentation into structured slide data for in-browser slide viewing
    """
    try:
        prs = Presentation(file_path)
        slides_data = []
        for i, slide in enumerate(prs.slides, 1):
            slide_title = f"Slide {i}"
            slide_texts = []
            
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        text = paragraph.text.strip()
                        if text:
                            # Try to identify title
                            if shape == slide.shapes.title and not slide_texts:
                                slide_title = text
                            else:
                                slide_texts.append(text)
                                
            slides_data.append({
                'slide_number': i,
                'title': slide_title,
                'content': slide_texts
            })
            
        return slides_data
    except Exception as e:
        return [{'slide_number': 1, 'title': 'Lỗi đọc file PPTX', 'content': [str(e)]}]

def get_pdf_metadata(file_path):
    """
    Get PDF basic info (page count, title) using PyMuPDF
    """
    try:
        doc = fitz.open(file_path)
        page_count = len(doc)
        title = doc.metadata.get('title') or os.path.basename(file_path)
        doc.close()
        return {'page_count': page_count, 'title': title}
    except Exception as e:
        return {'page_count': 0, 'title': os.path.basename(file_path), 'error': str(e)}


# ==============================================================================
# BUILT-IN SYSTEM QUESTION BANK (PART I: 24 MCQ x 0.25đ | PART II: 06 TF 4-STATEMENT)
# ==============================================================================
TF_SCORE_TABLE = (0.0, 0.1, 0.25, 0.5, 1.0)

TOPIC_LABELS = {
    'A': 'Chủ đề 1: Máy tính và xã hội tri thức',
    'C': 'Chủ đề 2 & 3: Lưu trữ, tìm kiếm & Đạo đức môi trường số',
    'F': 'Chủ đề 4, 5 & 6: Hệ Cơ sở dữ liệu & Thực hành khai thác CSDL',
    'E': 'Chủ đề 7: Phần mềm chỉnh sửa ảnh và làm video'
}

TOPIC_FILTER_MAP = {
    '1': 'A', 'A': 'A',
    '2': 'C', '3': 'C', 'C': 'C',
    '4': 'F', '5': 'F', '6': 'F', 'F': 'F',
    '7': 'E', 'E': 'E',
}

# ==============================================================================
# OFFICIAL CURRICULUM: TIN HỌC 11 (KẾT NỐI TRI THỨC - 7 CHỦ ĐỀ & 31 BÀI HỌC)
# ==============================================================================
CURRICULUM_TIN11 = [
    {
        'topic_num': 1,
        'code': 'CHỦ ĐỀ 1',
        'title': 'Chủ đề 1. Máy tính và xã hội tri thức',
        'description': 'Hệ điều hành, thực hành sử dụng hệ điều hành, phần mềm nguồn mở, cấu tạo bên trong máy tính và kết nối thiết bị số (Trang 5 – 31).',
        'poster_url': 'img/posters/poster_a_os.jpg',
        'lessons': [
            (1, 'Bài 1. Hệ điều hành', 5,
             '# I. Trọng tâm kiến thức (Trang 5)\n1. Lịch sử phát triển và vai trò của hệ điều hành đối với máy tính cá nhân và thiết bị di động.\n2. Các chức năng cơ bản: quản lí thiết bị, quản lí lưu trữ tệp, điều phối tiến trình và cung cấp giao diện người dùng.\n# II. Hoạt động thực hành & Vận dụng\n- Phân biệt hệ điều hành máy tính (Windows, Linux, macOS) và hệ điều hành di động (Android, iOS).'),
            (2, 'Bài 2. Thực hành sử dụng hệ điều hành', 10,
             '# I. Trọng tâm kiến thức (Trang 10)\n1. Khai thác các chức năng cơ bản của hệ điều hành trên máy tính và điện thoại thông minh.\n2. Quản lí tệp, thư mục và sử dụng các tiện ích hệ thống.\n# II. Hoạt động thực hành & Vận dụng\n- Thực hành kiểm tra dung lượng đĩa, tối ưu hóa bộ nhớ và cài đặt tiện ích cơ bản.'),
            (3, 'Bài 3. Phần mềm nguồn mở và phần mềm chạy trên Internet', 15,
             '# I. Trọng tâm kiến thức (Trang 15)\n1. Khái niệm phần mềm nguồn mở (Open Source) và phần mềm thương mại (Commercial Software).\n2. Giấy phép công cộng GPL và vai trò của phần mềm chạy trên Internet (SaaS / Web App).\n# II. Hoạt động thực hành & Vận dụng\n- Trải nghiệm bộ công cụ văn phòng nguồn mở LibreOffice và ứng dụng trực tuyến Google Docs.'),
            (4, 'Bài 4. Bên trong máy tính', 21,
             '# I. Trọng tâm kiến thức (Trang 21)\n1. Các thiết bị bên trong máy tính: Bộ xử lí trung tâm (CPU), bộ nhớ trong (RAM, ROM) và bảng mạch chính.\n2. Các cổng logic cơ bản (AND, OR, NOT, XOR) và mạch logic thực hiện phép tính nhị phân.\n# II. Hoạt động thực hành & Vận dụng\n- Đọc thông số kĩ thuật của CPU (tốc độ xung nhịp GHz, số nhân) và dung lượng RAM/SSD.'),
            (5, 'Bài 5. Kết nối máy tính với các thiết bị số', 27,
             '# I. Trọng tâm kiến thức (Trang 27)\n1. Các thiết bị vào – ra phổ biến và thông số kĩ thuật cơ bản.\n2. Các cổng kết nối vật lí (USB, HDMI, VGA, RJ45) và kết nối không dây (Bluetooth, Wi-Fi).\n# II. Hoạt động thực hành & Vận dụng\n- Thực hành kết nối máy tính với màn hình chiếu, máy in và điện thoại thông minh.'),
        ]
    },
    {
        'topic_num': 2,
        'code': 'CHỦ ĐỀ 2',
        'title': 'Chủ đề 2. Tổ chức lưu trữ, tìm kiếm và trao đổi thông tin',
        'description': 'Lưu trữ và chia sẻ tệp tin trên đám mây, tìm kiếm thông tin nâng cao và sử dụng thư điện tử, mạng xã hội hiệu quả (Trang 32 – 42).',
        'poster_url': 'img/posters/poster_c_cloud.jpg',
        'lessons': [
            (6, 'Bài 6. Lưu trữ và chia sẻ tệp tin trên Internet', 32,
             '# I. Trọng tâm kiến thức (Trang 32)\n1. Dịch vụ lưu trữ trực tuyến (Google Drive, OneDrive, Dropbox, iCloud) và cơ chế đồng bộ dữ liệu.\n2. Phân quyền chia sẻ tệp và thư mục: Người xem (Viewer), Người nhận xét (Commenter), Người chỉnh sửa (Editor).\n# II. Hoạt động thực hành & Vận dụng\n- Tạo cây thư mục học tập trên đám mây và chia sẻ tài liệu nhóm theo đúng quyền hạn.'),
            (7, 'Bài 7. Thực hành tìm kiếm thông tin trên Internet', 36,
             '# I. Trọng tâm kiến thức (Trang 36)\n1. Tìm kiếm thông tin bằng từ khóa và tìm kiếm bằng tiếng nói.\n2. Sử dụng toán tử tìm kiếm nâng cao: dấu ngoặc kép "..." và lọc định dạng tệp filetype:pdf, filetype:docx.\n# II. Hoạt động thực hành & Vận dụng\n- Thực hành tra cứu tài liệu học tập môn Tin học 11 theo đúng định dạng PDF/PPTX.'),
            (8, 'Bài 8. Thực hành nâng cao sử dụng thư điện tử và mạng xã hội', 39,
             '# I. Trọng tâm kiến thức (Trang 39)\n1. Phân loại, gắn nhãn (Label) và tìm kiếm thư điện tử nâng cao trong Gmail.\n2. Quản lí thông tin, quyền riêng tư và khai thác nhóm học tập trên mạng xã hội.\n# II. Hoạt động thực hành & Vận dụng\n- Thiết lập bộ lọc tự động phân loại thư học tập và cấu hình bảo mật tài khoản.'),
        ]
    },
    {
        'topic_num': 3,
        'code': 'CHỦ ĐỀ 3',
        'title': 'Chủ đề 3. Đạo đức, pháp luật và văn hoá trong môi trường số',
        'description': 'Quy tắc ứng xử văn minh, phòng tránh lừa đảo trên không gian mạng và bảo vệ thông tin cá nhân an toàn (Trang 43 – 48).',
        'poster_url': 'img/posters/poster_c_cloud.jpg',
        'lessons': [
            (9, 'Bài 9. Giao tiếp an toàn trên Internet', 43,
             '# I. Trọng tâm kiến thức (Trang 43)\n1. Nhận diện các hình thức lừa đảo trực tuyến (Phishing), tin giả và nguy cơ mất an toàn thông tin.\n2. Nguyên tắc giao tiếp văn minh, tôn trọng bản quyền và bảo vệ dữ liệu cá nhân (mật khẩu mạnh, xác thực 2 yếu tố 2FA).\n# II. Hoạt động thực hành & Vận dụng\n- Phân tích tình huống email/tin nhắn giả mạo và thực hành bật xác thực hai bước (2FA).'),
        ]
    },
    {
        'topic_num': 4,
        'code': 'CHỦ ĐỀ 4',
        'title': 'Chủ đề 4. Giới thiệu các hệ cơ sở dữ liệu',
        'description': 'Bài toán quản lí dữ liệu, khái niệm CSDL, Hệ quản trị CSDL, mô hình CSDL quan hệ, ngôn ngữ truy vấn SQL và bảo mật CSDL (Trang 49 – 76).',
        'poster_url': 'img/posters/poster_f_database.jpg',
        'lessons': [
            (10, 'Bài 10. Lưu trữ dữ liệu và khai thác thông tin phục vụ quản lí', 49,
             '# I. Trọng tâm kiến thức (Trang 49)\n1. Nhu cầu lưu trữ dữ liệu có tổ chức trong các bài toán quản lí thực tế (quản lí học sinh, thư viện, bán hàng).\n2. Thu thập, cập nhật dữ liệu và khai thác thông tin phục vụ ra quyết định.\n# II. Hoạt động thực hành & Vận dụng\n- Phân tích các bảng dữ liệu đầu vào và báo cáo đầu ra trong bài toán quản lí điểm lớp học.'),
            (11, 'Bài 11. Cơ sở dữ liệu', 53,
             '# I. Trọng tâm kiến thức (Trang 53)\n1. Định nghĩa Cơ sở dữ liệu (Database) và phân biệt với cách lưu trữ tệp rời rạc truyền thống.\n2. Các thuộc tính cơ bản của CSDL: tính cấu trúc, tính không dư thừa, tính độc lập dữ liệu và tính toàn vẹn.\n# II. Hoạt động thực hành & Vận dụng\n- Nhận biết ưu điểm của CSDL khi nhiều người dùng cùng khai thác dữ liệu.'),
            (12, 'Bài 12. Hệ quản trị cơ sở dữ liệu và hệ cơ sở dữ liệu', 58,
             '# I. Trọng tâm kiến thức (Trang 58)\n1. Chức năng của Hệ quản trị CSDL (DBMS): định nghĩa dữ liệu, thao tác dữ liệu và kiểm soát truy cập.\n2. Các thành phần của một Hệ cơ sở dữ liệu: CSDL, Hệ quản trị CSDL và Phần mềm ứng dụng CSDL.\n# II. Hoạt động thực hành & Vận dụng\n- Phân biệt Hệ CSDL tập trung và Hệ CSDL phân tán trong thực tiễn.'),
            (13, 'Bài 13. Cơ sở dữ liệu quan hệ', 64,
             '# I. Trọng tâm kiến thức (Trang 64)\n1. Các khái niệm của mô hình quan hệ: Bảng (Relation), Hàng / Bản ghi (Record), Cột / Trường (Field).\n2. Khóa (Key), Khóa chính (Primary Key), Khóa ngoài (Foreign Key) và liên kết giữa các bảng.\n# II. Hoạt động thực hành & Vận dụng\n- Xác định khóa chính và khóa ngoài trên lược đồ CSDL Quản lí âm nhạc / Quản lí học sinh.'),
            (14, 'Bài 14. SQL – Ngôn ngữ truy vấn có cấu trúc', 69,
             '# I. Trọng tâm kiến thức (Trang 69)\n1. Các thành phần của SQL: Ngôn ngữ định nghĩa dữ liệu (DDL), thao tác dữ liệu (DML) và kiểm soát dữ liệu (DCL).\n2. Câu lệnh truy vấn cốt lõi: SELECT ... FROM ... WHERE ... ORDER BY và kết nối bảng bằng INNER JOIN ... ON.\n# II. Hoạt động thực hành & Vận dụng\n- Viết câu lệnh SQL tạo bảng, thêm dòng (INSERT), cập nhật (UPDATE) và truy vấn có điều kiện.'),
            (15, 'Bài 15. Bảo mật và an toàn hệ cơ sở dữ liệu', 73,
             '# I. Trọng tâm kiến thức (Trang 73)\n1. Các nguy cơ mất an toàn dữ liệu (lỗi phần cứng, sự cố nguồn điện, truy cập trái phép).\n2. Các giải pháp bảo mật: phân quyền người dùng, mã hóa dữ liệu, ghi biên bản hệ thống (Log) và sao lưu dự phòng.\n# II. Hoạt động thực hành & Vận dụng\n- Xây dựng bảng phân quyền truy cập CSDL cho Quản trị viên, Giáo viên và Học sinh.'),
        ]
    },
    {
        'topic_num': 5,
        'code': 'CHỦ ĐỀ 5',
        'title': 'Chủ đề 5. Hướng nghiệp với Tin học',
        'description': 'Tìm hiểu nghề Quản trị cơ sở dữ liệu, yêu cầu năng lực chuyên môn và triển vọng nghề nghiệp trong kỉ nguyên số (Trang 77 – 80).',
        'poster_url': 'img/posters/poster_f_database.jpg',
        'lessons': [
            (16, 'Bài 16. Công việc quản trị cơ sở dữ liệu', 77,
             '# I. Trọng tâm kiến thức (Trang 77)\n1. Nhiệm vụ chính của Nhà quản trị cơ sở dữ liệu (DBA): cài đặt, giám sát hiệu năng, bảo mật và phục hồi dữ liệu.\n2. Phẩm chất, kiến thức chuyên môn cần thiết và nhu cầu nhân lực ngành Quản trị CSDL hiện nay.\n# II. Hoạt động thực hành & Vận dụng\n- Tìm hiểu chương trình đào tạo và vị trí việc làm liên quan đến Quản trị và Phân tích dữ liệu.'),
        ]
    },
    {
        'topic_num': 6,
        'code': 'CHỦ ĐỀ 6',
        'title': 'Chủ đề 6. Thực hành tạo và khai thác cơ sở dữ liệu',
        'description': 'Thực hành cài đặt phần mềm quản trị CSDL, thiết kế bảng, khóa chính, khóa ngoại, cập nhật, truy xuất liên kết bảng và sao lưu dữ liệu (Trang 81 – 115).',
        'poster_url': 'img/posters/poster_f_web.jpg',
        'lessons': [
            (17, 'Bài 17. Quản trị cơ sở dữ liệu trên máy tính', 81,
             '# I. Trọng tâm kiến thức (Trang 81)\n1. Làm quen với hệ quản trị CSDL MySQL / MariaDB và công cụ khách HeidiSQL trên máy tính.\n2. Khởi động dịch vụ CSDL, tạo phiên kết nối và làm quen giao diện làm việc.\n# II. Hoạt động thực hành & Vận dụng\n- Thực hành đăng nhập HeidiSQL và khám phá các thành phần quản lí CSDL.'),
            (18, 'Bài 18. Thực hành xác định cấu trúc bảng và các trường khoá', 86,
             '# I. Trọng tâm kiến thức (Trang 86)\n1. Phân tích bài toán thực tế để tổ chức dữ liệu thành các bảng giảm thiểu dư thừa.\n2. Xác định danh sách trường (cột), kiểu dữ liệu, khóa chính (Primary Key) và khóa ngoài (Foreign Key).\n# II. Hoạt động thực hành & Vận dụng\n- Thiết kế cấu trúc các bảng ca_si, nhac_si, ban_nhac, ban_thu_am cho CSDL Quản lí âm nhạc.'),
            (19, 'Bài 19. Thực hành tạo lập cơ sở dữ liệu và các bảng', 91,
             '# I. Trọng tâm kiến thức (Trang 91)\n1. Tạo mới một Cơ sở dữ liệu (Database) với bảng mã tiếng Việt UTF-8.\n2. Tạo bảng dữ liệu đơn, khai báo kiểu dữ liệu (INT, VARCHAR, DATE) và thiết lập khóa chính tự động tăng (AUTO_INCREMENT).\n# II. Hoạt động thực hành & Vận dụng\n- Thực hành tạo CSDL mymusic cùng hai bảng nhac_si và ca_si.'),
            (20, 'Bài 20. Thực hành tạo lập các bảng có khoá ngoại', 95,
             '# I. Trọng tâm kiến thức (Trang 95)\n1. Cách khai báo trường khóa ngoài (Foreign Key) tham chiếu đến khóa chính của bảng khác.\n2. Đảm bảo ràng buộc toàn vẹn tham chiếu giữa các bảng liên kết.\n# II. Hoạt động thực hành & Vận dụng\n- Thực hành tạo bảng ban_nhac và ban_thu_am có khóa ngoài liên kết tới nhac_si và ca_si.'),
            (21, 'Bài 21. Thực hành cập nhật và truy xuất dữ liệu các bảng', 100,
             '# I. Trọng tâm kiến thức (Trang 100)\n1. Thêm mới (INSERT), chỉnh sửa (UPDATE) và xóa (DELETE) các dòng dữ liệu trong bảng đơn.\n2. Truy xuất, sắp xếp và lọc dữ liệu trong bảng bằng giao diện trực quan hoặc câu lệnh SELECT.\n# II. Hoạt động thực hành & Vận dụng\n- Nhập danh sách nhạc sĩ, ca sĩ và thực hiện lọc tìm kiếm theo tên.'),
            (22, 'Bài 22. Thực hành cập nhật bảng dữ liệu có tham chiếu', 105,
             '# I. Trọng tâm kiến thức (Trang 105)\n1. Nguyên tắc nhập và sửa dữ liệu trên các bảng có trường khóa ngoài tham chiếu.\n2. Kiểm tra tính toàn vẹn dữ liệu khi xóa hoặc sửa bản ghi ở bảng cha.\n# II. Hoạt động thực hành & Vận dụng\n- Thực hành cập nhật dữ liệu cho bảng ban_nhac và ban_thu_am đúng ràng buộc khóa ngoại.'),
            (23, 'Bài 23. Thực hành truy xuất dữ liệu qua liên kết các bảng', 109,
             '# I. Trọng tâm kiến thức (Trang 109)\n1. Viết câu lệnh SELECT kết hợp mệnh đề INNER JOIN ... ON để lấy dữ liệu từ 2 hoặc 3 bảng liên kết.\n2. Kết hợp điều kiện WHERE và sắp xếp ORDER BY trên kết quả truy vấn liên bảng.\n# II. Hoạt động thực hành & Vận dụng\n- Truy xuất danh sách bản thu âm kèm tên bản nhạc, tên nhạc sĩ sáng tác và tên ca sĩ thể hiện.'),
            (24, 'Bài 24. Thực hành sao lưu dữ liệu', 113,
             '# I. Trọng tâm kiến thức (Trang 113)\n1. Quy trình xuất (Export) cấu trúc và dữ liệu CSDL ra tệp kịch bản .sql để sao lưu dự phòng.\n2. Quy trình phục hồi (Import / Restore) CSDL từ tệp sao lưu khi chuyển máy hoặc gặp sự cố.\n# II. Hoạt động thực hành & Vận dụng\n- Thực hành sao lưu CSDL mymusic ra tệp .sql và khôi phục lại hoàn chỉnh.'),
        ]
    },
    {
        'topic_num': 7,
        'code': 'CHỦ ĐỀ 7',
        'title': 'Chủ đề 7. Phần mềm chỉnh sửa ảnh và làm video',
        'description': 'Chỉnh sửa ảnh số đa lớp (Layers), tinh chỉnh màu sắc, vùng chọn, tạo ảnh động trên GIMP và biên tập phim hoạt hình, video đa phương tiện (Trang 116 – 150).',
        'poster_url': 'img/posters/poster_e_gimp.jpg',
        'lessons': [
            (25, 'Bài 25. Phần mềm chỉnh sửa ảnh', 116,
             '# I. Trọng tâm kiến thức (Trang 116)\n1. Giới thiệu phần mềm chỉnh sửa ảnh nguồn mở GIMP, giao diện làm việc và thông số ảnh số (độ phân giải, kích thước ảnh).\n2. Các thao tác cơ bản: Cắt ảnh (Crop), Thay đổi kích thước (Scale), Xoay ảnh (Rotate) và Biến đổi phối cảnh.\n# II. Hoạt động thực hành & Vận dụng\n- Mở tệp ảnh trong GIMP, căn chỉnh bố cục bằng Crop Tool và xuất ảnh sang định dạng PNG / JPG.'),
            (26, 'Bài 26. Công cụ tinh chỉnh màu sắc và công cụ chọn', 122,
             '# I. Trọng tâm kiến thức (Trang 122)\n1. Các công cụ chỉnh độ sáng – độ tương phản (Brightness-Contrast), cân bằng màu (Color Balance) và sắc thái – độ bão hòa (Hue-Saturation).\n2. Các công cụ tạo vùng chọn: Rectangle Select, Ellipse Select, Free Select (Lasso) và Fuzzy Select.\n# II. Hoạt động thực hành & Vận dụng\n- Thực hành khoanh vùng chọn đối tượng và làm sáng riêng phần chủ thể bức ảnh.'),
            (27, 'Bài 27. Công cụ vẽ và một số ứng dụng', 128,
             '# I. Trọng tâm kiến thức (Trang 128)\n1. Khái niệm Lớp ảnh (Layer), kênh Alpha trong suốt và quản lí thứ tự các lớp ảnh.\n2. Sử dụng công cụ vẽ (Paintbrush, Bucket Fill, Gradient) kết hợp công cụ tẩy xóa khuyết điểm (Clone Tool, Healing Tool).\n# II. Hoạt động thực hành & Vận dụng\n- Thực hành tẩy xóa chi tiết thừa trên ảnh phong cảnh và ghép thiết kế đa lớp.'),
            (28, 'Bài 28. Tạo ảnh động', 133,
             '# I. Trọng tâm kiến thức (Trang 133)\n1. Nguyên lí tạo ảnh động (Animation) từ chuỗi các khung hình (Frames) đặt trên từng lớp Layer trong GIMP.\n2. Thiết lập thời gian hiển thị từng khung hình (ms) và hiệu ứng chuyển cảnh động (Blend / Waves).\n# II. Hoạt động thực hành & Vận dụng\n- Thực hành tạo ảnh động chúc mừng hoặc biểu ngữ web và xuất ra tệp .gif.'),
            (29, 'Bài 29. Khám phá phần mềm làm phim', 137,
             '# I. Trọng tâm kiến thức (Trang 137)\n1. Cấu trúc chung của phần mềm làm phim (Video Editor): Kho tư liệu, Màn hình xem trước, Thanh thời gian (Timeline).\n2. Quy trình tạo dự án phim mới từ ảnh tĩnh, đoạn video clip và tệp âm thanh.\n# II. Hoạt động thực hành & Vận dụng\n- Nhập tư liệu ảnh/video vào dự án và sắp xếp các phân cảnh trên trục thời gian Timeline.'),
            (30, 'Bài 30. Biên tập phim', 143,
             '# I. Trọng tâm kiến thức (Trang 143)\n1. Các thao tác biên tập: cắt tách phân cảnh, điều chỉnh thời lượng, thêm hiệu ứng chuyển cảnh (Transitions) và hiệu ứng hình ảnh.\n2. Chèn phụ đề văn bản (Title / Text), lồng nhạc nền, ghi âm thuyết minh và xuất video chuẩn .mp4.\n# II. Hoạt động thực hành & Vận dụng\n- Hoàn thiện đoạn phim giới thiệu lớp học có nhạc nền, phụ đề và hiệu ứng chuyển cảnh mượt mà.'),
            (31, 'Bài 31. Thực hành tạo phim hoạt hình', 148,
             '# I. Trọng tâm kiến thức (Trang 148)\n1. Quy trình xây dựng kịch bản phân cảnh, chuẩn bị nhân vật – bối cảnh và tạo chuyển động hoạt hình.\n2. Đồng bộ hội thoại, hiệu ứng âm thanh, phụ đề và xuất bản sản phẩm phim hoạt hình hoàn chỉnh.\n# II. Hoạt động thực hành & Vận dụng\n- Thực hành dự án nhóm: Tạo một tập phim hoạt hình ngắn từ chuỗi hình ảnh và âm thanh.'),
        ]
    }
]

# Compact tuple list for Part I MCQ pool (32 questions -> random.sample picks 24)
_MCQ_RAW = [
    # --- CHỦ ĐỀ A (8 câu) ---
    ('a1', 'A', 'Chức năng nào sau đây KHÔNG phải là chức năng cơ bản của hệ điều hành?',
     'Quản lý tệp và thư mục trên bộ nhớ ngoài', 'Cung cấp giao diện giao tiếp giữa người dùng và máy tính',
     'Soạn thảo văn bản và chỉnh sửa ảnh chuyên nghiệp', 'Quản lý và phân phối tài nguyên phần cứng cho các tiến trình', 'C',
     'Soạn thảo văn bản và chỉnh sửa ảnh là chức năng của phần mềm ứng dụng, không phải hệ điều hành.'),
    ('a2', 'A', 'Đặc điểm nào sau đây thuộc về Phần mềm nguồn mở (Open Source Software)?',
     'Chỉ cho phép dùng thử trong 7 ngày rồi khóa', 'Công khai mã nguồn để người dùng được xem, sửa đổi và phân phối lại theo giấy phép',
     'Bắt buộc mua khóa bản quyền theo từng máy tính', 'Không thể chạy trên hệ điều hành Linux', 'B',
     'Phần mềm nguồn mở cung cấp mã nguồn công khai kèm giấy phép như GPL, MIT, Apache.'),
    ('a3', 'A', 'Bộ phận nào trong máy tính đóng vai trò là "bộ não" thực hiện các phép tính số học và logic?',
     'Bộ nhớ ngoài ổ cứng HDD', 'Bộ xử lý trung tâm (CPU)', 'Màn hình hiển thị', 'Bàn phím và chuột', 'B',
     'CPU (Central Processing Unit) gồm ALU và CU đảm nhiệm xử lý lệnh và tính toán.'),
    ('a4', 'A', 'Bộ nhớ nào sau đây mất toàn bộ dữ liệu đang lưu giữ khi tắt nguồn điện máy tính?',
     'Bộ nhớ RAM', 'Ổ cứng thể rắn SSD', 'Đĩa cứng từ HDD', 'Bộ nhớ chỉ đọc ROM', 'A',
     'RAM là bộ nhớ khả biến (volatile), dữ liệu bị xóa khi mất nguồn điện.'),
    ('a5', 'A', 'Đơn vị đo tốc độ xung nhịp của bộ xử lý trung tâm (CPU) thường dùng là gì?',
     'Gigabyte (GB)', 'Gigahertz (GHz)', 'Megabit trên giây (Mbps)', 'Điểm ảnh (Pixel)', 'B',
     'Tần số xung nhịp CPU được đo bằng Hz, MHz hoặc GHz.'),
    ('a6', 'A', 'Phần mềm nào sau đây là hệ điều hành nguồn mở phổ biến cho máy tính và máy chủ?',
     'Ubuntu Linux', 'Microsoft Windows 11', 'macOS Sonoma', 'Adobe Photoshop', 'A',
     'Ubuntu là bản phân phối tiêu biểu của hệ điều hành nguồn mở Linux.'),
    ('a7', 'A', 'Cổng kết nối nào thường dùng để truyền đồng thời cả hình ảnh độ phân giải cao và âm thanh số ra màn hình?',
     'Cổng VGA', 'Cổng HDMI', 'Cổng PS/2', 'Cổng RJ45', 'B',
     'HDMI truyền đồng thời tín hiệu hình ảnh và âm thanh số chất lượng cao.'),
    ('a8', 'A', 'Trên điện thoại thông minh, hệ điều hành nào được phát triển dựa trên nhân Linux nguồn mở?',
     'Android', 'iOS', 'Windows Phone', 'Symbian', 'A',
     'Hệ điều hành Android được phát triển dựa trên nhân Linux.'),

    # --- CHỦ ĐỀ C (8 câu) ---
    ('c1', 'C', 'Ưu điểm lớn nhất của dịch vụ lưu trữ đám mây (Google Drive, OneDrive) so với lưu trữ cục bộ là gì?',
     'Không cần Internet khi đồng bộ giữa các máy', 'Truy cập mọi lúc mọi nơi, đồng bộ đa thiết bị và chia sẻ phân quyền linh hoạt',
     'Tăng tốc độ xung nhịp CPU', 'Tự động nâng cấp dung lượng RAM vật lý', 'B',
     'Lưu trữ đám mây cho phép truy cập trực tuyến và phân quyền Xem / Nhận xét / Chỉnh sửa.'),
    ('c2', 'C', 'Trong máy tìm kiếm Google, toán tử nào dùng để lọc kết quả chỉ trả về tệp định dạng PDF?',
     'filetype:pdf', 'format=pdf', 'type#pdf', 'search:pdf', 'A',
     'Cú pháp chuẩn trên máy tìm kiếm là từ_khóa filetype:pdf.'),
    ('c3', 'C', 'Khi muốn tìm kiếm chính xác một cụm từ nguyên vẹn trên máy tìm kiếm, ta đặt cụm từ đó trong cặp dấu nào?',
     'Dấu ngoặc đơn ( )', 'Dấu ngoặc kép " "', 'Dấu ngoặc vuông [ ]', 'Dấu gạch chéo / /', 'B',
     'Đặt cụm từ trong dấu ngoặc kép "..." giúp tìm chính xác chuỗi ký tự đó.'),
    ('c4', 'C', 'Biện pháp nào sau đây giúp bảo vệ tài khoản thư điện tử và mạng xã hội an toàn nhất?',
     'Đặt mật khẩu là ngày sinh cho dễ nhớ', 'Bật xác thực hai yếu tố (2FA) kết hợp mật khẩu mạnh',
     'Gửi mật khẩu qua tin nhắn cho bạn bè giữ hộ', 'Dùng chung 1 mật khẩu cho mọi trang web', 'B',
     'Xác thực 2 yếu tố (2FA) yêu cầu mã xác nhận thứ hai ngoài mật khẩu truyền thống.'),
    ('c5', 'C', 'Khi chia sẻ tệp trên Google Drive, quyền nào chỉ cho phép người nhận đọc mà KHÔNG thể sửa hoặc xóa nội dung?',
     'Người chỉnh sửa (Editor)', 'Người xem (Viewer)', 'Chủ sở hữu (Owner)', 'Quản trị viên (Admin)', 'B',
     'Quyền Người xem (Viewer) chỉ cho phép xem tài liệu, không cho phép chỉnh sửa.'),
    ('c6', 'C', 'Hành vi gửi email giả mạo ngân hàng hoặc trường học để lừa người dùng nhập mật khẩu gọi là gì?',
     'Tấn công giả mạo (Phishing)', 'Sao lưu dữ liệu (Backup)', 'Chống phân mảnh ổ đĩa', 'Nén tệp tin', 'A',
     'Phishing là hình thức lừa đảo trực tuyến nhằm đánh cắp thông tin nhạy cảm.'),
    ('c7', 'C', 'Đâu là dấu hiệu nhận biết một trang web có kết nối mã hóa an toàn trên trình duyệt?',
     'Địa chỉ bắt đầu bằng https:// và có biểu tượng ổ khóa', 'Trang web có nhiều quảng cáo nhấp nháy',
     'Địa chỉ bắt đầu bằng http:// không có chữ s', 'Trang web yêu cầu tắt phần mềm diệt virus', 'A',
     'Giao thức HTTPS mã hóa dữ liệu truyền giữa trình duyệt và máy chủ.'),
    ('c8', 'C', 'Cách tổ chức thư mục và tệp tin nào trên đám mây giúp tìm kiếm nhanh và khoa học nhất?',
     'Lưu tất cả tệp vào một thư mục duy nhất không đặt tên', 'Phân cấp thư mục theo Năm học -> Môn học -> Chủ đề và đặt tên tệp rõ nghĩa',
     'Đặt tên tệp bằng các ký tự ngẫu nhiên 1, 2, 3', 'Tạo hàng trăm thư mục rỗng không chứa tệp', 'B',
     'Cấu trúc thư mục hình cây phân cấp theo chủ đề và tên tệp chuẩn hóa giúp tra cứu tức thì.'),

    # --- CHỦ ĐỀ F (8 câu) ---
    ('f1', 'F', 'Câu lệnh SQL nào lấy danh sách ho_ten, diem từ bảng HOC_SINH của lớp "11A1" và sắp xếp điểm giảm dần?',
     'SELECT ho_ten, diem FROM HOC_SINH WHERE lop = "11A1" ORDER BY diem DESC;',
     'GET ho_ten, diem FROM HOC_SINH HAVING lop = "11A1" SORT diem DESC;',
     'SELECT ho_ten, diem IN HOC_SINH WHERE lop = "11A1" ORDER BY diem ASC;',
     'UPDATE HOC_SINH SET ho_ten, diem WHERE lop = "11A1";', 'A',
     'Cú pháp chuẩn: SELECT <cột> FROM <bảng> WHERE <điều kiện> ORDER BY <cột> DESC.'),
    ('f2', 'F', 'Trong mô hình cơ sở dữ liệu quan hệ, mỗi hàng (row) của bảng được gọi là gì?',
     'Một trường (Field / Thuộc tính)', 'Một bản ghi (Record / Bộ)', 'Một khóa ngoại (Foreign Key)', 'Một câu truy vấn (Query)', 'B',
     'Mỗi hàng trong bảng biểu diễn một bản ghi (bộ/record), mỗi cột biểu diễn một trường (thuộc tính).'),
    ('f3', 'F', 'Tính chất bắt buộc của cột được chọn làm Khóa chính (Primary Key) trong bảng CSDL quan hệ là gì?',
     'Có thể trùng lặp và để trống (NULL)', 'Giá trị phải duy nhất (UNIQUE) và không được để trống (NOT NULL)',
     'Bắt buộc phải có kiểu dữ liệu ngày tháng', 'Chỉ được chứa chữ cái in thường', 'B',
     'Khóa chính định danh duy nhất mỗi bản ghi nên không được trùng lặp và không được rỗng.'),
    ('f4', 'F', 'Khóa ngoại (Foreign Key) trong cơ sở dữ liệu quan hệ có vai trò gì?',
     'Tăng kích thước phông chữ của bảng', 'Liên kết dữ liệu giữa hai bảng và đảm bảo toàn vẹn tham chiếu',
     'Xóa toàn bộ dữ liệu trong bảng khi tắt máy', 'Mã hóa mật khẩu người dùng', 'B',
     'Khóa ngoại tham chiếu đến khóa chính của bảng khác để thiết lập liên kết giữa các bảng.'),
    ('f5', 'F', 'Trong ngôn ngữ SQL, mệnh đề nào được sử dụng để kết nối dữ liệu từ hai bảng dựa trên trường chung?',
     'INNER JOIN ... ON ...', 'DELETE FROM ...', 'DROP TABLE ...', 'CREATE DATABASE ...', 'A',
     'Mệnh đề INNER JOIN ... ON kết hợp các bản ghi từ 2 bảng có giá trị khóa khớp nhau.'),
    ('f6', 'F', 'Câu lệnh SQL nào dùng để thêm một bản ghi mới vào bảng SACH?',
     'INSERT INTO SACH VALUES (...);', 'SELECT * FROM SACH;', 'UPDATE SACH SET ...;', 'DELETE FROM SACH;', 'A',
     'INSERT INTO dùng để chèn thêm dòng dữ liệu mới vào bảng.'),
    ('f7', 'F', 'Để cập nhật điểm môn Tin của học sinh có ma_hs = "HS01" thành 9.5 trong bảng DIEM, ta dùng lệnh nào?',
     'UPDATE DIEM SET diem_tin = 9.5 WHERE ma_hs = "HS01";',
     'ALTER TABLE DIEM SET diem_tin = 9.5;',
     'SELECT diem_tin = 9.5 FROM DIEM WHERE ma_hs = "HS01";',
     'REMOVE FROM DIEM WHERE ma_hs = "HS01";', 'A',
     'Cú pháp cập nhật dữ liệu: UPDATE <bảng> SET <cột> = <giá_trị> WHERE <điều_kiện>.'),
    ('f8', 'F', 'Hệ quản trị cơ sở dữ liệu (DBMS) nào sau đây là phần mềm nguồn mở thông dụng?',
     'PostgreSQL / MySQL', 'Microsoft Word', 'GIMP Image Editor', 'VLC Media Player', 'A',
     'PostgreSQL, MySQL và SQLite là các hệ quản trị CSDL quan hệ phổ biến.'),

    # --- CHỦ ĐỀ E (8 câu) ---
    ('e1', 'E', 'Trong phần mềm chỉnh sửa ảnh GIMP, việc sử dụng nhiều Lớp ảnh (Layers) mang lại lợi ích gì?',
     'Làm giảm độ phân giải của bức ảnh gốc xuống mức thấp nhất',
     'Tách biệt và chỉnh sửa từng thành phần độc lập mà không làm hỏng các lớp khác',
     'Chỉ cho phép lưu ảnh dưới định dạng văn bản .txt',
     'Tự động xóa toàn bộ màu sắc của ảnh thành đen trắng', 'B',
     'Layer giúp quản lý và chỉnh sửa từng đối tượng hình ảnh độc lập.'),
    ('e2', 'E', 'Khi xuất ảnh từ GIMP để giữ được vùng nền trong suốt (Alpha Channel) chèn vào web, ta chọn định dạng nào?',
     'PNG', 'JPG / JPEG', 'BMP', 'TXT', 'A',
     'Định dạng PNG hỗ trợ kênh Alpha lưu độ trong suốt, còn JPG không hỗ trợ nền trong suốt.'),
    ('e3', 'E', 'Định dạng tệp dự án gốc mặc định của phần mềm GIMP (lưu giữ nguyên toàn bộ các Layer) là gì?',
     '.xcf', '.psd', '.docx', '.mp4', 'A',
     'Tệp .xcf là định dạng gốc của GIMP giúp lưu lại mọi lớp ảnh, kênh và đường dẫn.'),
    ('e4', 'E', 'Trong GIMP, công cụ nào dùng để cắt bỏ phần rìa thừa và giữ lại khung hình mong muốn của bức ảnh?',
     'Crop Tool', 'Bucket Fill Tool', 'Text Tool', 'Zoom Tool', 'A',
     'Crop Tool dùng để cắt xén khung ảnh theo vùng chọn chữ nhật.'),
    ('e5', 'E', 'Công cụ Clone Tool (hoặc Healing Tool) trong GIMP thường được ứng dụng để làm gì?',
     'Xóa chi tiết thừa hoặc vết xước bằng cách sao chép vùng điểm ảnh lân cận',
     'Tạo bảng cơ sở dữ liệu mới', 'Gửi thư điện tử tự động', 'Nén tệp video sang MP3', 'A',
     'Clone/Healing Tool lấy mẫu vùng ảnh lành lặn để đắp lên vùng khuyết điểm.'),
    ('e6', 'E', 'Trong phần mềm biên tập video, thanh Thời gian (Timeline) có chức năng chính là gì?',
     'Sắp xếp thứ tự các phân cảnh (clip), chèn âm thanh, phụ đề và hiệu ứng chuyển cảnh theo trục thời gian',
     'Dùng để viết câu lệnh truy vấn SQL', 'Dùng để cài đặt trình điều khiển máy in', 'Dùng để định dạng ổ cứng', 'A',
     'Timeline là khu vực trung tâm để cắt ghép video, đồng bộ âm thanh và hiệu ứng theo thời gian.'),
    ('e7', 'E', 'Định dạng tệp nào sau đây là định dạng xuất video phổ biến, tương thích hầu hết trình duyệt và thiết bị?',
     '.mp4', '.xcf', '.sql', '.pptx', 'A',
     'MP4 (H.264/AAC) là chuẩn tệp video thông dụng nhất hiện nay.'),
    ('e8', 'E', 'Trong GIMP, để thay đổi kích thước (chiều rộng và chiều cao) của một lớp ảnh đang chọn, ta dùng công cụ nào?',
     'Scale Tool', 'Move Tool', 'Color Picker Tool', 'Eraser Tool', 'A',
     'Scale Tool cho phép phóng to hoặc thu nhỏ kích thước của Layer hoặc vùng chọn.')
]

# Part II: True/False 4-statement questions (a, b, c, d) -> 10 questions across Common, CS, and ICT
_TF4_RAW = [
    # --- PHẦN CHUNG (COMMON - 4 câu) ---
    {
        'id': 'tf_common_1',
        'topic': 'A',
        'topic_label': TOPIC_LABELS['A'],
        'group': 'COMMON',
        'group_label': 'Phần chung',
        'question_type': 'true_false',
        'content': 'Một trường THPT triển khai phòng máy tính mới phục vụ môn Tin học 11 với hai phương án: cài hệ điều hành nguồn mở Ubuntu Linux kèm LibreOffice hoặc cài Windows thương mại. Khi thảo luận về hệ điều hành và phần mềm, nhóm học sinh đưa ra các nhận định sau:',
        'option_a': 'Hệ điều hành là phần mềm hệ thống làm cầu nối trung gian giữa người dùng, phần mềm ứng dụng và phần cứng máy tính.',
        'option_b': 'Phần mềm nguồn mở hoàn toàn không có giấy phép sử dụng và không ai được phép xem mã nguồn.',
        'option_c': 'Ubuntu Linux và LibreOffice giúp nhà trường tiết kiệm chi phí bản quyền và cho phép tự do cài đặt cho học sinh thực hành.',
        'option_d': 'Khi tắt nguồn máy tính, toàn bộ hệ điều hành đang lưu trên ổ cứng SSD sẽ bị xóa sạch giống như dữ liệu trên RAM.',
        'correct_option': 'D,S,D,S',
        'points': 1.0,
        'explanation': 'a) Đúng; b) Sai (Phần mềm nguồn mở có giấy phép như GPL/MIT và công khai mã nguồn); c) Đúng; d) Sai (SSD là bộ nhớ ngoài bất khả biến, không mất dữ liệu khi tắt nguồn).'
    },
    {
        'id': 'tf_common_2',
        'topic': 'C',
        'topic_label': TOPIC_LABELS['C'],
        'group': 'COMMON',
        'group_label': 'Phần chung',
        'question_type': 'true_false',
        'content': 'Nhóm học sinh lớp 11A1 sử dụng Google Drive để lưu trữ tài liệu dự án môn Tin học và dùng máy tìm kiếm để tra cứu tư liệu tham khảo. Các bạn nêu các ý kiến sau:',
        'option_a': 'Khi chia sẻ thư mục dự án trên Google Drive với quyền "Người xem" (Viewer), các thành viên khác chỉ đọc và tải về chứ không thể xóa tệp.',
        'option_b': 'Sử dụng cú pháp tìm kiếm "Cơ sở dữ liệu" filetype:pdf trên Google giúp lọc các tài liệu PDF chứa cụm từ "Cơ sở dữ liệu".',
        'option_c': 'Để bảo mật tài khoản lưu trữ đám mây, học sinh nên tắt xác thực hai bước (2FA) và dùng chung một mật khẩu cho mọi trang web.',
        'option_d': 'Tệp tin lưu trên đám mây có thể truy cập đồng bộ từ cả máy tính ở trường và điện thoại cá nhân khi có kết nối Internet.',
        'correct_option': 'D,D,S,D',
        'points': 1.0,
        'explanation': 'a) Đúng; b) Đúng; c) Sai (Phải bật xác thực 2FA và dùng mật khẩu riêng mạnh); d) Đúng.'
    },
    {
        'id': 'tf_common_3',
        'topic': 'F',
        'topic_label': TOPIC_LABELS['F'],
        'group': 'COMMON',
        'group_label': 'Phần chung',
        'question_type': 'true_false',
        'content': 'Thư viện nhà trường chuyển đổi cách quản lý mượn trả sách từ sổ giấy sang hệ thống Cơ sở dữ liệu (CSDL) trên máy tính. Khi phân tích ưu điểm của CSDL, học sinh đưa ra các nhận định:',
        'option_a': 'Lưu trữ bằng CSDL giúp giảm dư thừa dữ liệu và đảm bảo tính nhất quán khi cập nhật thông tin bạn đọc.',
        'option_b': 'Hệ quản trị CSDL (DBMS) cung cấp các cơ chế phân quyền truy cập và sao lưu phục hồi khi có sự cố.',
        'option_c': 'Khi dùng CSDL, mỗi lần chỉ có tối đa một người duy nhất được tra cứu danh mục sách, không thể tra cứu đồng thời qua mạng.',
        'option_d': 'CSDL là một tập hợp các dữ liệu có liên quan với nhau, được tổ chức có cấu trúc để máy tính có thể lưu trữ và khai thác.',
        'correct_option': 'D,D,S,D',
        'points': 1.0,
        'explanation': 'a) Đúng; b) Đúng; c) Sai (Hệ CSDL hỗ trợ nhiều người dùng truy cập đồng thời); d) Đúng.'
    },
    {
        'id': 'tf_common_4',
        'topic': 'C',
        'topic_label': TOPIC_LABELS['C'],
        'group': 'COMMON',
        'group_label': 'Phần chung',
        'question_type': 'true_false',
        'content': 'Trong buổi sinh hoạt chuyên đề "An toàn trên không gian số", giáo viên đưa ra tình huống một học sinh nhận được email thông báo trúng thưởng yêu cầu bấm vào đường link lạ và nhập mật khẩu email. Các nhận định dưới đây là Đúng hay Sai?',
        'option_a': 'Đây là dấu hiệu điển hình của hình thức tấn công giả mạo (Phishing) nhằm đánh cắp tài khoản.',
        'option_b': 'Học sinh nên lập tức nhập mật khẩu và mã OTP vào đường link đó để nhận phần thưởng.',
        'option_c': 'Cần kiểm tra kỹ địa chỉ tên miền người gửi và tuyệt đối không cung cấp mã OTP cho bất kỳ ai.',
        'option_d': 'Giao thức https:// có biểu tượng ổ khóa trên trình duyệt cho biết dữ liệu truyền tải giữa trình duyệt và máy chủ được mã hóa.',
        'correct_option': 'D,S,D,D',
        'points': 1.0,
        'explanation': 'a) Đúng; b) Sai (Tuyệt đối không nhập mật khẩu/OTP vào link lạ); c) Đúng; d) Đúng.'
    },

    # --- PHẦN RIÊNG: ĐỊNH HƯỚNG KHOA HỌC MÁY TÍNH (CS - 3 câu) ---
    {
        'id': 'tf_cs_1',
        'topic': 'A',
        'topic_label': TOPIC_LABELS['A'],
        'group': 'CS',
        'group_label': 'Định hướng Khoa học máy tính',
        'question_type': 'true_false',
        'content': '[Định hướng Khoa học máy tính] Khi tìm hiểu về cổng logic, biểu diễn dữ liệu nhị phân và thực thi chương trình bên trong bộ xử lý trung tâm (CPU), một học sinh phát biểu các mệnh đề sau:',
        'option_a': 'Mọi dữ liệu (số, văn bản, hình ảnh, âm thanh) khi lưu trữ và xử lý trong máy tính đều được mã hóa thành dãy bit nhị phân (0 và 1).',
        'option_b': 'Cổng logic AND chỉ cho đầu ra bằng 1 khi cả hai đầu vào đều bằng 1.',
        'option_c': 'Bộ nhớ truy cập ngẫu nhiên RAM có tốc độ truy xuất chậm hơn ổ đĩa cứng từ HDD truyền thống.',
        'option_d': 'Cổng logic NOT thực hiện phép đảo bit: đầu vào là 0 thì đầu ra là 1 và ngược lại.',
        'correct_option': 'D,D,S,D',
        'points': 1.0,
        'explanation': 'a) Đúng; b) Đúng; c) Sai (RAM là bộ nhớ trong bán dẫn, nhanh hơn HDD rất nhiều lần); d) Đúng.'
    },
    {
        'id': 'tf_cs_2',
        'topic': 'F',
        'topic_label': TOPIC_LABELS['F'],
        'group': 'CS',
        'group_label': 'Định hướng Khoa học máy tính',
        'question_type': 'true_false',
        'content': '[Định hướng Khoa học máy tính] Cho danh sách điểm thi đã được sắp xếp tăng dần của 1.000 học sinh. Khi so sánh thuật toán Tìm kiếm tuần tự (Sequential Search) và Tìm kiếm nhị phân (Binary Search) trên danh sách này:',
        'option_a': 'Thuật toán tìm kiếm nhị phân chia đôi phạm vi tìm kiếm ở mỗi bước nên có số lần so sánh tối đa rất nhỏ (khoảng 10 bước với 1.000 phần tử).',
        'option_b': 'Thuật toán tìm kiếm nhị phân có thể áp dụng chính xác trên cả mảng dữ liệu chưa được sắp xếp.',
        'option_c': 'Trong trường hợp xấu nhất, thuật toán tìm kiếm tuần tự trên n phần tử phải thực hiện n phép so sánh.',
        'option_d': 'Độ phức tạp thời gian của tìm kiếm nhị phân là O(log n), hiệu quả hơn O(n) của tìm kiếm tuần tự khi n lớn.',
        'correct_option': 'D,S,D,D',
        'points': 1.0,
        'explanation': 'a) Đúng (2^10 = 1024); b) Sai (Tìm kiếm nhị phân bắt buộc dữ liệu phải được sắp xếp trước); c) Đúng; d) Đúng.'
    },
    {
        'id': 'tf_cs_3',
        'topic': 'A',
        'topic_label': TOPIC_LABELS['A'],
        'group': 'CS',
        'group_label': 'Định hướng Khoa học máy tính',
        'question_type': 'true_false',
        'content': '[Định hướng Khoa học máy tính] Khi thiết kế thuật toán sắp xếp và đánh giá hiệu quả chương trình bằng phương pháp làm mịn dần (Stepwise Refinement), các nhận định sau là Đúng hay Sai?',
        'option_a': 'Phương pháp làm mịn dần giúp chia bài toán lớn phức tạp thành các bài toán con nhỏ hơn, dễ cài đặt và kiểm thử.',
        'option_b': 'Các thuật toán sắp xếp cơ bản như Nổi bọt (Bubble Sort), Chọn (Selection Sort) và Chèn (Insertion Sort) đều có độ phức tạp thời gian trung bình cỡ O(n²).',
        'option_c': 'Một thuật toán đúng đắn thì không bao giờ cần kết thúc sau hữu hạn bước thực hiện.',
        'option_d': 'Sử dụng hàm (chương trình con) giúp tái sử dụng mã nguồn và làm chương trình rõ ràng, dễ bảo trì hơn.',
        'correct_option': 'D,D,S,D',
        'points': 1.0,
        'explanation': 'a) Đúng; b) Đúng; c) Sai (Tính dừng/hữu hạn là tính chất bắt buộc của thuật toán); d) Đúng.'
    },

    # --- PHẦN RIÊNG: ĐỊNH HƯỚNG TIN HỌC ỨNG DỤNG (ICT - 3 câu) ---
    {
        'id': 'tf_ict_1',
        'topic': 'F',
        'topic_label': TOPIC_LABELS['F'],
        'group': 'ICT',
        'group_label': 'Định hướng Tin học ứng dụng',
        'question_type': 'true_false',
        'content': '[Định hướng Tin học ứng dụng] Cho CSDL Quản lý điểm gồm bảng HOC_SINH(ma_hs, ho_ten, ma_lop) và bảng DIEM(ma_hs, ma_mon, diem_so). Xét các nhận định về khóa và truy vấn SQL:',
        'option_a': 'Trong bảng HOC_SINH, trường ma_hs được chọn làm Khóa chính (Primary Key) nên không được phép để trống (NULL) hoặc trùng lặp.',
        'option_b': 'Trường ma_hs trong bảng DIEM đóng vai trò là Khóa ngoại (Foreign Key) tham chiếu tới bảng HOC_SINH.',
        'option_c': 'Câu lệnh SELECT ho_ten FROM HOC_SINH WHERE ma_lop = "11A1" ORDER BY ho_ten DESC; dùng để xóa toàn bộ học sinh lớp 11A1.',
        'option_d': 'Để lấy danh sách họ tên học sinh kèm điểm số từ cả 2 bảng, ta sử dụng mệnh đề INNER JOIN kết nối qua trường chung ma_hs.',
        'correct_option': 'D,D,S,D',
        'points': 1.0,
        'explanation': 'a) Đúng; b) Đúng; c) Sai (SELECT chỉ truy vấn hiển thị dữ liệu, không xóa dữ liệu); d) Đúng.'
    },
    {
        'id': 'tf_ict_2',
        'topic': 'E',
        'topic_label': TOPIC_LABELS['E'],
        'group': 'ICT',
        'group_label': 'Định hướng Tin học ứng dụng',
        'question_type': 'true_false',
        'content': '[Định hướng Tin học ứng dụng] Một học sinh thiết kế áp phích tuyên truyền ngày Sách Việt Nam bằng phần mềm xử lý ảnh GIMP với 3 lớp ảnh (Layer): Lớp nền, Lớp biểu trưng (Logo) và Lớp chữ tiêu đề. Các phát biểu sau là Đúng hay Sai?',
        'option_a': 'Việc đặt Logo và chữ tiêu đề trên các Layer riêng biệt cho phép di chuyển, phóng to từng phần tử mà không làm hỏng lớp nền.',
        'option_b': 'Để tách nền cho Logo thành nền trong suốt, lớp ảnh Logo cần có kênh Alpha (Add Alpha Channel) và xuất ra định dạng PNG.',
        'option_c': 'Nếu lưu tệp sang định dạng .JPG thì mọi lớp ảnh (Layers) vẫn được giữ nguyên tách rời để hôm sau mở lên sửa tiếp từng lớp.',
        'option_d': 'Biểu tượng con mắt bên cạnh mỗi Layer trong hộp thoại Layers dùng để ẩn hoặc hiện lớp ảnh đó.',
        'correct_option': 'D,D,S,D',
        'points': 1.0,
        'explanation': 'a) Đúng; b) Đúng; c) Sai (JPG gộp phẳng các lớp; muốn giữ nguyên các Layer phải lưu định dạng dự án .XCF); d) Đúng.'
    },
    {
        'id': 'tf_ict_3',
        'topic': 'E',
        'topic_label': TOPIC_LABELS['E'],
        'group': 'ICT',
        'group_label': 'Định hướng Tin học ứng dụng',
        'question_type': 'true_false',
        'content': '[Định hướng Tin học ứng dụng] Nhóm học sinh thực hiện biên tập video giới thiệu trường THPT từ các đoạn phim quay bằng điện thoại, ảnh chụp hoạt động và tệp nhạc nền MP3. Khi dựng video trên phần mềm:',
        'option_a': 'Trên thanh Timeline, học sinh có thể cắt bỏ các đoạn video bị rung, sắp xếp thứ tự phân cảnh và chèn hiệu ứng chuyển cảnh (Transition).',
        'option_b': 'Có thể điều chỉnh âm lượng nhạc nền nhỏ xuống ở những đoạn có giọng thuyết minh để người xem nghe rõ lời dẫn.',
        'option_c': 'Sau khi xuất sản phẩm hoàn chỉnh ra tệp .mp4, tệp này chỉ xem được trên máy tính đã dựng phim chứ không thể phát trên trình duyệt web.',
        'option_d': 'Việc thêm phụ đề văn bản (Text / Subtitle) đồng bộ với lời thoại giúp người xem nắm bắt nội dung chính xác hơn.',
        'correct_option': 'D,D,S,D',
        'points': 1.0,
        'explanation': 'a) Đúng; b) Đúng; c) Sai (Định dạng .mp4 tương thích rộng rãi trên mọi trình duyệt web và thiết bị di động); d) Đúng.'
    }
]

SYSTEM_QUESTION_BANK = [
    {
        'id': f'bank_{qid}',
        'topic': topic,
        'topic_label': TOPIC_LABELS[topic],
        'group': 'PART1',
        'group_label': 'Phần I: Trắc nghiệm 4 lựa chọn',
        'question_type': 'mcq',
        'content': content,
        'option_a': oa,
        'option_b': ob,
        'option_c': oc,
        'option_d': od,
        'correct_option': ans,
        'points': 0.25,
        'explanation': exp
    }
    for (qid, topic, content, oa, ob, oc, od, ans, exp) in _MCQ_RAW
] + _TF4_RAW


def normalize_tf_token(tok):
    t = (tok or '').strip().upper()
    if t in ('D', 'Đ', 'ĐÚNG', 'DUNG', 'TRUE', 'T', '1'):
        return 'D'
    if t in ('S', 'SAI', 'FALSE', 'F', '0'):
        return 'S'
    return ''


def normalize_tf_pattern(raw):
    """Normalize 'D,S,D,D' or 'TRUE,FALSE,TRUE,TRUE' into a 4-item list ['D', 'S', 'D', 'D']."""
    val = (raw or '').strip()
    if ',' in val:
        parts = [normalize_tf_token(x) for x in val.split(',')]
    elif len(val) == 4 and all(c.upper() in ('D', 'Đ', 'S', 'T', 'F') for c in val):
        parts = [normalize_tf_token(c) for c in val]
    else:
        single = normalize_tf_token(val) or 'D'
        parts = [single, 'S', 'D', 'S']
    while len(parts) < 4:
        parts.append('D')
    return [p or 'D' for p in parts[:4]]


def score_true_false_4(user_raw, correct_raw):
    """
    Grade a 4-statement True/False question (a, b, c, d):
      1 correct -> 0.1 pt
      2 correct -> 0.25 pt
      3 correct -> 0.5 pt
      4 correct -> 1.0 pt
    Returns (score, correct_count, user_list, correct_list)
    """
    correct_list = normalize_tf_pattern(correct_raw)
    if isinstance(user_raw, (list, tuple)):
        user_list = [normalize_tf_token(x) for x in user_raw[:4]]
    else:
        raw_str = (user_raw or '').strip()
        user_list = [normalize_tf_token(x) for x in raw_str.split(',')] if raw_str else []
    while len(user_list) < 4:
        user_list.append('')

    hits = sum(1 for u, c in zip(user_list, correct_list) if u and u == c)
    return TF_SCORE_TABLE[hits], hits, user_list, correct_list


def generate_random_practice_exam(topic_filter='ALL'):
    """
    Generate a randomized practice exam from SYSTEM_QUESTION_BANK following the exact specification:
      - Part I: 24 multiple-choice questions (4 options, 0.25 pts each, max 6.0 pts).
      - Part II: 06 True/False 4-statement questions (a, b, c, d; Common + CS/ICT orientation; 0.1 / 0.25 / 0.5 / 1.0 pts).
    """
    import random

    mcq_pool = [dict(q) for q in SYSTEM_QUESTION_BANK if q['question_type'] == 'mcq']
    tf_pool = [dict(q) for q in SYSTEM_QUESTION_BANK if q['question_type'] == 'true_false']

    mapped_topic = TOPIC_FILTER_MAP.get(str(topic_filter).upper(), '')
    if mapped_topic in ('A', 'C', 'F', 'E'):
        topic_mcq = [q for q in mcq_pool if q['topic'] == mapped_topic]
        other_mcq = [q for q in mcq_pool if q['topic'] != mapped_topic]
        random.shuffle(topic_mcq)
        random.shuffle(other_mcq)
        part1 = (topic_mcq + other_mcq)[:24]
    else:
        part1 = random.sample(mcq_pool, min(24, len(mcq_pool)))

    # Part II: 2 Common + 2 CS + 2 ICT (total 06 questions)
    common_tf = [q for q in tf_pool if q.get('group') == 'COMMON']
    cs_tf = [q for q in tf_pool if q.get('group') == 'CS']
    ict_tf = [q for q in tf_pool if q.get('group') == 'ICT']

    picked_common = random.sample(common_tf, min(2, len(common_tf)))
    picked_cs = random.sample(cs_tf, min(2, len(cs_tf)))
    picked_ict = random.sample(ict_tf, min(2, len(ict_tf)))
    part2 = picked_common + picked_cs + picked_ict

    if len(part2) < 6:
        used_ids = {q['id'] for q in part2}
        remaining = [q for q in tf_pool if q['id'] not in used_ids]
        part2.extend(random.sample(remaining, min(6 - len(part2), len(remaining))))

    for q in part2:
        q['correct_list'] = normalize_tf_pattern(q.get('correct_option', 'D,S,D,D'))
        q['correct_option'] = ','.join(q['correct_list'])

    return part1, part2


def parse_questions_from_upload(file_storage):
    """
    ponytail parser: Extract questions (mcq, true_false 4-statement) from uploaded .csv, .txt, or .docx.
    CSV/TXT format per line:
      question_type,content,option_a,option_b,option_c,option_d,correct_option,points
    """
    import csv
    import io

    filename = (file_storage.filename or '').lower()
    parsed = []

    if filename.endswith('.docx'):
        doc = Document(file_storage)
        for table in doc.tables:
            for idx, row in enumerate(table.rows):
                cells = [c.text.strip() for c in row.cells]
                if not cells or not any(cells):
                    continue
                if idx == 0 and ('loại' in cells[0].lower() or 'type' in cells[0].lower() or 'nội dung' in cells[0].lower()):
                    continue
                item = _row_to_question_dict(cells)
                if item:
                    parsed.append(item)
        for p in doc.paragraphs:
            line = p.text.strip()
            if not line or line.startswith('#'):
                continue
            if '|' in line:
                parts = [x.strip() for x in line.split('|')]
                item = _row_to_question_dict(parts)
                if item:
                    parsed.append(item)
    else:
        raw = file_storage.read().decode('utf-8-sig', errors='replace')
        reader = csv.reader(io.StringIO(raw))
        for idx, row in enumerate(reader):
            cells = [c.strip() for c in row]
            if not cells or not any(cells):
                continue
            if idx == 0 and ('loại' in cells[0].lower() or 'type' in cells[0].lower() or 'question_type' in cells[0].lower()):
                continue
            item = _row_to_question_dict(cells)
            if item:
                parsed.append(item)

    return parsed


def _row_to_question_dict(cells):
    if len(cells) < 6:
        return None
    q_type = cells[0].lower().strip()
    if q_type in ['mcq', 'trac_nghiem', 'trắc nghiệm']:
        q_type = 'mcq'
    elif q_type in ['true_false', 'tf', 'dung_sai', 'đúng sai', 'đúng/sai']:
        q_type = 'true_false'
    else:
        return {
            'question_type': 'mcq',
            'content': cells[0],
            'option_a': cells[1],
            'option_b': cells[2],
            'option_c': cells[3],
            'option_d': cells[4],
            'correct_option': cells[5].upper().strip()[:1] or 'A',
            'points': float(cells[6]) if len(cells) >= 7 and _is_float(cells[6]) else 0.25
        }

    if len(cells) < 7:
        return None
    content = cells[1].strip()
    if not content:
        return None

    if q_type == 'mcq':
        return {
            'question_type': 'mcq',
            'content': content,
            'option_a': cells[2],
            'option_b': cells[3],
            'option_c': cells[4],
            'option_d': cells[5],
            'correct_option': cells[6].upper().strip()[:1] or 'A',
            'points': float(cells[7]) if len(cells) >= 8 and _is_float(cells[7]) else 0.25
        }
    elif q_type == 'true_false':
        ans_norm = ','.join(normalize_tf_pattern(cells[6]))
        return {
            'question_type': 'true_false',
            'content': content,
            'option_a': cells[2],
            'option_b': cells[3],
            'option_c': cells[4],
            'option_d': cells[5],
            'correct_option': ans_norm,
            'points': float(cells[7]) if len(cells) >= 8 and _is_float(cells[7]) else 1.0
        }
    return None


def _is_float(val):
    try:
        float(val)
        return True
    except Exception:
        return False


def get_poster_image(title):
    """Map a topic or lesson title to its corresponding flat academic poster image."""
    t = (title or '').lower()
    if any(k in t for k in ['phần cứng', 'bên trong máy tính', 'cpu', 'thiết bị số', 'bài 4.', 'bài 5.']):
        return 'img/posters/poster_a_hardware.jpg'
    if any(k in t for k in ['web', 'html', 'css', 'trang web', 'chủ đề 6', 'bài 17.', 'bài 18.', 'bài 19.', 'bài 20.', 'bài 21.', 'bài 22.', 'bài 23.', 'bài 24.']):
        return 'img/posters/poster_f_web.jpg'
    if any(k in t for k in ['gimp', 'ảnh', 'alpha', 'layer', 'video', 'làm phim', 'biên tập phim', 'hoạt hình', 'màu sắc', 'công cụ vẽ', 'chủ đề 7', 'chủ đề e']):
        return 'img/posters/poster_e_gimp.jpg'
    if any(k in t for k in ['csdl', 'cơ sở dữ liệu', 'sql', 'truy vấn', 'khóa ngoại', 'trường khoá', 'sao lưu', 'chủ đề 4', 'chủ đề 5', 'chủ đề f']):
        return 'img/posters/poster_f_database.jpg'
    if any(k in t for k in ['đám mây', 'tìm kiếm', 'lưu trữ và chia sẻ', 'thư điện tử', 'mạng xã hội', 'giao tiếp an toàn', 'đạo đức', 'chủ đề 2', 'chủ đề 3', 'chủ đề c']):
        return 'img/posters/poster_c_cloud.jpg'
    return 'img/posters/poster_a_os.jpg'


def render_video_embed(raw_input):
    """
    Convert a YouTube link (watch?v=..., youtu.be/..., shorts/..., embed/...),
    direct video URL (.mp4/.webm), or raw HTML (<iframe ...>, <video ...>)
    into a responsive 16:9 HTML video player.
    """
    import re
    from markupsafe import Markup, escape

    val = (raw_input or '').strip()
    if not val:
        return Markup('')

    low = val.lower()
    if '<iframe' in low or '<video' in low or '<embed' in low:
        return Markup(
            f'<div class="aspect-[16/9] w-full rounded-xl overflow-hidden bg-slate-950 border border-slate-800 [&_iframe]:w-full [&_iframe]:h-full [&_video]:w-full [&_video]:h-full">{val}</div>'
        )

    # Match YouTube video ID from common URL patterns
    yt_match = re.search(
        r'(?:youtube\.com/(?:watch\?v=|embed/|shorts/|v/)|youtu\.be/)([A-Za-z0-9_-]{6,20})',
        val
    )
    if yt_match:
        video_id = yt_match.group(1)
        embed_url = f'https://www.youtube.com/embed/{escape(video_id)}'
        return Markup(
            f'<div class="aspect-[16/9] w-full rounded-xl overflow-hidden bg-slate-950 border border-slate-800">'
            f'<iframe src="{embed_url}" title="YouTube video bài giảng" class="w-full h-full border-0" '
            f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
            f'allowfullscreen></iframe></div>'
        )

    if any(low.endswith(ext) for ext in ('.mp4', '.webm', '.ogg', '.mov')):
        safe_url = escape(val)
        return Markup(
            f'<div class="rounded-xl overflow-hidden bg-slate-950 border border-slate-800">'
            f'<video controls preload="metadata" class="w-full max-h-[420px] mx-auto block">'
            f'<source src="{safe_url}">Trình duyệt không hỗ trợ phát video trực tiếp.</video></div>'
        )

    if low.startswith('http://') or low.startswith('https://'):
        safe_url = escape(val)
        return Markup(
            f'<div class="aspect-[16/9] w-full rounded-xl overflow-hidden bg-slate-950 border border-slate-800">'
            f'<iframe src="{safe_url}" title="Video bài giảng" class="w-full h-full border-0" allowfullscreen></iframe></div>'
        )

    return Markup(f'<div class="p-4 rounded-xl bg-slate-50 border border-slate-200 text-sm text-slate-700">{escape(val)}</div>')


def format_lesson_sections(content):
    """
    Format lesson text into structured headings (#, ##, I., II., 1., 2.),
    semantic lists (- / • / *), and paragraphs so Admin/Teacher can freely
    organize lesson sections and sub-headings.
    """
    import re
    from markupsafe import Markup, escape

    raw = (content or '').strip()
    if not raw:
        return Markup('')

    lines = raw.splitlines()
    parts = []
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            parts.append('</ul>')
            in_list = False

    for line in lines:
        s = line.strip()
        if not s:
            close_list()
            continue
        if s.startswith('## '):
            close_list()
            heading_text = escape(s[3:].strip())
            parts.append(
                f'<h4 class="text-base font-bold text-slate-900 mt-4 mb-1.5">{heading_text}</h4>'
            )
        elif s.startswith('# '):
            close_list()
            heading_text = escape(s[2:].strip())
            parts.append(
                f'<h3 class="text-lg font-extrabold text-[#0B4FD8] mt-5 mb-2 border-l-4 border-[#0B4FD8] pl-3">{heading_text}</h3>'
            )
        elif re.match(r'^(I|II|III|IV|V|VI|VII|VIII|IX|X|Phần\s+\d+|Mục\s+\d+)[\.\:]\s+', s, re.IGNORECASE):
            close_list()
            parts.append(
                f'<h3 class="text-base font-extrabold text-[#0B4FD8] mt-4 mb-1.5 border-l-4 border-[#0B4FD8] pl-3">{escape(s)}</h3>'
            )
        elif re.match(r'^\d+[\.\)]\s+', s):
            close_list()
            parts.append(
                f'<p class="font-semibold text-slate-900 mt-3 mb-1">{escape(s)}</p>'
            )
        elif s.startswith('- ') or s.startswith('• ') or s.startswith('* '):
            if not in_list:
                parts.append('<ul class="list-disc pl-5 my-2 space-y-1.5 text-slate-700 marker:text-[#0B4FD8]">')
                in_list = True
            item_text = escape(s[2:].strip())
            parts.append(f'<li class="leading-relaxed">{item_text}</li>')
        else:
            close_list()
            parts.append(f'<p class="text-slate-700 leading-relaxed my-1.5">{escape(s)}</p>')

    close_list()
    return Markup('\n'.join(parts))
