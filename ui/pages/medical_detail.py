"""
Tıbbi Muayene Kayıt Sayfası
Anamnez, teşhis, tedavi, reçete kaydı
PDF reçete oluşturma
"""
import flet as ft
from datetime import datetime
from services.pdf_service import PDFService
from services.enabiz_service import ENabizService
import logging
import os

logger = logging.getLogger(__name__)


class MedicalDetailPage:
    def __init__(self, page: ft.Page, db, patient_id: int):
        self.page = page
        self.db = db
        self.patient_id = patient_id
        self.pdf_service = PDFService()
        self.enabiz_service = ENabizService(db)
        
        # Hasta bilgisini çek
        self.patient = self._get_patient_info()
        
        # Form alanları
        self.txt_anamnez = ft.TextField(
            label="Anamnez (Şikayet)",
            multiline=True,
            min_lines=3,
            max_lines=5,
            border_radius=10,
            filled=True,
            bgcolor="#f8f9fa",
            hint_text="Hastanın şikayetlerini detaylı yazınız..."
        )
        
        self.txt_diagnosis = ft.TextField(
            label="Teşhis (Tanı)",
            multiline=True,
            min_lines=2,
            max_lines=3,
            border_radius=10,
            filled=True,
            bgcolor="#f8f9fa",
            hint_text="ICD-10 kodu ile birlikte yazınız (örn: J06.9 - Üst Solunum Yolu Enfeksiyonu)"
        )
        
        self.txt_treatment = ft.TextField(
            label="Uygulanan Tedavi / Müdahale",
            multiline=True,
            min_lines=3,
            max_lines=5,
            border_radius=10,
            filled=True,
            bgcolor="#f8f9fa",
            hint_text="Yapılan tedavi, işlemler ve öneriler..."
        )
        
        self.txt_prescription = ft.TextField(
            label="Reçete (İlaçlar)",
            multiline=True,
            min_lines=4,
            max_lines=6,
            border_radius=10,
            filled=True,
            bgcolor="#f8f9fa",
            hint_text="İlaç adı, dozaj, kullanım süresi (örn: Augmentin 1000mg 2x1 7 gün)"
        )
        
        self.txt_notes = ft.TextField(
            label="Ek Notlar (İç Kullanım)",
            multiline=True,
            min_lines=2,
            border_radius=10,
            filled=True,
            bgcolor="#fff3cd",
            hint_text="Kontrol tarihi, özel notlar..."
        )
        
        # Dosya seçici (Ek belgeler için)
        self.file_picker = ft.FilePicker(on_result=self._on_file_selected)
        self.page.overlay.append(self.file_picker)
        
        self.attached_files = []
        self.files_list = ft.Column(spacing=5)

    def _get_patient_info(self):
        """Hasta bilgilerini getir"""
        try:
            patient = self.db.get_patient_by_id(self.patient_id)
            if patient:
                return {
                    "id": patient[0],
                    "tc": patient[1],
                    "name": patient[2],
                    "phone": patient[3],
                    "birth_date": patient[4],
                    "gender": patient[5],
                }
            return None
        except Exception as e:
            logger.error(f"Hasta bilgisi getirme hatası: {e}")
            return None

    def view(self):
        if not self.patient:
            return ft.View(
                "/error",
                controls=[
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.ERROR_OUTLINE, size=80, color="red"),
                            ft.Text("Hasta bulunamadı!", size=20, color="red"),
                            ft.ElevatedButton(
                                "Geri Dön",
                                on_click=lambda _: self.page.go("/patient_list")
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.center,
                        padding=50
                    )
                ]
            )
        
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    ft.Icons.ARROW_BACK,
                    on_click=lambda _: self.page.go(f"/patient_detail/{self.patient_id}"),
                    icon_color="white"
                ),
                ft.Column([
                    ft.Text(
                        "Tıbbi Muayene Kaydı",
                        size=20,
                        weight="bold",
                        color="white"
                    ),
                    ft.Text(
                        f"{self.patient['name']} - TC: {self.patient['tc']}",
                        size=14,
                        color="white70"
                    )
                ], spacing=2),
            ]),
            bgcolor="teal",
            padding=15,
            border_radius=ft.border_radius.only(top_left=10, top_right=10)
        )
        
        # Form bölümü
        form_section = ft.Container(
            content=ft.Column([
                ft.Text("Muayene Bilgileri", size=16, weight="bold", color="teal"),
                ft.Divider(height=1, color="#e0e0e0"),
                self.txt_anamnez,
                self.txt_diagnosis,
                self.txt_treatment,
                self.txt_prescription,
                self.txt_notes,
                
                # Dosya ekleme
                ft.Container(height=10),
                ft.Text("Ek Belgeler (Tetkik, Görsel vb.)", size=14, weight="bold"),
                ft.Row([
                    ft.OutlinedButton(
                        "Dosya Ekle",
                        icon=ft.Icons.ATTACH_FILE,
                        on_click=lambda _: self.file_picker.pick_files(
                            allow_multiple=True
                        )
                    ),
                    ft.Text(
                        f"{len(self.attached_files)} dosya eklendi",
                        size=12,
                        color="grey"
                    )
                ]),
                self.files_list,
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            padding=20,
            bgcolor="white",
            border_radius=ft.border_radius.only(bottom_left=10, bottom_right=10)
        )
        
        # Aksiyon butonları
        action_bar = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    "Kaydet",
                    icon=ft.Icons.SAVE,
                    bgcolor="teal",
                    color="white",
                    style=ft.ButtonStyle(padding=20),
                    width=150,
                    on_click=self._save_record
                ),
                ft.ElevatedButton(
                    "Reçete Yazdır (PDF)",
                    icon=ft.Icons.PRINT,
                    bgcolor="blue",
                    color="white",
                    style=ft.ButtonStyle(padding=20),
                    width=200,
                    on_click=self._print_prescription
                ),
                ft.ElevatedButton(
                    "E-Nabız'a Gönder",
                    icon=ft.Icons.CLOUD_UPLOAD,
                    bgcolor="green",
                    color="white",
                    style=ft.ButtonStyle(padding=20),
                    width=180,
                    on_click=self._send_to_enabiz
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
            padding=20
        )
        
        return ft.View(
            f"/medical_detail/{self.patient_id}",
            controls=[
                ft.Container(
                    content=ft.Column([
                        header,
                        form_section,
                        action_bar
                    ], spacing=0),
                    width=900,
                    shadow=ft.BoxShadow(
                        blur_radius=20,
                        color=ft.Colors.with_opacity(0.1, "black")
                    )
                )
            ],
            padding=20,
            bgcolor="#f5f5f5",
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

    def _on_file_selected(self, e: ft.FilePickerResultEvent):
        """Dosya seçildiğinde"""
        if e.files:
            for file in e.files:
                self.attached_files.append({
                    "name": file.name,
                    "path": file.path,
                    "size": file.size
                })
            self._update_files_list()

    def _update_files_list(self):
        """Dosya listesini güncelle"""
        self.files_list.controls.clear()
        
        for idx, file in enumerate(self.attached_files):
            size_mb = file["size"] / (1024 * 1024)
            self.files_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.INSERT_DRIVE_FILE, size=20, color="blue"),
                        ft.Text(file["name"], size=12, expand=True),
                        ft.Text(f"{size_mb:.2f} MB", size=10, color="grey"),
                        ft.IconButton(
                            ft.Icons.DELETE_OUTLINE,
                            icon_size=18,
                            icon_color="red",
                            on_click=lambda _, i=idx: self._remove_file(i)
                        )
                    ]),
                    bgcolor="#f0f0f0",
                    padding=8,
                    border_radius=5
                )
            )
        
        try:
            self.files_list.update()
        except:
            pass

    def _remove_file(self, index: int):
        """Dosyayı listeden çıkar"""
        if 0 <= index < len(self.attached_files):
            self.attached_files.pop(index)
            self._update_files_list()

    def _save_record(self, e):
        """Muayene kaydını kaydet"""
        try:
            # Validasyon
            if not self.txt_diagnosis.value:
                self.page.open(
                    ft.SnackBar(
                        ft.Text("Tanı alanı boş bırakılamaz!"),
                        bgcolor="red"
                    )
                )
                return
            
            user_id = self.page.session.get("user_id")
            
            # Veritabanına kaydet
            self.db.add_medical_record(
                patient_id=self.patient_id,
                doctor_id=user_id,
                anamnez=self.txt_anamnez.value or "",
                diagnosis=self.txt_diagnosis.value,
                treatment=self.txt_treatment.value or "",
                prescription=self.txt_prescription.value or "",
                notes=self.txt_notes.value or ""
            )
            
            # Eklenen dosyaları kaydet
            for file in self.attached_files:
                self.db.add_patient_file(
                    patient_id=self.patient_id,
                    file_name=file["name"],
                    file_path=file["path"],
                    file_type="medical_record"
                )
            
            self.page.open(
                ft.SnackBar(
                    ft.Text("✅ Muayene kaydedildi!"),
                    bgcolor="green"
                )
            )
            
            # Formu temizle
            self.txt_anamnez.value = ""
            self.txt_diagnosis.value = ""
            self.txt_treatment.value = ""
            self.txt_prescription.value = ""
            self.txt_notes.value = ""
            self.attached_files.clear()
            self._update_files_list()
            self.page.update()
            
            logger.info(f"Muayene kaydedildi - Hasta ID: {self.patient_id}")
            
        except Exception as ex:
            logger.error(f"Muayene kayıt hatası: {ex}")
            self.page.open(
                ft.SnackBar(
                    ft.Text(f"❌ Hata: {str(ex)}"),
                    bgcolor="red"
                )
            )

    def _print_prescription(self, e):
        """PDF reçete oluştur"""
        try:
            if not self.txt_prescription.value:
                self.page.open(
                    ft.SnackBar(
                        ft.Text("Reçete alanı boş!"),
                        bgcolor="orange"
                    )
                )
                return
            
            doctor_name = self.page.session.get("user_name", "Dr. Bilinmeyen")
            
            pdf_path = self.pdf_service.create_prescription(
                doctor_name=doctor_name,
                patient_name=self.patient["name"],
                diagnosis=self.txt_diagnosis.value or "Belirtilmemiş",
                prescription=self.txt_prescription.value
            )
            
            self.page.open(
                ft.SnackBar(
                    ft.Text(f"✅ PDF oluşturuldu: {pdf_path}"),
                    bgcolor="green"
                )
            )
            
            # PDF'i aç
            if os.name == 'nt':  # Windows
                os.startfile(pdf_path)
            else:  # Mac / Linux
                import subprocess
                subprocess.call(('open', pdf_path))
            
            logger.info(f"Reçete PDF oluşturuldu: {pdf_path}")
            
        except Exception as ex:
            logger.error(f"PDF oluşturma hatası: {ex}")
            self.page.open(
                ft.SnackBar(
                    ft.Text(f"❌ PDF Hatası: {str(ex)}"),
                    bgcolor="red"
                )
            )

    def _send_to_enabiz(self, e):
        """E-Nabız'a gönder"""
        try:
            if not self.txt_diagnosis.value:
                self.page.open(
                    ft.SnackBar(
                        ft.Text("Tanı bilgisi gerekli!"),
                        bgcolor="orange"
                    )
                )
                return
            
            # E-Nabız entegrasyonu
            patient_data = {
                "tc_no": self.patient["tc"],
                "name": self.patient["name"],
                "gender": self.patient["gender"]
            }
            
            appointment_data = {
                "date": datetime.now().strftime("%Y%m%d%H%M"),
                "diagnosis": self.txt_diagnosis.value,
                "treatment": self.txt_treatment.value or ""
            }
            
            result = self.enabiz_service.send_examination_data(
                patient_data,
                appointment_data
            )
            
            if result["status"] == "success":
                self.page.open(
                    ft.SnackBar(
                        ft.Text(f"✅ E-Nabız: {result['message']}"),
                        bgcolor="green"
                    )
                )
                logger.info(f"E-Nabız gönderimi başarılı - Takip: {result.get('tracking_id')}")
            else:
                self.page.open(
                    ft.SnackBar(
                        ft.Text(f"⚠️ {result['message']}"),
                        bgcolor="orange"
                    )
                )
            
        except Exception as ex:
            logger.error(f"E-Nabız gönderim hatası: {ex}")
            self.page.open(
                ft.SnackBar(
                    ft.Text(f"❌ E-Nabız Hatası: {str(ex)}"),
                    bgcolor="red"
                )
            )