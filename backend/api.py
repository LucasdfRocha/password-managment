# backend/api.py

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Tuple, List
import base64
import os

from auth import auth_manager   # usa o AuthManager global do auth.py
from password_manager import PasswordManager
from password_generator import PasswordGenerator
from schemas import (
    UserRegister,
    UserLogin,
    LoginResponse,
    MessageResponse,
    PasswordCreate,
    PasswordUpdate,
    PasswordResponse,
    PasswordDetailResponse,
    PasswordGenerateRequest,
    PasswordGenerateResponse,
)

# --------------------------------------------------------------------------
# APP & CORS
# --------------------------------------------------------------------------

app = FastAPI(title="Password Manager API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # para testes em rede local
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------
# DEPENDÊNCIA: obter usuário/sessão pelo token
# --------------------------------------------------------------------------

def get_user_from_token(
    token: str = Header(..., alias="X-Session-Token")
) -> Tuple[PasswordManager, int]:
    """
    Valida o token de sessão e devolve (PasswordManager, user_id).
    """
    is_valid, user_id, msg = auth_manager.validate_session(token)
    if not is_valid or user_id is None:
        raise HTTPException(status_code=401, detail=msg)

    pm = auth_manager.get_password_manager(token)
    if not pm:
        raise HTTPException(status_code=401, detail="Sessão inválida.")

    return pm, user_id


# --------------------------------------------------------------------------
# AUTH
# --------------------------------------------------------------------------

@app.post("/api/auth/register", response_model=MessageResponse)
def register(user: UserRegister):
    success, msg = auth_manager.register_user(user.username, user.email, user.password)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return MessageResponse(success=True, message=msg)


@app.post("/api/auth/login", response_model=LoginResponse)
def login(data: UserLogin):
    success, token, user_id, message = auth_manager.login(data.username, data.password)

    if not success or not token or user_id is None:
        raise HTTPException(status_code=401, detail=message)

    # pega o username da sessão (pode ser igual ao informado)
    session = auth_manager.get_session_info(token)
    username = session.username if session else data.username

    return LoginResponse(
        token=token,
        user_id=user_id,
        username=username,
        message=message,
    )


@app.post("/api/auth/logout", response_model=MessageResponse)
def logout(token: str = Header(..., alias="X-Session-Token")):
    success, msg = auth_manager.logout(token)
    return MessageResponse(success=success, message=msg)


# --------------------------------------------------------------------------
# PASSWORDS - CREATE
# --------------------------------------------------------------------------

@app.post("/api/passwords", response_model=PasswordResponse)
def create_password(
    password_data: PasswordCreate,
    user_ctx: Tuple[PasswordManager, int] = Depends(get_user_from_token),
):
    pm, user_id = user_ctx

    if not password_data.encrypted_password:
        raise HTTPException(
            status_code=400,
            detail="Campo encrypted_password ausente. A senha deve ser criptografada no cliente.",
        )

    try:
        encrypted_bytes = base64.b64decode(password_data.encrypted_password)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="encrypted_password inválido (não é base64).",
        )

    try:
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
            raise HTTPException(status_code=500, detail="Erro ao recuperar senha criada.")

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
        # erros de regra de negócio
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar senha: {str(e)}")


# --------------------------------------------------------------------------
# PASSWORDS - LIST
# --------------------------------------------------------------------------

@app.get("/api/passwords", response_model=List[PasswordResponse])
def list_passwords(
    user_ctx: Tuple[PasswordManager, int] = Depends(get_user_from_token),
):
    pm, user_id = user_ctx
    entries = pm.get_all_passwords(user_id)

    result: List[PasswordResponse] = []
    for e in entries:
        entropy_level = PasswordGenerator.get_entropy_level(e.entropy)
        result.append(
            PasswordResponse(
                id=e.id,
                title=e.title,
                site=e.site,
                length=e.length,
                use_uppercase=e.use_uppercase,
                use_lowercase=e.use_lowercase,
                use_digits=e.use_digits,
                use_special=e.use_special,
                entropy=e.entropy,
                entropy_level=entropy_level,
                expiration_date=e.expiration_date,
                created_at=e.created_at,
                updated_at=e.updated_at,
            )
        )
    return result


# --------------------------------------------------------------------------
# PASSWORDS - DETAIL (para buscar o blob criptografado)
# --------------------------------------------------------------------------

