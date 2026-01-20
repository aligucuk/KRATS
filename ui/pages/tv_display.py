"""
TV Bekleme Odası Ekranı
Hastaları sırayla gösterir
Otomatik güncellenir
"""
import flet as ft
import threading
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TVDisplayPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.is_running = True
        
        # UI Components
        self.current_patient_display = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        )
        
        self.waiting_list_display = ft.Column(spacing=15)
        
        self.lbl_time = ft.Text(
            size=50,
            weight="bold",
            color="white"
        )
        
        self.lbl_date = ft.Text(
            size=18,
            color="white70"
        )

    def view(self):
        """TV ekranı görünümü"""
        self.page.title = "KRATS - Bekleme Ekranı"
        
        # Sol Panel - Aktif Hasta
        left_panel = ft.Container(
            content=ft.Column([
                ft.Container(height=50),
                ft.Text(
                    "ŞU AN GÖRÜŞÜLENg",
                    size=28,
                    weight="w300",
                    color="white70",
                    text_align="center"
                ),
                ft.Container(height=40),
                self.current_patient_display,
                ft.Container(expand=True),
                ft.Divider(color="white24", height=2),
                ft.Container(height=20),
                ft.Row([
                    ft.Icon(ft.Icons.ACCESS_TIME, size=40, color="teal"),
                    ft.Container(width=15),
                    ft.Column([
                        self.lbl_time,
                        self.lbl_date
                    ], spacing=5)
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=6,
            bgcolor="#0f172a",  # Koyu lacivert
            padding=50
        )
        
        # Sağ Panel - Bekleyenler
        right_panel = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text(
                        "SIRADAKİ HASTALAR",
                        size=22,
                        weight="bold",
                        color="white",
                        text_align="center"
                    ),
                    bgcolor="teal",
                    padding=20,
                    border_radius=12,
                    alignment=ft.alignment.center
                ),
                ft.Container(height=30),
                self.waiting_list_display
            ]),
            expand=4,
            bgcolor="#f1f5f9",  # Açık gri
            padding=30
        )
        
        # Update thread'ini başlat
        if not any(t.name == "TVUpdateLoop" for t in threading.enumerate()):
            update_thread = threading.Thread(
                target=self._update_loop,
                name="TVUpdateLoop",
                daemon=True
            )
            update_thread.start()
        
        return ft.View(
            "/tv_display",
            controls=[
                ft.Row(
                    [left_panel, right_panel],
                    expand=True,
                    spacing=0
                )
            ],
            padding=0
        )

    def _update_loop(self):
        """Otomatik güncelleme döngüsü"""
        while self.is_running:
            try:
                # Route kontrolü
                if self.page.route != "/tv_display":
                    break
                
                # Zaman güncelle
                now = datetime.now()
                self.lbl_time.value = now.strftime("%H:%M")
                self.lbl_date.value = now.strftime("%d %B %Y, %A")
                
                # Randevuları getir
                appointments = self.db.get_todays_appointments()
                
                current_patient = None
                waiting_patients = []
                
                if appointments:
                    # Aktif hastayı bul
                    for app in appointments:
                        if app[3] == "Görüşülüyor":
                            current_patient = app
                            break
                    
                    # Aktif hasta yoksa bekleyen ilk hastayı al
                    if not current_patient:
                        for app in appointments:
                            if app[3] == "Bekliyor":
                                current_patient = app
                                break
                    
                    # Bekleyen hastaları listele
                    for app in appointments:
                        if app[3] == "Bekliyor":
                            if not current_patient or app[0] != current_patient[0]:
                                waiting_patients.append(app)
                
                # UI'ı güncelle
                self._update_current_patient(current_patient)
                self._update_waiting_list(waiting_patients)
                
                self.page.update()
                
            except Exception as e:
                logger.error(f"TV güncelleme hatası: {e}")
            
            # 5 saniye bekle
            time.sleep(5)

    def _update_current_patient(self, patient):
        """Aktif hasta gösterimini güncelle"""
        self.current_patient_display.controls.clear()
        
        if patient:
            # patient: (id, name, date, status, notes)
            patient_name = str(patient[1])
            
            # Avatar
            avatar = ft.Container(
                content=ft.Text(
                    patient_name[0].upper(),
                    size=80,
                    weight="bold",
                    color="white"
                ),
                bgcolor="teal",
                width=160,
                height=160,
                border_radius=80,
                alignment=ft.alignment.center,
                shadow=ft.BoxShadow(
                    blur_radius=30,
                    color=ft.Colors.with_opacity(0.5, "teal")
                )
            )
            
            # İsim
            name_display = ft.Text(
                patient_name,
                size=60,
                weight="bold",
                color="white",
                text_align="center"
            )
            
            # Mesaj
            message = ft.Text(
                "Lütfen Muayene Odasına Giriniz",
                size=28,
                color="teal",
                weight="w300",
                text_align="center"
            )
            
            self.current_patient_display.controls = [
                avatar,
                ft.Container(height=30),
                name_display,
                ft.Container(height=10),
                message
            ]
        else:
            # Boş durum
            self.current_patient_display.controls = [
                ft.Icon(
                    ft.Icons.HOTEL,
                    size=120,
                    color="white24"
                ),
                ft.Container(height=30),
                ft.Text(
                    "Bekleyen Hasta Yok",
                    size=32,
                    color="white24",
                    text_align="center"
                )
            ]

    def _update_waiting_list(self, patients):
        """Bekleyen hasta listesini güncelle"""
        self.waiting_list_display.controls.clear()
        
        if not patients:
            self.waiting_list_display.controls.append(
                ft.Container(
                    content=ft.Text(
                        "Sırada hasta yok",
                        size=18,
                        color="grey",
                        text_align="center"
                    ),
                    padding=40,
                    alignment=ft.alignment.center
                )
            )
        else:
            # İlk 6 hastayı göster
            for idx, patient in enumerate(patients[:6]):
                # patient: (id, name, date, status, notes)
                patient_name = str(patient[1])
                
                try:
                    time_str = patient[2].strftime("%H:%M")
                except:
                    time_str = str(patient[2])[-5:]
                
                # Kart
                card = ft.Card(
                    content=ft.Container(
                        content=ft.Row([
                            # Sıra numarası
                            ft.Container(
                                content=ft.Text(
                                    str(idx + 1),
                                    size=20,
                                    weight="bold",
                                    color="white"
                                ),
                                bgcolor="#1e293b",
                                width=40,
                                height=40,
                                border_radius=20,
                                alignment=ft.alignment.center
                            ),
                            # İsim
                            ft.Text(
                                patient_name,
                                size=20,
                                weight="bold",
                                color="#1e293b",
                                expand=True
                            ),
                            # Saat
                            ft.Container(
                                content=ft.Row([
                                    ft.Icon(
                                        ft.Icons.ACCESS_TIME,
                                        size=18,
                                        color="teal"
                                    ),
                                    ft.Text(
                                        time_str,
                                        size=18,
                                        weight="bold",
                                        color="teal"
                                    )
                                ], spacing=5),
                                padding=ft.padding.only(right=10)
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=15
                    ),
                    elevation=3,
                    color="white"
                )
                
                self.waiting_list_display.controls.append(card)

    def cleanup(self):
        """Sayfa kapatılırken temizlik"""
        self.is_running = False