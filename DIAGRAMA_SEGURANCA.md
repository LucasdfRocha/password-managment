# Diagrama de Arquitetura de Segurança - Session Fixation Protection

## 🏗️ Arquitetura de Autenticação

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Cliente)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. Usuário digita: username + senha                               │
│  2. HTML submit: POST /auth/login { username, password }           │
│  3. Recebe resposta:                                               │
│     {                                                              │
│       "token": "abc123..." (armazenar em memória)                  │
│       "user_id": 42,                                              │
│       "username": "john_doe"                                      │
│     }                                                              │
│  4. Próximos requests enviam:                                     │
│     Header: X-Session-Token: abc123...                           │
│                                                                    │
│  💡 PROTEÇÃO: Master password armazenada em RAM                   │
│     (não em localStorage/cookie para HTTPS-ready)                │
│                                                                    │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
                                 │
                          (HTTP Request)
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    BACKEND (API - FastAPI)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  @app.post("/auth/login")                                          │
│  ├─ Recebe: { username, password }                                │
│  ├─ Busca user no DB: user = db.get_user_by_username(username)   │
│  ├─ Valida senha: bcrypt.checkpw(password, user.password_hash)   │
│  │                                                                 │
│  │  🔐 PROTEÇÃO 1: Bcrypt Hash (não reversível)                  │
│  │     password_hash = bcrypt.hashpw(password, gensalt(12))      │
│  │     └─ Cost=12 = ~100ms por hash                              │
│  │     └─ Impossível fazer rainbow tables                        │
│  │                                                                 │
│  ├─ Gera NOVO token:                                             │
│  │  token = secrets.token_urlsafe(32)  # 192 bits aleatórios    │
│  │                                                                │
│  │  🔐 PROTEÇÃO 2: Token único a cada login                     │
│  │     └─ Cada login = novo token                              │
│  │     └─ Token anterior é DESCARTADO                          │
│  │     └─ Impossível reutilizar token antigo                   │
│  │                                                                │
│  ├─ Cria SessionInfo:                                            │
│  │  SessionInfo(                                                │
│  │    user_id=42,              # ← Vinculado ao usuário        │
│  │    token="abc123...",       # ← Token novo                  │
│  │    created_at=datetime.now() # ← Para timeout               │
│  │  )                                                           │
│  │                                                              │
│  │  🔐 PROTEÇÃO 3: Vinculação token ↔ user_id                │
│  │     └─ Mesmo que alguém roube token                        │
│  │     └─ Funciona apenas para user_id=42                    │
│  │                                                              │
│  ├─ Armazena em memoria:                                       │
│  │  sessions["abc123..."] = SessionInfo(42, "abc123...")      │
│  │                                                              │
│  └─ Responde:                                                  │
│     {                                                          │
│       "token": "abc123...",                                   │
│       "user_id": 42,                                          │
│       "username": "john_doe"                                  │
│     }                                                          │
│                                                                │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
                                 │
                          (HTTP Response)
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│              CLIENT - Armazena token em memória                      │
│              (sessionToken = data.token)                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Fluxo: Acessar Recurso Protegido

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CLIENTE: GET /api/passwords                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  fetch('/api/passwords', {                                         │
│    headers: {                                                      │
│      'X-Session-Token': 'abc123...'  ← Token do login             │
│    }                                                              │
│  })                                                               │
│                                                                    │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
                    X-Session-Token: abc123...
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    SERVIDOR: Dependency Injection                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  def get_user_from_token(token = Header('X-Session-Token')) → Tuple │
│    ├─ is_valid, user_id, msg = auth_manager.validate_session(tok) │
│    │                                                               │
│    │  🔐 PROTEÇÃO 4: Validação de token                          │
│    │  └─ Token existe em sessions?                              │
│    │     if token not in sessions:                              │
│    │       return (False, None, "Token inválido")               │
│    │                                                             │
│    │  🔐 PROTEÇÃO 5: Timeout de sessão                         │
│    │  └─ Sessão expirada (60 min)?                            │
│    │     if now - created_at > 60 min:                         │
│    │       return (False, None, "Sessão expirada")            │
│    │                                                            │
│    ├─ if not is_valid:                                         │
│    │   raise HTTPException(401, "Unauthorized")               │
│    │                                                            │
│    ├─ pm = auth_manager.get_password_manager(token)           │
│    │                                                            │
│    └─ return (pm, user_id=42)                                 │
│                                                                 │
│  @app.get("/api/passwords")                                    │
│  async def list_passwords(pm_and_user = Depends(get_user...)) │
│    pm, user_id = pm_and_user                                  │
│    ├─ entries = pm.get_all_passwords(user_id=42)            │
│    │                                                          │
│    │  🔐 PROTEÇÃO 6: Filtragem por user_id                 │
│    │  └─ Retorna apenas senhas onde user_id=42            │
│    │     SELECT * FROM passwords WHERE user_id = 42        │
│    │                                                        │
│    └─ return entries                                        │
│                                                             │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
                    [senha1, senha2, senha3]
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│              CLIENTE: Recebe apenas suas senhas                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🚨 Cenários de Ataque & Defesas

### Ataque 1: Session Fixation

```
ANTES (Vulnerável):
└─ Ataque funciona:
   1. Adversário gera token_123
   2. Vítima faz login → recebe token_123
   3. Adversário usa token_123 → Acesso concedido ❌

DEPOIS (Seguro):
└─ Ataque FALHA:
   1. Servidor gera token_novo a cada login
   2. Token antigo (token_123) é DESCARTADO
   3. Adversário tenta usar token_123 → 401 Unauthorized ✅
```

