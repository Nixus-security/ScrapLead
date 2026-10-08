import asyncio
import json
import logging
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
    
    async def analyze_lead(self, lead: dict) -> dict:
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
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 200
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data['choices'][0]['message']['content']
                        result = json.loads(content)
                        lead['ai_score'] = result.get('score', 0)
                        lead['ai_reason'] = result.get('reason', '')
                        return lead
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            lead['ai_score'] = 0
            lead['ai_reason'] = f"Error: {str(e)}"
        
        return lead
    
    async def score_leads(self, leads: list[dict]) -> list[dict]:
        tasks = [self.analyze_lead(lead) for lead in leads]
        return await asyncio.gather(*tasks)