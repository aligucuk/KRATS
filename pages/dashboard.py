import flet as ft

class DashboardPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        # Kullanıcı adı session'dan alınır, yoksa varsayılan atanır
        self.user_name = page.session.get("user_name") or "Kullanıcı"

    def create_card(self, title, icon, subtitle, route, color):
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Container(content=ft.Icon(icon, size=30, color=color), padding=10, bgcolor="surfaceVariant", border_radius=10),
                        ft.Container(height=10),
                        ft.Text(title, size=16, weight="bold", color="onSurface"),
                        ft.Text(subtitle, size=12, color="onSurfaceVariant"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.START
                ),
                padding=20, width=220, height=160, border_radius=15,
                on_click=lambda _: self.page.go(route)
            ),
            elevation=2, color="surface"
        )

    def view(self):
        self.db.auto_update_status() # Otomatik kontrol

        # --- TEMA & ÇIKIŞ ---
        def toggle_theme(e):
            is_dark = self.page.theme_mode == ft.ThemeMode.DARK
            self.page.theme_mode = ft.ThemeMode.LIGHT if is_dark else ft.ThemeMode.DARK
            e.control.icon = "dark_mode" if is_dark else "light_mode"
            e.control.tooltip = "Karanlık Mod" if is_dark else "Aydınlık Mod"
            self.page.update()

        def logout(e):
            self.page.session.clear()
            self.page.go("/login")

        # --- KARTLAR ---
        card_data = [
            ("Hasta Yönetimi", "people", "Listele & Ekle", "/patient_list", "blue"),
            ("Randevu Oluştur", "calendar_month", "Yeni Randevu", "/appointments", "orange"),
            ("Tüm Randevular", "history", "Geçmiş/Gelecek", "/all_appointments", "green"),
            ("Kasa & Finans", "account_balance_wallet", "Gelir/Gider", "/finance", "purple"),
            ("Ajanda", "event_note", "Aylık Görünüm", "/calendar", "teal"),
            ("Stok Takibi", "inventory", "Malzeme & Ürün", "/inventory", "amber"), # DÜZELTİLDİ: Parantez eklendi
            ("Analiz & CRM", "bar_chart", "Raporlar", "/stats", "indigo"), 
            ("Ayarlar", "settings", "Personel & Şifre", "/settings", "blue_grey")
        ]
        
        cards = [self.create_card(*c) for c in card_data]

        # --- TABLO VERİSİ (DB Manager'dan çekildi) ---
        appt_rows = []
        try:
            for name, dt, note, st, pid in self.db.get_todays_appointments(): # Değişken sayısı db fonksiyonuna uymalı
                color = "blue" if st == "Tamamlandı" else ("green" if st == "Bekliyor" else "red")
                appt_rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(name, color="onSurface")),
                    ft.DataCell(ft.Text(dt.strftime("%H:%M"), color="onSurface")),
                    ft.DataCell(ft.Text(st, weight="bold", color=color))
                ]))
        except: pass

        # --- GRAFİK VERİSİ ---
        stats = self.db.get_dashboard_stats()
        chart_sections = []
        if stats:
            for status, count in stats:
                color = {"Bekliyor": "green", "Tamamlandı": "blue"}.get(status, "red")
                chart_sections.append(ft.PieChartSection(count, color=color, title=f"{status}\n{count}", radius=100, title_style=ft.TextStyle(size=12, color="white", weight="bold")))
        
        if not chart_sections: 
            chart_sections = [ft.PieChartSection(100, color="grey", title="Veri Yok")]

        # --- SAYFA YAPISI ---
        chart_comp = ft.Container(content=ft.PieChart(sections=chart_sections, sections_space=2, center_space_radius=40, expand=True), width=300, height=300, bgcolor="surface", border_radius=15, padding=20)
        table_comp = ft.Container(content=ft.DataTable(columns=[ft.DataColumn(ft.Text("Hasta")), ft.DataColumn(ft.Text("Saat")), ft.DataColumn(ft.Text("Durum"))], rows=appt_rows, width=400), bgcolor="surface", border_radius=15, padding=20, alignment=ft.alignment.top_center)

        return ft.View("/dashboard", [
            ft.AppBar(title=ft.Text("Klinik Dashboard"), bgcolor="background", color="primary", 
                      actions=[
                          ft.IconButton("dark_mode", on_click=toggle_theme, tooltip="Tema Değiştir", icon_color="primary"),
                          ft.IconButton("logout", on_click=logout, icon_color="red")
                      ]),
            ft.Container(content=ft.Column([
                # Kartları Wrap içine alıyoruz, ekrana sığdıkça yan yana dizer
                ft.Row(cards, wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                
                ft.Container(height=30),
                ft.Row([chart_comp, table_comp], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.START, wrap=True)
            ]), padding=20, expand=True)
        ], bgcolor="background")