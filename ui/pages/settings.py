"""
Settings Page - Sistem Ayarları
Kullanıcı yönetimi, modül yönetimi, API ayarları, güvenlik
"""

import flet as ft
from database.db_manager import DatabaseManager
from database.models import User
from services.backup_service import BackupService
from services.google_calendar_service import GoogleCalendarService
from utils.logger import app_logger
from utils.encryption_manager import EncryptionManager
import os


class SettingsPage:
    def __init__(self, page: ft.Page, db: DatabaseManager):
        self.page = page
        self.db = db
        self.encryption = EncryptionManager()
        self.backup_service = BackupService(db)
        self.google_service = GoogleCalendarService()
        
        # UI Components
        self.users_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("AD SOYAD", weight="bold")),
                ft.DataColumn(ft.Text("KULLANICI ADI", weight="bold")),
                ft.DataColumn(ft.Text("ROL", weight="bold")),
                ft.DataColumn(ft.Text("BRANŞ", weight="bold")),
                ft.DataColumn(ft.Text("İŞLEM", weight="bold")),
            ],
            heading_row_color="#f8f9fa",
            width=float("inf")
        )
        
        # Yeni kullanıcı form
        self.txt_username = ft.TextField(label="Kullanıcı Adı *", width=200)
        self.txt_password = ft.TextField(label="Şifre *", password=True, can_reveal_password=True, width=200)
        self.txt_fullname = ft.TextField(label="Ad Soyad *", width=300)
        
        self.dd_role = ft.Dropdown(
            label="Rol *",
            options=[
                ft.dropdown.Option("admin", "Yönetici"),
                ft.dropdown.Option("doktor", "Doktor"),
                ft.dropdown.Option("sekreter", "Sekreter"),
                ft.dropdown.Option("muhasebe", "Muhasebe")
            ],
            value="sekreter",
            width=200
        )
        
        self.dd_specialty = ft.Dropdown(
            label="Branş",
            options=[
                ft.dropdown.Option("Genel"),
                ft.dropdown.Option("Diş"),
                ft.dropdown.Option("Fizyo"),
                ft.dropdown.Option("Diyet"),
                ft.dropdown.Option("Psiko"),
                ft.dropdown.Option("Kardio")
            ],
            value="Genel",
            width=200
        )
        
        # Modül switchleri
        self.sw_enabiz = ft.Switch(label="E-Nabız Entegrasyonu", active_color="teal")
        self.sw_sms = ft.Switch(label="SMS Bildirimleri", active_color="teal")
        self.sw_chat = ft.Switch(label="İç Mesajlaşma", active_color="teal")
        self.sw_ai = ft.Switch(label="AI Asistan", active_color="teal")
        
        # API alanları
        self.txt_email_user = ft.TextField(label="Email (SMTP)", width=300)
        self.txt_email_pass = ft.TextField(label="Email Şifresi", password=True, can_reveal_password=True, width=300)
        
    def view(self):
        """Ana görünüm"""
        self.load_users()
        self.load_module_settings()
        self.load_api_settings()
        
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.SETTINGS, color="teal", size=30),
                ft.Column([
                    ft.Text("Sistem Ayarları", size=24, weight="bold"),
                    ft.Text("Kullanıcılar, modüller ve entegrasyonlar", size=12, color="grey")
                ], spacing=0)
            ]),
            padding=20,
            bgcolor="white",
            border_radius=15
        )
        
        # Tabs
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Genel",
                    icon=ft.Icons.TUNE,
                    content=self._general_tab()
                ),
                ft.Tab(
                    text="Personel",
                    icon=ft.Icons.PEOPLE,
                    content=self._personnel_tab()
                ),
                ft.Tab(
                    text="Modüller",
                    icon=ft.Icons.EXTENSION,
                    content=self._modules_tab()
                ),
                ft.Tab(
                    text="Bağlantılar",
                    icon=ft.Icons.LINK,
                    content=self._connections_tab()
                ),
                ft.Tab(
                    text="Güvenlik",
                    icon=ft.Icons.SECURITY,
                    content=self._security_tab()
                )
            ],
            expand=True
        )
        
        return ft.View(
            "/settings",
            controls=[
                ft.Container(
                    content=ft.Column([
                        header,
                        tabs
                    ], spacing=15, expand=True),
                    padding=30,
                    bgcolor="#f8f9fa",
                    expand=True
                )
            ],
            padding=0
        )
    
    def _general_tab(self):
        """Genel ayarlar sekmesi"""
        return ft.Container(
            content=ft.Column([
                self._settings_section(
                    "Klinik Bilgileri",
                    ft.Icons.BUSINESS,
                    ft.Column([
                        ft.TextField(
                            label="Klinik Adı",
                            value=self.db.get_setting("clinic_name") or "",
                            on_blur=lambda e: self.save_setting("clinic_name", e.control.value)
                        ),
                        ft.TextField(
                            label="Telefon",
                            value=self.db.get_setting("clinic_phone") or "",
                            on_blur=lambda e: self.save_setting("clinic_phone", e.control.value)
                        ),
                        ft.TextField(
                            label="Adres",
                            multiline=True,
                            min_lines=2,
                            value=self.db.get_setting("clinic_address") or "",
                            on_blur=lambda e: self.save_setting("clinic_address", e.control.value)
                        )
                    ])
                ),
                self._settings_section(
                    "Bölge Ayarları",
                    ft.Icons.PUBLIC,
                    ft.Dropdown(
                        label="Ülke",
                        options=[
                            ft.dropdown.Option("TR", "Türkiye 🇹🇷"),
                            ft.dropdown.Option("US", "Amerika 🇺🇸"),
                            ft.dropdown.Option("DE", "Almanya 🇩🇪"),
                            ft.dropdown.Option("UK", "İngiltere 🇬🇧")
                        ],
                        value=self.db.get_setting("country") or "TR",
                        on_change=lambda e: self.save_setting("country", e.control.value)
                    )
                )
            ], spacing=20, scroll=ft.ScrollMode.AUTO),
            padding=20
        )
    
    def _personnel_tab(self):
        """Personel sekmesi"""
        return ft.Container(
            content=ft.Column([
                self._settings_section(
                    "Yeni Personel Ekle",
                    ft.Icons.PERSON_ADD,
                    ft.Column([
                        ft.Row([
                            self.txt_username,
                            self.txt_password,
                            self.txt_fullname
                        ], spacing=20, wrap=True),
                        ft.Row([
                            self.dd_role,
                            self.dd_specialty
                        ], spacing=20),
                        ft.Row([
                            ft.ElevatedButton(
                                "Personel Ekle",
                                icon=ft.Icons.ADD,
                                bgcolor="teal",
                                color="white",
                                on_click=self.add_user
                            )
                        ], alignment=ft.MainAxisAlignment.END)
                    ], spacing=15)
                ),
                self._settings_section(
                    "Personel Listesi",
                    ft.Icons.LIST,
                    ft.Container(
                        content=ft.Column([self.users_table], scroll=ft.ScrollMode.AUTO),
                        height=400
                    )
                )
            ], spacing=20, scroll=ft.ScrollMode.AUTO),
            padding=20
        )
    
    def _modules_tab(self):
        """Modüller sekmesi"""
        return ft.Container(
            content=ft.Column([
                self._settings_section(
                    "Aktif Modüller",
                    ft.Icons.EXTENSION,
                    ft.Column([
                        ft.Text(
                            "Kullanmak istediğiniz özellikleri aktifleştirin",
                            size=12,
                            color="grey"
                        ),
                        ft.Divider(),
                        self.sw_enabiz,
                        ft.Text(
                            "Sağlık Bakanlığı e-Nabız sistemi ile entegrasyon",
                            size=11,
                            color="grey"
                        ),
                        ft.Divider(),
                        self.sw_sms,
                        ft.Text(
                            "Hastalara otomatik SMS hatırlatma gönder",
                            size=11,
                            color="grey"
                        ),
                        ft.Divider(),
                        self.sw_chat,
                        ft.Text(
                            "Personel arası mesajlaşma sistemi",
                            size=11,
                            color="grey"
                        ),
                        ft.Divider(),
                        self.sw_ai,
                        ft.Text(
                            "AI destekli tıbbi asistan ve haberler",
                            size=11,
                            color="grey"
                        ),
                        ft.Container(height=20),
                        ft.ElevatedButton(
                            "Kaydet",
                            icon=ft.Icons.SAVE,
                            bgcolor="teal",
                            color="white",
                            on_click=self.save_module_settings
                        )
                    ])
                )
            ], spacing=20, scroll=ft.ScrollMode.AUTO),
            padding=20
        )
    
    def _connections_tab(self):
        """Bağlantılar sekmesi"""
        return ft.Container(
            content=ft.Column([
                self._settings_section(
                    "Email (SMTP) Ayarları",
                    ft.Icons.EMAIL,
                    ft.Column([
                        ft.Row([
                            self.txt_email_user,
                            self.txt_email_pass
                        ], spacing=20, wrap=True),
                        ft.Text(
                            "Bildirimler için kullanılacak email hesabı",
                            size=11,
                            color="grey"
                        ),
                        ft.ElevatedButton(
                            "SMTP Ayarlarını Kaydet",
                            icon=ft.Icons.SAVE,
                            on_click=self.save_api_settings
                        )
                    ])
                ),
                self._settings_section(
                    "Google Takvim Entegrasyonu",
                    ft.Icons.CALENDAR_MONTH,
                    ft.Column([
                        ft.Text(
                            "Randevularınızı Google Takvim ile senkronize edin",
                            size=12
                        ),
                        ft.ElevatedButton(
                            "Google Hesabı Bağla",
                            icon=ft.Icons.LINK,
                            bgcolor="blue",
                            color="white",
                            on_click=self.connect_google_calendar
                        )
                    ])
                ),
                self._settings_section(
                    "E-Nabız Ayarları",
                    ft.Icons.MEDICAL_SERVICES,
                    ft.Column([
                        ft.TextField(
                            label="USS Kullanıcı Adı",
                            value=self.db.get_setting("uss_username") or "",
                            on_blur=lambda e: self.save_setting("uss_username", e.control.value)
                        ),
                        ft.TextField(
                            label="USS Şifresi",
                            password=True,
                            can_reveal_password=True,
                            on_blur=lambda e: self.save_encrypted_setting("uss_password", e.control.value)
                        ),
                        ft.TextField(
                            label="Kurum Kodu",
                            value=self.db.get_setting("uss_firm_code") or "",
                            on_blur=lambda e: self.save_setting("uss_firm_code", e.control.value)
                        )
                    ])
                )
            ], spacing=20, scroll=ft.ScrollMode.AUTO),
            padding=20
        )
    
    def _security_tab(self):
        """Güvenlik sekmesi"""
        return ft.Container(
            content=ft.Column([
                self._settings_section(
                    "Yedekleme",
                    ft.Icons.BACKUP,
                    ft.Column([
                        ft.Text(
                            "Veritabanınızı düzenli olarak yedekleyin",
                            size=12
                        ),
                        ft.ElevatedButton(
                            "Şimdi Yedekle",
                            icon=ft.Icons.SAVE,
                            bgcolor="blue",
                            color="white",
                            on_click=self.create_backup
                        )
                    ])
                ),
                self._settings_section(
                    "Denetim Logları",
                    ft.Icons.HISTORY,
                    ft.Column([
                        ft.Text(
                            "Sistem aktivitelerini izleyin",
                            size=12
                        ),
                        ft.ElevatedButton(
                            "Logları Görüntüle",
                            icon=ft.Icons.VISIBILITY,
                            on_click=lambda _: self.page.go("/audit_logs")
                        )
                    ])
                ),
                self._settings_section(
                    "Lisans Bilgileri",
                    ft.Icons.VERIFIED,
                    ft.Column([
                        ft.Text(
                            f"Lisans Durumu: {self._get_license_status()}",
                            weight="bold"
                        ),
                        ft.Text(
                            f"Bitiş: {self._get_license_expiry()}",
                            size=12,
                            color="grey"
                        ),
                        ft.OutlinedButton(
                            "Lisansı Sıfırla",
                            icon=ft.Icons.REFRESH,
                            on_click=self.reset_license
                        )
                    ])
                )
            ], spacing=20, scroll=ft.ScrollMode.AUTO),
            padding=20
        )
    
    def _settings_section(self, title, icon, content):
        """Ayarlar bölümü helper"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, color="teal", size=20),
                    ft.Text(title, size=16, weight="bold")
                ], spacing=10),
                ft.Divider(),
                content
            ]),
            padding=20,
            bgcolor="white",
            border_radius=15,
            border=ft.border.all(1, "#f0f0f0")
        )
    
    def load_users(self):
        """Kullanıcıları yükle"""
        try:
            self.users_table.rows.clear()
            
            users = self.db.get_all_users()
            
            for user in users:
                specialty = user.specialty if hasattr(user, 'specialty') else "Genel"
                
                self.users_table.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(user.full_name, weight="bold")),
                        ft.DataCell(ft.Text(user.username)),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(user.role.upper(), size=10, color="white"),
                                bgcolor="teal",
                                padding=5,
                                border_radius=5
                            )
                        ),
                        ft.DataCell(ft.Text(specialty)),
                        ft.DataCell(
                            ft.IconButton(
                                ft.Icons.DELETE,
                                icon_color="red",
                                tooltip="Sil",
                                on_click=lambda _, uid=user.id: self.delete_user(uid)
                            )
                        )
                    ])
                )
            
            self.users_table.update()
            
        except Exception as e:
            app_logger.error(f"Load users error: {e}")
    
    def load_module_settings(self):
        """Modül ayarlarını yükle"""
        try:
            self.sw_enabiz.value = self.db.is_module_active("module_enabiz")
            self.sw_sms.value = self.db.is_module_active("module_sms")
            self.sw_chat.value = self.db.is_module_active("module_chat")
            self.sw_ai.value = self.db.is_module_active("module_ai")
            
        except Exception as e:
            app_logger.error(f"Load module settings error: {e}")
    
    def load_api_settings(self):
        """API ayarlarını yükle"""
        try:
            self.txt_email_user.value = self.db.get_setting("api_email_user") or ""
            # Şifre gösterilmez, sadece kayıt
            
        except Exception as e:
            app_logger.error(f"Load API settings error: {e}")
    
    def add_user(self, e):
        """Kullanıcı ekle"""
        try:
            # Validasyon
            if not self.txt_username.value or not self.txt_password.value or not self.txt_fullname.value:
                self.page.open(ft.SnackBar(
                    ft.Text("Lütfen tüm zorunlu alanları doldurun"),
                    bgcolor="red"
                ))
                return
            
            # User objesi oluştur
            user = User(
                id=None,
                username=self.txt_username.value,
                password=self.txt_password.value,  # DB'de hash'lenecek
                full_name=self.txt_fullname.value,
                role=self.dd_role.value,
                commission_rate=0,
                specialty=self.dd_specialty.value
            )
            
            # Kaydet
            success, message = self.db.add_user_secure(user)
            
            if success:
                # Form temizle
                self.txt_username.value = ""
                self.txt_password.value = ""
                self.txt_fullname.value = ""
                
                # Listeyi yenile
                self.load_users()
                
                self.page.open(ft.SnackBar(
                    ft.Text("✅ Kullanıcı eklendi"),
                    bgcolor="green"
                ))
            else:
                self.page.open(ft.SnackBar(
                    ft.Text(f"❌ {message}"),
                    bgcolor="red"
                ))
            
            self.page.update()
            
        except Exception as ex:
            app_logger.error(f"Add user error: {ex}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Hata: {ex}"),
                bgcolor="red"
            ))
    
    def delete_user(self, user_id):
        """Kullanıcı sil"""
        def confirm_delete(e):
            try:
                self.db.delete_user(user_id)
                
                self.page.close(dialog)
                self.load_users()
                
                self.page.open(ft.SnackBar(
                    ft.Text("Kullanıcı silindi"),
                    bgcolor="green"
                ))
                
            except Exception as ex:
                app_logger.error(f"Delete user error: {ex}")
                self.page.open(ft.SnackBar(
                    ft.Text(f"Silme hatası: {ex}"),
                    bgcolor="red"
                ))
        
        dialog = ft.AlertDialog(
            title=ft.Text("Kullanıcıyı Sil"),
            content=ft.Text("Bu kullanıcıyı silmek istediğinizden emin misiniz?"),
            actions=[
                ft.TextButton("İptal", on_click=lambda _: self.page.close(dialog)),
                ft.ElevatedButton(
                    "Sil",
                    bgcolor="red",
                    color="white",
                    on_click=confirm_delete
                )
            ]
        )
        
        self.page.open(dialog)
    
    def save_setting(self, key, value):
        """Ayar kaydet"""
        try:
            self.db.set_setting(key, value)
            app_logger.info(f"Setting saved: {key}")
            
        except Exception as e:
            app_logger.error(f"Save setting error: {e}")
    
    def save_encrypted_setting(self, key, value):
        """Şifreli ayar kaydet"""
        try:
            if value:
                encrypted = self.encryption.encrypt(value)
                self.db.set_setting(key, encrypted)
                app_logger.info(f"Encrypted setting saved: {key}")
            
        except Exception as e:
            app_logger.error(f"Save encrypted setting error: {e}")
    
    def save_module_settings(self, e):
        """Modül ayarlarını kaydet"""
        try:
            self.db.set_setting("module_enabiz", "1" if self.sw_enabiz.value else "0")
            self.db.set_setting("module_sms", "1" if self.sw_sms.value else "0")
            self.db.set_setting("module_chat", "1" if self.sw_chat.value else "0")
            self.db.set_setting("module_ai", "1" if self.sw_ai.value else "0")
            
            self.page.open(ft.SnackBar(
                ft.Text("✅ Modül ayarları kaydedildi"),
                bgcolor="green"
            ))
            
            # Menüyü yenile
            self.page.pubsub.send_all("refresh_menu")
            
        except Exception as ex:
            app_logger.error(f"Save module settings error: {ex}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Kayıt hatası: {ex}"),
                bgcolor="red"
            ))
    
    def save_api_settings(self, e):
        """API ayarlarını kaydet"""
        try:
            self.db.set_setting("api_email_user", self.txt_email_user.value)
            
            if self.txt_email_pass.value:
                encrypted = self.encryption.encrypt(self.txt_email_pass.value)
                self.db.set_setting("api_email_pass", encrypted)
            
            self.page.open(ft.SnackBar(
                ft.Text("✅ Email ayarları kaydedildi"),
                bgcolor="green"
            ))
            
        except Exception as ex:
            app_logger.error(f"Save API settings error: {ex}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Kayıt hatası: {ex}"),
                bgcolor="red"
            ))
    
    def connect_google_calendar(self, e):
        """Google Calendar bağla"""
        try:
            success, message = self.google_service.connect_account()
            
            color = "green" if success else "red"
            self.page.open(ft.SnackBar(
                ft.Text(message),
                bgcolor=color
            ))
            
        except Exception as ex:
            app_logger.error(f"Google Calendar connection error: {ex}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Bağlantı hatası: {ex}"),
                bgcolor="red"
            ))
    
    def create_backup(self, e):
        """Yedek oluştur"""
        try:
            filename = self.backup_service.create_backup()
            
            self.page.open(ft.SnackBar(
                ft.Text(f"✅ Yedek oluşturuldu: {filename}"),
                bgcolor="green"
            ))
            
        except Exception as ex:
            app_logger.error(f"Backup error: {ex}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Yedekleme hatası: {ex}"),
                bgcolor="red"
            ))
    
    def reset_license(self, e):
        """Lisansı sıfırla"""
        def confirm_reset(e):
            try:
                if os.path.exists("license.key"):
                    os.remove("license.key")
                
                self.page.close(dialog)
                
                self.page.open(ft.SnackBar(
                    ft.Text("Lisans silindi. Program yeniden başlatılıyor..."),
                    bgcolor="orange"
                ))
                
                # Programı kapat
                import time
                time.sleep(2)
                self.page.window.destroy()
                
            except Exception as ex:
                app_logger.error(f"Reset license error: {ex}")
                self.page.open(ft.SnackBar(
                    ft.Text(f"Hata: {ex}"),
                    bgcolor="red"
                ))
        
        dialog = ft.AlertDialog(
            title=ft.Text("Lisansı Sıfırla", color="red"),
            content=ft.Text(
                "Bu işlem lisansınızı silecek ve program kapanacak.\n"
                "Tekrar açmak için yeni lisans girmeniz gerekecek.\n\n"
                "Devam etmek istiyor musunuz?"
            ),
            actions=[
                ft.TextButton("İptal", on_click=lambda _: self.page.close(dialog)),
                ft.ElevatedButton(
                    "Sıfırla",
                    bgcolor="red",
                    color="white",
                    on_click=confirm_reset
                )
            ]
        )
        
        self.page.open(dialog)
    
    def _get_license_status(self):
        """Lisans durumu"""
        license_info = self.page.session.get("license_info")
        if license_info:
            return "Aktif ✓"
        return "Bilinmiyor"
    
    def _get_license_expiry(self):
        """Lisans bitiş tarihi"""
        license_info = self.page.session.get("license_info")
        if license_info:
            return license_info.get("expiry", "-")
        return "-"