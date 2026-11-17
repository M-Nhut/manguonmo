/**
 * AntiCheatingEngine v2.0 - Hệ thống Giám sát Phòng thi Trực tuyến Đa tầng
 * 7 Cảm biến bảo mật:
 * 1. TAB_SWITCH (Page Visibility API)
 * 2. WINDOW_BLUR (Alt+Tab / Cửa sổ nổi bên ngoài)
 * 3. EXIT_FULLSCREEN + 10s Lockout Shield (Khóa mờ đề thi khi thoát toàn màn hình)
 * 4. SPLIT_SCREEN_RESIZE (Phát hiện chia đôi màn hình / thu nhỏ cửa sổ)
 * 5. CLIPBOARD_COPY_PASTE (Chặn Copy, Cut, Paste, Kéo thả, PrintScreen)
 * 6. DEVTOOLS_ATTEMPT (Chặn F12, Ctrl+Shift+I/J/C, Ctrl+U)
 * 7. REALTIME_AUTOSAVE & SERVER_TIMER_SYNC (Tự động lưu đáp án & đồng bộ giờ máy chủ)
 */

class AntiCheatingEngine {
    constructor(config) {
        this.submissionId = config.submissionId;
        this.remainingSeconds = config.durationSeconds || 900;
        this.maxViolations = config.maxViolations || 3;
        this.violationsCount = config.initialViolations || 0;
        this.enableFullscreen = Boolean(config.enableFullscreen);
        this.enableTabLock = Boolean(config.enableTabLock);
        this.violationEndpoint = config.violationEndpoint;
        this.autosaveEndpoint = config.autosaveEndpoint;
        this.form = document.getElementById(config.formId);

        this.timerInterval = null;
        this.shieldCountdownInterval = null;
        this.autosaveTimeout = null;
        this.isSubmitting = false;
        this.hasEnteredFullscreen = false;
        this.lastViolationTime = 0;
    }

    init() {
        this.startTimer();
        this.setupAnswerTrackingAndAutosave();
        this.setupContextAndClipboardLocks();

        if (this.enableFullscreen) {
            this.setupFullscreenShield();
        }

        if (this.enableTabLock) {
            this.setupVisibilityAndFocusLocks();
            this.setupSplitScreenDetector();
        }

        if (this.form) {
            this.form.addEventListener('submit', () => {
                this.isSubmitting = true;
                this.clearIntervals();
            });
        }
    }

    clearIntervals() {
        if (this.timerInterval) clearInterval(this.timerInterval);
        if (this.shieldCountdownInterval) clearInterval(this.shieldCountdownInterval);
    }

    startTimer() {
        const timerEl = document.getElementById('examTimer');
        const renderTime = () => {
            if (!timerEl) return;
            const mins = Math.floor(this.remainingSeconds / 60);
            const secs = this.remainingSeconds % 60;
            timerEl.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
            if (this.remainingSeconds <= 60) {
                timerEl.classList.remove('text-[#004FB2]');
                timerEl.classList.add('text-rose-600');
            }
        };

        renderTime();
        this.timerInterval = setInterval(() => {
            if (this.isSubmitting) return;
            this.remainingSeconds -= 1;
            if (this.remainingSeconds <= 0) {
                this.remainingSeconds = 0;
                renderTime();
                this.clearIntervals();
                this.showAlert('Đã hết thời gian làm bài! Hệ thống đang tự động thu bài của bạn...');
                this.submitExamForm();
                return;
            }
            renderTime();
        }, 1000);
    }

    collectCurrentAnswers() {
        const answers = {};
        const cards = document.querySelectorAll('.question-card-item');
        let answeredCount = 0;

        cards.forEach((card) => {
            const qid = card.getAttribute('data-qid');
            const qtype = card.getAttribute('data-qtype');
            const pill = document.getElementById(`q-pill-${qid}`);

            if (qtype === 'true_false') {
                const parts = ['a', 'b', 'c', 'd'].map((sub) => {
                    const checked = card.querySelector(`input[name="question_${qid}_${sub}"]:checked`);
                    return checked ? checked.value : '';
                });
                const joined = parts.join(',');
                if (parts.some((v) => v !== '')) {
                    answers[qid] = joined;
                }
                const isComplete = parts.every((v) => v !== '');
                if (isComplete) answeredCount += 1;
                if (pill) {
                    pill.classList.toggle('answered', parts.some((v) => v !== ''));
                }
            } else {
                const checked = card.querySelector(`input[name="question_${qid}"]:checked`);
                if (checked) {
                    answers[qid] = checked.value;
                    answeredCount += 1;
                }
                if (pill) {
                    pill.classList.toggle('answered', Boolean(checked));
                }
            }
        });

        const countEl = document.getElementById('answeredCountText');
        if (countEl) countEl.textContent = String(answeredCount);
        return answers;
    }

    setupAnswerTrackingAndAutosave() {
        // Initial count calculation
        this.collectCurrentAnswers();

        const inputs = document.querySelectorAll('.exam-answer-input');
        inputs.forEach((input) => {
            input.addEventListener('change', () => {
                const answers = this.collectCurrentAnswers();
                this.scheduleAutosave(answers);
            });
        });
    }

