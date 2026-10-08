import aiohttp
import logging
from typing import Optional
from src.config import Config
from src.enricher.base_enricher import BaseEnricher

logger = logging.getLogger(__name__)

class ApolloEnricher(BaseEnricher):
    def __init__(self):
        self.api_key = Config.APOLLO_API_KEY
        self.base_url = "https://api.apollo.io/v1"
    
    async def enrich(self, lead: dict) -> Optional[dict]:
        if not self.api_key:
            logger.warning("Apollo API key not configured")
            return lead
        
        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": self.api_key
        }
        
        payload = {
            "q_keywords": lead.get('username', ''),
            "per_page": 1
        }
        
        if lead.get('linkedin_url'):
            payload["linkedin_url"] = lead['linkedin_url']
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/people/search",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        people = data.get('people', [])
                        if people:
                            person = people[0]
                            lead['first_name'] = person.get('first_name', '')
                            lead['last_name'] = person.get('last_name', '')
                            lead['email'] = person.get('email', '')
                            lead['company'] = person.get('organization_name', '')
                            lead['title'] = person.get('title', '')
                            return lead
        except Exception as e:
            logger.error(f"Apollo enrichment failed: {e}")
        
        return lead