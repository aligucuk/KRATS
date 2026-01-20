import flet as ft
from database.db_manager import DatabaseManager

class LoginPage:
    def __init__(self, page: ft.Page, db: DatabaseManager):
        self.page = page
        self.db = db
        self.page.title = "Giriş - KRATS"
        self.page.padding = 0

    def view(self):
        # --- CAM EFEKTLİ GİRİŞ KARTI ---
        login_card = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.LOCK_OUTLINE, size=40, color="white"),
                ft.Text("Tekrar Hoş Geldiniz", size=24, weight="bold", color="white"),
                ft.Container(height=20),
                
                # Inputlar (Şeffaf zeminli)
                ft.TextField(
                    label="Kullanıcı Adı", label_style=ft.TextStyle(color="white70"),
                    color="white", border_color="white54", 
                    prefix_icon=ft.Icons.PERSON, cursor_color="white",
                    border_radius=10,
                    ref=ft.Ref()
                ),
                self._password_field(),
                
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Giriş Yap", 
                    width=280, height=50,
                    style=ft.ButtonStyle(
                        bgcolor="white", color="black",
                        shape=ft.RoundedRectangleBorder(radius=10)
                    ),
                    on_click=self.login_click
                ),
                ft.Container(height=10),
                ft.TextButton("Erişilebilirlik", on_click=self.toggle_access, style=ft.ButtonStyle(color="white70"))
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            
            width=350,
            padding=40,
            border_radius=20,
            # GLASSMORPHISM (BUZLU CAM EFEKTİ)
            bgcolor=ft.Colors.with_opacity(0.15, "white"),
            blur=ft.Blur(15, 15, ft.BlurTileMode.MIRROR),
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, "white")),
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.2, "black"))
        )

        # --- ARKA PLAN (SOYUT) ---
        return ft.View(
            "/login",
            controls=[
                ft.Container(
                    content=ft.Stack([
                        # Arka plan resmi veya gradyanı
                        ft.Container(
                            gradient=ft.LinearGradient(
                                begin=ft.alignment.top_left, end=ft.alignment.bottom_right,
                                colors=["#0f2027", "#203a43", "#2c5364"] # Koyu Modern Gradyan
                            ),
                            expand=True
                        ),
                        # Giriş Kartı (Ortalanmış)
                        ft.Container(content=login_card, alignment=ft.alignment.center),
                        
                        # Alt bilgi
                        ft.Container(
                            content=ft.Text("KRATS Clinical OS v3.0", color="white24", size=12),
                            alignment=ft.alignment.bottom_center, padding=20
                        )
                    ]),
                    expand=True
                )
            ],
            padding=0
        )

    def _password_field(self):
        self.pass_input = ft.TextField(
            label="Şifre", label_style=ft.TextStyle(color="white70"),
            password=True, can_reveal_password=True,
            color="white", border_color="white54",
            prefix_icon=ft.Icons.LOCK, cursor_color="white",
            border_radius=10,
            on_submit=self.login_click
        )
        return self.pass_input

    def login_click(self, e):
        # Inputlara erişmek için sayfa kontrol listesine bakıyoruz
        # (Basitlik adına burada ref kullanmadan e.control.page ile de yapabiliriz ama
        # yukarıda self.pass_input'u kaydettik, user_input'u da bulalım)
        # Hızlı çözüm: TextField'ları init'te tanımlamak daha temiz olurdu ama 
        # görsel sadelik için view içinde tanımladık. 
        # User input'u bulmak için basit bir yol:
        
        # Not: Bu kodda user_input'u değişkene atamadım, hemen düzeltiyorum:
        # User input field'ı bulamazsa hata verir, o yüzden yukarıdaki TextField'ı self.user_input yapmalıyız.
        # Düzeltilmiş hali aşağıda:
        pass 

    # --- DÜZELTİLMİŞ VIEW METODU (Inputları self'e ata) ---
    def view(self):
        self.user_input = ft.TextField(
            label="Kullanıcı Adı", label_style=ft.TextStyle(color="white70"),
            color="white", border_color="white54", 
            prefix_icon=ft.Icons.PERSON, cursor_color="white",
            border_radius=10
        )
        self.pass_input = ft.TextField(
            label="Şifre", label_style=ft.TextStyle(color="white70"),
            password=True, can_reveal_password=True,
            color="white", border_color="white54",
            prefix_icon=ft.Icons.LOCK, cursor_color="white",
            border_radius=10,
            on_submit=self.login_click
        )
        
        login_card = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.LOCK_OUTLINE, size=40, color="white"),
                ft.Text("Klinik Oturumu", size=24, weight="bold", color="white"),
                ft.Container(height=20),
                self.user_input,
                self.pass_input,
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Oturum Aç", width=280, height=50,
                    style=ft.ButtonStyle(bgcolor="white", color="black", shape=ft.RoundedRectangleBorder(radius=10)),
                    on_click=self.login_click
                ),
                ft.Container(height=10),
                ft.TextButton("Erişilebilirlik", on_click=self.toggle_access, style=ft.ButtonStyle(color="white70"))
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=350, padding=40, border_radius=20,
            bgcolor=ft.Colors.with_opacity(0.15, "white"), blur=ft.Blur(20, 20, ft.BlurTileMode.MIRROR),
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, "white")),
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.2, "black"))
        )
        
        return ft.View("/login", controls=[
            ft.Container(content=ft.Stack([
                ft.Container(gradient=ft.LinearGradient(begin=ft.alignment.top_left, end=ft.alignment.bottom_right, colors=["#0f2027", "#203a43", "#2c5364"]), expand=True),
                ft.Container(content=login_card, alignment=ft.alignment.center),
            ]), expand=True)
        ], padding=0)

    def login_click(self, e):
        u = self.user_input.value
        p = self.pass_input.value
        user = self.db.check_login(u, p)
        if user:
            self.page.session.set("user_id", user[0])
            self.page.session.set("user_name", user[3])
            self.page.session.set("role", user[4])
            self.page.window_maximized = True
            self.page.go("/doctor_home")
        else:
            self.page.open(ft.SnackBar(ft.Text("Hatalı Giriş"), bgcolor="red"))

    def toggle_access(self, e):
        self.page.theme_mode = ft.ThemeMode.DARK if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        self.page.update()