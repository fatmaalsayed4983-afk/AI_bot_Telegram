import os
from pypdf import PdfReader
from docx import Document
import csv
import logging

logger = logging.getLogger(__name__)

class FileAnalyzer:
    @staticmethod
    def analyze_file_content(file_path: str, file_ext: str) -> str:
        if not os.path.exists(file_path):
            return "الملف المرفوع غير متوفر للتجميع."
            
        try:
            if file_ext == '.txt' or file_ext in ['.py', '.js', '.html', '.css', '.sql', '.json', '.java']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read(25000) # Read up to 25k characters
                    
            elif file_ext == '.pdf':
                reader = PdfReader(file_path)
                text = ""
                for idx, page in enumerate(reader.pages):
                    if idx > 15: # Stop at 15 pages for safety
                        break
                    text += page.extract_text() or ""
                return text[:25000]
                
            elif file_ext == '.docx':
                doc = Document(file_path)
                text = "\n".join([p.text for p in doc.paragraphs])
                return text[:25000]
                
            elif file_ext == '.csv':
                rows = []
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    reader = csv.reader(f)
                    for idx, r in enumerate(reader):
                        if idx > 100:
                            break
                        rows.append(", ".join(r))
                return "\n".join(rows)[:25000]
                
            else:
                return f"الملف من صيغة {file_ext} غير مدعوم مباشرة للقراءة تلقائياً بالكامل."
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return f"فشل قراءة الملف بسبب خطأ غير متوقع: {str(e)}"
