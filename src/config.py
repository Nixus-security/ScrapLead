import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    RAW_LEADS_DIR = DATA_DIR / "raw_leads"
    ENRICHED_LEADS_DIR = DATA_DIR / "enriched_leads"
    EXPORTS_DIR = DATA_DIR / "exports"
    LOGS_DIR = BASE_DIR / "logs"

    # Proxy
    PROXY_POOL = os.getenv("PROXY_POOL", "").split(",")
    PROXY_ROTATION_INTERVAL = int(os.getenv("PROXY_ROTATION_INTERVAL", "300"))

    # APIs
    APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
    HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct")

    # Reddit API (manquants -> crash RedditScraper)
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")

    # AI Scoring
    AI_SCORE_THRESHOLD = int(os.getenv("AI_SCORE_THRESHOLD", "75"))
    AI_CONCURRENCY = int(os.getenv("AI_CONCURRENCY", "5"))

    # Outreach
    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    EMAIL_FROM = os.getenv("EMAIL_FROM", "leads@gnawlead.com")

    # Discord
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    DISCORD_GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0"))

    # Rate Limiting
    SCRAPE_DELAY_MIN = float(os.getenv("SCRAPE_DELAY_MIN", "2.0"))
    SCRAPE_DELAY_MAX = float(os.getenv("SCRAPE_DELAY_MAX", "5.0"))
    OUTREACH_DELAY_MIN = float(os.getenv("OUTREACH_DELAY_MIN", "10.0"))
    OUTREACH_DELAY_MAX = float(os.getenv("OUTREACH_DELAY_MAX", "30.0"))

    @classmethod
    def ensure_dirs(cls):
        for dir_path in [cls.RAW_LEADS_DIR, cls.ENRICHED_LEADS_DIR, cls.EXPORTS_DIR, cls.LOGS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)

Config.ensure_dirs()