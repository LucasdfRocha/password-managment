from typing import Optional
from password_manager import PasswordManager
import secrets
import hashlib
import os


class AuthManager:
    def __init__(self):
        self.sessions: dict[str, PasswordManager] = {}

    def _generate_user_id(self, master_password: str) -> str:
        user_hash = hashlib.sha256(master_password.encode()).hexdigest()
        return user_hash[:16]

    def _get_storage_file_path(self, user_id: str, storage_dir: str = "data") -> str:
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir, exist_ok=True)

        return os.path.join(storage_dir, f"passwords_user_{user_id}.enc.json")

    def create_session(
        self, master_password: str, storage_file: Optional[str] = None
    ) -> str:
        try:
            if storage_file is None:
                user_id = self._generate_user_id(master_password)
                storage_file = self._get_storage_file_path(user_id)

            pm = PasswordManager(master_password, storage_file)
            token = secrets.token_urlsafe(32)
            self.sessions[token] = pm
            return token
        except Exception as e:
            raise ValueError(f"Erro ao criar sessão: {str(e)}")

    def get_password_manager(self, token: str) -> Optional[PasswordManager]:
        return self.sessions.get(token)

    def remove_session(self, token: str):
        self.sessions.pop(token, None)

    def is_valid_token(self, token: str) -> bool:
        return token in self.sessions


auth_manager = AuthManager()
