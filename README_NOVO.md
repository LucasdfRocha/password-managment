# Password Manager - Sistema Multi-Usuário

Um gerenciador de senhas seguro com autenticação de usuários e isolamento de dados.

## 🎯 Funcionalidades

✅ **Autenticação de Usuários**

- Registro de novo usuário
- Login com username/password
- Autenticação via JWT (tokens com expiração de 24h)

✅ **Isolamento de Dados**

- Cada usuário vê apenas suas senhas
- Proteção contra acesso cruzado
- Exclusão de dados ao deletar usuário

✅ **Geração de Senhas**

- Geração automática de senhas seguras
- Customização: maiúsculas, minúsculas, dígitos, especiais
- Cálculo de entropia
- Senhas customizadas (manuais)

✅ **Criptografia**

- AES-256-GCM para criptografia de senhas
- Bcrypt com 12 rounds para hash de senhas de usuário
- Armazenamento seguro no SQLite

✅ **API REST**

- Endpoints para CRUD de senhas
- Gerenciamento de sessões
- Suporte a CORS

## 🚀 Como Usar

### Instalação

```bash
# Clonar repositório
git clone https://github.com/LucasdfRocha/password-managment.git
cd password-managment/backend

# Instalar dependências
pip install -r requirements.txt
```

### Iniciar o Servidor

```bash
# Terminal 1: Backend
cd backend
python api.py
# Servidor disponível em http://localhost:8000

# Terminal 2: Frontend (opcional, ou abra index.html no navegador)
cd frontend
# Abrir index.html em um navegador
```

### Usar a API

#### 1. Registrar Novo Usuário

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "lucas",
    "email": "lucas@example.com",
    "password": "minhasenha123"
  }'

# Resposta:
# {
#   "token": "eyJhbGciOiJIUzI1NiIs...",
#   "message": "Usuário registrado com sucesso"
# }
```

#### 2. Fazer Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "lucas",
    "password": "minhasenha123"
  }'
```

#### 3. Criar Senha

```bash
curl -X POST http://localhost:8000/api/passwords \
  -H "X-Session-Token: SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Gmail",
    "site": "https://mail.google.com",
    "length": 16,
    "use_uppercase": true,
    "use_lowercase": true,
    "use_digits": true,
    "use_special": true
  }'
```

#### 4. Listar Minhas Senhas

```bash
curl -X GET http://localhost:8000/api/passwords \
  -H "X-Session-Token: SEU_TOKEN_AQUI"
```

#### 5. Obter Senha Específica (Descriptografada)

```bash
curl -X GET http://localhost:8000/api/passwords/1 \
  -H "X-Session-Token: SEU_TOKEN_AQUI"

# Resposta:
# {
#   "id": 1,
#   "title": "Gmail",
#   "site": "https://mail.google.com",
#   "password": "minhaSenhaGerada123!",
#   "length": 16,
#   "entropy": 94.4,
#   "entropy_level": "Strong"
#   ...
# }
```

#### 6. Fazer Logout

```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "X-Session-Token: SEU_TOKEN_AQUI"
```

## 🧪 Testes

### Teste do Sistema de Autenticação

```bash
python test_auth_system.py
```

Resultados esperados:

- ✓ Registro de usuário
- ✓ Login com credenciais corretas
- ✓ Rejeição de credenciais incorretas
- ✓ Validação de token JWT
- ✓ Criação e listagem de senhas

### Teste de Isolamento de Dados

```bash
python test_data_isolation.py
```

Verifica:

- ✓ Usuários diferentes não veem senhas um do outro
- ✓ Proteção contra acesso cruzado
- ✓ Deleção isolada por usuário

### Teste de Integração da API

```bash
# (Assumindo que o servidor está rodando)
python test_api_integration.py
```

## 📁 Estrutura

```
password-managment/
├── backend/
│   ├── api.py                    # API FastAPI principal
│   ├── auth.py                   # Sistema de autenticação JWT
│   ├── models.py                 # Modelos de dados
│   ├── database.py               # Gerenciador SQLite
│   ├── password_manager.py       # Gerenciador de senhas
│   ├── encryption.py             # Criptografia AES-256-GCM
│   ├── password_generator.py     # Gerador de senhas
│   ├── schemas.py                # Schemas Pydantic
│   ├── requirements.txt          # Dependências
│   ├── test_auth_system.py       # Teste de autenticação
│   ├── test_data_isolation.py    # Teste de isolamento
│   └── test_api_integration.py   # Teste da API
│
├── frontend/
│   └── index.html                # Interface web (login/senhas)
│
└── AUTH_SYSTEM_DOCS.md           # Documentação técnica
```

## 🔐 Segurança

### ✅ Implementado

- **Hashing de Senha**: Bcrypt com 12 rounds (PBKDF2 em produção)
- **Criptografia**: AES-256-GCM para senhas armazenadas
- **Autenticação**: JWT com expiração de 24 horas
- **Isolamento**: Cada usuário só acessa seus dados
- **Validação**: Schemas Pydantic na API

### ⚠️ TODO em Produção

- [ ] Usar HTTPS obrigatório
- [ ] Mudar `SECRET_KEY` via variável de ambiente
- [ ] Implementar rate limiting
- [ ] CORS mais restritivo
- [ ] Verificação de email
- [ ] Refresh tokens
- [ ] Logs de auditoria
- [ ] Banco de dados não-SQLite (PostgreSQL)

## 📝 Endpoints da API

| Método | Endpoint                  | Descrição                    |
| ------ | ------------------------- | ---------------------------- |
| POST   | `/api/auth/register`      | Registrar novo usuário       |
| POST   | `/api/auth/login`         | Fazer login                  |
| POST   | `/api/auth/logout`        | Fazer logout                 |
| POST   | `/api/passwords`          | Criar nova senha             |
| GET    | `/api/passwords`          | Listar minhas senhas         |
| GET    | `/api/passwords/{id}`     | Obter senha descriptografada |
| PUT    | `/api/passwords/{id}`     | Atualizar senha              |
| DELETE | `/api/passwords/{id}`     | Deletar senha                |
| POST   | `/api/passwords/generate` | Gerar senha de teste         |
| GET    | `/api/health`             | Health check                 |

## 🛠 Stack Tecnológico

- **Backend**: FastAPI (Python)
- **Banco de Dados**: SQLite
- **Autenticação**: JWT + Bcrypt
- **Criptografia**: AES-256-GCM
- **Frontend**: HTML5 + Vanilla JavaScript

## 📦 Dependências

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
bcrypt==5.0.0
PyJWT==2.10.1
cryptography==41.0.7
pycryptodome==3.19.0
```

## 🐛 Troubleshooting

### Erro: "Secret key not found"

Defina a variável de ambiente:

```bash
export JWT_SECRET_KEY="sua-chave-segura-aqui"
```

### Erro: "Database is locked"

SQLite travou. Reinicie o servidor e tente novamente.

### CORS Error

Verifique que o frontend está acessando `http://localhost:8000`

## 📄 Licença

MIT - Veja LICENSE para detalhes

## 👤 Autor

Lucas df Rocha

---

**Status**: ✅ Funcional para uso local

**Última atualização**: Novembro 2025
