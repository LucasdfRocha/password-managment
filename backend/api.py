"""
API REST para o gerenciador de senhas
"""
import base64
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from datetime import datetime

from schemas import (
    PasswordCreate, PasswordUpdate, PasswordResponse, PasswordDetailResponse,
    MasterPasswordRequest, WalletExportRequest, WalletImportRequest,
    PasswordGenerateRequest, PasswordGenerateResponse, MessageResponse
)
from auth import auth_manager
from password_manager import PasswordManager
from password_generator import PasswordGenerator
# from wallet import WalletManager

app = FastAPI(
    title="Password Manager API",
    description="API REST para gerenciamento de senhas com criptografia",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_password_manager(token: str = Header(..., alias="X-Session-Token")) -> PasswordManager:
    """
    Dependency para obter o PasswordManager da sessão
    
    Args:
        token: Token de sessão do header
        
    Returns:
        PasswordManager
        
    Raises:
        HTTPException: Se o token for inválido
    """
    pm = auth_manager.get_password_manager(token)
    if not pm:
        raise HTTPException(status_code=401, detail="Token de sessão inválido ou expirado")
    return pm


@app.post("/api/auth/login", response_model=dict)
async def login(request: MasterPasswordRequest):
    """
    Autentica o usuário e cria uma sessão
    
    Returns:
        Token de sessão
    """
    try:
        token = auth_manager.create_session(request.master_password)
        return {"token": token, "message": "Login realizado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/logout")
async def logout(token: str = Header(..., alias="X-Session-Token")):
    """
    Encerra a sessão do usuário
    
    Returns:
        Mensagem de sucesso
    """
    auth_manager.remove_session(token)
    return {"message": "Logout realizado com sucesso"}


# api.py

@app.post("/api/passwords", response_model=PasswordResponse, status_code=201)
async def create_password(
    password_data: PasswordCreate,
    pm: PasswordManager = Depends(get_password_manager)
):
    """
    Cria uma nova senha
    
    Agora aceita também password_data.encrypted_password (base64),
    gerada no front-end.
    """
    try:
        encrypted_bytes = None
        if getattr(password_data, "encrypted_password", None):
            try:
                encrypted_bytes = base64.b64decode(password_data.encrypted_password)
            except Exception:
                raise HTTPException(status_code=400, detail="encrypted_password inválido (base64)")

        entry_id = pm.create_password(
            title=password_data.title,
            site=password_data.site,
            length=password_data.length,
            use_uppercase=password_data.use_uppercase,
            use_lowercase=password_data.use_lowercase,
            use_digits=password_data.use_digits,
            use_special=password_data.use_special,
            expiration_date=password_data.expiration_date,
            custom_password=password_data.custom_password,  # pode ficar sempre None se usarem apenas o front
            encrypted_password=encrypted_bytes,
        )
        
        entry = pm.get_password(entry_id)
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
async def list_passwords(pm: PasswordManager = Depends(get_password_manager)):
    """
    Lista todas as senhas (sem mostrar a senha descriptografada)
    
    Returns:
        Lista de senhas
    """
    try:
        entries = pm.get_all_passwords()
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


# api.py

@app.get("/api/passwords/{entry_id}", response_model=PasswordDetailResponse)
async def get_password(
    entry_id: int,
    pm: PasswordManager = Depends(get_password_manager)
):
    """
    Obtém uma senha específica com a SENHA AINDA CRIPTOGRAFADA.
    Quem vai descriptografar é o cliente.
    """
    try:
        entry = pm.get_password(entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Senha não encontrada")

        # entry.password deve ser bytes vindos do DB
        encrypted_b64 = base64.b64encode(entry.password).decode("utf-8")

        entropy_level = PasswordGenerator.get_entropy_level(entry.entropy)
        
        return PasswordDetailResponse(
            id=entry.id,
            title=entry.title,
            site=entry.site,
            encrypted_password=encrypted_b64,  # <-- novo campo
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
    pm: PasswordManager = Depends(get_password_manager)
):
    """
    Atualiza uma senha.

    IMPORTANTE:
    - Idealmente, o cliente também envia encrypted_password (base64)
      se for trocar a senha em si.
    - O servidor continua sem descriptografar nada.
    """
    try:
        # Opcional: se você adicionar encrypted_password no PasswordUpdate
        encrypted_bytes = None
        if getattr(password_data, "encrypted_password", None):
            try:
                encrypted_bytes = base64.b64decode(password_data.encrypted_password)
            except Exception:
                raise HTTPException(status_code=400, detail="encrypted_password inválido (base64)")

        success = pm.update_password(
            entry_id=entry_id,
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
            encrypted_password=encrypted_bytes,  # novo parâmetro, ajuste no PasswordManager
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Senha não encontrada")
        
        entry = pm.get_password(entry_id)
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
    pm: PasswordManager = Depends(get_password_manager)
):
    """
    Deleta uma senha
    
    Args:
        entry_id: ID da senha
        
    Returns:
        Mensagem de sucesso
    """
    try:
        success = pm.delete_password(entry_id)
        if not success:
            raise HTTPException(status_code=404, detail="Senha não encontrada")
        
        return MessageResponse(message="Senha deletada com sucesso", success=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar senha: {str(e)}")


@app.post("/api/passwords/generate", response_model=PasswordGenerateResponse)
async def generate_test_password(
    request: PasswordGenerateRequest,
    pm: PasswordManager = Depends(get_password_manager)
):
    """
    Gera uma senha de teste sem salvar
    
    Returns:
        Senha gerada com informações de entropia
    """
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


@app.post("/api/wallet/export", response_model=MessageResponse)
async def export_wallet(
    request: WalletExportRequest,
    pm: PasswordManager = Depends(get_password_manager)
):
    """
    Exporta todas as senhas para um arquivo wallet
    
    Returns:
        Mensagem de sucesso
    """
    try:
        entries = pm.get_all_passwords()
        WalletManager.export_wallet(
            entries=entries,
            encryption_manager=pm.encryption_manager,
            wallet_password=request.wallet_password,
            output_file=request.output_file
        )
        return MessageResponse(
            message=f"Wallet exportado com sucesso para {request.output_file}",
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao exportar wallet: {str(e)}")


@app.post("/api/wallet/import")
async def wallet_import(
    data: dict,
    pm: PasswordManager = Depends(get_password_manager)
):
    """
    Importa entradas já criptografadas no cliente.
    O servidor nunca vê a senha em texto puro.
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
          "encrypted_password": "base64..."
        },
        ...
      ]
    }
    """
    if "entries" not in data or not isinstance(data["entries"], list):
        raise HTTPException(status_code=400, detail="Formato inválido de wallet (entries ausente).")

    count = 0
    for entry in data["entries"]:
        encrypted_b64 = entry.get("encrypted_password")
        if not encrypted_b64:
            continue

        try:
            encrypted_bytes = base64.b64decode(encrypted_b64)
        except Exception:
            continue  # ignora entrada com base64 inválido

        pm.create_password(
            title=entry.get("title", ""),
            site=entry.get("site", ""),
            length=entry.get("length", 16),
            use_uppercase=entry.get("use_uppercase", True),
            use_lowercase=entry.get("use_lowercase", True),
            use_digits=entry.get("use_digits", True),
            use_special=entry.get("use_special", True),
            expiration_date=entry.get("expiration_date", None),
            encrypted_password=encrypted_bytes
        )
        count += 1

    return {"success": True, "imported": count}

@app.get("/api/health")
async def health_check():
    """
    Endpoint de health check
    
    Returns:
        Status da API
    """
    return {"status": "ok", "message": "API está funcionando"}


@app.get("/api/wallet/export")
async def wallet_export(pm: PasswordManager = Depends(get_password_manager)):
    """
    Exporta TODAS as entradas de senha em formato bruto (criptografado).
    Não descriptografa nada — zero knowledge.
    """
    entries = pm.get_all_passwords()

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
    pm: PasswordManager = Depends(get_password_manager)
):
    """
    Importa entradas já criptografadas no cliente.
    O servidor nunca vê a senha em texto puro.
    """
    if "entries" not in data:
        raise HTTPException(status_code=400, detail="Formato inválido de wallet.")

    count = 0
    for entry in data["entries"]:
        encrypted_b64 = entry.get("encrypted_password")
        if not encrypted_b64:
            continue

        encrypted_bytes = base64.b64decode(encrypted_b64)

        pm.create_password(
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

