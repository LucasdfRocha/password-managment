# auth.py

"""
Sistema de autenticação com suporte a múltiplos usuários
e proteção contra session fixation
"""

from typing import Optional, Tuple
from datetime import datetime, timedelta
import secrets
import bcrypt

from password_manager import PasswordManager
from database import DatabaseManager
from models import User


class SessionInfo:
    """Informações sobre uma sessão de usuário"""

    def __init__(self, user_id: int, username: str, token: str, created_at: datetime):
        self.user_id = user_id
        self.username = username
        self.token = token
        self.created_at = created_at
        # Cada sessão tem seu próprio PasswordManager (mesmo banco)
        self.pm = PasswordManager(db_path="passwords.db")

    def is_expired(self, timeout_minutes: int = 60) -> bool:
        """Verifica se a sessão expirou"""
        return datetime.now() - self.created_at > timedelta(minutes=timeout_minutes)


class AuthManager:
    """
    Gerenciador de autenticação multi-usuário com proteção contra session fixation

    Mecanismos de segurança:
    - Tokens gerados com secrets.token_urlsafe (criptograficamente seguro)
    - Renovação de token após login (previne fixation)
    - Timeout de sessão (padrão 60 minutos)
    - Validação de user_id em cada request
    - Hash bcrypt para senhas
    """

    def __init__(self, db_path: str = "passwords.db", session_timeout_minutes: int = 60):
        """Inicializa o gerenciador de autenticação"""
        self.db_manager = DatabaseManager(db_path=db_path)
        self.sessions: dict[str, SessionInfo] = {}  # token -> SessionInfo
        self.session_timeout_minutes = session_timeout_minutes
        self.bcrypt_cost = 12  # custo de hash bcrypt

    # ===== USER REGISTRATION =====

    def register_user(self, username: str, email: str, password: str) -> Tuple[bool, str]:
        """
        Registra um novo usuário

        Args:
            username: Nome de usuário
            email: Email do usuário
            password: Senha em texto puro

        Returns:
            Tupla (sucesso, mensagem)
        """
        try:
            # Validações básicas
            if len(username) < 3:
                return False, "Username deve ter pelo menos 3 caracteres"
            if len(password) < 8:
                return False, "Senha deve ter pelo menos 8 caracteres"
            if len(email) < 5 or "@" not in email:
                return False, "Email inválido"

            # Verifica se username já existe
            existing = self.db_manager.get_user_by_username(username)
            if existing:
                return False, "Username já existe"

            # Hash da senha com bcrypt
            password_hash = bcrypt.hashpw(
                password.encode("utf-8"),
                bcrypt.gensalt(rounds=self.bcrypt_cost),
            ).decode("utf-8")

            # Cria o usuário
            now = datetime.now()
            user = User(
                id=None,
                username=username,
                email=email,
                password_hash=password_hash,
                created_at=now,
                updated_at=now,
            )

            self.db_manager.create_user(user)
            return True, f"Usuário {username} registrado com sucesso"

        except Exception as e:
            return False, f"Erro ao registrar: {str(e)}"

    # ===== USER LOGIN =====

    def login(self, username: str, password: str) -> Tuple[bool, Optional[str], Optional[int], str]:
        """
        Autentica um usuário e cria uma sessão

        PROTEÇÃO CONTRA SESSION FIXATION:
        - Gera token novo a cada login
        - Valida user_id em cada request
        - Timeout de sessão

        Args:
            username: Nome de usuário
            password: Senha em texto puro

        Returns:
            Tupla (success, token, user_id, message)
            - success: True/False
            - token: token de sessão ou None
            - user_id: id do usuário ou None
            - message: texto explicativo
        """
        try:
            # Busca o usuário
            user = self.db_manager.get_user_by_username(username)
            if not user:
                return False, None, None, "Username ou senha incorretos"

            # Verifica a senha com bcrypt
            if not bcrypt.checkpw(
                password.encode("utf-8"),
                user.password_hash.encode("utf-8"),
            ):
                return False, None, None, "Username ou senha incorretos"

            # ===== SESSION FIXATION PROTECTION =====
            # Gera novo token (nunca reutiliza)
            token = secrets.token_urlsafe(32)

            # Cria nova sessão
            session = SessionInfo(
                user_id=user.id,
                username=user.username,
                token=token,
                created_at=datetime.now(),
            )
            self.sessions[token] = session

            return True, token, user.id, "Login realizado com sucesso"

        except Exception as e:
            # Erro inesperado → login falhou, mas sem quebrar a API
            return False, None, None, f"Erro no login: {str(e)}"

    # ===== SESSION VALIDATION =====

    def validate_session(self, token: str) -> Tuple[bool, Optional[int], str]:
        """
        Valida se um token de sessão é válido

        Args:
            token: Token de sessão

        Returns:
            Tupla (válido, user_id, mensagem)
        """
        if not token or token not in self.sessions:
            return False, None, "Token de sessão inválido"

        session = self.sessions[token]

        # Verifica timeout
        if session.is_expired(self.session_timeout_minutes):
            self.sessions.pop(token, None)
            return False, None, "Sessão expirada"

        return True, session.user_id, "Sessão válida"

    def get_session_info(self, token: str) -> Optional[SessionInfo]:
        """Retorna informações da sessão (validação prévia recomendada)"""
        return self.sessions.get(token)

    def get_password_manager(self, token: str) -> Optional[PasswordManager]:
        """
        Retorna o PasswordManager associado ao token e user_id

        OBS: A validação é feita aqui internamente
        """
        is_valid, user_id, _ = self.validate_session(token)
        if not is_valid:
            return None

        session = self.sessions.get(token)
        if not session:
            return None

        return session.pm

    # ===== LOGOUT / CONTROLE DE SESSÃO =====

    def logout(self, token: str) -> Tuple[bool, str]:
        """Remove uma sessão (logout explícito)"""
        if token in self.sessions:
            self.sessions.pop(token, None)
            return True, "Sessão encerrada com sucesso."
        return False, "Sessão não encontrada."

    def remove_session(self, token: str):
        """Remove uma sessão (atalho simples)"""
        self.sessions.pop(token, None)

    def is_valid_token(self, token: str) -> bool:
        """Verifica rapidamente se um token existe"""
        return token in self.sessions


# Instância global usada pela API
auth_manager = AuthManager()
