# ui/app_layout.py

import flet as ft
from typing import Optional
from database.db_manager import DatabaseManager
from utils.logger import get_logger

logger = get_logger(__name__)


class AppLayout:
    """Main application layout with sidebar navigation"""
    
    def __init__(self, page: ft.Page, db: DatabaseManager):
        """Initialize app layout
        
        Args:
            page: Flet page instance
            db: Database manager
        """
        self.page = page
        self.db = db
        self.current_route = "/doctor_home"
        self.menu_column = ft.Column(spacing=5)
        
        # Subscribe to menu refresh events
        self.page.pubsub.subscribe(self.on_menu_refresh)
        
        logger.debug("AppLayout initialized")
    
    def on_menu_refresh(self, topic):
        """Handle menu refresh event"""
        if topic == "refresh_menu":
            try:
                if self.menu_column.page:
                    self.build_menu_items()
                    self.menu_column.update()
            except Exception as e:
                logger.error(f"Menu refresh failed: {e}")
    
    def get_view(self, route: str, content_control) -> ft.View:
        """Get main view with sidebar and content

        Args:
            route: Current route
            content_control: Content area control or ft.View

        Returns:
            Complete view with sidebar
        """
        self.current_route = route
        user_name = self.page.session.get("user_name") or "Kullanıcı"

        # If content_control is a View, extract its controls
        if isinstance(content_control, ft.View):
            # View içindeki ilk kontrolü al (genellikle ana Container)
            if content_control.controls:
                content_control = content_control.controls[0]
            else:
                content_control = ft.Container()

        # Build menu items
        self.build_menu_items()

        # Sidebar
        sidebar = ft.Container(
            content=ft.Column([
                # Logo area
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.MEDICAL_SERVICES_OUTLINED, color="teal", size=28),
                        ft.Text("KRATS", weight="bold", size=22, font_family="Segoe UI")
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.only(top=30, bottom=20),
                ),
                
                # User info
                ft.Container(
                    content=ft.Row([
                        ft.CircleAvatar(
                            content=ft.Text(user_name[:1].upper(), color="white"),
                            radius=18,
                            bgcolor="teal"
                        ),
                        ft.Column([
                            ft.Text(f"Dr. {user_name}", size=13, weight="bold"),
                            ft.Text("Çevrimiçi", size=11, color="green")
                        ], spacing=0)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    margin=ft.margin.only(bottom=30)
                ),
                
                # Scrollable menu
                ft.Container(
                    content=ft.Column(
                        [self.menu_column],
                        scroll=ft.ScrollMode.AUTO
                    ),
                    expand=True
                ),
                
                # Bottom fixed items
                ft.Divider(color="white10"),
                self._menu_item("Ayarlar", ft.Icons.SETTINGS_OUTLINED, "/settings", route),
                self._menu_item("Çıkış Yap", ft.Icons.LOGOUT, "/logout", route, is_danger=True),
                ft.Container(height=10)
            ]),
            width=260,
            bgcolor="#f8f9fa",
            border=ft.border.only(right=ft.BorderSide(1, "#eeeeee")),
            padding=10,
        )
        
        # Main content area
        main_area = ft.Container(
            content=content_control,
            expand=True,
            padding=0
        )
        
        return ft.View(
            route,
            controls=[ft.Row([sidebar, main_area], spacing=0, expand=True)],
            padding=0,
            bgcolor="white"
        )
    
    def build_menu_items(self):
        """Build dynamic menu items based on enabled modules"""
        self.menu_column.controls.clear()
        
        # Check module status
        try:
            chat_active = self.db.is_module_active("module_chat")
            ai_active = self.db.is_module_active("module_ai")
        except:
            chat_active = True
            ai_active = True
        
        # Core menu items (always visible)
        items = [
            ("Genel Bakış", ft.Icons.DASHBOARD_OUTLINED, "/doctor_home"),
            ("Hastalar", ft.Icons.PEOPLE_OUTLINE, "/patient_list"),
            ("Randevular", ft.Icons.CALENDAR_MONTH_OUTLINED, "/appointments"),
            ("CRM & Takip", ft.Icons.PIE_CHART_OUTLINE, "/crm"),
        ]
        
        # AI modules (if enabled)
        if ai_active:
            items.extend([
                ("AI Asistan", ft.Icons.AUTO_AWESOME_OUTLINED, "/ai_assistant"),
                ("Tıbbi Bülten", ft.Icons.NEWSPAPER_OUTLINED, "/medical_news"),
            ])
        
        # Other modules
        items.extend([
            ("Finans", ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED, "/finance"),
            ("Stok", ft.Icons.INVENTORY_2_OUTLINED, "/inventory"),
        ])
        
        # Chat module (if enabled)
        if chat_active:
            items.append(("Mesajlar", ft.Icons.CHAT_BUBBLE_OUTLINE, "/chat"))
        
        # HIDDEN FEATURES - NOW ACTIVATED!
        items.extend([
            ("TV Yansıt", ft.Icons.CAST, "OPEN_TV_WINDOW"),
            ("Yedekleme", ft.Icons.BACKUP, "/backup"),  # ACTIVATED
            ("Denetim Logları", ft.Icons.HISTORY, "/audit_logs"),  # ACTIVATED
            ("İstatistikler", ft.Icons.ANALYTICS, "/statistics"),  # ACTIVATED
        ])
        
        # Build menu items
        for title, icon, route in items:
            self.menu_column.controls.append(
                self._menu_item(title, icon, route, self.current_route)
            )
    
    def _menu_item(
        self, title: str, icon: str, target_route: str,
        current_route: str, is_danger: bool = False
    ) -> ft.Container:
        """Create menu item
        
        Args:
            title: Menu item title
            icon: Icon name
            target_route: Target route
            current_route: Current active route
            is_danger: Whether this is a danger action (logout)
            
        Returns:
            Menu item container
        """
        is_active = (target_route == current_route)
        
        # Colors
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
                ft.Icon(
                    icon,
                    size=22,
                    color=active_icon if is_active else normal_icon
                ),
                ft.Text(
                    title,
                    size=15,
                    color=active_text if is_active else normal_text,
                    weight="w600" if is_active else "normal"
                )
            ], spacing=15),
            padding=ft.padding.symmetric(horizontal=20, vertical=14),
            border_radius=10,
            bgcolor=active_bg if is_active else normal_bg,
            on_click=lambda _: self._navigate(target_route),
            animate=ft.Animation(150, "easeOut"),
            ink=True,
            tooltip=title
        )
    
    def _navigate(self, route: str):
        """Navigate to route
        
        Args:
            route: Target route or special action
        """
        if route == "/logout":
            # Logout
            self.page.session.clear()
            self.page.go("/login")
        
        elif route == "OPEN_TV_WINDOW":
            # Open TV display in separate window
            import sys
            import subprocess
            
            try:
                if sys.platform == "win32":
                    subprocess.Popen(
                        [sys.executable, "tv_launcher.py"],
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:
                    subprocess.Popen([sys.executable, "tv_launcher.py"])
                
                self.page.open(
                    ft.SnackBar(
                        ft.Text("TV Penceresi açıldı"),
                        bgcolor="green"
                    )
                )
            except Exception as e:
                logger.error(f"Failed to open TV window: {e}")
                self.page.open(
                    ft.SnackBar(
                        ft.Text("TV penceresi açılamadı"),
                        bgcolor="red"
                    )
                )
        
        else:
            # Normal navigation
            self.page.go(route)