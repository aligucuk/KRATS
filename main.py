"""
KRATS - Klinik Yönetim Sistemi
Ana başlangıç dosyası
Lisans kontrolü, tema, routing
"""
import flet as ft
import sys
import os
import logging
from datetime import datetime

# Proje kök dizinini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from services.license_service import LicenseService
from services.notification_service import NotificationService
from ui.app_layout import AppLayout
# Config sınıfı Settings olarak tanımlandığı için takma ad (alias) kullanıyoruz
from config import Settings as Config

# Sayfalar
from ui.pages.login import LoginPage
from ui.pages.doctor_home import DoctorHomePage
from ui.pages.patient_list import PatientListPage
from ui.pages.add_patient import AddPatientPage
from ui.pages.patient_detail import PatientDetailPage
from ui.pages.appointments import AppointmentsPage
from ui.pages.crm_page import CRMPage
from ui.pages.finance import FinancePage
from ui.pages.inventory import InventoryPage
from ui.pages.chat_page import ChatPage
from ui.pages.ai_assistant import AIAssistantPage
from ui.pages.medical_news import MedicalNewsPage
from ui.pages.settings import SettingsPage
from ui.pages.medical_detail import MedicalDetailPage
from ui.pages.tv_display import TVDisplayPage
from ui.pages.backup import BackupPage
from ui.pages.audit_logs import AuditLogsPage
from ui.pages.statistics import StatisticsPage

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('krats.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main(page: ft.Page):
    """Ana uygulama fonksiyonu"""
    
    # Sayfa başlangıç ayarları
    page.title = Config.APP_NAME
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_min_width = 1200
    page.window_min_height = 700
    
    # Tema renkleri
    page.theme = ft.Theme(
        color_scheme_seed="teal",
        use_material3=True
    )
    
    # ============================================
    # 1. LİSANS KONTROLÜ (Görsel Ekranlı)
    # ============================================
    license_service = LicenseService()
    
    # Eğer lisans geçerli değilse Lisans Ekranını göster
    if not license_service.check_license():
        show_license_screen(page, license_service)
        return

    # Lisans varsa uygulamayı başlat
    init_app(page)

def show_license_screen(page: ft.Page, license_service: LicenseService):
    """Lisans yoksa gösterilecek tam ekran form"""
    
    page.clean()
    hwid = license_service.get_hardware_id()
    
    txt_license_key = ft.TextField(
        label="Lisans Anahtarı",
        width=400,
        text_align="center",
        border_radius=10,
        prefix_icon=ft.Icons.KEY
    )
    
    lbl_error = ft.Text("", color="red", size=14)
    
    def activate_click(e):
        key = txt_license_key.value.strip()
        if not key:
            lbl_error.value = "Lütfen anahtar giriniz."
            lbl_error.update()
            return
        
        if license_service.activate_license(key):
            # Başarılı!
            page.snack_bar = ft.SnackBar(ft.Text("Lisans Aktif! Uygulama açılıyor..."), bgcolor="green")
            page.snack_bar.open = True
            page.update()
            
            # Uygulamayı başlat
            init_app(page)
        else:
            lbl_error.value = "❌ Geçersiz lisans anahtarı!"
            lbl_error.update()

    # Ekran tasarımı
    page.add(
        ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.LOCK_CLOCK, size=80, color="red"),
                ft.Text("KRATS Klinik Sistemi", size=30, weight="bold"),
                ft.Text("Bu yazılım lisanssızdır. Lütfen aktive edin.", size=16, color="grey"),
                ft.Divider(height=20, color="transparent"),
                
                ft.Container(
                    content=ft.Column([
                        ft.Text("Donanım Kimliğiniz (HWID):", weight="bold"),
                        ft.Container(
                            content=ft.Row([
                                ft.Text(hwid, size=16, font_family="monospace", weight="bold", selectable=True),
                                ft.IconButton(ft.Icons.COPY, tooltip="Kopyala", on_click=lambda _: page.set_clipboard(hwid))
                            ], alignment=ft.MainAxisAlignment.CENTER),
                            bgcolor=ft.Colors.GREY_100,
                            padding=10,
                            border_radius=5
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=10
                ),
                
                ft.Container(height=20),
                txt_license_key,
                lbl_error,
                ft.Container(height=20),
                
                ft.ElevatedButton(
                    "Lisansı Aktifleştir",
                    icon=ft.Icons.CHECK_CIRCLE,
                    bgcolor="teal",
                    color="white",
                    width=250,
                    height=50,
                    on_click=activate_click
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            expand=True
        )
    )
    page.update()

def init_app(page: ft.Page):
    """Lisans kontrolünden sonra uygulamayı başlatan fonksiyon"""
    
    # Önce sayfayı temizle
    page.clean()
    
    license_service = LicenseService()
    # Lisans bilgilerini session'a kaydet
    license_info = license_service.get_license_info()
    page.session.set("license_info", license_info)
    
    logger.info(f"✅ Lisans doğrulandı - Kullanıcı limiti: {license_info['user_limit']}")
    
    # ============================================
    # 2. VERİTABANI BAŞLAT
    # ============================================
    try:
        db = DatabaseManager()
        logger.info("✅ Veritabanı bağlantısı kuruldu")
    except Exception as e:
        logger.error(f"❌ Veritabanı hatası: {e}")
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ERROR, size=100, color="red"),
                    ft.Text(
                        "Veritabanı başlatılamadı!",
                        size=24,
                        color="red"
                    ),
                    ft.Text(str(e), size=14)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                expand=True
            )
        )
        return
    
    # ============================================
    # 3. BİLDİRİM SERVİSİNİ BAŞLAT
    # ============================================
    try:
        notification_service = NotificationService(db)
        notification_service.start() # DÜZELTME: start_daemon yerine start()
        logger.info("✅ Bildirim servisi başlatıldı")
    except Exception as e:
        logger.warning(f"⚠️ Bildirim servisi başlatılamadı: {e}")
    
    # ============================================
    # 4. ROUTING SİSTEMİ
    # ============================================
    def route_change(route):
        """Sayfa yönlendirme"""
        page.views.clear()
        
        # Login kontrolü
        if route == "/login":
            page.views.append(LoginPage(page, db).view())
            page.update()
            return
        
        # Kullanıcı girişi yapılmamışsa login'e yönlendir
        if not page.session.get("user_id"):
            page.go("/login")
            return
        
        # Kullanıcı bilgileri
        # DÜZELTME: get("role", "") yerine get("role") kullanıldı.
        user_role = page.session.get("role")
        
        # Sayfa görünümlerini oluştur
        try:
            if route == "/doctor_home":
                view = DoctorHomePage(page, db).view()
            
            elif route == "/patient_list":
                view = PatientListPage(page, db).view()
            
            elif route == "/add_patient":
                view = AddPatientPage(page, db).view()
            
            elif route.startswith("/patient_detail/"):
                patient_id = int(route.split("/")[-1])
                view = PatientDetailPage(page, db, patient_id).view()
            
            elif route.startswith("/medical_detail/"):
                patient_id = int(route.split("/")[-1])
                view = MedicalDetailPage(page, db, patient_id).view()
            
            elif route == "/appointments":
                view = AppointmentsPage(page, db).view()
            
            elif route == "/crm":
                view = CRMPage(page, db).view()
            
            elif route == "/finance":
                view = FinancePage(page, db).view()
            
            elif route == "/inventory":
                view = InventoryPage(page, db).view()
            
            elif route == "/chat":
                if db.is_module_active("module_chat"):
                    view = ChatPage(page, db).view()
                else:
                    view = _module_disabled_view(page, "Mesajlaşma")
            
            elif route == "/ai_assistant":
                if db.is_module_active("module_ai"):
                    view = AIAssistantPage(page, db).view()
                else:
                    view = _module_disabled_view(page, "AI Asistan")
            
            elif route == "/medical_news":
                if db.is_module_active("module_ai"): 
                    view = MedicalNewsPage(page, db).view()
                else:
                    view = _module_disabled_view(page, "Tıbbi Bülten")
            
            elif route == "/settings":
                view = SettingsPage(page, db).view()
            
            elif route == "/backup":
                if user_role == "admin":
                    view = BackupPage(page, db).view()
                else:
                    view = _access_denied_view(page)
            
            elif route == "/audit_logs":
                if user_role == "admin":
                    view = AuditLogsPage(page, db).view()
                else:
                    view = _access_denied_view(page)
            
            elif route == "/statistics":
                if user_role == "admin":
                    view = StatisticsPage(page, db).view()
                else:
                    view = _access_denied_view(page)
            
            else:
                page.go("/doctor_home")
                return
            
            # Layout ile sarmalama (TV ekranı hariç)
            if route != "/tv_display":
                layout = AppLayout(page, db)
                # Extract content from view (views return ft.View, but AppLayout needs controls)
                if isinstance(view, ft.View) and view.controls:
                    content = view.controls[0]  # Get first control from view
                else:
                    content = view  # Fallback if already a control
                page.views.append(layout.get_view(route, content))
            else:
                page.views.append(view)
            
            page.update()
            
        except Exception as e:
            logger.error(f"Routing hatası - {route}: {e}")
            page.views.append(_error_view(page, str(e)))
            page.update()
    
    # Route değişimlerini dinle
    page.on_route_change = lambda e: route_change(e.route)
    
    # İlk sayfa: Login
    page.go("/login")

