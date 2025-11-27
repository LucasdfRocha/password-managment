# Exemplos de Requisições HTTP - Multi-User API

## Base URL
```
http://localhost:8000/api
```

---

## 🔐 Authentication Endpoints

### 1. Registrar Novo Usuário

**Endpoint**: `POST /auth/register`

**Request**:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePassword123!"
  }'
```

**Response** (201 - Sucesso):
```json
{
  "message": "Usuário john_doe registrado com sucesso",
  "success": true
}
```

**Response** (400 - Erro):
```json
{
  "detail": "Username já existe"
}
```

---

### 2. Fazer Login

**Endpoint**: `POST /auth/login`

**Request**:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "SecurePassword123!"
  }'
```

**Response** (200 - Sucesso):
```json
{
  "token": "abcdef123456789...",
  "user_id": 1,
  "username": "john_doe",
  "message": "Login realizado com sucesso"
}
```

**Response** (401 - Erro):
```json
{
  "detail": "Username ou senha incorretos"
}
```

---

### 3. Fazer Logout

**Endpoint**: `POST /auth/logout`

**Request**:
```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "X-Session-Token: abcdef123456789..."
```

**Response** (200):
```json
{
  "message": "Logout realizado com sucesso",
  "success": true
}
```

---

## 📝 Password Endpoints

### 4. Criar Nova Senha

**Endpoint**: `POST /passwords`

**Request**:
```bash
curl -X POST http://localhost:8000/api/passwords \
  -H "Content-Type: application/json" \
  -H "X-Session-Token: abcdef123456789..." \
  -d '{
    "title": "Gmail Pessoal",
    "site": "https://mail.google.com",
    "length": 16,
    "use_uppercase": true,
    "use_lowercase": true,
    "use_digits": true,
    "use_special": true,
    "expiration_date": null,
    "encrypted_password": "base64_encrypted_blob"
  }'
```

**Response** (201 - Sucesso):
```json
{
  "id": 1,
  "title": "Gmail Pessoal",
  "site": "https://mail.google.com",
  "length": 16,
  "use_uppercase": true,
  "use_lowercase": true,
  "use_digits": true,
  "use_special": true,
  "entropy": 94.2,
  "entropy_level": "Strong",
  "expiration_date": null,
  "created_at": "2025-11-26T10:30:00",
  "updated_at": "2025-11-26T10:30:00"
}
```

---

### 5. Listar Todas as Senhas do Usuário

**Endpoint**: `GET /passwords`

**Request**:
```bash
curl -X GET http://localhost:8000/api/passwords \
  -H "X-Session-Token: abcdef123456789..."
```

**Response** (200):
```json
[
  {
    "id": 1,
    "title": "Gmail Pessoal",
    "site": "https://mail.google.com",
    "length": 16,
    "use_uppercase": true,
    "use_lowercase": true,
    "use_digits": true,
    "use_special": true,
    "entropy": 94.2,
    "entropy_level": "Strong",
    "expiration_date": null,
    "created_at": "2025-11-26T10:30:00",
    "updated_at": "2025-11-26T10:30:00"
  },
  {
    "id": 2,
    "title": "GitHub",
    "site": "https://github.com",
    "length": 20,
    "use_uppercase": true,
    "use_lowercase": true,
    "use_digits": true,
    "use_special": true,
    "entropy": 131.9,
    "entropy_level": "Strong",
    "expiration_date": null,
    "created_at": "2025-11-26T11:00:00",
    "updated_at": "2025-11-26T11:00:00"
  }
]
```

**Nota**: Retorna apenas senhas do usuário autenticado

---

### 6. Obter Senha Específica (Criptografada)

**Endpoint**: `GET /passwords/{entry_id}`

**Request**:
```bash
curl -X GET http://localhost:8000/api/passwords/1 \
  -H "X-Session-Token: abcdef123456789..."
```

**Response** (200):
```json
{
  "id": 1,
  "title": "Gmail Pessoal",
  "site": "https://mail.google.com",
  "encrypted_password": "base64_encrypted_blob_here",
  "length": 16,
  "use_uppercase": true,
  "use_lowercase": true,
  "use_digits": true,
  "use_special": true,
  "entropy": 94.2,
  "entropy_level": "Strong",
  "expiration_date": null,
  "created_at": "2025-11-26T10:30:00",
  "updated_at": "2025-11-26T10:30:00"
}
```

**Response** (404 - Erro):
```json
{
  "detail": "Senha não encontrada ou acesso negado"
}
```

**Nota**: 
- Senha retorna **criptografada** (base64)
- Cliente descriptografa localmente com master password
- Servidor nunca vê senha descriptografada

---

### 7. Atualizar Senha

**Endpoint**: `PUT /passwords/{entry_id}`

**Request**:
```bash
curl -X PUT http://localhost:8000/api/passwords/1 \
  -H "Content-Type: application/json" \
  -H "X-Session-Token: abcdef123456789..." \
  -d '{
    "title": "Gmail Novo Nome",
    "site": "https://mail.google.com",
    "expiration_date": "2025-12-26T00:00:00"
  }'
```

**Response** (200):
```json
{
  "id": 1,
  "title": "Gmail Novo Nome",
  "site": "https://mail.google.com",
  "length": 16,
  "use_uppercase": true,
  "use_lowercase": true,
  "use_digits": true,
  "use_special": true,
  "entropy": 94.2,
  "entropy_level": "Strong",
  "expiration_date": "2025-12-26T00:00:00",
  "created_at": "2025-11-26T10:30:00",
  "updated_at": "2025-11-26T11:15:00"
}
```

