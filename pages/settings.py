import flet as ft
from utils.system_id import get_device_fingerprint
from utils.license_manager import LicenseManager
from utils.whatsapp_bot import WhatsAppBot
from utils.backup_manager import BackupManager
from utils.google_calendar_manager import GoogleCalendarManager

class SettingsPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.lm = LicenseManager()

        self.input_style = {
            "border_radius": 8, "filled": True, "bgcolor": ft.Colors.with_opacity(0.05, "black"),
            "border_color": "transparent", "content_padding": 15, "text_size": 14
        }

        self.dd_country = ft.Dropdown(
            label="Klinik Bölgesi", options=[
                ft.dropdown.Option("TR", "Türkiye 🇹🇷"),
                ft.dropdown.Option("US", "Amerika 🇺🇸"),
                ft.dropdown.Option("DE", "Almanya 🇩🇪"),
            ], value=self.db.get_setting("country") or "TR", expand=1, **self.input_style
        )

        self.sw_enabiz = ft.Switch(label="E-Nabız", value=self.db.is_module_active("module_enabiz"), on_change=lambda e: self.toggle_module("module_enabiz", e.control.value))
        self.sw_sms = ft.Switch(label="SMS", value=self.db.is_module_active("module_sms"), on_change=lambda e: self.toggle_module("module_sms", e.control.value))
        self.sw_chat = ft.Switch(label="Sohbet", value=self.db.is_module_active("module_chat"), on_change=lambda e: self.toggle_module("module_chat", e.control.value))
        self.sw_ai = ft.Switch(label="AI Asistan", value=self.db.is_module_active("module_ai"), on_change=lambda e: self.toggle_module("module_ai", e.control.value))

        self.txt_username = ft.TextField(label="Kullanıcı Adı", prefix_icon=ft.Icons.PERSON, expand=1, **self.input_style)
        self.txt_password = ft.TextField(label="Şifre", password=True, can_reveal_password=True, prefix_icon=ft.Icons.LOCK, expand=1, **self.input_style)
        self.txt_fullname = ft.TextField(label="Ad Soyad", prefix_icon=ft.Icons.BADGE, expand=1, **self.input_style)
        
        self.dd_role = ft.Dropdown(
            label="Rol", options=[
                ft.dropdown.Option("doktor"), ft.dropdown.Option("sekreter"), 
                ft.dropdown.Option("muhasebe"), ft.dropdown.Option("admin")
            ], value="sekreter", expand=1, **self.input_style
        )
        
        self.dd_specialty = ft.Dropdown(
            label="Branş", options=[
                ft.dropdown.Option("Genel"), ft.dropdown.Option("Dis"), 
                ft.dropdown.Option("Fizyo"), ft.dropdown.Option("Diyet"),
                ft.dropdown.Option("Psiko"), ft.dropdown.Option("Kardiyo")
            ], value="Genel", expand=1, **self.input_style
        )

        self.user_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Ad Soyad", weight="bold")),
                ft.DataColumn(ft.Text("Kullanıcı")),
                ft.DataColumn(ft.Text("Branş")),
                ft.DataColumn(ft.Text("Rol")),
            ],
            border=ft.border.all(1, "#eeeeee"), border_radius=10, 
            heading_row_color=ft.Colors.with_opacity(0.05, "teal"), width=float("inf")
        )

        self.txt_email_user = ft.TextField(label="Email", expand=1, **self.input_style)
        self.txt_email_pass = ft.TextField(label="Şifre", password=True, expand=1, **self.input_style)
        self.txt_license = ft.TextField(label="Lisans Anahtarı", expand=1, **self.input_style)
        self.license_info = ft.Text("Yükleniyor...", size=12, color="grey")

    def view(self):
        self.load_users(update_ui=False)
        self.check_license(update_ui=False)

         # 1. Lisans Bilgileri (Session'dan al)
        lic_info = self.page.session.get("license_info") or {"expiry": "Bilinmiyor", "limit": 0}
        
        lic_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.VERIFIED, color="green", size=40),
                        title=ft.Text("Lisans Aktif", weight="bold"),
                        subtitle=ft.Text(f"Bitiş: {lic_info['expiry']} | Kullanıcı: {lic_info['limit']}")
                    ),
                    ft.ElevatedButton("Lisansı Sıfırla", on_click=self.reset_license, bgcolor="red", color="white")
                ]), padding=10
            )
        )

        # 2. Araçlar (Yedekleme & Google)
        tools_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Sistem Araçları", weight="bold"),
                    ft.Divider(),
                    ft.Row([
                        ft.ElevatedButton("Veritabanını Yedekle", icon=ft.icons.BACKUP, on_click=self.backup_db),
                        ft.ElevatedButton("Google Takvim Bağla", icon=ft.icons.CALENDAR_MONTH, on_click=self.connect_google)
                    ])
                ]), padding=20
            )
        )
        
        def settings_card(title, icon, content_control):
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(icon, color="teal", size=20),
                        ft.Text(title, size=16, weight="bold", color="#333")
                    ], spacing=10),
                    ft.Divider(height=1, color="#eeeeee"),
                    ft.Container(height=10),
                    content_control
                ], spacing=5),
                padding=25, bgcolor="white", border_radius=12,
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.05, "black")),
                border=ft.border.all(1, "#f0f0f0")
            )

        general_content = ft.Column([
            ft.Row([self.dd_country, ft.Container(expand=1)]),
            ft.ElevatedButton("Kaydet", bgcolor="teal", color="white", on_click=lambda _: self.save_setting("country", self.dd_country.value)),
            ft.Container(height=10),
            ft.Text("Aktif Modüller", weight="bold", size=14),
            ft.Row([self.sw_enabiz, self.sw_sms, self.sw_chat, self.sw_ai], wrap=True, spacing=20)
        ])

        personnel_form = ft.Column([
            ft.Row([self.txt_username, self.txt_password], spacing=20),
            ft.Row([self.txt_fullname, self.dd_role, self.dd_specialty], spacing=20),
            ft.Row([
                ft.ElevatedButton("Personel Ekle", icon=ft.Icons.ADD, bgcolor="teal", color="white", on_click=self.add_user)
            ], alignment=ft.MainAxisAlignment.END)
        ], spacing=15)

        comm_content = ft.Column([
            ft.Row([self.txt_email_user, self.txt_email_pass], spacing=20),
            ft.ElevatedButton("API Kaydet", on_click=self.save_api),
            ft.Divider(),
            ft.Row([
                # HATA DÜZELTİLDİ: Icons.WHATSAPP yerine Icons.CHAT
                ft.Icon(ft.Icons.CHAT, color="green"),
                ft.Text("WhatsApp Bot Entegrasyonu", weight="bold"),
                ft.Container(expand=True),
                ft.OutlinedButton("Botu Başlat", on_click=self.run_bot)
            ])
        ], spacing=15)

        tabs = ft.Tabs(
            selected_index=0, animation_duration=300,
            indicator_color="teal", label_color="teal", unselected_label_color="grey",
            tabs=[
                ft.Tab(text="Genel", icon=ft.Icons.SETTINGS, content=ft.ListView([settings_card("Sistem Ayarları", ft.Icons.TUNE, general_content)], padding=20)),
                ft.Tab(text="Personel", icon=ft.Icons.PEOPLE, content=ft.ListView([
                    settings_card("Yeni Personel", ft.Icons.PERSON_ADD, personnel_form),
                    ft.Container(height=20),
                    settings_card("Personel Listesi", ft.Icons.LIST, self.user_table)
                ], padding=20)),
                ft.Tab(text="Bağlantılar", icon=ft.Icons.LINK, content=ft.ListView([settings_card("İletişim API", ft.Icons.API, comm_content)], padding=20)),
            ],
            expand=True
        )

        return ft.View(
            "/settings", 
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Text("Ayarlar", size=28, weight="bold", color="#1a1a1a"),
                        ft.Container(content=tabs, expand=True)
                    ], spacing=20, expand=True),
                    padding=30, expand=True
                )
            ], 
            padding=0, bgcolor="#f8f9fa"
        )

    def toggle_module(self, key, value):
        self.db.set_setting(key, "1" if value else "0")
        self.page.open(ft.SnackBar(ft.Text("Güncellendi"), bgcolor="green"))
        self.page.pubsub.send_all("refresh_menu")

    def save_setting(self, key, value):
        self.db.set_setting(key, value)
        self.page.open(ft.SnackBar(ft.Text("Kaydedildi"), bgcolor="green"))

    def load_users(self, update_ui=True):
        self.user_table.rows = []
        for u in self.db.get_all_users():
            try:
                spec = u[5] if len(u)>5 and u[5] else "Genel"
                self.user_table.rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(u[2], weight="bold")),
                    ft.DataCell(ft.Text(u[1])),
                    ft.DataCell(ft.Container(content=ft.Text(spec, size=10, color="teal"), bgcolor=ft.Colors.TEAL_50, padding=5, border_radius=5)),
                    ft.DataCell(ft.Text(str(u[3]).upper()))
                ]))
            except: pass
        if update_ui: self.user_table.update()

    def add_user(self, e):
        if not self.txt_username.value: return
        success, msg = self.db.add_user_secure(self.txt_username.value, self.txt_password.value, self.txt_fullname.value, self.dd_role.value, specialty=self.dd_specialty.value)
        self.page.open(ft.SnackBar(ft.Text(msg), bgcolor="green" if success else "red"))
        if success: self.load_users()

    def save_api(self, e):
        self.db.set_setting("api_email_user", self.txt_email_user.value)
        self.page.open(ft.SnackBar(ft.Text("Kaydedildi"), bgcolor="green"))

    def reset_license(self, e):
        if os.path.exists("license.key"):
            os.remove("license.key")
            self.page.snack_bar = ft.SnackBar(ft.Text("Lisans silindi. Program kapanıyor..."))
            self.page.snack_bar.open = True
            self.page.update()
            import time; time.sleep(2)
            self.page.window.destroy()

    def backup_db(self, e):
        bm = BackupManager()
        success, msg = bm.create_backup("krats.db") # Senin DB adın
        color = "green" if success else "red"
        self.page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color)
        self.page.snack_bar.open = True
        self.page.update()

    def connect_google(self, e):
        gm = GoogleCalendarManager()
        success, msg = gm.connect_account() # Bu fonksiyonu önceki cevapta eklemiştik
        self.page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor="green" if success else "red")
        self.page.snack_bar.open = True
        self.page.update()

    def check_license(self, update_ui=True): pass 
    def activate_license(self, e): pass
    def backup_db(self, e): pass
    def run_bot(self, e): pass