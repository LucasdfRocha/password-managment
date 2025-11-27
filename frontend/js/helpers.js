// Utility helpers and UI helpers
function generatePassword(length, useUppercase, useLowercase, useDigits, useSpecial) {
  const UPPERCASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  const LOWERCASE = "abcdefghijklmnopqrstuvwxyz";
  const DIGITS = "0123456789";
  const SPECIAL = "!@#$%^&*()_+-=[]{}|;:,.<>?";

  let charset = "";
  if (useUppercase) charset += UPPERCASE;
  if (useLowercase) charset += LOWERCASE;
  if (useDigits) charset += DIGITS;
  if (useSpecial) charset += SPECIAL;

  if (!charset) {
    throw new Error("Pelo menos um tipo de caractere deve ser selecionado.");
  }

  const passwordChars = [];

  if (useUppercase) passwordChars.push(UPPERCASE[Math.floor(Math.random() * UPPERCASE.length)]);
  if (useLowercase) passwordChars.push(LOWERCASE[Math.floor(Math.random() * LOWERCASE.length)]);
  if (useDigits) passwordChars.push(DIGITS[Math.floor(Math.random() * DIGITS.length)]);
  if (useSpecial) passwordChars.push(SPECIAL[Math.floor(Math.random() * SPECIAL.length)]);

  while (passwordChars.length < length) {
    const idx = Math.floor(Math.random() * charset.length);
    passwordChars.push(charset[idx]);
  }

  for (let i = passwordChars.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [passwordChars[i], passwordChars[j]] = [passwordChars[j], passwordChars[i]];
  }

  return passwordChars.join("");
}

function setStatus(message, type = "ok") {
  statusEl.textContent = message;
  statusEl.className = "";
  if (type === "ok") statusEl.classList.add("ok");
  if (type === "error") statusEl.classList.add("error");
}

function showApp() {
  loginSection.classList.add('hidden');
  appSection.classList.remove('hidden');
}

function showLogin() {
  appSection.classList.add('hidden');
  loginSection.classList.remove('hidden');
  tbodyPasswords.innerHTML = "";
  allPasswords = [];
  searchInput.value = "";
}

function formatDate(isoString) {
  if (!isoString) return "-";
  try {
    const d = new Date(isoString);
    return d.toLocaleString('pt-BR');
  } catch (e) {
    return isoString;
  }
}

function getEntropyBadge(level) {
  const levelLower = level.toLowerCase();
  if (levelLower.includes('fraca') || levelLower.includes('weak')) {
    return 'weak';
  } else if (levelLower.includes('média') || levelLower.includes('medium') || levelLower.includes('moderate')) {
    return 'medium';
  } else {
    return 'strong';
  }
}

function calculatePasswordStrength(password) {
  if (!password) return { strength: 0, text: '', color: '' };
  
  let strength = 0;
  
  if (password.length >= 8) strength += 1;
  if (password.length >= 12) strength += 1;
  if (password.length >= 16) strength += 1;
  
  if (/[a-z]/.test(password)) strength += 1;
  if (/[A-Z]/.test(password)) strength += 1;
  if (/[0-9]/.test(password)) strength += 1;
  if (/[^a-zA-Z0-9]/.test(password)) strength += 1;
  
  const normalized = Math.min(strength / 7, 1);
  let text = '';
  let color = '';
  
  if (normalized < 0.3) {
    text = 'Muito fraca';
    color = '#ef4444';
  } else if (normalized < 0.5) {
    text = 'Fraca';
    color = '#f59e0b';
  } else if (normalized < 0.7) {
    text = 'Média';
    color = '#eab308';
  } else if (normalized < 0.9) {
    text = 'Forte';
    color = '#10b981';
  } else {
    text = 'Muito forte';
    color = '#059669';
  }
  
  return { strength: normalized * 100, text, color };
}

async function copyToClipboard(text, button) {
  try {
    await navigator.clipboard.writeText(text);
    const originalText = button.textContent;
    button.textContent = 'Copiado!';
    button.classList.add('copied');
    setTimeout(() => {
      button.textContent = originalText;
      button.classList.remove('copied');
    }, 2000);
  } catch (e) {
    console.error('Erro ao copiar:', e);
    setStatus('Erro ao copiar para área de transferência', 'error');
  }
}

function updateEmptyState() {
  const hasRows = tbodyPasswords.children.length > 0;
  if (hasRows) {
    emptyState.classList.add('hidden');
  } else {
    emptyState.classList.remove('hidden');
  }
}

function filterPasswords() {
  const searchTerm = searchInput.value.toLowerCase().trim();
  
  tbodyPasswords.innerHTML = ''; // garante que limpa sempre

  if (!searchTerm) {
    allPasswords.forEach(entry => addPasswordRow(entry));
    updateEmptyState();
    return;
  }
  
  const filtered = allPasswords.filter(entry => 
    entry.title.toLowerCase().includes(searchTerm) ||
    entry.site.toLowerCase().includes(searchTerm)
  );
  
  filtered.forEach(entry => addPasswordRow(entry));
  updateEmptyState();
}

// expose copy helper globally
window.copyToClipboard = copyToClipboard;
