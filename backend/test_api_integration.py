"""
Teste de integração da API REST
"""
import requests
import json
import time
import os
from subprocess import Popen, PIPE

# Limpar BD anterior
if os.path.exists("passwords.db"):
    os.remove("passwords.db")

API_URL = "http://localhost:8000/api"

print("=== Teste de Integração da API ===\n")

# Iniciar servidor em background
print("1. Iniciando servidor FastAPI...")
server_process = None
try:
    import uvicorn
    # Não vamos iniciar o servidor aqui, assumimos que está rodando
    print("   Assumindo que o servidor está rodando em http://localhost:8000")
except:
    pass

time.sleep(2)

# Tentar registrar novo usuário
print("\n2. Testando registro de usuário...")
try:
    resp = requests.post(f"{API_URL}/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    if resp.status_code == 200:
        data = resp.json()
        token = data.get("token")
        print(f"   ✓ Registro bem-sucedido!")
        print(f"   Token: {token[:30]}...")
    else:
        print(f"   ✗ Erro: {resp.status_code} - {resp.text}")
except Exception as e:
    print(f"   ✗ Erro de conexão: {e}")
    print("   Certifique-se de que o servidor está rodando com: python api.py")
    exit(1)

# Testar login
print("\n3. Testando login...")
try:
    resp = requests.post(f"{API_URL}/auth/login", json={
        "username": "testuser",
        "password": "password123"
    })
    if resp.status_code == 200:
        data = resp.json()
        token = data.get("token")
        print(f"   ✓ Login bem-sucedido!")
    else:
        print(f"   ✗ Erro: {resp.status_code}")
except Exception as e:
    print(f"   ✗ Erro: {e}")

# Criar senha
print("\n4. Testando criação de senha...")
try:
    headers = {"X-Session-Token": token}
    resp = requests.post(f"{API_URL}/passwords", 
        json={
            "title": "Gmail",
            "site": "https://mail.google.com",
            "length": 16,
            "use_uppercase": True,
            "use_lowercase": True,
            "use_digits": True,
            "use_special": True
        },
        headers=headers
    )
    if resp.status_code == 201:
        data = resp.json()
        entry_id = data.get("id")
        print(f"   ✓ Senha criada com ID: {entry_id}")
    else:
        print(f"   ✗ Erro: {resp.status_code} - {resp.text}")
except Exception as e:
    print(f"   ✗ Erro: {e}")

# Listar senhas
print("\n5. Testando listagem de senhas...")
try:
    resp = requests.get(f"{API_URL}/passwords", headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        print(f"   ✓ Total de senhas: {len(data)}")
        for pwd in data:
            print(f"      - {pwd['title']} ({pwd['entropy']} bits)")
    else:
        print(f"   ✗ Erro: {resp.status_code}")
except Exception as e:
    print(f"   ✗ Erro: {e}")

# Obter senha específica
print("\n6. Testando obtenção de senha...")
try:
    resp = requests.get(f"{API_URL}/passwords/{entry_id}", headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        print(f"   ✓ Senha obtida:")
        print(f"      Título: {data['title']}")
        print(f"      Site: {data['site']}")
        print(f"      Comprimento: {data['length']}")
        print(f"      Senha: {data['password']}")
    else:
        print(f"   ✗ Erro: {resp.status_code}")
except Exception as e:
    print(f"   ✗ Erro: {e}")

# Testar logout
print("\n7. Testando logout...")
try:
    resp = requests.post(f"{API_URL}/auth/logout", headers=headers)
    if resp.status_code == 200:
        print(f"   ✓ Logout bem-sucedido")
    else:
        print(f"   ✗ Erro: {resp.status_code}")
except Exception as e:
    print(f"   ✗ Erro: {e}")

# Testar acesso sem token
print("\n8. Testando proteção (acesso sem token)...")
try:
    resp = requests.get(f"{API_URL}/passwords")
    if resp.status_code == 401:
        print(f"   ✓ Acesso corretamente negado (401 Unauthorized)")
    else:
        print(f"   ✗ FALHA: Acesso permitido sem token!")
except Exception as e:
    print(f"   ✗ Erro: {e}")

print("\n=== Testes Concluídos ===")
