// Main JavaScript for Tin Hoc 11 (Luminous EdTech Design System v2.1)

// Top-layer <dialog> helpers with clean exit animation fallback for Firefox/Safari
let _supportsDisplayTransition;
function canTransitionDisplay() {
  if (_supportsDisplayTransition !== undefined) return _supportsDisplayTransition;
  if (!window.CSS?.supports?.('transition-behavior', 'allow-discrete') || !document.body) {
    return false;
  }
  const probe = document.createElement('div');
  probe.style.cssText = 'transition: display 1s allow-discrete !important; display: block;';
  document.body.appendChild(probe);
  getComputedStyle(probe).display;
  probe.style.display = 'none';
  _supportsDisplayTransition = getComputedStyle(probe).display === 'block';
  probe.remove();
  return _supportsDisplayTransition;
}

function supportsTopLayerExit() {
  return window.CSS?.supports?.('overlay', 'auto') && canTransitionDisplay();
}

async function closeTopLayerDialog(dialog) {
  if (!dialog || !dialog.open) return;
  if (!supportsTopLayerExit() && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    dialog.setAttribute('data-closing', '');
    const animations = dialog.getAnimations({ subtree: true });
    if (animations.length > 0) {
      await Promise.race([
        Promise.allSettled(animations.map((a) => a.finished)),
        new Promise((r) => setTimeout(r, 320)),
      ]);
    }
    if (!dialog.hasAttribute('data-closing')) return;
    dialog.removeAttribute('data-closing');
  }
  if (typeof dialog.close === 'function') {
    dialog.close();
  } else {
    dialog.removeAttribute('open');
  }
}

window.openDsDialog = function (dialogId) {
  const dlg = document.getElementById(dialogId);
  if (!dlg) return;
  dlg.removeAttribute('data-closing');
  if (typeof dlg.showModal === 'function') {
    if (!dlg.open) dlg.showModal();
  } else {
    dlg.setAttribute('open', '');
  }
};

window.closeDsDialog = function (dialogId) {
  const dlg = document.getElementById(dialogId);
  if (!dlg) return;
  closeTopLayerDialog(dlg);
};

