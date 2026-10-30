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