# --- Yardımcı Görünümler ---

def _module_disabled_view(page, module_name: str):
    return ft.View(
        "/module_disabled",
        controls=[
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.BLOCK, size=100, color="orange"),
                    ft.Text(f"{module_name} Modülü Kapalı", size=24, weight="bold"),
                    ft.Text("Bu özelliği kullanmak için Ayarlar > Modüller bölümünden etkinleştirin.", size=14, color="grey"),
                    ft.Container(height=20),
                    ft.ElevatedButton("Ayarlara Git", icon=ft.Icons.SETTINGS, on_click=lambda _: page.go("/settings"))
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                expand=True
            )
        ]
    )

def _access_denied_view(page):
    return ft.View(
        "/access_denied",
        controls=[
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.LOCK, size=100, color="red"),
                    ft.Text("Erişim Engellendi", size=24, weight="bold", color="red"),
                    ft.Text("Bu sayfayı görüntüleme yetkiniz yok.", size=14),
                    ft.Container(height=20),
                    ft.ElevatedButton("Ana Sayfaya Dön", on_click=lambda _: page.go("/doctor_home"))
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                expand=True
            )
        ]
    )

def _error_view(page, error_msg: str):
    return ft.View(
        "/error",
        controls=[
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=100, color="red"),
                    ft.Text("Bir Hata Oluştu", size=24, weight="bold"),
                    ft.Text(error_msg, size=14, color="grey"),
                    ft.Container(height=20),
                    ft.ElevatedButton("Ana Sayfaya Dön", on_click=lambda _: page.go("/doctor_home"))
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                expand=True
            )
        ]
    )

if __name__ == "__main__":
    try:
        ft.app(target=main, assets_dir="assets")
    except Exception as e:
        logger.critical(f"Uygulama başlatma hatası: {e}")
        sys.exit(1)