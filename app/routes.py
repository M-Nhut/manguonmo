import os
import json
import uuid
from datetime import datetime
from flask import (
    Blueprint, render_template, redirect, url_for, flash, 
    request, jsonify, current_app, send_from_directory, abort
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.models import (
    db, User, Classroom, Course, Lesson, Material, 
    Exam, Question, ExamSubmission, ProctoringLog
)
from app.auth import admin_required, teacher_required
from app.utils import (
    allowed_file, parse_docx_to_html, parse_pptx_slides, 
    get_pdf_metadata, format_file_size
)

main_bp = Blueprint('main', __name__)

# ----------------- HOME & DASHBOARDS -----------------

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('main.admin_dashboard'))
        elif current_user.is_teacher:
            return redirect(url_for('main.teacher_dashboard'))
        return redirect(url_for('main.student_dashboard'))
    return render_template('index.html')


@main_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.order_by(User.created_at.desc()).all()
    classrooms = Classroom.query.all()
    exams = Exam.query.all()
    recent_violations = ProctoringLog.query.order_by(ProctoringLog.timestamp.desc()).limit(10).all()
    
    stats = {
        'total_users': len(users),
        'total_teachers': sum(1 for u in users if u.role == 'teacher'),
        'total_students': sum(1 for u in users if u.role == 'student'),
        'total_classes': len(classrooms),
        'total_exams': len(exams),
        'total_violations': ProctoringLog.query.count()
    }
    return render_template('dashboard/admin.html', stats=stats, users=users, recent_violations=recent_violations)


@main_bp.route('/teacher/dashboard')
@login_required
@teacher_required
def teacher_dashboard():
    my_classrooms = Classroom.query.filter_by(teacher_id=current_user.id).order_by(Classroom.created_at.desc()).all()
    my_exams = Exam.query.filter_by(teacher_id=current_user.id).order_by(Exam.created_at.desc()).all()
    
    # Submissions needing attention (high violations)
    recent_submissions = (
        ExamSubmission.query
        .join(Exam)
        .filter(Exam.teacher_id == current_user.id)
        .order_by(ExamSubmission.started_at.desc())
        .limit(10)
        .all()
    )
    
    return render_template('dashboard/teacher.html', classrooms=my_classrooms, exams=my_exams, submissions=recent_submissions)


@main_bp.route('/student/dashboard')
@login_required
def student_dashboard():
    enrolled_classes = current_user.enrolled_classes
    my_submissions = ExamSubmission.query.filter_by(student_id=current_user.id).order_by(ExamSubmission.started_at.desc()).all()
    
    # Get all active exams in enrolled classes
    class_ids = [c.id for c in enrolled_classes]
    available_exams = []
    if class_ids:
        available_exams = Exam.query.filter(Exam.classroom_id.in_(class_ids), Exam.is_published == True).all()
        
    return render_template('dashboard/student.html', classrooms=enrolled_classes, submissions=my_submissions, available_exams=available_exams)


# ----------------- CLASSROOMS -----------------

@main_bp.route('/classrooms/create', methods=['POST'])
@login_required
@teacher_required
def create_classroom():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    
    if not name:
        flash('Vui lòng nhập tên lớp học.', 'warning')
        return redirect(url_for('main.teacher_dashboard'))
        
    # Generate unique 6-character code
    code = f"TIN11-{uuid.uuid4().hex[:4].upper()}"
    new_class = Classroom(
        name=name,
        code=code,
        description=description,
        teacher_id=current_user.id
    )
    db.session.add(new_class)
    db.session.commit()
    flash(f'Lớp học "{name}" đã được tạo thành công! Mã mời lớp là: {code}', 'success')
    return redirect(url_for('main.classroom_detail', class_id=new_class.id))


@main_bp.route('/classrooms/<int:class_id>')
@login_required
def classroom_detail(class_id):
    classroom = Classroom.query.get_or_404(class_id)
    # Check access
    if not current_user.is_admin and current_user.id != classroom.teacher_id and classroom not in current_user.enrolled_classes:
        flash('Bạn chưa tham gia lớp học này!', 'warning')
        return redirect(url_for('main.student_dashboard'))
        
    courses = classroom.courses.order_by(Course.created_at.desc()).all()
    exams = classroom.exams.order_by(Exam.created_at.desc()).all()
    students = classroom.students.all()
    
    return render_template('classrooms/detail.html', classroom=classroom, courses=courses, exams=exams, students=students)


