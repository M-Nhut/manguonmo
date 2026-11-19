// Main JavaScript for Tin Hoc 11 (UI/UX Pro Max v3.0 — Aero-Teal Studio + GSAP Scroll Motion)

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

  // Auto-dismiss non-critical alerts after 6s, pausing on hover/focus
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const alerts = document.querySelectorAll('.clay-alert.alert-success, .clay-alert.alert-info');
  alerts.forEach((alert) => {
    let timerId = null;
    const scheduleHide = () => {
      timerId = setTimeout(() => {
        if (prefersReduced) { alert.remove(); return; }
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-6px)';
        alert.style.transition = 'opacity 0.35s ease, transform 0.35s ease';
        setTimeout(() => alert.remove(), 350);
      }, 6000);
    };
    const cancelHide = () => { if (timerId) { clearTimeout(timerId); timerId = null; } };
    scheduleHide();
    alert.addEventListener('mouseenter', cancelHide);
    alert.addEventListener('focusin', cancelHide);
  });

  // 1. Global Scroll Progress Bar + Sticky Topbar Elevation + Floating Back-to-Top
  const globalBar = document.getElementById('global-scroll-progress-fill');
  const readingBar = document.getElementById('reading-progress-fill');
  const topbar = document.querySelector('.app-topbar');
  const backTopBtn = document.getElementById('back-to-top-btn');

  const onScrollUpdate = () => {
    const sy = window.scrollY || 0;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const pct = docHeight > 0 ? Math.min(100, Math.max(0, (sy / docHeight) * 100)) : 0;
    if (globalBar) globalBar.style.width = `${pct.toFixed(1)}%`;
    if (readingBar) readingBar.style.width = `${pct.toFixed(1)}%`;
    if (topbar) topbar.classList.toggle('is-scrolled', sy > 12);
    if (backTopBtn) backTopBtn.classList.toggle('is-visible', sy > 320);
  };
  onScrollUpdate();
  window.addEventListener('scroll', onScrollUpdate, { passive: true });
  if (backTopBtn) {
    backTopBtn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: prefersReduced ? 'auto' : 'smooth' });
    });
  }

  // 2. Interactive 3D Micro-Tilt & Radial Pointer Spotlight on Cards (hover devices only)
  if (!prefersReduced && window.matchMedia('(hover: hover)').matches) {
    const bindInteractiveCard = (card, withTilt) => {
      card.addEventListener('pointermove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        card.style.setProperty('--mx', `${x}px`);
        card.style.setProperty('--my', `${y}px`);
        if (withTilt && rect.width > 0 && rect.height > 0) {
          const rx = ((0.5 - y / rect.height) * 4.5).toFixed(2);
          const ry = ((x / rect.width - 0.5) * 5.0).toFixed(2);
          card.style.setProperty('--rx', `${rx}deg`);
          card.style.setProperty('--ry', `${ry}deg`);
        }
      }, { passive: true });
      if (withTilt) {
        card.addEventListener('pointerleave', () => {
          card.style.setProperty('--rx', '0deg');
          card.style.setProperty('--ry', '0deg');
        }, { passive: true });
      }
    };
    document.querySelectorAll('.card-interactive:not(.pro-card-tilt)').forEach((c) => bindInteractiveCard(c, false));
    document.querySelectorAll('.pro-card-tilt').forEach((c) => bindInteractiveCard(c, true));
  }

  // 3. GSAP + ScrollTrigger Pro Motion Choreography (with IntersectionObserver Fallback!)
  if (!prefersReduced && typeof window.gsap !== 'undefined') {
    const gsap = window.gsap;
    if (typeof window.ScrollTrigger !== 'undefined') {
      gsap.registerPlugin(window.ScrollTrigger);
    }

    const mm = gsap.matchMedia();
    mm.add('(prefers-reduced-motion: no-preference)', () => {
      // A. Hero Entrance Stagger
      const heroItems = document.querySelectorAll('[data-hero-stagger]');
      if (heroItems.length) {
        gsap.from(heroItems, {
          opacity: 0,
          y: 22,
          duration: 0.65,
          stagger: 0.08,
          ease: 'power3.out',
          clearProps: 'transform,opacity'
        });
      }

      // B. Decorative Parallax Layers on Scroll ([data-parallax])
      if (typeof window.ScrollTrigger !== 'undefined') {
        document.querySelectorAll('[data-parallax]').forEach((layer) => {
          const speed = parseFloat(layer.getAttribute('data-parallax') || '-12');
          gsap.to(layer, {
            yPercent: speed,
            ease: 'none',
            scrollTrigger: {
              trigger: layer.parentElement || layer,
              start: 'top bottom',
              end: 'bottom top',
              scrub: 0.6
            }
          });
        });
      }

      // C. Scroll-Triggered Stagger Groups ([data-reveal-group])
      document.querySelectorAll('[data-reveal-group]').forEach((group) => {
        if (group.closest('[hidden]')) return;
        const children = group.querySelectorAll('[data-reveal]');
        if (!children.length) return;
        const cfg = {
          opacity: 0,
          y: 24,
          scale: 0.985,
          duration: 0.52,
          stagger: 0.065,
          ease: 'power3.out',
          clearProps: 'transform,opacity'
        };
        if (typeof window.ScrollTrigger !== 'undefined') {
          cfg.scrollTrigger = { trigger: group, start: 'top 90%', once: true };
        }
        gsap.from(children, cfg);
      });

      // D. Standalone Section Reveals ([data-reveal] outside groups)
      document.querySelectorAll('[data-reveal]:not([data-reveal-group] [data-reveal])').forEach((el) => {
        if (el.closest('[hidden]')) return;
        const cfg = {
          opacity: 0,
          y: 18,
          duration: 0.48,
          ease: 'power2.out',
          clearProps: 'transform,opacity'
        };
        if (typeof window.ScrollTrigger !== 'undefined') {
          cfg.scrollTrigger = { trigger: el, start: 'top 92%', once: true };
        }
        gsap.from(el, cfg);
      });

      // E. Smooth KPI Count-Up on Scroll ([data-countup])
      document.querySelectorAll('[data-countup]').forEach((el) => {
        const raw = (el.getAttribute('data-countup') || '').trim();
        const target = parseFloat(raw);
        if (Number.isNaN(target)) return;
        const decimals = raw.includes('.') ? (raw.split('.')[1] || '').length : 0;
        const suffix = el.getAttribute('data-countup-suffix') || '';
        const counter = { val: 0 };
        const cfg = {
          val: target,
          duration: 0.95,
          ease: 'power2.out',
          onUpdate: () => { el.textContent = counter.val.toFixed(decimals) + suffix; }
        };
        if (typeof window.ScrollTrigger !== 'undefined') {
          cfg.scrollTrigger = { trigger: el, start: 'top 92%', once: true };
        }
        gsap.to(counter, cfg);
      });
    });
  } else if (!prefersReduced && 'IntersectionObserver' in window) {
    // Zero-dependency IntersectionObserver fallback if GSAP CDN is unavailable
    document.documentElement.classList.add('js-reveal-ready');
    const items = document.querySelectorAll('[data-reveal]');
    items.forEach((el) => { if (!el.closest('[hidden]')) el.classList.add('reveal-pending'); });
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.remove('reveal-pending');
          entry.target.classList.add('is-revealed');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08 });
    items.forEach((el) => io.observe(el));
  }
});

// Helper for dynamic view switches (e.g., opening a Topic Drawer with staggered poster cards!)
window.animateStaggerReveal = function (container) {
  if (!container) return;
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReduced) return;
  const items = container.querySelectorAll('[data-stagger-card]');
  if (!items.length) return;
  if (typeof window.gsap !== 'undefined') {
    window.gsap.fromTo(items,
      { opacity: 0, y: 20, scale: 0.975 },
      { opacity: 1, y: 0, scale: 1, duration: 0.44, stagger: 0.055, ease: 'power3.out', clearProps: 'transform,opacity' }
    );
  }
};
