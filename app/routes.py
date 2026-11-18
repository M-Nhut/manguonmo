import os
import io
import csv
import json
import uuid
import random
from datetime import datetime
from flask import (
    Blueprint, render_template, redirect, url_for, flash, 
    request, jsonify, current_app, send_from_directory, abort, Response
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.models import (
    db, User, Classroom, Course, Lesson, Material, 
    Exam, Question, ExamSubmission, ProctoringLog, GameScore
)
from app.auth import admin_required, teacher_required
from app.utils import (
    allowed_file, allowed_image_file, parse_docx_to_html, parse_pptx_slides, 
    get_pdf_metadata, format_file_size,
    SYSTEM_QUESTION_BANK, parse_questions_from_upload,
    generate_random_practice_exam, score_true_false_4, normalize_tf_pattern,
    CURRICULUM_TIN11, TOPIC_FILTER_MAP
)

main_bp = Blueprint('main', __name__)

PUBLIC_CLASS_CODE = 'PUBLIC-TIN11'


def _save_uploaded_poster(file_storage):
    """Save an uploaded poster image file and return its /uploads/<filename> URL path."""
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_image_file(file_storage.filename):
        return None
    original_name = file_storage.filename
    unique_name = f"poster_{uuid.uuid4().hex}_{secure_filename(original_name)}"
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)
    file_storage.save(file_path)
    return url_for('main.serve_uploaded_file', filename=unique_name)


@main_bp.route('/uploads/<path:filename>')
def serve_uploaded_file(filename):
    """Serve uploaded poster images and public assets from UPLOAD_FOLDER."""
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        filename,
        as_attachment=False
    )


def _populate_public_curriculum(pub, owner):
    """Populate the 7 Chủ đề & 31 Bài học of SGK Tin học 11 into the PUBLIC-TIN11 hub."""
    for topic in CURRICULUM_TIN11:
        course = Course(
            title=topic['title'],
            description=topic['description'],
            poster_url=topic.get('poster_url', ''),
            classroom_id=pub.id,
            teacher_id=owner.id
        )
        db.session.add(course)
        db.session.flush()
        for l_idx, l_title, _page, l_content in topic['lessons']:
            db.session.add(Lesson(
                course_id=course.id,
                title=l_title,
                content=l_content,
                order_index=l_idx
            ))


def ensure_public_hub():
    """
    ponytail: Reuse Classroom/Course/Lesson/Exam models with code='PUBLIC-TIN11'
    so Free Students and Class Students both get the full 7 Chủ đề & 31 Bài học
    of SGK Tin học 11 plus system chapter exams without a duplicate set of tables.
    """
    owner = User.query.filter(User.role.in_(['teacher', 'admin'])).first()
    pub = Classroom.query.filter_by(code=PUBLIC_CLASS_CODE).first()
    if pub:
        # Auto-upgrade legacy 4-topic hub to the full 7 Chủ đề & 31 Bài học if needed
        existing_courses = pub.courses.all()
        if len(existing_courses) < 7 and owner:
            has_user_materials = any(
                l.materials.count() > 0
                for c in existing_courses
                for l in c.lessons.all()
            )
            if not has_user_materials:
                for old_c in existing_courses:
                    db.session.delete(old_c)
                db.session.flush()
                _populate_public_curriculum(pub, owner)
                db.session.commit()
        return pub

    if not owner:
        return None

    pub = Classroom(
        name='Kho Học Liệu Chung (7 Chủ Đề • 31 Bài Học SGK)',
        code=PUBLIC_CLASS_CODE,
        description='Kho bài giảng 7 Chủ đề (31 Bài học), tài liệu đa phương tiện và đề ôn luyện chuẩn SGK Tin học 11.',
        teacher_id=owner.id
    )
    db.session.add(pub)
    db.session.flush()

    _populate_public_curriculum(pub, owner)

    # Create a System Chapter Exam with Part I (24 MCQ) and Part II (06 True/False 4-statement)
    pub_exam = Exam(
        classroom_id=pub.id,
        teacher_id=owner.id,
        title='Đề Ôn Luyện Tổng Hợp Tin Học 11 (Phần I: 24 Câu Trắc Nghiệm • Phần II: 06 Câu Đúng/Sai)',
        description='Đề kiểm tra chung từ Kho Học Liệu Hệ Thống dành cho học sinh tự do và học sinh các lớp.',
        duration_minutes=45,
        max_violations=3,
        enable_fullscreen=True,
        enable_tab_lock=True,
        is_published=True
    )
    db.session.add(pub_exam)
    db.session.flush()

    part1_init, part2_init = generate_random_practice_exam('ALL')
    for item in (part1_init + part2_init):
        db.session.add(Question(
            exam_id=pub_exam.id,
            question_type=item['question_type'],
            content=item['content'],
            option_a=item['option_a'],
            option_b=item['option_b'],
            option_c=item['option_c'],
            option_d=item['option_d'],
            correct_option=item['correct_option'],
            points=item['points']
        ))

    db.session.commit()
    return pub


def get_student_accessible_classes(user):
    """Return enrolled classrooms + the public system hub"""
    pub = ensure_public_hub()
    enrolled = list(user.enrolled_classes)
    if pub and pub not in enrolled:
        return enrolled + [pub]
    return enrolled


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
    ensure_public_hub()
    users = User.query.order_by(User.created_at.desc()).all()
    classrooms = Classroom.query.all()
    exams = Exam.query.order_by(Exam.created_at.desc()).all()
    recent_violations = ProctoringLog.query.order_by(ProctoringLog.timestamp.desc()).limit(8).all()
    
    stats = {
        'total_users': len(users),
        'total_teachers': sum(1 for u in users if u.role == 'teacher'),
        'total_students': sum(1 for u in users if u.role == 'student'),
        'total_classes': len(classrooms),
        'total_exams': len(exams),
        'open_exams': sum(1 for e in exams if e.is_published),
        'total_courses': Course.query.count(),
        'total_lessons': Lesson.query.count(),
        'total_violations': ProctoringLog.query.count(),
        'auto_locked_count': ExamSubmission.query.filter_by(status='auto_submitted_violation').count()
    }
    return render_template('dashboard/admin.html', stats=stats, users=users[:8], exams=exams[:6], recent_violations=recent_violations)


@main_bp.route('/teacher/dashboard')
@login_required
@teacher_required
def teacher_dashboard():
    ensure_public_hub()
    my_classrooms = Classroom.query.filter(
        Classroom.teacher_id == current_user.id,
        Classroom.code != PUBLIC_CLASS_CODE
    ).order_by(Classroom.created_at.desc()).all()
    my_exams = Exam.query.join(Classroom).filter(
        Exam.teacher_id == current_user.id,
        Classroom.code != PUBLIC_CLASS_CODE
    ).order_by(Exam.created_at.desc()).all()
    
    recent_submissions = (
        ExamSubmission.query
        .join(Exam)
        .filter(Exam.teacher_id == current_user.id)
        .order_by(ExamSubmission.started_at.desc())
        .limit(8)
        .all()
    )
    teacher_stats = {
        'total_classes': len(my_classrooms),
        'total_exams': len(my_exams),
        'open_exams': sum(1 for e in my_exams if e.is_published),
        'total_submissions': len(recent_submissions),
        'violation_cases': sum(1 for s in recent_submissions if (s.violations_count or 0) > 0)
    }
    
    return render_template(
        'dashboard/teacher.html',
        classrooms=my_classrooms,
        exams=my_exams,
        submissions=recent_submissions,
        teacher_stats=teacher_stats
    )


@main_bp.route('/student/dashboard')
@login_required
def student_dashboard():
    pub_hub = ensure_public_hub()
    enrolled_classes = list(current_user.enrolled_classes)
    my_submissions = ExamSubmission.query.filter_by(student_id=current_user.id).order_by(ExamSubmission.started_at.desc()).all()
    user_submissions = {s.exam_id: s for s in my_submissions}
    
    accessible_classes = get_student_accessible_classes(current_user)
    class_ids = [c.id for c in accessible_classes]
    available_exams = []
    if class_ids:
        available_exams = Exam.query.filter(Exam.classroom_id.in_(class_ids), Exam.is_published == True).order_by(Exam.created_at.desc()).all()

    completed_subs = [s for s in my_submissions if s.status in ('submitted', 'auto_submitted_violation')]
    avg_score_10 = 0.0
    if completed_subs:
        ratios = [((s.score / (s.total_points or 10.0)) * 10.0) for s in completed_subs if (s.total_points or 0) > 0]
        if ratios:
            avg_score_10 = round(sum(ratios) / len(ratios), 1)

    pending_exams_count = sum(1 for ex in available_exams if ex.id not in user_submissions)
    ensure_arena_demo_leaderboard(pub_hub)
    lb_data = _build_weekly_leaderboard(class_id=None, mode_filter='ALL', viewer_user=current_user)
        
    return render_template(
        'dashboard/student.html',
        classrooms=enrolled_classes,
        public_hub=pub_hub,
        submissions=my_submissions[:6],
        user_submissions=user_submissions,
        available_exams=available_exams,
        avg_score_10=avg_score_10,
        pending_exams_count=pending_exams_count,
        arena_top5=lb_data['entries'][:5],
        my_arena_stats=lb_data['my_stats'],
        week_label=lb_data['week_label']
    )


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
    if (
        classroom.code != PUBLIC_CLASS_CODE
        and not current_user.is_admin
        and current_user.id != classroom.teacher_id
        and classroom not in current_user.enrolled_classes
    ):
        flash('Bạn chưa tham gia lớp học này!', 'warning')
        return redirect(url_for('main.student_dashboard'))
        
    courses = classroom.courses.order_by(Course.id.asc()).all()
    exams = classroom.exams.order_by(Exam.created_at.desc()).all()
    students = classroom.students.all()
    
    return render_template('classrooms/detail.html', classroom=classroom, courses=courses, exams=exams, students=students)


@main_bp.route('/classrooms/join', methods=['POST'])
@login_required
def join_classroom():
    code = (request.form.get('code') or request.form.get('class_code') or '').strip().upper()
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
    if not current_user.is_admin and classroom.teacher_id != current_user.id and classroom.code != PUBLIC_CLASS_CODE:
        abort(403)
        
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    poster_url = request.form.get('poster_url', '').strip()
    uploaded_poster = _save_uploaded_poster(request.files.get('poster_file'))
    if uploaded_poster:
        poster_url = uploaded_poster

    if not title:
        flash('Tiêu đề khoá học không được để trống.', 'warning')
        return redirect(url_for('main.classroom_detail', class_id=class_id))
        
    course = Course(
        title=title,
        description=description,
        poster_url=poster_url,
        classroom_id=classroom.id,
        teacher_id=current_user.id
    )
    db.session.add(course)
    db.session.commit()
    flash(f'Khoá học "{title}" đã được tạo thành công!', 'success')
    return redirect(url_for('main.course_detail', course_id=course.id))


