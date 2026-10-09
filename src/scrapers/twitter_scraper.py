import asyncio
import random
import logging
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from src.scrapers.base import BaseScraper
from src.config import Config
from src.scrapers.proxy_manager import ProxyManager

logger = logging.getLogger(__name__)

class TwitterScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.proxy_manager = ProxyManager()
    
    async def scrape_keywords(self, keywords: list[str], limit: int = 50) -> list[dict]:
        leads = []
        proxy = self.proxy_manager.get_proxy()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
            )
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                proxy={"server": proxy} if proxy else None
            )
            await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            page = await context.new_page()
            
            for keyword in keywords:
                logger.info(f"Scraping Twitter for: {keyword}")
                search_url = f"https://twitter.com/search?q={keyword.replace(' ', '%20')}&f=live"
                
                try:
                    await page.goto(search_url, timeout=30000)
                    await page.wait_for_selector('article', timeout=10000)
                    
                    # Scroll to load tweets
                    for _ in range(5):
                        await page.mouse.wheel(0, 1000)
                        await asyncio.sleep(random.uniform(1.5, 3.0))
                    
                    articles = await page.query_selector_all('article')
                    for article in articles[:limit]:
                        try:
                            username_el = await article.query_selector('a[role="link"]')
                            text_el = await article.query_selector('div[lang]')
                            
                            if username_el and text_el:
                                username = (await username_el.get_attribute('href') or '').replace('/', '')
                                text = await text_el.inner_text()
                                
                                lead = {
                                    'platform': 'twitter',
                                    'username': username,
                                    'text': self.clean_text(text),
                                    'source_url': f"https://twitter.com/{username}",
                                    'scraped_at': self.extract_metadata({})['scraped_at']
                                }
                                leads.append(lead)
                        except Exception:
                            continue
                            
                except PlaywrightTimeout:
                    logger.warning(f"Twitter timeout on keyword: {keyword}")
                
                await asyncio.sleep(random.uniform(Config.SCRAPE_DELAY_MIN, Config.SCRAPE_DELAY_MAX))
            
            await browser.close()
        return leads
    
    async def scrape_user(self, username: str) -> dict:
        return {'username': username, 'platform': 'twitter', 'status': 'stub'}