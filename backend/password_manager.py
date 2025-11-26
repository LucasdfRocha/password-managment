from datetime import datetime
from typing import List, Optional
from models import PasswordEntry
from database import DatabaseManager
from encryption import EncryptionManager
from password_generator import PasswordGenerator


class PasswordManager:
    """Gerenciador principal de senhas"""
    
    def __init__(self, master_password: str, db_path: str = "passwords.db"):
        """
        Inicializa o gerenciador de senhas
        
        Args:
            master_password: Senha mestra do usuário
            db_path: Caminho do banco de dados
        """
        self.encryption_manager = EncryptionManager(master_password)
        self.db_manager = DatabaseManager(db_path)
        self.user_id: Optional[int] = None  # Será definido durante autenticação
    
    def create_password(
        self,
        title: str,
        site: str,
        length: int = 16,
        use_uppercase: bool = True,
        use_lowercase: bool = True,
        use_digits: bool = True,
        use_special: bool = True,
        expiration_date: Optional[datetime] = None,
        custom_password: Optional[str] = None
    ) -> int:
        """
        Cria uma nova senha
        
        Args:
            title: Título da entrada
            site: Site relacionado
            length: Tamanho da senha
            use_uppercase: Usar letras maiúsculas
            use_lowercase: Usar letras minúsculas
            use_digits: Usar dígitos
            use_special: Usar caracteres especiais
            expiration_date: Data de expiração (opcional)
            custom_password: Senha customizada (opcional, se não fornecida será gerada)
            
        Returns:
            ID da entrada criada
        """
        if not self.user_id:
            raise ValueError("Usuário não autenticado")
        
        if custom_password:
            password = custom_password
            length = len(password)
        else:
            password = PasswordGenerator.generate(
                length, use_uppercase, use_lowercase, use_digits, use_special
            )
        
        entropy = PasswordGenerator.calculate_entropy(
            length, use_uppercase, use_lowercase, use_digits, use_special
        )
        
        now = datetime.now()
        entry = PasswordEntry(
            id=None,
            user_id=self.user_id,
            title=title,
            site=site,
            password="",
            length=length,
            use_uppercase=use_uppercase,
            use_lowercase=use_lowercase,
            use_digits=use_digits,
            use_special=use_special,
            entropy=entropy,
            expiration_date=expiration_date,
            created_at=now,
            updated_at=now
        )
        
        encrypted_password = self.encryption_manager.encrypt(password)
        entry_id = self.db_manager.create_entry(entry, encrypted_password)
        return entry_id
    
    def get_all_passwords(self) -> List[PasswordEntry]:
        """Retorna todas as senhas do usuário (sem descriptografar)"""
        if not self.user_id:
            raise ValueError("Usuário não autenticado")
        return self.db_manager.get_all_entries(self.user_id)
    
    def get_password(self, entry_id: int) -> Optional[tuple]:
        """
        Retorna uma senha descriptografada
        
        Args:
            entry_id: ID da entrada
            
        Returns:
            Tupla (PasswordEntry, senha_descriptografada) ou None
        """
        if not self.user_id:
            raise ValueError("Usuário não autenticado")
        
        entry = self.db_manager.get_entry_by_id(entry_id, self.user_id)
        if not entry:
            return None
        
        decrypted_password = self.encryption_manager.decrypt(entry.password)
        return (entry, decrypted_password)
    
    def update_password(
        self,
        entry_id: int,
        title: Optional[str] = None,
        site: Optional[str] = None,
        length: Optional[int] = None,
        use_uppercase: Optional[bool] = None,
        use_lowercase: Optional[bool] = None,
        use_digits: Optional[bool] = None,
        use_special: Optional[bool] = None,
        expiration_date: Optional[datetime] = None,
        regenerate: bool = False,
        custom_password: Optional[str] = None
    ) -> bool:
        """
        Atualiza uma senha
        
        Args:
            entry_id: ID da entrada
            title: Novo título (opcional)
            site: Novo site (opcional)
            length: Novo tamanho (opcional)
            use_uppercase: Usar maiúsculas (opcional)
            use_lowercase: Usar minúsculas (opcional)
            use_digits: Usar dígitos (opcional)
            use_special: Usar especiais (opcional)
            expiration_date: Nova data de expiração (opcional)
            regenerate: Se True, regenera a senha
            custom_password: Senha customizada (opcional)
            
        Returns:
            True se atualizado com sucesso, False caso contrário
        """
        if not self.user_id:
            raise ValueError("Usuário não autenticado")
        
        entry = self.db_manager.get_entry_by_id(entry_id, self.user_id)
        if not entry:
            return False
        
        if title is not None:
            entry.title = title
        if site is not None:
            entry.site = site
        if length is not None:
            entry.length = length
        if use_uppercase is not None:
            entry.use_uppercase = use_uppercase
        if use_lowercase is not None:
            entry.use_lowercase = use_lowercase
        if use_digits is not None:
            entry.use_digits = use_digits
        if use_special is not None:
            entry.use_special = use_special
        if expiration_date is not None:
            entry.expiration_date = expiration_date
        
        if regenerate or custom_password:
            if custom_password:
                password = custom_password
                entry.length = len(password)
            else:
                password = PasswordGenerator.generate(
                    entry.length,
                    entry.use_uppercase,
                    entry.use_lowercase,
                    entry.use_digits,
                    entry.use_special
                )
            
            entry.entropy = PasswordGenerator.calculate_entropy(
                entry.length,
                entry.use_uppercase,
                entry.use_lowercase,
                entry.use_digits,
                entry.use_special
            )
            encrypted_password = self.encryption_manager.encrypt(password)
        else:
            encrypted_password = entry.password
        
        entry.updated_at = datetime.now()
        self.db_manager.update_entry(entry_id, self.user_id, entry, encrypted_password)
        return True
    
    def delete_password(self, entry_id: int) -> bool:
        """
        Deleta uma senha
        
        Args:
            entry_id: ID da entrada
            
        Returns:
            True se deletado com sucesso, False caso contrário
        """
        if not self.user_id:
            raise ValueError("Usuário não autenticado")
        
        entry = self.db_manager.get_entry_by_id(entry_id, self.user_id)
        if not entry:
            return False
        
        self.db_manager.delete_entry(entry_id, self.user_id)
        return True

