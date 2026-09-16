/**
 * SmartHostel Application JS Helpers
 */

function toggleModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.toggle('open');
  }
}

function togglePasswordVisibility(inputId, btn) {
  const input = document.getElementById(inputId);
  if (input) {
    const icon = btn.querySelector('i');
    if (input.type === 'password') {
      input.type = 'text';
      if (icon) icon.className = 'fa-solid fa-eye-slash';
    } else {
      input.type = 'password';
      if (icon) icon.className = 'fa-solid fa-eye';
    }
  }
}

function fillLogin(email, password) {
  const emailInput = document.querySelector('input[name="email"]');
  const passInput = document.querySelector('input[name="password"]');
  if (emailInput) emailInput.value = email;
  if (passInput) passInput.value = password;
}

function toggleNotifDropdown(event) {
  if (event) event.stopPropagation();
  const dropdown = document.getElementById('notifDropdown');
  if (dropdown) {
    dropdown.classList.toggle('open');
    document.getElementById('themePopover')?.classList.remove('open');
  }
}

function markNotifRead(notificationId, link) {
  fetch(`/notifications/mark-read/${notificationId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  }).then(res => res.json()).then(data => {
    if (link && link !== '#') {
      window.location.href = link;
    } else {
      window.location.reload();
    }
  }).catch(err => {
    if (link && link !== '#') window.location.href = link;
  });
}

function setBtnLoading(btn) {
  if (!btn) return;
  const form = btn.closest('form');
  if (form && !form.checkValidity()) return;

  btn.dataset.originalText = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Submitting...`;

  if (form) {
    form.submit();
  }
}

function dismissToast(btn) {
  const toast = btn.closest('.toast');
  if (toast) {
    toast.classList.add('toast-hide');
    setTimeout(() => toast.remove(), 300);
  }
}

// Global click & keyboard listeners
document.addEventListener('click', (e) => {
  const notifDropdown = document.getElementById('notifDropdown');
  if (notifDropdown && notifDropdown.classList.contains('open')) {
    if (!e.target.closest('.notif-wrapper')) {
      notifDropdown.classList.remove('open');
    }
  }

  if (e.target.classList.contains('modal')) {
    e.target.classList.remove('open');
  }
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal.open').forEach(m => m.classList.remove('open'));
    document.getElementById('notifDropdown')?.classList.remove('open');
    document.getElementById('themePopover')?.classList.remove('open');
  }
});
