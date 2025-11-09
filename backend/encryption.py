"""
Sistema de criptografia para senhas
"""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import os
import json


class EncryptionManager:
    """Gerenciador de criptografia usando Fernet (AES 128)"""
    
    SALT_FILE = ".salt"
    
    def __init__(self, master_password: str, salt: bytes = None):
        """
        Inicializa o gerenciador de criptografia
        
        Args:
            master_password: Senha mestra do usuário
            salt: Salt para derivação de chave (opcional, será carregado/gerado automaticamente)
        """
        if salt is None:
            salt = self._load_or_create_salt()
        self.salt = salt
        self.master_password = master_password
        self._fernet = None
        self._initialize_fernet()
    
    def _load_or_create_salt(self) -> bytes:
        """
        Carrega o salt do arquivo ou cria um novo se não existir
        
        Returns:
            Salt em bytes
        """
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
        """Salva o salt em um arquivo"""
        with open(self.SALT_FILE, 'w') as f:
            json.dump({'salt': base64.b64encode(salt).decode()}, f)
    
    def _initialize_fernet(self):
        """Inicializa o objeto Fernet com a chave derivada da senha mestra"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_password.encode()))
        self._fernet = Fernet(key)
    
    def encrypt(self, plaintext: str) -> bytes:
        """Criptografa um texto"""
        return self._fernet.encrypt(plaintext.encode())
    
    def decrypt(self, ciphertext: bytes) -> str:
        """Descriptografa um texto"""
        return self._fernet.decrypt(ciphertext).decode()
    
    def get_salt(self) -> bytes:
        """Retorna o salt usado"""
        return self.salt


def create_encryption_manager(master_password: str, salt: bytes = None) -> EncryptionManager:
    """Factory function para criar um EncryptionManager"""
    return EncryptionManager(master_password, salt)

