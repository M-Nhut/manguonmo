from app import create_app, db
from app.models import User, Classroom, Course, Lesson, Exam, Question

app = create_app()

def seed_database():
    with app.app_context():
        # Drop all & recreate for fresh clean setup
        db.create_all()
        
        # 1. Check if admin exists
        if User.query.filter_by(username='admin').first():
            print("Database đã có dữ liệu khởi tạo.")
            return

        print("Đang khởi tạo tài khoản và dữ liệu mẫu...")

        # 2. Tạo Người Dùng
        admin = User(
            username='admin',
            email='admin@tin11.edu.vn',
            full_name='Quản Trị Viên Hệ Thống',
            role='admin'
        )
        admin.set_password('admin123')

        teacher = User(
            username='gv.huong',
            email='gv.huong@tin11.edu.vn',
            full_name='Cô Nguyễn Thị Hương',
            role='teacher'
        )
        teacher.set_password('teacher123')

        student = User(
            username='hs.nam',
            email='hs.nam@tin11.edu.vn',
            full_name='Trần Văn Nam',
            role='student'
        )
        student.set_password('student123')

        db.session.add_all([admin, teacher, student])
        db.session.commit()

        # 3. Tạo Lớp học mẫu
        classroom = Classroom(
            name='11A1 - Tin học ứng dụng',
            code='TIN11-A1',
            description='Lớp học Tin học 11 (Định hướng Tin học ứng dụng) - Năm học 2026',
            teacher_id=teacher.id
        )
        # Thêm học sinh Nam vào lớp
        classroom.students.append(student)
        db.session.add(classroom)
        db.session.commit()

        # 4. Tạo Khóa học mẫu thuộc lớp 11A1
        course = Course(
            title='Chủ đề 4. Giới thiệu các hệ cơ sở dữ liệu (Lớp 11A1)',
            description='Lớp học chuyên đề Cơ sở dữ liệu quan hệ, khóa chính, khóa ngoại và ngôn ngữ truy vấn SQL.',
            classroom_id=classroom.id,
            teacher_id=teacher.id
        )
        db.session.add(course)
        db.session.commit()

        # 5. Tạo Bài học mẫu (sẵn sàng để giáo viên tải thêm PPT/DOCX/PDF vào)
        lesson1 = Lesson(
            course_id=course.id,
            title='Bài 14. SQL – Ngôn ngữ truy vấn có cấu trúc',
            content='# I. Trọng tâm kiến thức\n1. Khái niệm ngôn ngữ truy vấn có cấu trúc SQL (DDL, DML, DCL).\n2. Cú pháp câu lệnh truy vấn cơ bản: SELECT <cột> FROM <bảng> WHERE <điều kiện> ORDER BY <cột>.\n# II. Nội dung thực hành\n- Kết nối dữ liệu giữa các bảng bằng mệnh đề INNER JOIN ... ON.',
            order_index=14
        )
        db.session.add(lesson1)

        # 6. Tạo Đề kiểm tra mẫu với cơ chế chống gian lận
        exam = Exam(
            classroom_id=classroom.id,
            teacher_id=teacher.id,
            title='Kiểm tra 15 phút: Cấu trúc cơ bản HTML & Web',
            description='Đề thi trắc nghiệm khách quan gồm 3 câu hỏi mẫu. Học sinh lưu ý: Không chuyển tab hoặc rời toàn màn hình trong suốt thời gian làm bài!',
            duration_minutes=15,
            max_violations=3,
            enable_fullscreen=True,
            enable_tab_lock=True,
            is_published=True
        )
        db.session.add(exam)
        db.session.commit()

        # 7. Thêm các câu hỏi mẫu
        q1 = Question(
            exam_id=exam.id,
            content='Thẻ HTML nào sau đây được sử dụng để chèn hình ảnh vào trang web?',
            option_a='<img>',
            option_b='<image>',
            option_c='<picture>',
            option_d='<src>',
            correct_option='A',
            points=3.5
        )
        q2 = Question(
            exam_id=exam.id,
            content='Thuộc tính nào trong CSS được dùng để thay đổi màu chữ của một phần tử?',
            option_a='text-color',
            option_b='color',
            option_c='font-color',
            option_d='text-style',
            correct_option='B',
            points=3.5
        )
        q3 = Question(
            exam_id=exam.id,
            content='Thẻ HTML nào sau đây dùng để tạo liên kết (hyperlink) sang một trang web khác?',
            option_a='<link>',
            option_b='<a>',
            option_c='<href>',
            option_d='<nav>',
            correct_option='B',
            points=3.0
        )
        db.session.add_all([q1, q2, q3])
        db.session.commit()

        print("Khởi tạo dữ liệu thành công!")
        print("Tài khoản mẫu:")
        print("  - Admin:    admin / admin123")
        print("  - Teacher:  gv.huong / teacher123")
        print("  - Student:  hs.nam / student123")
        print("  - Lớp mẫu:  11A1 - Tin học ứng dụng (Mã: TIN11-A1)")

if __name__ == '__main__':
    seed_database()
