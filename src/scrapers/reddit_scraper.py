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
        if not Config.REDDIT_CLIENT_ID or not Config.REDDIT_CLIENT_SECRET:
            raise ValueError("REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET manquants dans .env")
        self.reddit = asyncpraw.Reddit(
            client_id=Config.REDDIT_CLIENT_ID,
            client_secret=Config.REDDIT_CLIENT_SECRET,
            user_agent="GnawLead/1.0"
        )

    async def close(self):
        await self.reddit.close()

    async def scrape_keywords(self, keywords: list[str], limit: int = 50) -> list[dict]:
        leads = []

        for keyword in keywords:
            logger.info(f"Scraping Reddit for: {keyword}")
            try:
                async for submission in self.reddit.subreddit("all").search(
                    keyword, sort="new", time_filter="week", limit=limit
                ):
                    author = getattr(submission, 'author', None)
                    if author is None:
                        continue
                    lead = {
                        'platform': 'reddit',
                        'username': str(author),
                        'text': self.clean_text(submission.selftext or ''),
                        'title': self.clean_text(submission.title or ''),
                        'source_url': f"https://reddit.com{submission.permalink}",
                        'created_at': submission.created_utc,
                        'subreddit': str(submission.subreddit)
                    }
                    lead.update(self.extract_metadata(lead))
                    leads.append(lead)

                    await asyncio.sleep(random.uniform(Config.SCRAPE_DELAY_MIN, Config.SCRAPE_DELAY_MAX))

                comments = await self._search_comments(keyword, limit)
                leads.extend(comments)
            except Exception as e:  # incl. erreurs réseau asyncprawcore
                logger.error(f"Reddit network error on '{keyword}': {e}")
            except Exception as e:
                logger.error(f"Reddit scrape failed on '{keyword}': {e}")

        return leads

    async def _search_comments(self, keyword: str, limit: int) -> list[dict]:
        comments = []
        async for submission in self.reddit.subreddit("all").search(
            keyword, sort="new", time_filter="week", limit=max(limit // 2, 5)
        ):
            try:
                await submission.comment_forest.fetch_more(limit=0)
            except Exception as e:
                logger.debug(f"Comment fetch skipped: {e}")
                continue

            forest = getattr(submission, 'comments', None)
            if forest is None:
                continue

            for comment in forest.list()[:10]:
                body = getattr(comment, 'body', '') or ''
                if keyword.lower() not in body.lower():
                    continue
                author = getattr(comment, 'author', None)
                if author is None:
                    continue
                lead = {
                    'platform': 'reddit',
                    'username': str(author),
                    'text': self.clean_text(body),
                    'source_url': f"https://reddit.com{comment.permalink}",
                    'created_at': comment.created_utc,
                    'subreddit': str(submission.subreddit)
                }
                lead.update(self.extract_metadata(lead))
                comments.append(lead)

                await asyncio.sleep(random.uniform(Config.SCRAPE_DELAY_MIN, Config.SCRAPE_DELAY_MAX))

        return comments

    async def scrape_user(self, username: str) -> dict:
        redditor = await self.reddit.redditor(username)
        await redditor.load()
        return {
            'username': username,
            'platform': 'reddit',
            'comment_karma': redditor.comment_karma,
            'created_at': redditor.created_utc
        }
