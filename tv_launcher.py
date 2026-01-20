"""
TV Bekleme Ekranı Launcher
Ayrı pencerede TV ekranını başlatır
"""
import flet as ft
from database.db_manager import DatabaseManager
from ui.pages.tv_display import TVDisplayPage
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(page: ft.Page):
    """TV penceresi main fonksiyonu"""
    
    # Pencere ayarları
    page.title = "KRATS - Bekleme Ekranı"
    page.window_min_width = 800
    page.window_min_height = 600
    page.window_maximized = True  # Tam ekran başlat
    page.padding = 0
    page.bgcolor = "black"
    
    # Route'u manuel ayarla
    page.route = "/tv_display"
    
    try:
        # Veritabanı bağlantısı
        db = DatabaseManager()
        
        # TV sayfasını başlat
        tv_page = TVDisplayPage(page, db)
        
        # Görünümü ekle
        page.views.append(tv_page.view())
        page.update()
        
        logger.info("✅ TV ekranı başlatıldı")
        
    except Exception as e:
        logger.error(f"❌ TV ekranı başlatma hatası: {e}")
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ERROR, size=80, color="red"),
                    ft.Text(
                        "TV Ekranı Başlatılamadı",
                        size=24,
                        color="red"
                    ),
                    ft.Text(str(e), size=14, color="white")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                expand=True
            )
        )


if __name__ == "__main__":
    ft.app(target=main)