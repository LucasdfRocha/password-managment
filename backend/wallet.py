import json
import base64
from datetime import datetime
from typing import List
from encryption import EncryptionManager
from models import PasswordEntry
from database import DatabaseManager


class WalletManager:
    """Gerenciador de wallet para exportação/importação de senhas"""
    
    @staticmethod
    def export_wallet(
        entries: List[PasswordEntry],
        encryption_manager: EncryptionManager,
        wallet_password: str,
        output_file: str = "wallet.enc"
    ):
        """
        Exporta todas as senhas para um arquivo wallet criptografado
        
        Args:
            entries: Lista de entradas de senha
            encryption_manager: Gerenciador de criptografia principal
            wallet_password: Senha para criptografar o wallet
            output_file: Nome do arquivo de saída
        """

        wallet_data = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "entries": []
        }
        
        for entry in entries:
            decrypted_password = encryption_manager.decrypt(entry.password)
            
            entry_data = {
                "title": entry.title,
                "site": entry.site,
                "password": decrypted_password,  # Senha descriptografada
                "length": entry.length,
                "use_uppercase": entry.use_uppercase,
                "use_lowercase": entry.use_lowercase,
                "use_digits": entry.use_digits,
                "use_special": entry.use_special,
                "entropy": entry.entropy,
                "expiration_date": entry.expiration_date.isoformat() if entry.expiration_date else None,
                "created_at": entry.created_at.isoformat(),
                "updated_at": entry.updated_at.isoformat()
            }
            wallet_data["entries"].append(entry_data)

        json_data = json.dumps(wallet_data, indent=2)

        wallet_encryption = EncryptionManager(wallet_password)

        encrypted_data = wallet_encryption.encrypt(json_data)

        wallet_file_data = {
            "salt": base64.b64encode(wallet_encryption.get_salt()).decode(),
            "data": base64.b64encode(encrypted_data).decode()
        }
        
        with open(output_file, 'w') as f:
            json.dump(wallet_file_data, f, indent=2)
        
        print(f"Wallet exportado com sucesso para {output_file}")
    
    @staticmethod
    def import_wallet(
        wallet_file: str,
        wallet_password: str,
        encryption_manager: EncryptionManager,
        db_manager: DatabaseManager
    ) -> int:
        """
        Importa senhas de um arquivo wallet
        
        Args:
            wallet_file: Caminho do arquivo wallet
            wallet_password: Senha do wallet
            encryption_manager: Gerenciador de criptografia principal
            db_manager: Gerenciador do banco de dados
            
        Returns:
            Número de entradas importadas
        """
        with open(wallet_file, 'r') as f:
            wallet_file_data = json.load(f)
        
        salt = base64.b64decode(wallet_file_data["salt"])
        encrypted_data = base64.b64decode(wallet_file_data["data"])
        
        wallet_encryption = EncryptionManager(wallet_password, salt)
        
        json_data = wallet_encryption.decrypt(encrypted_data)
        wallet_data = json.loads(json_data)
        
        imported_count = 0
        for entry_data in wallet_data["entries"]:
            encrypted_password = encryption_manager.encrypt(entry_data["password"])
            
            entry = PasswordEntry(
                id=None,
                title=entry_data["title"],
                site=entry_data["site"],
                password="",  # Será substituído pelo encrypted_password
                length=entry_data["length"],
                use_uppercase=entry_data["use_uppercase"],
                use_lowercase=entry_data["use_lowercase"],
                use_digits=entry_data["use_digits"],
                use_special=entry_data["use_special"],
                entropy=entry_data["entropy"],
                expiration_date=datetime.fromisoformat(entry_data["expiration_date"]) if entry_data["expiration_date"] else None,
                created_at=datetime.fromisoformat(entry_data["created_at"]),
                updated_at=datetime.fromisoformat(entry_data["updated_at"])
            )
            
            db_manager.create_entry(entry, encrypted_password)
            imported_count += 1
        
        print(f"{imported_count} entradas importadas com sucesso")
        return imported_count

