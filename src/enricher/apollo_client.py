import asyncio
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
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                for attempt in range(3):
                    async with session.post(
                        f"{self.base_url}/people/search",
                        headers=headers,
                        json=payload
                    ) as response:
                        if response.status == 429:
                            await asyncio.sleep((2 ** attempt) * 5)
                            continue
                        if response.status != 200:
                            body = await response.text()
                            logger.error(f"Apollo erreur {response.status}: {body[:200]}")
                            return lead
                        data = await response.json()
                        people = data.get('people', [])
                        if people:
                            person = people[0]
                            lead['first_name'] = person.get('first_name') or ''
                            lead['last_name'] = person.get('last_name') or ''
                            lead['email'] = person.get('email') or ''
                            lead['company'] = person.get('organization_name') or ''
                            lead['title'] = person.get('title') or ''
                            lead['linkedin_url'] = person.get('linked_in_url') or lead.get('linkedin_url', '')
                        return lead
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Apollo enrichment failed: {e}")

        return lead
