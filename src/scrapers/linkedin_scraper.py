import asyncio
import random
import logging
import json
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from src.scrapers.base import BaseScraper
from src.config import Config

logger = logging.getLogger(__name__)

class LinkedInScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.cookie_string = Config.LINKEDIN_COOKIE

    async def _inject_cookies(self, page):
        if not self.cookie_string:
            logger.warning("Aucun cookie LinkedIn fourni. Le scraping échouera probablement.")
            return
        
        try:
            cookies = json.loads(self.cookie_string)
            await page.context.add_cookies(cookies)
            logger.info("Cookies LinkedIn injectés avec succès.")
        except json.JSONDecodeError:
            logger.error("Format de cookie LinkedIn invalide. Attendu: JSON array.")

    async def scrape_keywords(self, keywords: list[str], limit: int = 50) -> list[dict]:
        leads = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox'
                ]
            )
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            # Masquer webdriver
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            """)
            
            page = await context.new_page()
            await self._inject_cookies(page)
            
            # Vérifier si on est connecté
            await page.goto("https://www.linkedin.com/feed/", timeout=30000)
            await asyncio.sleep(3) # Laisser le JS charger
            
            for keyword in keywords:
                logger.info(f"Scraping LinkedIn pour : {keyword}")
                search_url = f"https://www.linkedin.com/search/results/people/?keywords={keyword.replace(' ', '%20')}&origin=GLOBAL_SEARCH_HEADER"
                
                try:
                    await page.goto(search_url, timeout=30000)
                    await page.wait_for_selector('.reusable-search__result-container', timeout=15000)
                    
                    # Scroll pour charger les résultats
                    for _ in range(3):
                        await page.mouse.wheel(0, 800)
                        await asyncio.sleep(random.uniform(1.5, 2.5))
                    
                    cards = await page.query_selector_all('.reusable-search__result-container')
                    
                    for card in cards[:limit]:
                        try:
                            name_el = await card.query_selector('.entity-result__title-text a span[aria-hidden="true"]')
                            title_el = await card.query_selector('.entity-result__primary-subtitle')
                            link_el = await card.query_selector('.entity-result__title-text a')
                            
                            if name_el and link_el:
                                name = await name_el.inner_text()
                                title = await title_el.inner_text() if title_el else "Non spécifié"
                                profile_url = await link_el.get_attribute('href')
                                
                                # Extraire le username de l'URL
                                username = profile_url.split('/in/')[-1].split('/')[0] if '/in/' in profile_url else 'unknown'
                                
                                lead = {
                                    'platform': 'linkedin',
                                    'username': username,
                                    'full_name': self.clean_text(name),
                                    'title': self.clean_text(title),
                                    'linkedin_url': profile_url.split('?')[0],
                                    'text': f"Recherche: {keyword}", # Placeholder pour l'analyseur IA
                                    'source_url': profile_url.split('?')[0],
                                    'scraped_at': self.extract_metadata({})['scraped_at']
                                }
                                leads.append(lead)
                                
                        except Exception as e:
                            logger.debug(f"Erreur extraction carte LinkedIn: {e}")
                            continue
                            
                except PlaywrightTimeout:
                    logger.warning(f"Timeout LinkedIn sur le mot-clé: {keyword}. Vérifiez les cookies ou le captcha.")
                
                # Délai humain entre les recherches
                await asyncio.sleep(random.uniform(Config.SCRAPE_DELAY_MIN, Config.SCRAPE_DELAY_MAX))
            
            await browser.close()
            
        return leads

    async def scrape_user(self, username: str) -> dict:
        # Pour une recherche directe par profil
        return {'username': username, 'platform': 'linkedin', 'status': 'stub_implementation'}