# services/news_service.py

import time
import socket
import warnings
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
import requests
import feedparser

from config import settings
from utils.logger import get_logger
from database.db_manager import DatabaseManager

logger = get_logger(__name__)

# Disable SSL warnings for RSS feeds
warnings.filterwarnings("ignore")
socket.setdefaulttimeout(15.0)


class MedicalNewsService:
    """Medical news RSS feed aggregation service"""
    
    def __init__(self, db: DatabaseManager):
        """Initialize news service
        
        Args:
            db: Database manager instance
        """
        self.db = db
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        
        # Configuration from database
        self.refresh_interval = int(
            self.db.get_setting("news_refresh_interval") or 30
        ) * 60  # Convert to seconds
        
        self.retention_days = int(
            self.db.get_setting("news_retention_days") or 7
        )
        
        logger.info("Medical news service initialized")
    
    def start(self):
        """Start news service in background"""
        if self.is_running:
            logger.warning("News service already running")
            return
        
        self.is_running = True
        self.thread = threading.Thread(
            target=self._run_loop,
            name="MedicalNewsService",
            daemon=True
        )
        self.thread.start()
        logger.info("Medical news service started")
    
    def stop(self):
        """Stop news service"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Medical news service stopped")
    
    def _run_loop(self):
        """Main service loop"""
        logger.info("News service loop started")
        
        # Initial fetch
        time.sleep(5)  # Wait for app to fully start
        self.fetch_news()
        
        while self.is_running:
            try:
                time.sleep(self.refresh_interval)
                
                if self.is_running:
                    self.fetch_news()
            
            except Exception as e:
                logger.error(f"News service error: {e}")
                time.sleep(60)
    
    def fetch_news(
        self, progress_callback: Optional[Callable[[str], None]] = None
    ) -> int:
        """Fetch news from all sources
        
        Args:
            progress_callback: Optional callback for progress updates
            
        Returns:
            Number of new articles fetched
        """
        try:
            logger.info("Fetching medical news")
            
            # Get news sources from database
            with self.db.get_session() as session:
                from database.models import NewsSource
                sources = session.query(NewsSource).filter_by(is_active=True).all()
            
            if not sources:
                logger.warning("No active news sources")
                return 0
            
            # Get existing article links to avoid duplicates
            existing_links = set()
            with self.db.get_session() as session:
                from database.models import MedicalNews
                existing = session.query(MedicalNews.link).all()
                existing_links = {link[0] for link in existing}
            
            new_count = 0
            
            for source in sources:
                if progress_callback:
                    progress_callback(f"Fetching from {source.name}...")
                
                try:
                    # Fetch RSS feed
                    feed_data = self._fetch_feed_content(source.url)
                    
                    if not feed_data:
                        logger.warning(f"Failed to fetch feed: {source.name}")
                        continue
                    
                    # Parse feed
                    feed = feedparser.parse(feed_data)
                    
                    # Process entries
                    for entry in feed.entries[:10]:  # Limit to 10 per source
                        try:
                            # Check if already exists
                            if entry.link in existing_links:
                                continue
                            
                            # Extract data
                            title = entry.title
                            summary = self._extract_summary(entry)
                            link = entry.link
                            image_url = self._extract_image(entry)
                            published_date = self._parse_date(entry)
                            
                            # Add to database
                            if self.db.add_news_article(
                                title=title,
                                summary=summary,
                                link=link,
                                source=source.name,
                                published_date=published_date,
                                image_url=image_url
                            ):
                                new_count += 1
                                existing_links.add(link)
                        
                        except Exception as e:
                            logger.error(f"Failed to process entry: {e}")
                
                except Exception as e:
                    logger.error(f"Failed to fetch from {source.name}: {e}")
            
            if new_count > 0:
                logger.info(f"Fetched {new_count} new articles")
            
            # Cleanup old articles
            self._cleanup_old_articles()
            
            return new_count
        
        except Exception as e:
            logger.error(f"News fetch failed: {e}")
            return 0
    
    def _fetch_feed_content(self, url: str) -> Optional[bytes]:
        """Fetch RSS feed content with proper headers
        
        Args:
            url: Feed URL
            
        Returns:
            Feed content as bytes or None
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://google.com'
        }
        
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=15,
                verify=True
            )
            return response.content
        except requests.exceptions.SSLError:
            # Retry without SSL verification
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=15,
                    verify=False
                )
                return response.content
            except:
                return None
        except:
            return None
    
    def _extract_summary(self, entry) -> str:
        """Extract and clean summary from entry
        
        Args:
            entry: Feed entry object
            
        Returns:
            Cleaned summary text
        """
        import re
        
        # Try different summary fields
        summary = ""
        if hasattr(entry, 'summary'):
            summary = entry.summary
        elif hasattr(entry, 'description'):
            summary = entry.description
        
        # Remove HTML tags
        summary = re.sub(r'<[^>]+>', '', summary)
        
        # Limit length
        if len(summary) > 250:
            summary = summary[:247] + "..."
        
        return summary.strip()
    
    def _extract_image(self, entry) -> Optional[str]:
        """Extract image URL from entry
        
        Args:
            entry: Feed entry object
            
        Returns:
            Image URL or None
        """
        import re
        
        # Try media content
        if hasattr(entry, 'media_content'):
            return entry.media_content[0]['url']
        
        # Try media thumbnail
        if hasattr(entry, 'media_thumbnail'):
            return entry.media_thumbnail[0]['url']
        
        # Try to find image in content
        if hasattr(entry, 'summary'):
            match = re.search(r'src="(.*?)"', str(entry.summary))
            if match:
                return match.group(1)
        
        return None
    
    def _parse_date(self, entry) -> datetime:
        """Parse published date from entry
        
        Args:
            entry: Feed entry object
            
        Returns:
            Parsed datetime
        """
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                return datetime(*entry.published_parsed[:6])
            except:
                pass
        
        return datetime.now()
    
    def _cleanup_old_articles(self):
        """Remove old articles based on retention policy"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            with self.db.get_session() as session:
                from database.models import MedicalNews
                deleted = session.query(MedicalNews).filter(
                    MedicalNews.published_date < cutoff_date,
                    MedicalNews.is_saved == False
                ).delete()
                
                session.commit()
                
                if deleted > 0:
                    logger.info(f"Cleaned up {deleted} old articles")
        
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    def get_article_count(self) -> Dict[str, int]:
        """Get article count statistics
        
        Returns:
            Dictionary with counts
        """
        try:
            with self.db.get_session() as session:
                from database.models import MedicalNews
                
                total = session.query(MedicalNews).count()
                unread = session.query(MedicalNews).filter_by(is_read=False).count()
                saved = session.query(MedicalNews).filter_by(is_saved=True).count()
                
                return {
                    'total': total,
                    'unread': unread,
                    'saved': saved
                }
        except:
            return {'total': 0, 'unread': 0, 'saved': 0}