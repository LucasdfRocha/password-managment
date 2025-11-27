"""
Gerenciamento do banco de dados SQLite
"""
import sqlite3
from datetime import datetime
from typing import List, Optional

from models import PasswordEntry, User


class DatabaseManager:
    """Gerenciador do banco de dados SQLite"""
    
    def __init__(self, db_path: str = "passwords.db"):
        """
        Inicializa o gerenciador do banco de dados
        
        Args:
            db_path: Caminho do arquivo do banco de dados
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Inicializa o banco de dados criando as tabelas necessárias"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de usuários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Tabela de senhas com FK para user
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                site TEXT NOT NULL,
                password_encrypted BLOB NOT NULL,
                length INTEGER NOT NULL,
                use_uppercase INTEGER NOT NULL,
                use_lowercase INTEGER NOT NULL,
                use_digits INTEGER NOT NULL,
                use_special INTEGER NOT NULL,
                entropy REAL NOT NULL,
                expiration_date TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        conn.close()
    
    # ======================================================================
    # USER OPERATIONS
    # ======================================================================
    
    def create_user(self, user: User) -> int:
        """
        Cria um novo usuário.
        
        Raises:
            sqlite3.IntegrityError: Se username ou email já existem.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user.username,
                user.email,
                user.password_hash,
                user.created_at.isoformat(),
                user.updated_at.isoformat()
            ))
            
            user_id = cursor.lastrowid
            conn.commit()
            return user_id
        finally:
            conn.close()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Busca um usuário por username"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(
                id=row[0],
                username=row[1],
                email=row[2],
                password_hash=row[3],
                created_at=datetime.fromisoformat(row[4]),
                updated_at=datetime.fromisoformat(row[5])
            )
        return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Busca um usuário por ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(
                id=row[0],
                username=row[1],
                email=row[2],
                password_hash=row[3],
                created_at=datetime.fromisoformat(row[4]),
                updated_at=datetime.fromisoformat(row[5])
            )
        return None
    
    # ======================================================================
    # PASSWORD OPERATIONS
    # ======================================================================
    
    def create_entry(self, entry: PasswordEntry, encrypted_password: bytes) -> int:
        """
        Cria uma nova entrada de senha.
        
        Args:
            entry: Objeto PasswordEntry (metadados)
            encrypted_password: Senha criptografada em bytes
            
        Returns:
            ID da entrada criada
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO password_entries 
            (user_id, title, site, password_encrypted, length, use_uppercase, use_lowercase, 
             use_digits, use_special, entropy, expiration_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.user_id,
            entry.title,
            entry.site,
            encrypted_password,
            entry.length,
            1 if entry.use_uppercase else 0,
            1 if entry.use_lowercase else 0,
            1 if entry.use_digits else 0,
            1 if entry.use_special else 0,
            entry.entropy,
            entry.expiration_date.isoformat() if entry.expiration_date else None,
            entry.created_at.isoformat(),
            entry.updated_at.isoformat()
        ))
        
        entry_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return entry_id
    
    def get_all_entries_for_user(self, user_id: int) -> List[PasswordEntry]:
        """Retorna todas as entradas de senha de um usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM password_entries WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        entries: List[PasswordEntry] = []
        for row in rows:
            entries.append(PasswordEntry(
                id=row[0],
                user_id=row[1],
                title=row[2],
                site=row[3],
                password=row[4],  # password_encrypted (BLOB)
                length=row[5],
                use_uppercase=bool(row[6]),
                use_lowercase=bool(row[7]),
                use_digits=bool(row[8]),
                use_special=bool(row[9]),
                entropy=row[10],
                expiration_date=datetime.fromisoformat(row[11]) if row[11] else None,
                created_at=datetime.fromisoformat(row[12]),
                updated_at=datetime.fromisoformat(row[13])
            ))
        return entries
    
    def get_entry_by_id(self, entry_id: int) -> Optional[PasswordEntry]:
        """
        Retorna uma entrada por ID.
        
        Args:
            entry_id: ID da entrada
            
        Returns:
            PasswordEntry ou None se não encontrado
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM password_entries WHERE id = ?", (entry_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return PasswordEntry(
                id=row[0],
                user_id=row[1],
                title=row[2],
                site=row[3],
                password=row[4],  # password_encrypted (BLOB)
                length=row[5],
                use_uppercase=bool(row[6]),
                use_lowercase=bool(row[7]),
                use_digits=bool(row[8]),
                use_special=bool(row[9]),
                entropy=row[10],
                expiration_date=datetime.fromisoformat(row[11]) if row[11] else None,
                created_at=datetime.fromisoformat(row[12]),
                updated_at=datetime.fromisoformat(row[13])
            )
        return None
    
    def update_entry(self, entry_id: int, entry: PasswordEntry, encrypted_password: bytes) -> None:
        """
        Atualiza uma entrada de senha.
        
        Args:
            entry_id: ID da entrada
            entry: Objeto PasswordEntry atualizado
            encrypted_password: Senha criptografada em bytes
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE password_entries 
            SET title = ?, site = ?, password_encrypted = ?, length = ?,
                use_uppercase = ?, use_lowercase = ?, use_digits = ?, use_special = ?,
                entropy = ?, expiration_date = ?, updated_at = ?
            WHERE id = ?
        """, (
            entry.title,
            entry.site,
            encrypted_password,
            entry.length,
            1 if entry.use_uppercase else 0,
            1 if entry.use_lowercase else 0,
            1 if entry.use_digits else 0,
            1 if entry.use_special else 0,
            entry.entropy,
            entry.expiration_date.isoformat() if entry.expiration_date else None,
            entry.updated_at.isoformat(),
            entry_id
        ))
        
        conn.commit()
        conn.close()
    
    def delete_entry(self, entry_id: int) -> None:
        """
        Deleta uma entrada de senha
        
        Args:
            entry_id: ID da entrada
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM password_entries WHERE id = ?", (entry_id,))
        conn.commit()
        conn.close()
