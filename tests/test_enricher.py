import pytest
from src.enricher.apollo_client import ApolloEnricher
from src.enricher.hunter_client import HunterEnricher
from src.config import Config


@pytest.mark.asyncio
async def test_apollo_no_key_returns_lead(monkeypatch):
    monkeypatch.setattr(Config, "APOLLO_API_KEY", None)
    lead = {"username": "bob"}
    out = await ApolloEnricher().enrich(lead)
    assert out == lead


@pytest.mark.asyncio
async def test_hunter_no_company_skips(monkeypatch):
    monkeypatch.setattr(Config, "HUNTER_API_KEY", "fake")
    lead = {"username": "bob"}
    out = await HunterEnricher().enrich(lead)
    assert "email" not in out or not out.get("email")


def test_parse_name():
    e = ApolloEnricher.__new__(ApolloEnricher)
    from src.enricher.base_enricher import BaseEnricher
    assert BaseEnricher.parse_name(e, "Jane Doe") == ("Jane", "Doe")