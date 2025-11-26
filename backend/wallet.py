import json
import base64
from datetime import datetime
from typing import List
from encryption import EncryptionManager
from models import PasswordEntry
from database import DatabaseManager
import hashlib
import hmac


class WalletManager:
    """Gerenciador de wallet para exportação/importação de senhas"""
    APP_NAME = "password-managment"
    APP_VERSION = "1.0"
    WALLET_FORMAT_VERSION = "1.0"
    
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
            "version": WalletManager.WALLET_FORMAT_VERSION,
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

        # Create a separate encryption manager for the exported wallet
        wallet_encryption = EncryptionManager(wallet_password)

        # Metadata about the source encryption (how passwords are stored in the app)
        # Use the runtime EncryptionManager metadata so the export reflects actual config
        source_meta = encryption_manager.get_metadata()

        # Encrypt the exported JSON using the wallet password
        encrypted_data = wallet_encryption.encrypt(json_data)

        # Wallet-level metadata (how the wallet file itself is encrypted)
        wallet_meta = {
            "wallet_format_version": WalletManager.WALLET_FORMAT_VERSION,
            "app": {
                "name": WalletManager.APP_NAME,
                "version": WalletManager.APP_VERSION
            },
            "exported_at": datetime.now().isoformat(),
            "source_encryption": source_meta,
            "wallet_encryption": wallet_encryption.get_metadata()
        }

        wallet_file_data = {
            "meta": wallet_meta,
            "data": base64.b64encode(encrypted_data).decode()
        }

        # Create deterministic payload for signing (sort keys, no extra whitespace)
        payload = json.dumps(wallet_file_data, separators=(",", ":"), sort_keys=True).encode()

        # Derive signing key from wallet password and salt and compute HMAC-SHA256
        signing_key = wallet_encryption.derive_key()
        signature = hmac.new(signing_key, payload, hashlib.sha256).digest()
        wallet_file_data["hmac"] = base64.b64encode(signature).decode()

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

        # Support both legacy format (top-level 'salt' + 'data') and new format with 'meta'
        meta = wallet_file_data.get("meta", {})

        # Determine salt and encrypted payload
        salt_b64 = None
        if "data" not in wallet_file_data:
            raise ValueError("Wallet file missing 'data' field")

        encrypted_data_b64 = wallet_file_data.get("data")

        # Prefer explicit salt in meta -> wallet_encryption.salt
        salt_b64 = meta.get("wallet_encryption", {}).get("salt") or wallet_file_data.get("salt")

        if salt_b64:
            salt = base64.b64decode(salt_b64)
            wallet_encryption = EncryptionManager(wallet_password, salt)
        else:
            # No salt provided: try to initialize without explicit salt
            wallet_encryption = EncryptionManager(wallet_password)

        # Verify HMAC if present BEFORE attempting to decrypt
        hmac_b64 = wallet_file_data.get("hmac")
        if hmac_b64:
            provided = base64.b64decode(hmac_b64)
            # Recreate deterministic payload (same as export)
            verify_payload = json.dumps({k: wallet_file_data[k] for k in ("data","meta")}, separators=(",", ":"), sort_keys=True).encode()
            verify_key = wallet_encryption.derive_key()
            expected = hmac.new(verify_key, verify_payload, hashlib.sha256).digest()
            if not hmac.compare_digest(provided, expected):
                raise ValueError("HMAC mismatch: wallet file may have been tampered with or wrong password")

        encrypted_data = base64.b64decode(encrypted_data_b64)

        json_data = wallet_encryption.decrypt(encrypted_data)
        wallet_data = json.loads(json_data)

        # If meta exists, optionally validate wallet format
        if meta:
            wallet_format = meta.get("wallet_format_version")
            if wallet_format and wallet_format != WalletManager.WALLET_FORMAT_VERSION:
                print(f"Aviso: formato de wallet diferente ({wallet_format}), import may be partial")
        
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

