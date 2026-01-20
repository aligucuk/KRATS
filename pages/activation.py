import flet as ft
from utils.license_manager import LicenseManager
import clipboard

class ActivationPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.lm = LicenseManager(db)
        self.hwid = self.lm.get_hardware_id()

    def view(self):
        self.txt_key = ft.TextField(label="Lisans Anahtarı", width=400, text_align="center")
        
        return ft.View(
            "/activation",
            [
                ft.Container(
                    content=ft.Column([
                        ft.Icon("lock", size=80, color="red"),
                        ft.Text("LİSANS AKTİVASYONU", size=30, weight="bold", color="red"),
                        ft.Text("Bu yazılım lisanssızdır. Kullanmak için lütfen satıcı ile iletişime geçin.", color="grey"),
                        ft.Divider(),
                        ft.Text("Bilgisayar Kimliği (HWID):", weight="bold"),
                        ft.Row([
                            ft.Container(content=ft.Text(self.hwid, size=20, weight="bold", color="blue", font_family="monospace"), bgcolor="#e0e0ff", padding=10, border_radius=5),
                            ft.IconButton(icon="copy", tooltip="Kopyala", on_click=lambda _: self.copy_hwid())
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Container(height=20),
                        self.txt_key,
                        ft.ElevatedButton("AKTİVE ET", icon="vpn_key", bgcolor="green", color="white", width=200, on_click=self.activate_click),
                        ft.Container(height=20),
                        ft.Text("Destek: info@fizyomaster.com", size=12, color="grey")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    padding=50, bgcolor="white", border_radius=20, shadow=ft.BoxShadow(blur_radius=20, color="grey")
                )
            ],
            bgcolor="#333333",
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

    def copy_hwid(self):
        clipboard.copy(self.hwid)
        self.page.open(ft.SnackBar(ft.Text("Kopyalandı!"), bgcolor="green"))

    def activate_click(self, e):
        if not self.txt_key.value: return
        
        valid, msg = self.lm.activate_license(self.txt_key.value.strip())
        if valid:
            self.page.open(ft.SnackBar(ft.Text("Lisans Başarılı! Hoşgeldiniz."), bgcolor="green"))
            self.page.go("/login")
        else:
            self.page.open(ft.SnackBar(ft.Text(f"Hata: {msg}"), bgcolor="red"))