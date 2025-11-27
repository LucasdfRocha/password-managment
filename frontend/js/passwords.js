// Passwords CRUD and UI
async function loadPasswords() {
  if (!sessionToken) return;

  setStatus("Carregando senhas...");
  tbodyPasswords.innerHTML = "";
  allPasswords = [];

  try {
    const resp = await apiRequest("/passwords", {
      method: "GET"
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || "Erro ao listar senhas");
    }

    const data = await resp.json();
    if (!Array.isArray(data)) {
      throw new Error("Resposta inesperada do servidor.");
    }

    allPasswords = data;
    data.forEach(entry => addPasswordRow(entry));
    updateEmptyState();
    setStatus("Senhas carregadas.");
  } catch (e) {
    console.error(e);
    setStatus("Erro ao carregar senhas: " + e.message, "error");
    updateEmptyState();
  }
}

function addPasswordRow(entry) {
  const tr = document.createElement('tr');
  tr.dataset.id = entry.id;

  const tdId = document.createElement('td');
  tdId.textContent = entry.id;

  const tdTitle = document.createElement('td');
  tdTitle.textContent = entry.title;

  const tdSite = document.createElement('td');
  tdSite.textContent = entry.site;

  const tdEntropy = document.createElement('td');
  const badgeClass = getEntropyBadge(entry.entropy_level);
  tdEntropy.innerHTML = `
    <div>${entry.entropy} bits</div>
    <span class="badge ${badgeClass}">${entry.entropy_level}</span>
  `;

  const tdExp = document.createElement('td');
  tdExp.textContent = formatDate(entry.expiration_date);

  const tdActions = document.createElement('td');
  const actionsDiv = document.createElement('div');
  actionsDiv.className = "row-actions";

  const btnView = document.createElement('button');
  btnView.textContent = "Ver";
  btnView.className = "secondary";
  btnView.addEventListener('click', () => viewPassword(entry.id, tr));

  const btnDelete = document.createElement('button');
  btnDelete.textContent = "Excluir";
  btnDelete.className = "danger";
  btnDelete.addEventListener('click', () => deletePassword(entry.id, tr));

  actionsDiv.appendChild(btnView);
  actionsDiv.appendChild(btnDelete);
  tdActions.appendChild(actionsDiv);

  tr.appendChild(tdId);
  tr.appendChild(tdTitle);
  tr.appendChild(tdSite);
  tr.appendChild(tdEntropy);
  tr.appendChild(tdExp);
  tr.appendChild(tdActions);

  tbodyPasswords.appendChild(tr);
}

