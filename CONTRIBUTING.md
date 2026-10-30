# Quy trình Đóng góp Mã nguồn mở (Contributing Guidelines)

Dự án **E-Learning Tin học 11 (Ứng dụng)** được phát triển theo mô hình mã nguồn mở. Chúng tôi hoan nghênh mọi đóng góp từ cộng đồng và các thành viên!

## 1. Quy trình làm việc với Git & GitHub

1. **Fork** repository về tài khoản GitHub của bạn.
2. Tạo branch mới cho tính năng hoặc sửa lỗi:
   ```bash
   git checkout -b feature/ten-tinh-nang
   # hoặc
   git checkout -b fix/ten-loi
   ```
3. Tuân thủ **Conventional Commits**:
   - `feat: thêm chức năng nộp bài kiểm tra tự động`
   - `fix: sửa lỗi mất fullscreen khi ấn phím Esc`
   - `docs: cập nhật hướng dẫn cài đặt Docker`
   - `style: tinh chỉnh shadow claymorphism cho nút bấm`
4. Viết code sạch sẽ, tuân thủ PEP 8 (Python) và chuẩn ES6+ (JavaScript).
5. Tạo **Pull Request (PR)** đến nhánh `main` của repository gốc kèm mô tả chi tiết các thay đổi.

## 2. Tiêu chuẩn Mã nguồn

- **Backend (Python/Flask):** Code có chú thích rõ ràng, xử lý ngoại lệ (try/except), kiểm tra phân quyền người dùng (Role-Based Access Control).
- **Frontend (Claymorphism & Motion):** Sử dụng các biến CSS chung (`--clay-bg`, `--clay-shadow`, v.v.), hiệu ứng chuyển động mượt mà với spring easing, hỗ trợ responsive trên màn hình laptop và tablet.
- **Bảo mật:** Không commit mật khẩu, secret key, hoặc thông tin nhạy cảm vào mã nguồn.

## 3. Báo cáo sự cố (Issues)

Vui lòng sử dụng tính năng **Issues** trên GitHub để:
- Báo lỗi (Bug report) kèm ảnh chụp màn hình và các bước tái hiện.
- Đề xuất tính năng mới (Feature request) giải thích rõ lợi ích cho học sinh hoặc giáo viên.
