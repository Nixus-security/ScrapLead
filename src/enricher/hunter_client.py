import aiohttp
import logging
from src.config import Config
from src.enricher.base_enricher import BaseEnricher

logger = logging.getLogger(__name__)

class HunterEnricher(BaseEnricher):
    def __init__(self):
        self.api_key = Config.HUNTER_API_KEY
        self.base_url = "https://api.hunter.io/v2"
    
    async def enrich(self, lead: dict):
        if not self.api_key or not lead.get('company'):
            return lead
        
        domain = self._extract_domain(lead.get('company', ''))
        if not domain:
            return lead
            
        first, last = self.parse_name(lead.get('username', 'Unknown User'))
        
        url = f"{self.base_url}/email-finder"
        params = {
            "domain": domain,
            "first_name": first,
            "last_name": last,
            "api_key": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        email_data = data.get('data', {})
                        if email_data.get('email'):
                            lead['email'] = email_data['email']
                            lead['email_confidence'] = email_data.get('score', 0)
        except Exception as e:
            logger.error(f"Hunter enrichment failed: {e}")
            
        return lead

    def _extract_domain(self, company_name: str) -> str:
        # Simplifié : enlève les espaces et ajoute .com (à améliorer avec un vrai parser de domaine)
        return company_name.lower().replace(' ', '') + '.com'