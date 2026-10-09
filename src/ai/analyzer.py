import asyncio
import json
import logging
import re
from typing import List, Dict
import aiohttp
from src.config import Config
from src.ai.prompts import INTENT_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)


class LeadAnalyzer:
    def __init__(self):
        self.api_key = Config.OPENROUTER_API_KEY
        self.model = Config.OPENROUTER_MODEL
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.semaphore = asyncio.Semaphore(getattr(Config, 'AI_CONCURRENCY', 5))

    @staticmethod
    def _parse_json(content: str) -> dict:
        """Extrait un JSON même si le modèle ajoute du texte/markdown autour."""
        match = re.search(r'\{.*?\}', content, re.DOTALL)
        if not match:
            raise ValueError(f"Aucun JSON dans la réponse: {content[:100]}")
        return json.loads(match.group(0))

    async def analyze_lead(self, session: aiohttp.ClientSession, lead: dict) -> dict:
        return await self._analyze(session, lead)

    async def _analyze(self, session, lead):
        prompt = INTENT_ANALYSIS_PROMPT.format(
            text=lead.get('text', ''),
            platform=lead.get('platform', 'unknown')
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 200
        }

        async with self.semaphore:
            for attempt in range(3):
                try:
                    async with session.post(self.base_url, headers=headers, json=payload) as response:
                        if response.status == 429 or response.status >= 500:
                            raise aiohttp.ClientResponseError(
                                response.request_info, response.history,
                                status=response.status, message="Retryable"
                            )
                        if response.status != 200:
                            body = await response.text()
                            logger.error(f"OpenRouter erreur {response.status}: {body[:200]}")
                            break
                        data = await response.json()
                        content = data['choices'][0]['message']['content']
                        result = self._parse_json(content)
                        lead['ai_score'] = int(result.get('score', 0))
                        lead['ai_reason'] = result.get('reason', '')
                        return lead
                except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, KeyError) as e:
                    wait = 2 ** attempt
                    logger.warning(f"AI analyse retry {attempt + 1}/3 dans {wait}s: {e}")
                    await asyncio.sleep(wait)

        lead['ai_score'] = 0
        lead['ai_reason'] = "analysis_failed"
        return lead

    async def score_leads(self, leads: list[dict]) -> list[dict]:
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY absent -> score IA désactivé")
            for lead in leads:
                lead['ai_score'] = 0
                lead['ai_reason'] = "no_api_key"
            return leads

        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            tasks = [self.analyze_lead(session, lead) for lead in leads]
            return await asyncio.gather(*tasks)