@main_bp.route('/courses/<int:course_id>/edit', methods=['POST'])
@login_required
@teacher_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    if not current_user.is_admin and course.teacher_id != current_user.id and course.classroom.code != PUBLIC_CLASS_CODE:
        abort(403)

    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    poster_url = request.form.get('poster_url', '').strip()
    uploaded_poster = _save_uploaded_poster(request.files.get('poster_file'))

    if title:
        course.title = title
    course.description = description
    if uploaded_poster:
        course.poster_url = uploaded_poster
    elif 'poster_url' in request.form:
        course.poster_url = poster_url

    db.session.commit()
    flash(f'Đã cập nhật chủ đề "{course.title}" thành công!', 'success')
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
    if not current_user.is_admin and course.teacher_id != current_user.id and course.classroom.code != PUBLIC_CLASS_CODE:
        abort(403)
        
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    video_embed = request.form.get('video_embed', '').strip()
    poster_url = request.form.get('poster_url', '').strip()
    uploaded_poster = _save_uploaded_poster(request.files.get('poster_file'))
    if uploaded_poster:
        poster_url = uploaded_poster
    try:
        order_index = int(request.form.get('order_index', 1))
    except ValueError:
        order_index = 1
    
    if not title:
        flash('Vui lòng nhập tên bài học.', 'warning')
        return redirect(url_for('main.course_detail', course_id=course_id))
        
    lesson = Lesson(
        course_id=course.id,
        title=title,
        content=content,
        poster_url=poster_url,
        video_embed=video_embed,
        order_index=order_index
    )
    db.session.add(lesson)
    db.session.commit()
    flash(f'Bài học "{title}" đã được thêm!', 'success')
    return redirect(url_for('main.lesson_detail', lesson_id=lesson.id))


@main_bp.route('/lessons/<int:lesson_id>/edit', methods=['POST'])
@login_required
@teacher_required
def edit_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.course
    if not current_user.is_admin and course.teacher_id != current_user.id and course.classroom.code != PUBLIC_CLASS_CODE:
        abort(403)

    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    video_embed = request.form.get('video_embed', '').strip()
    poster_url = request.form.get('poster_url', '').strip()
    uploaded_poster = _save_uploaded_poster(request.files.get('poster_file'))

    if title:
        lesson.title = title
    if 'content' in request.form:
        lesson.content = content
    if 'video_embed' in request.form:
        lesson.video_embed = video_embed
    if uploaded_poster:
        lesson.poster_url = uploaded_poster
    elif 'poster_url' in request.form:
        lesson.poster_url = poster_url

    if 'order_index' in request.form:
        try:
            lesson.order_index = int(request.form.get('order_index', lesson.order_index))
        except ValueError:
            pass

    db.session.commit()
    flash(f'Đã lưu chỉnh sửa bài học "{lesson.title}"!', 'success')
    return redirect(url_for('main.lesson_detail', lesson_id=lesson.id))


