"""
Gerador de senhas com cálculo de entropia
"""
import random
import string
import math


class PasswordGenerator:
    """Gerador de senhas com opções customizáveis"""
    
    UPPERCASE = string.ascii_uppercase
    LOWERCASE = string.ascii_lowercase
    DIGITS = string.digits
    SPECIAL = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    @staticmethod
    def generate(
        length: int,
        use_uppercase: bool = True,
        use_lowercase: bool = True,
        use_digits: bool = True,
        use_special: bool = True
    ) -> str:
        """
        Gera uma senha aleatória
        
        Args:
            length: Tamanho da senha
            use_uppercase: Incluir letras maiúsculas
            use_lowercase: Incluir letras minúsculas
            use_digits: Incluir dígitos
            use_special: Incluir caracteres especiais
            
        Returns:
            Senha gerada
        """
        charset = ""
        if use_uppercase:
            charset += PasswordGenerator.UPPERCASE
        if use_lowercase:
            charset += PasswordGenerator.LOWERCASE
        if use_digits:
            charset += PasswordGenerator.DIGITS
        if use_special:
            charset += PasswordGenerator.SPECIAL
        
        if not charset:
            raise ValueError("Pelo menos um tipo de caractere deve ser selecionado")
        
        password_chars = []
        if use_uppercase:
            password_chars.append(random.choice(PasswordGenerator.UPPERCASE))
        if use_lowercase:
            password_chars.append(random.choice(PasswordGenerator.LOWERCASE))
        if use_digits:
            password_chars.append(random.choice(PasswordGenerator.DIGITS))
        if use_special:
            password_chars.append(random.choice(PasswordGenerator.SPECIAL))
        
        while len(password_chars) < length:
            password_chars.append(random.choice(charset))
        
        random.shuffle(password_chars)
        
        return ''.join(password_chars[:length])
    
    @staticmethod
    def calculate_entropy(
        length: int,
        use_uppercase: bool = True,
        use_lowercase: bool = True,
        use_digits: bool = True,
        use_special: bool = True
    ) -> float:
        """
        Calcula a entropia de uma senha baseado no tamanho e charset
        
        Args:
            length: Tamanho da senha
            use_uppercase: Incluir letras maiúsculas
            use_lowercase: Incluir letras minúsculas
            use_digits: Incluir dígitos
            use_special: Incluir caracteres especiais
            
        Returns:
            Entropia em bits
        """
        charset_size = 0
        if use_uppercase:
            charset_size += len(PasswordGenerator.UPPERCASE)
        if use_lowercase:
            charset_size += len(PasswordGenerator.LOWERCASE)
        if use_digits:
            charset_size += len(PasswordGenerator.DIGITS)
        if use_special:
            charset_size += len(PasswordGenerator.SPECIAL)
        
        if charset_size == 0:
            return 0.0
        
        entropy = length * math.log2(charset_size)
        return round(entropy, 2)
    
    @staticmethod
    def get_entropy_level(entropy: float) -> str:
        """
        Retorna o nível de entropia em texto
        
        Args:
            entropy: Entropia em bits
            
        Returns:
            Nível de entropia (Fraco, Médio, Forte, Muito Forte)
        """
        if entropy < 28:
            return "Fraco"
        elif entropy < 36:
            return "Médio"
        elif entropy < 60:
            return "Forte"
        else:
            return "Muito Forte"