### Ataque 2: Token Hijacking (Roubo de Token)

```
ANTES (Vulnerável):
└─ Adversário rouba token_ABC → tem acesso indefinido ❌

DEPOIS (Com Timeout):
└─ Adversário rouba token_ABC:
   1. Se < 60 min: tem acesso limitado ao prazo
   2. Se > 60 min: token expirado, precisa novo login
   3. Logout automático em 60 min de inatividade ✅
```

### Ataque 3: Privilege Escalation (Acessar senha de outro usuário)

```
ANTES (Vulnerável):
└─ GET /api/passwords/1  (sem user_id check)
   └─ Retorna qualquer senha com ID=1 ❌

DEPOIS (Com Isolamento):
└─ GET /api/passwords/1
   └─ Valida: entry.user_id == token.user_id?
   └─ Se NÃO: 404 Não encontrado ✅
```

### Ataque 4: Brute Force de Senhas

```
ANTES (Vulnerável):
└─ Rápido: MD5 hash = 1 bilhão tentativas/sec ❌

DEPOIS (Com Bcrypt):
└─ Lento: bcrypt(cost=12) = 1 tentativa a cada ~100ms
└─ 10 tentativas = 1 segundo
└─ 1.000.000 tentativas = ~11 dias ✅
└─ Rate limiting pode adicionar delay exponencial
```

### Ataque 5: Reutilização de Token Antigo

```
ANTES:
└─ Usuário faz login → token_ABC
└─ Usuário faz novo login → MESMO token_ABC
└─ Adversário pode reutilizar token_ABC indefinidamente ❌

DEPOIS:
└─ Usuário faz login #1 → token_ABC (armazenado)
└─ Usuário faz login #2 → token_XYZ (novo token)
└─ Token_ABC é descartado
└─ Qualquer uso de token_ABC → 401 ✅
```

---

## 🔐 Camadas de Proteção

```
Layer 1: REGISTRO
├─ Username único (no banco)
├─ Email único (no banco)
└─ Senha ≥ 8 caracteres (validado no backend)

Layer 2: LOGIN
├─ Validar username existe
├─ Comparar senha com bcrypt hash
└─ Gerar token novo (nunca reutilizar)

Layer 3: SESSION
├─ Token vinculado a user_id
├─ Validar timeout (60 min)
└─ Armazenar em memória (não persistente)

Layer 4: REQUESTS
├─ Header X-Session-Token obrigatório
├─ Validar token existe + não expirado
└─ Retornar user_id para isolamento

Layer 5: QUERIES
├─ Todas as queries filtram por user_id
├─ DELETE/UPDATE verificam propriedade
└─ Impossível acessar recurso de outro usuário

Layer 6: CRIPTOGRAFIA E2E
├─ Senha criptografada no cliente
├─ Servidor armazena apenas blob
└─ Servidor nunca vê senha descriptografada
```

---

## 📊 Comparação: Antes vs Depois

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Autenticação** | Apenas senha mestra | Username + Email + Senha |
| **Hash** | Sem hash (vulnerável) | Bcrypt cost=12 |
| **Token** | Mesmos token reutilizado | Token novo a cada login |
| **Vinculação** | Token sem user_id | Token vinculado a user_id |
| **Timeout** | Sem timeout | 60 min de inatividade |
| **Isolamento** | Todos veem todas as senhas | Cada usuário vê apenas suas |
| **DELETE/UPDATE** | Qualquer um pode | Apenas proprietário |
| **Session Fixation** | ❌ Vulnerável | ✅ Protegido |
| **Criptografia** | E2E (bom) | E2E + Isolamento (melhor) |

---

## 🎯 Checklist de Segurança Implementada

```
✅ Autenticação Multi-Usuário
   └─ Username único + Email único + Senha forte

✅ Session Fixation Protection
   └─ Token novo a cada login
   └─ Token vinculado a user_id
   └─ Token anterior invalidado

✅ Session Timeout
   └─ Expiração após 60 min inatividade
   └─ Verificação automática em cada request

✅ Isolamento de Dados
   └─ Cada usuário vê apenas suas senhas
   └─ Verificação de propriedade em operações
   └─ Filtro user_id em todas as queries

✅ Hash Seguro
   └─ Bcrypt com cost=12
   └─ Resistente a brute force
   └─ Resistente a timing attacks

✅ Criptografia E2E
   └─ AES-256-GCM no cliente
   └─ PBKDF2 para derivação de chave
   └─ Servidor não descriptografa

✅ Validações
   └─ Username ≥ 3 caracteres
   └─ Email válido
   └─ Senha ≥ 8 caracteres

✅ Proteção OWASP
   └─ A01:2021 – Broken Access Control ✅
   └─ A02:2021 – Cryptographic Failures ✅
   └─ A06:2021 – Vulnerable and Outdated ✅
   └─ A07:2021 – Identification and Auth ✅
```

---

## 🚀 Próximas Melhorias (Recomendadas)

1. **Rate Limiting**: 5 tentativas de login/min
2. **IP Blacklisting**: Bloquear IP com muitas falhas
3. **2FA**: Autenticação de dois fatores
4. **JWT com Refresh Tokens**: Para sessões mais longas
5. **HTTPS Obrigatório**: Em produção
6. **Audit Log**: Registrar todas as operações sensíveis
7. **Password Rotation**: Exigir mudança periódica
8. **Passwordless Auth**: Biometria, WebAuthn
9. **CORS Restrito**: Whitelist de domínios
10. **CSP Headers**: Content Security Policy

---

*Diagrama de Segurança - Session Fixation Protection*  
*Versão 2.0.0 - Multi-User Release*  
*26 de novembro de 2025*