---

### 8. Deletar Senha

**Endpoint**: `DELETE /passwords/{entry_id}`

**Request**:
```bash
curl -X DELETE http://localhost:8000/api/passwords/1 \
  -H "X-Session-Token: abcdef123456789..."
```

**Response** (200):
```json
{
  "message": "Senha deletada com sucesso",
  "success": true
}
```

**Response** (404 - Erro):
```json
{
  "detail": "Senha não encontrada ou acesso negado"
}
```

---

### 9. Gerar Senha (Teste)

**Endpoint**: `POST /passwords/generate`

**Request**:
```bash
curl -X POST http://localhost:8000/api/passwords/generate \
  -H "Content-Type: application/json" \
  -H "X-Session-Token: abcdef123456789..." \
  -d '{
    "length": 20,
    "use_uppercase": true,
    "use_lowercase": true,
    "use_digits": true,
    "use_special": true
  }'
```

**Response** (200):
```json
{
  "password": "aB3$xYz9!mN@pQr2Ks",
  "length": 20,
  "entropy": 131.9,
  "entropy_level": "Strong"
}
```

---

## 💾 Wallet Endpoints

### 10. Exportar Wallet (Backup Remoto)

**Endpoint**: `GET /wallet/export`

**Request**:
```bash
curl -X GET http://localhost:8000/api/wallet/export \
  -H "X-Session-Token: abcdef123456789..."
```

**Response** (200):
```json
{
  "exported_at": "2025-11-26T11:30:00",
  "entries": [
    {
      "title": "Gmail Pessoal",
      "site": "https://mail.google.com",
      "length": 16,
      "use_uppercase": true,
      "use_lowercase": true,
      "use_digits": true,
      "use_special": true,
      "entropy": 94.2,
      "expiration_date": null,
      "created_at": "2025-11-26T10:30:00",
      "updated_at": "2025-11-26T10:30:00",
      "encrypted_password": "base64_blob_1"
    },
    {
      "title": "GitHub",
      "site": "https://github.com",
      "length": 20,
      "use_uppercase": true,
      "use_lowercase": true,
      "use_digits": true,
      "use_special": true,
      "entropy": 131.9,
      "expiration_date": null,
      "created_at": "2025-11-26T11:00:00",
      "updated_at": "2025-11-26T11:00:00",
      "encrypted_password": "base64_blob_2"
    }
  ]
}
```

---

### 11. Importar Wallet

**Endpoint**: `POST /wallet/import`

**Request**:
```bash
curl -X POST http://localhost:8000/api/wallet/import \
  -H "Content-Type: application/json" \
  -H "X-Session-Token: abcdef123456789..." \
  -d '{
    "entries": [
      {
        "title": "Gmail Pessoal",
        "site": "https://mail.google.com",
        "length": 16,
        "use_uppercase": true,
        "use_lowercase": true,
        "use_digits": true,
        "use_special": true,
        "expiration_date": null,
        "encrypted_password": "base64_blob_1"
      }
    ]
  }'
```

**Response** (200):
```json
{
  "success": true,
  "imported": 1
}
```

---

## ✅ Health Check

### 12. Verificar Status da API

**Endpoint**: `GET /health`

**Request**:
```bash
curl -X GET http://localhost:8000/api/health
```

**Response** (200):
```json
{
  "status": "ok",
  "message": "API está funcionando"
}
```

---

## 🔑 Segurança: Headers Obrigatórios

### Para Endpoints Protegidos

Todos os endpoints de passwords, wallet e logout **exigem**:

```bash
-H "X-Session-Token: <token_do_login>"
```

**Se não enviar**:
```json
{
  "detail": "Token de sessão inválido"
}
```

**Se token expirado** (60 min):
```json
{
  "detail": "Sessão expirada"
}
```

**Se token de outro usuário**:
```json
{
  "detail": "Token de sessão inválido ou expirado"
}
```

---

## 🚀 Fluxo Completo de Uso

```bash
# 1. Registrar
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"john","email":"john@ex.com","password":"Pass123!"}'

# 2. Login
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john","password":"Pass123!"}' | jq -r '.token')

# 3. Listar senhas
curl -X GET http://localhost:8000/api/passwords \
  -H "X-Session-Token: $TOKEN"

# 4. Criar senha
curl -X POST http://localhost:8000/api/passwords \
  -H "X-Session-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Gmail","site":"gmail.com","encrypted_password":"base64..."}'

# 5. Logout
curl -X POST http://localhost:8000/api/auth/logout \
  -H "X-Session-Token: $TOKEN"
```

---

## 🔍 Isolamento de Dados - Teste de Segurança

```bash
# User A
TOKEN_A=$(curl ... /auth/login com user A)

# User B
TOKEN_B=$(curl ... /auth/login com user B)

# User A cria senha
curl -X POST /api/passwords \
  -H "X-Session-Token: $TOKEN_A" ...

# User B tenta acessar senha de User A (COM TOKEN_B)
curl -X GET /api/passwords/1 \
  -H "X-Session-Token: $TOKEN_B"

# ❌ Response: 404 Não encontrado
# ✅ Isolamento funcionando!
```

---

## 📊 Status Codes

| Code | Significado |
|------|------------|
| 200 | Sucesso |
| 201 | Criado |
| 400 | Erro de validação |
| 401 | Sem autenticação / Token inválido |
| 403 | Sem permissão |
| 404 | Não encontrado / Acesso negado |
| 500 | Erro interno servidor |

---

*Documentação atualizada: 26 de novembro de 2025*
