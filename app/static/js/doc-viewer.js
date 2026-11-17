/**
 * IN-BROWSER PRESENTATION SLIDE VIEWER (PPTX/PPT)
 */

class SlideViewer {
  constructor(slides) {
    this.slides = slides || [];
    this.currentIndex = 0;
    this.totalSlides = this.slides.length;

    this.initElements();
    this.bindEvents();
    this.render();
  }

  initElements() {
    this.container = document.getElementById('slide-content-area');
    this.titleEl = document.getElementById('slide-title');
    this.bulletsEl = document.getElementById('slide-bullets');
    this.counterEl = document.getElementById('slide-counter');
    this.prevBtn = document.getElementById('prev-slide-btn');
    this.nextBtn = document.getElementById('next-slide-btn');
  }

  bindEvents() {
    if (this.prevBtn) {
      this.prevBtn.addEventListener('click', () => this.prev());
    }
    if (this.nextBtn) {
      this.nextBtn.addEventListener('click', () => this.next());
    }

    document.addEventListener('keydown', (e) => {
      const tag = (e.target && e.target.tagName) ? e.target.tagName.toUpperCase() : '';
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

      if (e.key === 'ArrowRight' || e.key === 'PageDown') {
        e.preventDefault();
        this.next();
      } else if (e.key === ' ' && tag !== 'BUTTON' && tag !== 'A') {
        e.preventDefault();
        this.next();
      } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
        e.preventDefault();
        this.prev();
      }
    });
  }

  next() {
    if (this.currentIndex < this.totalSlides - 1) {
      this.currentIndex++;
      this.render('next');
    }
  }

  prev() {
    if (this.currentIndex > 0) {
      this.currentIndex--;
      this.render('prev');
    }
  }

  render() {
    if (!this.totalSlides || !this.slides[this.currentIndex]) return;

    const current = this.slides[this.currentIndex];

    if (this.counterEl) {
      this.counterEl.textContent = `Slide ${this.currentIndex + 1} / ${this.totalSlides}`;
    }

    if (this.titleEl) {
      this.titleEl.textContent = current.title || `Slide ${this.currentIndex + 1}`;
    }

    if (this.bulletsEl) {
      this.bulletsEl.innerHTML = '';
      if (current.content && current.content.length > 0) {
        current.content.forEach((bullet) => {
          const li = document.createElement('li');
          li.className = 'clay-list-item text-base sm:text-lg text-slate-700 leading-relaxed';
          li.textContent = bullet;
          this.bulletsEl.appendChild(li);
        });
      } else {
        const li = document.createElement('li');
        li.className = 'text-slate-600 italic list-none';
        li.textContent = '(Slide này không có nội dung văn bản phụ)';
        this.bulletsEl.appendChild(li);
      }
    }

    if (this.prevBtn) this.prevBtn.disabled = (this.currentIndex === 0);
    if (this.nextBtn) this.nextBtn.disabled = (this.currentIndex === this.totalSlides - 1);

    if (this.container) {
      this.container.classList.remove('slide-enter-active');
      void this.container.offsetWidth;
      this.container.classList.add('slide-enter-active');
    }
  }
}

window.SlideViewer = SlideViewer;
