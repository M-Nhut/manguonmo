# Arena Page Overrides (Đấu Trường Tin Học 11 & BXH Tuần)

> **PROJECT:** Tin Hoc 11 E-Learning
> **Page:** `/arena` (`app/templates/courses/arena.html`)
> **Style Direction:** v3.0 Hybrid Architecture — Aero-Teal Swiss Academic Studio Outer Shell + Dark Esports Active Gameplay Console

---

## Page-Specific Rules

### 1. Hybrid Layout & Stage Architecture
- **Outer Shell (`Aero-Teal Swiss Academic Studio v3.0`)**:
  - **Hero Header (`.pro-hero-banner`)**: Light gradient (`#FFFFFF -> #F0FDFA -> #EFF6FF`), `[data-hero-stagger]`, ambient `.pro-mesh-orb[data-parallax]`, `.animate-live-dot` seasonal badge, `.text-gradient-brand` heading (`#arena-hero-title`), light Gold/XP wallet pills, light Player Rank summary card, and Weekly Rotating Topic Bar (`.topic-pill-switcher` + `.clay-select`).
  - **4 Mode Selector Cards (`.esports-mode-grid` / `.esports-mode-card.pro-card-tilt`)**: Crisp `#FFFFFF` cards with `.poster-shine` 16:9 thumbnails and `#0D9488` active highlight for `boss_rpg` (`Thánh Địa Vượt Ải 2D`), `space_shooter` (`Chiến Cơ 1945`), `blitz` (`Đấu Trường Tia Chớp 60s`), and `sql_puzzle` (`Thợ Săn Lệnh SQL`).
  - **2-Column Workspace (`.arena-main-grid`)**: Responsive `1fr` on mobile/tablet (`min-width: 0` overflow guards), `minmax(0, 1.56fr) minmax(308px, 1fr)` on desktop (`>= 1024px`) inside `.app-content-body`.
  - **Pre-Match Lobby (`#arena-prematch-lobby`), Post-Match Result Screen (`#arena-result-screen`), & Shop Modal (`#arena-shop-modal`)**: Cohesive `#FFFFFF` / `#F8FAFC` light studio surfaces (`#0F172A` titles, `#334155`/`#475569` body), keeping `#shop-anim-preview-canvas` and sprite/VFX thumbnails in framed `#0F172A` studio viewports for high contrast.
  - **Weekly Leaderboard & Top-3 Podium (`.arena-lb-card`)**: Light `#FFFFFF` card with `#2 / #1 / #3` podium hierarchy (`.podium-col.rank-1/2/3`), `.arena-lb-list`, `.arena-lb-row.is-me` teal-cobalt highlight, and live DOM refresh after `/api/arena/submit`.
- **Active In-Game Console (`#arena-stage-root.is-in-match` / `.is-expanded`)**:
  - Switches `#arena-stage-root` to `#0B1120` / `#070B14` dark esports console when a match starts (`startArenaMatchNow()`), reveals `#arena-hud-bar` (`display: none !important` while `.hidden` pre-match), opens Theater Mode (`[F]` toggle via `toggleTheaterExpand()`), and preserves all 4 gameplay panels (`#stage-panel-boss_rpg`, `#stage-panel-space_shooter`, `#stage-panel-blitz`, `#stage-panel-sql_puzzle`), canvases, `.moba-skill-bar`, `.arena-compact-quiz-dock`, `.arena-touch-dpad` (`< 900px`), and Web Audio SFX (`#btn-sfx-toggle`).

### 2. Color & Contrast Tokens
- **Outer Shell**: Canvas `#F3F8F9`, Cards `#FFFFFF`, Teal `#0D9488`/`#0F766E`, Cobalt `#0B4FD8`, Amber `#D97706`/`#B45309`, Title Ink `#0F172A`, Body Ink `#334155`.
- **Podium Accents**:
  - `#1 Quán Quân`: Gold border `#F59E0B`, warm cream surface `#FFFBEB`, text `#78350F` / `#92400E`.
  - `#2 Á Quân`: Silver border `#94A3B8`, surface `#F8FAFC`, text `#1E293B`.
  - `#3 Hạng Ba`: Bronze border `#D97706`, surface `#FFF7ED`, text `#7C2D12` / `#9A3412`.
- **Active Gameplay Stage**: Deep slate/navy (`#060B16`, `#0B1120`, `#0F172A`) with high-contrast `#FFFFFF` / `#F8FAFC` quiz text and `#38BDF8` / `#FACC15` / `#34D399` arcade accents.

### 3. Motion, Audio & Accessibility
- **Web Audio API Synthesizer**: Built-in pure Web Audio SFX (`ArenaSFX`) with Mute/Unmute toggle (`#btn-sfx-toggle`).
- **Scroll & Hover Motion**: `[data-hero-stagger]`, `[data-parallax]`, `[data-reveal-group]`/`[data-reveal]`, `.pro-card-tilt`, `.poster-shine`, and `.animate-live-dot`.
- **Reduced Motion**: Custom transitions, hover lifts/zooms, and `@keyframes quizPulseAlert` are disabled under `@media (prefers-reduced-motion: reduce)`.
- **Scroll Containment**: `#arena-shop-modal` (`.arena-shop-card`), `.arena-theater-backdrop`, `.esports-stage-card.is-expanded`, and `.arena-lb-list` enforce `overscroll-behavior: contain`.
