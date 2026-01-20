import flet as ft
import subprocess
import sys
import time
import os
from database.db_manager import DatabaseManager
from utils.notification_service import NotificationService
from utils.app_layout import AppLayout
from utils.config_manager import get_app_config
from utils.license_manager import LicenseManager
from utils.system_id import get_device_fingerprint

# --- SAYFA IMPORTLARI ---
from pages.login import LoginPage
from pages.doctor_home import DoctorHomePage
from pages.patient_list import PatientListPage
from pages.add_patient import AddPatientPage
from pages.appointments import AppointmentsPage
from pages.crm_page import CRMPage
from pages.settings import SettingsPage
from pages.patient_detail import PatientDetailPage
from pages.medical_detail import MedicalDetailPage
from pages.finance import FinancePage
from pages.inventory import InventoryPage
from pages.chat_page import ChatPage
from pages.waiting_room import WaitingRoomPage
from pages.tv_display import TVDisplayPage
from pages.ai_assistant import AIAssistantPage
from pages.medical_news import MedicalNewsPage


def start_3d_server():
    """3D Model sunucusunu başlatır - Port çakışması korumalı"""
    import socket
    
    def find_free_port(start=8000, end=8100):
        for port in range(start, end):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                continue
        return None
    
    port = find_free_port()
    if not port:
        print("⚠️  HTTP sunucu için boş port bulunamadı (8000-8100 arası dolu)")
        return
    
    try:
        if sys.platform == "win32":
            subprocess.Popen(
                [sys.executable, "-m", "http.server", str(port), "--directory", "assets"], 
                creationflags=subprocess.CREATE_NO_WINDOW, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
        else:
            subprocess.Popen(
                ["python3", "-m", "http.server", str(port), "--directory", "assets"], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
        print(f"✅ 3D sunucu başlatıldı: http://localhost:{port}")
    except Exception as e:
        print(f"⚠️  HTTP sunucu başlatılamadı: {e}")


def main(page: ft.Page):
    
    # 1. KONFİGÜRASYON (Uzaktan Yönetim)
    config = get_app_config()
    page.session.set("app_config", config)

    # Bakım Modu Kontrolü
    if config.get("maintenance_mode") == True:
        page.title = "Sistem Bakımda"
        page.window.width, page.window.height = 400, 400
        page.add(ft.Column([
            ft.Icon(ft.icons.WARNING, size=50, color="orange"),
            ft.Text("Sistem Bakımda", size=20, weight="bold"),
            ft.Text(config.get("maintenance_message", "Güncelleme yapılıyor."))
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER))
        return

    # -----------------------------------------------------------
    # 2. LİSANS KONTROLÜ
    # -----------------------------------------------------------
    lic_manager = LicenseManager()
    saved_key = ""
    if os.path.exists("license.key"):
        with open("license.key", "r") as f: 
            saved_key = f.read().strip()

    is_valid, message, limit, expiry = lic_manager.validate_license(saved_key)

    if not is_valid:
        page.title = "Lisans Aktivasyonu"
        page.window.width, page.window.height = 500, 600
        hwid = get_device_fingerprint()
        
        def activate(e):
            key = txt_key.value.strip()
            valid, msg, lim, exp = lic_manager.validate_license(key)
            if valid:
                with open("license.key", "w") as f: 
                    f.write(key)
                page.snack_bar = ft.SnackBar(
                    ft.Text("✅ Lisans Başarılı! Programı yeniden başlatın."), 
                    bgcolor="green"
                )
                page.snack_bar.open = True
                page.update()
                time.sleep(2)
                page.window.destroy()
            else:
                lbl_error.value = f"❌ Hata: {msg}"
                lbl_error.update()

        txt_key = ft.TextField(label="Lisans Anahtarı", text_align=ft.TextAlign.CENTER, width=350)
        lbl_error = ft.Text("", color="red")
        
        page.add(ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.LOCK_CLOCK, size=80, color="red"),
                ft.Text("LİSANS BULUNAMADI", size=24, weight="bold"),
                ft.Text("Cihaz ID (Bunu satıcıya iletin):", color="grey"),
                ft.Container(
                    content=ft.Text(hwid, size=16, weight="bold", selectable=True), 
                    bgcolor="#f0f0f0", 
                    padding=10, 
                    border_radius=5
                ),
                ft.Divider(),
                txt_key,
                ft.ElevatedButton("Etkinleştir", on_click=activate, bgcolor="blue", color="white"),
                lbl_error
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
            alignment=ft.alignment.center, 
            padding=40
        ))
        return

    # Lisans geçerliyse bilgileri sakla
    page.session.set("license_info", {"limit": limit, "expiry": expiry})

    # -----------------------------------------------------------
    # 3. NORMAL BAŞLANGIÇ
    # -----------------------------------------------------------
    page.title = "KRATS - Klinik OS v3.0"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#f8f9fa"
    
    db = DatabaseManager()
    
    # AppLayout oluştur (Sidebar için)
    app_layout = AppLayout(page, db)
    
    try: 
        NotificationService(db).start_daemon()
    except Exception as e:
        print(f"⚠️  Bildirim servisi başlatılamadı: {e}")

    def route_change(route):
        """Sayfa yönlendirme sistemi"""
        print(f"🔀 Rota değişti: {route}")
        
        page.views.clear()
        
        # Login kontrolü
        user_id = page.session.get("user_id")
        
        # Login sayfası - Sidebar YOK
        if route == "/login" or (route != "/login" and not user_id):
            print("📄 Login sayfası yükleniyor")
            page.views.append(LoginPage(page, db).view())
            page.update()
            return
        
        # Oturum varsa sayfa yönlendirmeleri - Sidebar VAR
        print(f"✅ Oturum aktif (User ID: {user_id}), sayfa yükleniyor: {route}")
        
        try:
            content = None
            
            if route == "/doctor_home":
                content = DoctorHomePage(page, db, "admin").view().controls[0]
            elif route == "/patient_list":
                content = PatientListPage(page, db).view().controls[0]
            elif route == "/appointments":
                content = AppointmentsPage(page, db).view().controls[0]
            elif route == "/settings":
                content = SettingsPage(page, db).view().controls[0]
            elif route == "/inventory":
                content = InventoryPage(page, db).view().controls[0]
            elif route == "/add_patient":
                content = AddPatientPage(page, db).view().controls[0]
            elif route == "/crm":
                content = CRMPage(page, db).view().controls[0]
            elif route == "/finance":
                content = FinancePage(page, db).view().controls[0]
            elif route == "/chat":
                content = ChatPage(page, db).view().controls[0]
            elif route == "/waiting_room":
                content = WaitingRoomPage(page, db).view().controls[0]
            elif route == "/tv_display":
                # TV Display tam ekran olmalı, sidebar olmadan
                page.views.append(TVDisplayPage(page, db).view())
                page.update()
                return
            elif route == "/ai_assistant":
                content = AIAssistantPage(page, db).view().controls[0]
            elif route == "/medical_news":
                content = MedicalNewsPage(page, db).view().controls[0]
            elif route.startswith("/patient_detail/"):
                patient_id = route.split("/")[-1]
                content = PatientDetailPage(page, db, int(patient_id)).view().controls[0]
            elif route.startswith("/medical_detail/"):
                record_id = route.split("/")[-1]
                content = MedicalDetailPage(page, db, int(record_id)).view().controls[0]
            else:
                # Bilinmeyen rota - ana sayfaya yönlendir
                print(f"⚠️  Bilinmeyen rota: {route}, ana sayfaya yönlendiriliyor")
                content = DoctorHomePage(page, db, "admin").view().controls[0]
            
            # Sidebar ile birlikte view oluştur
            if content:
                view = app_layout.get_view(route, content)
                page.views.append(view)
                page.update()
                print(f"✅ Sayfa yüklendi: {route}")
            else:
                print(f"❌ Content oluşturulamadı: {route}")
                
        except Exception as e:
            print(f"❌ Sayfa yükleme hatası ({route}): {e}")
            import traceback
            traceback.print_exc()
            
            # Hata durumunda login'e dön
            page.views.clear()
            page.views.append(LoginPage(page, db).view())
            page.update()

    # Route değişikliklerini dinle
    page.on_route_change = lambda e: route_change(e.route)
    
    # Geri tuşu desteği
    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)
    
    page.on_view_pop = view_pop
    
    # İlk başlatma - login'e git
    print("🚀 Uygulama başlatılıyor...")
    route_change("/login")


if __name__ == "__main__":
    start_3d_server()
    ft.app(target=main, assets_dir="assets")
