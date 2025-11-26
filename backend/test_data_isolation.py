"""
Teste de isolamento de dados entre usuários
"""
from auth import auth_manager
import os

# Limpar BD anterior
if os.path.exists("passwords_test.db"):
    os.remove("passwords_test.db")

# Recria auth_manager com novo banco
from database import DatabaseManager
auth_manager.db_manager = DatabaseManager("passwords_test.db")

print("=== Teste de Isolamento de Dados ===\n")

# Usuário 1
print("1. Registrando Usuário 1...")
token_user1 = auth_manager.register_user("alice", "alice@test.com", "senha123")
user_id_1 = auth_manager.get_user_id_from_token(token_user1)
pm1 = auth_manager.get_password_manager(token_user1)
pm1.user_id = user_id_1

# Usuário 2
print("2. Registrando Usuário 2...")
token_user2 = auth_manager.register_user("bob", "bob@test.com", "senha456")
user_id_2 = auth_manager.get_user_id_from_token(token_user2)
pm2 = auth_manager.get_password_manager(token_user2)
pm2.user_id = user_id_2

# Usuário 1 cria senhas
print("\n3. Usuário 1 criando senhas...")
id1_1 = pm1.create_password("Gmail", "https://gmail.com", 16)
id1_2 = pm1.create_password("GitHub", "https://github.com", 20)
print(f"   Criadas 2 senhas para usuário 1 (IDs: {id1_1}, {id1_2})")

# Usuário 2 cria senhas
print("\n4. Usuário 2 criando senhas...")
id2_1 = pm2.create_password("Facebook", "https://facebook.com", 18)
print(f"   Criada 1 senha para usuário 2 (ID: {id2_1})")

# Verificar isolamento
print("\n5. Verificando isolamento de dados...")
senhas_user1 = pm1.get_all_passwords()
senhas_user2 = pm2.get_all_passwords()

print(f"\n   Usuário 1 ({user_id_1}) vê {len(senhas_user1)} senhas:")
for s in senhas_user1:
    print(f"      - {s.title} (user_id={s.user_id})")

print(f"\n   Usuário 2 ({user_id_2}) vê {len(senhas_user2)} senhas:")
for s in senhas_user2:
    print(f"      - {s.title} (user_id={s.user_id})")

# Teste de acesso cruzado (tentativa de hack)
print("\n6. Testando proteção contra acesso cruzado...")
print("   Usuário 1 tentando acessar senha de Usuário 2...")
result = pm1.get_password(id2_1)  # id2_1 pertence ao user 2
if result is None:
    print("   ✓ Acesso negado corretamente!")
else:
    print("   ✗ FALHA DE SEGURANÇA: Acesso permitido!")

print("\n   Usuário 2 tentando acessar senha de Usuário 1...")
result = pm2.get_password(id1_1)  # id1_1 pertence ao user 1
if result is None:
    print("   ✓ Acesso negado corretamente!")
else:
    print("   ✗ FALHA DE SEGURANÇA: Acesso permitido!")

# Teste de deleção
print("\n7. Testando deleção com isolamento...")
pm1.delete_password(id1_1)
print("   Usuário 1 deletou sua senha de Gmail")
senhas_user1_after = pm1.get_all_passwords()
senhas_user2_after = pm2.get_all_passwords()

print(f"   Usuário 1 agora tem {len(senhas_user1_after)} senhas (era {len(senhas_user1)})")
print(f"   Usuário 2 ainda tem {len(senhas_user2_after)} senhas (não foi afetado)")

if len(senhas_user1_after) == len(senhas_user1) - 1 and len(senhas_user2_after) == len(senhas_user2):
    print("   ✓ Deleção com isolamento funciona corretamente!")
else:
    print("   ✗ Erro no isolamento de deleção!")

print("\n=== Teste Concluído ===")

# Limpar
os.remove("passwords_test.db")
