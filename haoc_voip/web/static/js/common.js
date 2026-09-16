/**
 * HAOC VoIP Monitor Enterprise - JavaScript Utilitário Comum
 * Suporte a alternância de tema, alertas e controle de modais
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Inicializar tema visual a partir do localStorage
  const savedTheme = localStorage.getItem('haoc_theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeIcon(savedTheme);

  const themeBtn = document.getElementById('theme-toggle-btn');
  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      const nextTheme = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', nextTheme);
      localStorage.setItem('haoc_theme', nextTheme);
      updateThemeIcon(nextTheme);
    });
  }

  // 2. Fechamento automático de alertas flash após 6 segundos
  const alerts = document.querySelectorAll('.alert-auto-dismiss');
  alerts.forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity 0.5s ease';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 500);
    }, 6000);
  });
});

function updateThemeIcon(theme) {
  const icon = document.getElementById('theme-icon');
  if (icon) {
    icon.textContent = theme === 'dark' ? '☀️' : '🌙';
  }
}

// Utilitários de Modal
window.openModal = function(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.add('active');
};

window.closeModal = function(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.remove('active');
};

// Toast notification leve
window.showToast = function(mensagem, tipo = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `alert alert-${tipo}`;
  toast.style.boxShadow = '0 4px 6px -1px rgb(0 0 0 / 0.1)';
  toast.style.marginBottom = '0.5rem';
  toast.textContent = mensagem;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.4s ease';
    setTimeout(() => toast.remove(), 400);
  }, 4000);
};
