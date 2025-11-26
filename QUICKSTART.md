# 🚀 Guia Rápido - Password Manager Multi-Usuário

## Antes de Começar

Certifique-se de ter Python 3.8+ instalado:

```bash
python --version
```

## 5 Minutos para Começar

### 1️⃣ Instalar Dependências

```bash
cd backend
pip install -r requirements.txt
```

✅ Pronto! Todas as dependências instaladas (FastAPI, Bcrypt, JWT, etc)

### 2️⃣ Iniciar o Servidor Backend

```bash
python api.py
```

Você verá:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
Press CTRL+C to quit
```

### 3️⃣ Abrir o Frontend

- **Opção 1**: Abrir `frontend/index.html` no navegador
- **Opção 2**: Usar um live server (VS Code Live Server extension)
- **Opção 3**: Usar Python:
  ```bash
  cd frontend
  python -m http.server 8001
  # Abra http://localhost:8001
  ```

### 4️⃣ Usar a Aplicação

#### Na Interface Web:

1. **Registrar**:

   - Clique em "Novo Usuário?"
   - Preencha username, email, senha
   - Clique em "Registrar"

2. **Login**:

   - Preencha username e senha
   - Clique em "Login"

3. **Criar Senha**:

   - Preencha título (ex: "Gmail")
   - Preencha site (ex: "https://mail.google.com")
   - Configure opções (maiúsculas, dígitos, etc)
   - Clique em "Criar senha"

4. **Ver Senha**:
   - Clique em "Ver" na tabela
   - A senha descriptografada aparece abaixo

#### Pela API (com curl):

```bash
# 1. Registrar
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"seu_user","email":"seu@email.com","password":"senha123"}'

# Salve o token retornado

# 2. Criar senha
TOKEN="seu_token_aqui"
curl -X POST http://localhost:8000/api/passwords \
  -H "X-Session-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"Gmail",
    "site":"https://mail.google.com",
    "length":16,
    "use_uppercase":true,
    "use_lowercase":true,
    "use_digits":true,
    "use_special":true
  }'

# 3. Listar senhas
curl -X GET http://localhost:8000/api/passwords \
  -H "X-Session-Token: $TOKEN"
```

## ✅ Verificar que Tudo Funciona

Execute os testes:

```bash
# Teste 1: Sistema de autenticação
python test_auth_system.py

# Teste 2: Isolamento de dados
python test_data_isolation.py
```

Resultado esperado: Todos os testes com ✓

## 📊 Dados de Teste

Banco de dados é criado automaticamente em `backend/passwords.db`

Primeira vez? Use:

```
username: testuser
email: test@example.com
password: password123
```

## 🔑 Pontos-Chave

| Aspecto                | Detalhes                           |
| ---------------------- | ---------------------------------- |
| **Autenticação**       | JWT com expiração de 24h           |
| **Senha do Usuário**   | Hash com Bcrypt (12 rounds)        |
| **Senhas Armazenadas** | Criptografia AES-256-GCM           |
| **Isolamento**         | Cada usuário vê apenas suas senhas |
| **Banco de Dados**     | SQLite (arquivo `passwords.db`)    |

## 🆘 Problemas Comuns

### Porta 8000 já está em uso

```bash
# Mate o processo
# Windows: netstat -ano | findstr :8000
# Linux: lsof -i :8000
```

### "Module not found"

```bash
# Reinstale dependências
pip install -r requirements.txt --force-reinstall
```

### Erro de CORS

- Certifique-se que frontend acessa `http://localhost:8000`
- Frontend deve estar em `http://localhost:8001` ou `file://`

### Banco de dados corrompido

```bash
# Remova e deixe recrear
rm backend/passwords.db
# Reinicie o servidor
```

## 📚 Próximas Etapas

1. ✅ **Sistema funcionando** - Continue abaixo
2. 🔒 **Produção** - Veja seção "TODO em Produção" no README
3. 🗂️ **Backup de Senhas** - Use a função "Export Wallet"
4. 📱 **App Mobile** - Adapte a API para Mobile
5. ☁️ **Deploy** - Heroku, AWS, ou seu servidor

## 🎯 Status do Sistema

- ✅ Autenticação multi-usuário
- ✅ Geração de senhas
- ✅ Criptografia segura
- ✅ API REST completa
- ✅ Frontend responsivo
- ✅ Testes de isolamento
- ⏳ TODO: Email verification
- ⏳ TODO: Autenticação de dois fatores (2FA)

---

**Pronto para usar!** 🎉

Dúvidas? Veja `AUTH_SYSTEM_DOCS.md` para detalhes técnicos.
