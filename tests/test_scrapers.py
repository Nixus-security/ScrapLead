import pytest
from src.scrapers.base import BaseScraper
from src.scrapers.proxy_manager import ProxyManager
from src.config import Config


class DummyScraper(BaseScraper):
    async def scrape_keywords(self, keywords, limit=50):
        return []

    async def scrape_user(self, username):
        return {}


def test_base_metadata():
    s = DummyScraper()
    md = s.extract_metadata({})
    assert md["platform"] == "dummy"
    assert "scraped_at" in md


def test_clean_text():
    s = DummyScraper()
    assert s.clean_text(" a\nb\r ") == "a b"


def test_proxy_empty_pool():
    pm = ProxyManager.__new__(ProxyManager)
    pm.proxies = []
    assert pm.get_proxy() is None
    assert pm.get_proxy_dict() == {}


def test_proxy_formats_url():
    pm = ProxyManager.__new__(ProxyManager)
    pm.proxies = ["user:pass@1.2.3.4:8080"]
    p = pm.get_proxy()
    assert p.startswith("http://")


@pytest.mark.asyncio
async def test_base_is_abstract():
    with pytest.raises(TypeError):
        BaseScraper()  # noqa: abstract instantiation must fail


@pytest.mark.asyncio
async def test_dummy_scraper_async_contract():
    s = DummyScraper()
    result = await s.scrape_keywords(["x"], limit=5)
    assert isinstance(result, list)
    user = await s.scrape_user("bob")
    assert user == {}