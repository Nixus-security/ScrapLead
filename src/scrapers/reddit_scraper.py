import asyncio
import random
import logging
from typing import List
import asyncpraw
from src.scrapers.base import BaseScraper
from src.config import Config

logger = logging.getLogger(__name__)

class RedditScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.reddit = asyncpraw.Reddit(
            client_id=Config.REDDIT_CLIENT_ID,
            client_secret=Config.REDDIT_CLIENT_SECRET,
            user_agent="GnawLead/1.0"
        )
    
    async def scrape_keywords(self, keywords: list[str], limit: int = 50) -> list[dict]:
        leads = []
        
        for keyword in keywords:
            logger.info(f"Scraping Reddit for: {keyword}")
            
            async for submission in self.reddit.subreddit("all").search(
                keyword, sort="new", time_filter="week", limit=limit
            ):
                lead = {
                    'platform': 'reddit',
                    'username': submission.author.name if submission.author else 'deleted',
                    'text': self.clean_text(submission.selftext),
                    'title': self.clean_text(submission.title),
                    'source_url': f"https://reddit.com{submission.permalink}",
                    'created_at': submission.created_utc,
                    'subreddit': submission.subreddit.display_name
                }
                lead.update(self.extract_metadata(lead))
                leads.append(lead)
                
                await asyncio.sleep(random.uniform(Config.SCRAPE_DELAY_MIN, Config.SCRAPE_DELAY_MAX))
            
            for comment in await self._search_comments(keyword, limit):
                leads.append(comment)
        
        return leads
    
    async def _search_comments(self, keyword: str, limit: int) -> list[dict]:
        comments = []
        async for submission in self.reddit.subreddit("all").search(
            keyword, sort="new", time_filter="week", limit=limit // 2
        ):
            await submission.load()
            submission.comments.replace_more(limit=0)
            
            for comment in submission.comments.list()[:10]:
                if keyword.lower() in comment.body.lower():
                    lead = {
                        'platform': 'reddit',
                        'username': comment.author.name if comment.author else 'deleted',
                        'text': self.clean_text(comment.body),
                        'source_url': f"https://reddit.com{comment.permalink}",
                        'created_at': comment.created_utc,
                        'subreddit': comment.submission.subreddit.display_name
                    }
                    lead.update(self.extract_metadata(lead))
                    comments.append(lead)
                    
                    await asyncio.sleep(random.uniform(Config.SCRAPE_DELAY_MIN, Config.SCRAPE_DELAY_MAX))
        
        return comments
    
    async def scrape_user(self, username: str) -> dict:
        redditor = await self.reddit.redditor(username)
        return {
            'username': username,
            'comment_karma': redditor.comment_karma,
            'created_at': redditor.created_utc
        }