"""
so serve pra testar 
"""
import sys
from datetime import datetime
from getpass import getpass
from password_manager import PasswordManager
from password_generator import PasswordGenerator
from wallet import WalletManager


def print_menu():
    """Imprime o menu principal"""
    print("\n" + "="*50)
    print("GERENCIADOR DE SENHAS")
    print("="*50)
    print("1. Criar nova senha")
    print("2. Listar todas as senhas")
    print("3. Ver senha (descriptografada)")
    print("4. Atualizar senha")
    print("5. Deletar senha")
    print("6. Exportar wallet (cold/hot)")
    print("7. Importar wallet")
    print("8. Gerar senha de teste (sem salvar)")
    print("0. Sair")
    print("="*50)


def get_master_password() -> str:
    """Solicita a senha mestra do usuário"""
    return getpass("Digite sua senha mestra: ")


def create_password_interactive(pm: PasswordManager):
    """Interface interativa para criar uma senha"""
    print("\n--- Criar Nova Senha ---")
    title = input("Título: ").strip()
    site = input("Site: ").strip()
    
    print("\nOpções de geração:")
    use_custom = input("Deseja usar uma senha customizada? (s/n): ").strip().lower()
    
    if use_custom == 's':
        custom_password = getpass("Digite a senha: ")
        length = len(custom_password)
        use_uppercase = any(c.isupper() for c in custom_password)
        use_lowercase = any(c.islower() for c in custom_password)
        use_digits = any(c.isdigit() for c in custom_password)
        use_special = any(not c.isalnum() for c in custom_password)
    else:
        length = int(input("Tamanho da senha (padrão: 16): ") or "16")
        use_uppercase = input("Usar letras maiúsculas? (s/n, padrão: s): ").strip().lower() != 'n'
        use_lowercase = input("Usar letras minúsculas? (s/n, padrão: s): ").strip().lower() != 'n'
        use_digits = input("Usar dígitos? (s/n, padrão: s): ").strip().lower() != 'n'
        use_special = input("Usar caracteres especiais? (s/n, padrão: s): ").strip().lower() != 'n'
        custom_password = None
    
    expiration = input("Data de expiração (YYYY-MM-DD, ou Enter para nenhuma): ").strip()
    expiration_date = None
    if expiration:
        try:
            expiration_date = datetime.strptime(expiration, "%Y-%m-%d")
        except ValueError:
            print("Data inválida, ignorando...")
    
    try:
        if use_custom == 's':
            entry_id = pm.create_password(
                title, site, length=length,
                use_uppercase=use_uppercase, use_lowercase=use_lowercase,
                use_digits=use_digits, use_special=use_special,
                expiration_date=expiration_date, custom_password=custom_password
            )
        else:
            entry_id = pm.create_password(
                title, site, length=length,
                use_uppercase=use_uppercase, use_lowercase=use_lowercase,
                use_digits=use_digits, use_special=use_special,
                expiration_date=expiration_date
            )
        print(f"\n✓ Senha criada com sucesso! ID: {entry_id}")
    except Exception as e:
        print(f"\n✗ Erro ao criar senha: {e}")


def list_passwords(pm: PasswordManager):
    """Lista todas as senhas"""
    print("\n--- Todas as Senhas ---")
    entries = pm.get_all_passwords()
    
    if not entries:
        print("Nenhuma senha cadastrada.")
        return
    
    print(f"\n{'ID':<5} {'Título':<20} {'Site':<25} {'Tamanho':<8} {'Entropia':<10} {'Nível':<15} {'Expiração':<12}")
    print("-" * 100)
    
    for entry in entries:
        entropy_level = PasswordGenerator.get_entropy_level(entry.entropy)
        expiration = entry.expiration_date.strftime("%Y-%m-%d") if entry.expiration_date else "N/A"
        print(f"{entry.id:<5} {entry.title:<20} {entry.site:<25} {entry.length:<8} "
              f"{entry.entropy:<10.2f} {entropy_level:<15} {expiration:<12}")


