"""
Patient Detail Page - Hasta Detay Sayfası
Sekmeli yapı: Bilgiler, Dosyalar, Muayene Geçmişi, Randevular
"""

import flet as ft
from datetime import datetime
from database.db_manager import DatabaseManager
from utils.logger import app_logger
from utils.encryption_manager import EncryptionManager
import os


class PatientDetailPage:
    def __init__(self, page: ft.Page, db: DatabaseManager, patient_id: int):
        self.page = page
        self.db = db
        self.patient_id = patient_id
        self.encryption = EncryptionManager()
        
        # Patient data
        self.patient = None
        
        # File picker
        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        self.page.overlay.append(self.file_picker)
        
        # UI Components
        self.info_tab = ft.Container()
        self.files_tab = ft.Container()
        self.history_tab = ft.Container()
        self.appointments_tab = ft.Container()
        
    def view(self):
        """Ana görünüm"""
        # Hasta bilgilerini yükle
        self.load_patient()
        
        if not self.patient:
            return ft.View(
                f"/patient_detail/{self.patient_id}",
                controls=[
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.ERROR, size=80, color="red"),
                            ft.Text("Hasta bulunamadı!", size=24, weight="bold"),
                            ft.ElevatedButton(
                                "Geri Dön",
                                on_click=lambda _: self.page.go("/patient_list")
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.center,
                        expand=True
                    )
                ],
                padding=20
            )
        
        # Sekmeleri yükle
        self.load_info_tab()
        self.load_files_tab()
        self.load_history_tab()
        self.load_appointments_tab()
        
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    ft.Icons.ARROW_BACK,
                    on_click=lambda _: self.page.go("/patient_list")
                ),
                ft.CircleAvatar(
                    content=ft.Text(
                        self.patient.full_name[0].upper(),
                        size=24,
                        weight="bold"
                    ),
                    bgcolor="teal",
                    radius=30
                ),
                ft.Column([
                    ft.Text(self.patient.full_name, size=24, weight="bold"),
                    ft.Text(
                        f"Hasta No: {self.patient.id} • {self.patient.gender} • {self.calculate_age()}",
                        size=12,
                        color="grey"
                    )
                ], spacing=0),
                ft.Container(expand=True),
                ft.Row([
                    ft.ElevatedButton(
                        "Yeni Randevu",
                        icon=ft.Icons.EVENT,
                        on_click=self.new_appointment
                    ),
                    ft.ElevatedButton(
                        "Muayene Ekle",
                        icon=ft.Icons.MEDICAL_SERVICES,
                        bgcolor="teal",
                        color="white",
                        on_click=lambda _: self.page.go(f"/medical_detail/{self.patient_id}")
                    )
                ])
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
                    text="Genel Bilgiler",
                    icon=ft.Icons.INFO,
                    content=self.info_tab
                ),
                ft.Tab(
                    text="Dosyalar",
                    icon=ft.Icons.FOLDER,
                    content=self.files_tab
                ),
                ft.Tab(
                    text="Muayene Geçmişi",
                    icon=ft.Icons.HISTORY,
                    content=self.history_tab
                ),
                ft.Tab(
                    text="Randevular",
                    icon=ft.Icons.CALENDAR_MONTH,
                    content=self.appointments_tab
                )
            ],
            expand=True
        )
        
        return ft.View(
            f"/patient_detail/{self.patient_id}",
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
    
    def load_patient(self):
        """Hasta bilgilerini yükle"""
        try:
            patient = self.db.get_patient_by_id(self.patient_id)
            
            if patient:
                # Decrypt
                self.patient = patient._replace(
                    full_name=self.encryption.decrypt(patient.full_name),
                    tc_no=self.encryption.decrypt(patient.tc_no) if patient.tc_no else "",
                    phone=self.encryption.decrypt(patient.phone) if patient.phone else "",
                    address=self.encryption.decrypt(patient.address) if patient.address else ""
                )
            
        except Exception as e:
            app_logger.error(f"Load patient error: {e}")
    
    def calculate_age(self):
        """Yaş hesapla"""
        if not self.patient.birth_date:
            return "-"
        
        try:
            birth = datetime.strptime(self.patient.birth_date, "%Y-%m-%d")
            age = (datetime.now() - birth).days // 365
            return f"{age} yaş"
        except:
            return "-"
    
    def load_info_tab(self):
        """Genel bilgiler sekmesi"""
        # Bilgi satırları
        info_rows = [
            self._info_row("TC Kimlik No", self.patient.tc_no or "-"),
            self._info_row("Ad Soyad", self.patient.full_name),
            self._info_row("Telefon", self.patient.phone or "-"),
            self._info_row("E-Posta", self.patient.email or "-"),
            self._info_row("Cinsiyet", self.patient.gender or "-"),
            self._info_row("Doğum Tarihi", self.format_date(self.patient.birth_date)),
            self._info_row("Yaş", self.calculate_age()),
            self._info_row("Kaynak", self.patient.source or "-"),
            self._info_row("Durum", self.patient.status or "-"),
        ]
        
        # Adres
        address_section = ft.Container(
            content=ft.Column([
                ft.Text("Adres:", weight="bold"),
                ft.Text(self.patient.address or "Belirtilmemiş", size=14)
            ]),
            padding=15,
            bgcolor=ft.Colors.GREY_100,
            border_radius=10
        )
        
        # Düzenle butonu
        edit_button = ft.ElevatedButton(
            "Bilgileri Düzenle",
            icon=ft.Icons.EDIT,
            on_click=self.edit_patient
        )
        
        self.info_tab.content = ft.Container(
            content=ft.Column([
                ft.Column(info_rows, spacing=10),
                ft.Divider(),
                address_section,
                ft.Container(height=20),
                edit_button
            ], scroll=ft.ScrollMode.AUTO),
            padding=20
        )
    
    def _info_row(self, label, value):
        """Bilgi satırı"""
        return ft.Row([
            ft.Text(f"{label}:", weight="bold", width=150, color="grey"),
            ft.Text(str(value), size=16)
        ])
    
    def format_date(self, date_str):
        """Tarihi formatla"""
        if not date_str:
            return "-"
        
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            return date.strftime("%d.%m.%Y")
        except:
            return date_str
    
    def load_files_tab(self):
        """Dosyalar sekmesi"""
        # Dosyaları çek
        files = self.db.get_patient_files(self.patient_id)
        
        # Upload butonu
        upload_section = ft.Container(
            content=ft.Column([
                ft.Text("Dosya Yönetimi", size=16, weight="bold"),
                ft.Divider(),
                ft.ElevatedButton(
                    "Dosya Yükle",
                    icon=ft.Icons.UPLOAD_FILE,
                    on_click=lambda _: self.file_picker.pick_files(
                        allow_multiple=True,
                        allowed_extensions=["pdf", "jpg", "jpeg", "png", "doc", "docx"]
                    )
                )
            ]),
            padding=20,
            bgcolor="white",
            border_radius=10
        )
        
        # Dosya listesi
        files_list = ft.Column(spacing=10)
        
        if not files:
            files_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.FOLDER_OPEN, size=60, color="grey"),
                        ft.Text("Henüz dosya yüklenmemiş", color="grey")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=40,
                    alignment=ft.alignment.center
                )
            )
        else:
            for file in files:
                # Icon seçimi
                icon = ft.Icons.PICTURE_AS_PDF if file.file_type == "pdf" else ft.Icons.IMAGE
                
                files_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Row([
                                ft.Icon(icon, color="teal", size=30),
                                ft.Column([
                                    ft.Text(file.file_name, weight="bold"),
                                    ft.Text(
                                        self.format_date(file.upload_date),
                                        size=12,
                                        color="grey"
                                    )
                                ], expand=True, spacing=2),
                                ft.Row([
                                    ft.IconButton(
                                        ft.Icons.DOWNLOAD,
                                        tooltip="İndir",
                                        on_click=lambda _, f=file: self.download_file(f)
                                    ),
                                    ft.IconButton(
                                        ft.Icons.DELETE,
                                        tooltip="Sil",
                                        icon_color="red",
                                        on_click=lambda _, fid=file.id: self.delete_file(fid)
                                    )
                                ])
                            ]),
                            padding=15
                        )
                    )
                )
        
        self.files_tab.content = ft.Container(
            content=ft.Column([
                upload_section,
                ft.Container(height=10),
                files_list
            ], scroll=ft.ScrollMode.AUTO, expand=True),
            padding=20
        )
    
    def load_history_tab(self):
        """Muayene geçmişi sekmesi"""
        # Muayene kayıtlarını çek
        records = self.db.get_medical_records(self.patient_id)
        
        records_list = ft.Column(spacing=15)
        
        if not records:
            records_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.MEDICAL_SERVICES_OUTLINED, size=60, color="grey"),
                        ft.Text("Muayene kaydı bulunamadı", color="grey")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=40,
                    alignment=ft.alignment.center
                )
            )
        else:
            for record in records:
                # Doktor adı
                doctor = self.db.get_user_name(record.doctor_id)
                
                records_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.Icons.CALENDAR_TODAY, size=16, color="grey"),
                                    ft.Text(
                                        self.format_date(record.date),
                                        size=12,
                                        color="grey"
                                    ),
                                    ft.Container(expand=True),
                                    ft.Text(
                                        f"Dr. {doctor}",
                                        size=12,
                                        color="teal",
                                        weight="bold"
                                    )
                                ]),
                                ft.Divider(),
                                ft.Column([
                                    ft.Text("Şikayet:", weight="bold", size=12),
                                    ft.Text(record.anamnez or "-", size=13),
                                    ft.Container(height=5),
                                    ft.Text("Tanı:", weight="bold", size=12),
                                    ft.Text(record.diagnosis or "-", size=13),
                                    ft.Container(height=5),
                                    ft.Text("Tedavi:", weight="bold", size=12),
                                    ft.Text(record.treatment or "-", size=13),
                                    ft.Container(height=5),
                                    ft.Text("Reçete:", weight="bold", size=12),
                                    ft.Text(record.prescription or "-", size=13)
                                ], spacing=2)
                            ]),
                            padding=15
                        )
                    )
                )
        
        self.history_tab.content = ft.Container(
            content=records_list,
            padding=20,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
    
    def load_appointments_tab(self):
        """Randevular sekmesi"""
        # Randevuları çek
        appointments = self.db.get_patient_appointments(self.patient_id)
        
        appointments_list = ft.Column(spacing=10)
        
        if not appointments:
            appointments_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.EVENT_BUSY, size=60, color="grey"),
                        ft.Text("Randevu bulunamadı", color="grey")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=40,
                    alignment=ft.alignment.center
                )
            )
        else:
            # Durum renkleri
            status_colors = {
                "Bekliyor": "orange",
                "Tamamlandı": "green",
                "İptal": "red",
                "Görüşülüyor": "blue"
            }
            
            for appt in appointments:
                color = status_colors.get(appt.status, "grey")
                
                appointments_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(
                                        appt.appointment_date.strftime("%d.%m.%Y"),
                                        weight="bold"
                                    ),
                                    ft.Text(
                                        appt.appointment_date.strftime("%H:%M"),
                                        size=12,
                                        color="grey"
                                    )
                                ], spacing=2),
                                ft.Container(expand=True),
                                ft.Container(
                                    content=ft.Text(
                                        appt.status,
                                        size=11,
                                        color="white"
                                    ),
                                    bgcolor=color,
                                    padding=8,
                                    border_radius=8
                                ),
                                ft.PopupMenuButton(
                                    items=[
                                        ft.PopupMenuItem(
                                            text="Düzenle",
                                            icon=ft.Icons.EDIT
                                        ),
                                        ft.PopupMenuItem(
                                            text="İptal Et",
                                            icon=ft.Icons.CANCEL
                                        )
                                    ]
                                )
                            ]),
                            padding=15
                        )
                    )
                )
        
        self.appointments_tab.content = ft.Container(
            content=appointments_list,
            padding=20,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
    
    def on_file_picked(self, e: ft.FilePickerResultEvent):
        """Dosya seçildiğinde"""
        if not e.files:
            return
        
        try:
            for file in e.files:
                # Dosyayı kaydet
                upload_dir = "uploads/patients"
                os.makedirs(upload_dir, exist_ok=True)
                
                # Benzersiz dosya adı
                filename = f"{self.patient_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.name}"
                filepath = os.path.join(upload_dir, filename)
                
                # Dosyayı kopyala
                import shutil
                shutil.copy(file.path, filepath)
                
                # Veritabanına kaydet
                self.db.add_patient_file(
                    patient_id=self.patient_id,
                    file_name=file.name,
                    file_path=filepath,
                    file_type=file.name.split('.')[-1].lower()
                )
            
            # Dosyalar sekmesini yenile
            self.load_files_tab()
            self.files_tab.update()
            
            self.page.open(ft.SnackBar(
                ft.Text("Dosya(lar) başarıyla yüklendi"),
                bgcolor="green"
            ))
            
        except Exception as ex:
            app_logger.error(f"File upload error: {ex}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Dosya yükleme hatası: {ex}"),
                bgcolor="red"
            ))
    
    def download_file(self, file):
        """Dosyayı indir"""
        try:
            import subprocess
            
            # Dosyayı aç
            if os.name == 'nt':  # Windows
                os.startfile(file.file_path)
            else:  # Mac/Linux
                subprocess.call(('open', file.file_path))
                
        except Exception as e:
            app_logger.error(f"Download file error: {e}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Dosya açma hatası: {e}"),
                bgcolor="red"
            ))
    
    def delete_file(self, file_id):
        """Dosyayı sil"""
        # Onay dialogu
        def confirm_delete(e):
            try:
                self.db.delete_patient_file(file_id)
                self.load_files_tab()
                self.files_tab.update()
                self.page.close(dialog)
                self.page.open(ft.SnackBar(
                    ft.Text("Dosya silindi"),
                    bgcolor="green"
                ))
            except Exception as ex:
                app_logger.error(f"Delete file error: {ex}")
                self.page.open(ft.SnackBar(
                    ft.Text(f"Silme hatası: {ex}"),
                    bgcolor="red"
                ))
        
        dialog = ft.AlertDialog(
            title=ft.Text("Dosyayı Sil"),
            content=ft.Text("Bu dosyayı silmek istediğinizden emin misiniz?"),
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
    
    def edit_patient(self, e):
        """Hasta bilgilerini düzenle"""
        # TODO: Düzenleme dialogu veya sayfası
        self.page.open(ft.SnackBar(
            ft.Text("Düzenleme özelliği yakında eklenecek"),
            bgcolor="blue"
        ))
    
    def new_appointment(self, e):
        """Yeni randevu oluştur"""
        # Randevu sayfasına yönlendir (hasta pre-selected)
        self.page.session.set("selected_patient_id", self.patient_id)
        self.page.go("/appointments")