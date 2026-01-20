import flet as ft

class AppLayout:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        self.menu_column = ft.Column(spacing=5)
        
        # Sayfa yenileme dinleyicisi
        self.page.pubsub.subscribe(self.on_menu_refresh)
        
        # İlk oluşturma
        self.current_route = "/doctor_home"

    def on_menu_refresh(self, topic):
        if topic == "refresh_menu":
            try:
                if self.menu_column.page:
                    self.build_menu_items()
                    self.menu_column.update()
            except: pass 

    def get_view(self, route, content_control):
        self.current_route = route
        user_name = self.page.session.get("user_name") or ""
        self.build_menu_items()

        # SIDEBAR TASARIMI
        sidebar = ft.Container(
            content=ft.Column([
                # Logo Alanı
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.MEDICAL_SERVICES_OUTLINED, color="teal", size=24),
                        ft.Text("KRATS", weight="bold", size=20, font_family="Segoe UI")
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.only(top=30, bottom=20),
                ),
                
                # Kullanıcı Bilgisi
                ft.Container(
                    content=ft.Row([
                        ft.CircleAvatar(content=ft.Text(user_name[:1].upper()), radius=16, bgcolor="teal"),
                        ft.Column([
                            ft.Text(f"Dr. {user_name}", size=12, weight="bold"),
                            ft.Text("Çevrimiçi", size=10, color="green")
                        ], spacing=0)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    margin=ft.margin.only(bottom=30)
                ),
                
                # MENÜLER (Kaydırılabilir)
                ft.Container(
                    content=ft.Column([self.menu_column], scroll=ft.ScrollMode.AUTO),
                    expand=True
                ),
                
                # Alt Sabitler
                ft.Divider(color="white10"),
                self._menu_item("Ayarlar", ft.Icons.SETTINGS_OUTLINED, "/settings", route),
                self._menu_item("Çıkış Yap", ft.Icons.LOGOUT, "/logout", route, is_danger=True),
                ft.Container(height=10)
            ]),
            width=260,
            bgcolor="#f8f9fa" if not self.is_dark else "#1a1a1a",
            border=ft.border.only(right=ft.BorderSide(1, "#eeeeee")),
            padding=10,
        )

        main_area = ft.Container(
            content=content_control, expand=True, padding=0
        )

        return ft.View(
            route,
            controls=[ft.Row([sidebar, main_area], spacing=0, expand=True)],
            padding=0, bgcolor="white"
        )

    def build_menu_items(self):
        self.menu_column.controls.clear()
        
        # Modül durumlarını kontrol et
        try: chat_active = self.db.is_module_active("module_chat")
        except: chat_active = True
        try: ai_active = self.db.is_module_active("module_ai")
        except: ai_active = True

        # TÜM MENÜ LİSTESİ (Ayrım yapmadan)
        # Buradaki sırayı istediğin gibi değiştirebilirsin
        items = [
            ("Genel Bakış", ft.Icons.DASHBOARD_OUTLINED, "/doctor_home"),
            ("Hastalar", ft.Icons.PEOPLE_OUTLINE, "/patient_list"),
            ("Randevular", ft.Icons.CALENDAR_MONTH_OUTLINED, "/appointments"),
            ("CRM & Takip", ft.Icons.PIE_CHART_OUTLINE, "/crm"),
        ]
        
        # AI Modülleri (Aktifse ekle)
        if ai_active:
            items.append(("AI Asistanı", ft.Icons.AUTO_AWESOME_OUTLINED, "/ai_assistant"))
            items.append(("Tıbbi Bülten", ft.Icons.NEWSPAPER_OUTLINED, "/medical_news"))
            
        # Diğer Modüller
        items.append(("Finans", ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED, "/finance"))
        items.append(("Stok", ft.Icons.INVENTORY_2_OUTLINED, "/inventory"))
        
        if chat_active:
            items.append(("Mesajlar", ft.Icons.CHAT_BUBBLE_OUTLINE, "/chat"))
            
        items.append(("TV Yansıt", ft.Icons.CAST, "OPEN_TV_WINDOW"))

        # Menüleri oluştur
        for item in items:
            title, icon, route = item
            self.menu_column.controls.append(self._menu_item(title, icon, route, self.current_route))

    def _menu_item(self, title, icon, target_route, current_route, is_danger=False):
        is_active = (target_route == current_route)
        
        # Renk Ayarları
        active_bg = ft.Colors.TEAL_50
        active_icon = "teal"
        active_text = "teal"
        
        normal_bg = "transparent"
        normal_icon = "grey"
        normal_text = "#444444"
        
        if is_danger:
            normal_icon = "red"
            normal_text = "red"

        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=22, color=active_icon if is_active else normal_icon),
                ft.Text(title, size=15, color=active_text if is_active else normal_text, weight="w600" if is_active else "normal")
            ], spacing=15),
            padding=ft.padding.symmetric(horizontal=20, vertical=14),
            border_radius=10,
            bgcolor=active_bg if is_active else normal_bg,
            on_click=lambda _: self._navigate(target_route),
            animate=ft.Animation(150, "easeOut"),
            ink=True,
            tooltip=title
        )

    def _navigate(self, route):
        if route == "/logout":
            self.page.session.clear()
            self.page.go("/login")
        elif route == "OPEN_TV_WINDOW":
            import sys, subprocess
            try:
                if sys.platform == "win32":
                    subprocess.Popen([sys.executable, "tv_launcher.py"], creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    subprocess.Popen([sys.executable, "tv_launcher.py"])
                self.page.open(ft.SnackBar(ft.Text("TV Penceresi açıldı"), bgcolor="green"))
            except: pass
        else:
            self.page.go(route)