# Gerenciador de Senhas com Criptografia

Sistema de gerenciamento de senhas com criptografia em Python, utilizando SQLite como banco de dados.

## Características

- ✅ CRUD completo de senhas
- ✅ Criptografia AES-128 (Fernet) com PBKDF2
- ✅ Geração de senhas customizáveis
- ✅ Cálculo de entropia e classificação de segurança
- ✅ Suporte a data de expiração
- ✅ Exportação/Importação de wallet (cold/hot)
- ✅ Interface CLI interativa
- ✅ **API REST com FastAPI** para integração com front-end
- ✅ Documentação automática da API (Swagger/OpenAPI)
- ✅ CORS configurado para requisições do front-end

## Instalação

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd password-managment
```

1.1 Acesse a pasta do backend:

```bash
cd backend
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Uso

### Modo CLI (Terminal)

Execute o programa:
```bash
python3 main.py
```

Você será solicitado a inserir uma senha mestra. Esta senha será usada para criptografar todas as suas senhas armazenadas.

### Modo API (Front-end)

1. Inicie o servidor da API:
```bash
python3 api.py
```

Ou usando uvicorn diretamente:
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

2. Acesse a documentação interativa da API:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

3. **Autenticação**: 
   - Primeiro, faça login em `POST /api/auth/login` com sua senha mestra
   - Você receberá um token de sessão
   - Use este token no header `X-Session-Token` em todas as requisições subsequentes

#### Exemplo de uso da API

```bash
# 1. Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"master_password": "sua_senha_mestra"}'

# Resposta: {"token": "seu_token_aqui", "message": "Login realizado com sucesso"}

# 2. Criar senha (usando o token recebido)
curl -X POST "http://localhost:8000/api/passwords" \
  -H "Content-Type: application/json" \
  -H "X-Session-Token: seu_token_aqui" \
  -d '{
    "title": "Gmail",
    "site": "gmail.com",
    "length": 16,
    "use_uppercase": true,
    "use_lowercase": true,
    "use_digits": true,
    "use_special": true
  }'

# 3. Listar todas as senhas
curl -X GET "http://localhost:8000/api/passwords" \
  -H "X-Session-Token: seu_token_aqui"

# 4. Obter senha específica (com senha descriptografada)
curl -X GET "http://localhost:8000/api/passwords/1" \
  -H "X-Session-Token: seu_token_aqui"

# 5. Atualizar senha
curl -X PUT "http://localhost:8000/api/passwords/1" \
  -H "Content-Type: application/json" \
  -H "X-Session-Token: seu_token_aqui" \
  -d '{
    "title": "Gmail Atualizado",
    "regenerate": true
  }'

# 6. Deletar senha
curl -X DELETE "http://localhost:8000/api/passwords/1" \
  -H "X-Session-Token: seu_token_aqui"

# 7. Gerar senha de teste
curl -X POST "http://localhost:8000/api/passwords/generate" \
  -H "Content-Type: application/json" \
  -H "X-Session-Token: seu_token_aqui" \
  -d '{
    "length": 20,
    "use_uppercase": true,
    "use_lowercase": true,
    "use_digits": true,
    "use_special": true
  }'

# 8. Logout
curl -X POST "http://localhost:8000/api/auth/logout" \
  -H "X-Session-Token: seu_token_aqui"
```

#### Integração com Front-end (JavaScript/TypeScript)

```javascript
const API_BASE_URL = 'http://localhost:8000/api';

// Login
async function login(masterPassword) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ master_password: masterPassword })
  });
  const data = await response.json();
  localStorage.setItem('sessionToken', data.token);
  return data.token;
}

// Criar senha
async function createPassword(passwordData) {
  const token = localStorage.getItem('sessionToken');
  const response = await fetch(`${API_BASE_URL}/passwords`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Session-Token': token
    },
    body: JSON.stringify(passwordData)
  });
  return await response.json();
}

// Listar senhas
async function listPasswords() {
  const token = localStorage.getItem('sessionToken');
  const response = await fetch(`${API_BASE_URL}/passwords`, {
    headers: { 'X-Session-Token': token }
  });
  return await response.json();
}

// Obter senha específica
async function getPassword(id) {
  const token = localStorage.getItem('sessionToken');
  const response = await fetch(`${API_BASE_URL}/passwords/${id}`, {
    headers: { 'X-Session-Token': token }
  });
  return await response.json();
}
```

### Funcionalidades

1. **Criar nova senha**: Gera uma senha aleatória ou permite inserir uma senha customizada
2. **Listar todas as senhas**: Mostra todas as senhas cadastradas (sem mostrar a senha em si)
3. **Ver senha**: Visualiza uma senha específica descriptografada
4. **Atualizar senha**: Modifica informações de uma senha ou regenera a senha
5. **Deletar senha**: Remove uma senha do banco de dados
6. **Exportar wallet**: Exporta todas as senhas para um arquivo criptografado (cold/hot wallet)
7. **Importar wallet**: Importa senhas de um arquivo wallet
8. **Gerar senha de teste**: Gera uma senha sem salvar (para testar configurações)

### Opções de Geração de Senha

Ao criar ou atualizar uma senha, você pode escolher:
- **Tamanho**: Comprimento da senha
- **Letras maiúsculas**: Incluir A-Z
- **Letras minúsculas**: Incluir a-z
- **Dígitos**: Incluir 0-9
- **Caracteres especiais**: Incluir !@#$%^&*()_+-=[]{}|;:,.<>?

### Entropia

O sistema calcula automaticamente a entropia de cada senha:
- **Fraco**: < 28 bits
- **Médio**: 28-35 bits
- **Forte**: 36-59 bits
- **Muito Forte**: ≥ 60 bits

### Wallet (Cold/Hot)

O sistema permite exportar todas as senhas para um arquivo wallet criptografado com uma senha separada. Isso permite:
- **Cold Wallet**: Armazenar offline em um dispositivo seguro
- **Hot Wallet**: Ter uma cópia para uso diário

O arquivo wallet pode ser importado em outra instalação do sistema.

## Estrutura do Projeto

```
password-managment/
├── main.py                 # Interface CLI principal
├── api.py                  # API REST com FastAPI
├── auth.py                 # Sistema de autenticação/sessões
├── schemas.py              # Schemas Pydantic para validação
├── password_manager.py     # Lógica de negócio e CRUD
├── database.py             # Gerenciamento do SQLite
├── encryption.py           # Sistema de criptografia
├── password_generator.py   # Geração de senhas e cálculo de entropia
├── wallet.py               # Exportação/importação de wallet
├── models.py               # Modelos de dados
├── requirements.txt        # Dependências
└── README.md              # Este arquivo
```

## Segurança

- Todas as senhas são criptografadas usando AES-128 (Fernet)
- A chave de criptografia é derivada da senha mestra usando PBKDF2 (100.000 iterações)
- O salt é armazenado localmente no arquivo `.salt`
- O banco de dados SQLite armazena apenas senhas criptografadas
- O wallet usa criptografia separada com senha própria

## Notas Importantes

⚠️ **IMPORTANTE**: 
- Guarde sua senha mestra com segurança. Sem ela, não será possível recuperar suas senhas.
- O arquivo `.salt` é necessário para descriptografar as senhas. Mantenha-o seguro junto com o banco de dados.
- Faça backups regulares do arquivo `passwords.db` e `.salt`.

## Licença

Este projeto é para fins educacionais.
