import flet as ft
from database.db_manager import DatabaseManager

class LoginPage:
    def __init__(self, page: ft.Page, db: DatabaseManager):
        self.page = page
        self.db = db
        self.page.title = "Giriş - KRATS"
        self.page.padding = 0
        
        # Erişilebilirlik ayarları
        self.high_contrast = False
        self.large_text = False
        self.screen_reader_mode = False

    def view(self):
        # Input field'ları
        self.user_input = ft.TextField(
            label="Kullanıcı Adı",
            hint_text="admin",
            prefix_icon=ft.Icons.PERSON,
            border_radius=12,
            focused_border_color=ft.Colors.BLUE_400,
            text_size=16 if not self.large_text else 20,
            height=60 if not self.large_text else 70
        )
        
        self.pass_input = ft.TextField(
            label="Şifre",
            hint_text="••••••••",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK,
            border_radius=12,
            focused_border_color=ft.Colors.BLUE_400,
            text_size=16 if not self.large_text else 20,
            height=60 if not self.large_text else 70,
            on_submit=self.login_click
        )
        
        # Hata mesajı container
        self.error_text = ft.Text(
            "",
            color=ft.Colors.RED_400,
            size=14,
            visible=False
        )
        
        # Ana giriş kartı
        login_card = ft.Container(
            content=ft.Column([
                # Logo & Başlık
                ft.Container(
                    content=ft.Column([
                        ft.Icon(
                            ft.Icons.MEDICAL_SERVICES_ROUNDED,
                            size=60,
                            color=ft.Colors.BLUE_400
                        ),
                        ft.Text(
                            "KRATS",
                            size=32 if not self.large_text else 40,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_400
                        ),
                        ft.Text(
                            "Klinik Yönetim Sistemi",
                            size=14 if not self.large_text else 18,
                            color=ft.Colors.GREY_600
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                    margin=ft.margin.only(bottom=30)
                ),
                
                # Form
                self.user_input,
                ft.Container(height=15),
                self.pass_input,
                
                # Hata mesajı
                ft.Container(
                    content=self.error_text,
                    margin=ft.margin.only(top=10)
                ),
                
                # Giriş butonu
                ft.Container(
                    content=ft.ElevatedButton(
                        "Giriş Yap",
                        width=300,
                        height=50 if not self.large_text else 60,
                        bgcolor=ft.Colors.BLUE_400,
                        color=ft.Colors.WHITE,
                        style=ft.ButtonStyle(
                            text_style=ft.TextStyle(
                                size=16 if not self.large_text else 20,
                                weight=ft.FontWeight.BOLD
                            ),
                            shape=ft.RoundedRectangleBorder(radius=12),
                        ),
                        on_click=self.login_click
                    ),
                    margin=ft.margin.only(top=20)
                ),
                
                # Erişilebilirlik butonu
                ft.Container(
                    content=ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.ACCESSIBILITY,
                            tooltip="Erişilebilirlik Ayarları",
                            on_click=self.show_accessibility_menu,
                            icon_color=ft.Colors.GREY_600
                        ),
                        ft.Text(
                            "Erişilebilirlik",
                            size=12 if not self.large_text else 16,
                            color=ft.Colors.GREY_600
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    margin=ft.margin.only(top=10)
                ),
                
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            
            width=400,
            padding=40,
            border_radius=20,
            bgcolor=ft.Colors.WHITE if not self.high_contrast else ft.Colors.BLACK,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            ),
            border=ft.border.all(
                2 if self.high_contrast else 1,
                ft.Colors.BLUE_400 if self.high_contrast else ft.Colors.GREY_300
            )
        )
        
        # Arka plan
        background = ft.Container(
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[
                    ft.Colors.BLUE_50,
                    ft.Colors.BLUE_100,
                    ft.Colors.PURPLE_50,
                ] if not self.high_contrast else [ft.Colors.BLACK, ft.Colors.BLACK]
            ) if not self.high_contrast else None,
            bgcolor=ft.Colors.WHITE if self.high_contrast else None,
            expand=True
        )
        
        return ft.View(
            "/login",
            controls=[
                ft.Stack([
                    background,
                    # Login kartı ortalanmış
                    ft.Container(
                        content=login_card,
                        alignment=ft.alignment.center,
                        expand=True
                    ),
                    # Sürüm bilgisi
                    ft.Container(
                        content=ft.Text(
                            "KRATS v3.0 | © 2025",
                            size=12 if not self.large_text else 16,
                            color=ft.Colors.GREY_500
                        ),
                        alignment=ft.alignment.bottom_center,
                        padding=20
                    )
                ])
            ],
            padding=0
        )

    def login_click(self, e):
        """Giriş işlemi"""
        username = self.user_input.value or ""
        password = self.pass_input.value or ""
        
        # Boş alan kontrolü
        if not username or not password:
            self.show_error("Lütfen tüm alanları doldurun")
            return
        
        print(f"🔐 Giriş denemesi: {username}")
        
        # Veritabanı kontrolü
        user = self.db.check_login(username, password)
        
        if user:
            print(f"✅ Giriş başarılı! Kullanıcı: {user[3]}, Rol: {user[4]}")
            
            # Session kaydet
            self.page.session.set("user_id", user[0])
            self.page.session.set("user_name", user[3])
            self.page.session.set("role", user[4])
            
            # Yönlendir
            self.page.window.maximized = True
            self.page.go("/doctor_home")
        else:
            print("❌ Hatalı giriş!")
            self.show_error("Kullanıcı adı veya şifre hatalı")

    def show_error(self, message):
        """Hata mesajı göster"""
        self.error_text.value = f"⚠️ {message}"
        self.error_text.visible = True
        self.page.update()

    def show_accessibility_menu(self, e):
        """Erişilebilirlik menüsü"""
        def close_dialog(e):
            dialog.open = False
            self.page.update()
        
        def apply_settings(e):
            self.high_contrast = contrast_switch.value
            self.large_text = text_size_switch.value
            self.screen_reader_mode = screen_reader_switch.value
            
            # Ayarları uygula
            self.apply_accessibility_settings()
            
            close_dialog(e)
        
        # Switch'ler
        contrast_switch = ft.Switch(
            label="Yüksek Kontrast",
            value=self.high_contrast
        )
        
        text_size_switch = ft.Switch(
            label="Büyük Metin",
            value=self.large_text
        )
        
        screen_reader_switch = ft.Switch(
            label="Ekran Okuyucu Modu",
            value=self.screen_reader_mode
        )
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Erişilebilirlik Ayarları", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Görme engelliler için:", weight=ft.FontWeight.BOLD, size=14),
                    contrast_switch,
                    text_size_switch,
                    screen_reader_switch,
                    ft.Divider(),
                    ft.Text("💡 İpucu: Klavye kısayolları", size=12, italic=True),
                    ft.Text("• Tab: Sonraki alan", size=11),
                    ft.Text("• Enter: Giriş yap", size=11),
                    ft.Text("• Esc: İptal", size=11),
                ], spacing=10, tight=True),
                width=350,
                height=300
            ),
            actions=[
                ft.TextButton("İptal", on_click=close_dialog),
                ft.ElevatedButton("Uygula", on_click=apply_settings),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.open(dialog)

    def apply_accessibility_settings(self):
        """Erişilebilirlik ayarlarını uygula"""
        # Sayfayı yeniden oluştur
        self.page.views.clear()
        self.page.views.append(self.view())
        self.page.update()
        
        # Bildirim göster
        snack = ft.SnackBar(
            content=ft.Text("✅ Erişilebilirlik ayarları uygulandı"),
            bgcolor=ft.Colors.GREEN_400
        )
        self.page.open(snack)