from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2, HKDF
from Crypto.Hash import SHA256
import os
import base64
from typing import Union


class EncryptionManager:
    NONCE_SIZE = 12
    TAG_SIZE = 16
    KEY_SIZE = 32
    SALT_SIZE = 16
    KDF_ITERATIONS = 300000

    def __init__(self, master_password: str, salt: Union[bytes, str, None] = None):
        self.master_password = master_password
        if salt is None:
            self.salt = os.urandom(self.SALT_SIZE)
        elif isinstance(salt, str):
            self.salt = base64.b64decode(salt)
        else:
            self.salt = salt

        self.key = PBKDF2(
            self.master_password.encode(),
            self.salt,
            dkLen=self.KEY_SIZE,
            count=self.KDF_ITERATIONS,
            hmac_hash_module=SHA256
        )

    def encrypt(self, plaintext: str) -> bytes:
        plaintext_bytes = plaintext.encode("utf-8")

        nonce = os.urandom(self.NONCE_SIZE)
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce, mac_len=self.TAG_SIZE)

        ciphertext, tag = cipher.encrypt_and_digest(plaintext_bytes)

        return self.salt + nonce + tag + ciphertext

    def decrypt(self, blob: bytes) -> str:
        offset = 0
        salt = blob[offset:offset+self.SALT_SIZE]
        offset += self.SALT_SIZE

        nonce = blob[offset:offset+self.NONCE_SIZE]
        offset += self.NONCE_SIZE

        tag = blob[offset:offset+self.TAG_SIZE]
        offset += self.TAG_SIZE

        ciphertext = blob[offset:]

        key = PBKDF2(
            self.master_password.encode(),
            salt,
            dkLen=self.KEY_SIZE,
            count=self.KDF_ITERATIONS,
            hmac_hash_module=SHA256
        )

        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce, mac_len=self.TAG_SIZE)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)

        return plaintext.decode("utf-8")


    def get_metadata(self):
        return {
            "algorithm": "AES-256-GCM",
            "kdf": "PBKDF2",
            "kdf_hash": "SHA256",
            "kdf_iterations": self.KDF_ITERATIONS,
            "salt": base64.b64encode(self.salt).decode("utf-8"),
            "key_size": self.KEY_SIZE * 8,
        }
