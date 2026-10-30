import os
from flask import Flask
from flask_login import LoginManager
from config import Config
from app.models import db, User
from app.utils import format_file_size

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
        
    # Register blueprints
    from app.auth import auth_bp
    from app.routes import main_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    
    return app
