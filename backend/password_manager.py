# password_manager.py

from datetime import datetime
from typing import List, Optional
from models import PasswordEntry
from database import DatabaseManager
from password_generator import PasswordGenerator


class PasswordManager:
    """
    Gerenciador principal de senhas com isolamento por usuário.

    IMPORTANTE:
    - O servidor NÃO faz mais encrypt/decrypt.
    - Ele só armazena blobs criptografados vindos do cliente.
    - Cada usuário vê apenas suas próprias senhas.
    """

    def __init__(self, db_path: str = "passwords.db"):
        """
        Inicializa o gerenciador de senhas.
        
        Nota: user_id é passado a cada operação para garantir isolamento.
        """
        self.db_manager = DatabaseManager(db_path)
        self.encryption_manager = None

    # -------------------------------------------------------------------------
    # CREATE
    # -------------------------------------------------------------------------
    def create_password(
        self,
        user_id: int,
        title: str,
        site: str,
        length: int = 16,
        use_uppercase: bool = True,
        use_lowercase: bool = True,
        use_digits: bool = True,
        use_special: bool = True,
        expiration_date: Optional[datetime] = None,
        custom_password: Optional[str] = None,
        encrypted_password: Optional[bytes] = None,
    ) -> int:
        """
        Cria uma nova senha para um usuário.

        - O SERVIDOR NÃO GERA NEM CRIPTOGRAFA SENHA.
        - encrypted_password deve vir do CLIENTE (já criptografado).
        - user_id garante isolamento de dados.
        """
        if encrypted_password is None:
            raise ValueError(
                "encrypted_password é obrigatório; a senha deve ser criptografada no cliente."
            )

        now = datetime.now()

        entropy = PasswordGenerator.calculate_entropy(
            length, use_uppercase, use_lowercase, use_digits, use_special
        )

        entry = PasswordEntry(
            id=None,
            user_id=user_id,
            title=title,
            site=site,
            password=b"",
            length=length,
            use_uppercase=use_uppercase,
            use_lowercase=use_lowercase,
            use_digits=use_digits,
            use_special=use_special,
            entropy=entropy,
            expiration_date=expiration_date,
            created_at=now,
            updated_at=now,
        )

        entry_id = self.db_manager.create_entry(entry, encrypted_password)
        return entry_id

    # -------------------------------------------------------------------------
    # READ
    # -------------------------------------------------------------------------
    def get_all_passwords(self, user_id: int) -> List[PasswordEntry]:
        """
        Retorna todas as senhas de um usuário (sem descriptografar).
        
        ISOLAMENTO: Apenas senhas do user_id são retornadas.
        """
        return self.db_manager.get_all_entries_for_user(user_id)

    def get_password(self, entry_id: int, user_id: int) -> Optional[PasswordEntry]:
        """
        Retorna a entrada de senha SEM descriptografar.
        
        ISOLAMENTO: Verifica se entry_id pertence ao user_id.
        """
        entry = self.db_manager.get_entry_by_id(entry_id)
        if entry and entry.user_id == user_id:
            return entry
        return None

    # -------------------------------------------------------------------------
    # UPDATE
    # -------------------------------------------------------------------------
    def update_password(
        self,
        entry_id: int,
        user_id: int,
        title: Optional[str] = None,
        site: Optional[str] = None,
        length: Optional[int] = None,
        use_uppercase: Optional[bool] = None,
        use_lowercase: Optional[bool] = None,
        use_digits: Optional[bool] = None,
        use_special: Optional[bool] = None,
        expiration_date: Optional[datetime] = None,
        regenerate: bool = False,
        custom_password: Optional[str] = None,
        encrypted_password: Optional[bytes] = None,
    ) -> bool:
        """
        Atualiza metadados da senha e, opcionalmente, o blob criptografado.
        
        ISOLAMENTO: Verifica se entry_id pertence ao user_id antes de atualizar.
        """
        entry = self.db_manager.get_entry_by_id(entry_id)
        if not entry or entry.user_id != user_id:
            return False

        # Atualiza metadados
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

        # Recalcula entropia
        entry.entropy = PasswordGenerator.calculate_entropy(
            entry.length,
            entry.use_uppercase,
            entry.use_lowercase,
            entry.use_digits,
            entry.use_special,
        )

        # Decide qual blob criptografado salvar
        if encrypted_password is not None:
            encrypted_blob = encrypted_password
        else:
            encrypted_blob = entry.password

        entry.updated_at = datetime.now()
        self.db_manager.update_entry(entry_id, entry, encrypted_blob)
        return True

    # -------------------------------------------------------------------------
    # DELETE
    # -------------------------------------------------------------------------
    def delete_password(self, entry_id: int, user_id: int) -> bool:
        """
        Deleta uma senha.
        
        ISOLAMENTO: Verifica se entry_id pertence ao user_id antes de deletar.
        """
        entry = self.db_manager.get_entry_by_id(entry_id)
        if not entry or entry.user_id != user_id:
            return False

        self.db_manager.delete_entry(entry_id)
        return True