@main_bp.route('/classrooms/join', methods=['POST'])
@login_required
def join_classroom():
    code = request.form.get('code', '').strip().upper()
    if not code:
        flash('Vui lòng nhập mã lớp học.', 'warning')
        return redirect(url_for('main.student_dashboard'))
        
    classroom = Classroom.query.filter_by(code=code).first()
    if not classroom:
        flash('Mã lớp học không hợp lệ. Vui lòng kiểm tra lại.', 'danger')
        return redirect(url_for('main.student_dashboard'))
        
    if classroom in current_user.enrolled_classes:
        flash('Bạn đã là thành viên của lớp học này rồi.', 'info')
        return redirect(url_for('main.classroom_detail', class_id=classroom.id))
        
    classroom.students.append(current_user)
    db.session.commit()
    flash(f'Chúc mừng bạn đã tham gia thành công lớp "{classroom.name}"!', 'success')
    return redirect(url_for('main.classroom_detail', class_id=classroom.id))


# ----------------- COURSES & LESSONS -----------------

@main_bp.route('/classrooms/<int:class_id>/courses/create', methods=['POST'])
@login_required
@teacher_required
def create_course(class_id):
    classroom = Classroom.query.get_or_404(class_id)
    if not current_user.is_admin and classroom.teacher_id != current_user.id:
        abort(403)
        
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    if not title:
        flash('Tiêu đề khoá học không được để trống.', 'warning')
        return redirect(url_for('main.classroom_detail', class_id=class_id))
        
    course = Course(
        title=title,
        description=description,
        classroom_id=classroom.id,
        teacher_id=current_user.id
    )
    db.session.add(course)
    db.session.commit()
    flash(f'Khoá học "{title}" đã được tạo thành công!', 'success')
    return redirect(url_for('main.course_detail', course_id=course.id))


@main_bp.route('/courses/<int:course_id>')
@login_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    lessons = course.lessons.order_by(Lesson.order_index.asc()).all()
    return render_template('courses/detail.html', course=course, lessons=lessons)


@main_bp.route('/courses/<int:course_id>/lessons/create', methods=['POST'])
@login_required
@teacher_required
def create_lesson(course_id):
    course = Course.query.get_or_404(course_id)
    if not current_user.is_admin and course.teacher_id != current_user.id:
        abort(403)
        
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    order_index = int(request.form.get('order_index', 1))
    
    if not title:
        flash('Vui lòng nhập tên bài học.', 'warning')
        return redirect(url_for('main.course_detail', course_id=course_id))
        
    lesson = Lesson(
        course_id=course.id,
        title=title,
        content=content,
        order_index=order_index
    )
    db.session.add(lesson)
    db.session.commit()
    flash(f'Bài học "{title}" đã được thêm!', 'success')
    return redirect(url_for('main.lesson_detail', lesson_id=lesson.id))


@main_bp.route('/lessons/<int:lesson_id>')
@login_required
def lesson_detail(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    materials = lesson.materials.order_by(Material.uploaded_at.desc()).all()
    return render_template('courses/lesson_detail.html', lesson=lesson, materials=materials)


# ----------------- MATERIALS (UPLOAD & IN-BROWSER VIEWER) -----------------

@main_bp.route('/lessons/<int:lesson_id>/materials/upload', methods=['POST'])
@login_required
@teacher_required
def upload_material(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.course
    if not current_user.is_admin and course.teacher_id != current_user.id:
        abort(403)
        
    if 'file' not in request.files:
        flash('Không tìm thấy tệp đính kèm.', 'warning')
        return redirect(url_for('main.lesson_detail', lesson_id=lesson_id))
        
    file = request.files['file']
    title = request.form.get('title', '').strip()
    
    if file.filename == '':
        flash('Bạn chưa chọn tệp để tải lên.', 'warning')
        return redirect(url_for('main.lesson_detail', lesson_id=lesson_id))
        
    if file and allowed_file(file.filename):
        original_name = file.filename
        ext = original_name.rsplit('.', 1)[1].lower()
        if not title:
            title = original_name.rsplit('.', 1)[0]
            
        unique_name = f"{uuid.uuid4().hex}_{secure_filename(original_name)}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        
        material = Material(
            lesson_id=lesson.id,
            title=title,
            file_type=ext,
            file_name=unique_name,
            original_name=original_name,
            file_size=file_size
        )
        db.session.add(material)
        db.session.commit()
        flash(f'Tài liệu "{original_name}" ({ext.upper()}) đã được tải lên thành công!', 'success')
    else:
        flash('Định dạng tệp không được hỗ trợ. Chỉ chấp nhận các định dạng PPT, PPTX, DOCX, PDF.', 'danger')
        
    return redirect(url_for('main.lesson_detail', lesson_id=lesson_id))


@main_bp.route('/materials/<int:material_id>/view')
@login_required
def view_material(material_id):
    material = Material.query.get_or_404(material_id)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], material.file_name)
    
    if not os.path.exists(file_path):
        flash('Tệp tài liệu không tồn tại trên máy chủ.', 'danger')
        return redirect(url_for('main.lesson_detail', lesson_id=material.lesson_id))
        
    if material.file_type == 'pdf':
        meta = get_pdf_metadata(file_path)
        return render_template('materials/view_pdf.html', material=material, meta=meta)
    elif material.file_type == 'docx':
        html_content = parse_docx_to_html(file_path)
        return render_template('materials/view_docx.html', material=material, html_content=html_content)
    elif material.file_type in ['pptx', 'ppt']:
        slides = parse_pptx_slides(file_path)
        return render_template('materials/view_pptx.html', material=material, slides=slides)
    else:
        return redirect(url_for('main.download_material', material_id=material.id))


