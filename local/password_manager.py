from datetime import datetime
from typing import List, Optional, Tuple
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from password_generator import PasswordGenerator
from encryption import EncryptionManager
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
import json
import base64


class PasswordEntry:
    """Modelo simplificado para entrada de senha (sem user_id)"""
    def __init__(self, id: int, title: str, site: str, password: str, length: int,
                 use_uppercase: bool, use_lowercase: bool, use_digits: bool,
                 use_special: bool, entropy: float, expiration_date: Optional[datetime],
                 created_at: datetime, updated_at: datetime):
        self.id = id
        self.title = title
        self.site = site
        self.password = password
        self.length = length
        self.use_uppercase = use_uppercase
        self.use_lowercase = use_lowercase
        self.use_digits = use_digits
        self.use_special = use_special
        self.entropy = entropy
        self.expiration_date = expiration_date
        self.created_at = created_at
        self.updated_at = updated_at


class JSONPasswordManager:
    def __init__(self, master_password: str, json_file: str = "passwords.json"):
        self.json_file = json_file
        self.master_password = master_password
        self.encryption_manager = None
        self.entries: List[PasswordEntry] = []
        self.next_id = 1
        
        self._load_or_create()
    
    def _load_or_create(self):
        """Carrega o arquivo JSON existente ou cria um novo"""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extrai informações de criptografia do meta
            meta = data.get('meta', {})
            encryption_info = meta.get('encryption', {})
            
            # Cria o EncryptionManager com o salt do arquivo
            salt_b64 = encryption_info.get('salt')
            if salt_b64:
                self.encryption_manager = EncryptionManager(self.master_password, salt=salt_b64)
            else:
                self.encryption_manager = EncryptionManager(self.master_password)
            
            # Descriptografa e carrega as entradas
            entries_encrypted = data.get('data', {}).get('entries_encrypted', '')
            if entries_encrypted:
                entries_blob = base64.b64decode(entries_encrypted)
                entries_json = self.encryption_manager.decrypt(entries_blob)
                entries_data = json.loads(entries_json)
                
                self.entries = []
                for entry_data in entries_data.get('entries', []):
                    entry = PasswordEntry(
                        id=entry_data['id'],
                        title=entry_data['title'],
                        site=entry_data['site'],
                        password=entry_data['password'],
                        length=entry_data['length'],
                        use_uppercase=entry_data['use_uppercase'],
                        use_lowercase=entry_data['use_lowercase'],
                        use_digits=entry_data['use_digits'],
                        use_special=entry_data['use_special'],
                        entropy=entry_data['entropy'],
                        expiration_date=datetime.fromisoformat(entry_data['expiration_date']) if entry_data.get('expiration_date') else None,
                        created_at=datetime.fromisoformat(entry_data['created_at']),
                        updated_at=datetime.fromisoformat(entry_data['updated_at'])
                    )
                    self.entries.append(entry)
                    if entry.id >= self.next_id:
                        self.next_id = entry.id + 1
        except FileNotFoundError:
            # Arquivo não existe, cria novo
            self.encryption_manager = EncryptionManager(self.master_password)
            self.entries = []
            self._save()
        except Exception as e:
            raise Exception(f"Erro ao carregar arquivo: {e}")
    
    def _save(self):
        """Salva as entradas no arquivo JSON no formato especificado"""
        # Prepara os dados das entradas
        entries_data = {
            'entries': []
        }
        
        for entry in self.entries:
            entry_dict = {
                'id': entry.id,
                'title': entry.title,
                'site': entry.site,
                'password': entry.password,
                'length': entry.length,
                'use_uppercase': entry.use_uppercase,
                'use_lowercase': entry.use_lowercase,
                'use_digits': entry.use_digits,
                'use_special': entry.use_special,
                'entropy': entry.entropy,
                'expiration_date': entry.expiration_date.isoformat() if entry.expiration_date else None,
                'created_at': entry.created_at.isoformat(),
                'updated_at': entry.updated_at.isoformat()
            }
            entries_data['entries'].append(entry_dict)
        
        # Serializa e criptografa as entradas
        entries_json = json.dumps(entries_data, ensure_ascii=False, indent=2)
        entries_blob = self.encryption_manager.encrypt(entries_json)
        entries_encrypted = base64.b64encode(entries_blob).decode('utf-8')
        
        # Extrai informações de criptografia
        metadata = self.encryption_manager.get_metadata()
        
        # Extrai salt e nonce do blob criptografado
        # O formato do EncryptionManager é: salt (16) + nonce (12) + tag (16) + ciphertext
        salt_b64 = metadata['salt']
        # Extrai o nonce do blob (antes de codificar em base64)
        nonce_start = 16  # após o salt
        nonce_end = nonce_start + 12
        nonce_bytes = entries_blob[nonce_start:nonce_end]
        nonce_b64 = base64.b64encode(nonce_bytes).decode('utf-8')
        
        # Normaliza o kdf_hash para o formato esperado
        kdf_hash = metadata.get("kdf_hash", "SHA256")
        if kdf_hash == "SHA256":
            kdf_hash = "SHA-256"
        
        # Cria a estrutura JSON no formato especificado
        wallet_data = {
            "meta": {
                "wallet_format_version": "1.0",
                "app": {
                    "name": "password-managment",
                    "version": "1.0"
                },
                "exported_at": datetime.now().isoformat() + "Z",
                "encryption": {
                    "algorithm": "AES-GCM",
                    "kdf": metadata.get("kdf", "PBKDF2"),
                    "kdf_hash": kdf_hash,
                    "kdf_iterations": metadata.get("kdf_iterations", 300000),
                    "salt": salt_b64,
                    "nonce": nonce_b64,
                    "tag_bytes": 16
                },
                "serialization": {
                    "format": "json",
                    "encoding": "utf-8",
                    "indent": 2
                }
            },
            "data": {
                "entries_encrypted": entries_encrypted
            }
        }
        
        # Salva no arquivo
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(wallet_data, f, ensure_ascii=False, indent=2)
    
    def create_password(
        self,
        title: str,
        site: str,
        length: int = 16,
        use_uppercase: bool = True,
        use_lowercase: bool = True,
        use_digits: bool = True,
        use_special: bool = True,
        expiration_date: Optional[datetime] = None,
        custom_password: Optional[str] = None
    ) -> int:
        """Cria uma nova senha"""
        if custom_password:
            password = custom_password
        else:
            password = PasswordGenerator.generate(
                length, use_uppercase, use_lowercase, use_digits, use_special
            )
        
        entropy = PasswordGenerator.calculate_entropy(
            length, use_uppercase, use_lowercase, use_digits, use_special
        )
        
        now = datetime.now()
        entry = PasswordEntry(
            id=self.next_id,
            title=title,
            site=site,
            password=password,
            length=length,
            use_uppercase=use_uppercase,
            use_lowercase=use_lowercase,
            use_digits=use_digits,
            use_special=use_special,
            entropy=entropy,
            expiration_date=expiration_date,
            created_at=now,
            updated_at=now
        )
        
        self.entries.append(entry)
        self.next_id += 1
        self._save()
        
        return entry.id
    
    def get_all_passwords(self) -> List[PasswordEntry]:
        """Retorna todas as senhas"""
        return self.entries
    
    def get_password(self, entry_id: int) -> Optional[Tuple[PasswordEntry, str]]:
        """Retorna a entrada e a senha descriptografada"""
        for entry in self.entries:
            if entry.id == entry_id:
                return (entry, entry.password)
        return None
    
    def update_password(
        self,
        entry_id: int,
        title: Optional[str] = None,
        site: Optional[str] = None,
        length: Optional[int] = None,
        use_uppercase: Optional[bool] = None,
        use_lowercase: Optional[bool] = None,
        use_digits: Optional[bool] = None,
        use_special: Optional[bool] = None,
        expiration_date: Optional[datetime] = None,
        regenerate: bool = False,
        custom_password: Optional[str] = None
    ) -> bool:
        """Atualiza uma senha"""
        entry = None
        for e in self.entries:
            if e.id == entry_id:
                entry = e
                break
        
        if not entry:
            return False
        
        if title is not None:
            entry.title = title
        if site is not None:
            entry.site = site
        if length is not None:
            entry.length = length
        if use_uppercase is not None:
            entry.use_uppercase = use_uppercase
        if use_lowercase is not None:
            entry.use_lowercase = use_lowercase
        if use_digits is not None:
            entry.use_digits = use_digits
        if use_special is not None:
            entry.use_special = use_special
        if expiration_date is not None:
            entry.expiration_date = expiration_date
        
        if regenerate:
            if custom_password:
                entry.password = custom_password
            else:
                entry.password = PasswordGenerator.generate(
                    entry.length, entry.use_uppercase, entry.use_lowercase,
                    entry.use_digits, entry.use_special
                )
        
        entry.entropy = PasswordGenerator.calculate_entropy(
            entry.length, entry.use_uppercase, entry.use_lowercase,
            entry.use_digits, entry.use_special
        )
        entry.updated_at = datetime.now()
        
        self._save()
        return True
    
    def delete_password(self, entry_id: int) -> bool:
        """Deleta uma senha"""
        for i, entry in enumerate(self.entries):
            if entry.id == entry_id:
                self.entries.pop(i)
                self._save()
                return True
        return False
    
    @staticmethod
    def import_from_json(import_file: str, master_password: str) -> List[PasswordEntry]:
        """
        Importa senhas de um arquivo JSON externo.
        Suporta dois formatos:
        1. Formato do frontend: salt/nonce no metadata, ciphertext+tag em entries_encrypted
        2. Formato do backend: salt+nonce+tag+ciphertext tudo junto no blob
        
        Args:
            import_file: Caminho para o arquivo JSON a ser importado
            master_password: Senha mestra para descriptografar o arquivo
            
        Returns:
            Lista de PasswordEntry importadas
            
        Raises:
            Exception: Se o arquivo não existir, formato inválido ou senha incorreta
        """
        try:
            with open(import_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extrai informações de criptografia do meta
            meta = data.get('meta', {})
            encryption_info = meta.get('encryption', {})
            
            entries_encrypted = data.get('data', {}).get('entries_encrypted', '')
            if not entries_encrypted:
                return []  # Arquivo vazio, retorna lista vazia
            
            entries_blob = base64.b64decode(entries_encrypted)
            
            # Tenta detectar o formato: frontend ou backend
            # Frontend: tem nonce no metadata e ciphertext+tag juntos
            # Backend: tem salt+nonce+tag+ciphertext tudo junto no blob
            nonce_b64 = encryption_info.get('nonce')
            salt_b64 = encryption_info.get('salt')
            kdf_iterations = encryption_info.get('kdf_iterations', 300000)
            
            if nonce_b64 and salt_b64:
                # Formato do frontend: descriptografa usando salt/nonce do metadata
                salt = base64.b64decode(salt_b64)
                nonce = base64.b64decode(nonce_b64)
                
                # O ciphertext do frontend contém ciphertext + tag (últimos 16 bytes são o tag)
                TAG_SIZE = 16
                if len(entries_blob) < TAG_SIZE:
                    raise Exception("Arquivo corrompido: dados insuficientes")
                
                ciphertext = entries_blob[:-TAG_SIZE]
                tag = entries_blob[-TAG_SIZE:]
                
                # Deriva a chave usando PBKDF2
                key = PBKDF2(
                    master_password.encode(),
                    salt,
                    dkLen=32,  # KEY_SIZE
                    count=kdf_iterations,
                    hmac_hash_module=SHA256
                )
                
                # Descriptografa
                cipher = AES.new(key, AES.MODE_GCM, nonce=nonce, mac_len=TAG_SIZE)
                plaintext = cipher.decrypt_and_verify(ciphertext, tag)
                entries_json = plaintext.decode("utf-8")
            else:
                # Formato do backend: usa EncryptionManager
                if not salt_b64:
                    raise Exception("Arquivo JSON inválido: salt não encontrado")
                
                encryption_manager = EncryptionManager(master_password, salt=salt_b64)
                entries_json = encryption_manager.decrypt(entries_blob)
            
            entries_data = json.loads(entries_json)
            
            imported_entries = []
            for entry_data in entries_data.get('entries', []):
                entry = PasswordEntry(
                    id=entry_data.get('id', 0),  # ID pode não existir em imports
                    title=entry_data['title'],
                    site=entry_data['site'],
                    password=entry_data['password'],
                    length=entry_data['length'],
                    use_uppercase=entry_data['use_uppercase'],
                    use_lowercase=entry_data['use_lowercase'],
                    use_digits=entry_data['use_digits'],
                    use_special=entry_data['use_special'],
                    entropy=entry_data['entropy'],
                    expiration_date=datetime.fromisoformat(entry_data['expiration_date']) if entry_data.get('expiration_date') else None,
                    created_at=datetime.fromisoformat(entry_data['created_at']),
                    updated_at=datetime.fromisoformat(entry_data['updated_at'])
                )
                imported_entries.append(entry)
            
            return imported_entries
        except FileNotFoundError:
            raise Exception(f"Arquivo não encontrado: {import_file}")
        except Exception as e:
            # Se for erro de descriptografia, provavelmente senha incorreta
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ["decrypt", "mac", "tag", "verification", "authentication"]):
                raise Exception("Senha mestra incorreta ou arquivo corrompido")
            raise Exception(f"Erro ao importar arquivo: {e}")
    
    def import_entries(self, imported_entries: List[PasswordEntry]):
        """
        Adiciona entradas importadas ao gerenciador atual.
        Reatribui IDs para evitar conflitos.
        
        Args:
            imported_entries: Lista de PasswordEntry a serem importadas
        """
        for entry in imported_entries:
            # Reatribui ID para evitar conflitos
            entry.id = self.next_id
            self.next_id += 1
            self.entries.append(entry)
        
        self._save()
