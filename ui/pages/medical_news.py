"""
Medical News Page - Tıbbi Haberler
RSS feed okuyucu, otomatik güncelleme
"""

import flet as ft
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from services.rss_service import RSSService
from utils.logger import app_logger
import threading


class MedicalNewsPage:
    def __init__(self, page: ft.Page, db: DatabaseManager):
        self.page = page
        self.db = db
        self.rss_service = RSSService(db)
        
        # Filtreler
        self.show_unread_only = False
        
        # UI Components
        self.news_grid = ft.GridView(
            expand=True,
            runs_count=2,
            max_extent=500,
            child_aspect_ratio=0.85,
            spacing=15,
            run_spacing=15
        )
        
        self.saved_news_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        
        self.refresh_progress = ft.ProgressRing(visible=False, width=20, height=20)
        
    def view(self):
        """Ana görünüm"""
        self.load_news()
        
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.NEWSPAPER, color="teal", size=30),
                ft.Column([
                    ft.Text("Tıbbi Bülten", size=24, weight="bold"),
                    ft.Text("Güncel tıbbi haberler ve araştırmalar", size=12, color="grey")
                ], spacing=0),
                ft.Container(expand=True),
                ft.Row([
                    ft.Switch(
                        label="Sadece Okunmayanlar",
                        value=self.show_unread_only,
                        on_change=self.on_filter_changed
                    ),
                    self.refresh_progress,
                    ft.IconButton(
                        ft.Icons.REFRESH,
                        tooltip="Yenile",
                        on_click=self.refresh_news
                    ),
                    ft.IconButton(
                        ft.Icons.SETTINGS,
                        tooltip="RSS Kaynakları",
                        on_click=self.open_sources_settings
                    )
                ])
            ]),
            padding=20,
            bgcolor="white",
            border_radius=15
        )
        
        # Tabs
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Bülten",
                    icon=ft.Icons.FEED,
                    content=ft.Container(
                        content=self.news_grid,
                        padding=20
                    )
                ),
                ft.Tab(
                    text="Kaydedilenler",
                    icon=ft.Icons.BOOKMARKS,
                    content=ft.Container(
                        content=self.saved_news_list,
                        padding=20
                    )
                )
            ],
            expand=True
        )
        
        return ft.View(
            "/medical_news",
            controls=[
                ft.Container(
                    content=ft.Column([
                        header,
                        tabs
                    ], spacing=15, expand=True),
                    padding=30,
                    bgcolor="#f8f9fa",
                    expand=True
                )
            ],
            padding=0
        )
    
    def load_news(self):
        """Haberleri yükle"""
        try:
            self.news_grid.controls.clear()
            
            # Veritabanından haberleri çek
            if self.show_unread_only:
                news_items = self.db.get_unread_news(limit=20)
            else:
                news_items = self.db.get_all_news(limit=20)
            
            if not news_items:
                self.news_grid.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.NEWSPAPER, size=60, color="grey"),
                            ft.Text("Haber bulunamadı", color="grey"),
                            ft.ElevatedButton(
                                "Yenile",
                                icon=ft.Icons.REFRESH,
                                on_click=self.refresh_news
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.center,
                        expand=True
                    )
                )
            else:
                for news in news_items:
                    self.news_grid.controls.append(
                        self._news_card(news)
                    )
            
            self.news_grid.update()
            
            # Kaydedilenleri de yükle
            self.load_saved_news()
            
        except Exception as e:
            app_logger.error(f"Load news error: {e}")
    
    def _news_card(self, news):
        """Haber kartı"""
        # Tarih
        try:
            pub_date = datetime.fromisoformat(news.published_date) if isinstance(news.published_date, str) else news.published_date
            date_str = pub_date.strftime("%d.%m.%Y") if pub_date else "Tarih yok"
        except:
            date_str = "Tarih yok"
        
        # Okundu mu?
        is_read = news.is_read if hasattr(news, 'is_read') else False
        
        # Kaydedildi mi?
        is_saved = news.is_saved if hasattr(news, 'is_saved') else False
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    # Image (eğer varsa)
                    ft.Image(
                        src=news.image_url if hasattr(news, 'image_url') and news.image_url else "https://via.placeholder.com/400x200?text=Medical+News",
                        height=180,
                        width=float("inf"),
                        fit=ft.ImageFit.COVER,
                        border_radius=ft.border_radius.only(top_left=10, top_right=10)
                    ),
                    # Content
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Container(
                                    content=ft.Text(
                                        news.source,
                                        size=10,
                                        color="white",
                                        weight="bold"
                                    ),
                                    bgcolor="grey",
                                    padding=5,
                                    border_radius=5
                                ),
                                ft.Container(expand=True),
                                ft.IconButton(
                                    ft.Icons.BOOKMARK if is_saved else ft.Icons.BOOKMARK_BORDER,
                                    icon_color="teal" if is_saved else "grey",
                                    icon_size=20,
                                    tooltip="Kaydet",
                                    on_click=lambda _, nid=news.id: self.toggle_save(nid)
                                )
                            ]),
                            ft.Text(
                                news.title,
                                weight="bold",
                                size=14,
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS
                            ),
                            ft.Text(
                                date_str,
                                size=10,
                                color="grey"
                            ),
                            ft.Text(
                                news.summary,
                                size=12,
                                color="#444",
                                max_lines=3,
                                overflow=ft.TextOverflow.ELLIPSIS
                            ),
                            ft.Container(expand=True),
                            ft.ElevatedButton(
                                "Haberi Oku",
                                icon=ft.Icons.OPEN_IN_NEW,
                                on_click=lambda _, link=news.link: self.open_news(link, news.id)
                            )
                        ], spacing=8),
                        padding=15
                    )
                ], spacing=0),
                border=ft.border.all(2, "teal") if not is_read else ft.border.all(1, "#f0f0f0")
            ),
            elevation=2
        )
    
    def load_saved_news(self):
        """Kaydedilen haberleri yükle"""
        try:
            self.saved_news_list.controls.clear()
            
            saved_news = self.db.get_saved_news()
            
            if not saved_news:
                self.saved_news_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.BOOKMARKS, size=60, color="grey"),
                            ft.Text("Kaydedilen haber yok", color="grey")
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=40,
                        alignment=ft.alignment.center
                    )
                )
            else:
                for news in saved_news:
                    self.saved_news_list.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.BOOKMARK, color="teal", size=30),
                                    ft.Column([
                                        ft.Text(news.title, weight="bold", size=14),
                                        ft.Text(news.source, size=12, color="grey")
                                    ], expand=True, spacing=2),
                                    ft.IconButton(
                                        ft.Icons.OPEN_IN_NEW,
                                        tooltip="Aç",
                                        on_click=lambda _, link=news.link: self.page.launch_url(link)
                                    ),
                                    ft.IconButton(
                                        ft.Icons.DELETE,
                                        tooltip="Kaldır",
                                        icon_color="red",
                                        on_click=lambda _, nid=news.id: self.toggle_save(nid)
                                    )
                                ]),
                                padding=15
                            )
                        )
                    )
            
            self.saved_news_list.update()
            
        except Exception as e:
            app_logger.error(f"Load saved news error: {e}")
    
    def open_news(self, link, news_id):
        """Haberi aç ve okundu işaretle"""
        try:
            # Okundu olarak işaretle
            self.db.mark_news_as_read(news_id)
            
            # Tarayıcıda aç
            self.page.launch_url(link)
            
            # Listeyi yenile
            self.load_news()
            
        except Exception as e:
            app_logger.error(f"Open news error: {e}")
    
    def toggle_save(self, news_id):
        """Kaydet/Kaldır"""
        try:
            self.db.toggle_news_save(news_id)
            self.load_news()
            
        except Exception as e:
            app_logger.error(f"Toggle save error: {e}")
    
    def on_filter_changed(self, e):
        """Filtre değiştiğinde"""
        self.show_unread_only = e.control.value
        self.load_news()
    
    def refresh_news(self, e):
        """RSS'lerden yeni haberleri çek"""
        self.refresh_progress.visible = True
        self.page.update()
        
        def fetch():
            try:
                # RSS servisini kullan
                new_count = self.rss_service.fetch_all_feeds()
                
                # Haberleri yenile
                self.load_news()
                
                self.page.open(ft.SnackBar(
                    ft.Text(f"✅ {new_count} yeni haber eklendi"),
                    bgcolor="green"
                ))
                
            except Exception as ex:
                app_logger.error(f"Refresh news error: {ex}")
                self.page.open(ft.SnackBar(
                    ft.Text(f"Hata: {ex}"),
                    bgcolor="red"
                ))
            
            finally:
                self.refresh_progress.visible = False
                self.page.update()
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def open_sources_settings(self, e):
        """RSS kaynakları ayarları"""
        # TODO: RSS kaynaklarını ekleme/çıkarma dialogu
        self.page.open(ft.SnackBar(
            ft.Text("RSS kaynakları ayarları yakında eklenecek"),
            bgcolor="blue"
        ))