@main_bp.route('/lessons/<int:lesson_id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course_id = lesson.course_id
    if not current_user.is_admin and lesson.course.teacher_id != current_user.id and lesson.course.classroom.code != PUBLIC_CLASS_CODE:
        abort(403)
    title = lesson.title
    db.session.delete(lesson)
    db.session.commit()
    flash(f'Đã xóa bài học "{title}".', 'info')
    return redirect(url_for('main.course_detail', course_id=course_id))


@main_bp.route('/lessons/<int:lesson_id>')
@login_required
def lesson_detail(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    materials = lesson.materials.order_by(Material.uploaded_at.desc()).all()
    course_lessons = lesson.course.lessons.order_by(Lesson.order_index.asc(), Lesson.id.asc()).all()
    prev_lesson = None
    next_lesson = None
    for idx, item in enumerate(course_lessons):
        if item.id == lesson.id:
            if idx > 0:
                prev_lesson = course_lessons[idx - 1]
            if idx < len(course_lessons) - 1:
                next_lesson = course_lessons[idx + 1]
            break
    return render_template(
        'courses/lesson_detail.html',
        lesson=lesson,
        materials=materials,
        course_lessons=course_lessons,
        prev_lesson=prev_lesson,
        next_lesson=next_lesson
    )


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
        flash('Định dạng tệp không được hỗ trợ. Chỉ chấp nhận PPT, PPTX, DOCX, PDF và Video (MP4, WEBM, OGG, MOV).', 'danger')
        
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
    elif material.file_type in ['mp4', 'webm', 'ogg', 'mov']:
        return render_template('materials/view_video.html', material=material)
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

def _grade_submission(submission, form_data=None):
    """Chấm điểm bài làm từ dữ liệu form kết hợp với dữ liệu autosave đã lưu."""
    saved_answers = {}
    try:
        saved_answers = json.loads(submission.answers_json or '{}')
    except Exception:
        saved_answers = {}

    answers = {}
    exam = submission.exam
    questions = exam.questions.all()
    score = 0.0

    for q in questions:
        qid_str = str(q.id)
        q_type = (q.question_type or 'mcq').lower()
        if q_type == 'true_false':
            raw_tf = ''
            if form_data is not None:
                sub_choices = [
                    form_data.get(f'question_{q.id}_a', '').strip(),
                    form_data.get(f'question_{q.id}_b', '').strip(),
                    form_data.get(f'question_{q.id}_c', '').strip(),
                    form_data.get(f'question_{q.id}_d', '').strip()
                ]
                if any(sub_choices):
                    raw_tf = ','.join(sub_choices)
                else:
                    raw_tf = form_data.get(f'question_{q.id}', '').strip()
            if not raw_tf and qid_str in saved_answers:
                raw_tf = str(saved_answers.get(qid_str, '')).strip()
            pts, _, user_list, _ = score_true_false_4(raw_tf, q.correct_option)
            answers[qid_str] = ','.join(user_list)
            score += pts
        else:
            raw_val = ''
            if form_data is not None:
                raw_val = form_data.get(f'question_{q.id}', '').strip().upper()
            if not raw_val and qid_str in saved_answers:
                raw_val = str(saved_answers.get(qid_str, '')).strip().upper()
            answers[qid_str] = raw_val
            if raw_val and raw_val == (q.correct_option or '').strip().upper():
                score += q.points

    submission.answers_json = json.dumps(answers)
    submission.score = round(score, 2)
    submission.total_points = round(sum(q.points for q in questions), 2)
    return submission.score


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
        duration = max(1, int(request.form.get('duration_minutes', 15) or 15))
        max_violations = max(1, int(request.form.get('max_violations', 3) or 3))
        access_code = request.form.get('access_code', '').strip().upper()
        enable_fullscreen = bool(request.form.get('enable_fullscreen'))
        enable_tab_lock = bool(request.form.get('enable_tab_lock'))
        shuffle_questions = bool(request.form.get('shuffle_questions')) if 'shuffle_questions' in request.form else True
        is_published = bool(request.form.get('is_published')) if 'is_published' in request.form else True
        
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
            access_code=access_code,
            enable_fullscreen=enable_fullscreen,
            enable_tab_lock=enable_tab_lock,
            shuffle_questions=shuffle_questions,
            is_published=is_published
        )
        db.session.add(exam)
        db.session.commit()
        flash(f'Đã khởi tạo đề kiểm tra "{title}". Hãy thêm câu hỏi vào đề thi!', 'success')
        return redirect(url_for('main.exam_detail', exam_id=exam.id))
        
    return render_template('exams/create.html', classroom=classroom)


@main_bp.route('/exams/<int:exam_id>')
@login_required
def exam_detail(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    questions = exam.questions.all()
    submissions = exam.submissions.order_by(ExamSubmission.started_at.desc()).all()
    
    student_submission = None
    if current_user.is_student:
        student_submission = ExamSubmission.query.filter_by(
            exam_id=exam.id,
            student_id=current_user.id
        ).order_by(ExamSubmission.started_at.desc()).first()
        
    return render_template(
        'exams/detail.html',
        exam=exam,
        questions=questions,
        submissions=submissions,
        student_submission=student_submission,
        system_bank=SYSTEM_QUESTION_BANK
    )


@main_bp.route('/exams/<int:exam_id>/settings', methods=['POST'])
@login_required
@teacher_required
def update_exam_settings(exam_id):
    """Cập nhật cấu hình giám sát, mã PIN, thời gian và trạng thái đóng/mở đề kiểm tra."""
    exam = Exam.query.get_or_404(exam_id)
    if not current_user.is_admin and exam.teacher_id != current_user.id:
        abort(403)

    title = request.form.get('title', '').strip()
    if title:
        exam.title = title
    if 'description' in request.form:
        exam.description = request.form.get('description', '').strip()
    exam.duration_minutes = max(1, int(request.form.get('duration_minutes', exam.duration_minutes) or exam.duration_minutes))
    exam.max_violations = max(1, int(request.form.get('max_violations', exam.max_violations) or exam.max_violations))
    exam.access_code = request.form.get('access_code', '').strip().upper()
    exam.enable_fullscreen = bool(request.form.get('enable_fullscreen'))
    exam.enable_tab_lock = bool(request.form.get('enable_tab_lock'))
    exam.shuffle_questions = bool(request.form.get('shuffle_questions'))
    exam.is_published = bool(request.form.get('is_published'))

    db.session.commit()
    flash(f'Đã lưu cấu hình giám sát cho đề "{exam.title}".', 'success')
    return redirect(url_for('main.exam_detail', exam_id=exam.id))


@main_bp.route('/exams/<int:exam_id>/toggle-status', methods=['POST'])
@login_required
@teacher_required
def toggle_exam_status(exam_id):
    """Đóng hoặc mở phòng thi nhanh bằng 1 cú nhấp chuột."""
    exam = Exam.query.get_or_404(exam_id)
    if not current_user.is_admin and exam.teacher_id != current_user.id:
        abort(403)

    exam.is_published = not exam.is_published
    db.session.commit()
    status_label = 'ĐANG MỞ PHÒNG THI' if exam.is_published else 'ĐÃ KHÓA PHÒNG THI'
    flash(f'Đề "{exam.title}": {status_label}.', 'info' if not exam.is_published else 'success')
    next_url = request.form.get('next') or request.referrer
    if next_url:
        return redirect(next_url)
    return redirect(url_for('main.exam_detail', exam_id=exam.id))


@main_bp.route('/questions/<int:question_id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_question(question_id):
    """Xóa câu hỏi khỏi đề kiểm tra."""
    question = Question.query.get_or_404(question_id)
    exam = question.exam
    if not current_user.is_admin and exam.teacher_id != current_user.id:
        abort(403)

    db.session.delete(question)
    db.session.commit()
    flash('Đã xóa câu hỏi khỏi đề kiểm tra.', 'info')
    return redirect(url_for('main.exam_detail', exam_id=exam.id))


@main_bp.route('/submissions/<int:submission_id>/reset', methods=['POST'])
@login_required
@teacher_required
def reset_submission(submission_id):
    """Giáo viên/Admin xóa lượt thi cũ để cho phép học sinh làm lại bài."""
    submission = ExamSubmission.query.get_or_404(submission_id)
    exam = submission.exam
    if not current_user.is_admin and exam.teacher_id != current_user.id:
        abort(403)

    student_name = submission.student.full_name
    db.session.delete(submission)
    db.session.commit()
    flash(f'Đã mở khóa và cho phép học sinh "{student_name}" làm lại bài kiểm tra.', 'success')
    next_url = request.form.get('next') or request.referrer
    if next_url and '/proctoring-report' not in next_url:
        return redirect(next_url)
    return redirect(url_for('main.exam_detail', exam_id=exam.id))


@main_bp.route('/exams/<int:exam_id>/add-question', methods=['POST'])
@login_required
@teacher_required
def add_question(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if not current_user.is_admin and exam.teacher_id != current_user.id:
        abort(403)
        
    q_type = request.form.get('question_type', 'mcq').strip().lower()
    if q_type not in ['mcq', 'true_false']:
        q_type = 'mcq'

    content = request.form.get('content', '').strip()
    opt_a = request.form.get('option_a', '').strip()
    opt_b = request.form.get('option_b', '').strip()
    opt_c = request.form.get('option_c', '').strip()
    opt_d = request.form.get('option_d', '').strip()
    correct_option = request.form.get('correct_option', 'A').strip()

    if not content:
        flash('Vui lòng nhập nội dung câu hỏi.', 'warning')
        return redirect(url_for('main.exam_detail', exam_id=exam_id))

    if q_type == 'mcq':
        points = float(request.form.get('points', 0.25))
        if not opt_a or not opt_b or not opt_c or not opt_d:
            flash('Câu hỏi trắc nghiệm cần đủ 4 đáp án A, B, C, D.', 'warning')
            return redirect(url_for('main.exam_detail', exam_id=exam_id))
        correct_option = correct_option.upper()[:1] or 'A'
    else:
        points = float(request.form.get('points', 1.0))
        if not opt_a:
            opt_a = 'Phát biểu a)'
        if not opt_b:
            opt_b = 'Phát biểu b)'
        if not opt_c:
            opt_c = 'Phát biểu c)'
        if not opt_d:
            opt_d = 'Phát biểu d)'
        tf_parts = [
            request.form.get('tf_ans_a', ''),
            request.form.get('tf_ans_b', ''),
            request.form.get('tf_ans_c', ''),
            request.form.get('tf_ans_d', '')
        ]
        if any(tf_parts):
            correct_option = ','.join(normalize_tf_pattern(','.join(tf_parts)))
        else:
            correct_option = ','.join(normalize_tf_pattern(correct_option))

    question = Question(
        exam_id=exam.id,
        question_type=q_type,
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
    flash('Đã thêm câu hỏi vào đề kiểm tra!', 'success')
    return redirect(url_for('main.exam_detail', exam_id=exam_id))


@main_bp.route('/exams/<int:exam_id>/import-bank', methods=['POST'])
@login_required
@teacher_required
def import_question_bank(exam_id):
    """Giáo viên lấy câu hỏi từ Ngân hàng đề hệ thống vào đề kiểm tra của lớp"""
    exam = Exam.query.get_or_404(exam_id)
    if not current_user.is_admin and exam.teacher_id != current_user.id:
        abort(403)

    selected_ids = request.form.getlist('bank_ids')
    topic_filter = request.form.get('topic_quick', '').upper().strip()

    items_to_add = []
    if topic_filter == 'RANDOM_30':
        p1, p2 = generate_random_practice_exam('ALL')
        items_to_add = p1 + p2
    elif topic_filter in ['A', 'C', 'F', 'E', 'ALL']:
        items_to_add = [
            q for q in SYSTEM_QUESTION_BANK
            if topic_filter == 'ALL' or q['topic'] == topic_filter
        ]
    elif selected_ids:
        items_to_add = [q for q in SYSTEM_QUESTION_BANK if q['id'] in selected_ids]

    for item in items_to_add:
        db.session.add(Question(
            exam_id=exam.id,
            question_type=item['question_type'],
            content=item['content'],
            option_a=item['option_a'],
            option_b=item['option_b'],
            option_c=item['option_c'],
            option_d=item['option_d'],
            correct_option=item['correct_option'],
            points=item['points']
        ))

    if items_to_add:
        db.session.commit()
        flash(f'Đã thêm {len(items_to_add)} câu hỏi từ Ngân hàng đề hệ thống!', 'success')
    else:
        flash('Vui lòng chọn ít nhất 1 câu hỏi hoặc chủ đề từ Ngân hàng đề.', 'warning')

    return redirect(url_for('main.exam_detail', exam_id=exam_id))


@main_bp.route('/exams/<int:exam_id>/upload-questions', methods=['POST'])
@login_required
@teacher_required
def upload_exam_questions(exam_id):
    """Giáo viên tải tệp đề kiểm tra (.docx, .csv, .txt) lên web để tạo câu hỏi tự động"""
    exam = Exam.query.get_or_404(exam_id)
    if not current_user.is_admin and exam.teacher_id != current_user.id:
        abort(403)

    file = request.files.get('exam_file')
    if not file or not file.filename:
        flash('Vui lòng chọn tệp đề kiểm tra (.csv, .txt, .docx).', 'warning')
        return redirect(url_for('main.exam_detail', exam_id=exam_id))

    try:
        parsed_questions = parse_questions_from_upload(file)
    except Exception as e:
        flash(f'Lỗi đọc tệp đề kiểm tra: {str(e)}', 'danger')
        return redirect(url_for('main.exam_detail', exam_id=exam_id))

    for q in parsed_questions:
        db.session.add(Question(
            exam_id=exam.id,
            question_type=q['question_type'],
            content=q['content'],
            option_a=q['option_a'],
            option_b=q['option_b'],
            option_c=q['option_c'],
            option_d=q['option_d'],
            correct_option=q['correct_option'],
            points=q['points']
        ))

    if parsed_questions:
        db.session.commit()
        flash(f'Đã tải lên và nhập thành công {len(parsed_questions)} câu hỏi vào đề thi!', 'success')
    else:
        flash('Không tìm thấy câu hỏi hợp lệ trong tệp. Hãy kiểm tra đúng định dạng mẫu.', 'warning')

    return redirect(url_for('main.exam_detail', exam_id=exam_id))


@main_bp.route('/exams/<int:exam_id>/export-excel')
@login_required
@teacher_required
def export_exam_excel(exam_id):
    """Xuất bảng điểm kết quả kiểm tra của lớp ra file Excel (.csv UTF-8 with BOM)"""
    exam = Exam.query.get_or_404(exam_id)
    if not current_user.is_admin and exam.teacher_id != current_user.id:
        abort(403)

    submissions = exam.submissions.order_by(ExamSubmission.score.desc(), ExamSubmission.submitted_at.asc()).all()

    output = io.StringIO()
    output.write('\ufeff')  # UTF-8 BOM for native Vietnamese display in Microsoft Excel
    writer = csv.writer(output)
    writer.writerow([
        'STT',
        'Ho va Ten Hoc Sinh',
        'Tai Khoan',
        'Email',
        'Lop Hoc',
        'De Kiem Tra',
        'Diem Dat Duoc',
        'Tong Diem',
        'So Lan Vi Pham',
        'Trang Thai',
        'Thoi Gian Nop Bai'
    ])

    for idx, sub in enumerate(submissions, start=1):
        status_vn = 'Hợp lệ' if sub.status == 'submitted' else (
            'Thu bài tự động (Vi phạm)' if sub.status == 'auto_submitted_violation' else 'Đang làm bài'
        )
        submitted_str = sub.submitted_at.strftime('%H:%M:%S %d/%m/%Y') if sub.submitted_at else 'Chưa nộp'
        writer.writerow([
            idx,
            sub.student.full_name,
            sub.student.username,
            sub.student.email,
            exam.classroom.name,
            exam.title,
            round(sub.score, 2),
            round(sub.total_points, 2),
            sub.violations_count,
            status_vn,
            submitted_str
        ])

    filename = f"Bang_Diem_Lop_{exam.classroom.code}_De_{exam.id}.csv"
    return Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@main_bp.route('/exams/<int:exam_id>/take', methods=['GET', 'POST'])
@login_required
def take_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    
    # Allow if public hub exam OR enrolled in classroom OR teacher/admin
    if (
        exam.classroom.code != PUBLIC_CLASS_CODE
        and not current_user.is_admin
        and exam.classroom not in current_user.enrolled_classes
        and current_user.id != exam.teacher_id
    ):
        flash('Bạn chưa tham gia lớp học có bài kiểm tra này.', 'warning')
        return redirect(url_for('main.student_dashboard'))

    # Block students when exam room is locked by teacher
    if not exam.is_published and not current_user.is_teacher and not current_user.is_admin:
        flash('Phòng thi hiện đang tạm khóa bởi Giáo viên.', 'warning')
        return redirect(url_for('main.exam_detail', exam_id=exam.id))
        
    submission = ExamSubmission.query.filter_by(
        exam_id=exam.id,
        student_id=current_user.id
    ).first()
    
    if submission and submission.status in ['submitted', 'auto_submitted_violation']:
        flash('Bạn đã hoàn thành bài kiểm tra này rồi. Mỗi học sinh chỉ được làm bài 1 lần.', 'info')
        return redirect(url_for('main.exam_result', submission_id=submission.id))

    # Enforce Exam Access PIN before starting a new submission
    required_pin = (exam.access_code or '').strip().upper()
    if not submission and required_pin and not current_user.is_teacher and not current_user.is_admin:
        entered_pin = (
            request.form.get('access_code', '') or request.args.get('access_code', '')
        ).strip().upper()
        if entered_pin != required_pin:
            if request.method == 'POST' or 'access_code' in request.args:
                flash('Mã PIN phòng thi không chính xác. Vui lòng kiểm tra lại với Giáo viên.', 'danger')
            return render_template(
                'exams/take_exam.html',
                exam=exam,
                submission=None,
                questions=[],
                pin_required=True,
                remaining_seconds=exam.duration_minutes * 60,
                saved_answers={}
            )
        
    if not submission:
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

    # Server-side countdown enforcement (anti-F5 timer reset)
    elapsed_seconds = int((datetime.utcnow() - submission.started_at).total_seconds())
    total_seconds = max(60, int(exam.duration_minutes * 60))
    remaining_seconds = max(0, total_seconds - elapsed_seconds)

    if remaining_seconds <= 0:
        _grade_submission(submission)
        submission.status = 'submitted'
        submission.submitted_at = datetime.utcnow()
        db.session.commit()
        flash('Đã hết thời gian làm bài! Hệ thống tự động thu bài của bạn.', 'warning')
        return redirect(url_for('main.exam_result', submission_id=submission.id))
        
    questions = exam.questions.order_by(Question.id.asc()).all()
    if getattr(exam, 'shuffle_questions', True) and len(questions) > 1:
        rng = random.Random(f"exam-{exam.id}-sub-{submission.id}-student-{current_user.id}")
        # Keep Part I (MCQ) and Part II (True/False) grouped cleanly, shuffled within each group
        mcq_qs = [q for q in questions if (q.question_type or 'mcq') == 'mcq']
        tf_qs = [q for q in questions if (q.question_type or 'mcq') == 'true_false']
        rng.shuffle(mcq_qs)
        rng.shuffle(tf_qs)
        questions = mcq_qs + tf_qs

    try:
        saved_answers = json.loads(submission.answers_json or '{}')
    except Exception:
        saved_answers = {}

    return render_template(
        'exams/take_exam.html',
        exam=exam,
        submission=submission,
        questions=questions,
        pin_required=False,
        remaining_seconds=remaining_seconds,
        saved_answers=saved_answers
    )


@main_bp.route('/api/exam/<int:submission_id>/autosave', methods=['POST'])
@login_required
def autosave_exam(submission_id):
    """Lưu nháp đáp án theo thời gian thực để chống mất bài khi rớt mạng hoặc bị thu bài tự động."""
    submission = ExamSubmission.query.get_or_404(submission_id)
    if submission.student_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    if submission.status in ['submitted', 'auto_submitted_violation']:
        return jsonify({'status': 'locked', 'saved': False})

    data = request.get_json() or {}
    incoming = data.get('answers', {})
    if isinstance(incoming, dict):
        try:
            current_ans = json.loads(submission.answers_json or '{}')
        except Exception:
            current_ans = {}
        for k, v in incoming.items():
            current_ans[str(k)] = str(v).strip()
        submission.answers_json = json.dumps(current_ans)
        db.session.commit()

    elapsed_seconds = int((datetime.utcnow() - submission.started_at).total_seconds())
    remaining_seconds = max(0, int(submission.exam.duration_minutes * 60) - elapsed_seconds)
    return jsonify({
        'saved': True,
        'remaining_seconds': remaining_seconds,
        'violations_count': submission.violations_count
    })


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
    
    submission.violations_count += 1
    
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
        _grade_submission(submission)
        submission.status = 'auto_submitted_violation'
        submission.submitted_at = datetime.utcnow()
        
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
        
    _grade_submission(submission, form_data=request.form)
    if submission.status != 'auto_submitted_violation':
        submission.status = 'submitted'
    submission.submitted_at = datetime.utcnow()
    
    db.session.commit()
    if submission.status == 'auto_submitted_violation':
        flash('Bài kiểm tra đã bị hệ thống thu tự động do vượt quá giới hạn vi phạm quy chế thi.', 'danger')
    else:
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
    tf_details = {}
    for q in questions:
        if (q.question_type or 'mcq').lower() == 'true_false':
            u_ans = answers.get(str(q.id), '')
            pts, hits, u_list, c_list = score_true_false_4(u_ans, q.correct_option)
            tf_details[q.id] = {
                'score': pts,
                'hits': hits,
                'user_list': u_list,
                'correct_list': c_list
            }
    
    return render_template('exams/result.html', submission=submission, exam=exam, questions=questions, answers=answers, tf_details=tf_details)


@main_bp.route('/submissions/<int:submission_id>/proctoring-report')
@login_required
@teacher_required
def proctoring_report(submission_id):
    submission = ExamSubmission.query.get_or_404(submission_id)
    logs = submission.logs.order_by(ProctoringLog.timestamp.asc()).all()
    return render_template('exams/proctoring_report.html', submission=submission, logs=logs)


# ----------------- DEDICATED SIDEBAR SECTION VIEWS -----------------

@main_bp.route('/lessons')
@login_required
def lessons_list():
    """Mục Bài học: hiển thị cả Kho Học Liệu Chung (7 Chủ đề • 31 Bài học SGK) và Bài học của Lớp đang tham gia"""
    pub_hub = ensure_public_hub()
    if current_user.is_admin:
        classrooms = Classroom.query.all()
        all_courses = Course.query.order_by(Course.id.asc()).all()
        lessons = Lesson.query.order_by(Lesson.course_id.asc(), Lesson.order_index.asc()).all()
    elif current_user.is_teacher:
        classrooms = Classroom.query.filter(
            (Classroom.teacher_id == current_user.id) | (Classroom.code == PUBLIC_CLASS_CODE)
        ).all()
        class_ids = [c.id for c in classrooms]
        all_courses = Course.query.filter(Course.classroom_id.in_(class_ids)).order_by(Course.id.asc()).all() if class_ids else []
        course_ids = [co.id for co in all_courses]
        lessons = Lesson.query.filter(Lesson.course_id.in_(course_ids)).order_by(Lesson.course_id.asc(), Lesson.order_index.asc()).all() if course_ids else []
    else:
        classrooms = get_student_accessible_classes(current_user)
        class_ids = [c.id for c in classrooms]
        all_courses = Course.query.filter(Course.classroom_id.in_(class_ids)).order_by(Course.id.asc()).all() if class_ids else []
        course_ids = [co.id for co in all_courses]
        lessons = Lesson.query.filter(Lesson.course_id.in_(course_ids)).order_by(Lesson.course_id.asc(), Lesson.order_index.asc()).all() if course_ids else []

    selected_class_id = request.args.get('class_id', type=int)
    selected_course_id = request.args.get('course_id', type=int)
    search_query = (request.args.get('q') or '').strip()

    if selected_class_id:
        all_courses = [c for c in all_courses if c.classroom_id == selected_class_id]
        lessons = [l for l in lessons if l.course.classroom_id == selected_class_id]
    if selected_course_id:
        lessons = [l for l in lessons if l.course_id == selected_course_id]
    if search_query:
        q_low = search_query.lower()
        lessons = [
            l for l in lessons
            if q_low in (l.title or '').lower()
            or q_low in (l.course.title or '').lower()
            or q_low in (l.content or '').lower()
        ]

    return render_template(
        'courses/lessons_list.html',
        lessons=lessons,
        all_courses=all_courses,
        classrooms=classrooms,
        selected_class_id=selected_class_id,
        selected_course_id=selected_course_id,
        search_query=search_query,
        public_hub=pub_hub
    )


@main_bp.route('/practice')
@login_required
def practice_hub():
    """
    Góc Ôn Luyện: Sinh đề ngẫu nhiên từ Ngân hàng đề có sẵn theo cấu trúc chuẩn:
      - Phần I: 24 câu trắc nghiệm 4 lựa chọn (0,25 điểm/câu -> tối đa 6,0 điểm)
      - Phần II: 06 câu trắc nghiệm Đúng/Sai 4 ý a, b, c, d (Phần chung & Định hướng CS / ICT; 0,1 - 0,25 - 0,5 - 1,0 điểm)
    """
    ensure_public_hub()
    raw_topic = request.args.get('topic', 'ALL').upper().strip()
    topic_filter = TOPIC_FILTER_MAP.get(raw_topic, 'ALL') if raw_topic != 'ALL' else 'ALL'
    is_generated = request.args.get('generated', '0').strip() == '1'
    selected_duration = request.args.get('duration', 45, type=int)
    if selected_duration not in (15, 30, 45, 60):
        selected_duration = 45

    part1_questions, part2_questions = generate_random_practice_exam(topic_filter)

    flashcards = [
        {'topic': 'Chủ đề 1', 'term': 'Hệ điều hành & Phần mềm nguồn mở', 'definition': 'Hệ điều hành điều phối CPU, RAM, thiết bị; Phần mềm nguồn mở công khai mã nguồn theo giấy phép GPL/MIT.'},
        {'topic': 'Chủ đề 1', 'term': 'CPU, RAM, ROM & Cổng kết nối', 'definition': 'CPU xử lí lệnh (GHz); RAM là bộ nhớ khả biến; HDMI truyền đồng thời hình ảnh và âm thanh số.'},
        {'topic': 'Chủ đề 2 & 3', 'term': 'Lưu trữ đám mây & Toán tử tìm kiếm', 'definition': 'Phân quyền Xem / Nhận xét / Chỉnh sửa trên đám mây; dùng "..." và filetype:pdf khi tìm kiếm; bật xác thực 2FA.'},
        {'topic': 'Chủ đề 4 & 5', 'term': 'CSDL quan hệ & Ngôn ngữ SQL', 'definition': 'Khóa chính (Primary Key) duy nhất, không rỗng; Khóa ngoài (Foreign Key) liên kết bảng; truy vấn SELECT ... FROM ... WHERE.'},
        {'topic': 'Chủ đề 6', 'term': 'Thực hành khai thác & Sao lưu CSDL', 'definition': 'Dùng INNER JOIN ... ON kết nối các bảng qua khóa ngoại và xuất tệp .sql để sao lưu/phục hồi dữ liệu.'},
        {'topic': 'Chủ đề 7', 'term': 'Chỉnh sửa ảnh GIMP & Làm phim', 'definition': 'Layer tách lớp ảnh độc lập; Alpha Channel lưu nền trong suốt (PNG); Timeline sắp xếp phân cảnh, âm thanh và xuất .mp4.'}
    ]

    return render_template(
        'courses/practice.html',
        part1_questions=part1_questions,
        part2_questions=part2_questions,
        questions=part1_questions + part2_questions,
        bank_count=len(SYSTEM_QUESTION_BANK),
        current_topic=topic_filter,
        is_generated=is_generated,
        selected_duration=selected_duration,
        flashcards=flashcards
    )


# ----------------- CYBER ARENA & WEEKLY LEADERBOARD -----------------

ARENA_SQL_CHALLENGES = [
    {
        'id': 'sql_1',
        'topic': 'F',
        'title': 'Lọc danh sách Học sinh Giỏi lớp 11A1',
        'scenario': 'Truy vấn cột HoTen và DiemTB từ bảng HocSinh cho các học sinh thuộc lớp 11A1 có DiemTB từ 8.0 trở lên, sắp xếp điểm giảm dần.',
        'schema_hint': 'Bảng HocSinh(MaHS, HoTen, Lop, DiemTB)',
        'ordered_tokens': [
            'SELECT HoTen, DiemTB',
            'FROM HocSinh',
            "WHERE Lop = '11A1' AND DiemTB >= 8.0",
            'ORDER BY DiemTB DESC'
        ],
        'distractors': [
            'GROUP BY HoTen',
            'ORDER BY DiemTB ASC'
        ],
        'explanation': 'Thứ tự chuẩn trong SQL: SELECT (chọn cột) → FROM (chọn bảng) → WHERE (lọc điều kiện) → ORDER BY ... DESC (sắp xếp giảm dần).'
    },
    {
        'id': 'sql_2',
        'topic': 'F',
        'title': 'Kết nối liên bảng Mượn Sách & Học Sinh (INNER JOIN)',
        'scenario': 'Lấy tên học sinh và ngày mượn sách bằng cách kết nối bảng MuonSach (m) với bảng HocSinh (hs) qua khóa ngoại MaHS.',
        'schema_hint': 'HocSinh(MaHS, HoTen) • MuonSach(MaPhieu, MaHS, NgayMuon)',
        'ordered_tokens': [
            'SELECT hs.HoTen, m.NgayMuon',
            'FROM MuonSach m',
            'INNER JOIN HocSinh hs',
            'ON m.MaHS = hs.MaHS'
        ],
        'distractors': [
            'LINK TABLE HocSinh',
            'WHERE m.MaHS IS NULL'
        ],
        'explanation': 'Mệnh đề INNER JOIN ... ON kết nối các bản ghi có giá trị khóa ngoại MaHS trùng khớp với khóa chính giữa 2 bảng.'
    },
    {
        'id': 'sql_3',
        'topic': 'F',
        'title': 'Thống kê sĩ số học sinh theo từng lớp',
        'scenario': 'Đếm số lượng học sinh của mỗi lớp từ bảng HocSinh và gom nhóm theo cột Lop.',
        'schema_hint': 'Bảng HocSinh(MaHS, HoTen, Lop)',
        'ordered_tokens': [
            'SELECT Lop, COUNT(*) AS SiSo',
            'FROM HocSinh',
            'GROUP BY Lop',
            'ORDER BY SiSo DESC'
        ],
        'distractors': [
            'WHERE COUNT(*) > 0',
            'JOIN Lop ON MaHS'
        ],
        'explanation': 'Khi dùng hàm gộp COUNT(*) theo từng lớp, cần sử dụng mệnh đề GROUP BY Lop trước ORDER BY.'
    },
    {
        'id': 'sql_4',
        'topic': 'F',
        'title': 'Tạo bảng CSDL Quản lý Thư viện có Khóa chính',
        'scenario': 'Khởi tạo bảng Sach gồm mã sách MaSach làm khóa chính (không rỗng) và tên sách TenSach.',
        'schema_hint': 'DDL: Câu lệnh khởi tạo cấu trúc bảng',
        'ordered_tokens': [
            'CREATE TABLE Sach (',
            'MaSach VARCHAR(10) PRIMARY KEY,',
            'TenSach NVARCHAR(150) NOT NULL',
            ');'
        ],
        'distractors': [
            'INSERT TABLE Sach (',
            'FOREIGN KEY AUTO'
        ],
        'explanation': 'Câu lệnh DDL CREATE TABLE định nghĩa tên bảng, kiểu dữ liệu từng trường và ràng buộc PRIMARY KEY / NOT NULL.'
    },
    {
        'id': 'sql_5',
        'topic': 'F',
        'title': 'Cập nhật điểm thưởng thực hành CSDL',
        'scenario': 'Cộng thêm 0.5 điểm vào cột DiemTH trong bảng BangDiem cho học sinh có mã HS102.',
        'schema_hint': 'Bảng BangDiem(MaHS, DiemTH)',
        'ordered_tokens': [
            'UPDATE BangDiem',
            'SET DiemTH = DiemTH + 0.5',
            "WHERE MaHS = 'HS102'"
        ],
        'distractors': [
            'MODIFY BangDiem',
            'FROM BangDiem'
        ],
        'explanation': 'Cú pháp cập nhật dữ liệu chuẩn DML: UPDATE <tên_bảng> SET <cột> = <giá_trị_mới> WHERE <điều_kiện>.'
    },
    {
        'id': 'sql_6',
        'topic': 'F',
        'title': 'Truy vấn các ca sĩ hoặc nhạc sĩ từ CSDL Âm nhạc',
        'scenario': 'Lấy danh sách TenBanThuAm và TenCaSi thông qua kết nối bảng BanThuAm (b) với bảng CaSi (c) theo khóa ngoại MaCaSi.',
        'schema_hint': 'BanThuAm(MaBTA, TenBanThuAm, MaCaSi) • CaSi(MaCaSi, TenCaSi)',
        'ordered_tokens': [
            'SELECT b.TenBanThuAm, c.TenCaSi',
            'FROM BanThuAm b',
            'INNER JOIN CaSi c',
            'ON b.MaCaSi = c.MaCaSi'
        ],
        'distractors': [
            'GROUP BY b.MaCaSi',
            'HAVING c.MaCaSi'
        ],
        'explanation': 'Thực hành CSDL Âm nhạc (SGK Tin 11): dùng INNER JOIN ... ON b.MaCaSi = c.MaCaSi để lấy tên ca sĩ biểu diễn.'
    }
]

ARENA_MEMORY_PAIRS = [
    {'id': 'm1', 'topic': 'A', 'term': 'Hệ điều hành (OS)', 'match': 'Điều phối CPU, RAM & thiết bị ngoại vi'},
    {'id': 'm2', 'topic': 'A', 'term': 'Phần mềm nguồn mở', 'match': 'Công khai mã nguồn theo giấy phép GPL/MIT'},
    {'id': 'm3', 'topic': 'A', 'term': 'Bộ nhớ RAM', 'match': 'Bộ nhớ khả biến, mất dữ liệu khi tắt nguồn'},
    {'id': 'm4', 'topic': 'A', 'term': 'Cổng kết nối HDMI', 'match': 'Truyền đồng thời hình ảnh HD & âm thanh số'},
    {'id': 'm5', 'topic': 'C', 'term': 'Xác thực 2 bước (2FA)', 'match': 'Bảo mật bằng Mật khẩu kết hợp mã OTP'},
    {'id': 'm6', 'topic': 'C', 'term': 'Toán tử filetype:pdf', 'match': 'Tìm kiếm nâng cao chỉ lọc tệp PDF'},
    {'id': 'm7', 'topic': 'C', 'term': 'Tấn công Phishing', 'match': 'Giả mạo trang web/email để đánh cắp tài khoản'},
    {'id': 'm8', 'topic': 'F', 'term': 'Khóa chính (Primary Key)', 'match': 'Xác định duy nhất mỗi bản ghi, không trùng/rỗng'},
    {'id': 'm9', 'topic': 'F', 'term': 'Khóa ngoại (Foreign Key)', 'match': 'Trường tham chiếu tới khóa chính của bảng khác'},
    {'id': 'm10', 'topic': 'F', 'term': 'Mệnh đề INNER JOIN', 'match': 'Kết nối dữ liệu giữa 2 bảng qua trường khóa'},
    {'id': 'm11', 'topic': 'E', 'term': 'Kênh Alpha (PNG)', 'match': 'Lưu thông tin độ trong suốt của nền ảnh'},
    {'id': 'm12', 'topic': 'E', 'term': 'Khung Timeline Video', 'match': 'Sắp xếp phân cảnh, âm thanh & hiệu ứng theo thời gian'}
]


WEEKLY_ARENA_CAMPAIGNS = [
    {
        'slot': 1,
        'topic_code': 'A',
        'title': 'Chủ đề 1: Hệ Điều Hành & Kiến Trúc Phần Cứng',
        'short_title': 'Tuần Chủ đề 1 • HĐH & Phần cứng',
        'boss_name': 'BOSS TROJAN HỆ ĐIỀU HÀNH',
        'map_name': 'Pháo Đài Vi Mạch Trung Tâm'
    },
    {
        'slot': 2,
        'topic_code': 'C',
        'title': 'Chủ đề 2 & 3: Lưu Trữ Đám Mây & An Toàn Không Gian Số',
        'short_title': 'Tuần Chủ đề 2 & 3 • Đám mây & An toàn số',
        'boss_name': 'TRÙM LỪA ĐẢO PHISHING MẠNG',
        'map_name': 'Trạm Vệ Tinh Đám Mây Bảo Mật'
    },
    {
        'slot': 3,
        'topic_code': 'F',
        'title': 'Chủ đề 4, 5 & 6: Hệ Cơ Sở Dữ Liệu & Truy Vấn SQL',
        'short_title': 'Tuần Chủ đề 4, 5, 6 • CSDL & SQL',
        'boss_name': 'GOLEM LỖI TRUY VẤN SQL',
        'map_name': 'Lõi Máy Chủ Cơ Sở Dữ Liệu'
    },
    {
        'slot': 4,
        'topic_code': 'E',
        'title': 'Chủ đề 7: Chỉnh Sửa Ảnh GIMP & Dựng Phim Hoạt Hình',
        'short_title': 'Tuần Chủ đề 7 • Thiết kế GIMP & Video',
        'boss_name': 'TRÙM GLITCH ĐA PHƯƠNG TIỆN',
        'map_name': 'Studio Đồ Họa Không Gian 3D'
    }
]


def current_iso_week_key():
    iso = datetime.utcnow().isocalendar()
    return f"{iso[0]}-W{int(iso[1]):02d}"


def current_week_label():
    iso = datetime.utcnow().isocalendar()
    return f"Tuần {int(iso[1]):02d} • Năm {iso[0]}"


def get_weekly_topic_campaign():
    iso = datetime.utcnow().isocalendar()
    week_num = int(iso[1])
    campaign = dict(WEEKLY_ARENA_CAMPAIGNS[(week_num - 1) % len(WEEKLY_ARENA_CAMPAIGNS)])
    campaign['week_num'] = week_num
    campaign['year'] = int(iso[0])
    return campaign


def ensure_arena_demo_leaderboard(pub_hub=None):
    """Khởi tạo các đối thủ mẫu trong BXH Tuần hiện tại để bảng xếp hạng luôn sôi động."""
    wk = current_iso_week_key()
    if GameScore.query.filter_by(week_key=wk).count() > 0:
        return

    target_class = Classroom.query.filter(Classroom.code != PUBLIC_CLASS_CODE).first() or pub_hub
    class_id = target_class.id if target_class else None

    demo_rivals = [
        ('hs.khoi', 'Nguyễn Minh Khôi', 'khoi.11a1@tin11.edu.vn', [
            ('blitz', 'ALL', 1180, 1180, 12, 12, 5, 34),
            ('sql_puzzle', 'F', 960, 960, 5, 5, 5, 42),
            ('memory', 'ALL', 840, 840, 6, 6, 5, 31),
        ]),
        ('hs.ngoc', 'Lê Hoàng Bảo Ngọc', 'ngoc.11a1@tin11.edu.vn', [
            ('blitz', 'F', 1120, 1120, 11, 12, 5, 37),
            ('sql_puzzle', 'F', 920, 920, 5, 5, 4, 46),
            ('memory', 'C', 780, 780, 6, 6, 4, 36),
        ]),
        ('hs.anh', 'Phạm Quốc Anh', 'anh.11a1@tin11.edu.vn', [
            ('blitz', 'A', 1040, 1040, 11, 12, 4, 41),
            ('memory', 'E', 820, 820, 6, 6, 4, 39),
        ]),
        ('hs.tien', 'Vũ Thảo Tiên', 'tien.11a1@tin11.edu.vn', [
            ('sql_puzzle', 'F', 910, 910, 5, 5, 4, 45),
            ('blitz', 'C', 860, 860, 10, 12, 3, 47),
        ]),
        ('hs.huy', 'Đặng Gia Huy', 'huy.11a1@tin11.edu.vn', [
            ('memory', 'A', 840, 840, 6, 6, 4, 48),
            ('blitz', 'ALL', 780, 780, 9, 12, 3, 51),
        ]),
        ('hs.linh', 'Hoàng Khánh Linh', 'linh.11a1@tin11.edu.vn', [
            ('blitz', 'E', 740, 740, 9, 12, 3, 53),
        ]),
        ('hs.minh', 'Bùi Nhật Minh', 'minh.11a1@tin11.edu.vn', [
            ('memory', 'F', 680, 680, 6, 8, 3, 56),
        ]),
    ]

    for uname, fname, email, games in demo_rivals:
        u = User.query.filter_by(username=uname).first()
        if not u:
            u = User(username=uname, email=email, full_name=fname, role='student')
            u.set_password('student123')
            db.session.add(u)
            db.session.flush()
            if target_class and target_class not in u.enrolled_classes:
                target_class.students.append(u)
        for g_mode, t_code, sc, xp, corr, tot, combo, dur in games:
            db.session.add(GameScore(
                user_id=u.id,
                classroom_id=class_id,
                game_mode=g_mode,
                topic_code=t_code,
                score=sc,
                xp_earned=xp,
                correct_count=corr,
                total_count=tot,
                max_combo=combo,
                duration_sec=dur,
                week_key=wk
            ))

    # Give demo student hs.nam a starting score right at Rank #4 (just behind #3)
    nam = User.query.filter_by(username='hs.nam').first()
    if nam and GameScore.query.filter_by(user_id=nam.id, week_key=wk).count() == 0:
        nam_class_id = nam.enrolled_classes[0].id if nam.enrolled_classes else class_id
        db.session.add(GameScore(
            user_id=nam.id,
            classroom_id=nam_class_id,
            game_mode='blitz',
            topic_code='F',
            score=980,
            xp_earned=980,
            correct_count=11,
            total_count=12,
            max_combo=4,
            duration_sec=43,
            week_key=wk
        ))
        db.session.add(GameScore(
            user_id=nam.id,
            classroom_id=nam_class_id,
            game_mode='sql_puzzle',
            topic_code='F',
            score=720,
            xp_earned=720,
            correct_count=4,
            total_count=5,
            max_combo=4,
            duration_sec=52,
            week_key=wk
        ))

    db.session.commit()


def _build_weekly_leaderboard(class_id=None, mode_filter='ALL', viewer_user=None):
    """
    Xếp hạng BXH Tuần theo đúng tiêu chí thi đấu:
      1. Điểm kỷ lục cao nhất (best_score giảm dần)
      2. Thời gian hoàn thành ngắn nhất (best_duration_sec tăng dần)
      3. Chuỗi Combo cao nhất (max_combo giảm dần)
      4. Tổng XP tích lũy trong tuần (total_xp giảm dần)
    """
    wk = current_iso_week_key()
    q = GameScore.query.filter_by(week_key=wk)
    if class_id:
        q = q.filter_by(classroom_id=class_id)
    if mode_filter in ('boss_rpg', 'space_shooter', 'blitz', 'sql_puzzle', 'memory'):
        q = q.filter_by(game_mode=mode_filter)

    rows = q.all()
    agg = {}
    for r in rows:
        uid = r.user_id
        if uid not in agg:
            u = r.player
            if not u:
                continue
            cls_name = 'Tự do'
            if r.classroom and r.classroom.code != PUBLIC_CLASS_CODE:
                cls_name = r.classroom.name.split('-')[0].strip()
            elif u.enrolled_classes:
                non_pub = [c for c in u.enrolled_classes if c.code != PUBLIC_CLASS_CODE]
                if non_pub:
                    cls_name = non_pub[0].name.split('-')[0].strip()
            agg[uid] = {
                'user_id': uid,
                'username': u.username,
                'full_name': u.full_name,
                'avatar_char': (u.full_name or u.username)[:1].upper(),
                'class_label': cls_name,
                'total_xp': 0,
                'best_score': -1,
                'best_duration_sec': 999,
                'max_combo': 0,
                'games_played': 0,
                'correct_sum': 0,
                'total_sum': 0,
                'mode_counts': {'boss_rpg': 0, 'space_shooter': 0, 'blitz': 0, 'sql_puzzle': 0, 'memory': 0}
            }
        item = agg[uid]
        sc = r.score or 0
        dur = max(1, r.duration_sec or 60)
        if sc > item['best_score'] or (sc == item['best_score'] and dur < item['best_duration_sec']):
            item['best_score'] = sc
            item['best_duration_sec'] = dur
        item['total_xp'] += (r.xp_earned or 0)
        item['max_combo'] = max(item['max_combo'], r.max_combo or 0)
        item['games_played'] += 1
        item['correct_sum'] += (r.correct_count or 0)
        item['total_sum'] += (r.total_count or 0)
        if r.game_mode in item['mode_counts']:
            item['mode_counts'][r.game_mode] += (r.xp_earned or 0)

    entries = list(agg.values())
    for e in entries:
        if e['best_score'] < 0:
            e['best_score'] = 0
    entries.sort(key=lambda x: (-x['best_score'], x['best_duration_sec'], -x['max_combo'], -x['total_xp'], x['user_id']))

    for idx, e in enumerate(entries):
        e['rank'] = idx + 1
        e['accuracy'] = round((e['correct_sum'] / e['total_sum']) * 100) if e['total_sum'] > 0 else 100
        top_mode = max(e['mode_counts'].items(), key=lambda kv: kv[1])[0]
        if e['rank'] == 1:
            e['badge_title'] = 'Quán Quân Tuần'
            e['badge_style'] = 'badge-admin'
        elif top_mode == 'boss_rpg' and e['mode_counts']['boss_rpg'] > 0:
            e['badge_title'] = 'Dũng Sĩ Diệt Boss'
            e['badge_style'] = 'badge-coral'
        elif top_mode == 'space_shooter' and e['mode_counts']['space_shooter'] > 0:
            e['badge_title'] = 'Xạ Thủ Ngân Hà'
            e['badge_style'] = 'badge-teal'
        elif top_mode == 'sql_puzzle' and e['mode_counts']['sql_puzzle'] > 0:
            e['badge_title'] = 'Kiện Tướng SQL'
            e['badge_style'] = 'badge-ai'
        elif top_mode == 'memory' and e['mode_counts']['memory'] > 0:
            e['badge_title'] = 'Siêu Trí Nhớ 3D'
            e['badge_style'] = 'badge-teal'
        else:
            e['badge_title'] = 'Tia Chớp Cyber'
            e['badge_style'] = 'badge-teacher'

    my_stats = {
        'rank': None,
        'total_xp': 0,
        'best_score': 0,
        'best_duration_sec': 0,
        'max_combo': 0,
        'games_played': 0,
        'accuracy': 0,
        'score_to_next': 100,
        'xp_to_next': 100,
        'next_target_name': 'Top 1 BXH',
        'next_target_rank': 1,
        'next_target_score': entries[0]['best_score'] if entries else 1000,
        'next_target_time': entries[0]['best_duration_sec'] if entries else 40
    }
    if viewer_user and viewer_user.is_authenticated:
        for idx, e in enumerate(entries):
            if e['user_id'] == viewer_user.id:
                my_stats.update({
                    'rank': e['rank'],
                    'total_xp': e['total_xp'],
                    'best_score': e['best_score'],
                    'best_duration_sec': e['best_duration_sec'],
                    'max_combo': e['max_combo'],
                    'games_played': e['games_played'],
                    'accuracy': e['accuracy']
                })
                if idx > 0:
                    above = entries[idx - 1]
                    diff_score = max(0, above['best_score'] - e['best_score'])
                    my_stats['score_to_next'] = diff_score
                    my_stats['xp_to_next'] = max(10, diff_score + 10)
                    my_stats['next_target_name'] = above['full_name']
                    my_stats['next_target_rank'] = above['rank']
                    my_stats['next_target_score'] = above['best_score']
                    my_stats['next_target_time'] = above['best_duration_sec']
                else:
                    my_stats['score_to_next'] = 0
                    my_stats['xp_to_next'] = 0
                    my_stats['next_target_name'] = 'Đang giữ Top #1'
                    my_stats['next_target_rank'] = 1
                break
        else:
            if entries:
                last_e = entries[-1]
                my_stats['score_to_next'] = last_e['best_score']
                my_stats['xp_to_next'] = max(50, last_e['best_score'])
                my_stats['next_target_name'] = last_e['full_name']
                my_stats['next_target_rank'] = last_e['rank']
                my_stats['next_target_score'] = last_e['best_score']
                my_stats['next_target_time'] = last_e['best_duration_sec']

    return {
        'week_key': wk,
        'week_label': current_week_label(),
        'entries': entries,
        'podium': entries[:3],
        'my_stats': my_stats
    }


@main_bp.route('/arena')
@login_required
def arena_hub():
    """Đấu Trường Tin Học 11 & Bảng Xếp Hạng Tuần (Mỗi tuần 1 Chủ đề + Màn hình chơi phóng to + PNG Sprites)"""
    pub_hub = ensure_public_hub()
    ensure_arena_demo_leaderboard(pub_hub)

    weekly_campaign = get_weekly_topic_campaign()
    raw_topic = request.args.get('topic', '').upper().strip()
    if not raw_topic:
        topic_filter = weekly_campaign['topic_code']
    else:
        topic_filter = TOPIC_FILTER_MAP.get(raw_topic, 'ALL') if raw_topic != 'ALL' else 'ALL'

    selected_class_id = request.args.get('class_id', type=int)
    selected_mode = request.args.get('mode', 'ALL').strip()
    if selected_mode not in ('ALL', 'boss_rpg', 'space_shooter', 'blitz', 'sql_puzzle', 'memory'):
        selected_mode = 'ALL'

    if current_user.is_admin:
        classrooms = [c for c in Classroom.query.all() if c.code != PUBLIC_CLASS_CODE]
    elif current_user.is_teacher:
        classrooms = [c for c in Classroom.query.filter_by(teacher_id=current_user.id).all() if c.code != PUBLIC_CLASS_CODE]
    else:
        classrooms = [c for c in current_user.enrolled_classes if c.code != PUBLIC_CLASS_CODE]

    # Build full question & memory pools so Lobby can filter by topic dynamically on client too
    all_mcq_pool = [q for q in SYSTEM_QUESTION_BANK if (q.get('question_type') or 'mcq') == 'mcq']
    blitz_pool = [
        q for q in all_mcq_pool
        if topic_filter == 'ALL' or q.get('topic') == topic_filter
    ]
    if len(blitz_pool) < 10:
        blitz_pool = all_mcq_pool

    memory_pool = [
        p for p in ARENA_MEMORY_PAIRS
        if topic_filter == 'ALL' or p['topic'] == topic_filter
    ]
    if len(memory_pool) < 6:
        memory_pool = list(ARENA_MEMORY_PAIRS)

    lb_data = _build_weekly_leaderboard(
        class_id=selected_class_id,
        mode_filter=selected_mode,
        viewer_user=current_user
    )

    return render_template(
        'courses/arena.html',
        blitz_questions=blitz_pool,
        all_mcq_questions=all_mcq_pool,
        sql_challenges=ARENA_SQL_CHALLENGES,
        memory_pairs=memory_pool,
        all_memory_pairs=list(ARENA_MEMORY_PAIRS),
        leaderboard=lb_data['entries'],
        podium=lb_data['podium'],
        my_stats=lb_data['my_stats'],
        week_label=lb_data['week_label'],
        week_key=lb_data['week_key'],
        weekly_campaign=weekly_campaign,
        weekly_campaigns_list=WEEKLY_ARENA_CAMPAIGNS,
        classrooms=classrooms,
        selected_class_id=selected_class_id,
        selected_mode=selected_mode,
        current_topic=topic_filter
    )


@main_bp.route('/api/arena/submit', methods=['POST'])
@login_required
def api_arena_submit():
    """Lưu điểm lượt chơi Đấu Trường và trả về thứ hạng BXH Tuần mới nhất"""
    pub_hub = ensure_public_hub()
    ensure_arena_demo_leaderboard(pub_hub)

    data = request.get_json(silent=True) or {}
    game_mode = str(data.get('game_mode') or 'boss_rpg').strip()
    if game_mode == 'platformer_2d':
        game_mode = 'boss_rpg'
    if game_mode not in ('boss_rpg', 'space_shooter', 'blitz', 'sql_puzzle', 'memory'):
        game_mode = 'boss_rpg'

    raw_topic = str(data.get('topic_code') or 'ALL').upper().strip()
    topic_code = TOPIC_FILTER_MAP.get(raw_topic, 'ALL') if raw_topic != 'ALL' else 'ALL'

    raw_score = max(0, min(3000, int(data.get('score') or 0)))
    correct_count = max(0, min(60, int(data.get('correct_count') or 0)))
    total_count = max(1, min(60, int(data.get('total_count') or 1)))
    max_combo = max(0, min(60, int(data.get('max_combo') or 0)))
    duration_sec = max(1, min(600, int(data.get('duration_sec') or 30)))

    # Determine previous rank before saving
    before_lb = _build_weekly_leaderboard(viewer_user=current_user)
    prev_rank = before_lb['my_stats']['rank']

    # Determine classroom association for student
    cls_id = None
    non_pub_classes = [c for c in current_user.enrolled_classes if c.code != PUBLIC_CLASS_CODE]
    if non_pub_classes:
        cls_id = non_pub_classes[0].id
    elif pub_hub:
        cls_id = pub_hub.id

    wk = current_iso_week_key()
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    games_today = GameScore.query.filter(
        GameScore.user_id == current_user.id,
        GameScore.played_at >= today_start
    ).count()

    # Anti-farm rule: first 10 games per day grant 100% XP; subsequent grant 35% practice XP
    xp_multiplier = 1.0 if games_today < 10 else 0.35
    xp_earned = max(25, int(round(raw_score * xp_multiplier)))

    entry = GameScore(
        user_id=current_user.id,
        classroom_id=cls_id,
        game_mode=game_mode,
        topic_code=topic_code,
        score=raw_score,
        xp_earned=xp_earned,
        correct_count=correct_count,
        total_count=total_count,
        max_combo=max_combo,
        duration_sec=duration_sec,
        week_key=wk
    )
    db.session.add(entry)
    db.session.commit()

    after_lb = _build_weekly_leaderboard(viewer_user=current_user)
    new_rank = after_lb['my_stats']['rank']
    rank_up = (prev_rank is None and new_rank is not None) or (
        prev_rank is not None and new_rank is not None and new_rank < prev_rank
    )

    return jsonify({
        'success': True,
        'score': raw_score,
        'duration_sec': duration_sec,
        'xp_earned': xp_earned,
        'games_today': games_today + 1,
        'prev_rank': prev_rank,
        'new_rank': new_rank,
        'rank_up': rank_up,
        'my_stats': after_lb['my_stats'],
        'leaderboard': after_lb['entries'],
        'podium': after_lb['podium']
    })


@main_bp.route('/exams')
@login_required
def exams_list():
    """Mục Đề kiểm tra: hiển thị cả Đề ôn luyện chung của hệ thống và Đề giáo viên giao về lớp"""
    pub_hub = ensure_public_hub()
    if current_user.is_admin:
        exams = Exam.query.order_by(Exam.created_at.desc()).all()
        classrooms = Classroom.query.all()
    elif current_user.is_teacher:
        classrooms = Classroom.query.filter_by(teacher_id=current_user.id).all()
        exams = Exam.query.filter_by(teacher_id=current_user.id).order_by(Exam.created_at.desc()).all()
    else:
        classrooms = get_student_accessible_classes(current_user)
        class_ids = [c.id for c in classrooms]
        exams = Exam.query.filter(Exam.classroom_id.in_(class_ids), Exam.is_published == True).order_by(Exam.created_at.desc()).all() if class_ids else []

    user_submissions = {}
    if current_user.is_student:
        subs = ExamSubmission.query.filter_by(student_id=current_user.id).all()
        for s in subs:
            user_submissions[s.exam_id] = s

    return render_template('exams/exams_list.html', exams=exams, classrooms=classrooms, user_submissions=user_submissions, public_hub=pub_hub)


@main_bp.route('/materials')
@login_required
def materials_list():
    """Mục Kho Tài liệu: tổng hợp toàn bộ PPTX, DOCX, PDF, VIDEO từ Kho chung & Lớp học"""
    ensure_public_hub()
    file_type = request.args.get('type', '').lower()
    
    base_query = Material.query.join(Lesson).join(Course).join(Classroom)
    
    if not current_user.is_admin:
        if current_user.is_teacher:
            base_query = base_query.filter(
                (Classroom.teacher_id == current_user.id) | (Classroom.code == PUBLIC_CLASS_CODE)
            )
        else:
            class_ids = [c.id for c in get_student_accessible_classes(current_user)]
            base_query = base_query.filter(Classroom.id.in_(class_ids)) if class_ids else base_query.filter(Classroom.id == -1)

    all_materials = base_query.all()
    counts = {
        'all': len(all_materials),
        'pptx': sum(1 for m in all_materials if m.file_type in ['pptx', 'ppt']),
        'docx': sum(1 for m in all_materials if m.file_type == 'docx'),
        'pdf': sum(1 for m in all_materials if m.file_type == 'pdf'),
        'video': sum(1 for m in all_materials if m.file_type in ['mp4', 'webm', 'ogg', 'mov'])
    }

    query = base_query
    if file_type in ['pdf', 'docx', 'pptx', 'video']:
        if file_type == 'pptx':
            query = query.filter(Material.file_type.in_(['pptx', 'ppt']))
        elif file_type == 'video':
            query = query.filter(Material.file_type.in_(['mp4', 'webm', 'ogg', 'mov']))
        else:
            query = query.filter(Material.file_type == file_type)
            
    materials = query.order_by(Material.uploaded_at.desc()).all()

    return render_template('materials/materials_list.html', materials=materials, current_type=file_type, counts=counts)


@main_bp.route('/ai-advisor')
@login_required
def ai_advisor():
    """AI Tư Vấn Lộ Trình Học Tập Cá Nhân Hóa cho học sinh Tin học 11"""
    submissions = ExamSubmission.query.filter_by(student_id=current_user.id).order_by(ExamSubmission.started_at.desc()).all()
    total_exams_taken = len(submissions)
    avg_ratio = 0.0
    total_violations = 0
    if submissions:
        ratios = []
        for s in submissions:
            tp = s.total_points or 10.0
            ratios.append((s.score / tp) * 10.0 if tp > 0 else 0.0)
            total_violations += (s.violations_count or 0)
        avg_ratio = round(sum(ratios) / len(ratios), 1)

    # Determine learner level & recommended priority
    if total_exams_taken == 0:
        learner_tier = 'Khởi động lộ trình'
        recommended_topic = 'F'
        summary_advice = 'Bạn chưa thực hiện bài kiểm tra định kỳ nào. AI khuyến nghị bắt đầu từ Chủ đề F (Cơ sở dữ liệu & SQL) kết hợp lật thẻ Flashcard trước khi làm bài thi 15 phút.'
    elif avg_ratio >= 8.0:
        learner_tier = 'Năng lực Tốt • Sẵn sàng nâng cao'
        recommended_topic = 'F'
        summary_advice = f'Điểm trung bình quy đổi của bạn đạt {avg_ratio}/10. Bạn nắm vững kiến thức nền tảng; hãy tập trung luyện các câu truy vấn SQL nâng cao (JOIN, GROUP BY) và thực hành xử lý ảnh đa lớp trên GIMP.'
    elif avg_ratio >= 5.5:
        learner_tier = 'Năng lực Khá • Cần củng cố thực hành'
        recommended_topic = 'C'
        summary_advice = f'Điểm trung bình quy đổi đạt {avg_ratio}/10. Bạn cần đọc kỹ lại tài liệu DOCX/PDF của từng bài và hoàn thành tối thiểu 8 câu tại Góc Ôn Luyện trước khi bước vào phòng thi giám sát.'
    else:
        learner_tier = 'Cần bù đắp kiến thức trọng tâm'
        recommended_topic = 'A'
        summary_advice = f'Điểm trung bình hiện tại là {avg_ratio}/10. Đừng lo lắng! AI đã chia nhỏ lộ trình 4 bước từ cơ bản nhất (Chủ đề A & C) để bạn ôn lại từng khái niệm qua Flashcard và Video bài giảng.'

    lessons = Lesson.query.order_by(Lesson.order_index.asc()).limit(6).all()
    return render_template(
        'courses/ai_advisor.html',
        submissions=submissions,
        total_exams_taken=total_exams_taken,
        avg_ratio=avg_ratio,
        total_violations=total_violations,
        learner_tier=learner_tier,
        recommended_topic=recommended_topic,
        summary_advice=summary_advice,
        lessons=lessons
    )


@main_bp.route('/api/ai-learning-path', methods=['POST'])
@login_required
def api_ai_learning_path():
    """API sinh lộ trình học tập cá nhân hóa dựa trên mục tiêu, chủ đề yếu và quỹ thời gian"""
    data = request.get_json(silent=True) or {}
    goal = data.get('goal', 'score_9')
    topic = TOPIC_FILTER_MAP.get(str(data.get('topic', 'F')).upper().strip(), 'F')
    daily_minutes = int(data.get('daily_minutes', 30))
    custom_note = (data.get('custom_note') or '').strip()

    topic_catalog = {
        'A': {
            'code': 'CHỦ ĐỀ 1 (A)',
            'title': 'Chủ đề 1. Máy tính và xã hội tri thức (Bài 1 – Bài 5)',
            'theory_focus': 'Phân biệt rõ chức năng quản lý tiến trình/tài nguyên của Hệ điều hành, giấy phép Phần mềm nguồn mở (GPL, MIT), CPU/RAM và thiết bị số.',
            'doc_formats': 'Đọc slide PPTX sơ đồ kiến trúc hệ điều hành và tài liệu PDF so sánh Windows, Linux, Android, iOS.',
            'practice_link': url_for('main.practice_hub', topic='A'),
            'key_milestone': 'Hoàn thành bộ câu hỏi Chủ đề 1 đạt 100% và nắm vững 5 bài đầu SGK.'
        },
        'C': {
            'code': 'CHỦ ĐỀ 2 & 3 (C)',
            'title': 'Chủ đề 2 & 3. Lưu trữ, tìm kiếm thông tin & Giao tiếp an toàn (Bài 6 – Bài 9)',
            'theory_focus': 'Nắm vững cơ chế đồng bộ đám mây (Google Drive, OneDrive), toán tử tìm kiếm (filetype:, dấu ngoặc kép) và phòng tránh lừa đảo Phishing / bảo mật 2FA.',
            'doc_formats': 'Xem tài liệu hướng dẫn DOCX về phân quyền thư mục đám mây và Video tình huống an toàn môi trường số.',
            'practice_link': url_for('main.practice_hub', topic='C'),
            'key_milestone': 'Thực hành phân loại quyền Xem/Nhận xét/Chỉnh sửa và vượt qua bài ôn luyện Chủ đề 2 & 3.'
        },
        'F': {
            'code': 'CHỦ ĐỀ 4, 5 & 6 (F)',
            'title': 'Chủ đề 4, 5 & 6. Hệ Cơ sở dữ liệu, SQL & Thực hành khai thác CSDL (Bài 10 – Bài 24)',
            'theory_focus': 'Hiểu bản chất Khóa chính (Primary Key), Khóa ngoại (Foreign Key), câu lệnh SELECT ... FROM ... WHERE ... INNER JOIN và thực hành tạo lập, sao lưu CSDL.',
            'doc_formats': 'Đọc sổ tay PDF mẫu câu lệnh SQL, xem Video minh họa kết nối bảng bằng INNER JOIN và sao lưu tệp .sql.',
            'practice_link': url_for('main.practice_hub', topic='F'),
            'key_milestone': 'Tự viết được truy vấn lọc dữ liệu liên bảng và đạt điểm tối đa phần trắc nghiệm CSDL.'
        },
        'E': {
            'code': 'CHỦ ĐỀ 7 (E)',
            'title': 'Chủ đề 7. Phần mềm chỉnh sửa ảnh và làm video (Bài 25 – Bài 31)',
            'theory_focus': 'Làm chủ cơ chế Lớp ảnh (Layers), công cụ vùng chọn, kênh Alpha tạo nền trong suốt (PNG), ảnh động và biên tập phim hoạt hình / video.',
            'doc_formats': 'Xem Video thao tác trực tiếp trên phần mềm GIMP và đọc tệp DOCX quy trình biên tập phim trên Timeline.',
            'practice_link': url_for('main.practice_hub', topic='E'),
            'key_milestone': 'Phân biệt đúng định dạng xuất tệp PNG/JPG/XCF/MP4 và hoàn thành bài ôn tập Chủ đề 7.'
        }
    }

    selected = topic_catalog.get(topic, topic_catalog['F'])

    goal_labels = {
        'exam_15m': 'Ôn cấp tốc kiểm tra 15 phút',
        'midterm': 'Chinh phục bài thi Giữa kỳ / Học kỳ',
        'score_9': 'Mục tiêu bứt phá 9.0+ môn Tin học 11',
        'practical': 'Tăng tốc kỹ năng thực hành ứng dụng'
    }
    goal_title = goal_labels.get(goal, 'Lộ trình học tập cá nhân hóa')

    coach_reply = (
        f"Dựa trên mục tiêu \"{goal_title}\" với quỹ thời gian {daily_minutes} phút/ngày, "
        f"AI đề xuất bạn ưu tiên {selected['code']} ({selected['title']})."
    )
    if custom_note:
        coach_reply += f" Về câu hỏi của bạn (\"{custom_note}\"): hãy bắt đầu bằng việc đọc tóm tắt lý thuyết kết hợp tài liệu DOCX/PDF trong bài học, sau đó kiểm tra đáp án tức thì tại Góc Ôn Luyện để nắm bản chất."

    steps = [
        {
            'step': 'Giai đoạn 01',
            'duration': f'{max(8, int(daily_minutes * 0.3))} phút',
            'title': f'Đọc Poster trọng tâm & Học liệu ({selected["code"]})',
            'detail': f'{selected["theory_focus"]} {selected["doc_formats"]}',
            'action_label': 'Mở Mục Bài Học',
            'action_url': url_for('main.lessons_list')
        },
        {
            'step': 'Giai đoạn 02',
            'duration': f'{max(7, int(daily_minutes * 0.25))} phút',
            'title': 'Xem Video minh họa & Tài liệu DOCX / PDF',
            'detail': 'Mở Kho Tài Liệu Đa Phương Tiện để xem trực tuyến slide bài giảng, tài liệu Word và video thao tác mẫu ngay trên trình duyệt.',
            'action_label': 'Mở Kho Tài Liệu & Video',
            'action_url': url_for('main.materials_list')
        },
        {
            'step': 'Giai đoạn 03',
            'duration': f'{max(8, int(daily_minutes * 0.25))} phút',
            'title': 'Lật thẻ Flashcard & Trắc nghiệm giải thích tức thì',
            'detail': selected['key_milestone'],
            'action_label': f'Ôn luyện {selected["code"]}',
            'action_url': selected['practice_link']
        },
        {
            'step': 'Giai đoạn 04',
            'duration': f'{max(7, int(daily_minutes * 0.2))} phút',
            'title': 'Thử sức tại Phòng thi Giám sát Anti-Cheat',
            'detail': 'Làm đề kiểm tra định kỳ với chế độ toàn màn hình và bảng điều hướng câu hỏi để rèn tâm lý phòng thi thực tế.',
            'action_label': 'Vào Phòng Thi Chính Thức',
            'action_url': url_for('main.exams_list')
        }
    ]

    return jsonify({
        'success': True,
        'goal_title': goal_title,
        'topic_code': selected['code'],
        'topic_title': selected['title'],
        'coach_reply': coach_reply,
        'steps': steps
    })


@main_bp.route('/admin/manage')
@login_required
def admin_manage():
    """Mục Quản trị hệ thống: quản lý tài khoản & toàn bộ audit log chống gian lận"""
    if not current_user.is_admin and not current_user.is_teacher:
        flash('Bạn không có quyền truy cập mục Quản trị!', 'warning')
        return redirect(url_for('main.index'))
        
    users = User.query.order_by(User.created_at.desc()).all()
    classrooms = Classroom.query.all()
    
    # Filter logs by event type if requested
    event_filter = request.args.get('event', '')
    log_query = ProctoringLog.query.order_by(ProctoringLog.timestamp.desc())
    if event_filter:
        log_query = log_query.filter_by(event_type=event_filter)
    violations = log_query.limit(50).all()
    
    stats = {
        'total_users': len(users),
        'total_teachers': sum(1 for u in users if u.role == 'teacher'),
        'total_students': sum(1 for u in users if u.role == 'student'),
        'total_admins': sum(1 for u in users if u.role == 'admin'),
        'total_classes': len(classrooms),
        'total_exams': Exam.query.count(),
        'total_violations': ProctoringLog.query.count()
    }
    
    return render_template('dashboard/admin_manage.html', users=users, violations=violations, stats=stats, current_event=event_filter)


@main_bp.route('/admin/users/<int:user_id>/role', methods=['POST'])
@login_required
@admin_required
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Bạn không thể tự thay đổi vai trò của chính mình!', 'warning')
        return redirect(url_for('main.admin_manage'))
        
    new_role = request.form.get('role', 'student')
    if new_role in ['student', 'teacher', 'admin']:
        user.role = new_role
        db.session.commit()
        flash(f'Đã cập nhật vai trò của {user.full_name} thành {new_role.upper()}!', 'success')
        
    return redirect(url_for('main.admin_manage'))

