"""
Script de teste básico para o novo sistema de autenticação
"""
from auth import auth_manager

# Teste 1: Registrar um novo usuário
print("=== Teste 1: Registrando usuário ===")
try:
    token1 = auth_manager.register_user("testuser", "test@example.com", "password123")
    print(f"✓ Usuário registrado. Token: {token1[:20]}...")
except Exception as e:
    print(f"✗ Erro ao registrar: {e}")

# Teste 2: Login com credenciais corretas
print("\n=== Teste 2: Login com credenciais corretas ===")
try:
    token2 = auth_manager.login("testuser", "password123")
    print(f"✓ Login bem-sucedido. Token: {token2[:20]}...")
except Exception as e:
    print(f"✗ Erro no login: {e}")

# Teste 3: Login com senha incorreta
print("\n=== Teste 3: Login com senha incorreta ===")
try:
    token3 = auth_manager.login("testuser", "wrongpassword")
    print(f"✗ Login deveria ter falhado!")
except ValueError as e:
    print(f"✓ Erro esperado: {e}")

# Teste 4: Verificar token válido
print("\n=== Teste 4: Verificar token válido ===")
try:
    payload = auth_manager.verify_token(token2)
    print(f"✓ Token válido. User ID: {payload['user_id']}, Username: {payload['username']}")
except Exception as e:
    print(f"✗ Erro ao verificar token: {e}")

# Teste 5: Obter password manager
print("\n=== Teste 5: Obter password manager ===")
try:
    pm = auth_manager.get_password_manager(token2)
    user_id = auth_manager.get_user_id_from_token(token2)
    pm.user_id = user_id
    print(f"✓ Password manager obtido. User ID: {pm.user_id}")
except Exception as e:
    print(f"✗ Erro ao obter PM: {e}")

# Teste 6: Criar uma senha
print("\n=== Teste 6: Criar uma senha ===")
try:
    entry_id = pm.create_password("Gmail", "https://mail.google.com", 16)
    print(f"✓ Senha criada com ID: {entry_id}")
except Exception as e:
    print(f"✗ Erro ao criar senha: {e}")

# Teste 7: Listar senhas do usuário
print("\n=== Teste 7: Listar senhas do usuário ===")
try:
    passwords = pm.get_all_passwords()
    print(f"✓ Total de senhas: {len(passwords)}")
    for pwd in passwords:
        print(f"  - {pwd.title} ({pwd.site})")
except Exception as e:
    print(f"✗ Erro ao listar: {e}")

# Teste 8: Obter e descriptografar uma senha
print("\n=== Teste 8: Obter e descriptografar senha ===")
try:
    entry, decrypted = pm.get_password(entry_id)
    print(f"✓ Senha obtida: {entry.title}")
    print(f"  Título: {entry.title}")
    print(f"  Site: {entry.site}")
    print(f"  Senha: {decrypted}")
    print(f"  Comprimento: {entry.length}")
except Exception as e:
    print(f"✗ Erro ao obter senha: {e}")

print("\n=== Testes concluídos ===")
