# Design System Master File — Tin Học 11 (Ứng Dụng) E-Learning LMS

> **Version 2.0 — Aero-Academic Studio**
> **Applied Skills:** `ui-ux-pro-max`, `design-system`, `ui-styling`, `banner-design`, `modern-web-guidance`
> **Target Product:** Hệ thống Quản lý Học tập & Thi trực tuyến Chống gian lận môn Tin học 11 (GDPT 2018)

---

## 1. Visual Direction & Architecture (`Aero-Academic Studio`)

| Thuộc tính | Quy chuẩn thiết kế |
| :--- | :--- |
| **Aesthetic** | **Aero-Academic Studio** — Bề mặt kính mờ nhẹ (`rgba(255,255,255,0.88)` + `backdrop-filter: blur(14px)`) cho thanh điều hướng & lớp phủ, kết hợp thẻ nội dung phẳng sắc nét (`1px solid #E2E8F0`), đổ bóng phân tầng tinh tế, không clay bevel. |
| **Token Architecture** | **3-Layer Tokens** (`tokens.json` → `tokens.css`): Primitive → Semantic → Component. Zero raw hex hardcoded in UI components where tokens apply. |
| **CSS Cascade Strategy** | Zero-specificity `:where(...)` component defaults + Tailwind Play CDN utilities so utility classes override cleanly without specificity collisions. |
| **Banner Art Direction** | **3-Zone Visual Hierarchy** (`Eyebrow / Headline + Subtext / Primary CTA or Metric Strip`) với **Safe Zones** 70–80%, gradient scrim `>= 4.5:1` trên ảnh nền, tối đa 2 họ font. |
| **Iconography** | **100% Vector SVG Icons (Lucide style)** — Stroke `2px`, `aria-hidden="true"` khi đi kèm nhãn chữ, `aria-label` bắt buộc khi là nút chỉ có icon. |

---

## 2. Color Palette & WCAG 2.1 AA Verified Contrast

| Vai trò | Mã Hex / Giá trị | Biến Semantic | Độ tương phản (Verified) |
| :--- | :--- | :--- | :--- |
| **Canvas Background** | `#F4F7FB` | `--color-bg-canvas` | Nền dịu mắt |
| **Card Surface** | `#FFFFFF` | `--color-bg-surface` | Bề mặt chính |
| **Text Title** | `#0F172A` | `--color-text-title` | **17.85:1** trên trắng (AAA) |
| **Text Body** | `#334155` | `--color-text-body` | **10.35:1** trên trắng (AAA) |
| **Text Muted** | `#475569` | `--color-text-muted` | **7.58:1** trên trắng / **6.92:1** trên subtle (AAA) |
| **Primary (Cobalt)** | `#0B4FD8` | `--color-primary` | **6.72:1** với chữ trắng (AA+) |
| **Primary Hover** | `#093EB0` | `--color-primary-hover` | **9.02:1** với chữ trắng (AAA) |
| **Secondary (Indigo)** | `#4338CA` | `--color-secondary` | **7.07:1** trên `#EEF2FF` (AAA) — Dùng cho AI & Huy hiệu |
| **Accent (Sky)** | `#0369A1` | `--color-accent` | **5.57:1** trên `#F0F9FF` (AA) |
| **Success** | `#047857` | `--color-success` | **5.21:1** trên `#ECFDF5` (AA) |
| **Warning** | `#92400E` | `--color-warning` | **6.84:1** trên `#FFFBEB` (AA) |
| **Danger / Proctoring** | `#BE123C` | `--color-danger` | **5.72:1** trên `#FFF1F2` (AA) |
| **Control Border** | `#64748B` | `--color-border-control` | **4.76:1** trên trắng (Pass 3:1 UI & 4.5:1 placeholder) |

---

## 3. Typography (Vietnamese-First Academic Scale)

- **Display & Headings (`--font-display`)**: `Be Vietnam Pro` (`600`, `700`, `800`) — Tối ưu dấu thanh tiếng Việt, `letter-spacing: -0.025em`, `text-wrap: balance`.
- **Body & UI (`--font-sans`)**: `Inter` (`400`, `500`, `600`, `700`) — `15px–16px` base, `line-height: 1.65`.
- **Monospace (`--font-mono`)**: `JetBrains Mono` (`500`, `600`, `700`) + `font-variant-numeric: tabular-nums` cho mã lớp, mã PIN, bộ đếm phòng thi, điểm số.

---

## 4. Accessibility & Modern Web Standards

- **Landmarks & Skip Link**: Mọi trang đều có skip link `#main-content`, `<header>`, `<nav aria-label="...">`, `<main id="main-content" tabindex="-1">`, `<footer>`.
- **Single Navigation Hierarchy**: Sidebar (`264px`) đảm nhận điều hướng toàn cục; Topbar hiển thị ngữ cảnh trang, huy hiệu vai trò và thao tác nhanh (không lặp lại menu sidebar).
- **Native `<dialog>` Modals**: Mọi modal CRUD sử dụng `<dialog>` + `showModal()`, `closedby="any"` + fallback click-outside, `overscroll-behavior: contain`, và `::backdrop` blur.
- **Forms & Radios**: 100% input có `<label for="...">` hoặc `aria-label`, checkbox/radio phòng thi có vùng chạm `>= 44×44px`, `<fieldset>`/`<legend>` cho từng câu hỏi.
- **Motion**: Tôn trọng `@media (prefers-reduced-motion: reduce)` trên toàn hệ thống.