window.toggleSidebar = function (forceOpen) {
  const sidebar = document.getElementById('app-sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  const toggleBtn = document.getElementById('sidebar-toggle-btn');
  if (!sidebar || !overlay) return;

  const isOpen = typeof forceOpen === 'boolean'
    ? forceOpen
    : !sidebar.classList.contains('open');

  sidebar.classList.toggle('open', isOpen);
  overlay.classList.toggle('active', isOpen);

  if (toggleBtn) {
    toggleBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  }

  const isDesktop = window.matchMedia('(min-width: 1024px)').matches;
  sidebar.inert = !isDesktop && !isOpen;

  if (isOpen && !isDesktop) {
    const firstLink = sidebar.querySelector('a, button');
    if (firstLink) firstLink.focus();
  } else if (!isOpen && !isDesktop && toggleBtn && sidebar.contains(document.activeElement)) {
    toggleBtn.focus();
  }
};

document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.getElementById('app-sidebar');
  const mqDesktop = window.matchMedia('(min-width: 1024px)');

  const syncSidebarInert = () => {
    if (!sidebar) return;
    const isDesktop = mqDesktop.matches;
    if (isDesktop) {
      sidebar.inert = false;
      sidebar.classList.remove('open');
      const overlay = document.getElementById('sidebar-overlay');
      if (overlay) overlay.classList.remove('active');
    } else {
      sidebar.inert = !sidebar.classList.contains('open');
    }
  };

  if (sidebar) {
    syncSidebarInert();
    mqDesktop.addEventListener('change', syncSidebarInert);
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && sidebar.classList.contains('open')) {
        window.toggleSidebar(false);
      }
    });
  }

  // Native <dialog> cancel animation & closedby="any" fallback
  document.querySelectorAll('dialog.ds-dialog').forEach((dialog) => {
    dialog.addEventListener('cancel', (e) => {
      if (!supportsTopLayerExit()) {
        e.preventDefault();
        closeTopLayerDialog(dialog);
      }
    });
  });

  if (typeof HTMLDialogElement !== 'undefined' && !('closedBy' in HTMLDialogElement.prototype)) {
    const isOutside = (e, dialog) => {
      const r = dialog.getBoundingClientRect();
      return e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
    };
    document.querySelectorAll('dialog[closedby="any"]').forEach((dialog) => {
      let pressedOutside = false;
      dialog.addEventListener('pointerdown', (e) => {
        pressedOutside = isOutside(e, dialog);
      });
      dialog.addEventListener('pointerup', (e) => {
        if (pressedOutside && isOutside(e, dialog)) closeTopLayerDialog(dialog);
      });
    });
  }

  // Auto-dismiss only non-critical (success/info) alerts after 6s, pausing on hover/focus
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const alerts = document.querySelectorAll('.clay-alert.alert-success, .clay-alert.alert-info');
  alerts.forEach((alert) => {
    let timerId = null;
    const scheduleHide = () => {
      timerId = setTimeout(() => {
        if (prefersReduced) {
          alert.remove();
          return;
        }
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-6px)';
        alert.style.transition = 'opacity 0.35s ease, transform 0.35s ease';
        setTimeout(() => alert.remove(), 350);
      }, 6000);
    };
    const cancelHide = () => {
      if (timerId) {
        clearTimeout(timerId);
        timerId = null;
      }
    };
    scheduleHide();
    alert.addEventListener('mouseenter', cancelHide);
    alert.addEventListener('focusin', cancelHide);
  });

  // Pointer radial spotlight on interactive cards (hover devices + reduced-motion safe)
  if (!prefersReduced && window.matchMedia('(hover: hover)').matches) {
    document.querySelectorAll('.card-interactive').forEach((card) => {
      card.addEventListener('pointermove', (e) => {
        const rect = card.getBoundingClientRect();
        card.style.setProperty('--mx', `${e.clientX - rect.left}px`);
        card.style.setProperty('--my', `${e.clientY - rect.top}px`);
      }, { passive: true });
    });
  }

  // Reading progress indicator if present on page
  const readingBar = document.getElementById('reading-progress-fill');
  if (readingBar) {
    const updateReadingBar = () => {
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const pct = docHeight > 0 ? Math.min(100, Math.max(0, (window.scrollY / docHeight) * 100)) : 0;
      readingBar.style.width = `${pct.toFixed(1)}%`;
    };
    updateReadingBar();
    window.addEventListener('scroll', updateReadingBar, { passive: true });
  }

  // GSAP Motion Choreography (if GSAP loaded & user does not prefer reduced motion)
  if (!prefersReduced && typeof window.gsap !== 'undefined') {
    const gsap = window.gsap;
    if (typeof window.ScrollTrigger !== 'undefined') {
      gsap.registerPlugin(window.ScrollTrigger);
    }

    const mm = gsap.matchMedia();
    mm.add('(prefers-reduced-motion: no-preference)', () => {
      // 1. Hero Entrance Stagger
      const heroItems = document.querySelectorAll('[data-hero-stagger]');
      if (heroItems.length) {
        gsap.from(heroItems, {
          opacity: 0,
          y: 18,
          duration: 0.6,
          stagger: 0.08,
          ease: 'power3.out',
          clearProps: 'transform,opacity'
        });
      }

      // 2. Scroll-triggered stagger groups ([data-reveal-group])
      document.querySelectorAll('[data-reveal-group]').forEach((group) => {
        const children = group.querySelectorAll('[data-reveal]');
        if (!children.length) return;
        const animConfig = {
          opacity: 0,
          y: 16,
          duration: 0.45,
          stagger: 0.06,
          ease: 'power2.out',
          clearProps: 'transform,opacity'
        };
        if (typeof window.ScrollTrigger !== 'undefined') {
          animConfig.scrollTrigger = {
            trigger: group,
            start: 'top 90%',
            once: true
          };
        }
        gsap.from(children, animConfig);
      });

      // 3. Single section reveals ([data-reveal] not inside a group)
      document.querySelectorAll('[data-reveal]:not([data-reveal-group] [data-reveal])').forEach((el) => {
        const animConfig = {
          opacity: 0,
          y: 14,
          duration: 0.42,
          ease: 'power2.out',
          clearProps: 'transform,opacity'
        };
        if (typeof window.ScrollTrigger !== 'undefined') {
          animConfig.scrollTrigger = {
            trigger: el,
            start: 'top 92%',
            once: true
          };
        }
        gsap.from(el, animConfig);
      });

      // 4. Smooth KPI Number Count-Up ([data-countup])
      document.querySelectorAll('[data-countup]').forEach((el) => {
        const raw = (el.getAttribute('data-countup') || '').trim();
        const target = parseFloat(raw);
        if (Number.isNaN(target)) return;
        const decimals = raw.includes('.') ? (raw.split('.')[1] || '').length : 0;
        const suffix = el.getAttribute('data-countup-suffix') || '';
        const counter = { val: 0 };
        gsap.to(counter, {
          val: target,
          duration: 0.85,
          ease: 'power2.out',
          onUpdate: () => {
            el.textContent = counter.val.toFixed(decimals) + suffix;
          }
        });
      });
    });
  }
});
