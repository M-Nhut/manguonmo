# Design System Master File — Tin Học 11 (Ứng Dụng) E-Learning LMS

> **Version 3.0 — Aero-Teal Swiss Academic Studio (UI/UX Pro Max)**
> **Applied Skills:** `ui-ux-pro-max`, `modern-web-guidance`
> **Target Product:** Hệ thống Quản lý Học tập, Đấu Trường Kiến Thức & Khảo thí Trực tuyến môn Tin học 11 (GDPT 2018)

---

## 1. Visual Direction & Architecture (`Aero-Teal Swiss Academic Studio`)

| Thuộc tính | Quy chuẩn thiết kế |
| :--- | :--- |
| **Aesthetic** | **Aero-Teal Swiss Academic Studio** — Nền sứ thoáng sáng (`#F3F8F9`), kết hợp bề mặt kính mờ nhẹ (`backdrop-filter: blur(18px)`) ở Sidebar & Topbar, dải màu thương hiệu Education Teal (`#0D9488`) + Academic Cobalt (`#0B4FD8`), nhấn Course Amber (`#D97706`), cùng thẻ Poster sắc nét có đổ bóng mềm phân tầng. |
| **Information Architecture** | **Progressive Disclosure (Tiết lộ tăng dần)** — Ngoài cùng hiển thị gọn 7 **Chủ đề (Topic Poster Cards)** trọng tâm; bấm vào từng Chủ đề mới mở trọn bộ **Bài học dạng thẻ Poster 16:9** đầy đủ tóm tắt, video & tài liệu đính kèm. |
| **Scroll & Micro-Motion** | **GSAP 3.12 + ScrollTrigger + CSS Fallback** — Thanh tiến độ cuộn toàn cục (`#global-scroll-progress`), Parallax chiều sâu trên Hero Orbs (`[data-parallax]`), hiệu ứng xuất hiện so le khi lướt (`[data-reveal]`, `[data-reveal-group]`), nghiêng 3D + vệt sáng theo con trỏ (`.pro-card-tilt`), ánh lướt Poster (`.poster-shine`), đếm số KPI (`[data-countup]`) và nút quay lại đầu trang (`#back-to-top-btn`). Tôn trọng `@media (prefers-reduced-motion: reduce)`. |
| **Typography** | `Be Vietnam Pro` (Display/Headings), `Inter` (Body/UI 15px–16px, `line-height: 1.65`), `JetBrains Mono` (Tabular numbers, SQL, mã PIN, số bài). |
| **Iconography & Accessibility** | 100% Vector SVG sắc nét, tương phản WCAG 2.1 AA+ (`>= 4.5:1`), skip link `#main-content`, focus ring rõ ràng (`#0D9488`), native `<dialog>` với `overscroll-behavior: contain`. |

---

## 2. Core Semantic Palette (v3.0)

| Vai trò | Mã Hex | Biến CSS |
| :--- | :--- | :--- |
| **Canvas Background** | `#F3F8F9` | `--color-bg-canvas` |
| **Card Surface** | `#FFFFFF` | `--color-bg-surface` |
| **Education Teal (Primary Accent)** | `#0D9488` / `#0F766E` | `--color-teal` / `--color-teal-dark` |
| **Academic Cobalt (Primary CTA)** | `#0B4FD8` | `--color-primary` |
| **Course Amber (Highlights)** | `#D97706` | `--color-accent` |
| **Grade Emerald (Success)** | `#047857` | `--color-success` |
| **Proctoring Rose (Danger)** | `#BE123C` | `--color-danger` |
| **Title Ink** | `#0F172A` | `--color-text-title` |
| **Body Ink** | `#334155` | `--color-text-body` |
