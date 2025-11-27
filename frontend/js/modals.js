// Modal helpers
function showWalletPasswordModal({ title = 'Senha do Wallet', confirm = false } = {}) {
  return new Promise((resolve) => {
    const modal = document.getElementById('wallet-password-modal');
    const titleEl = document.getElementById('wallet-modal-title');
    const input = document.getElementById('wallet-password-input');
    const confirmContainer = document.getElementById('wallet-password-confirm-container');
    const confirmInput = document.getElementById('wallet-password-confirm');
    const okBtn = document.getElementById('wallet-password-ok');
    const cancelBtn = document.getElementById('wallet-password-cancel');

    titleEl.textContent = title;
    input.value = '';
    confirmInput.value = '';
    confirmContainer.style.display = confirm ? 'block' : 'none';

    modal.classList.remove('hidden');
    modal.style.display = 'flex';
    modal.style.visibility = 'visible';
    modal.style.opacity = '1';

    setTimeout(() => {
      try { input.focus(); } catch (e) { }
    }, 20);

    function cleanup() {
      okBtn.removeEventListener('click', onOk);
      cancelBtn.removeEventListener('click', onCancel);
      document.removeEventListener('keydown', onKeyDown);
      modal.style.display = 'none';
      modal.style.visibility = '';
      modal.style.opacity = '';
    }

    function onKeyDown(ev) {
      if (ev.key === 'Enter') {
        onOk();
      } else if (ev.key === 'Escape') {
        onCancel();
      }
    }
    document.addEventListener('keydown', onKeyDown);

    function onOk() {
      const val = input.value;
      if (!val) {
        setStatus('Informe a senha do wallet.', 'error');
        return;
      }
      if (confirm) {
        if (confirmInput.value !== val) {
          setStatus('Senhas não conferem.', 'error');
          return;
        }
      }
      cleanup();
      resolve(val);
    }

    function onCancel() {
      cleanup();
      resolve(null);
    }

    okBtn.addEventListener('click', onOk);
    cancelBtn.addEventListener('click', onCancel);
    input.focus();
  });
}

function showConfirmModal({ title = 'Confirmar', message = 'Tem certeza?' } = {}) {
  return new Promise((resolve) => {
    const modal = document.getElementById('confirm-modal');
    const titleEl = document.getElementById('confirm-modal-title');
    const msgEl = document.getElementById('confirm-modal-message');
    const okBtn = document.getElementById('confirm-ok');
    const cancelBtn = document.getElementById('confirm-cancel');

    titleEl.textContent = title;
    msgEl.textContent = message;

    modal.classList.remove('hidden');
    modal.style.display = 'flex';
    modal.style.visibility = 'visible';

    function cleanup() {
      okBtn.removeEventListener('click', onOk);
      cancelBtn.removeEventListener('click', onCancel);
      document.removeEventListener('keydown', onKeyDown);
      modal.style.display = 'none';
      modal.style.visibility = '';
    }

    function onKeyDown(ev) {
      if (ev.key === 'Enter') onOk();
      if (ev.key === 'Escape') onCancel();
    }
    document.addEventListener('keydown', onKeyDown);

    function onOk() { cleanup(); resolve(true); }
    function onCancel() { cleanup(); resolve(false); }

    okBtn.addEventListener('click', onOk);
    cancelBtn.addEventListener('click', onCancel);
  });
}

function showEditPasswordModal(entry) {
  return new Promise((resolve) => {
    const modal = document.getElementById('edit-password-modal');
    const titleEl = document.getElementById('edit-modal-title');
    const inputTitle = document.getElementById('edit-title');
    const inputSite = document.getElementById('edit-site');
    const inputPassword = document.getElementById('edit-password-input');
    const inputExpiration = document.getElementById('edit-expiration');
    const okBtn = document.getElementById('edit-password-ok');
    const cancelBtn = document.getElementById('edit-password-cancel');

    titleEl.textContent = 'Editar senha';
    inputTitle.value = entry.title || '';
    inputSite.value = entry.site || '';
    inputPassword.value = entry._decrypted_preview || '';
    inputExpiration.value = entry.expiration_date ? (new Date(entry.expiration_date)).toISOString().slice(0,16) : '';

    modal.classList.remove('hidden');
    modal.style.display = 'flex';
    modal.style.visibility = 'visible';

    function cleanup() {
      okBtn.removeEventListener('click', onOk);
      cancelBtn.removeEventListener('click', onCancel);
      document.removeEventListener('keydown', onKeyDown);
      modal.style.display = 'none';
      modal.style.visibility = '';
    }

    function onKeyDown(ev) {
      if (ev.key === 'Enter') onOk();
      if (ev.key === 'Escape') onCancel();
    }
    document.addEventListener('keydown', onKeyDown);

    function onOk() {
      const val = inputPassword.value;
      const t = inputTitle.value.trim();
      const s = inputSite.value.trim();
      const exp = inputExpiration.value ? new Date(inputExpiration.value).toISOString() : null;
      if (!t || !s) { setStatus('Título e site são obrigatórios.', 'error'); return; }
      cleanup();
      resolve({ title: t, site: s, password: val, expiration_date: exp });
    }

    function onCancel() { cleanup(); resolve(null); }

    okBtn.addEventListener('click', onOk);
    cancelBtn.addEventListener('click', onCancel);

    setTimeout(() => inputPassword.focus(), 20);
  });
}
