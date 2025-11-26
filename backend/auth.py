# auth.py

"""
Sistema de autenticação simples para gerenciar sessões
"""

from typing import Optional
from password_manager import PasswordManager
import secrets


class AuthManager:
    """Gerenciador de autenticação simples baseado em tokens"""

    def __init__(self):
        """Inicializa o gerenciador de autenticação"""
        self.sessions: dict[str, PasswordManager] = {}

    def create_session(self, master_password: str, db_path: str = "passwords.db") -> str:
        """
        Cria uma nova sessão.

        OBS:
        - master_password ainda é recebido para manter a ideia de "senha mestra",
          mas NÃO é mais usado para gerar chave no servidor.
        - Toda a criptografia real acontece no CLIENTE.
        """
        try:
            # Agora o PasswordManager não precisa mais da master_password
            pm = PasswordManager(db_path=db_path)
            token = secrets.token_urlsafe(32)
            self.sessions[token] = pm
            return token
        except Exception as e:
            raise ValueError(f"Erro ao criar sessão: {str(e)}")

    def get_password_manager(self, token: str) -> Optional[PasswordManager]:
        """
        Retorna o PasswordManager associado ao token
        """
        return self.sessions.get(token)

    def remove_session(self, token: str):
        """
        Remove uma sessão
        """
        self.sessions.pop(token, None)

    def is_valid_token(self, token: str) -> bool:
        """
        Verifica se um token é válido
        """
        return token in self.sessions


auth_manager = AuthManager()
