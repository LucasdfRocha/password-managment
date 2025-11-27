// Crypto helpers (WebCrypto)
function bytesToBase64(bytes) {
  let binary = "";
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

function base64ToBytes(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

async function deriveAesKey(masterPassword, salt, iterations = 300000) {
  const enc = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey(
    "raw",
    enc.encode(masterPassword),
    { name: "PBKDF2" },
    false,
    ["deriveKey"]
  );

  const key = await crypto.subtle.deriveKey(
    {
      name: "PBKDF2",
      salt: salt,
      iterations: iterations,
      hash: "SHA-256",
    },
    keyMaterial,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"]
  );

  return key;
}

async function encryptWithMasterPassword(plaintext, masterPassword) {
  const enc = new TextEncoder();
  const plaintextBytes = enc.encode(plaintext);

  const SALT_SIZE = 16;
  const NONCE_SIZE = 12;
  const TAG_SIZE = 16;

  const salt = crypto.getRandomValues(new Uint8Array(SALT_SIZE));
  const nonce = crypto.getRandomValues(new Uint8Array(NONCE_SIZE));
  const key = await deriveAesKey(masterPassword, salt);

  const cipherBuffer = await crypto.subtle.encrypt(
    {
      name: "AES-GCM",
      iv: nonce,
      tagLength: 128,
    },
    key,
    plaintextBytes
  );

  const cipherBytes = new Uint8Array(cipherBuffer);

  // WebCrypto returns ciphertext || tag
  const ciphertext = cipherBytes.slice(0, cipherBytes.length - TAG_SIZE);
  const tag = cipherBytes.slice(cipherBytes.length - TAG_SIZE);

  const blob = new Uint8Array(
    salt.length + nonce.length + tag.length + ciphertext.length
  );

  blob.set(salt, 0);
  blob.set(nonce, salt.length);
  blob.set(tag, salt.length + nonce.length);
  blob.set(ciphertext, salt.length + nonce.length + tag.length);

  return bytesToBase64(blob);
}

async function decryptWithMasterPassword(base64Blob, masterPassword) {
  const blob = base64ToBytes(base64Blob);

  const SALT_SIZE = 16;
  const NONCE_SIZE = 12;
  const TAG_SIZE = 16;

  let offset = 0;
  const salt = blob.slice(offset, offset + SALT_SIZE);
  offset += SALT_SIZE;

  const nonce = blob.slice(offset, offset + NONCE_SIZE);
  offset += NONCE_SIZE;

  const tag = blob.slice(offset, offset + TAG_SIZE);
  offset += TAG_SIZE;

  const ciphertext = blob.slice(offset);

  const key = await deriveAesKey(masterPassword, salt);

  const cipherPlusTag = new Uint8Array(ciphertext.length + tag.length);
  cipherPlusTag.set(ciphertext, 0);
  cipherPlusTag.set(tag, ciphertext.length);

  const plainBuffer = await crypto.subtle.decrypt(
    {
      name: "AES-GCM",
      iv: nonce,
      tagLength: 128,
    },
    key,
    cipherPlusTag
  );

  return new TextDecoder().decode(plainBuffer);
}

async function encryptPayloadWithWalletPassword(plaintextJson, walletPassword, iterations = 300000) {
  const encoder = new TextEncoder();
  const SALT_SIZE = 16;
  const NONCE_SIZE = 12;
  const salt = crypto.getRandomValues(new Uint8Array(SALT_SIZE));
  const nonce = crypto.getRandomValues(new Uint8Array(NONCE_SIZE));

  const key = await deriveAesKey(walletPassword, salt, iterations);

  const cipherBuf = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv: nonce, tagLength: 128 },
    key,
    encoder.encode(plaintextJson)
  );

  const cipherBytes = new Uint8Array(cipherBuf);
  return {
    ciphertext_b64: bytesToBase64(cipherBytes),
    salt_b64: bytesToBase64(salt),
    nonce_b64: bytesToBase64(nonce),
    kdf_iterations: iterations
  };
}

async function decryptPayloadWithWalletPassword(ciphertext_b64, walletPassword, salt_b64, nonce_b64, iterations = 300000) {
  const decoder = new TextDecoder();
  const salt = base64ToBytes(salt_b64);
  const nonce = base64ToBytes(nonce_b64);
  const cipherBytes = base64ToBytes(ciphertext_b64);

  const key = await deriveAesKey(walletPassword, salt, iterations);

  const plainBuf = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: nonce, tagLength: 128 },
    key,
    cipherBytes
  );

  return decoder.decode(plainBuf);
}
