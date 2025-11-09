"""
Modelos de dados para o gerenciador de senhas
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PasswordEntry:
    """Modelo para uma entrada de senha"""
    id: Optional[int]
    title: str
    site: str
    password: str  # criptografada
    length: int
    use_uppercase: bool
    use_lowercase: bool
    use_digits: bool
    use_special: bool
    entropy: float
    expiration_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

