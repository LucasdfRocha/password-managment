# 🔐 Password Manager — Gerenciador de Senhas Zero-Knowledge

Projeto demonstrativo de um gerenciador de senhas que aplica criptografia no cliente (zero-knowledge): as senhas são cifradas no navegador antes de serem enviadas ao backend.

Tecnologias principais
- Backend: FastAPI + SQLite + bcrypt (para autenticação/hasheamento de senhas)
- Frontend: HTML/CSS/JavaScript + Web Crypto API (AES-GCM + PBKDF2) — criptografia no cliente
- Local: versão local com scripts Python para execução sem servidor web

---

## Estrutura do projeto

```text
password-managment/
├─ backend/
│  ├─ api.py
│  ├─ auth.py
│  ├─ database.py
│  ├─ models.py
│  ├─ password_manager.py
│  ├─ password_generator.py
│  ├─ schemas.py
│  └─ requirements.txt
├─ frontend/
│  ├─ index.html
│  ├─ app.js
│  ├─ stylesheet.css
│  └─ js/
│     ├─ api.js
│     ├─ auth.js
│     ├─ crypto.js
│     └─ ...
└─ local/
   ├─ main.py
   ├─ gui.py
   ├─ encryption.py
   └─ local_requirements.txt
```

## Pré-requisitos
- Python 3.10+ (recomendado)
- `pip` para instalar dependências
- Navegador com suporte ao Web Crypto API (Chrome, Firefox, Edge, etc.)

## Instalação geral

1. Clone o repositório:

```powershell
git clone https://github.com/LucasdfRocha/password-managment.git
cd password-managment
```

2. (Opcional) criar e ativar um ambiente virtual:

```powershell
python -m venv .venv
source .venv/bin/activate
```

3. Instalar dependências do backend:

```powershell
cd backend
pip install -r requirements.txt
```

4. Instalar dependências para a versão local/gui:

```powershell
cd ..\local
pip install -r local_requirements.txt
```

## Executando o backend (API)

Por padrão o backend usa FastAPI/uvicorn e um banco SQLite local. O arquivo de banco (`passwords.db`) será criado automaticamente se não existir.

Exemplo (PowerShell / Python 3):

```powershell
cd backend
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

## Executando o frontend (estático)

O frontend é um conjunto de arquivos estáticos (HTML/JS/CSS) que consomem a API do backend. 

Exemplo (PowerShell / Python 3):

```powershell
cd frontend
python -m http.server 8080 --bind 127.0.0.1

# Abra http://127.0.0.1:8080 no navegador
```

## Executando a versão local (GUI/script)

Há uma pasta `local/` com uma versão que roda localmente (sem servidor). Para usar:

```powershell
cd local
pip install -r local_requirements.txt
python main.py
```

Ou execute `gui.py` se quiser a interface gráfica local com gui em tkinter.

## Modelo de segurança — Zero-Knowledge 

- Criptografia no cliente: chaves derivadas da senha mestra do usuário com PBKDF2; dados (senhas) cifrados com AES-GCM antes de serem enviados ao backend.
- Backend não armazena senhas em texto plano — armazena somente dados cifrados ou hashes necessários para autenticação.


