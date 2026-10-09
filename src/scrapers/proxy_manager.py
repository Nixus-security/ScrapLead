import random
import logging
from src.config import Config

logger = logging.getLogger(__name__)

class ProxyManager:
    def __init__(self):
        self.proxies = [p.strip() for p in Config.PROXY_POOL if p.strip()]
        self.current_index = 0
    
    def get_proxy(self) -> str:
        if not self.proxies:
            return None
        
        proxy = random.choice(self.proxies)
        # Format for Playwright/aiohttp: http://user:pass@ip:port
        if not proxy.startswith('http'):
            proxy = f"http://{proxy}"
            
        logger.debug(f"Rotated to proxy: {proxy.split('@')[-1]}")
        return proxy
    
    def get_proxy_dict(self) -> dict:
        proxy_url = self.get_proxy()
        if not proxy_url:
            return {}
        return {"http": proxy_url, "https": proxy_url}