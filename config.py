import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tin-hoc-11-ung-dung-secret-key-2026'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"sqlite:///{os.path.join(BASE_DIR, 'elearning_tin11.sqlite3')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload configuration
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 64 * 1024 * 1024  # 64 MB max upload size
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'pptx'}
