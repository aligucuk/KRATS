import flet as ft
from database.db_manager import DatabaseManager
from pages.tv_display import TVDisplayPage

def main(page: ft.Page):
    # Pencere Ayarları
    page.title = "KRATS - TV Bekleme Ekranı"
    page.window_min_width = 800
    page.window_min_height = 600
    page.window_maximized = True # Tam ekran başlasın
    page.padding = 0
    page.bgcolor = "black"
    
    # TV Ekranı kodu "/tv_display" rotasını kontrol ettiği için
    # bu pencerenin rotasını manuel olarak ayarlıyoruz.
    page.route = "/tv_display"

    # Veritabanı Bağlantısı
    db = DatabaseManager()

    # Sayfayı Başlat
    tv_page = TVDisplayPage(page, db)
    
    # Görünümü Ekle
    page.views.append(tv_page.view())
    page.update()

if __name__ == "__main__":
    ft.app(target=main)