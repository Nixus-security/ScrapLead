import logging
from src.config import Config

logger = logging.getLogger(__name__)

class LeadFilter:
    def __init__(self):
        self.threshold = Config.AI_SCORE_THRESHOLD
        self.seen_emails = set()
        self.seen_usernames = set()
    
    def filter_and_deduplicate(self, scored_leads: list[dict]) -> list[dict]:
        filtered = []
        
        for lead in scored_leads:
            # 1. Filtrer par score IA
            if lead.get('ai_score', 0) < self.threshold:
                continue
            
            # 2. Dédoublonnage (email prioritaire, sinon username + platform)
            email = lead.get('email', '').lower()
            username = f"{lead.get('platform')}:{lead.get('username', '')}".lower()
            
            if email and email in self.seen_emails:
                continue
            if not email and username in self.seen_usernames:
                continue
            
            # Ajouter aux vus
            if email:
                self.seen_emails.add(email)
            else:
                self.seen_usernames.add(username)
                
            filtered.append(lead)
            
        logger.info(f"Filtrage: {len(scored_leads)} leads réduits à {len(filtered)} leads chauds uniques.")
        return filtered