async function viewPassword(id, row) {
  try {
    // Toggle: if detail row exists, remove it ("unsee")
    const existing = row.nextElementSibling;
    const viewBtn = row.querySelector('.secondary');
    if (existing && existing.classList && existing.classList.contains('password-row')) {
      existing.remove();
      if (viewBtn) viewBtn.textContent = 'Ver';
      setStatus('Visualização fechada.');
      return;
    }

    if (!masterPasswordPlain) {
      setStatus("Senha mestra não está disponível no cliente.", "error");
      return;
    }

    setStatus("Carregando senha...");
    const resp = await apiRequest(`/passwords/${id}`, {
      method: "GET"
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || "Erro ao obter senha");
    }

    const data = await resp.json();

    // decrypt on client
    let decrypted;
    try {
      decrypted = await decryptWithMasterPassword(data.encrypted_password, masterPasswordPlain);
    } catch (e) {
      console.error(e);
      setStatus("Erro ao descriptografar a senha no cliente: " + e.message, "error");
      return;
    }

    setStatus("Senha carregada.");

    try {
      const entryObj = allPasswords.find(p => p.id === id);
      if (entryObj) entryObj._decrypted_preview = decrypted;
    } catch (e) { }

    const prev = row.nextElementSibling;
    if (prev && prev.classList && prev.classList.contains("password-row")) {
      prev.remove();
    }

    const tr = document.createElement('tr');
    tr.className = "password-row";

    const td = document.createElement('td');
    td.colSpan = 6;

    const escaped = decrypted.replace(/'/g, "\\'");

    td.innerHTML = `
      <div>
        <strong>Senha:</strong>
        <div class="password-value">
          ${decrypted}
          <button class="copy-btn" onclick="copyToClipboard('${escaped}', this)"> Copiar</button>
        </div>
      </div>
    `;

    tr.appendChild(td);
    row.parentNode.insertBefore(tr, row.nextSibling);

    const editBtn = document.createElement('button');
    editBtn.textContent = 'Editar';
    editBtn.className = 'edit-btn';
    editBtn.style.marginLeft = '0.5rem';
    editBtn.addEventListener('click', () => startEditPassword(id));

    const pwValEl = td.querySelector('.password-value');
    if (pwValEl) pwValEl.appendChild(editBtn);

    if (viewBtn) viewBtn.textContent = 'Esconder';

  } catch (e) {
    console.error(e);
    setStatus("Erro ao obter senha: " + e.message, "error");
  }
}

async function deletePassword(id, row) {
  const ok = await showConfirmModal({ title: 'Confirmar exclusão', message: 'Tem certeza que deseja excluir esta senha?' });
  if (!ok) {
    return;
  }

  try {
    setStatus("Excluindo senha...");
    const resp = await apiRequest(`/passwords/${id}`, {
      method: "DELETE"
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || "Erro ao deletar senha");
    }

    const extra = row.nextElementSibling;
    if (extra && extra.classList.contains("password-row")) {
      extra.remove();
    }

    row.remove();

    allPasswords = allPasswords.filter(p => p.id !== id);

    updateEmptyState();

    const data = await resp.json().catch(() => null);
    setStatus(data?.message || "Senha deletada com sucesso.");
  } catch (e) {
    console.error(e);
    setStatus("Erro ao deletar senha: " + e.message, "error");
  }
}

// Start edit flow
async function startEditPassword(id) {
  if (!masterPasswordPlain) {
    setStatus("Senha mestra não está disponível no cliente.", "error");
    return;
  }

  const entry = allPasswords.find(p => p.id === id);
  if (!entry) {
    setStatus('Entrada não encontrada.', 'error');
    return;
  }

  try {
    if (!entry._decrypted_preview) {
      const resp = await apiRequest(`/passwords/${id}`, { method: 'GET' });
      if (!resp.ok) throw new Error('Erro ao buscar senha para edição');
      const data = await resp.json();
      entry._decrypted_preview = await decryptWithMasterPassword(data.encrypted_password, masterPasswordPlain);
    }
  } catch (e) {
    console.error(e);
    setStatus('Erro ao obter senha para edição: ' + e.message, 'error');
    return;
  }

  const result = await showEditPasswordModal(entry);
  if (!result) {
    setStatus('Edição cancelada pelo usuário.');
    return;
  }

  setStatus('Criptografando nova senha...');
  let encryptedBase64;
  try {
    encryptedBase64 = await encryptWithMasterPassword(result.password || '', masterPasswordPlain);
  } catch (e) {
    console.error(e);
    setStatus('Erro ao criptografar nova senha: ' + e.message, 'error');
    return;
  }

  const payload = {
    title: result.title,
    site: result.site,
    length: entry.length || 0,
    use_uppercase: entry.use_uppercase,
    use_lowercase: entry.use_lowercase,
    use_digits: entry.use_digits,
    use_special: entry.use_special,
    expiration_date: result.expiration_date,
    encrypted_password: encryptedBase64
  };

  try {
    setStatus('Atualizando senha no servidor...');
    const resp = await apiRequest(`/passwords/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || 'Erro ao atualizar senha');
    }

    const updated = await resp.json().catch(() => null);

    entry.title = payload.title;
    entry.site = payload.site;
    entry.expiration_date = payload.expiration_date;
    entry.encrypted_password = payload.encrypted_password;
    entry._decrypted_preview = result.password || '';

    const rows = Array.from(tbodyPasswords.querySelectorAll('tr'));
    for (const r of rows) {
      if (String(r.dataset.id) === String(id)) {
        const tds = r.children;
        if (tds[1]) tds[1].textContent = entry.title;
        if (tds[2]) tds[2].textContent = entry.site;
        if (tds[4]) tds[4].textContent = formatDate(entry.expiration_date);
        break;
      }
    }

    const mainRow = tbodyPasswords.querySelector(`tr[data-id="${id}"]`);
    if (mainRow) {
      const detail = mainRow.nextElementSibling;
      if (detail && detail.classList && detail.classList.contains('password-row')) {
        const pwDiv = detail.querySelector('.password-value');
        if (pwDiv) {
          const escaped = (entry._decrypted_preview || '').replace(/'/g, "\\'");
          pwDiv.innerHTML = `${entry._decrypted_preview}<button class="copy-btn" onclick="copyToClipboard('${escaped}', this)"> Copiar</button>`;
          const editBtn = document.createElement('button');
          editBtn.textContent = 'Editar';
          editBtn.className = 'primary';
          editBtn.style.marginLeft = '0.5rem';
          editBtn.addEventListener('click', () => startEditPassword(id));
          pwDiv.appendChild(editBtn);
        }
      }
    }

    setStatus('Senha atualizada com sucesso.');
  } catch (e) {
    console.error(e);
    setStatus('Erro ao atualizar senha: ' + e.message, 'error');
  }
}

// Form create
formCreatePassword.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!sessionToken) {
    setStatus("Você precisa estar logado.", "error");
    return;
  }
  if (!masterPasswordPlain) {
    setStatus("Senha mestra não está disponível no cliente.", "error");
    return;
  }

  const title = document.getElementById('title').value.trim();
  const site = document.getElementById('site').value.trim();
  let length = parseInt(document.getElementById('length').value, 10) || 16;
  const useUppercase = document.getElementById('use-uppercase').checked;
  const useLowercase = document.getElementById('use-lowercase').checked;
  const useDigits = document.getElementById('use-digits').checked;
  const useSpecial = document.getElementById('use-special').checked;
  const expirationInput = document.getElementById('expiration-date').value;
  const customPassword = document.getElementById('custom-password').value.trim() || null;

  let plainPassword;
  if (customPassword) {
    plainPassword = customPassword;
    length = customPassword.length;
  } else {
    try {
      plainPassword = generatePassword(length, useUppercase, useLowercase, useDigits, useSpecial);
    } catch (e) {
      setStatus(e.message, "error");
      return;
    }
  }

  setStatus("Criptografando senha no cliente...");

  let encryptedBase64;
  try {
    encryptedBase64 = await encryptWithMasterPassword(plainPassword, masterPasswordPlain);
  } catch (e) {
    console.error(e);
    setStatus("Erro ao criptografar a senha no cliente: " + e.message, "error");
    return;
  }

  const payload = {
    title,
    site,
    length,
    use_uppercase: useUppercase,
    use_lowercase: useLowercase,
    use_digits: useDigits,
    use_special: useSpecial,
    expiration_date: expirationInput ? new Date(expirationInput).toISOString() : null,
    custom_password: null,
    encrypted_password: encryptedBase64
  };

  setStatus("Criando senha...");

  try {
    const resp = await apiRequest("/passwords", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || "Erro ao criar senha");
    }

    const data = await resp.json();
    addPasswordRow(data);
    allPasswords.push(data);
    formCreatePassword.reset();
    document.getElementById('length').value = 16;
    document.getElementById('use-uppercase').checked = true;
    document.getElementById('use-lowercase').checked = true;
    document.getElementById('use-digits').checked = true;
    document.getElementById('use-special').checked = true;
    passwordStrengthBar.style.width = '0%';
    passwordStrengthText.textContent = '';
    updateEmptyState();
    setStatus("Senha criada com sucesso.");
  } catch (e) {
    console.error(e);
    setStatus("Erro ao criar senha: " + e.message, "error");
  }
});

// Password strength indicator
customPasswordInput.addEventListener('input', (e) => {
  const password = e.target.value;
  const result = calculatePasswordStrength(password);
  
  passwordStrengthBar.style.width = result.strength + '%';
  passwordStrengthBar.style.backgroundColor = result.color;
  passwordStrengthText.textContent = result.text;
  passwordStrengthText.style.color = result.color;
});

// Search functionality
searchInput.addEventListener('input', filterPasswords);