def view_password(pm: PasswordManager):
    """Visualiza uma senha descriptografada"""
    print("\n--- Ver Senha ---")
    try:
        entry_id = int(input("ID da senha: "))
        result = pm.get_password(entry_id)
        
        if not result:
            print("Senha não encontrada.")
            return
        
        entry, password = result
        entropy_level = PasswordGenerator.get_entropy_level(entry.entropy)
        
        print(f"\nTítulo: {entry.title}")
        print(f"Site: {entry.site}")
        print(f"Senha: {password}")
        print(f"Tamanho: {entry.length}")
        print(f"Entropia: {entry.entropy} bits ({entropy_level})")
        print(f"Caracteres: Maiúsculas={entry.use_uppercase}, Minúsculas={entry.use_lowercase}, "
              f"Dígitos={entry.use_digits}, Especiais={entry.use_special}")
        print(f"Criado em: {entry.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Atualizado em: {entry.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if entry.expiration_date:
            print(f"Expira em: {entry.expiration_date.strftime('%Y-%m-%d')}")
    except ValueError:
        print("ID inválido.")
    except Exception as e:
        print(f"Erro: {e}")


def update_password_interactive(pm: PasswordManager):
    """Interface interativa para atualizar uma senha"""
    print("\n--- Atualizar Senha ---")
    try:
        entry_id = int(input("ID da senha: "))
        result = pm.get_password(entry_id)
        if not result:
            print("Senha não encontrada.")
            return
        entry, _ = result
        
        print(f"\nAtualizando: {entry.title} ({entry.site})")
        print("Deixe em branco para manter o valor atual.\n")
        
        title = input(f"Título [{entry.title}]: ").strip() or None
        site = input(f"Site [{entry.site}]: ").strip() or None
        
        regenerate = input("Regenerar senha? (s/n): ").strip().lower() == 's'
        custom_password = None
        length = None
        use_uppercase = None
        use_lowercase = None
        use_digits = None
        use_special = None
        
        if regenerate:
            use_custom = input("Usar senha customizada? (s/n): ").strip().lower()
            if use_custom == 's':
                custom_password = getpass("Digite a nova senha: ")
            else:
                length_input = input(f"Tamanho [{entry.length}]: ").strip()
                length = int(length_input) if length_input else entry.length
                use_uppercase_input = input(f"Usar maiúsculas? (s/n) [{entry.use_uppercase}]: ").strip()
                use_uppercase = use_uppercase_input.lower() != 'n' if use_uppercase_input else entry.use_uppercase
                use_lowercase_input = input(f"Usar minúsculas? (s/n) [{entry.use_lowercase}]: ").strip()
                use_lowercase = use_lowercase_input.lower() != 'n' if use_lowercase_input else entry.use_lowercase
                use_digits_input = input(f"Usar dígitos? (s/n) [{entry.use_digits}]: ").strip()
                use_digits = use_digits_input.lower() != 'n' if use_digits_input else entry.use_digits
                use_special_input = input(f"Usar especiais? (s/n) [{entry.use_special}]: ").strip()
                use_special = use_special_input.lower() != 'n' if use_special_input else entry.use_special
        
        expiration = input(f"Data de expiração (YYYY-MM-DD) [{entry.expiration_date.strftime('%Y-%m-%d') if entry.expiration_date else 'N/A'}]: ").strip()
        expiration_date = None
        if expiration:
            try:
                expiration_date = datetime.strptime(expiration, "%Y-%m-%d")
            except ValueError:
                print("Data inválida, ignorando...")
        
        success = pm.update_password(
            entry_id, title=title, site=site, length=length,
            use_uppercase=use_uppercase, use_lowercase=use_lowercase,
            use_digits=use_digits, use_special=use_special,
            expiration_date=expiration_date, regenerate=regenerate,
            custom_password=custom_password
        )
        
        if success:
            print("\n✓ Senha atualizada com sucesso!")
        else:
            print("\n✗ Erro ao atualizar senha.")
    except ValueError:
        print("ID inválido.")
    except Exception as e:
        print(f"Erro: {e}")


def delete_password_interactive(pm: PasswordManager):
    """Interface interativa para deletar uma senha"""
    print("\n--- Deletar Senha ---")
    try:
        entry_id = int(input("ID da senha: "))
        result = pm.get_password(entry_id)
        if not result:
            print("Senha não encontrada.")
            return
        entry, _ = result
        
        confirm = input(f"Tem certeza que deseja deletar '{entry.title}' ({entry.site})? (s/n): ").strip().lower()
        if confirm == 's':
            success = pm.delete_password(entry_id)
            if success:
                print("\n✓ Senha deletada com sucesso!")
            else:
                print("\n✗ Erro ao deletar senha.")
        else:
            print("Operação cancelada.")
    except ValueError:
        print("ID inválido.")
    except Exception as e:
        print(f"Erro: {e}")


def export_wallet_interactive(pm: PasswordManager):
    """Interface interativa para exportar wallet"""
    print("\n--- Exportar Wallet ---")
    entries = pm.get_all_passwords()
    
    if not entries:
        print("Nenhuma senha para exportar.")
        return
    
    wallet_password = getpass("Digite a senha para o wallet: ")
    confirm_password = getpass("Confirme a senha: ")
    
    if wallet_password != confirm_password:
        print("Senhas não coincidem!")
        return
    
    output_file = input("Nome do arquivo (padrão: wallet.enc): ").strip() or "wallet.enc"
    
    try:
        WalletManager.export_wallet(entries, pm.encryption_manager, wallet_password, output_file)
    except Exception as e:
        print(f"Erro ao exportar wallet: {e}")


def import_wallet_interactive(pm: PasswordManager):
    """Interface interativa para importar wallet"""
    print("\n--- Importar Wallet ---")
    wallet_file = input("Caminho do arquivo wallet: ").strip()
    wallet_password = getpass("Digite a senha do wallet: ")
    
    try:
        WalletManager.import_wallet(wallet_file, wallet_password, pm.encryption_manager, pm.db_manager)
    except Exception as e:
        print(f"Erro ao importar wallet: {e}")


def generate_test_password():
    """Gera uma senha de teste sem salvar"""
    print("\n--- Gerar Senha de Teste ---")
    try:
        length = int(input("Tamanho da senha (padrão: 16): ") or "16")
        use_uppercase = input("Usar letras maiúsculas? (s/n, padrão: s): ").strip().lower() != 'n'
        use_lowercase = input("Usar letras minúsculas? (s/n, padrão: s): ").strip().lower() != 'n'
        use_digits = input("Usar dígitos? (s/n, padrão: s): ").strip().lower() != 'n'
        use_special = input("Usar caracteres especiais? (s/n, padrão: s): ").strip().lower() != 'n'
        
        password = PasswordGenerator.generate(length, use_uppercase, use_lowercase, use_digits, use_special)
        entropy = PasswordGenerator.calculate_entropy(length, use_uppercase, use_lowercase, use_digits, use_special)
        entropy_level = PasswordGenerator.get_entropy_level(entropy)
        
        print(f"\nSenha gerada: {password}")
        print(f"Tamanho: {length}")
        print(f"Entropia: {entropy} bits ({entropy_level})")
    except Exception as e:
        print(f"Erro: {e}")


def main():
    """Função principal"""
    print("Bem-vindo ao Gerenciador de Senhas!")
    master_password = get_master_password()
    
    try:
        pm = PasswordManager(master_password)
    except Exception as e:
        print(f"Erro ao inicializar: {e}")
        sys.exit(1)
    
    while True:
        print_menu()
        choice = input("\nEscolha uma opção: ").strip()
        
        if choice == '0':
            print("Até logo!")
            break
        elif choice == '1':
            create_password_interactive(pm)
        elif choice == '2':
            list_passwords(pm)
        elif choice == '3':
            view_password(pm)
        elif choice == '4':
            update_password_interactive(pm)
        elif choice == '5':
            delete_password_interactive(pm)
        elif choice == '6':
            export_wallet_interactive(pm)
        elif choice == '7':
            import_wallet_interactive(pm)
        elif choice == '8':
            generate_test_password()
        else:
            print("Opção inválida!")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    main()

