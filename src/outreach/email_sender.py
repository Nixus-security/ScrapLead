import aiohttp
import logging
from src.config import Config
from src.ai.prompts import OUTREACH_EMAIL_TEMPLATE

logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self):
        self.api_key = Config.RESEND_API_KEY
        self.from_email = Config.EMAIL_FROM
        self.base_url = "https://api.resend.com/emails"
    
    async def send_single(self, lead: dict) -> bool:
        if not lead.get('email') or not self.api_key:
            return False
        
        snippet = lead.get('text', '')[:100] + "..."
        subject = f"Re: {lead.get('platform', 'your post')}"
        
        body = OUTREACH_EMAIL_TEMPLATE.format(
            context=snippet,
            first_name=lead.get('first_name', 'there'),
            platform=lead.get('platform', 'the web').capitalize(),
            snippet=snippet,
            personalized_hook="J'ai une solution qui correspond exactement à ce que tu cherches.",
            sender_name="L'équipe GnawLead"
        )
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "from": self.from_email,
            "to": [lead['email']],
            "subject": subject,
            "html": body.replace('\n', '<br>')
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=payload) as response:
                    if response.status in [200, 201]:
                        logger.info(f"Email sent to {lead['email']}")
                        return True
                    else:
                        logger.error(f"Failed to send to {lead['email']}: {await response.text()}")
        except Exception as e:
            logger.error(f"Email send error: {e}")
        
        return False
    
    async def send_batch(self, leads: list[dict]):
        for lead in leads:
            await self.send_single(lead)
            # Rate limiting handled by caller or added here