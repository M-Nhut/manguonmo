/**
 * ANTI-CHEATING PROCTORING ENGINE
 * Hệ thống giám sát và chống gian lận kiểm tra trực tuyến
 */

class AntiCheatingEngine {
  constructor(config) {
    this.submissionId = config.submissionId;
    this.maxViolations = config.maxViolations || 3;
    this.enableFullscreen = config.enableFullscreen !== false;
    this.enableTabLock = config.enableTabLock !== false;
    this.durationMinutes = config.durationMinutes || 15;
    
    this.violationsCount = config.initialViolations || 0;
    this.isExamActive = false;
    this.isSubmitting = false;
    this.lastBlurTime = 0;
    
    this.initElements();
    this.bindEvents();
  }
  
  initElements() {
    this.examForm = document.getElementById('exam-form');
    this.warningModal = document.getElementById('cheating-modal');
    this.warningMessage = document.getElementById('cheating-warning-text');
    this.violationCounter = document.getElementById('violation-counter');
    this.timerDisplay = document.getElementById('exam-timer');
    this.fullscreenPrompt = document.getElementById('fullscreen-prompt-modal');
  }
  
  start() {
    this.isExamActive = true;
    this.startTimer();
    
    // Request Fullscreen if enabled
    if (this.enableFullscreen) {
      this.requestFullscreen();
    }
    
    this.setupLockdown();
  }
  
