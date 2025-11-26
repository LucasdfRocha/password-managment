import os
import tempfile
import json
from datetime import datetime

from encryption import EncryptionManager
from wallet import WalletManager
from models import PasswordEntry


def run_hmac_tamper_test():
    master_password = "master-secret"
    encryption_manager = EncryptionManager(master_password)

    now = datetime.now()
    # Create one sample entry
    plaintext = "Secret123!"
    encrypted = encryption_manager.encrypt(plaintext)
    entry = PasswordEntry(
        id=None,
        title="Test",
        site="example.com",
        password=encrypted,
        length=len(plaintext),
        use_uppercase=True,
        use_lowercase=True,
        use_digits=True,
        use_special=True,
        entropy=40.0,
        expiration_date=None,
        created_at=now,
        updated_at=now,
    )

    fd, wallet_path = tempfile.mkstemp(prefix="wallet_hmac_test_", suffix=".json")
    os.close(fd)

    try:
        # Export wallet with HMAC
        WalletManager.export_wallet([entry], encryption_manager, wallet_password="wallet-pass", output_file=wallet_path)

        # Load and tamper the data field (change one character in base64 string)
        with open(wallet_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        orig_b64 = data.get('data')
        if not orig_b64 or len(orig_b64) < 5:
            raise RuntimeError('unexpected wallet data for tamper test')

        # Flip a character in the middle of the base64 string (safe modification)
        i = len(orig_b64) // 2
        c = orig_b64[i]
        # choose a different base64-char (A-Z,a-z,0-9,+,/ or -_ from urlsafe)
        replacement = 'A' if c != 'A' else 'B'
        tampered_b64 = orig_b64[:i] + replacement + orig_b64[i+1:]

        data['data'] = tampered_b64

        # Write tampered wallet back
        with open(wallet_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        # Attempt import - should raise ValueError due to HMAC mismatch
        try:
            WalletManager.import_wallet(wallet_path, wallet_password="wallet-pass", encryption_manager=encryption_manager, db_manager=type('D', (), {'create_entry': lambda *a, **k: None})())
        except ValueError as e:
            print('HMAC verification failed as expected:', str(e))
            return True
        except Exception as e:
            print('Unexpected exception type:', type(e), e)
            return False
        else:
            print('Import succeeded unexpectedly; HMAC verification failed to detect tampering')
            return False
    finally:
        try:
            os.remove(wallet_path)
        except Exception:
            pass


if __name__ == '__main__':
    ok = run_hmac_tamper_test()
    if not ok:
        raise SystemExit(1)
    else:
        print('Tamper test passed')
