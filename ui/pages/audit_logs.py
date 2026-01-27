"""
Audit Logs Page - Denetim Kayıtları Görüntüleme
GİZLİ ÖZELLİK - Sadece admin rolü erişebilir
"""

import flet as ft
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from utils.logger import app_logger


class AuditLogsPage:
    def __init__(self, page: ft.Page, db: DatabaseManager):
        self.page = page
        self.db = db
        self.current_filter = "all"
        self.date_range = 7  # Son 7 gün
        
        # UI Components
        self.logs_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ZAMAN", size=11, weight="bold")),
                ft.DataColumn(ft.Text("KULLANICI", size=11, weight="bold")),
                ft.DataColumn(ft.Text("İŞLEM", size=11, weight="bold")),
                ft.DataColumn(ft.Text("AÇIKLAMA", size=11, weight="bold")),
                ft.DataColumn(ft.Text("IP", size=11, weight="bold")),
            ],
            heading_row_color="#f8f9fa",
            width=float("inf"),
        )
        
        self.filter_chips = ft.Row(spacing=10, wrap=True)
        self.date_dropdown = ft.Dropdown(
            label="Zaman Aralığı",
            options=[
                ft.dropdown.Option("1", "Son 24 Saat"),
                ft.dropdown.Option("7", "Son 7 Gün"),
                ft.dropdown.Option("30", "Son 30 Gün"),
                ft.dropdown.Option("90", "Son 3 Ay"),
            ],
            value="7",
            width=200,
            on_change=self.on_date_change
        )
        
        self.search_field = ft.TextField(
            hint_text="Ara (kullanıcı, işlem, açıklama...)",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=10,
            on_change=self.on_search,
            expand=True
        )
        
        self.stats_cards = ft.Row(spacing=15)
        
    def view(self):
        """Ana görünüm"""
        # Yetki kontrolü
        user_role = self.page.session.get("role")
        if user_role != "admin":
            return ft.View(
                "/audit_logs",
                controls=[
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.LOCK, size=80, color="red"),
                            ft.Text("Yetkisiz Erişim", size=24, weight="bold"),
                            ft.Text("Bu sayfaya sadece yöneticiler erişebilir."),
                            ft.ElevatedButton(
                                "Geri Dön",
                                on_click=lambda _: self.page.go("/doctor_home")
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.center,
                        expand=True
                    )
                ],
                padding=20
            )
        
        self.load_filter_chips()
        self.load_stats()
        self.load_logs()
        
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.SECURITY, color="teal", size=30),
                ft.Column([
                    ft.Text("Denetim Kayıtları", size=24, weight="bold"),
                    ft.Text("Sistem aktivitelerini izleyin", size=12, color="grey")
                ], spacing=0),
                ft.Container(expand=True),
                ft.Row([
                    self.date_dropdown,
                    ft.IconButton(
                        ft.Icons.REFRESH,
                        tooltip="Yenile",
                        on_click=lambda _: self.load_logs()
                    ),
                    ft.IconButton(
                        ft.Icons.DOWNLOAD,
                        tooltip="Dışa Aktar",
                        on_click=self.export_logs
                    )
                ])
            ]),
            padding=20,
            bgcolor="white",
            border_radius=15
        )
        
        # Filters
        filters_section = ft.Container(
            content=ft.Column([
                ft.Text("Filtreler", weight="bold"),
                self.filter_chips,
                self.search_field
            ], spacing=10),
            padding=20,
            bgcolor="white",
            border_radius=15
        )
        
        # Stats
        stats_section = ft.Container(
            content=ft.Column([
                ft.Text("İstatistikler", weight="bold"),
                self.stats_cards
            ], spacing=10),
            padding=20,
            bgcolor="white",
            border_radius=15
        )
        
        # Logs Table
        table_container = ft.Container(
            content=ft.Column([
                ft.Text("Kayıt Listesi", weight="bold"),
                ft.Container(
                    content=ft.Column([self.logs_table], scroll=ft.ScrollMode.AUTO),
                    height=500
                )
            ]),
            padding=20,
            bgcolor="white",
            border_radius=15,
            expand=True
        )
        
        return ft.View(
            "/audit_logs",
            controls=[
                ft.Container(
                    content=ft.Column([
                        header,
                        stats_section,
                        filters_section,
                        table_container
                    ], spacing=15, expand=True),
                    padding=30,
                    bgcolor="#f8f9fa",
                    expand=True
                )
            ],
            padding=0
        )
    
    def load_filter_chips(self):
        """Filtre chiplerini yükle"""
        filters = [
            ("all", "Tümü", ft.Icons.LIST),
            ("login", "Giriş/Çıkış", ft.Icons.LOGIN),
            ("patient", "Hasta İşlemleri", ft.Icons.PERSON),
            ("appointment", "Randevular", ft.Icons.CALENDAR_MONTH),
            ("financial", "Finansal", ft.Icons.ATTACH_MONEY),
            ("settings", "Ayarlar", ft.Icons.SETTINGS),
            ("error", "Hatalar", ft.Icons.ERROR),
        ]
        
        self.filter_chips.controls.clear()
        for filter_id, label, icon in filters:
            is_selected = (filter_id == self.current_filter)
            self.filter_chips.controls.append(
                ft.Chip(
                    label=ft.Row([
                        ft.Icon(icon, size=16, color="white" if is_selected else "teal"),
                        ft.Text(label, color="white" if is_selected else "teal")
                    ], spacing=5),
                    bgcolor="teal" if is_selected else ft.Colors.TEAL_50,
                    on_click=lambda e, fid=filter_id: self.on_filter_click(fid)
                )
            )
    
    def load_stats(self):
        """İstatistik kartlarını yükle"""
        try:
            # Son X günün istatistikleri
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.date_range)
            
            total = self.db.get_audit_count(start_date, end_date)
            by_type = self.db.get_audit_by_type(start_date, end_date)
            errors = self.db.get_audit_errors(start_date, end_date)
            
            self.stats_cards.controls = [
                self._stat_card("Toplam İşlem", str(total), ft.Icons.ANALYTICS, "blue"),
                self._stat_card("Giriş", str(by_type.get("login", 0)), ft.Icons.LOGIN, "green"),
                self._stat_card("Hata", str(errors), ft.Icons.ERROR, "red"),
                self._stat_card("Aktif Kullanıcı", str(by_type.get("active_users", 0)), ft.Icons.PEOPLE, "orange"),
            ]
            
        except Exception as e:
            app_logger.error(f"Stats loading error: {e}")
    
    def _stat_card(self, title, value, icon, color):
        """İstatistik kartı oluştur"""
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, color=color, size=30),
                ft.Text(value, size=24, weight="bold"),
                ft.Text(title, size=12, color="grey")
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            padding=20,
            bgcolor="white",
            border_radius=10,
            border=ft.border.all(1, "#f0f0f0"),
            width=150
        )
    
    def load_logs(self):
        """Logları yükle"""
        try:
            self.logs_table.rows.clear()
            
            # Tarih aralığı hesapla
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.date_range)
            
            # Filtreye göre logları çek
            if self.current_filter == "all":
                logs = self.db.get_audit_logs(start_date, end_date)
            else:
                logs = self.db.get_audit_logs_by_type(
                    self.current_filter, 
                    start_date, 
                    end_date
                )
            
            # Arama varsa filtrele
            search_term = self.search_field.value
            if search_term:
                search_term = search_term.lower()
                logs = [
                    log for log in logs
                    if search_term in str(log).lower()
                ]
            
            # Tabloyu doldur
            for log in logs[:100]:  # Son 100 kayıt
                # log: (id, user_id, action_type, description, timestamp, ip_address)
                timestamp = log[4]
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp)
                    except:
                        pass
                
                time_str = timestamp.strftime("%d.%m.%Y %H:%M") if isinstance(timestamp, datetime) else str(timestamp)
                
                # Kullanıcı adını çek
                user_name = self.db.get_user_name(log[1]) if log[1] else "Sistem"
                
                # Renk kodlama
                action_color = self._get_action_color(log[2])
                
                self.logs_table.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(time_str, size=11)),
                        ft.DataCell(ft.Text(user_name, size=11, weight="bold")),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(log[2], size=10, color="white"),
                                bgcolor=action_color,
                                padding=5,
                                border_radius=5
                            )
                        ),
                        ft.DataCell(ft.Text(log[3][:50] + "..." if len(log[3]) > 50 else log[3], size=11)),
                        ft.DataCell(ft.Text(log[5] if log[5] else "-", size=11, font_family="monospace")),
                    ])
                )
            
            if not logs:
                self.logs_table.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text("Kayıt bulunamadı", italic=True, color="grey")),
                        ft.DataCell(ft.Text("")),  # Empty cell
                        ft.DataCell(ft.Text("")),  # Empty cell
                        ft.DataCell(ft.Text("")),  # Empty cell
                        ft.DataCell(ft.Text("")),  # Empty cell
                    ])
                )
            
            self.logs_table.update()
            
        except Exception as e:
            app_logger.error(f"Logs loading error: {e}")
            self.page.open(ft.SnackBar(ft.Text(f"Hata: {e}"), bgcolor="red"))
    
    def _get_action_color(self, action_type):
        """İşlem tipine göre renk döndür"""
        colors = {
            "login": "green",
            "logout": "grey",
            "patient": "blue",
            "appointment": "orange",
            "financial": "purple",
            "settings": "indigo",
            "error": "red",
            "delete": "red",
            "update": "blue",
            "create": "green",
        }
        return colors.get(action_type.lower(), "grey")
    
    def on_filter_click(self, filter_id):
        """Filtre tıklama"""
        self.current_filter = filter_id
        self.load_filter_chips()
        self.load_logs()
        self.filter_chips.update()
    
    def on_date_change(self, e):
        """Tarih aralığı değişimi"""
        self.date_range = int(e.control.value)
        self.load_stats()
        self.load_logs()
        self.stats_cards.update()
    
    def on_search(self, e):
        """Arama"""
        self.load_logs()
    
    def export_logs(self, e):
        """Logları dışa aktar"""
        try:
            import csv
            from datetime import datetime
            
            filename = f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            # Logları çek
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.date_range)
            logs = self.db.get_audit_logs(start_date, end_date)
            
            # CSV'ye yaz
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Tarih', 'Kullanıcı', 'İşlem', 'Açıklama', 'IP'])
                
                for log in logs:
                    user_name = self.db.get_user_name(log[1]) if log[1] else "Sistem"
                    writer.writerow([
                        log[4],  # timestamp
                        user_name,
                        log[2],  # action_type
                        log[3],  # description
                        log[5] if log[5] else "-"  # ip_address
                    ])
            
            self.page.open(ft.SnackBar(
                ft.Text(f"Dışa aktarıldı: {filename}"),
                bgcolor="green"
            ))
            
        except Exception as e:
            app_logger.error(f"Export error: {e}")
            self.page.open(ft.SnackBar(ft.Text(f"Hata: {e}"), bgcolor="red"))