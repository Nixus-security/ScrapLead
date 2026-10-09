import asyncio
import random
import logging
from playwright.async_api import async_playwright
from src.config import Config

logger = logging.getLogger(__name__)

class DMSender:
    def __init__(self):
        self.platform = "twitter" # ou "discord"
    
    async def _human_type(self, page, selector: str, text: str):
        """Simule une frappe humaine avec des variations de délai."""
        await page.click(selector)
        for char in text:
            await page.keyboard.type(char, delay=random.uniform(50, 150))
            if random.random() < 0.1: # Pause aléatoire de réflexion
                await asyncio.sleep(random.uniform(0.5, 1.5))
    
    async def send_twitter_dm(self, username: str, message: str) -> bool:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
            context = await browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
            await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            page = await context.new_page()
            
            try:
                # Nécessite des cookies de session Twitter valides injectés ici
                await page.goto(f"https://twitter.com/messages/compose?recipient_id={username}", timeout=30000)
                await asyncio.sleep(random.uniform(2.0, 4.0))
                
                await self._human_type(page, 'div[role="textbox"]', message)
                await asyncio.sleep(random.uniform(1.0, 2.0))
                
                send_btn = await page.query_selector('div[data-testid="DmComposerSendMessageButton"]')
                if send_btn:
                    await send_btn.click()
                    logger.info(f"DM envoyé à {username}")
                    return True
            except Exception as e:
                logger.error(f"Échec envoi DM Twitter à {username}: {e}")
            finally:
                await browser.close()
        return False