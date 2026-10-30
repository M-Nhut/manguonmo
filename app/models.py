from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Association table for Classroom <-> Student
classroom_students = db.Table(
    'classroom_students',
    db.Column('classroom_id', db.Integer, db.ForeignKey('classrooms.id'), primary_key=True),
    db.Column('student_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('joined_at', db.DateTime, default=datetime.utcnow)
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='student', nullable=False)  # 'admin', 'teacher', 'student'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    classrooms_taught = db.relationship('Classroom', backref='teacher', lazy='dynamic', foreign_keys='Classroom.teacher_id')
    enrolled_classes = db.relationship('Classroom', secondary=classroom_students, backref=db.backref('students', lazy='dynamic'))
    submissions = db.relationship('ExamSubmission', backref='student', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_admin(self):
        return self.role == 'admin'
        
    @property
    def is_teacher(self):
        return self.role in ['teacher', 'admin']
        
    @property
    def is_student(self):
        return self.role == 'student'


class Classroom(db.Model):
    __tablename__ = 'classrooms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(16), unique=True, nullable=False)
    description = db.Column(db.Text, default='')
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    courses = db.relationship('Course', backref='classroom', lazy='dynamic', cascade='all, delete-orphan')
    exams = db.relationship('Exam', backref='classroom', lazy='dynamic', cascade='all, delete-orphan')


class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, default='')
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    lessons = db.relationship('Lesson', backref='course', lazy='dynamic', cascade='all, delete-orphan')


class Lesson(db.Model):
    __tablename__ = 'lessons'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, default='')
    order_index = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    materials = db.relationship('Material', backref='lesson', lazy='dynamic', cascade='all, delete-orphan')


class Material(db.Model):
    __tablename__ = 'materials'
    
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)  # 'pdf', 'docx', 'pptx'
    file_name = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, default=0)  # bytes
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class Exam(db.Model):
    __tablename__ = 'exams'
    
    id = db.Column(db.Integer, primary_key=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, default='')
    duration_minutes = db.Column(db.Integer, default=15, nullable=False)
    max_violations = db.Column(db.Integer, default=3, nullable=False)
    enable_fullscreen = db.Column(db.Boolean, default=True)
    enable_tab_lock = db.Column(db.Boolean, default=True)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    questions = db.relationship('Question', backref='exam', lazy='dynamic', cascade='all, delete-orphan')
    submissions = db.relationship('ExamSubmission', backref='exam', lazy='dynamic', cascade='all, delete-orphan')


class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)
    correct_option = db.Column(db.String(2), nullable=False)  # 'A', 'B', 'C', 'D'
    points = db.Column(db.Float, default=1.0)


class ExamSubmission(db.Model):
    __tablename__ = 'exam_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Float, default=0.0)
    total_points = db.Column(db.Float, default=0.0)
    violations_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(30), default='in_progress')  # 'in_progress', 'submitted', 'auto_submitted_violation'
    answers_json = db.Column(db.Text, default='{}')
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime, nullable=True)
    
    logs = db.relationship('ProctoringLog', backref='submission', lazy='dynamic', cascade='all, delete-orphan')


class ProctoringLog(db.Model):
    __tablename__ = 'proctoring_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('exam_submissions.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # TAB_SWITCH, WINDOW_BLUR, EXIT_FULLSCREEN, DEVTOOLS_ATTEMPT, AUTO_SUBMIT
    details = db.Column(db.Text, default='')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
