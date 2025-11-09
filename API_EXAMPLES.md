# Exemplos de Uso da API

## Endpoints Disponíveis

### Autenticação

#### POST `/api/auth/login`
Autentica o usuário e retorna um token de sessão.

**Request:**
```json
{
  "master_password": "sua_senha_mestra"
}
```

**Response:**
```json
{
  "token": "token_gerado_aqui",
  "message": "Login realizado com sucesso"
}
```

#### POST `/api/auth/logout`
Encerra a sessão do usuário.

**Headers:**
- `X-Session-Token: seu_token_aqui`

**Response:**
```json
{
  "message": "Logout realizado com sucesso"
}
```

### Senhas

#### POST `/api/passwords`
Cria uma nova senha.

**Headers:**
- `X-Session-Token: seu_token_aqui`
- `Content-Type: application/json`

**Request:**
```json
{
  "title": "Gmail",
  "site": "gmail.com",
  "length": 16,
  "use_uppercase": true,
  "use_lowercase": true,
  "use_digits": true,
  "use_special": true,
  "expiration_date": "2025-12-31T00:00:00",
  "custom_password": null
}
```

**Response:**
```json
{
  "id": 1,
  "title": "Gmail",
  "site": "gmail.com",
  "length": 16,
  "use_uppercase": true,
  "use_lowercase": true,
  "use_digits": true,
  "use_special": true,
  "entropy": 95.27,
  "entropy_level": "Muito Forte",
  "expiration_date": "2025-12-31T00:00:00",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

#### GET `/api/passwords`
Lista todas as senhas (sem mostrar a senha descriptografada).

**Headers:**
- `X-Session-Token: seu_token_aqui`

**Response:**
```json
[
  {
    "id": 1,
    "title": "Gmail",
    "site": "gmail.com",
    "length": 16,
    "use_uppercase": true,
    "use_lowercase": true,
    "use_digits": true,
    "use_special": true,
    "entropy": 95.27,
    "entropy_level": "Muito Forte",
    "expiration_date": "2025-12-31T00:00:00",
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
  }
]
```

#### GET `/api/passwords/{id}`
Obtém uma senha específica com a senha descriptografada.

**Headers:**
- `X-Session-Token: seu_token_aqui`

**Response:**
```json
{
  "id": 1,
  "title": "Gmail",
  "site": "gmail.com",
  "password": "aB3$kL9#mN2@qR7",
  "length": 16,
  "use_uppercase": true,
  "use_lowercase": true,
  "use_digits": true,
  "use_special": true,
  "entropy": 95.27,
  "entropy_level": "Muito Forte",
  "expiration_date": "2025-12-31T00:00:00",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

#### PUT `/api/passwords/{id}`
Atualiza uma senha.

**Headers:**
- `X-Session-Token: seu_token_aqui`
- `Content-Type: application/json`

**Request:**
```json
{
  "title": "Gmail Atualizado",
  "regenerate": true
}
```

**Response:**
```json
{
  "id": 1,
  "title": "Gmail Atualizado",
  "site": "gmail.com",
  "length": 16,
  "use_uppercase": true,
  "use_lowercase": true,
  "use_digits": true,
  "use_special": true,
  "entropy": 95.27,
  "entropy_level": "Muito Forte",
  "expiration_date": "2025-12-31T00:00:00",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T11:00:00"
}
```

#### DELETE `/api/passwords/{id}`
Deleta uma senha.

**Headers:**
- `X-Session-Token: seu_token_aqui`

**Response:**
```json
{
  "message": "Senha deletada com sucesso",
  "success": true
}
```

#### POST `/api/passwords/generate`
Gera uma senha de teste sem salvar.

**Headers:**
- `X-Session-Token: seu_token_aqui`
- `Content-Type: application/json`

**Request:**
```json
{
  "length": 20,
  "use_uppercase": true,
  "use_lowercase": true,
  "use_digits": true,
  "use_special": true
}
```

**Response:**
```json
{
  "password": "aB3$kL9#mN2@qR7xY5",
  "length": 20,
  "entropy": 119.09,
  "entropy_level": "Muito Forte"
}
```

### Wallet

#### POST `/api/wallet/export`
Exporta todas as senhas para um arquivo wallet.

**Headers:**
- `X-Session-Token: seu_token_aqui`
- `Content-Type: application/json`

**Request:**
```json
{
  "wallet_password": "senha_do_wallet",
  "output_file": "wallet.enc"
}
```

**Response:**
```json
{
  "message": "Wallet exportado com sucesso para wallet.enc",
  "success": true
}
```

#### POST `/api/wallet/import`
Importa senhas de um arquivo wallet.

**Headers:**
- `X-Session-Token: seu_token_aqui`
- `Content-Type: application/json`

**Request:**
```json
{
  "wallet_file": "wallet.enc",
  "wallet_password": "senha_do_wallet"
}
```

**Response:**
```json
{
  "message": "5 entradas importadas com sucesso",
  "success": true
}
```

### Health Check

#### GET `/api/health`
Verifica o status da API.

**Response:**
```json
{
  "status": "ok",
  "message": "API está funcionando"
}
```

## Códigos de Status HTTP

- `200 OK`: Requisição bem-sucedida
- `201 Created`: Recurso criado com sucesso
- `400 Bad Request`: Erro na requisição (dados inválidos)
- `401 Unauthorized`: Token de sessão inválido ou ausente
- `404 Not Found`: Recurso não encontrado
- `500 Internal Server Error`: Erro interno do servidor