@main_bp.route('/materials/<int:material_id>/raw')
@login_required
def serve_raw_material(material_id):
    """Serve file for inline PDF display"""
    material = Material.query.get_or_404(material_id)
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        material.file_name,
        as_attachment=False,
        download_name=material.original_name
    )


@main_bp.route('/materials/<int:material_id>/download')
@login_required
def download_material(material_id):
    material = Material.query.get_or_404(material_id)
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        material.file_name,
        as_attachment=True,
        download_name=material.original_name
    )


# ----------------- EXAMS & ANTI-CHEATING -----------------

@main_bp.route('/classrooms/<int:class_id>/exams/create', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_exam(class_id):
    classroom = Classroom.query.get_or_404(class_id)
    if not current_user.is_admin and classroom.teacher_id != current_user.id:
        abort(403)
        
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        duration = int(request.form.get('duration_minutes', 15))
        max_violations = int(request.form.get('max_violations', 3))
        enable_fullscreen = bool(request.form.get('enable_fullscreen'))
        enable_tab_lock = bool(request.form.get('enable_tab_lock'))
        
        if not title:
            flash('Vui lòng nhập tiêu đề bài kiểm tra.', 'warning')
            return render_template('exams/create.html', classroom=classroom)
            
        exam = Exam(
            classroom_id=classroom.id,
            teacher_id=current_user.id,
            title=title,
            description=description,
            duration_minutes=duration,
            max_violations=max_violations,
            enable_fullscreen=enable_fullscreen,
            enable_tab_lock=enable_tab_lock
        )
        db.session.add(exam)
        db.session.commit()
        flash(f'Đã khởi tạo đề kiểm tra "{title}". Hãy thêm câu hỏi trắc nghiệm!', 'success')
        return redirect(url_for('main.exam_detail', exam_id=exam.id))
        
    return render_template('exams/create.html', classroom=classroom)


@main_bp.route('/exams/<int:exam_id>')
@login_required
def exam_detail(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    questions = exam.questions.all()
    submissions = exam.submissions.order_by(ExamSubmission.started_at.desc()).all()
    
    # Check if student already submitted
    student_submission = None
    if current_user.is_student:
        student_submission = ExamSubmission.query.filter_by(
            exam_id=exam.id,
            student_id=current_user.id
        ).order_by(ExamSubmission.started_at.desc()).first()
        
    return render_template('exams/detail.html', exam=exam, questions=questions, submissions=submissions, student_submission=student_submission)


@main_bp.route('/exams/<int:exam_id>/add-question', methods=['POST'])
@login_required
@teacher_required
def add_question(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if not current_user.is_admin and exam.teacher_id != current_user.id:
        abort(403)
        
    content = request.form.get('content', '').strip()
    opt_a = request.form.get('option_a', '').strip()
    opt_b = request.form.get('option_b', '').strip()
    opt_c = request.form.get('option_c', '').strip()
    opt_d = request.form.get('option_d', '').strip()
    correct_option = request.form.get('correct_option', 'A').upper()
    points = float(request.form.get('points', 1.0))
    
    if not content or not opt_a or not opt_b or not opt_c or not opt_d:
        flash('Vui lòng điền nội dung câu hỏi và cả 4 đáp án A, B, C, D.', 'warning')
        return redirect(url_for('main.exam_detail', exam_id=exam_id))
        
    question = Question(
        exam_id=exam.id,
        content=content,
        option_a=opt_a,
        option_b=opt_b,
        option_c=opt_c,
        option_d=opt_d,
        correct_option=correct_option,
        points=points
    )
    db.session.add(question)
    db.session.commit()
    flash('Câu hỏi đã được thêm thành công!', 'success')
    return redirect(url_for('main.exam_detail', exam_id=exam_id))


@main_bp.route('/exams/<int:exam_id>/take')
@login_required
def take_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if classroom member
    if not current_user.is_admin and exam.classroom not in current_user.enrolled_classes and current_user.id != exam.teacher_id:
        flash('Bạn chưa tham gia lớp học có bài kiểm tra này.', 'warning')
        return redirect(url_for('main.student_dashboard'))
        
    # Check previous submission
    submission = ExamSubmission.query.filter_by(
        exam_id=exam.id,
        student_id=current_user.id
    ).first()
    
    if submission and submission.status in ['submitted', 'auto_submitted_violation']:
        flash('Bạn đã hoàn thành bài kiểm tra này rồi.', 'info')
        return redirect(url_for('main.exam_result', submission_id=submission.id))
        
    if not submission:
        # Calculate total points
        total_pts = sum(q.points for q in exam.questions)
        submission = ExamSubmission(
            exam_id=exam.id,
            student_id=current_user.id,
            total_points=total_pts,
            status='in_progress',
            started_at=datetime.utcnow()
        )
        db.session.add(submission)
        db.session.commit()
        
    questions = exam.questions.all()
    return render_template('exams/take_exam.html', exam=exam, submission=submission, questions=questions)


@main_bp.route('/api/exam/<int:submission_id>/violation', methods=['POST'])
@login_required
def log_violation(submission_id):
    submission = ExamSubmission.query.get_or_404(submission_id)
    if submission.student_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
        
    if submission.status in ['submitted', 'auto_submitted_violation']:
        return jsonify({'status': 'already_submitted', 'auto_submit': True})
        
    data = request.get_json() or {}
    event_type = data.get('event_type', 'UNKNOWN_VIOLATION')
    details = data.get('details', '')
    
    # Increment violation count
    submission.violations_count += 1
    
    # Log to proctoring logs table
    log = ProctoringLog(
        submission_id=submission.id,
        event_type=event_type,
        details=details,
        timestamp=datetime.utcnow()
    )
    db.session.add(log)
    
    max_allowed = submission.exam.max_violations
    auto_submit = False
    
    if submission.violations_count >= max_allowed:
        auto_submit = True
        submission.status = 'auto_submitted_violation'
        submission.submitted_at = datetime.utcnow()
        # Auto calculate score for whatever is answered so far
        # Handled in final submit
        
    db.session.commit()
    
    return jsonify({
        'success': True,
        'violations_count': submission.violations_count,
        'max_violations': max_allowed,
        'auto_submit': auto_submit,
        'message': f'Cảnh báo gian lận! Bạn đã vi phạm {submission.violations_count}/{max_allowed} lần.'
    })


@main_bp.route('/exams/<int:submission_id>/submit', methods=['POST'])
@login_required
def submit_exam(submission_id):
    submission = ExamSubmission.query.get_or_404(submission_id)
    if submission.student_id != current_user.id and not current_user.is_admin:
        abort(403)
        
    if submission.status == 'submitted':
        flash('Bài thi đã được nộp trước đó.', 'info')
        return redirect(url_for('main.exam_result', submission_id=submission.id))
        
    answers = {}
    exam = submission.exam
    questions = exam.questions.all()
    score = 0.0
    
    for q in questions:
        user_choice = request.form.get(f'question_{q.id}', '').upper()
        answers[str(q.id)] = user_choice
        if user_choice == q.correct_option:
            score += q.points
            
    submission.answers_json = json.dumps(answers)
    submission.score = score
    if submission.status != 'auto_submitted_violation':
        submission.status = 'submitted'
    submission.submitted_at = datetime.utcnow()
    
    db.session.commit()
    flash('Bài kiểm tra đã được nộp thành công!', 'success')
    return redirect(url_for('main.exam_result', submission_id=submission.id))


@main_bp.route('/exams/<int:submission_id>/result')
@login_required
def exam_result(submission_id):
    submission = ExamSubmission.query.get_or_404(submission_id)
    if submission.student_id != current_user.id and not current_user.is_teacher and not current_user.is_admin:
        abort(403)
        
    answers = json.loads(submission.answers_json or '{}')
    exam = submission.exam
    questions = exam.questions.all()
    
    return render_template('exams/result.html', submission=submission, exam=exam, questions=questions, answers=answers)


@main_bp.route('/submissions/<int:submission_id>/proctoring-report')
@login_required
@teacher_required
def proctoring_report(submission_id):
    submission = ExamSubmission.query.get_or_404(submission_id)
    logs = submission.logs.order_by(ProctoringLog.timestamp.asc()).all()
    return render_template('exams/proctoring_report.html', submission=submission, logs=logs)
