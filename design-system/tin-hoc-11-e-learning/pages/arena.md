# Arena Page Overrides (Đấu Trường Tin Học 11 & BXH Tuần)

> **PROJECT:** Tin Hoc 11 E-Learning
> **Page:** `/arena` (`app/templates/courses/arena.html`)
> **Style Direction:** Vibrant & Block-based + Luminous EdTech Cyber Arena

---

## Page-Specific Rules

### 1. Layout & Stage Architecture
- **12-Column Split**:
  - **Left 7 Columns**: Interactive Game Stage (`.arena-stage-card`) with 3 mode tabs (`Tốc Chiến 60s`, `Thợ Săn SQL`, `Ghép Thẻ 3D`), dark HUD bar (`.arena-hud-bar`), tactile answer cards (`.arena-option-btn`), SQL query terminal (`.sql-terminal-box`), and 4×3 3D Memory Matrix (`.memory-card-3d`).
  - **Right 5 Columns**: Weekly Leaderboard & Top 3 Podium (`.podium-rank-1`, `.podium-rank-2`, `.podium-rank-3`) + live standings (`#leaderboard-list-body`) + sticky personal rank motivation bar.

### 2. Color & Contrast Tokens
- **Arena Hero & HUD**: Deep Cyber Navy (`#070E24` → `#0E235C` → `#24195E`) with `#FFFFFF` text (`> 12:1` contrast) and `#FDE68A` / `#7DD3FC` accents.
- **Podium Accents**:
  - `#1 Quán Quân`: Gold border `#F59E0B`, warm cream surface `#FFFBEB`, text `#92400E` (`6.84:1`).
  - `#2 Á Quân`: Silver border `#94A3B8`, surface `#F8FAFC`, text `#1E293B`.
  - `#3 Hạng Ba`: Bronze border `#D97706`, surface `#FFF7ED`, text `#9A3412`.

### 3. Motion, Audio & Accessibility
- **Web Audio API Synthesizer**: Built-in triangle/sine chiptune chord generator with explicit Mute/Unmute toggle (`#sound-toggle-btn`, `aria-pressed`).
- **Contextual Screen-Reader Live Region**: Single atomic status region (`#arena-sr-status` with `role="status" aria-atomic="true"`) announcing completed match score, earned XP, and updated weekly rank.
- **Reduced Motion**: Canvas confetti burst and 3D card transitions automatically respect `prefers-reduced-motion: reduce`.
