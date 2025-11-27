// Wallet export / import handlers
btnWalletExport.addEventListener('click', async () => {
  if (!masterPasswordPlain) {
    setStatus("Você precisa estar logado para exportar a wallet.", "error");
    return;
  }

  setStatus("Preparando exportação da wallet...");

  const resp = await apiRequest("/wallet/export", { method: "GET" });
  const data = await resp.json();

  const decryptedEntries = [];
  for (const e of data.entries) {
    const decrypted = await decryptWithMasterPassword(e.encrypted_password, masterPasswordPlain);
    decryptedEntries.push({
      title: e.title,
      site: e.site,
      password: decrypted,
      length: e.length,
      use_uppercase: e.use_uppercase,
      use_lowercase: e.use_lowercase,
      use_digits: e.use_digits,
      use_special: e.use_special,
      entropy: e.entropy,
      expiration_date: e.expiration_date,
      created_at: e.created_at,
      updated_at: e.updated_at
    });
  }

  const payload = { version: "1.0", entries: decryptedEntries };
  const payloadJson = JSON.stringify(payload, null, 2);

  const walletPassword = await showWalletPasswordModal({ title: 'Escolha uma senha para o arquivo wallet', confirm: true });
  if (!walletPassword) {
    setStatus('Exportação cancelada pelo usuário.', 'error');
    return;
  }

  setStatus('Criptografando payload do wallet...');
  const encResult = await encryptPayloadWithWalletPassword(payloadJson, walletPassword, 300000);

  const meta = {
    wallet_format_version: "1.0",
    app: { name: "password-managment", version: "1.0" },
    exported_at: new Date().toISOString(),
    encryption: {
      algorithm: "AES-GCM",
      kdf: "PBKDF2",
      kdf_hash: "SHA-256",
      kdf_iterations: encResult.kdf_iterations,
      salt: encResult.salt_b64,
      nonce: encResult.nonce_b64,
      tag_bytes: 16,
    },
    serialization: { format: "json", encoding: "utf-8", indent: 2 }
  };

  const walletFile = {
    meta,
    data: {
      entries_encrypted: encResult.ciphertext_b64
    }
  };

  const blob = new Blob([JSON.stringify(walletFile, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "wallet.json";
  a.click();

  setStatus("Wallet exportada com sucesso.");
});

btnWalletImport.addEventListener('click', () => {
  walletFileInput.click();
});

walletFileInput.addEventListener('change', async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  const text = await file.text();
  const json = JSON.parse(text);

  let entriesSource = null;
  if (json && json.data && json.data.entries_encrypted) {
    try {
      const walletPassword = await showWalletPasswordModal({ title: 'Digite a senha do wallet para importar', confirm: false });
      if (!walletPassword) {
        setStatus('Importação cancelada pelo usuário.', 'error');
        return;
      }

      const encMeta = json.meta && json.meta.encryption ? json.meta.encryption : {};
      const iterations = encMeta.kdf_iterations || 300000;
      const salt_b64 = encMeta.salt;
      const nonce_b64 = encMeta.nonce;

      if (!salt_b64 || !nonce_b64) {
        setStatus('Formato de wallet inválido: metadados de criptografia ausentes.', 'error');
        return;
      }

      const plaintext = await decryptPayloadWithWalletPassword(json.data.entries_encrypted, walletPassword, salt_b64, nonce_b64, iterations);
      const parsed = JSON.parse(plaintext);
      if (!parsed || !Array.isArray(parsed.entries)) {
        setStatus('Arquivo de wallet descriptografado mas formato inválido.', 'error');
        return;
      }

      entriesSource = parsed.entries;
    } catch (e) {
      console.error('Erro ao descriptografar wallet:', e);
      setStatus('Erro ao descriptografar o arquivo do wallet: senha incorreta ou arquivo inválido.', 'error');
      return;
    }
  } else if (json && json.data && Array.isArray(json.data.entries)) {
    if (json.hmac && json.meta && json.meta.hmac) {
      try {
        const walletPassword = await showWalletPasswordModal({ title: 'Digite a senha do wallet para verificar assinatura', confirm: false });
        if (!walletPassword) {
          setStatus('Importação cancelada pelo usuário.', 'error');
          return;
        }

        const encoder = new TextEncoder();
        const salt = base64ToBytes(json.meta.hmac.salt);
        const iterations = json.meta.hmac.kdf_iterations || 300000;
        const pwKey = await crypto.subtle.importKey('raw', encoder.encode(walletPassword), { name: 'PBKDF2' }, false, ['deriveKey']);
        const hmacKey = await crypto.subtle.deriveKey(
          { name: 'PBKDF2', salt: salt, iterations: iterations, hash: 'SHA-256' },
          pwKey,
          { name: 'HMAC', hash: 'SHA-256' },
          false,
          ['verify']
        );

        const payloadJson = JSON.stringify(json.data, null, 2);
        const sig = base64ToBytes(json.hmac);
        const ok = await crypto.subtle.verify('HMAC', hmacKey, sig, encoder.encode(payloadJson));
        if (!ok) {
          setStatus('HMAC inválido: arquivo corrompido ou senha do wallet incorreta.', 'error');
          return;
        }
      } catch (e) {
        console.error('Erro ao verificar HMAC:', e);
        setStatus('Erro ao verificar assinatura do arquivo.', 'error');
        return;
      }
    }

    entriesSource = json.data.entries;
  } else if (json && Array.isArray(json.entries)) {
    entriesSource = json.entries;
  } else {
    setStatus('Formato de wallet desconhecido.', 'error');
    return;
  }

  const payloadToServer = { entries: [] };
  for (const e of entriesSource) {
    const encrypted = await encryptWithMasterPassword(e.password, masterPasswordPlain);
    payloadToServer.entries.push({
      title: e.title,
      site: e.site,
      length: e.length,
      use_uppercase: e.use_uppercase,
      use_lowercase: e.use_lowercase,
      use_digits: e.use_digits,
      use_special: e.use_special,
      entropy: e.entropy,
      expiration_date: e.expiration_date,
      created_at: e.created_at,
      updated_at: e.updated_at,
      encrypted_password: encrypted
    });
  }

  const resp = await apiRequest("/wallet/import", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payloadToServer)
  });

  const result = await resp.json();
  setStatus(`Wallet importada: ${result.imported || result.message || 'ok'} senhas.`);
  await loadPasswords();
});
