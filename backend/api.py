"""
API REST para o gerenciador de senhas
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from datetime import datetime

from schemas import (
    PasswordCreate,
    PasswordUpdate,
    PasswordResponse,
    PasswordDetailResponse,
    MasterPasswordRequest,
    WalletExportRequest,
    WalletImportRequest,
    PasswordGenerateRequest,
    PasswordGenerateResponse,
    MessageResponse,
)
from auth import auth_manager
from password_manager import PasswordManager
from password_generator import PasswordGenerator
from wallet import WalletManager

app = FastAPI(
    title="Password Manager API",
    description="API REST para gerenciamento de senhas com criptografia",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_password_manager(
    token: str = Header(..., alias="X-Session-Token")
) -> PasswordManager:
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
        raise HTTPException(
            status_code=401, detail="Token de sessão inválido ou expirado"
        )
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


@app.post("/api/passwords", response_model=PasswordResponse, status_code=201)
async def create_password(
    password_data: PasswordCreate, pm: PasswordManager = Depends(get_password_manager)
):
    """
    Cria uma nova senha

    Returns:
        Dados da senha criada
    """
    try:
        entry_id = pm.create_password(
            title=password_data.title,
            site=password_data.site,
            length=password_data.length,
            use_uppercase=password_data.use_uppercase,
            use_lowercase=password_data.use_lowercase,
            use_digits=password_data.use_digits,
            use_special=password_data.use_special,
            expiration_date=password_data.expiration_date,
            custom_password=password_data.custom_password,
        )

        result = pm.get_password(entry_id)
        if not result:
            raise HTTPException(
                status_code=500, detail="Erro ao recuperar senha criada"
            )

        entry, _ = result
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
            updated_at=entry.updated_at,
        )
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
            result.append(
                PasswordResponse(
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
                    updated_at=entry.updated_at,
                )
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar senhas: {str(e)}")


@app.get("/api/passwords/{entry_id}", response_model=PasswordDetailResponse)
async def get_password(
    entry_id: int, pm: PasswordManager = Depends(get_password_manager)
):
    """
    Obtém uma senha específica com a senha descriptografada

    Args:
        entry_id: ID da senha

    Returns:
        Dados completos da senha incluindo a senha descriptografada
    """
    try:
        result = pm.get_password(entry_id)
        if not result:
            raise HTTPException(status_code=404, detail="Senha não encontrada")

        entry, decrypted_password = result
        entropy_level = PasswordGenerator.get_entropy_level(entry.entropy)

        return PasswordDetailResponse(
            id=entry.id,
            title=entry.title,
            site=entry.site,
            password=decrypted_password,
            length=entry.length,
            use_uppercase=entry.use_uppercase,
            use_lowercase=entry.use_lowercase,
            use_digits=entry.use_digits,
            use_special=entry.use_special,
            entropy=entry.entropy,
            entropy_level=entropy_level,
            expiration_date=entry.expiration_date,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter senha: {str(e)}")


@app.put("/api/passwords/{entry_id}", response_model=PasswordResponse)
async def update_password(
    entry_id: int,
    password_data: PasswordUpdate,
    pm: PasswordManager = Depends(get_password_manager),
):
    """
    Atualiza uma senha

    Args:
        entry_id: ID da senha
        password_data: Dados para atualização

    Returns:
        Dados atualizados da senha
    """
    try:
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
        )

        if not success:
            raise HTTPException(status_code=404, detail="Senha não encontrada")

        result = pm.get_password(entry_id)
        if not result:
            raise HTTPException(
                status_code=500, detail="Erro ao recuperar senha atualizada"
            )

        entry, _ = result
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
            updated_at=entry.updated_at,
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao atualizar senha: {str(e)}"
        )


@app.delete("/api/passwords/{entry_id}", response_model=MessageResponse)
async def delete_password(
    entry_id: int, pm: PasswordManager = Depends(get_password_manager)
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
    pm: PasswordManager = Depends(get_password_manager),
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
            use_special=request.use_special,
        )

        entropy = PasswordGenerator.calculate_entropy(
            request.length,
            request.use_uppercase,
            request.use_lowercase,
            request.use_digits,
            request.use_special,
        )
        entropy_level = PasswordGenerator.get_entropy_level(entropy)

        return PasswordGenerateResponse(
            password=password,
            length=request.length,
            entropy=entropy,
            entropy_level=entropy_level,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar senha: {str(e)}")


@app.post("/api/wallet/export", response_model=MessageResponse)
async def export_wallet(
    request: WalletExportRequest, pm: PasswordManager = Depends(get_password_manager)
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
            output_file=request.output_file,
        )
        return MessageResponse(
            message=f"Wallet exportado com sucesso para {request.output_file}",
            success=True,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao exportar wallet: {str(e)}"
        )


@app.post("/api/wallet/import", response_model=MessageResponse)
async def import_wallet(
    request: WalletImportRequest, pm: PasswordManager = Depends(get_password_manager)
):
    """
    Importa senhas de um arquivo wallet

    Returns:
        Mensagem de sucesso com número de entradas importadas
    """
    try:
        count = WalletManager.import_wallet(
            wallet_file=request.wallet_file,
            wallet_password=request.wallet_password,
            encryption_manager=pm.encryption_manager,
            storage_manager=pm.db_manager,
        )
        return MessageResponse(
            message=f"{count} entradas importadas com sucesso", success=True
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Arquivo wallet não encontrado")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao importar wallet: {str(e)}"
        )


@app.get("/api/health")
async def health_check():
    """
    Endpoint de health check

    Returns:
        Status da API
    """
    return {"status": "ok", "message": "API está funcionando"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
