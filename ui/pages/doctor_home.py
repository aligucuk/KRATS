"""
Doctor Home Page - Ana Dashboard
Modern, responsive dashboard tasarımı
"""

import flet as ft
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from utils.logger import app_logger


class DoctorHomePage:
    def __init__(self, page: ft.Page, db: DatabaseManager):
        self.page = page
        self.db = db
        
        # UI Components
        self.welcome_text = ft.Text(size=28, weight="bold")
        self.date_text = ft.Text(size=14, color="grey")
        self.stats_row = ft.Row(spacing=20, wrap=True)
        self.timeline_column = ft.Column(spacing=15, scroll=ft.ScrollMode.AUTO)
        self.quick_actions = ft.Row(spacing=15, wrap=True)
        self.notifications_list = ft.Column(spacing=10)
        
    def view(self):
        """Ana görünüm"""
        user_name = self.page.session.get("user_name") or "Doktor"
        user_role = self.page.session.get("role") or "doktor"
        
        # Verileri yükle
        self.load_welcome_section(user_name)
        self.load_stats()
        self.load_timeline()
        self.load_quick_actions(user_role)
        self.load_notifications()
        
        # Hero Section (Karşılama)
        hero_section = ft.Container(
            content=ft.Column([
                self.welcome_text,
                self.date_text,
                ft.Container(height=20),
                self.quick_actions
            ]),
            padding=30,
            border_radius=20,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=["#009688", "#004D40"]
            ),
            shadow=ft.BoxShadow(
                blur_radius=15,
                color=ft.Colors.with_opacity(0.4, "teal")
            )
        )
        
        # Stats Section (İstatistikler)
        stats_section = ft.Container(
            content=ft.Column([
                ft.Text("Bugünün Özeti", size=18, weight="bold"),
                ft.Divider(height=10, color="transparent"),
                self.stats_row
            ]),
            padding=20,
            bgcolor="white",
            border_radius=15,
            border=ft.border.all(1, "#f0f0f0")
        )
        
        # Timeline Section (Günlük Akış)
        timeline_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Günlük Akış", size=18, weight="bold"),
                    ft.Container(expand=True),
                    ft.IconButton(
                        ft.Icons.REFRESH,
                        tooltip="Yenile",
                        on_click=lambda _: self.load_timeline()
                    )
                ]),
                ft.Divider(),
                ft.Container(
                    content=self.timeline_column,
                    height=400
                )
            ]),
            padding=20,
            bgcolor="white",
            border_radius=15,
            border=ft.border.all(1, "#f0f0f0"),
            expand=True
        )
        
        # Notifications Section (Bildirimler)
        notifications_section = ft.Container(
            content=ft.Column([
                ft.Text("Bildirimler", size=18, weight="bold"),
                ft.Divider(),
                ft.Container(
                    content=self.notifications_list,
                    height=400
                )
            ]),
            padding=20,
            bgcolor="white",
            border_radius=15,
            border=ft.border.all(1, "#f0f0f0"),
            width=350
        )
        
        # Layout
        main_content = ft.Column([
            hero_section,
            ft.Container(height=20),
            stats_section,
            ft.Container(height=20),
            ft.Row([
                timeline_section,
                notifications_section
            ], spacing=20, vertical_alignment=ft.CrossAxisAlignment.START)
        ], spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)
        
        return ft.View(
            "/doctor_home",
            controls=[
                ft.Container(
                    content=main_content,
                    padding=30,
                    bgcolor="#f8f9fa",
                    expand=True
                )
            ],
            padding=0
        )
    
    def load_welcome_section(self, user_name):
        """Karşılama bölümünü yükle"""
        try:
            # Günün saatine göre selamlama
            hour = datetime.now().hour
            if hour < 12:
                greeting = "Günaydın"
            elif hour < 18:
                greeting = "İyi günler"
            else:
                greeting = "İyi akşamlar"
            
            self.welcome_text.value = f"{greeting}, Dr. {user_name} 👋"
            self.welcome_text.color = "white"
            
            # Tarih
            locale_date = datetime.now().strftime("%d %B %Y, %A")
            self.date_text.value = f"Bugün {locale_date}. Klinik durumu stabil."
            self.date_text.color = "white70"
            
        except Exception as e:
            app_logger.error(f"Welcome section error: {e}")
    
    def load_stats(self):
        """İstatistik kartlarını yükle"""
        try:
            # Bugünün verileri
            today = datetime.now().date()
            today_appointments = self.db.get_appointments_by_date(today)
            waiting_count = len([a for a in today_appointments if a.status == "Bekliyor"])
            completed_count = len([a for a in today_appointments if a.status == "Tamamlandı"])
            
            # Bu ayın geliri
            month_start = datetime.now().replace(day=1)
            month_revenue = self.db.get_total_revenue(month_start, datetime.now())
            
            # Toplam hasta
            total_patients = self.db.get_patient_count()
            
            self.stats_row.controls = [
                self._stat_card(
                    "Bugünkü Randevu",
                    str(len(today_appointments)),
                    f"{waiting_count} bekliyor",
                    ft.Icons.CALENDAR_TODAY,
                    "blue",
                    "/appointments"
                ),
                self._stat_card(
                    "Tamamlanan",
                    str(completed_count),
                    "Bugün",
                    ft.Icons.CHECK_CIRCLE,
                    "green",
                    "/appointments"
                ),
                self._stat_card(
                    "Aylık Gelir",
                    f"₺{month_revenue:,.0f}",
                    "Bu ay",
                    ft.Icons.ATTACH_MONEY,
                    "purple",
                    "/finance"
                ),
                self._stat_card(
                    "Toplam Hasta",
                    str(total_patients),
                    "Kayıtlı",
                    ft.Icons.PEOPLE,
                    "orange",
                    "/patient_list"
                )
            ]
            
        except Exception as e:
            app_logger.error(f"Stats loading error: {e}")
    
    def _stat_card(self, title, value, subtitle, icon, color, route):
        """İstatistik kartı oluştur"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, color=color, size=24),
                        padding=12,
                        bgcolor=ft.Colors.with_opacity(0.1, color),
                        border_radius=12
                    ),
                    ft.Container(expand=True)
                ]),
                ft.Text(value, size=28, weight="bold"),
                ft.Text(title, size=14, color="grey"),
                ft.Text(subtitle, size=12, color=color)
            ], spacing=8),
            padding=20,
            bgcolor="white",
            border_radius=15,
            border=ft.border.all(1, "#f0f0f0"),
            shadow=ft.BoxShadow(
                blur_radius=5,
                color=ft.Colors.with_opacity(0.05, "black")
            ),
            width=220,
            on_click=lambda _, r=route: self.page.go(r),
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            ink=True
        )
    
    def load_timeline(self):
        """Günlük akışı yükle"""
        try:
            self.timeline_column.controls.clear()
            
            # Bugünkü randevular
            today = datetime.now().date()
            appointments = self.db.get_appointments_by_date(today)
            
            if not appointments:
                self.timeline_column.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.COFFEE, size=60, color="grey"),
                            ft.Text("Bugün randevu yok", color="grey", italic=True)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=40,
                        alignment=ft.alignment.center
                    )
                )
            else:
                # Randevuları saate göre sırala
                appointments.sort(key=lambda x: x.appointment_date)
                
                for app in appointments:
                    # Hasta bilgisini çek
                    patient = self.db.get_patient_by_id(app.patient_id)
                    patient_name = patient.full_name if patient else "Bilinmeyen"
                    
                    # Saat
                    time_str = app.appointment_date.strftime("%H:%M")
                    
                    # Durum rengi
                    status_colors = {
                        "Bekliyor": "orange",
                        "Tamamlandı": "green",
                        "Görüşülüyor": "blue",
                        "İptal": "red"
                    }
                    status_color = status_colors.get(app.status, "grey")
                    
                    # Timeline item
                    self.timeline_column.controls.append(
                        ft.Container(
                            content=ft.Row([
                                # Zaman ve nokta
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text(time_str, weight="bold", color="teal", size=16),
                                        ft.Container(
                                            width=12,
                                            height=12,
                                            bgcolor=status_color,
                                            border_radius=6
                                        )
                                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                                    width=60
                                ),
                                # Dikey çizgi
                                ft.VerticalDivider(width=1, color="grey"),
                                # İçerik
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text(patient_name, weight="bold", size=15),
                                        ft.Text(app.notes if app.notes else "Not yok", size=12, color="grey"),
                                        ft.Container(
                                            content=ft.Text(app.status, size=10, color="white"),
                                            bgcolor=status_color,
                                            padding=5,
                                            border_radius=5
                                        )
                                    ], spacing=3),
                                    expand=True
                                ),
                                # Aksiyon butonları
                                ft.PopupMenuButton(
                                    items=[
                                        ft.PopupMenuItem(
                                            text="Görüşmeye Başla",
                                            icon=ft.Icons.PLAY_ARROW,
                                            on_click=lambda _, aid=app.id: self.start_appointment(aid)
                                        ),
                                        ft.PopupMenuItem(
                                            text="Tamamla",
                                            icon=ft.Icons.CHECK,
                                            on_click=lambda _, aid=app.id: self.complete_appointment(aid)
                                        ),
                                        ft.PopupMenuItem(
                                            text="İptal Et",
                                            icon=ft.Icons.CANCEL,
                                            on_click=lambda _, aid=app.id: self.cancel_appointment(aid)
                                        ),
                                    ]
                                )
                            ]),
                            padding=10,
                            border=ft.border.only(bottom=ft.BorderSide(1, "#f0f0f0"))
                        )
                    )
            
            self.timeline_column.update()
            
        except Exception as e:
            app_logger.error(f"Timeline loading error: {e}")
    
    def load_quick_actions(self, user_role):
        """Hızlı aksiyonları yükle"""
        try:
            actions = []
            
            # Ortak aksiyonlar
            actions.append(
                self._quick_action_button(
                    "Yeni Randevu",
                    ft.Icons.ADD_CIRCLE,
                    "/appointments"
                )
            )
            
            actions.append(
                self._quick_action_button(
                    "Hasta Ara",
                    ft.Icons.SEARCH,
                    "/patient_list"
                )
            )
            
            # Role göre özel aksiyonlar
            if user_role in ["admin", "doktor"]:
                actions.append(
                    self._quick_action_button(
                        "Yeni Hasta",
                        ft.Icons.PERSON_ADD,
                        "/add_patient"
                    )
                )
            
            if user_role in ["admin", "muhasebe"]:
                actions.append(
                    self._quick_action_button(
                        "Finans",
                        ft.Icons.ACCOUNT_BALANCE_WALLET,
                        "/finance"
                    )
                )
            
            self.quick_actions.controls = actions
            
        except Exception as e:
            app_logger.error(f"Quick actions error: {e}")
    
    def _quick_action_button(self, text, icon, route):
        """Hızlı aksiyon butonu"""
        return ft.ElevatedButton(
            text,
            icon=icon,
            color="white",
            bgcolor=ft.Colors.with_opacity(0.2, "white"),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            on_click=lambda _: self.page.go(route)
        )
    
    def load_notifications(self):
        """Bildirimleri yükle"""
        try:
            self.notifications_list.controls.clear()
            
            notifications = []
            
            # Düşük stok uyarıları
            low_stock = self.db.get_low_stock_products()
            for product in low_stock:
                notifications.append({
                    "type": "warning",
                    "icon": ft.Icons.INVENTORY,
                    "title": "Düşük Stok",
                    "message": f"{product.name} - Kalan: {product.quantity} {product.unit}",
                    "time": "Stok Takibi"
                })
            
            # Bekleyen onaylar (varsa)
            pending_approvals = self.db.get_pending_approvals()
            if pending_approvals:
                notifications.append({
                    "type": "info",
                    "icon": ft.Icons.APPROVAL,
                    "title": "Bekleyen Onay",
                    "message": f"{len(pending_approvals)} işlem onay bekliyor",
                    "time": "Yönetim"
                })
            
            # Yarınki randevular
            tomorrow = datetime.now().date() + timedelta(days=1)
            tomorrow_apps = self.db.get_appointments_by_date(tomorrow)
            if tomorrow_apps:
                notifications.append({
                    "type": "info",
                    "icon": ft.Icons.EVENT,
                    "title": "Yarınki Randevular",
                    "message": f"{len(tomorrow_apps)} randevu var",
                    "time": "Takvim"
                })
            
            # Sistem bildirimleri
            system_notifications = self.db.get_unread_notifications(
                self.page.session.get("user_id")
            )
            for notif in system_notifications[:3]:  # Son 3 bildirim
                notifications.append({
                    "type": "success",
                    "icon": ft.Icons.NOTIFICATIONS,
                    "title": notif.title,
                    "message": notif.message,
                    "time": notif.created_at.strftime("%H:%M")
                })
            
            # Bildirimleri göster
            if not notifications:
                self.notifications_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.NOTIFICATIONS_OFF, size=60, color="grey"),
                            ft.Text("Bildirim yok", color="grey", italic=True)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=40,
                        alignment=ft.alignment.center
                    )
                )
            else:
                for notif in notifications[:5]:  # İlk 5 bildirim
                    color_map = {
                        "warning": "orange",
                        "info": "blue",
                        "success": "green",
                        "error": "red"
                    }
                    color = color_map.get(notif["type"], "grey")
                    
                    self.notifications_list.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Container(
                                    content=ft.Icon(notif["icon"], color=color, size=20),
                                    padding=10,
                                    bgcolor=ft.Colors.with_opacity(0.1, color),
                                    border_radius=10
                                ),
                                ft.Column([
                                    ft.Text(notif["title"], weight="bold", size=13),
                                    ft.Text(notif["message"], size=12, color="grey"),
                                    ft.Text(notif["time"], size=10, color="grey")
                                ], spacing=2, expand=True)
                            ]),
                            padding=10,
                            border=ft.border.all(1, "#f0f0f0"),
                            border_radius=10
                        )
                    )
            
            self.notifications_list.update()
            
        except Exception as e:
            app_logger.error(f"Notifications loading error: {e}")
    
    def start_appointment(self, appointment_id):
        """Randevuyu başlat"""
        try:
            self.db.update_appointment_status(appointment_id, "Görüşülüyor")
            self.load_timeline()
            self.page.open(ft.SnackBar(
                ft.Text("Randevu başlatıldı"),
                bgcolor="blue"
            ))
        except Exception as e:
            app_logger.error(f"Start appointment error: {e}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Hata: {e}"),
                bgcolor="red"
            ))
    
    def complete_appointment(self, appointment_id):
        """Randevuyu tamamla"""
        try:
            self.db.update_appointment_status(appointment_id, "Tamamlandı")
            self.load_timeline()
            self.load_stats()
            self.page.open(ft.SnackBar(
                ft.Text("Randevu tamamlandı"),
                bgcolor="green"
            ))
        except Exception as e:
            app_logger.error(f"Complete appointment error: {e}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Hata: {e}"),
                bgcolor="red"
            ))
    
    def cancel_appointment(self, appointment_id):
        """Randevuyu iptal et"""
        try:
            self.db.update_appointment_status(appointment_id, "İptal")
            self.load_timeline()
            self.load_stats()
            self.page.open(ft.SnackBar(
                ft.Text("Randevu iptal edildi"),
                bgcolor="orange"
            ))
        except Exception as e:
            app_logger.error(f"Cancel appointment error: {e}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Hata: {e}"),
                bgcolor="red"
            ))