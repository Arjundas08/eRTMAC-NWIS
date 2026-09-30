/**
 * NWIS Landing Page Interactive Controller
 * Oil India Limited — eRTMAC-NWIS Enterprise Platform
 */

document.addEventListener('DOMContentLoaded', () => {
  initNav();
  initApiStatus();
  initModal();
});

// -------------------------------------------------------------
// Sticky Navigation & Smooth Scrolling
// -------------------------------------------------------------
function initNav() {
  const nav = document.getElementById('landing-nav');
  const toggle = document.getElementById('nav-mobile-toggle');
  const navLinks = document.getElementById('nav-links');

  window.addEventListener('scroll', () => {
    if (window.scrollY > 40) {
      nav.style.background = 'rgba(4, 13, 24, 0.96)';
      nav.style.borderBottomColor = 'rgba(8, 127, 140, 0.3)';
    } else {
      nav.style.background = 'rgba(4, 13, 24, 0.88)';
      nav.style.borderBottomColor = 'rgba(255, 255, 255, 0.08)';
    }
  });

  if (toggle && navLinks) {
    toggle.addEventListener('click', () => {
      const isOpen = navLinks.style.display === 'flex';
      navLinks.style.display = isOpen ? 'none' : 'flex';
      toggle.setAttribute('aria-expanded', !isOpen);
    });
  }

  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      const targetEl = document.querySelector(targetId);
      if (targetEl) {
        e.preventDefault();
        targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}

// -------------------------------------------------------------
// Fetch Real Live Backend Status
// -------------------------------------------------------------
async function initApiStatus() {
  try {
    const res = await fetch('/api/v1/status');
    if (res.ok) {
      const data = await res.json();
      console.log('eRTMAC-NWIS Backend Online:', data);
      const badge = document.querySelector('.hero-badge');
      if (badge) {
        badge.innerHTML = `
          <span class="hero-badge-dot" style="background:#22C55E"></span>
          OIL INDIA LIMITED — eRTMAC LIVE STATUS: ${data.status} (v${data.version})
        `;
      }
    }
  } catch (err) {
    console.warn('Backend status check offline or running standalone:', err);
  }
}

// -------------------------------------------------------------
// Image Lightbox Modal
// -------------------------------------------------------------
function initModal() {
  const modal = document.getElementById('imageModal');
  if (!modal) return;

  // Close on outside click
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      closeImageModal();
    }
  });

  // Close on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('open')) {
      closeImageModal();
    }
  });
}

window.openImageModal = function(imgSrc, title, caption) {
  const modal = document.getElementById('imageModal');
  const modalImg = document.getElementById('modalImg');
  const modalTitle = document.getElementById('modalTitle');
  const modalCaption = document.getElementById('modalCaption');

  if (!modal || !modalImg) return;

  modalImg.src = imgSrc;
  modalImg.alt = title;
  modalTitle.textContent = title;
  modalCaption.innerHTML = `<strong>Engineering Analysis & Context:</strong> ${caption}`;

  modal.classList.add('open');
  modal.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';
};

window.closeImageModal = function() {
  const modal = document.getElementById('imageModal');
  if (!modal) return;
  modal.classList.remove('open');
  modal.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = '';
};
