import flet as ft

class WaitingRoomPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        # AppLayout SİLİNDİ

    def view(self):
        # Bu sayfada doktor, dışarıdaki ekrana (TV) ne yansıyacağını seçer
        # Basit bir kontrol paneli
        
        btn_call = ft.ElevatedButton("Sıradaki Hastayı Çağır", icon=ft.Icons.MEGAPHONE, bgcolor="orange", color="white", width=200, height=50)
        btn_clear = ft.ElevatedButton("Ekranı Temizle", icon=ft.Icons.CLEAR_ALL, bgcolor="grey", color="white")

        content = ft.Column([
            ft.Text("Bekleme Odası Kontrol", size=24, weight="bold", color="teal"),
            ft.Divider(),
            ft.Text("Dış ekrana sesli anons göndermek için tıklayın."),
            ft.Container(height=20),
            ft.Row([btn_call, btn_clear], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=50),
            ft.Image(src="/logo.png", width=100, height=100, color="grey") # Demo logo
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        return ft.View("/waiting_room", controls=[ft.Container(content=content, padding=20)], padding=0)