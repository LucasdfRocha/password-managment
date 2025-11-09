"""
Gerenciamento do banco de dados SQLite
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Optional
from models import PasswordEntry


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
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                updated_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_entry(self, entry: PasswordEntry, encrypted_password: bytes) -> int:
        """
        Cria uma nova entrada de senha
        
        Args:
            entry: Objeto PasswordEntry
            encrypted_password: Senha criptografada em bytes
            
        Returns:
            ID da entrada criada
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO password_entries 
            (title, site, password_encrypted, length, use_uppercase, use_lowercase, 
             use_digits, use_special, entropy, expiration_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            entry.created_at.isoformat(),
            entry.updated_at.isoformat()
        ))
        
        entry_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return entry_id
    
    def get_all_entries(self) -> List[PasswordEntry]:
        """Retorna todas as entradas de senha"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM password_entries ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        entries = []
        for row in rows:
            entries.append(self._row_to_entry(row))
        return entries
    
    def get_entry_by_id(self, entry_id: int) -> Optional[PasswordEntry]:
        """
        Retorna uma entrada por ID
        
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
            return self._row_to_entry(row)
        return None
    
    def update_entry(self, entry_id: int, entry: PasswordEntry, encrypted_password: bytes):
        """
        Atualiza uma entrada de senha
        
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
    
    def delete_entry(self, entry_id: int):
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
    
    def _row_to_entry(self, row) -> PasswordEntry:
        """Converte uma linha do banco em PasswordEntry"""
        return PasswordEntry(
            id=row[0],
            title=row[1],
            site=row[2],
            password=row[3],
            length=row[4],
            use_uppercase=bool(row[5]),
            use_lowercase=bool(row[6]),
            use_digits=bool(row[7]),
            use_special=bool(row[8]),
            entropy=row[9],
            expiration_date=datetime.fromisoformat(row[10]) if row[10] else None,
            created_at=datetime.fromisoformat(row[11]),
            updated_at=datetime.fromisoformat(row[12])
        )

