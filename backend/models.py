from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union


@dataclass
class PasswordEntry:
    id: Optional[int]
    title: str
    site: str
    password: Union[str, bytes]
    length: int
    use_uppercase: bool
    use_lowercase: bool
    use_digits: bool
    use_special: bool
    entropy: float
    expiration_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
