import flet as ft
from utils.pdf_maker import create_prescription_pdf
import subprocess # PDF'i açmak için gerekli

class MedicalDetailPage:
    def __init__(self, page: ft.Page, db, patient_id):
        self.page = page
        self.db = db
        self.patient_id = patient_id

        # Form Alanları
        self.txt_anamnez = ft.TextField(label="Anamnez (Şikayet)", multiline=True, min_lines=3, border_radius=10)
        self.txt_diagnosis = ft.TextField(label="Teşhis (Tanı)", multiline=True, border_radius=10)
        self.txt_treatment = ft.TextField(label="Uygulanan Tedavi", multiline=True, min_lines=3, border_radius=10)
        self.txt_prescription = ft.TextField(label="Reçete / İlaçlar", multiline=True, icon=ft.Icons.MEDICATION, border_radius=10)

    def view(self):
        # Hastanın adını çekelim
        p = self.db.get_patient_by_id(self.patient_id)
        p_name = p[2] if p else "Bilinmeyen Hasta"

        header = ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: self.page.go(f"/patient_detail/{self.patient_id}")),
            ft.Column([
                ft.Text("Tıbbi Muayene Kaydı", size=20, weight="bold", color="teal"),
                ft.Text(p_name, color="grey")
            ])
        ])

        form = ft.Column([
            self.txt_anamnez,
            self.txt_diagnosis,
            self.txt_treatment,
            self.txt_prescription,
            ft.Container(height=10),
            ft.Row([
                ft.ElevatedButton("Muayeneyi Kaydet", icon=ft.Icons.SAVE, bgcolor="teal", color="white", on_click=self.save_record),
                # Reçete butonunu fonksiyona bağladık 👇
                ft.ElevatedButton("Reçete Yazdır", icon=ft.Icons.PRINT, bgcolor="blue", color="white", on_click=self.print_prescription)
            ])
        ], spacing=20, scroll=ft.ScrollMode.AUTO)

        return ft.View(
            f"/medical_detail/{self.patient_id}",
            controls=[
                ft.Container(
                    content=ft.Column([header, ft.Divider(), form], expand=True),
                    padding=30, bgcolor="white", border_radius=10
                )
            ],
            padding=20
        )
    
    def print_prescription(self, e):
        # --- DÜZELTİLEN GİRİNTİLER BAŞLANGIÇ ---
        # Formdaki verileri al
        tani = self.txt_diagnosis.value # Tanı alanı
        ilaclar = self.txt_prescription.value # Reçete alanı
        
        # Hasta adını veritabanından çek (Hata almamak için)
        p = self.db.get_patient_by_id(self.patient_id)
        hasta = p[2] if p else "Bilinmeyen Hasta"
        
        doktor = "Dr. Ali Gücük" # Şimdilik sabit, ilerde session'dan alınır
        
        if not ilaclar:
            self.page.snack_bar = ft.SnackBar(ft.Text("Reçete boş olamaz!"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()
            return

        # PDF Oluştur
        try:
            path = create_prescription_pdf(doktor, hasta, tani, ilaclar)
            
            self.page.snack_bar = ft.SnackBar(ft.Text(f"PDF Oluşturuldu: {path}"), bgcolor="green")
            self.page.snack_bar.open = True
            self.page.update()
            
            # Otomatik Aç (Windows/Mac)
            import os
            if os.name == 'nt': # Windows
                os.startfile(path)
            else: # Mac / Linux
                subprocess.call(('open', path))
                
        except Exception as ex:
            print(f"PDF Hatası: {ex}")
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Hata: {ex}"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()
        # --- DÜZELTİLEN GİRİNTİLER BİTİŞ ---

    def save_record(self, e):
        # Kayıt işlemi
        user_id = self.page.session.get("user_id")
        
        self.db.add_medical_record(
            self.patient_id, user_id,
            self.txt_anamnez.value,
            self.txt_diagnosis.value,
            self.txt_treatment.value,
            self.txt_prescription.value
        )
        
        self.page.open(ft.SnackBar(ft.Text("Muayene kaydedildi!"), bgcolor="green"))
        # Kaydettikten sonra geri dönebilir veya temizleyebiliriz
        self.page.go(f"/patient_detail/{self.patient_id}")