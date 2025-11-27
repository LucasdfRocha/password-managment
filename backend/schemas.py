from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# =======================
#   USER / AUTH
# =======================

class UserRegister(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user_id: int
    username: str
    message: str


class MessageResponse(BaseModel):
    success: bool
    message: str


# =======================
#   PASSWORDS
# =======================

class PasswordCreate(BaseModel):
    """
    Payload enviado pelo front-end ao criar senha.
    O encrypted_password vem em base64, gerado no cliente.
    """
    title: str
    site: str
    length: int
    use_uppercase: bool
    use_lowercase: bool
    use_digits: bool
    use_special: bool

    expiration_date: Optional[datetime] = None
    custom_password: Optional[str] = None
    encrypted_password: Optional[str] = None  # base64


class PasswordUpdate(BaseModel):
    """
    Payload para atualizar uma senha existente.
    Todos os campos são opcionais.
    """
    title: Optional[str] = None
    site: Optional[str] = None

    length: Optional[int] = None
    use_uppercase: Optional[bool] = None
    use_lowercase: Optional[bool] = None
    use_digits: Optional[bool] = None
    use_special: Optional[bool] = None

    expiration_date: Optional[datetime] = None

    # se quiser forçar nova geração/criptografia
    regenerate: bool = False

    custom_password: Optional[str] = None
    encrypted_password: Optional[str] = None  # base64


class PasswordResponse(BaseModel):
    """
    Resposta usada em listagem e criação/atualização de senhas.
    IMPORTANTE: o api.py precisa preencher TODOS esses campos.
    """
    id: int
    title: str
    site: str

    length: int
    use_uppercase: bool
    use_lowercase: bool
    use_digits: bool
    use_special: bool

    entropy: float
    entropy_level: str

    expiration_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class PasswordDetailResponse(BaseModel):
    """
    Resposta detalhada de uma senha específica (GET /passwords/{id}),
    incluindo o blob criptografado em base64.
    """
    id: int
    title: str
    site: str
    encrypted_password: str  # base64 da senha criptografada

    entropy: float
    expiration_date: Optional[datetime]
    created_at: datetime


# =======================
#   GERADOR DE SENHAS
# =======================

class PasswordGenerateRequest(BaseModel):
    length: int = 16
    use_uppercase: bool = True
    use_lowercase: bool = True
    use_digits: bool = True
    use_special: bool = True


class PasswordGenerateResponse(BaseModel):
    password: str
    entropy: float
