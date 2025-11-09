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
        Cria uma nova sessão com a senha mestra
        
        Args:
            master_password: Senha mestra do usuário
            db_path: Caminho do banco de dados
            
        Returns:
            Token de sessão
        """
        try:
            pm = PasswordManager(master_password, db_path)
            token = secrets.token_urlsafe(32)
            self.sessions[token] = pm
            return token
        except Exception as e:
            raise ValueError(f"Erro ao criar sessão: {str(e)}")
    
    def get_password_manager(self, token: str) -> Optional[PasswordManager]:
        """
        Retorna o PasswordManager associado ao token
        
        Args:
            token: Token de sessão
            
        Returns:
            PasswordManager ou None se token inválido
        """
        return self.sessions.get(token)
    
    def remove_session(self, token: str):
        """
        Remove uma sessão
        
        Args:
            token: Token de sessão
        """
        self.sessions.pop(token, None)
    
    def is_valid_token(self, token: str) -> bool:
        """
        Verifica se um token é válido
        
        Args:
            token: Token de sessão
            
        Returns:
            True se válido, False caso contrário
        """
        return token in self.sessions


auth_manager = AuthManager()

