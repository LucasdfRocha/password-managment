from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
import base64
import os
import json


class EncryptionManager:
    """Gerenciador de criptografia usando AES-256-GCM"""
    KDF_ITERATIONS = 100000
    SALT_FILE = ".salt"
    KEY_SIZE = 32  # 256 bits para AES-256
    NONCE_SIZE = 12  # 96 bits recomendado para GCM

    def __init__(self, master_password: str, salt: bytes = None):
        if salt is None:
            salt = self._load_or_create_salt()
        self.salt = salt
        self.master_password = master_password
        self._key = self._derive_key()

    def _load_or_create_salt(self) -> bytes:
        if os.path.exists(self.SALT_FILE):
            try:
                with open(self.SALT_FILE, 'r') as f:
                    data = json.load(f)
                    return base64.b64decode(data['salt'])
            except Exception:
                pass

        salt = os.urandom(16)
        self._save_salt(salt)
        return salt

    def _save_salt(self, salt: bytes):
        with open(self.SALT_FILE, 'w') as f:
            json.dump({'salt': base64.b64encode(salt).decode()}, f)

    def _derive_key(self) -> bytes:
        return PBKDF2(
            self.master_password.encode(),
            self.salt,
            dkLen=self.KEY_SIZE,
            count=self.KDF_ITERATIONS,
            hmac_hash_module=SHA256
        )

    def encrypt(self, plaintext: str) -> bytes:
        plaintext_bytes = plaintext.encode('utf-8')

        cipher = AES.new(self._key, AES.MODE_GCM)

        ciphertext, tag = cipher.encrypt_and_digest(plaintext_bytes)

        return cipher.nonce + tag + ciphertext

    def decrypt(self, ciphertext: bytes) -> str:
        if len(ciphertext) < self.NONCE_SIZE + 16: #minimo
            raise ValueError("Ciphertext muito curto")

        # pega o nonce, tag e ciphertext
        nonce = ciphertext[:self.NONCE_SIZE]
        tag = ciphertext[self.NONCE_SIZE:self.NONCE_SIZE + 16]
        ciphertext_data = ciphertext[self.NONCE_SIZE + 16:]

        # cria o cipher GCM com o nonce
        cipher = AES.new(self._key, AES.MODE_GCM, nonce=nonce)

        plaintext_bytes = cipher.decrypt_and_verify(ciphertext_data, tag)
        return plaintext_bytes.decode('utf-8')

    def get_salt(self) -> bytes:
        return self.salt

    def get_metadata(self, include_salt: bool = True) -> dict:
        """Retorna metadados da configuração de criptografia usada por este manager.

        Args:
            include_salt: Se True inclui o salt codificado em base64.

        Returns:
            Dicionário com chaves: algorithm, kdf, kdf_hash, kdf_iterations, salt
        """
        meta = {
            "algorithm": "AES-256-GCM",
            "kdf": "PBKDF2",
            "kdf_hash": "SHA256",
            "kdf_iterations": self.KDF_ITERATIONS,
        }
        if include_salt:
            meta["salt"] = base64.b64encode(self.salt).decode() if self.salt else None
        return meta

    def derive_key(self, length: int = 32) -> bytes:
        """Deriva uma chave a partir da senha mestra e do salt.

        Essa chave pode ser usada para HMAC/assinatura ou outras operações.
        """
        return PBKDF2(
            self.master_password.encode(),
            self.salt,
            dkLen=length,
            count=self.KDF_ITERATIONS,
            hmac_hash_module=SHA256
        )


def create_encryption_manager(master_password: str, salt: bytes = None) -> EncryptionManager:
    return EncryptionManager(master_password, salt)

