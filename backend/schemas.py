"""
Schemas Pydantic para validação de dados da API
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PasswordCreate(BaseModel):
    """Schema para criação de senha"""
    title: str = Field(..., min_length=1, max_length=200)
    site: str = Field(..., min_length=1, max_length=200)
    length: int = Field(default=16, ge=4, le=128)
    use_uppercase: bool = Field(default=True)
    use_lowercase: bool = Field(default=True)
    use_digits: bool = Field(default=True)
    use_special: bool = Field(default=True)
    expiration_date: Optional[datetime] = None
    custom_password: Optional[str] = None
    encrypted_password: Optional[str] = None


class PasswordUpdate(BaseModel):
    """Schema para atualização de senha"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    site: Optional[str] = Field(None, min_length=1, max_length=200)
    length: Optional[int] = Field(None, ge=4, le=128)
    use_uppercase: Optional[bool] = None
    use_lowercase: Optional[bool] = None
    use_digits: Optional[bool] = None
    use_special: Optional[bool] = None
    expiration_date: Optional[datetime] = None
    regenerate: bool = Field(default=False)
    custom_password: Optional[str] = None


class PasswordResponse(BaseModel):
    """Schema de resposta para senha (sem a senha descriptografada)"""
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

    class Config:
        from_attributes = True


class PasswordDetailResponse(BaseModel):
    id: int
    title: str
    site: str
    encrypted_password: str  # base64
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



class MasterPasswordRequest(BaseModel):
    """Schema para requisição de senha mestra"""
    master_password: str = Field(..., min_length=1)


class WalletExportRequest(BaseModel):
    """Schema para exportação de wallet"""
    wallet_password: str = Field(..., min_length=1)
    output_file: Optional[str] = Field(default="wallet.enc")


class WalletImportRequest(BaseModel):
    """Schema para importação de wallet"""
    wallet_file: str = Field(..., min_length=1)
    wallet_password: str = Field(..., min_length=1)


class PasswordGenerateRequest(BaseModel):
    """Schema para geração de senha de teste"""
    length: int = Field(default=16, ge=4, le=128)
    use_uppercase: bool = Field(default=True)
    use_lowercase: bool = Field(default=True)
    use_digits: bool = Field(default=True)
    use_special: bool = Field(default=True)


class PasswordGenerateResponse(BaseModel):
    """Schema de resposta para geração de senha"""
    password: str
    length: int
    entropy: float
    entropy_level: str


class MessageResponse(BaseModel):
    """Schema para mensagens de resposta"""
    message: str
    success: bool = True

