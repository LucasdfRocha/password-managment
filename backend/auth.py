"""
Sistema de autenticação com JWT e gerenciamento de usuários
"""
from typing import Optional
from datetime import datetime, timedelta
import bcrypt
import jwt
from password_manager import PasswordManager
from database import DatabaseManager


class AuthManager:
    """Gerenciador de autenticação com JWT"""
    
    SECRET_KEY = "seu-secret-key-super-seguro-mudar-em-producao"  # TODO: Usar variável de ambiente
    ALGORITHM = "HS256"
    TOKEN_EXPIRATION_HOURS = 24
    
    def __init__(self):
        """Inicializa o gerenciador de autenticação"""
        self.db_manager = DatabaseManager()
        self.sessions: dict[str, dict] = {}  # token -> {user_id, user_obj, pm}
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash seguro de senha usando bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode(), salt).decode()
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verifica se a senha corresponde ao hash"""
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    
    def register_user(self, username: str, email: str, password: str) -> str:
        """
        Registra um novo usuário
        
        Args:
            username: Nome de usuário
            email: Email do usuário
            password: Senha em plaintext
            
        Returns:
            Token JWT
            
        Raises:
            ValueError: Se o usuário já existe ou dados inválidos
        """
        # Validação básica
        if not username or len(username) < 3:
            raise ValueError("Username deve ter pelo menos 3 caracteres")
        if not email or "@" not in email:
            raise ValueError("Email inválido")
        if not password or len(password) < 6:
            raise ValueError("Senha deve ter pelo menos 6 caracteres")
        
        # Verifica se usuário já existe
        if self.db_manager.get_user_by_username(username):
            raise ValueError("Username já existe")
        
        # Cria novo usuário
        password_hash = self.hash_password(password)
        try:
            user_id = self.db_manager.create_user(username, email, password_hash)
        except Exception as e:
            raise ValueError(f"Erro ao criar usuário: {str(e)}")
        
        # Cria sessão e retorna token
        return self._create_session(user_id, username)
    
    def login(self, username: str, password: str) -> str:
        """
        Autentica um usuário com username e senha
        
        Args:
            username: Nome de usuário
            password: Senha em plaintext
            
        Returns:
            Token JWT
            
        Raises:
            ValueError: Se credenciais inválidas
        """
        user = self.db_manager.get_user_by_username(username)
        if not user:
            raise ValueError("Usuário não encontrado")
        
        if not self.verify_password(password, user.password_hash):
            raise ValueError("Senha incorreta")
        
        return self._create_session(user.id, user.username)
    
    def _create_session(self, user_id: int, username: str) -> str:
        """
        Cria uma nova sessão e retorna o token JWT
        
        Args:
            user_id: ID do usuário
            username: Nome de usuário
            
        Returns:
            Token JWT
        """
        # Cria token JWT
        payload = {
            "user_id": user_id,
            "username": username,
            "exp": datetime.utcnow() + timedelta(hours=self.TOKEN_EXPIRATION_HOURS)
        }
        token = jwt.encode(payload, self.SECRET_KEY, algorithm=self.ALGORITHM)
        
        # Armazena sessão em memória
        user = self.db_manager.get_user_by_id(user_id)
        pm = PasswordManager(user.username)  # Usa username como master password para criptografia
        pm.user_id = user_id  # Anexa user_id ao PM
        
        self.sessions[token] = {
            "user_id": user_id,
            "username": username,
            "password_manager": pm
        }
        
        return token
    
    def verify_token(self, token: str) -> Optional[dict]:
        """
        Verifica e decodifica um token JWT
        
        Args:
            token: Token JWT
            
        Returns:
            Payload do token ou None se inválido
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            # Remove sessão expirada
            self.sessions.pop(token, None)
            raise ValueError("Token expirado")
        except jwt.InvalidTokenError:
            raise ValueError("Token inválido")
    
    def get_password_manager(self, token: str) -> Optional[PasswordManager]:
        """
        Retorna o PasswordManager associado ao token
        
        Args:
            token: Token JWT
            
        Returns:
            PasswordManager ou None se token inválido
        """
        session = self.sessions.get(token)
        if not session:
            return None
        return session.get("password_manager")
    
    def get_user_id_from_token(self, token: str) -> Optional[int]:
        """
        Retorna o user_id do token
        
        Args:
            token: Token JWT
            
        Returns:
            user_id ou None
        """
        session = self.sessions.get(token)
        if not session:
            return None
        return session.get("user_id")
    
    def logout(self, token: str):
        """
        Remove uma sessão (logout)
        
        Args:
            token: Token JWT
        """
        self.sessions.pop(token, None)


auth_manager = AuthManager()

