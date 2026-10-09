import pytest
from src.export.formatters import DataFormatter
from src.export.csv_exporter import CSVExporter
from src.config import Config


def test_validate_email():
    assert DataFormatter.validate_email("a@b.com")
    assert not DataFormatter.validate_email("nope")
    assert not DataFormatter.validate_email("")


def test_clean_text():
    assert DataFormatter.clean_text("  hello \n world ") == "hello world"


def test_format_name():
    assert DataFormatter.format_name("john DOE") == ("John", "Doe")
    assert DataFormatter.format_name("cher") == ("Cher", "")


def test_sanitize_lead_invalid_email_dropped():
    lead = {"text": "hi", "username": " Bob ", "email": "bad@@x"}
    out = DataFormatter.sanitize_lead(dict(lead))
    assert out["email"] == ""
    assert out["username"] == "bob"


def test_csv_export(tmp_path, monkeypatch):
    leads = [
        {"platform": "reddit", "username": "u1", "ai_score": 90, "text": "t"},
        {"platform": "twitter", "username": "u2", "ai_score": 40, "text": "t"},
    ]
    monkeypatch.setattr(Config, "EXPORTS_DIR", tmp_path)
    path = CSVExporter().export(leads)
    assert path.exists()
    content = path.read_text(encoding="utf-8-sig")
    # tri par score decroissant -> u1 premier
    assert content.index("u1") < content.index("u2")
