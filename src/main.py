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

async def run_pipeline(keywords: list[str], platforms: list[str] = None):
    if platforms is None:
        platforms = ["reddit", "twitter"]
    
    logger.info(f"Pipeline started. Keywords: {keywords}, Platforms: {platforms}")
    
    # Phase 1: Scraping
    raw_leads = []
    if "reddit" in platforms:
        reddit = RedditScraper()
        reddit_leads = await reddit.scrape_keywords(keywords, limit=50)
        raw_leads.extend(reddit_leads)
        logger.info(f"Reddit: {len(reddit_leads)} leads collected")
    
    if "twitter" in platforms:
        twitter = TwitterScraper()
        twitter_leads = await twitter.scrape_keywords(keywords, limit=50)
        raw_leads.extend(twitter_leads)
        logger.info(f"Twitter: {len(twitter_leads)} leads collected")
    
    # Save raw leads
    raw_file = Config.RAW_LEADS_DIR / f"raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    import json
    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump(raw_leads, f, ensure_ascii=False, indent=2)
    
    # Phase 2: AI Analysis
    analyzer = LeadAnalyzer()
    scored_leads = await analyzer.score_leads(raw_leads)
    hot_leads = [lead for lead in scored_leads if lead.get('ai_score', 0) >= Config.AI_SCORE_THRESHOLD]
    logger.info(f"AI Analysis: {len(hot_leads)} hot leads (score >= {Config.AI_SCORE_THRESHOLD})")
    
    # Phase 3: Enrichment
    enricher = ApolloEnricher()
    enriched_leads = []
    for lead in hot_leads:
        enriched = await enricher.enrich(lead)
        if enriched:
            enriched_leads.append(enriched)
        await asyncio.sleep(1)  # Rate limit
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
            campaign = target_manager.get_campaign(name)
            status = "✅ Active" if campaign.get('active') else "❌ Inactive"
            print(f"  - {name}: {status} ({len(campaign.get('keywords', []))} keywords)")
    else:
        campaign = target_manager.get_campaign(args.campaign)
        if campaign:
            print(f"🐀 Lancement de la campagne: {args.campaign or target_manager.targets['default_campaign']}")
            asyncio.run(run_pipeline(
                keywords=campaign['keywords'],
                platforms=campaign['platforms'],
                limit=campaign.get('limit', 50)
            ))
        else:
            print("❌ Aucune campagne valide trouvée. Vérifie targets.json")