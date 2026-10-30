import os
import pymupdf as fitz
from docx import Document
from pptx import Presentation

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'pptx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
