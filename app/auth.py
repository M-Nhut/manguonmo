from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User

auth_bp = Blueprint('auth', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Bạn không có quyền truy cập trang quản trị!', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_teacher:
            flash('Chức năng này chỉ dành cho Giáo viên hoặc Quản trị viên!', 'warning')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('main.admin_dashboard'))
        elif current_user.is_teacher:
            return redirect(url_for('main.teacher_dashboard'))
        return redirect(url_for('main.student_dashboard'))
        
    if request.method == 'POST':
        login_input = request.form.get('login_input', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        
        # Support login by username or email
        user = User.query.filter(
            (User.username == login_input) | (User.email == login_input)
        ).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f'Chào mừng bạn trở lại, {user.full_name}!', 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            if user.is_admin:
                return redirect(url_for('main.admin_dashboard'))
            elif user.is_teacher:
                return redirect(url_for('main.teacher_dashboard'))
            return redirect(url_for('main.student_dashboard'))
        else:
            flash('Tên đăng nhập / Email hoặc mật khẩu không chính xác.', 'danger')
            
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'student')
        
        # Basic validation
        if not username or not email or not full_name or not password:
            flash('Vui lòng điền đầy đủ tất cả các trường.', 'warning')
            return render_template('auth/register.html')
            
        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp.', 'warning')
            return render_template('auth/register.html')
            
        if role not in ['student', 'teacher']:
            role = 'student'
            
        # Check existing user
        if User.query.filter_by(username=username).first():
            flash('Tên tài khoản này đã được sử dụng. Vui lòng chọn tên khác.', 'warning')
            return render_template('auth/register.html')
            
        if User.query.filter_by(email=email).first():
            flash('Email này đã được đăng ký tài khoản.', 'warning')
            return render_template('auth/register.html')
            
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            role=role
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Đăng ký tài khoản thành công! Bạn có thể đăng nhập ngay bây giờ.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Bạn đã đăng xuất an toàn.', 'info')
    return redirect(url_for('auth.login'))
