import flet as ft
from datetime import datetime
import locale

try: locale.setlocale(locale.LC_ALL, '')
except: pass

class DoctorHomePage:
    def __init__(self, page: ft.Page, db, role):
        self.page = page
        self.db = db
        self.role = role

    def view(self):
        user_name = self.page.session.get("user_name") or "Doktor"
        todays_apps = self.db.get_todays_appointments()
        
        # Tarih
        date_str = datetime.now().strftime("%d %B %Y, %A")

        # --- 1. HERO KARTI (Renkli Karşılama) ---
        hero_card = ft.Container(
            content=ft.Column([
                ft.Text(f"Merhaba, {user_name} 👋", size=28, weight="bold", color="white"),
                ft.Text(f"Bugün {date_str}. Klinik durumu stabil.", size=14, color="white70"),
                ft.Container(height=10),
                ft.ElevatedButton("Hızlı Randevu", icon=ft.Icons.ADD, color="teal", bgcolor="white")
            ]),
            padding=30, border_radius=20,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left, end=ft.alignment.bottom_right,
                colors=["#009688", "#004D40"] # Teal Gradient
            ),
            shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.with_opacity(0.4, "teal")),
            expand=True
        )

        # --- 2. İSTATİSTİKLER (Renkli İkonlu Kartlar) ---
        def stat_card(title, value, icon, color):
            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, color=color, size=24),
                        padding=12, bgcolor=ft.Colors.with_opacity(0.1, color),
                        border_radius=12
                    ),
                    ft.Column([
                        ft.Text(value, size=20, weight="bold"),
                        ft.Text(title, size=12, color="grey")
                    ], spacing=0)
                ]),
                padding=20, bgcolor="white", border_radius=15,
                border=ft.border.all(1, "#f0f0f0"),
                shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.05, "black")),
                expand=1
            )

        stats_row = ft.Row([
            stat_card("Bugünkü Randevu", str(len(todays_apps)), ft.Icons.CALENDAR_TODAY, "blue"),
            stat_card("Bekleyen Hasta", "2", ft.Icons.TIMELAPSE, "orange"),
            stat_card("Toplam Kazanç", "₺12.500", ft.Icons.ATTACH_MONEY, "green"),
        ], spacing=20)

        # --- 3. AKIŞ (Timeline) ---
        timeline_items = []
        if not todays_apps:
            timeline_items.append(ft.Container(content=ft.Text("Bugün için kayıtlı randevu yok.", color="grey", italic=True), padding=20))
        else:
            for app in todays_apps:
                timeline_items.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(str(app[2])[-5:], weight="bold", color="teal"),
                            ft.VerticalDivider(width=10, color="grey"),
                            ft.Column([ft.Text(app[1], weight="bold"), ft.Text(app[3], size=12, color="grey")])
                        ]),
                        padding=10, border=ft.border.only(bottom=ft.BorderSide(1, "#f0f0f0"))
                    )
                )

        timeline_section = ft.Container(
            content=ft.Column([
                ft.Text("Günlük Akış", size=18, weight="bold"),
                ft.Divider(height=10, color="transparent"),
                ft.Column(timeline_items, scroll=ft.ScrollMode.AUTO)
            ]),
            padding=25, bgcolor="white", border_radius=20, expand=True,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.05, "black"))
        )

        # --- LAYOUT BİRLEŞTİRME ---
        layout = ft.Column([
            ft.Row([hero_card], height=180),
            ft.Container(height=10),
            stats_row,
            ft.Container(height=10),
            ft.Row([timeline_section], expand=True) # Burası ekranı kaplar
        ], spacing=20, expand=True)

        return ft.View(
            "/doctor_home",
            controls=[ft.Container(content=layout, padding=30)],
            padding=0, bgcolor="#f8f9fa"
        )