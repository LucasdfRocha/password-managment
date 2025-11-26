import os
import tempfile
import json
from datetime import datetime

from encryption import EncryptionManager
from wallet import WalletManager
from models import PasswordEntry


class FakeDB:
    def __init__(self):
        self.created = []

    def create_entry(self, entry: PasswordEntry, encrypted_password: bytes):
        # store minimal info for validation
        self.created.append({
            "title": entry.title,
            "site": entry.site,
            "password_encrypted": encrypted_password,
        })
        return len(self.created)


def run_test():
    master_password = "master-secret"
    encryption_manager = EncryptionManager(master_password)

    # Create two sample entries
    now = datetime.now()
    entries = []
    for i in range(2):
        plaintext = f"P@ssw0rd{i}"
        encrypted = encryption_manager.encrypt(plaintext)
        entry = PasswordEntry(
            id=None,
            title=f"Title{i}",
            site=f"site{i}.example",
            password=encrypted,
            length=len(plaintext),
            use_uppercase=True,
            use_lowercase=True,
            use_digits=True,
            use_special=False,
            entropy=30.0 + i,
            expiration_date=None,
            created_at=now,
            updated_at=now,
        )
        entries.append(entry)

    fd, wallet_path = tempfile.mkstemp(prefix="wallet_test_", suffix=".json")
    os.close(fd)

    try:
        WalletManager.export_wallet(entries, encryption_manager, wallet_password="wallet-pass", output_file=wallet_path)

        fake_db = FakeDB()
        imported = WalletManager.import_wallet(wallet_path, wallet_password="wallet-pass", encryption_manager=encryption_manager, db_manager=fake_db)

        print(f"Imported count returned: {imported}")
        print(f"Fake DB created entries: {len(fake_db.created)}")
        assert imported == len(entries)
        assert len(fake_db.created) == len(entries)
        print("Functional export/import test succeeded")
    finally:
        try:
            os.remove(wallet_path)
        except Exception:
            pass


if __name__ == "__main__":
    run_test()
