import flet as ft
from database.db_manager import DatabaseManager
from utils.logger import get_logger

logger = get_logger(__name__)

class LoginPage:
    """Modern glassmorphic login page"""
    
    def __init__(self, page: ft.Page, db: DatabaseManager):
        self.page = page
        self.db = db
        self.page.title = "Giriş - KRATS"
        self.page.padding = 0
        
        # Input fields
        self.user_input = ft.TextField(
            label="Kullanıcı Adı",
            label_style=ft.TextStyle(color="white70"),
            color="white",
            border_color="white54",
            prefix_icon=ft.Icons.PERSON,
            cursor_color="white",
            border_radius=10
        )
        
        self.pass_input = ft.TextField(
            label="Şifre",
            label_style=ft.TextStyle(color="white70"),
            password=True,
            can_reveal_password=True,
            color="white",
            border_color="white54",
            prefix_icon=ft.Icons.LOCK,
            cursor_color="white",
            border_radius=10,
            on_submit=self.login_click
        )
    
    def view(self) -> ft.View:
        # Glass effect login card
        login_card = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.LOCK_OUTLINE, size=40, color="white"),
                ft.Text("Klinik Oturumu", size=24, weight="bold", color="white"),
                ft.Container(height=20),
                
                self.user_input,
                self.pass_input,
                
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Oturum Aç",
                    width=280,
                    height=50,
                    style=ft.ButtonStyle(
                        bgcolor="white",
                        color="black",
                        shape=ft.RoundedRectangleBorder(radius=10)
                    ),
                    on_click=self.login_click
                ),
                ft.Container(height=10),
                # Erişilebilirlik Butonu
                ft.TextButton(
                    "Erişilebilirlik Modu",
                    icon=ft.Icons.ACCESSIBILITY_NEW,
                    on_click=self.toggle_access,
                    style=ft.ButtonStyle(color="white70")
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            
            width=350,
            padding=40,
            border_radius=20,
            bgcolor=ft.Colors.with_opacity(0.15, "white"),
            blur=ft.Blur(20, 20, ft.BlurTileMode.MIRROR),
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, "white")),
            shadow=ft.BoxShadow(
                blur_radius=20,
                color=ft.Colors.with_opacity(0.2, "black")
            )
        )
        
        # Basitleştirilmiş Layout (Stack yerine Column/Row kullanıldı)
        return ft.View(
            "/login",
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Container(expand=True), # Üst boşluk (itici)
                            
                            # Kartı ortalamak için Row
                            ft.Row(
                                controls=[login_card],
                                alignment=ft.MainAxisAlignment.CENTER
                            ),
                            
                            ft.Container(expand=True), # Alt boşluk (itici)
                            
                            # Footer
                            ft.Text(
                                "KRATS Clinical OS v3.0",
                                color="white24",
                                size=12
                            ),
                            ft.Container(height=20) # En alt padding
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    # Arka Plan Gradient
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_left,
                        end=ft.alignment.bottom_right,
                        colors=["#0f2027", "#203a43", "#2c5364"]
                    ),
                    expand=True,
                    padding=20
                )
            ],
            padding=0
        )
    
    def login_click(self, e):
        username = self.user_input.value
        password = self.pass_input.value
        
        if not username or not password:
            self.show_error("Kullanıcı adı ve şifre gereklidir")
            return
        
        try:
            user = self.db.authenticate_user(username, password)
            
            if user:
                self.page.session.set("user_id", user.id)
                self.page.session.set("user_name", user.full_name)
                self.page.session.set("role", user.role.value)
                
                logger.info(f"User logged in: {username}")
                self.page.window.maximized = True
                self.page.go("/doctor_home")
            else:
                self.show_error("Hatalı kullanıcı adı veya şifre")
        
        except Exception as e:
            logger.error(f"Login error: {e}")
            self.show_error("Giriş sırasında bir hata oluştu")
    
    def toggle_access(self, e):
        if self.page.theme_mode == ft.ThemeMode.LIGHT:
            self.page.theme_mode = ft.ThemeMode.DARK
        else:
            self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.update()
    
    def show_error(self, message: str):
        self.page.open(
            ft.SnackBar(
                ft.Text(message),
                bgcolor="red"
            )
        )