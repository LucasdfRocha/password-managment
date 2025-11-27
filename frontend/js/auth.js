// Authentication handlers (register, login, logout)

// Toggle between login and register forms
btnToggleRegister.addEventListener('click', () => {
  document.getElementById('login-form').classList.add('hidden');
  document.getElementById('register-form').classList.remove('hidden');
  document.getElementById('form-title').textContent = 'Registrar';
});

btnToggleLogin.addEventListener('click', () => {
  document.getElementById('register-form').classList.add('hidden');
  document.getElementById('login-form').classList.remove('hidden');
  document.getElementById('form-title').textContent = 'Login';
});

// Toggle password visibility
togglePasswordBtn.addEventListener('click', () => {
  if (passwordInput.type === 'password') {
    passwordInput.type = 'text';
    togglePasswordBtn.textContent = 'Ocultar';
  } else {
    passwordInput.type = 'password';
    togglePasswordBtn.textContent = 'Mostrar';
  }
});

toggleRegisterPasswordBtn.addEventListener('click', () => {
  if (registerPasswordInput.type === 'password') {
    registerPasswordInput.type = 'text';
    toggleRegisterPasswordBtn.textContent = 'Ocultar';
  } else {
    registerPasswordInput.type = 'password';
    toggleRegisterPasswordBtn.textContent = 'Mostrar';
  }
});

// Register
btnRegister.addEventListener('click', async () => {
  const username = registerUsernameInput.value.trim();
  const email = registerEmailInput.value.trim();
  const password = registerPasswordInput.value.trim();

  if (!username || !email || !password) {
    setStatus("Preencha todos os campos.", "error");
    return;
  }

  btnRegister.disabled = true;
  setStatus("Registrando...");

  try {
    const resp = await fetch(API_BASE + "/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password })
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || "Erro no registro");
    }

    setStatus("Registro realizado com sucesso! Faça login.");
    registerUsernameInput.value = "";
    registerEmailInput.value = "";
    registerPasswordInput.value = "";
    
    // Volta para login
    document.getElementById('register-form').classList.add('hidden');
    document.getElementById('login-form').classList.remove('hidden');
    document.getElementById('form-title').textContent = 'Login';
  } catch (e) {
    console.error(e);
    setStatus("Erro no registro: " + e.message, "error");
  } finally {
    btnRegister.disabled = false;
  }
});

// Login
usernameInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') btnLogin.click();
});

passwordInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') btnLogin.click();
});

btnLogin.addEventListener('click', async () => {
  const username = usernameInput.value.trim();
  const password = passwordInput.value.trim();

  if (!username || !password) {
    setStatus("Digite username e senha.", "error");
    return;
  }

  btnLogin.disabled = true;
  setStatus("Fazendo login...");

  try {
    const resp = await fetch(API_BASE + "/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || "Falha no login");
    }

    const data = await resp.json();
    sessionToken = data.token;
    currentUserId = data.user_id;
    currentUsername = data.username;
    
    // Usa a senha como master password para descriptografar no cliente
    masterPasswordPlain = password;

    setStatus("Login realizado com sucesso.");
    usernameInput.value = "";
    passwordInput.value = "";
    currentUsernameSpan.textContent = currentUsername;
    showApp();
    await loadPasswords();
  } catch (e) {
    console.error(e);
    setStatus("Erro no login: " + e.message, "error");
  } finally {
    btnLogin.disabled = false;
  }
});

// Logout
btnLogout.addEventListener('click', async () => {
  if (!sessionToken) {
    showLogin();
    setStatus("Sessão encerrada.");
    return;
  }

  try {
    await apiRequest("/auth/logout", {
      method: "POST"
    });
  } catch (e) {
    console.warn("Erro no logout (ignorado):", e);
  } finally {
    sessionToken = null;
    masterPasswordPlain = null;
    currentUserId = null;
    currentUsername = null;
    currentUsernameSpan.textContent = "";
    showLogin();
    setStatus("Sessão encerrada.");
  }
});
