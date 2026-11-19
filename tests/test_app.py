import pytest
from app import create_app, db
from app.models import User, Classroom, Course, Lesson, Exam, Question, ExamSubmission, ProctoringLog

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'test-secret-key'
    UPLOAD_FOLDER = '/tmp/test_uploads'

@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # Seed test teacher and student
        teacher = User(username='test_teacher', email='teacher@test.com', full_name='Thầy Test', role='teacher')
        teacher.set_password('pass123')
        student = User(username='test_student', email='student@test.com', full_name='Em Test', role='student')
        student.set_password('pass123')
        db.session.add_all([teacher, student])
        db.session.commit()
        
        yield app.test_client()
        db.session.remove()
        db.drop_all()

def test_user_roles(client):
    teacher = User.query.filter_by(username='test_teacher').first()
    student = User.query.filter_by(username='test_student').first()
    
    assert teacher.is_teacher is True
    assert teacher.is_admin is False
    assert student.is_student is True
    assert student.check_password('pass123') is True
    assert student.check_password('wrongpass') is False

def test_login_logout(client):
    response = client.post('/auth/login', data={
        'login_input': 'test_student',
        'password': 'pass123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'G\xc3\xb3c H\xe1\xbb\x8dc T\xe1\xba\xadp' in response.data  # "Góc Học Tập"

    logout_resp = client.get('/auth/logout', follow_redirects=True)
    assert logout_resp.status_code == 200
    assert b'\xc4\x90\xc4\x83ng Nh\xe1\xba\xadp' in logout_resp.data  # "Đăng Nhập"

def test_classroom_and_exam_flow(client):
    # 1. Login as teacher
    client.post('/auth/login', data={'login_input': 'test_teacher', 'password': 'pass123'})
    
    # 2. Create classroom
    resp = client.post('/classrooms/create', data={
        'name': 'Lớp 11 Tin Học Ứng Dụng',
        'description': 'Mô tả lớp'
    }, follow_redirects=True)
    assert resp.status_code == 200
    
    classroom = Classroom.query.first()
    assert classroom is not None
    assert classroom.name == 'Lớp 11 Tin Học Ứng Dụng'
    
    # 3. Create Exam with Anti-cheating
    client.post(f'/classrooms/{classroom.id}/exams/create', data={
        'title': 'Đề Kiểm Tra Giữa Kỳ',
        'duration_minutes': 15,
        'max_violations': 2,
        'enable_fullscreen': True,
        'enable_tab_lock': True
    }, follow_redirects=True)
    
    exam = Exam.query.first()
    assert exam is not None
    assert exam.max_violations == 2
    
    # 4. Add Question
    client.post(f'/exams/{exam.id}/add-question', data={
        'content': 'Thẻ HTML nào tạo liên kết?',
        'option_a': '<a>',
        'option_b': '<link>',
        'option_c': '<href>',
        'option_d': '<nav>',
        'correct_option': 'A',
        'points': 10.0
    }, follow_redirects=True)
    
    assert Question.query.count() == 1
    
    # 5. Switch to student and join class
    client.get('/auth/logout')
    client.post('/auth/login', data={'login_input': 'test_student', 'password': 'pass123'})
    
    join_resp = client.post('/classrooms/join', data={'code': classroom.code}, follow_redirects=True)
    assert join_resp.status_code == 200
    
    # 6. Take Exam
    take_resp = client.get(f'/exams/{exam.id}/take')
    assert take_resp.status_code == 200
    
    submission = ExamSubmission.query.first()
    assert submission is not None
    assert submission.status == 'in_progress'
    
    # 7. Test Anti-cheating violation API
    v_resp = client.post(f'/api/exam/{submission.id}/violation', json={
        'event_type': 'TAB_SWITCH',
        'details': 'Học sinh chuyển sang tab khác'
    })
    v_data = v_resp.get_json()
    assert v_data['success'] is True
    assert v_data['violations_count'] == 1
    assert v_data['auto_submit'] is False
    
    # Second violation -> reaches max_violations (2) -> trigger auto submit
    v_resp2 = client.post(f'/api/exam/{submission.id}/violation', json={
        'event_type': 'EXIT_FULLSCREEN',
        'details': 'Học sinh thoát toàn màn hình'
    })
    v_data2 = v_resp2.get_json()
    assert v_data2['violations_count'] == 2
    assert v_data2['auto_submit'] is True
    
    # 8. Submit Answers and check scoring
    submit_resp = client.post(f'/exams/{submission.id}/submit', data={
        f'question_{Question.query.first().id}': 'A'
    }, follow_redirects=True)
    assert submit_resp.status_code == 200
    
    updated_sub = db.session.get(ExamSubmission, submission.id)
    assert updated_sub.score == 10.0

def test_sidebar_sections_access(client):
    # 1. Login as teacher
    client.post('/auth/login', data={'login_input': 'test_teacher', 'password': 'pass123'})
    
    # 2. Access Mục Bài Học (/lessons)
    resp_lessons = client.get('/lessons')
    assert resp_lessons.status_code == 200
    assert b'M\xe1\xbb\xa5c B\xc3\xa0i H\xe1\xbb\x8dc' in resp_lessons.data  # "Mục Bài Học"
    
    # 3. Access Mục Kiểm Tra (/exams)
    resp_exams = client.get('/exams')
    assert resp_exams.status_code == 200
    assert b'M\xe1\xbb\xa5c Ki\xe1\xbb\x83m Tra' in resp_exams.data  # "Mục Kiểm Tra"
    
    # 4. Access Mục Kho Tài Liệu (/materials)
    resp_materials = client.get('/materials')
    assert resp_materials.status_code == 200
    assert b'Kho T\xc3\xa0i Li\xe1\xbb\x87u' in resp_materials.data  # "Kho Tài Liệu"
    
    # 5. Access Mục Quản Trị (/admin/manage) as teacher
    resp_manage = client.get('/admin/manage')
    assert resp_manage.status_code == 200
    assert b'M\xe1\xbb\xa5c Qu\xe1\xba\xa3n Tr\xe1\xbb\x8b' in resp_manage.data  # "Mục Quản Trị"

    # 6. Access Góc Ôn Luyện (/practice) & topic filter
    resp_practice = client.get('/practice')
    assert resp_practice.status_code == 200
    assert 'Góc Ôn Luyện'.encode('utf-8') in resp_practice.data
    resp_practice_f = client.get('/practice?topic=F')
    assert resp_practice_f.status_code == 200
    assert 'SQL'.encode('utf-8') in resp_practice_f.data

    # 7. Access AI Tư Vấn Lộ Trình Học Tập (/ai-advisor) & API (/api/ai-learning-path)
    resp_ai = client.get('/ai-advisor')
    assert resp_ai.status_code == 200
    assert 'AI Tư Vấn Lộ Trình Học Tập'.encode('utf-8') in resp_ai.data

    api_ai_resp = client.post('/api/ai-learning-path', json={
        'goal': 'score_9',
        'topic': 'F',
        'daily_minutes': 30,
        'custom_note': 'Em muốn học nhanh SQL'
    })
    assert api_ai_resp.status_code == 200
    ai_json = api_ai_resp.get_json()
    assert ai_json['success'] is True
    assert len(ai_json['steps']) == 4


def test_free_student_question_types_and_excel_export(client):
    import io
    from app.utils import SYSTEM_QUESTION_BANK, generate_random_practice_exam, score_true_false_4

    # Verify only mcq and true_false exist in SYSTEM_QUESTION_BANK
    assert all(q['question_type'] in ('mcq', 'true_false') for q in SYSTEM_QUESTION_BANK)

    # Verify random practice generator produces 24 MCQ (0.25 pts) + 6 True/False 4-statement (1.0 pt)
    part1, part2 = generate_random_practice_exam('ALL')
    assert len(part1) == 24
    assert all(q['points'] == 0.25 for q in part1)
    assert round(sum(q['points'] for q in part1), 2) == 6.0
    assert len(part2) == 6
    assert all(q['question_type'] == 'true_false' and q['points'] == 1.0 for q in part2)

    # Verify 4-statement True/False scoring table: 1->0.1, 2->0.25, 3->0.5, 4->1.0
    assert score_true_false_4('S,D,S,D', 'D,S,D,S')[0] == 0.0
    assert score_true_false_4('D,D,S,D', 'D,S,D,S')[0] == 0.1
    assert score_true_false_4('D,S,S,D', 'D,S,D,S')[0] == 0.25
    assert score_true_false_4('D,S,D,D', 'D,S,D,S')[0] == 0.5
    assert score_true_false_4('D,S,D,S', 'D,S,D,S')[0] == 1.0

    # 1. Free student (not enrolled in any class) logs in and sees Public Hub lessons & exams
    client.post('/auth/login', data={'login_input': 'test_student', 'password': 'pass123'})
    resp_free_lessons = client.get('/lessons')
    assert resp_free_lessons.status_code == 200
    assert 'Kho Học Liệu Chung'.encode('utf-8') in resp_free_lessons.data

    resp_free_exams = client.get('/exams')
    assert resp_free_exams.status_code == 200
    assert 'Đề Ôn Luyện Tổng Hợp'.encode('utf-8') in resp_free_exams.data
    client.get('/auth/logout')

    # 2. Teacher creates classroom, exam, imports RANDOM_30 from bank, uploads CSV, adds 4-statement TF
    client.post('/auth/login', data={'login_input': 'test_teacher', 'password': 'pass123'})
    client.post('/classrooms/create', data={'name': '11A2', 'description': 'Lop 11A2'})
    cls = Classroom.query.filter_by(name='11A2').first()
    client.post(f'/classrooms/{cls.id}/exams/create', data={
        'title': 'De Kiem Tra Chuan Cau Truc',
        'duration_minutes': 45,
        'max_violations': 3
    })
    exam = Exam.query.filter_by(title='De Kiem Tra Chuan Cau Truc').first()

    # Add 4-statement True/False question
    client.post(f'/exams/{exam.id}/add-question', data={
        'question_type': 'true_false',
        'content': 'Xet cac phat bieu ve he dieu hanh nguon mo:',
        'option_a': 'Linux la he dieu hanh nguon mo.',
        'option_b': 'Khong ai duoc xem ma nguon Linux.',
        'option_c': 'Ubuntu phat trien dua tren nhan Linux.',
        'option_d': 'Android su dung nhan Linux.',
        'correct_option': 'D,S,D,D',
        'points': 1.0
    })

    # Import RANDOM_30 from System Question Bank (24 MCQ + 6 TF = 30 questions)
    client.post(f'/exams/{exam.id}/import-bank', data={'topic_quick': 'RANDOM_30'})

    # Upload CSV question file (MCQ)
    csv_bytes = b"question_type,content,option_a,option_b,option_c,option_d,correct_option,points\nmcq,Dinh dang anh nen trong suot,PNG,JPG,BMP,TXT,A,0.25\n"
    client.post(
        f'/exams/{exam.id}/upload-questions',
        data={'exam_file': (io.BytesIO(csv_bytes), 'de_mau.csv')},
        content_type='multipart/form-data'
    )

    assert exam.questions.count() == 32

    # Export Excel (.csv UTF-8 BOM)
    excel_resp = client.get(f'/exams/{exam.id}/export-excel')
    assert excel_resp.status_code == 200
    assert 'text/csv' in excel_resp.content_type
    assert b'Ho va Ten Hoc Sinh' in excel_resp.data


def test_guest_landing_and_admin_lesson_editing(client):
    # 1. Verify concise, visual Guest Landing page renders image slots and key highlights cleanly
    guest_resp = client.get('/')
    assert guest_resp.status_code == 200
    assert 'VỊ TRÍ ẢNH 1'.encode('utf-8') in guest_resp.data
    assert '7 Chủ Đề'.encode('utf-8') in guest_resp.data
    assert '4 Mảng Kiến Thức Cốt Lõi'.encode('utf-8') in guest_resp.data

    # 2. Seed an admin user and login
    admin = User(username='test_admin', email='admin@test.com', full_name='Quản Trị Viên', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()

    client.post('/auth/login', data={'login_input': 'test_admin', 'password': 'admin123'})

    # Verify Admin Dashboard renders 200 cleanly
    admin_dash = client.get('/admin')
    assert admin_dash.status_code == 200
    assert 'Quản Trị &amp; Giám Sát An Ninh Thi'.encode('utf-8') in admin_dash.data

    # Ensure public hub 7 topics & 31 lessons exist on /lessons
    lessons_resp = client.get('/lessons')
    assert lessons_resp.status_code == 200
    assert Course.query.count() == 7
    assert Lesson.query.count() == 31
    assert 'Chủ đề 1. Máy tính và xã hội tri thức'.encode('utf-8') in lessons_resp.data
    assert 'Chủ đề 7. Phần mềm chỉnh sửa ảnh và làm video'.encode('utf-8') in lessons_resp.data
    assert 'Thực hành tạo phim hoạt hình'.encode('utf-8') in lessons_resp.data
    lesson = Lesson.query.first()
    assert lesson is not None

    # 3. Admin freely edits lesson title, headings/sections, poster_url, and YouTube video_embed
    edit_resp = client.post(f'/lessons/{lesson.id}/edit', data={
        'order_index': 5,
        'title': 'Bài 5. Kiến trúc Hệ điều hành & Thực hành Linux',
        'content': '# I. Khái niệm hệ điều hành\n## 1. Vai trò điều phối\n- Quản lý CPU và bộ nhớ RAM',
        'poster_url': 'img/posters/poster_f_web.jpg',
        'video_embed': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    }, follow_redirects=True)
    assert edit_resp.status_code == 200
    html = edit_resp.data.decode('utf-8')
    assert 'Bài 5. Kiến trúc Hệ điều hành &amp; Thực hành Linux' in html or 'Bài 5. Kiến trúc Hệ điều hành' in html
    assert 'I. Khái niệm hệ điều hành' in html
    assert 'poster_f_web.jpg' in html
    assert 'https://www.youtube.com/embed/dQw4w9WgXcQ' in html

    # 4. Admin also tests raw HTML iframe embed in video_embed
    edit_html_resp = client.post(f'/lessons/{lesson.id}/edit', data={
        'order_index': 5,
        'title': 'Bài 5. Kiến trúc Hệ điều hành',
        'content': '# I. Tổng quan',
        'poster_url': 'img/posters/poster_c_cloud.jpg',
        'video_embed': '<iframe src="https://www.youtube.com/embed/abc123xyz" allowfullscreen></iframe>'
    }, follow_redirects=True)
    assert edit_html_resp.status_code == 200
    assert b'https://www.youtube.com/embed/abc123xyz' in edit_html_resp.data


def test_strict_exam_management_and_anticheating_v2(client):
    from app.models import ExamSubmission

    # 1. Teacher creates classroom and exam with PIN, fullscreen lock, tab lock, and question shuffling
    client.post('/auth/login', data={'login_input': 'test_teacher', 'password': 'pass123'})
    client.post('/classrooms/create', data={'name': '11A9-PROCTOR', 'description': 'Lop thi nghiem ngat'})
    cls = Classroom.query.filter_by(name='11A9-PROCTOR').first()

    client.post(f'/classrooms/{cls.id}/exams/create', data={
        'title': 'Kiem Tra 15p Chuyen Sau',
        'duration_minutes': 20,
        'max_violations': 2,
        'access_code': 'TIN11VIP',
        'enable_fullscreen': 'on',
        'enable_tab_lock': 'on',
        'shuffle_questions': 'on',
        'is_published': 'on'
    })
    exam = Exam.query.filter_by(title='Kiem Tra 15p Chuyen Sau').first()
    assert exam is not None
    assert exam.access_code == 'TIN11VIP'
    assert exam.shuffle_questions is True

    # Add 2 questions
    client.post(f'/exams/{exam.id}/add-question', data={
        'question_type': 'mcq',
        'content': 'Khoa chinh trong SQL la tu khoa nao?',
        'option_a': 'PRIMARY KEY',
        'option_b': 'FOREIGN KEY',
        'option_c': 'UNIQUE',
        'option_d': 'CHECK',
        'correct_option': 'A',
        'points': 5.0
    })
    client.post(f'/exams/{exam.id}/add-question', data={
        'question_type': 'mcq',
        'content': 'Câu hỏi phụ để test xóa',
        'option_a': 'A',
        'option_b': 'B',
        'option_c': 'C',
        'option_d': 'D',
        'correct_option': 'B',
        'points': 1.0
    })
    assert exam.questions.count() == 2

    # Delete the second question
    q_to_del = exam.questions.order_by(Question.id.desc()).first()
    client.post(f'/questions/{q_to_del.id}/delete', follow_redirects=True)
    assert exam.questions.count() == 1
    q_main = exam.questions.first()

    # Teacher locks exam with 1-click toggle
    client.post(f'/exams/{exam.id}/toggle-status')
    db.session.refresh(exam)
    assert exam.is_published is False
    client.get('/auth/logout')

    # 2. Student joins class and tries to take locked exam -> blocked
    client.post('/auth/login', data={'login_input': 'test_student', 'password': 'pass123'})
    client.post('/classrooms/join', data={'class_code': cls.code})
    locked_resp = client.get(f'/exams/{exam.id}/take', follow_redirects=True)
    assert 'Phòng thi hiện đang tạm khóa'.encode('utf-8') in locked_resp.data
    client.get('/auth/logout')

    # 3. Teacher unlocks exam
    client.post('/auth/login', data={'login_input': 'test_teacher', 'password': 'pass123'})
    client.post(f'/exams/{exam.id}/toggle-status')
    db.session.refresh(exam)
    assert exam.is_published is True
    client.get('/auth/logout')

    # 4. Student enters exam -> sees PIN gate first
    client.post('/auth/login', data={'login_input': 'test_student', 'password': 'pass123'})
    pin_gate_resp = client.get(f'/exams/{exam.id}/take')
    assert pin_gate_resp.status_code == 200
    assert 'Nhập mã PIN phòng thi'.encode('utf-8') in pin_gate_resp.data
    assert ExamSubmission.query.filter_by(exam_id=exam.id).count() == 0

    # Student enters wrong PIN -> still on PIN gate
    wrong_pin_resp = client.post(f'/exams/{exam.id}/take', data={'access_code': 'WRONGPIN'})
    assert 'Mã PIN phòng thi không chính xác'.encode('utf-8') in wrong_pin_resp.data
    assert ExamSubmission.query.filter_by(exam_id=exam.id).count() == 0

    # Student enters correct PIN -> submission starts!
    ok_pin_resp = client.post(f'/exams/{exam.id}/take', data={'access_code': 'tin11vip'})
    assert ok_pin_resp.status_code == 200
    assert b'PROCTORING v2.0' in ok_pin_resp.data
    sub = ExamSubmission.query.filter_by(exam_id=exam.id).first()
    assert sub is not None
    assert sub.status == 'in_progress'

    # 5. Student autosaves answer A (worth 5.0 pts)
    autosave_resp = client.post(f'/api/exam/{sub.id}/autosave', json={
        'answers': {str(q_main.id): 'A'}
    })
    assert autosave_resp.status_code == 200
    assert autosave_resp.get_json()['saved'] is True

    # 6. Anti-cheat sensors log 2 violations -> auto-submits AND grades the autosaved answer!
    v1 = client.post(f'/api/exam/{sub.id}/violation', json={
        'event_type': 'SPLIT_SCREEN_RESIZE',
        'details': 'Chia đôi màn hình làm bài'
    }).get_json()
    assert v1['violations_count'] == 1
    assert v1['auto_submit'] is False

    v2 = client.post(f'/api/exam/{sub.id}/violation', json={
        'event_type': 'DEVTOOLS_ATTEMPT',
        'details': 'Mở F12 DevTools'
    }).get_json()
    assert v2['violations_count'] == 2
    assert v2['auto_submit'] is True

    db.session.refresh(sub)
    assert sub.status == 'auto_submitted_violation'
    assert sub.score == 5.0  # Autosaved answer was automatically graded!

    # Student cannot retake while locked
    retake_resp = client.get(f'/exams/{exam.id}/take', follow_redirects=False)
    assert retake_resp.status_code == 302
    client.get('/auth/logout')

    # 7. Teacher views teacher dashboard, proctoring report, and resets submission so student can retake
    client.post('/auth/login', data={'login_input': 'test_teacher', 'password': 'pass123'})
    teacher_dash = client.get('/teacher/dashboard')
    assert teacher_dash.status_code == 200
    assert 'Bảng Điều Khiển Giáo Viên'.encode('utf-8') in teacher_dash.data
    rep_resp = client.get(f'/submissions/{sub.id}/proctoring-report')
    assert rep_resp.status_code == 200
    assert b'SPLIT_SCREEN_RESIZE' in rep_resp.data
    assert b'DEVTOOLS_ATTEMPT' in rep_resp.data

    reset_resp = client.post(f'/submissions/{sub.id}/reset', follow_redirects=True)
    assert reset_resp.status_code == 200
    assert ExamSubmission.query.filter_by(exam_id=exam.id).count() == 0


def test_cyber_arena_and_weekly_leaderboard(client):
    # Login as student
    client.post('/auth/login', data={'login_input': 'test_student', 'password': 'pass123'})

    # 1. Access Cyber Arena & Weekly Leaderboard (/arena) -> Pre-Match Lobby shown first, questions hidden until Bắt Đầu
    arena_resp = client.get('/arena')
    assert arena_resp.status_code == 200
    arena_html = arena_resp.data.decode('utf-8')
    assert 'Đấu Trường Tin Học 11' in arena_html
    assert 'Bảng Xếp Hạng Tuần' in arena_html
    assert 'BẮT ĐẦU THI ĐẤU NGAY' in arena_html
    assert 'Hiệp Sĩ Diệt Boss' in arena_html
    assert 'Bắn Quái Vũ Trụ' in arena_html
    assert 'poster_boss_rpg.png' in arena_html
    assert 'poster_space_shooter.png' in arena_html
    assert 'map_platformer_world.png' in arena_html
    assert 'map_air_battlefield.png' in arena_html
    assert 'sprite_plat_mario.png' in arena_html
    assert 'sheet_hero_yasuo.png' in arena_html
    assert 'sheet_hero_lauriel.png' in arena_html
    assert 'part_head_yasuo.png' in arena_html
    assert 'part_thigh_yasuo.png' in arena_html
    assert 'part_shin_boot_yasuo.png' in arena_html
    assert 'triggerPlatformerDash' in arena_html
    assert 'prop_knowledge_gate.png' in arena_html
    assert 'sprite_boss_dreadnought.png' in arena_html
    assert 'Kaelen — Phong Kiếm Sư' in arena_html
    assert 'Seraphina — Quang Minh Thiên Sứ' in arena_html
    assert 'moba-skill-cd-overlay' in arena_html
    assert 'vfx_tornado_cyclone.png' in arena_html
    assert 'vfx_divine_sword_drop.png' in arena_html
    assert 'weapon_yasuo_katana.png' in arena_html
    assert 'sheet_boss_caesar.png' in arena_html
    assert 'sprite_jet_falcon.png' in arena_html
    assert 'sprite_wingman_plane.png' in arena_html
    assert 'arena-shop-modal' in arena_html
    assert 'arena-compact-quiz-dock' in arena_html
    assert 'id="arena-hud-bar" class="arena-hud-bar hidden"' in arena_html
    assert 'id="stage-panel-boss_rpg" role="tabpanel" hidden' in arena_html
    assert 'id="stage-panel-space_shooter" role="tabpanel" hidden' in arena_html

    # 2. Submit a high-score fast-time Boss RPG session -> verify Top 1 ranking by (Highest Score, Shortest Time)
    sub_resp = client.post('/api/arena/submit', json={
        'game_mode': 'boss_rpg',
        'topic_code': 'F',
        'score': 1350,
        'correct_count': 10,
        'total_count': 10,
        'max_combo': 5,
        'duration_sec': 25
    })
    assert sub_resp.status_code == 200
    sub_json = sub_resp.get_json()
    assert sub_json['success'] is True
    assert sub_json['new_rank'] == 1
    lb = sub_json['leaderboard']
    assert len(lb) >= 6
    # Verify leaderboard is sorted from Top 1 downward by (-best_score, best_duration_sec)
    for i in range(len(lb) - 1):
        curr_key = (-lb[i]['best_score'], lb[i]['best_duration_sec'])
        next_key = (-lb[i + 1]['best_score'], lb[i + 1]['best_duration_sec'])
        assert curr_key <= next_key

    # 3. Verify Practice Hub generator flow: hidden before clicking Sinh Đề, visible with countdown timer when generated=1
    p_init = client.get('/practice').data.decode('utf-8')
    assert 'Thiết Lập Đề Ôn Luyện Ngẫu Nhiên' in p_init
    assert 'id="practice-exam-workspace" class="flex flex-col gap-6 hidden"' in p_init

    p_gen = client.get('/practice?generated=1&topic=F&duration=30').data.decode('utf-8')
    assert 'id="practice-exam-workspace" class="flex flex-col gap-6 "' in p_gen
    assert '30:00' in p_gen
    assert 'Tự học • Không giám sát' in p_gen