    scheduleAutosave(answers) {
        if (!this.autosaveEndpoint || this.isSubmitting) return;
        const statusEl = document.getElementById('autosaveStatus');
        if (statusEl) {
            statusEl.textContent = 'Đang lưu đáp án...';
        }

        if (this.autosaveTimeout) clearTimeout(this.autosaveTimeout);
        this.autosaveTimeout = setTimeout(async () => {
            try {
                const resp = await fetch(this.autosaveEndpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ answers })
                });
                const data = await resp.json();
                if (data.saved && statusEl) {
                    const now = new Date();
                    const timeStr = now.toTimeString().split(' ')[0];
                    statusEl.textContent = `Đã lưu tự động (${timeStr})`;
                }
            } catch (err) {
                console.warn('Autosave failed:', err);
            }
        }, 450);
    }

    setupFullscreenShield() {
        const shield = document.getElementById('fullscreenShield');
        const paper = document.getElementById('examPaperContent');
        const enterBtn = document.getElementById('enterFullscreenBtn');

        const isFullscreenActive = () => Boolean(
            document.fullscreenElement ||
            document.webkitFullscreenElement ||
            document.msFullscreenElement
        );

        const unlockPaper = () => {
            if (shield) shield.classList.add('hidden');
            if (paper) paper.classList.remove('exam-paper-blurred');
            if (this.shieldCountdownInterval) {
                clearInterval(this.shieldCountdownInterval);
                this.shieldCountdownInterval = null;
            }
        };

        const lockPaper = (isViolationExit) => {
            if (this.isSubmitting) return;
            if (shield) shield.classList.remove('hidden');
            if (paper) paper.classList.add('exam-paper-blurred');

            if (isViolationExit) {
                const titleEl = document.getElementById('shieldTitle');
                const msgEl = document.getElementById('shieldMessage');
                const boxEl = document.getElementById('shieldCountdownBox');
                const secEl = document.getElementById('shieldCountdownSec');

                if (titleEl) titleEl.textContent = 'Cảnh Báo: Bạn Đã Thoát Toàn Màn Hình!';
                if (msgEl) msgEl.textContent = 'Đề thi đã bị khóa tạm thời để chống gian lận. Hãy nhấn nút bên dưới để quay lại chế độ Toàn màn hình ngay lập tức.';
                if (boxEl) boxEl.classList.remove('hidden');

                let secsLeft = 10;
                if (secEl) secEl.textContent = String(secsLeft);
                if (this.shieldCountdownInterval) clearInterval(this.shieldCountdownInterval);
                this.shieldCountdownInterval = setInterval(() => {
                    if (this.isSubmitting || isFullscreenActive()) {
                        clearInterval(this.shieldCountdownInterval);
                        return;
                    }
                    secsLeft -= 1;
                    if (secEl) secEl.textContent = String(Math.max(0, secsLeft));
                    if (secsLeft <= 0) {
                        clearInterval(this.shieldCountdownInterval);
                        this.recordViolation(
                            'FULLSCREEN_TIMEOUT',
                            'Không quay lại chế độ Toàn màn hình sau 10 giây cảnh báo'
                        );
                    }
                }, 1000);
            }
        };

        if (enterBtn) {
            enterBtn.addEventListener('click', () => {
                const docEl = document.documentElement;
                const req = docEl.requestFullscreen || docEl.webkitRequestFullscreen || docEl.msRequestFullscreen;
                if (req) {
                    req.call(docEl).then(() => {
                        this.hasEnteredFullscreen = true;
                        unlockPaper();
                    }).catch(() => {
                        // Fallback for headless/test environments that block Fullscreen API
                        this.hasEnteredFullscreen = true;
                        unlockPaper();
                    });
                } else {
                    this.hasEnteredFullscreen = true;
                    unlockPaper();
                }
            });
        }

        document.addEventListener('fullscreenchange', () => {
            if (this.isSubmitting) return;
            if (isFullscreenActive()) {
                this.hasEnteredFullscreen = true;
                unlockPaper();
            } else if (this.hasEnteredFullscreen) {
                lockPaper(true);
                this.recordViolation(
                    'EXIT_FULLSCREEN',
                    'Thoát khỏi chế độ khóa toàn màn hình (Fullscreen) khi đang làm bài'
                );
            }
        });
    }

    setupVisibilityAndFocusLocks() {
        // Sensor 1: Tab Switch (Page Visibility API)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && !this.isSubmitting) {
                this.recordViolation(
                    'TAB_SWITCH',
                    'Rời khỏi tab bài thi hoặc ẩn trình duyệt sang ứng dụng khác'
                );
            }
        });

        // Sensor 2: Window Blur (Alt+Tab or floating window focus)
        window.addEventListener('blur', () => {
            if (!this.isSubmitting && !document.hidden) {
                this.recordViolation(
                    'WINDOW_BLUR',
                    'Mất tiêu điểm cửa sổ làm bài (Chuyển sang cửa sổ nổi hoặc ứng dụng khác)'
                );
            }
        });
    }

    setupSplitScreenDetector() {
        // Sensor 4: Split-Screen / Window Resize Detector
        window.addEventListener('resize', () => {
            if (this.isSubmitting || !this.hasEnteredFullscreen) return;
            const availW = window.screen.availWidth || window.innerWidth;
            const availH = window.screen.availHeight || window.innerHeight;
            if (window.innerWidth < availW * 0.78 || window.innerHeight < availH * 0.75) {
                this.recordViolation(
                    'SPLIT_SCREEN_RESIZE',
                    `Thu nhỏ hoặc chia đôi màn hình làm bài (${window.innerWidth}x${window.innerHeight})`
                );
            }
        });
    }

    setupContextAndClipboardLocks() {
        // Block right-click context menu
        document.addEventListener('contextmenu', (e) => e.preventDefault());

        // Sensor 5: Block Copy, Cut, Paste, Drag/Drop
        ['copy', 'cut', 'paste', 'dragstart', 'drop'].forEach((evtName) => {
            document.addEventListener(evtName, (e) => {
                e.preventDefault();
                if (!this.isSubmitting && (evtName === 'copy' || evtName === 'paste')) {
                    this.recordViolation(
                        'CLIPBOARD_COPY_PASTE',
                        `Thao tác ${evtName.toUpperCase()} nội dung trong phòng thi`
                    );
                }
            });
        });

        // Sensor 6: Block DevTools, View-Source, PrintScreen, Ctrl+P
        document.addEventListener('keydown', (e) => {
            if (this.isSubmitting) return;
            const key = (e.key || '').toUpperCase();
            const ctrlOrCmd = e.ctrlKey || e.metaKey;

            // DevTools shortcuts: F12, Ctrl+Shift+I/J/C, Ctrl+U
            if (
                e.key === 'F12' ||
                (ctrlOrCmd && e.shiftKey && ['I', 'J', 'C'].includes(key)) ||
                (ctrlOrCmd && key === 'U')
            ) {
                e.preventDefault();
                this.recordViolation(
                    'DEVTOOLS_ATTEMPT',
                    `Cố gắng mở công cụ kiểm tra mã nguồn (${e.key})`
                );
                return;
            }

            // Print / Save page shortcuts
            if (ctrlOrCmd && ['P', 'S'].includes(key)) {
                e.preventDefault();
                this.recordViolation(
                    'CLIPBOARD_COPY_PASTE',
                    `Cố gắng in hoặc lưu trang đề thi (Ctrl+${key})`
                );
            }

            if (e.key === 'PrintScreen') {
                e.preventDefault();
                this.recordViolation(
                    'CLIPBOARD_COPY_PASTE',
                    'Phát hiện phím chụp màn hình (PrintScreen)'
                );
            }
        });
    }

    async recordViolation(eventType, details) {
        if (this.isSubmitting) return;

        // Debounce rapid duplicate events within 1.5s (e.g. Alt+Tab firing both blur and visibilitychange)
        const now = Date.now();
        if (now - this.lastViolationTime < 1500) {
            return;
        }
        this.lastViolationTime = now;

        // Save current answers before reporting violation in case auto-submit triggers
        const currentAnswers = this.collectCurrentAnswers();
        if (this.autosaveEndpoint) {
            try {
                await fetch(this.autosaveEndpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ answers: currentAnswers })
                });
            } catch (_) {}
        }

        try {
            const response = await fetch(this.violationEndpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    event_type: eventType,
                    details: details
                })
            });

            const data = await response.json();
            if (data.violations_count !== undefined) {
                this.violationsCount = data.violations_count;
                const counterEl = document.getElementById('violationCounter');
                if (counterEl) {
                    counterEl.textContent = `${this.violationsCount} / ${this.maxViolations}`;
                }

                // Update Live Integrity Score
                const trustEl = document.getElementById('integrityScoreBadge');
                if (trustEl) {
                    const trustScore = Math.max(0, Math.round(100 - (this.violationsCount * 100 / this.maxViolations)));
                    trustEl.textContent = `${trustScore}%`;
                    trustEl.className = 'text-lg font-extrabold font-mono ' + (
                        trustScore >= 70 ? 'text-emerald-600' : (trustScore >= 40 ? 'text-amber-600' : 'text-rose-600')
                    );
                }
            }

            this.showAlert(`${data.message || 'Cảnh báo vi phạm quy chế thi!'} (${details})`);

            if (data.auto_submit) {
                this.isSubmitting = true;
                this.clearIntervals();
                this.showAlert('Bạn đã vượt quá giới hạn vi phạm! Hệ thống đang khóa và tự động thu bài thi...');
                setTimeout(() => this.submitExamForm(), 900);
            }
        } catch (err) {
            console.error('Proctoring log error:', err);
        }
    }

    showAlert(msg) {
        const box = document.getElementById('violationAlertBox');
        const text = document.getElementById('violationAlertText');
        if (box && text) {
            text.textContent = msg;
            box.classList.remove('hidden');
        }
    }

    submitExamForm() {
        this.isSubmitting = true;
        this.clearIntervals();
        if (this.form) {
            this.form.submit();
        }
    }
}
