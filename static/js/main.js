/* ═══════════════════════════════════════════════
   KADAM FOUNDATION — main.js
═══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  /* ── NAV SCROLL ── */
  const nav = document.querySelector('.nav');
  if (nav) {
    window.addEventListener('scroll', () => {
      nav.classList.toggle('scrolled', window.scrollY > 60);
    }, { passive: true });
  }

  // NOTE: Hamburger / mobile overlay is handled inline in base.html
  // (openNav / closeNav functions) so we do NOT re-bind it here.

  /* ── ACTIVE NAV LINK ── */
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-links a').forEach(a => {
    const href = a.getAttribute('href');
    if (href === currentPath || (currentPath === '/' && href === '/')) {
      a.classList.add('active');
    }
  });

  /* ── REVEAL ON SCROLL ── */
  const revealEls = document.querySelectorAll('.reveal, .reveal-left, .reveal-right');
  if (revealEls.length) {
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
    revealEls.forEach(el => revealObserver.observe(el));
  }

  /* ── STAT COUNTER ── */
  const statItems = document.querySelectorAll('.stat-item');
  if (statItems.length) {
    const statsObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
          setTimeout(() => {
            entry.target.classList.add('visible');
            const numEl = entry.target.querySelector('.stat-number');
            if (numEl && numEl.dataset.target) {
              animateCount(numEl, parseInt(numEl.dataset.target), 1800);
            }
          }, i * 100);
          statsObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.3 });
    statItems.forEach(el => statsObserver.observe(el));
  }

  function animateCount(el, target, duration) {
    const start  = performance.now();
    const update = (now) => {
      const t    = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - t, 3); // cubic ease-out
      el.textContent = Math.floor(ease * target) + (t >= 1 ? '+' : '');
      if (t < 1) requestAnimationFrame(update);
    };
    requestAnimationFrame(update);
  }

  /* ── HERO PARALLAX (home only) ── */
  const heroContent = document.querySelector('.hero-content');
  if (heroContent) {
    window.addEventListener('scroll', () => {
      const y  = window.scrollY;
      const vh = window.innerHeight;
      if (y < vh) {
        heroContent.style.transform = `translateY(${y * 0.16}px)`;
        heroContent.style.opacity   = String(1 - y / (vh * 0.85));
      }
    }, { passive: true });
  }

  /* ── DONATE CARD SELECTION ── */
  document.querySelectorAll('.donate-card').forEach(card => {
    card.addEventListener('click', () => {
      document.querySelectorAll('.donate-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      const amountInput = document.getElementById('custom-amount');
      if (amountInput && card.dataset.amount) {
        amountInput.value = card.dataset.amount;
      }
    });
  });

  /* ── SMOOTH SCROLL for anchor links ── */
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const target = document.querySelector(a.getAttribute('href'));
      if (target) {
        e.preventDefault();
        const top = target.getBoundingClientRect().top + window.scrollY - 80;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    });
  });

  /* ── TOAST UTILITY ── */
  window.showToast = function(message, type = 'success') {
    let toast = document.getElementById('toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id        = 'toast';
      toast.className = 'toast';
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.className   = `toast${type === 'error' ? ' error' : ''}`;
    void toast.offsetWidth; // force reflow
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 4000);
  };

  /* ── VOLUNTEER FORM ── */
  const volunteerForm = document.getElementById('volunteer-form');
  if (volunteerForm) {
    volunteerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn      = volunteerForm.querySelector('[type=submit]');
      btn.disabled   = true;
      btn.textContent = 'Submitting…';

      const data = {
        name:    volunteerForm.querySelector('[name=name]').value,
        email:   volunteerForm.querySelector('[name=email]').value,
        phone:   volunteerForm.querySelector('[name=phone]')?.value || '',  // FIX: now included
        city:    volunteerForm.querySelector('[name=city]').value,
        cause:   volunteerForm.querySelector('[name=cause]').value,
        message: volunteerForm.querySelector('[name=message]')?.value || '',
      };

      try {
        const res  = await fetch('/api/volunteer', {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify(data),
        });
        const json = await res.json();
        if (json.success) {
          showToast(json.message);
          volunteerForm.reset();
        } else {
          showToast(json.error || 'Something went wrong.', 'error');
        }
      } catch {
        showToast('Network error. Please try again.', 'error');
      } finally {
        btn.disabled    = false;
        btn.textContent = 'Submit Application →';
      }
    });
  }

  // NOTE: Contact form submission is handled in contact.html's own
  // {% block extra_js %} script to keep organisation/subject merging logic
  // co-located with the form. No duplicate handler here.

  /* ── LIVE STATS FETCH (if element exists) ── */
  const liveStats = document.querySelector('[data-live-stats]');
  if (liveStats) {
    fetch('/api/stats')
      .then(r => r.json())
      .then(data => {
        document.querySelectorAll('[data-stat]').forEach(el => {
          const key = el.dataset.stat;
          if (data[key] !== undefined) el.dataset.target = data[key];
        });
      })
      .catch(() => {}); // fail silently
  }

});
