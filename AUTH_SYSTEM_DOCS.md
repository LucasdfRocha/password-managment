# Sistema de Autenticação de Usuários - Documentação

## Resumo das Mudanças

O gerenciador de senhas foi atualizado para suportar um sistema de autenticação de múltiplos usuários com login/senha persistente no banco de dados. Cada usuário agora só vê suas próprias senhas.

## Principais Alterações

### 1. **Modelos de Dados (models.py)**

- Adicionado novo modelo `User` com campos:

  - `username`: Nome de usuário único
  - `email`: Email único
  - `password_hash`: Hash bcrypt da senha
  - `created_at`, `updated_at`: Timestamps

- Atualizado `PasswordEntry` para incluir:
  - `user_id`: Relacionamento com o usuário que possui a senha

### 2. **Banco de Dados (database.py)**

- Criada tabela `users` com:

  - Índice único em `username` e `email`
  - Hash seguro de senha

- Tabela `password_entries` agora contém:

  - Chave estrangeira `user_id` com delete cascata
  - Todos os métodos foram atualizados para receber `user_id`

- Novos métodos de usuário:
  - `create_user()`: Cria novo usuário
  - `get_user_by_username()`: Busca usuário por nome
  - `get_user_by_id()`: Busca usuário por ID

### 3. **Autenticação (auth.py)**

- Substituído sistema de tokens simples por **JWT (JSON Web Tokens)**
- Novos métodos:

  - `register_user()`: Registra novo usuário com validações
  - `login()`: Autentica com username/password
  - `verify_token()`: Valida e decodifica JWT
  - `hash_password()`: Hash seguro com bcrypt (12 rounds)
  - `verify_password()`: Compara senha com hash

- Recursos:
  - Tokens expiram em 24 horas
  - Secret key (deve ser mudada em produção via variável de ambiente)
  - Sessões armazenadas em memória durante a sessão do servidor

### 4. **Gerenciador de Senhas (password_manager.py)**

- Adicionado atributo `user_id` ao `PasswordManager`
- Todos os métodos agora validam `user_id`:
  - `create_password()`: Requer `user_id` definido
  - `get_all_passwords()`: Retorna apenas senhas do usuário
  - `get_password()`: Valida propriedade antes de retornar
  - `update_password()`: Valida propriedade antes de atualizar
  - `delete_password()`: Valida propriedade antes de deletar

### 5. **API (api.py)**

- Novos endpoints:

  - `POST /api/auth/register`: Registra novo usuário
  - `POST /api/auth/login`: Autentica usuário

- Endpoints antigos mantidos:

  - `POST /api/auth/logout`: Encerra sessão

- Dependency `get_password_manager()` agora:
  - Valida JWT
  - Extrai `user_id` do token
  - Associa `user_id` ao `PasswordManager`

### 6. **Schemas (schemas.py)**

- Novos schemas:

  - `UserRegisterRequest`: username, email, password
  - `UserLoginRequest`: username, password
  - `UserResponse`: token, message

- Schema removido:
  - `MasterPasswordRequest` (não mais necessário)

### 7. **Frontend (index.html)**

- Interface renovada com dois formulários:

  - **Login**: username + password
  - **Registro**: username + email + password

- Funcionalidades:
  - Botão para alternar entre login e registro
  - Validação básica de campos
  - Tokens JWT armazenados e enviados em headers
  - Cada usuário vê apenas suas senhas

## Fluxo de Autenticação

```
1. Novo Usuário?
   ├─ Preenche: username, email, password
   ├─ POST /api/auth/register
   ├─ Recebe: token JWT
   └─ Entra na app

2. Usuário Existente?
   ├─ Preenche: username, password
   ├─ POST /api/auth/login
   ├─ Recebe: token JWT
   └─ Entra na app

3. Dentro da App:
   ├─ Token enviado em: header "X-Session-Token"
   ├─ Token validado em cada requisição
   ├─ user_id extraído do token
   ├─ Operações filtradas por user_id
   └─ Logout remove sessão
```

## Segurança

### ✓ Implementado

- Hashing bcrypt com 12 rounds (salt seguro)
- JWT com expiração de 24h
- Validação de entrada básica
- Isolamento de dados por usuário
- Criptografia de senhas com AES-256-GCM

### ⚠️ TODO em Produção

- Mudar `SECRET_KEY` em auth.py via variável de ambiente
- HTTPS obrigatório
- Rate limiting em login/registro
- CORS mais restritivo (não usar `allow_origins=["*"]`)
- Adicionar email verification
- Implementar refresh tokens
- Adicionar logs de auditoria

## Teste Local

Executar:

```bash
cd backend
python test_auth_system.py
```

Resultado esperado: Todos os testes devem passar ✓

## Exemplo de Uso da API

### Registrar

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "lucas",
    "email": "lucas@example.com",
    "password": "minhasenha123"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "lucas",
    "password": "minhasenha123"
  }'
```

### Usar Token

```bash
curl -X GET http://localhost:8000/api/passwords \
  -H "X-Session-Token: eyJhbGciOiJIUzI1NiIs..."
```

## Compatibilidade

- ✓ Python 3.8+
- ✓ FastAPI 0.104.1
- ✓ SQLite 3
- ✓ Bcrypt 5.0.0
- ✓ PyJWT 2.10.1
- ✓ Cryptography 41.0.7
