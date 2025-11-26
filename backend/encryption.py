from Crypto.Cipher import AES
from Crypto.Hash import SHA256
import os


class EncryptionManager:
    NONCE_SIZE = 12   # 96 bits para GCM
    TAG_SIZE = 16     # 128 bits

    def __init__(self, master_password: str):
        h = SHA256.new()
        h.update(master_password.encode())
        self.key = h.digest()

    def encrypt(self, plaintext: str) -> bytes:
        plaintext_bytes = plaintext.encode("utf-8")

        nonce = os.urandom(self.NONCE_SIZE)
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext_bytes)

        return nonce + tag + ciphertext

    def decrypt(self, blob: bytes) -> str:
        if len(blob) < self.NONCE_SIZE + self.TAG_SIZE:
            raise ValueError("Ciphertext muito curto")

        nonce = blob[:self.NONCE_SIZE]
        tag = blob[self.NONCE_SIZE:self.NONCE_SIZE + self.TAG_SIZE]
        ciphertext = blob[self.NONCE_SIZE + self.TAG_SIZE:]

        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)

        return plaintext.decode("utf-8")

    def get_metadata(self):
        return {
            "algorithm": "AES-256-GCM",
            "kdf": "PBKDF2",
            "kdf_hash": "SHA256",
            "kdf_iterations": self.KDF_ITERATIONS,
        }


def create_encryption_manager(master_password: str, salt: bytes = None) -> EncryptionManager:
    return EncryptionManager(master_password, salt)
