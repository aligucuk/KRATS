# services/rss_service.py

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

# SSL uyarılarını ve timeout'u ayarla
warnings.filterwarnings("ignore")
socket.setdefaulttimeout(15.0)

class RSSService:
    """
    RSS Feed Okuyucu Servisi.
    Tıbbi haber kaynaklarından veri çeker ve veritabanına kaydeder.
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        # Ayarları DB'den veya varsayılanlardan al
        self.refresh_interval = int(self.db.get_setting("news_refresh_interval") or 30) * 60
        self.retention_days = int(self.db.get_setting("news_retention_days") or 7)
        
        logger.info("RSSService başlatıldı")

    def fetch_all_feeds(self) -> int:
        """
        Tüm aktif RSS kaynaklarını tarar ve yeni haberleri kaydeder.
        Geriye eklenen yeni haber sayısını döndürür.
        """
        try:
            logger.info("RSS taraması başlıyor...")
            
            # 1. Aktif Kaynakları Getir
            # (ORM yerine SQL sorgusu kullanarak daha güvenli yapalım)
            try:
                sources = self.db.cursor.execute("SELECT name, url FROM news_sources WHERE is_active=1").fetchall()
            except Exception as e:
                logger.error(f"Kaynaklar alınamadı: {e}")
                return 0

            if not sources:
                logger.warning("Aktif RSS kaynağı bulunamadı.")
                return 0
            
            # 2. Mevcut Linkleri Al (Tekrarı önlemek için)
            existing_links = set()
            try:
                rows = self.db.cursor.execute("SELECT link FROM medical_news").fetchall()
                existing_links = {row[0] for row in rows}
            except:
                pass

            new_count = 0
            
            # 3. Her Kaynağı Tara
            for name, url in sources:
                try:
                    content = self._fetch_content(url)
                    if not content: continue
                    
                    feed = feedparser.parse(content)
                    
                    # İlk 10 haberi al
                    for entry in feed.entries[:10]:
                        if entry.link in existing_links:
                            continue
                        
                        # Veriyi İşle
                        summary = self._clean_summary(entry)
                        img_url = self._find_image(entry)
                        pub_date = self._parse_date(entry)
                        
                        # Veritabanına Ekle
                        # (db_manager.add_news_article metodunu kullanıyoruz)
                        if self.db.add_news_article(
                            title=entry.title,
                            summary=summary,
                            link=entry.link,
                            source=name,
                            published_date=pub_date,
                            image_url=img_url
                        ):
                            new_count += 1
                            existing_links.add(entry.link)
                            
                except Exception as e:
                    logger.error(f"Kaynak hatası ({name}): {e}")
            
            # 4. Eski Haberleri Temizle
            self._cleanup_old_news()
            
            return new_count
            
        except Exception as e:
            logger.error(f"Genel RSS hatası: {e}")
            return 0

    def _fetch_content(self, url):
        """Güvenli içerik çekme (User-Agent ve SSL bypass)"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://google.com'
        }
        try:
            return requests.get(url, headers=headers, timeout=15, verify=True).content
        except:
            try:
                return requests.get(url, headers=headers, timeout=15, verify=False).content
            except:
                return None

    def _clean_summary(self, entry):
        """Özet metnini temizle (HTML taglerini kaldır)"""
        import re
        text = ""
        if hasattr(entry, 'summary'): text = entry.summary
        elif hasattr(entry, 'description'): text = entry.description
        
        text = re.sub(r'<[^>]+>', '', text)
        return text[:250] + "..." if len(text) > 250 else text

    def _find_image(self, entry):
        """Haber görselini bulmaya çalış"""
        import re
        if hasattr(entry, 'media_content'): return entry.media_content[0]['url']
        if hasattr(entry, 'media_thumbnail'): return entry.media_thumbnail[0]['url']
        
        # Metin içinde img src ara
        if hasattr(entry, 'summary'):
            match = re.search(r'src="(.*?)"', str(entry.summary))
            if match: return match.group(1)
        return None

    def _parse_date(self, entry):
        """Tarih formatını düzelt"""
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])
        return datetime.now()

    def _cleanup_old_news(self):
        """Eski haberleri sil"""
        try:
            # is_saved=0 olan ve süresi dolmuşları sil
            # Not: Bu sorguyu doğrudan SQL olarak çalıştırıyoruz
            cutoff = (datetime.now() - timedelta(days=self.retention_days)).strftime("%Y-%m-%d")
            self.db.cursor.execute(
                "DELETE FROM medical_news WHERE is_saved = 0 AND date(published_date) < ?", 
                (cutoff,)
            )
            self.db.conn.commit()
        except Exception as e:
            logger.error(f"Temizlik hatası: {e}")