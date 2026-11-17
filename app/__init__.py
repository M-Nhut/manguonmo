import os
from flask import Flask, url_for
from flask_login import LoginManager
from config import Config
from app.models import db, User
from app.utils import (
    format_file_size, get_poster_image,
    render_video_embed, format_lesson_sections
)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Vui lòng đăng nhập để truy cập trang này.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize plugins
    db.init_app(app)
    login_manager.init_app(app)
    
    # Template filters
    @app.template_filter('filesize')
    def filesize_filter(size):
        return format_file_size(size)

    @app.template_filter('poster_img')
    def poster_img_filter(title):
        return get_poster_image(title)

    @app.template_filter('poster_src')
    def poster_src_filter(item):
        if item is None:
            return url_for('static', filename='img/posters/poster_a_os.jpg')
        if isinstance(item, str):
            return url_for('static', filename=get_poster_image(item))
        custom = (getattr(item, 'poster_url', '') or '').strip()
        if custom:
            if custom.startswith('http://') or custom.startswith('https://') or custom.startswith('/'):
                return custom
            return url_for('static', filename=custom)
        title = getattr(item, 'title', '') or ''
        return url_for('static', filename=get_poster_image(title))

    @app.template_filter('video_embed_html')
    def video_embed_html_filter(raw_embed):
        return render_video_embed(raw_embed)

    @app.template_filter('lesson_sections')
    def lesson_sections_filter(content):
        return format_lesson_sections(content)
        
    # Register blueprints
    from app.auth import auth_bp
    from app.routes import main_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)

    # Lightweight SQLite schema sync for new columns
    with app.app_context():
        alter_statements = [
            "ALTER TABLE questions ADD COLUMN question_type VARCHAR(20) NOT NULL DEFAULT 'mcq'",
            "ALTER TABLE courses ADD COLUMN poster_url VARCHAR(500) NOT NULL DEFAULT ''",
            "ALTER TABLE lessons ADD COLUMN poster_url VARCHAR(500) NOT NULL DEFAULT ''",
            "ALTER TABLE lessons ADD COLUMN video_embed TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE exams ADD COLUMN access_code VARCHAR(32) NOT NULL DEFAULT ''",
            "ALTER TABLE exams ADD COLUMN shuffle_questions BOOLEAN NOT NULL DEFAULT 1",
            """CREATE TABLE IF NOT EXISTS game_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                classroom_id INTEGER REFERENCES classrooms(id),
                game_mode VARCHAR(32) NOT NULL DEFAULT 'blitz',
                topic_code VARCHAR(16) NOT NULL DEFAULT 'ALL',
                score INTEGER NOT NULL DEFAULT 0,
                xp_earned INTEGER NOT NULL DEFAULT 0,
                correct_count INTEGER NOT NULL DEFAULT 0,
                total_count INTEGER NOT NULL DEFAULT 0,
                max_combo INTEGER NOT NULL DEFAULT 0,
                duration_sec INTEGER NOT NULL DEFAULT 0,
                week_key VARCHAR(16) NOT NULL,
                played_at DATETIME
            )"""
        ]
        for stmt in alter_statements:
            try:
                db.session.execute(db.text(stmt))
                db.session.commit()
            except Exception:
                db.session.rollback()
    
    return app
