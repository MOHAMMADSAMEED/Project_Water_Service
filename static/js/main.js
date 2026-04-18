/**
 * Mulla Water Filter — Main JS
 */

// ── Hamburger Menu ──
const hamburger = document.getElementById('hamburger');
const navLinks = document.getElementById('nav-links');
if (hamburger && navLinks) {
  hamburger.addEventListener('click', () => {
    navLinks.classList.toggle('open');
  });
  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!hamburger.contains(e.target) && !navLinks.contains(e.target)) {
      navLinks.classList.remove('open');
    }
  });
}

// ── Update Cart Badge ──
function updateCartBadge() {
  const badge = document.getElementById('cart-count');
  if (!badge) return;
  fetch('/api/cart-count')
    .then(r => r.json())
    .then(data => {
      badge.textContent = data.count;
      badge.style.display = data.count > 0 ? 'flex' : 'none';
    })
    .catch(() => {});
}
updateCartBadge();

// ── Auto-dismiss Flash Messages ──
setTimeout(() => {
  document.querySelectorAll('.flash').forEach(el => {
    el.style.transition = 'opacity 0.5s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 500);
  });
}, 4000);

// ── Smooth scroll for anchor links ──
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', function(e) {
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});
