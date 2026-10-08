from abc import ABC, abstractmethod
from typing import List, Dict

class BaseScraper(ABC):
    def __init__(self):
        self.platform = self.__class__.__name__.replace("Scraper", "").lower()
    
    @abstractmethod
    async def scrape_keywords(self, keywords: list[str], limit: int = 50) -> list[dict]:
        pass
    
    @abstractmethod
    async def scrape_user(self, username: str) -> dict:
        pass
    
    def clean_text(self, text: str) -> str:
        return text.strip().replace('\n', ' ').replace('\r', '')
    
    def extract_metadata(self, post_data: dict) -> dict:
        return {
            'platform': self.platform,
            'scraped_at': __import__('datetime').datetime.now().isoformat()
        }