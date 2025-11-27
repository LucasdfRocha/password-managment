"""
API REST para o gerenciador de senhas com suporte a múltiplos usuários
"""
import base64
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Tuple
from datetime import datetime

from schemas import (
    PasswordCreate, PasswordUpdate, PasswordResponse, PasswordDetailResponse,
    UserRegister, UserLogin, LoginResponse,
    WalletExportRequest, WalletImportRequest,
    PasswordGenerateRequest, PasswordGenerateResponse, MessageResponse
)
from auth import auth_manager, SessionInfo
from password_manager import PasswordManager
from password_generator import PasswordGenerator

app = FastAPI(
    title="Password Manager API",
    description="API REST para gerenciamento de senhas com criptografia e multi-usuário",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_user_from_token(token: str = Header(..., alias="X-Session-Token")) -> Tuple[PasswordManager, int]:
    """
    Dependency para obter o usuário e PasswordManager da sessão
    
    Valida:
    - Se o token é válido
    - Se a sessão não expirou
    - Retorna user_id para garantir isolamento de dados
    
    Args:
        token: Token de sessão do header
        
    Returns:
        Tupla (PasswordManager, user_id)
        
    Raises:
        HTTPException: Se o token for inválido ou expirado
    """
    is_valid, user_id, message = auth_manager.validate_session(token)
    
    if not is_valid:
        raise HTTPException(status_code=401, detail=message)
    
    pm = auth_manager.get_password_manager(token)
    if not pm:
        raise HTTPException(status_code=401, detail="Sessão inválida")
    
    return pm, user_id


# ===== AUTHENTICATION ENDPOINTS =====

@app.post("/api/auth/register", response_model=MessageResponse)
async def register(request: UserRegister):
    """
    Registra um novo usuário
    
    Validações:
    - Username: 3+ caracteres, único
    - Password: 8+ caracteres
    - Email: válido e único
    
    Returns:
        Mensagem de sucesso
    """
    try:
        success, message = auth_manager.register_user(
            username=request.username,
            email=request.email,
            password=request.password
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return MessageResponse(message=message, success=True)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao registrar: {str(e)}")


@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: UserLogin):
    """
    Autentica o usuário e cria uma sessão
    
    Mecanismos de segurança:
    - Token gerado com secrets.token_urlsafe (criptograficamente seguro)
    - Token renovado a cada login (previne session fixation)
    - Validação de user_id em cada request
    - Timeout de sessão (60 minutos)
    
    Returns:
        Token de sessão + user_id + username
    """
    try:
        token, user_id, message = auth_manager.login(
            username=request.username,
            password=request.password
        )
        
        if not token:
            raise HTTPException(status_code=401, detail=message)
        
        # Obtém informações da sessão
        session = auth_manager.get_session_info(token)
        
        return LoginResponse(
            token=token,
            user_id=user_id,
            username=session.username,
            message=message
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no login: {str(e)}")


@app.post("/api/auth/logout", response_model=MessageResponse)
async def logout(token: str = Header(..., alias="X-Session-Token")):
    """
    Encerra a sessão do usuário
    
    Returns:
        Mensagem de sucesso
    """
    auth_manager.remove_session(token)
    return MessageResponse(message="Logout realizado com sucesso", success=True)


# ===== PASSWORD ENDPOINTS =====

@app.post("/api/passwords", response_model=PasswordResponse, status_code=201)
async def create_password(
    password_data: PasswordCreate,
    pm_and_user: Tuple[PasswordManager, int] = Depends(get_user_from_token)
):
    """
    Cria uma nova senha para o usuário autenticado
    
    ISOLAMENTO: A senha é associada ao user_id do token
    
    Aceita encrypted_password (base64) gerada no front-end
    """
    pm, user_id = pm_and_user
    
    try:
        encrypted_bytes = None
        if getattr(password_data, "encrypted_password", None):
            try:
                encrypted_bytes = base64.b64decode(password_data.encrypted_password)
            except Exception:
                raise HTTPException(status_code=400, detail="encrypted_password inválido (base64)")

        entry_id = pm.create_password(
            user_id=user_id,
            title=password_data.title,
            site=password_data.site,
            length=password_data.length,
            use_uppercase=password_data.use_uppercase,
            use_lowercase=password_data.use_lowercase,
            use_digits=password_data.use_digits,
            use_special=password_data.use_special,
            expiration_date=password_data.expiration_date,
            custom_password=password_data.custom_password,
            encrypted_password=encrypted_bytes,
        )
        
        entry = pm.get_password(entry_id, user_id)
        if not entry:
            raise HTTPException(status_code=500, detail="Erro ao recuperar senha criada")
        
        entropy_level = PasswordGenerator.get_entropy_level(entry.entropy)
        
        return PasswordResponse(
            id=entry.id,
            title=entry.title,
            site=entry.site,
            length=entry.length,
            use_uppercase=entry.use_uppercase,
            use_lowercase=entry.use_lowercase,
            use_digits=entry.use_digits,
            use_special=entry.use_special,
            entropy=entry.entropy,
            entropy_level=entropy_level,
            expiration_date=entry.expiration_date,
            created_at=entry.created_at,
            updated_at=entry.updated_at
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar senha: {str(e)}")


@app.get("/api/passwords", response_model=List[PasswordResponse])
async def list_passwords(pm_and_user: Tuple[PasswordManager, int] = Depends(get_user_from_token)):
    """
    Lista todas as senhas do usuário autenticado
    
    ISOLAMENTO: Apenas senhas do usuário são retornadas
    
    Returns:
        Lista de senhas (sem mostrar a senha descriptografada)
    """
    pm, user_id = pm_and_user
    
    try:
        entries = pm.get_all_passwords(user_id)
        result = []
        for entry in entries:
            entropy_level = PasswordGenerator.get_entropy_level(entry.entropy)
            result.append(PasswordResponse(
                id=entry.id,
                title=entry.title,
                site=entry.site,
                length=entry.length,
                use_uppercase=entry.use_uppercase,
                use_lowercase=entry.use_lowercase,
                use_digits=entry.use_digits,
                use_special=entry.use_special,
                entropy=entry.entropy,
                entropy_level=entropy_level,
                expiration_date=entry.expiration_date,
                created_at=entry.created_at,
                updated_at=entry.updated_at
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar senhas: {str(e)}")


@app.get("/api/passwords/{entry_id}", response_model=PasswordDetailResponse)
async def get_password(
    entry_id: int,
    pm_and_user: Tuple[PasswordManager, int] = Depends(get_user_from_token)
):
    """
    Obtém uma senha específica com a SENHA CRIPTOGRAFADA
    
    ISOLAMENTO: Verifica se entry_id pertence ao usuário autenticado
    Quem vai descriptografar é o cliente
    """
    pm, user_id = pm_and_user
    
    try:
        entry = pm.get_password(entry_id, user_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Senha não encontrada ou acesso negado")

        encrypted_b64 = base64.b64encode(entry.password).decode("utf-8")
        entropy_level = PasswordGenerator.get_entropy_level(entry.entropy)
        
        return PasswordDetailResponse(
            id=entry.id,
            title=entry.title,
            site=entry.site,
            encrypted_password=encrypted_b64,
            length=entry.length,
            use_uppercase=entry.use_uppercase,
            use_lowercase=entry.use_lowercase,
            use_digits=entry.use_digits,
            use_special=entry.use_special,
            entropy=entry.entropy,
            entropy_level=entropy_level,
            expiration_date=entry.expiration_date,
            created_at=entry.created_at,
            updated_at=entry.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter senha: {str(e)}")


@app.put("/api/passwords/{entry_id}", response_model=PasswordResponse)
async def update_password(
    entry_id: int,
    password_data: PasswordUpdate,
    pm_and_user: Tuple[PasswordManager, int] = Depends(get_user_from_token)
):
    """
    Atualiza uma senha
    
    ISOLAMENTO: Verifica se entry_id pertence ao usuário autenticado
    """
    pm, user_id = pm_and_user
    
    try:
        encrypted_bytes = None
        if getattr(password_data, "encrypted_password", None):
            try:
                encrypted_bytes = base64.b64decode(password_data.encrypted_password)
            except Exception:
                raise HTTPException(status_code=400, detail="encrypted_password inválido (base64)")

        success = pm.update_password(
            entry_id=entry_id,
            user_id=user_id,
            title=password_data.title,
            site=password_data.site,
            length=password_data.length,
            use_uppercase=password_data.use_uppercase,
            use_lowercase=password_data.use_lowercase,
            use_digits=password_data.use_digits,
            use_special=password_data.use_special,
            expiration_date=password_data.expiration_date,
            regenerate=password_data.regenerate,
            custom_password=password_data.custom_password,
            encrypted_password=encrypted_bytes,
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Senha não encontrada ou acesso negado")
        
        entry = pm.get_password(entry_id, user_id)
        if not entry:
            raise HTTPException(status_code=500, detail="Erro ao recuperar senha atualizada")
        
        entropy_level = PasswordGenerator.get_entropy_level(entry.entropy)
        
        return PasswordResponse(
            id=entry.id,
            title=entry.title,
            site=entry.site,
            length=entry.length,
            use_uppercase=entry.use_uppercase,
            use_lowercase=entry.use_lowercase,
            use_digits=entry.use_digits,
            use_special=entry.use_special,
            entropy=entry.entropy,
            entropy_level=entropy_level,
            expiration_date=entry.expiration_date,
            created_at=entry.created_at,
            updated_at=entry.updated_at
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar senha: {str(e)}")


@app.delete("/api/passwords/{entry_id}", response_model=MessageResponse)
async def delete_password(
    entry_id: int,
    pm_and_user: Tuple[PasswordManager, int] = Depends(get_user_from_token)
):
    """
    Deleta uma senha
    
    ISOLAMENTO: Verifica se entry_id pertence ao usuário autenticado
    
    Args:
        entry_id: ID da senha
        
    Returns:
        Mensagem de sucesso
    """
    pm, user_id = pm_and_user
    
    try:
        success = pm.delete_password(entry_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Senha não encontrada ou acesso negado")
        
        return MessageResponse(message="Senha deletada com sucesso", success=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar senha: {str(e)}")


@app.post("/api/passwords/generate", response_model=PasswordGenerateResponse)
async def generate_test_password(
    request: PasswordGenerateRequest,
    pm_and_user: Tuple[PasswordManager, int] = Depends(get_user_from_token)
):
    """
    Gera uma senha de teste sem salvar
    
    Returns:
        Senha gerada com informações de entropia
    """
    pm, user_id = pm_and_user
    
    try:
        password = PasswordGenerator.generate(
            length=request.length,
            use_uppercase=request.use_uppercase,
            use_lowercase=request.use_lowercase,
            use_digits=request.use_digits,
            use_special=request.use_special
        )
        
        entropy = PasswordGenerator.calculate_entropy(
            request.length,
            request.use_uppercase,
            request.use_lowercase,
            request.use_digits,
            request.use_special
        )
        entropy_level = PasswordGenerator.get_entropy_level(entropy)
        
        return PasswordGenerateResponse(
            password=password,
            length=request.length,
            entropy=entropy,
            entropy_level=entropy_level
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar senha: {str(e)}")


@app.get("/api/wallet/export")
async def wallet_export(pm_and_user: Tuple[PasswordManager, int] = Depends(get_user_from_token)):
    """
    Exporta TODAS as entradas de senha do usuário em formato bruto (criptografado).
    
    ISOLAMENTO: Apenas senhas do usuário são exportadas
    Zero knowledge: O servidor nunca vê as senhas descriptografadas
    """
    pm, user_id = pm_and_user
    
    entries = pm.get_all_passwords(user_id)

    payload = []
    for e in entries:
        payload.append({
            "title": e.title,
            "site": e.site,
            "length": e.length,
            "use_uppercase": e.use_uppercase,
            "use_lowercase": e.use_lowercase,
            "use_digits": e.use_digits,
            "use_special": e.use_special,
            "entropy": e.entropy,
            "expiration_date": e.expiration_date,
            "created_at": e.created_at,
            "updated_at": e.updated_at,
            "encrypted_password": base64.b64encode(e.password).decode("utf-8")
        })

    return {
        "exported_at": datetime.now().isoformat(),
        "entries": payload
    }


@app.post("/api/wallet/import")
async def wallet_import(
    data: dict,
    pm_and_user: Tuple[PasswordManager, int] = Depends(get_user_from_token)
):
    """
    Importa entradas já criptografadas no cliente
    
    ISOLAMENTO: Senhas importadas são associadas ao user_id
    O servidor nunca vê a senha em texto puro
    
    Formato esperado:
    {
      "entries": [
        {
          "title": "...",
          "site": "...",
          "length": 16,
          "use_uppercase": true,
          "use_lowercase": true,
          "use_digits": true,
          "use_special": true,
          "expiration_date": null,
          "encrypted_password": "encoded-string"
        },
        ...
      ]
    }
    """
    pm, user_id = pm_and_user
    
    if "entries" not in data:
        raise HTTPException(status_code=400, detail="Formato inválido de wallet.")

    count = 0
    for entry in data["entries"]:
        encrypted_b64 = entry.get("encrypted_password")
        if not encrypted_b64:
            continue

        try:
            encrypted_bytes = base64.b64decode(encrypted_b64)
        except Exception:
            continue

        pm.create_password(
            user_id=user_id,
            title=entry["title"],
            site=entry["site"],
            length=entry["length"],
            use_uppercase=entry["use_uppercase"],
            use_lowercase=entry["use_lowercase"],
            use_digits=entry["use_digits"],
            use_special=entry["use_special"],
            expiration_date=entry["expiration_date"],
            encrypted_password=encrypted_bytes
        )
        count += 1

    return {"success": True, "imported": count}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

