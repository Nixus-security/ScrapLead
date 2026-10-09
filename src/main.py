import asyncio
import logging
from datetime import datetime
from pathlib import Path
from src.config.targets import TargetManager

from src.config import Config
from src.scrapers.reddit_scraper import RedditScraper
from src.scrapers.twitter_scraper import TwitterScraper
from src.ai.analyzer import LeadAnalyzer
from src.enricher.apollo_client import ApolloEnricher
from src.export.csv_exporter import CSVExporter
from src.outreach.email_sender import EmailSender

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOGS_DIR / "pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def run_pipeline(keywords: list[str], platforms: list[str] = None, limit: int = 50):
    if platforms is None:
        platforms = ["reddit", "twitter"]

    logger.info(f"Pipeline started. Keywords: {keywords}, Platforms: {platforms}")

    # Phase 1: Scraping (plateformes en parallèle)
    async def _scrape_reddit():
        reddit = RedditScraper()
        leads = await reddit.scrape_keywords(keywords, limit=limit)
        logger.info(f"Reddit: {len(leads)} leads collected")
        return leads

    async def _scrape_twitter():
        twitter = TwitterScraper()
        leads = await twitter.scrape_keywords(keywords, limit=limit)
        logger.info(f"Twitter: {len(leads)} leads collected")
        return leads

    scrape_tasks = []
    if "reddit" in platforms:
        scrape_tasks.append(_scrape_reddit())
    if "twitter" in platforms:
        scrape_tasks.append(_scrape_twitter())

    raw_leads = []
    for result in await asyncio.gather(*scrape_tasks, return_exceptions=True):
        if isinstance(result, Exception):
            logger.error(f"Échec d'un scraper: {result}")
        else:
            raw_leads.extend(result)

    # Dédoublonnage brut avant analyse IA (économie de tokens)
    seen_keys = set()
    deduped = []
    for lead in raw_leads:
        key = (lead.get('platform'), lead.get('username'), lead.get('text', '')[:80])
        if key not in seen_keys:
            seen_keys.add(key)
            deduped.append(lead)
    raw_leads = deduped
    logger.info(f"{len(raw_leads)} leads uniques après dédoublonnage brut")

    # Save raw leads
    import json
    raw_file = Config.RAW_LEADS_DIR / f"raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump(raw_leads, f, ensure_ascii=False, indent=2)

    if not raw_leads:
        logger.warning("Aucun lead collecté. Pipeline arrêté.")
        return []

    # Phase 2: AI Analysis
    analyzer = LeadAnalyzer()
    scored_leads = await analyzer.score_leads(raw_leads)
    hot_leads = [lead for lead in scored_leads if lead.get('ai_score', 0) >= Config.AI_SCORE_THRESHOLD]
    logger.info(f"AI Analysis: {len(hot_leads)} hot leads (score >= {Config.AI_SCORE_THRESHOLD})")

    # Phase 3: Enrichment (en parallèle, limité en concurrence)
    enricher = ApolloEnricher()
    sem = asyncio.Semaphore(5)

    async def _enrich(lead: dict):
        async with sem:
            enriched = await enricher.enrich(lead)
            await asyncio.sleep(1)  # Rate limit API
            return enriched

    results = await asyncio.gather(*(_enrich(l) for l in hot_leads), return_exceptions=True)
    enriched_leads = [r for r in results if isinstance(r, dict) and r]
    logger.info(f"Enrichment: {len(enriched_leads)} leads enriched")

    # Phase 4: Export
    exporter = CSVExporter()
    csv_path = exporter.export(enriched_leads)
    logger.info(f"Export: {csv_path}")

    # Phase 5: Outreach (optional)
    # sender = EmailSender()
    # await sender.send_batch(enriched_leads)

    logger.info("Pipeline completed")
    return enriched_leads

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GnawLead Pipeline")
    parser.add_argument('--campaign', type=str, help='Nom de la campagne à exécuter')
    parser.add_argument('--list', action='store_true', help='Lister toutes les campagnes')
    args = parser.parse_args()

    target_manager = TargetManager()

    if args.list:
        campaigns = target_manager.list_campaigns()
        print("Campagnes disponibles:")
        for name in campaigns:
            campaign = target_manager.get_campaign(name) or target_manager.targets['campaigns'].get(name, {})
            status = "✅ Active" if campaign.get('active') else "❌ Inactive"
            print(f"  - {name}: {status} ({len(campaign.get('keywords', []))} keywords)")
    else:
        campaign = target_manager.get_campaign(args.campaign)
        if campaign:
            print(f"🐀 Lancement de la campagne: {args.campaign or target_manager.targets.get('default_campaign')}")
            asyncio.run(run_pipeline(
                keywords=campaign['keywords'],
                platforms=campaign.get('platforms'),
                limit=campaign.get('limit', 50)
            ))
        else:
            print("❌ Aucune campagne valide trouvée. Vérifie targets.json")