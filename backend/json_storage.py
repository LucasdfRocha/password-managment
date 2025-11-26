import json
import os
import base64
from datetime import datetime
from typing import List, Optional
from models import PasswordEntry
from encryption import EncryptionManager


class JsonStorageManager:
    def __init__(
        self,
        encryption_manager: EncryptionManager,
        storage_file: str = "passwords.enc.json",
    ):
        self.encryption_manager = encryption_manager
        self.storage_file = storage_file

    def _load_data(self) -> dict:
        if not os.path.exists(self.storage_file):
            return {
                "version": "1.0",
                "entries": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

        try:
            with open(self.storage_file, "rb") as f:
                encrypted_data = f.read()

            MIN_SIZE = 44
            if len(encrypted_data) < MIN_SIZE:
                return {
                    "version": "1.0",
                    "entries": [],
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }

            json_data = self.encryption_manager.decrypt(encrypted_data)
            return json.loads(json_data)
        except Exception as e:
            error_msg = str(e).lower()
            if (
                "nonce cannot be empty" in error_msg
                or "invalid" in error_msg
                or "corrupted" in error_msg
            ):
                return {
                    "version": "1.0",
                    "entries": [],
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }
            raise ValueError(
                f"Erro ao carregar dados: {str(e)}. Verifique se a senha mestra está correta."
            )

    def _save_data(self, data: dict):
        """
        Criptografa e salva os dados no arquivo JSON.
        Este método é chamado a cada operação (criar, atualizar, deletar)
        para garantir que o arquivo seja sempre atualizado.

        Args:
            data: Dicionário com os dados a serem salvos
        """
        data["updated_at"] = datetime.now().isoformat()
        json_data = json.dumps(data, indent=2, default=str)

        encrypted_data = self.encryption_manager.encrypt(json_data)

        with open(self.storage_file, "wb") as f:
            f.write(encrypted_data)
            f.flush()
            os.fsync(f.fileno())

    def create_entry(self, entry: PasswordEntry, encrypted_password: bytes) -> int:
        """
        Cria uma nova entrada de senha e salva no arquivo JSON criptografado.
        O arquivo é atualizado imediatamente após a criação.

        Args:
            entry: Objeto PasswordEntry
            encrypted_password: Senha criptografada em bytes

        Returns:
            ID da entrada criada
        """
        data = self._load_data()

        if data["entries"]:
            next_id = max(e.get("id", 0) for e in data["entries"]) + 1
        else:
            next_id = 1

        encrypted_password_b64 = base64.b64encode(encrypted_password).decode("utf-8")

        entry_dict = {
            "id": next_id,
            "title": entry.title,
            "site": entry.site,
            "password_encrypted": encrypted_password_b64,
            "length": entry.length,
            "use_uppercase": entry.use_uppercase,
            "use_lowercase": entry.use_lowercase,
            "use_digits": entry.use_digits,
            "use_special": entry.use_special,
            "entropy": entry.entropy,
            "expiration_date": (
                entry.expiration_date.isoformat() if entry.expiration_date else None
            ),
            "created_at": entry.created_at.isoformat(),
            "updated_at": entry.updated_at.isoformat(),
        }

        data["entries"].append(entry_dict)

        self._save_data(data)
        return next_id

    def get_all_entries(self) -> List[PasswordEntry]:
        data = self._load_data()
        entries = []

        for entry_dict in data.get("entries", []):
            encrypted_password = base64.b64decode(entry_dict["password_encrypted"])

            entry = PasswordEntry(
                id=entry_dict["id"],
                title=entry_dict["title"],
                site=entry_dict["site"],
                password=encrypted_password,
                length=entry_dict["length"],
                use_uppercase=entry_dict["use_uppercase"],
                use_lowercase=entry_dict["use_lowercase"],
                use_digits=entry_dict["use_digits"],
                use_special=entry_dict["use_special"],
                entropy=entry_dict["entropy"],
                expiration_date=(
                    datetime.fromisoformat(entry_dict["expiration_date"])
                    if entry_dict.get("expiration_date")
                    else None
                ),
                created_at=datetime.fromisoformat(entry_dict["created_at"]),
                updated_at=datetime.fromisoformat(entry_dict["updated_at"]),
            )
            entries.append(entry)

        return entries

    def get_entry_by_id(self, entry_id: int) -> Optional[PasswordEntry]:
        data = self._load_data()

        for entry_dict in data.get("entries", []):
            if entry_dict.get("id") == entry_id:
                encrypted_password = base64.b64decode(entry_dict["password_encrypted"])

                return PasswordEntry(
                    id=entry_dict["id"],
                    title=entry_dict["title"],
                    site=entry_dict["site"],
                    password=encrypted_password,
                    length=entry_dict["length"],
                    use_uppercase=entry_dict["use_uppercase"],
                    use_lowercase=entry_dict["use_lowercase"],
                    use_digits=entry_dict["use_digits"],
                    use_special=entry_dict["use_special"],
                    entropy=entry_dict["entropy"],
                    expiration_date=(
                        datetime.fromisoformat(entry_dict["expiration_date"])
                        if entry_dict.get("expiration_date")
                        else None
                    ),
                    created_at=datetime.fromisoformat(entry_dict["created_at"]),
                    updated_at=datetime.fromisoformat(entry_dict["updated_at"]),
                )

        return None

    def update_entry(
        self, entry_id: int, entry: PasswordEntry, encrypted_password: bytes
    ):
        """
        Atualiza uma entrada de senha e salva no arquivo JSON criptografado.
        O arquivo é atualizado imediatamente após a atualização.

        Args:
            entry_id: ID da entrada
            entry: Objeto PasswordEntry atualizado
            encrypted_password: Senha criptografada em bytes
        """
        data = self._load_data()

        for i, entry_dict in enumerate(data.get("entries", [])):
            if entry_dict.get("id") == entry_id:
                encrypted_password_b64 = base64.b64encode(encrypted_password).decode(
                    "utf-8"
                )

                data["entries"][i] = {
                    "id": entry_id,
                    "title": entry.title,
                    "site": entry.site,
                    "password_encrypted": encrypted_password_b64,
                    "length": entry.length,
                    "use_uppercase": entry.use_uppercase,
                    "use_lowercase": entry.use_lowercase,
                    "use_digits": entry.use_digits,
                    "use_special": entry.use_special,
                    "entropy": entry.entropy,
                    "expiration_date": (
                        entry.expiration_date.isoformat()
                        if entry.expiration_date
                        else None
                    ),
                    "created_at": entry_dict["created_at"],
                    "updated_at": entry.updated_at.isoformat(),
                }
                break

        self._save_data(data)

    def delete_entry(self, entry_id: int):
        """
        Deleta uma entrada de senha e salva no arquivo JSON criptografado.
        O arquivo é atualizado imediatamente após a deleção.

        Args:
            entry_id: ID da entrada
        """
        data = self._load_data()
        data["entries"] = [
            e for e in data.get("entries", []) if e.get("id") != entry_id
        ]

        self._save_data(data)
