import re
from typing import Dict, Optional

class DataFormatter:
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        # Supprime les emojis et caractères de contrôle
        text = re.sub(r'[^\w\s\-\.\,\!\?]', '', text)
        # Normalise les espaces
        return ' '.join(text.split())
    
    @staticmethod
    def validate_email(email: str) -> bool:
        return bool(re.match(DataFormatter.EMAIL_REGEX, str(email).strip()))
    
    @staticmethod
    def format_name(full_name: str) -> tuple[str, str]:
        parts = str(full_name).strip().title().split()
        if len(parts) == 0:
            return "Unknown", ""
        if len(parts) == 1:
            return parts[0], ""
        return parts[0], parts[-1]
    
    @classmethod
    def sanitize_lead(cls, lead: dict) -> dict:
        lead['text'] = cls.clean_text(lead.get('text', ''))
        lead['username'] = str(lead.get('username', '')).strip().lower()
        
        if 'full_name' in lead:
            first, last = cls.format_name(lead['full_name'])
            lead['first_name'] = first
            lead['last_name'] = last
            
        if 'email' in lead and not cls.validate_email(lead['email']):
            lead['email'] = '' # Invalide, on vide le champ
            
        return lead