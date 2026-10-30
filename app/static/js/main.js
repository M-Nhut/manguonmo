// Main JavaScript for Tin Hoc 11 ELearning

document.addEventListener('DOMContentLoaded', () => {
  // Add subtle ripple / spring bounce effect on clay buttons
  const clayButtons = document.querySelectorAll('.clay-btn');
  clayButtons.forEach(btn => {
    btn.addEventListener('mousedown', () => {
      btn.style.transform = 'scale(0.96) translateY(2px)';
    });
    btn.addEventListener('mouseup', () => {
      btn.style.transform = '';
    });
    btn.addEventListener('mouseleave', () => {
      btn.style.transform = '';
    });
  });

  // Auto-dismiss alerts after 5 seconds
  const alerts = document.querySelectorAll('.clay-alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transition = 'opacity 0.5s ease';
      setTimeout(() => alert.remove(), 500);
    }, 5000);
  });
});