  startTimer() {
    let timeLeft = this.durationMinutes * 60;
    
    this.timerInterval = setInterval(() => {
      if (!this.isExamActive || this.isSubmitting) {
        clearInterval(this.timerInterval);
        return;
      }
      
      timeLeft--;
      const minutes = Math.floor(timeLeft / 60);
      const seconds = timeLeft % 60;
      
      if (this.timerDisplay) {
        this.timerDisplay.textContent = 
          `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
          
        if (timeLeft <= 60) {
          this.timerDisplay.style.color = 'var(--danger-clay)';
          this.timerDisplay.classList.add('animate-shake');
        }
      }
      
      if (timeLeft <= 0) {
        clearInterval(this.timerInterval);
        this.autoSubmit('Hết thời gian làm bài!');
      }
    }, 1000);
  }
  
  requestFullscreen() {
    const el = document.documentElement;
    if (el.requestFullscreen) {
      el.requestFullscreen().catch(err => {
        console.warn('Lỗi xin quyền Fullscreen:', err);
      });
    }
  }
  
  setupLockdown() {
    // 1. Chặn chuột phải (Context Menu)
    document.addEventListener('contextmenu', (e) => {
      if (this.isExamActive) {
        e.preventDefault();
        this.showToast('Vô hiệu hoá chuột phải trong phòng thi!', 'warning');
      }
    });
    
    // 2. Chặn phím tắt mở DevTools, Copy, Paste, Print
    document.addEventListener('keydown', (e) => {
      if (!this.isExamActive) return;
      
      // F12
      if (e.key === 'F12') {
        e.preventDefault();
        this.recordViolation('DEVTOOLS_ATTEMPT', 'Thử mở Developer Tools bằng phím F12');
        return;
      }
      
      // Ctrl+Shift+I, Cmd+Option+I, Ctrl+Shift+J, Ctrl+U (View Source)
      if ((e.ctrlKey || e.metaKey) && (e.shiftKey && (e.key === 'I' || e.key === 'i' || e.key === 'J' || e.key === 'j'))) {
        e.preventDefault();
        this.recordViolation('DEVTOOLS_ATTEMPT', 'Thử mở Developer Tools bằng tổ hợp phím tắt');
        return;
      }
      
      if ((e.ctrlKey || e.metaKey) && (e.key === 'u' || e.key === 'U')) {
        e.preventDefault();
        this.recordViolation('DEVTOOLS_ATTEMPT', 'Thử xem mã nguồn (View Source)');
        return;
      }
      
      // Chặn Copy, Paste
      if ((e.ctrlKey || e.metaKey) && ['c', 'v', 'x', 'a'].includes(e.key.toLowerCase())) {
        e.preventDefault();
        this.showToast('Thao tác Copy/Paste bị vô hiệu hoá!', 'warning');
      }
    });
    
    // 3. Giám sát chuyển Tab (Page Visibility API)
    if (this.enableTabLock) {
      document.addEventListener('visibilitychange', () => {
        if (!this.isExamActive || this.isSubmitting) return;
        
        if (document.hidden) {
          this.recordViolation('TAB_SWITCH', 'Học sinh chuyển sang tab khác hoặc ẩn trình duyệt');
        }
      });
      
      // 4. Giám sát mất Focus (Blur)
      window.addEventListener('blur', () => {
        if (!this.isExamActive || this.isSubmitting) return;
        const now = Date.now();
        // Tránh trùng lặp với visibilitychange (trong khoảng 800ms)
        if (now - this.lastBlurTime > 1000) {
          this.lastBlurTime = now;
          this.recordViolation('WINDOW_BLUR', 'Học sinh chuyển tiêu điểm sang cửa sổ ứng dụng khác');
        }
      });
    }
    
    // 5. Giám sát thoát Toàn màn hình (Fullscreen Exit)
    if (this.enableFullscreen) {
      document.addEventListener('fullscreenchange', () => {
        if (!this.isExamActive || this.isSubmitting) return;
        
        if (!document.fullscreenElement) {
          this.recordViolation('EXIT_FULLSCREEN', 'Học sinh thoát chế độ toàn màn hình');
        }
      });
    }
  }
  
  async recordViolation(eventType, details) {
    if (this.isSubmitting) return;
    
    try {
      const response = await fetch(`/api/exam/${this.submissionId}/violation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          event_type: eventType,
          details: details
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        this.violationsCount = data.violations_count;
        if (this.violationCounter) {
          this.violationCounter.textContent = `${this.violationsCount}/${this.maxViolations}`;
        }
        
        if (data.auto_submit) {
          this.autoSubmit('ĐÃ VƯỢT QUÁ SỐ LẦN VI PHẠM CHO PHÉP! Bài thi bị khoá tự động.');
        } else {
          this.showWarningModal(
            `CẢNH BÁO VI PHẠM (${this.violationsCount}/${this.maxViolations})\n${details}.\nHãy tập trung làm bài thi, không rời khỏi màn hình!`
          );
        }
      }
    } catch (err) {
      console.error('Lỗi ghi nhận vi phạm:', err);
    }
  }
  
  showWarningModal(message) {
    if (!this.warningModal) return;
    if (this.warningMessage) {
      this.warningMessage.innerText = message;
    }
    this.warningModal.classList.add('active');
    
    const card = this.warningModal.querySelector('.clay-modal');
    if (card) {
      card.classList.add('animate-shake');
      setTimeout(() => card.classList.remove('animate-shake'), 500);
    }
  }
  
  closeWarningModal() {
    if (this.warningModal) {
      this.warningModal.classList.remove('active');
    }
    if (this.enableFullscreen && !document.fullscreenElement) {
      this.requestFullscreen();
    }
  }
  
  autoSubmit(reason) {
    if (this.isSubmitting) return;
    this.isSubmitting = true;
    this.isExamActive = false;
    
    alert(reason || 'Bài thi đang được nộp...');
    if (this.examForm) {
      this.examForm.submit();
    }
  }
  
  showToast(msg, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `clay-alert alert-${type === 'warning' ? 'warning' : 'info'} animate-spring-pop`;
    toast.style.position = 'fixed';
    toast.style.top = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '10000';
    toast.style.boxShadow = 'var(--shadow-clay-card)';
    toast.textContent = msg;
    document.body.appendChild(toast);
    
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.4s ease';
      setTimeout(() => toast.remove(), 400);
    }, 2500);
  }
  
  bindEvents() {
    const closeBtn = document.getElementById('close-warning-btn');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.closeWarningModal());
    }
    
    if (this.examForm) {
      this.examForm.addEventListener('submit', () => {
        this.isSubmitting = true;
        this.isExamActive = false;
      });
    }
  }
}

window.AntiCheatingEngine = AntiCheatingEngine;