@app.get("/api/passwords/{entry_id}", response_model=PasswordDetailResponse)
def get_password_detail(
    entry_id: int,
    user_ctx: Tuple[PasswordManager, int] = Depends(get_user_from_token),
):
    pm, user_id = user_ctx
    entry = pm.get_password(entry_id, user_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Senha não encontrada.")

    encrypted_b64 = base64.b64encode(entry.password).decode("utf-8")

    return PasswordDetailResponse(
        id=entry.id,
        title=entry.title,
        site=entry.site,
        encrypted_password=encrypted_b64,
        entropy=entry.entropy,
        expiration_date=entry.expiration_date,
        created_at=entry.created_at,
    )


# --------------------------------------------------------------------------
# PASSWORDS - UPDATE
# --------------------------------------------------------------------------

@app.put("/api/passwords/{entry_id}", response_model=PasswordResponse)
def update_password(
    entry_id: int,
    data: PasswordUpdate,
    user_ctx: Tuple[PasswordManager, int] = Depends(get_user_from_token),
):
    pm, user_id = user_ctx

    encrypted_bytes = None
    if data.encrypted_password:
        try:
            encrypted_bytes = base64.b64decode(data.encrypted_password)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="encrypted_password inválido (não é base64).",
            )

    success = pm.update_password(
        entry_id=entry_id,
        user_id=user_id,
        title=data.title,
        site=data.site,
        length=data.length,
        use_uppercase=data.use_uppercase,
        use_lowercase=data.use_lowercase,
        use_digits=data.use_digits,
        use_special=data.use_special,
        expiration_date=data.expiration_date,
        regenerate=data.regenerate,
        custom_password=data.custom_password,
        encrypted_password=encrypted_bytes,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Senha não encontrada ou não pertence ao usuário.")

    entry = pm.get_password(entry_id, user_id)
    if not entry:
        raise HTTPException(status_code=500, detail="Erro ao recuperar senha atualizada.")

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


# --------------------------------------------------------------------------
# PASSWORDS - DELETE
# --------------------------------------------------------------------------

@app.delete("/api/passwords/{entry_id}", response_model=MessageResponse)
def delete_password(
    entry_id: int,
    user_ctx: Tuple[PasswordManager, int] = Depends(get_user_from_token),
):
    pm, user_id = user_ctx
    success = pm.delete_password(entry_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Senha não encontrada ou não pertence ao usuário.")
    return MessageResponse(success=True, message="Senha removida com sucesso.")


# --------------------------------------------------------------------------
# GERADOR DE SENHAS (para testes)
# --------------------------------------------------------------------------

@app.post("/api/passwords/generate", response_model=PasswordGenerateResponse)
def generate_password(data: PasswordGenerateRequest):
    pw = PasswordGenerator.generate(
        length=data.length,
        use_uppercase=data.use_uppercase,
        use_lowercase=data.use_lowercase,
        use_digits=data.use_digits,
        use_special=data.use_special,
    )

    entropy = PasswordGenerator.calculate_entropy(
        data.length,
        data.use_uppercase,
        data.use_lowercase,
        data.use_digits,
        data.use_special,
    )

    return PasswordGenerateResponse(password=pw, entropy=entropy)


# --------------------------------------------------------------------------
# WALLET EXPORT / IMPORT
# --------------------------------------------------------------------------

@app.get("/api/wallet/export")
def export_wallet(
    user_ctx: Tuple[PasswordManager, int] = Depends(get_user_from_token),
):
    pm, user_id = user_ctx
    entries = pm.get_all_passwords(user_id)

    exported = []
    for e in entries:
        encrypted_b64 = base64.b64encode(e.password).decode("utf-8")
        exported.append({
            "title": e.title,
            "site": e.site,
            "length": e.length,
            "use_uppercase": e.use_uppercase,
            "use_lowercase": e.use_lowercase,
            "use_digits": e.use_digits,
            "use_special": e.use_special,
            "entropy": e.entropy,
            "expiration_date": e.expiration_date.isoformat() if e.expiration_date else None,
            "encrypted_password": encrypted_b64,
        })

    return {"success": True, "entries": exported}


@app.post("/api/wallet/import")
def import_wallet(
    data: dict,
    user_ctx: Tuple[PasswordManager, int] = Depends(get_user_from_token),
):
    pm, user_id = user_ctx
    entries = data.get("entries", [])

    count = 0
    for e in entries:
        try:
            encrypted_bytes = base64.b64decode(e["encrypted_password"])
        except Exception:
            continue

        pm.create_password(
            user_id=user_id,
            title=e.get("title", ""),
            site=e.get("site", ""),
            length=e.get("length", 16),
            use_uppercase=e.get("use_uppercase", True),
            use_lowercase=e.get("use_lowercase", True),
            use_digits=e.get("use_digits", True),
            use_special=e.get("use_special", True),
            expiration_date=datetime.fromisoformat(e["expiration_date"]) if e.get("expiration_date") else None,
            custom_password=None,
            encrypted_password=encrypted_bytes,
        )
        count += 1

    return {"success": True, "imported": count}


# --------------------------------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------------------------------

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "API operacional"}


# --------------------------------------------------------------------------
# SERVIR FRONT-END (./frontend) EM "/"
# --------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

app.mount(
    "/",
    StaticFiles(directory=FRONTEND_DIR, html=True),
    name="frontend",
)
