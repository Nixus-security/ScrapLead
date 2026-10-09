import asyncio
import pytest
from src.ai.analyzer import LeadAnalyzer


def test_parse_json_plain():
    assert LeadAnalyzer._parse_json('{"score": 85, "reason": "urgent"}') == {"score": 85, "reason": "urgent"}


def test_parse_json_wrapped_markdown():
    raw = 'Here you go:\n```json\n{"score": 42, "reason": "ok"}\n```'
    assert LeadAnalyzer._parse_json(raw)["score"] == 42


def test_parse_json_invalid():
    with pytest.raises(ValueError):
        LeadAnalyzer._parse_json("pas de json ici")


@pytest.mark.asyncio
async def test_score_leads_no_api_key(monkeypatch):
    from src.config import Config
    monkeypatch.setattr(Config, "OPENROUTER_API_KEY", None)
    analyzer = LeadAnalyzer()
    leads = [{"text": "x", "platform": "reddit"}]
    out = await analyzer.score_leads(leads)
    assert out[0]["ai_score"] == 0
    assert out[0]["ai_reason"] == "no_api_key"