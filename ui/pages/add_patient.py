"""
Add Patient Page - Yeni Hasta Ekleme Formu
Gelişmiş validasyon ve kullanıcı deneyimi
"""

import flet as ft
from datetime import datetime
from database.db_manager import DatabaseManager
from database.models import Patient
from utils.logger import app_logger
from utils.encryption_manager import EncryptionManager
import re



class AddPatientPage:
    def __init__(self, page: ft.Page, db: DatabaseManager):
        self.page = page
        self.db = db
        self.encryption = EncryptionManager()
        
        # Form stilleri
        self.input_style = {
            "border_radius": 10,
            "filled": True,
            "bgcolor": "#f8f9fa",
            "border_color": "transparent",
            "content_padding": 15
        }
        
        # Form alanları
        self.txt_tc = ft.TextField(
            label="TC Kimlik No *",
            max_length=11,
            keyboard_type=ft.KeyboardType.NUMBER,
            input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]"),
            hint_text="11 haneli TC No",
            on_change=self.validate_tc,
            **self.input_style
        )
        
        self.txt_name = ft.TextField(
            label="Ad Soyad *",
            hint_text="Örn: Ahmet Yılmaz",
            input_filter=ft.InputFilter(
                allow=True,
                regex_string=r"[a-zA-ZğüşıöçĞÜŞİÖÇ\s]"
            ),
            on_change=self.validate_name,
            **self.input_style
        )
        
        self.txt_phone = ft.TextField(
            label="Telefon *",
            prefix_text="+90 ",
            max_length=10,
            keyboard_type=ft.KeyboardType.PHONE,
            input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]"),
            hint_text="5XX XXX XX XX",
            on_change=self.validate_phone,
            **self.input_style
        )
        
        self.txt_email = ft.TextField(
            label="E-Posta",
            keyboard_type=ft.KeyboardType.EMAIL,
            hint_text="ornek@email.com",
            on_change=self.validate_email,
            **self.input_style
        )
        
        self.dd_gender = ft.Dropdown(
            label="Cinsiyet *",
            options=[
                ft.dropdown.Option("Erkek"),
                ft.dropdown.Option("Kadın")
            ],
            **self.input_style
        )
        
        self.txt_birth_date = ft.TextField(
            label="Doğum Tarihi *",
            hint_text="GG/AA/YYYY",
            keyboard_type=ft.KeyboardType.NUMBER,
            max_length=10,
            on_change=self.format_date_input,
            **self.input_style
        )
        
        self.txt_address = ft.TextField(
            label="Adres",
            multiline=True,
            min_lines=3,
            max_lines=5,
            **self.input_style
        )
        
        self.dd_source = ft.Dropdown(
            label="Bizi Nereden Duydunuz?",
            options=[
                ft.dropdown.Option("Google", "Google Arama"),
                ft.dropdown.Option("Sosyal Medya", "Sosyal Medya"),
                ft.dropdown.Option("Tavsiye", "Arkadaş Tavsiyesi"),
                ft.dropdown.Option("Billboard", "Billboard/İlan"),
                ft.dropdown.Option("Diğer", "Diğer")
            ],
            value="Diğer",
            **self.input_style
        )
        
        # Validation mesajları
        self.validation_messages = ft.Column(spacing=5)
        
        # Kaydet butonu
        self.btn_save = ft.ElevatedButton(
            "Hastayı Kaydet",
            icon=ft.Icons.SAVE,
            bgcolor="teal",
            color="white",
            disabled=True,
            style=ft.ButtonStyle(padding=20),
            width=200,
            on_click=self.save_patient
        )
        
        # Progress indicator
        self.progress = ft.ProgressRing(visible=False, width=20, height=20)
        
    def view(self):
        """Ana görünüm"""
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    ft.Icons.ARROW_BACK,
                    on_click=lambda _: self.page.go("/patient_list")
                ),
                ft.Column([
                    ft.Text("Yeni Hasta Kaydı", size=24, weight="bold", color="teal"),
                    ft.Text("Hasta bilgilerini eksiksiz doldurun", size=12, color="grey")
                ], spacing=0)
            ]),
            padding=20,
            bgcolor="white",
            border_radius=15
        )
        
        # Form bölümleri
        personal_info_section = ft.Container(
            content=ft.Column([
                ft.Text("Kişisel Bilgiler", size=16, weight="bold"),
                ft.Divider(),
                ft.Row([self.txt_tc, self.txt_name], spacing=20),
                ft.Row([self.dd_gender, self.txt_birth_date], spacing=20),
            ], spacing=15),
            padding=20,
            bgcolor="white",
            border_radius=15
        )
        
        contact_info_section = ft.Container(
            content=ft.Column([
                ft.Text("İletişim Bilgileri", size=16, weight="bold"),
                ft.Divider(),
                ft.Row([self.txt_phone, self.txt_email], spacing=20),
                self.txt_address,
            ], spacing=15),
            padding=20,
            bgcolor="white",
            border_radius=15
        )
        
        additional_info_section = ft.Container(
            content=ft.Column([
                ft.Text("Ek Bilgiler", size=16, weight="bold"),
                ft.Divider(),
                self.dd_source,
            ], spacing=15),
            padding=20,
            bgcolor="white",
            border_radius=15
        )
        
        # Validation messages
        validation_section = ft.Container(
            content=self.validation_messages,
            padding=10,
            bgcolor=ft.Colors.RED_50,
            border_radius=10,
            visible=False
        )
        
        # Action buttons
        action_section = ft.Container(
            content=ft.Row([
                ft.OutlinedButton(
                    "İptal",
                    icon=ft.Icons.CANCEL,
                    on_click=lambda _: self.page.go("/patient_list")
                ),
                ft.Container(expand=True),
                self.progress,
                self.btn_save
            ], alignment=ft.MainAxisAlignment.END),
            padding=20,
            bgcolor="white",
            border_radius=15
        )
        
        # Ana layout
        form_content = ft.Column([
            header,
            personal_info_section,
            contact_info_section,
            additional_info_section,
            validation_section,
            action_section
        ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)
        
        return ft.View(
            "/add_patient",
            controls=[
                ft.Container(
                    content=form_content,
                    padding=30,
                    bgcolor="#f8f9fa",
                    expand=True
                )
            ],
            padding=0
        )
    
    def validate_tc(self, e):
        """TC kimlik numarası validasyonu"""
        tc = e.control.value
        
        if len(tc) == 11:
            if self.is_valid_tc(tc):
                e.control.error_text = None
                e.control.suffix_icon = ft.Icons.CHECK_CIRCLE
                e.control.suffix_icon_color = "green"
            else:
                e.control.error_text = "Geçersiz TC kimlik numarası"
                e.control.suffix_icon = ft.Icons.ERROR
                e.control.suffix_icon_color = "red"
        else:
            e.control.error_text = None
            e.control.suffix_icon = None
        
        e.control.update()
        self.check_form_validity()
    
    def is_valid_tc(self, tc):
        """TC kimlik numarası algoritması"""
        try:
            if len(tc) != 11 or not tc.isdigit() or tc[0] == '0':
                return False
            
            digits = [int(d) for d in tc]
            
            # 10. hane kontrolü
            sum_odd = sum(digits[0:9:2])
            sum_even = sum(digits[1:8:2])
            check_10 = (sum_odd * 7 - sum_even) % 10
            
            if check_10 != digits[9]:
                return False
            
            # 11. hane kontrolü
            check_11 = sum(digits[0:10]) % 10
            
            return check_11 == digits[10]
            
        except:
            return False
    
    def validate_name(self, e):
        """İsim validasyonu"""
        name = e.control.value.strip()
        
        if len(name) < 3:
            e.control.error_text = "En az 3 karakter olmalı"
        elif not " " in name:
            e.control.error_text = "Ad ve soyad giriniz"
        else:
            e.control.error_text = None
            e.control.suffix_icon = ft.Icons.CHECK_CIRCLE
            e.control.suffix_icon_color = "green"
        
        e.control.update()
        self.check_form_validity()
    
    def validate_phone(self, e):
        """Telefon validasyonu"""
        phone = e.control.value
        
        if len(phone) == 10 and phone.startswith('5'):
            e.control.error_text = None
            e.control.suffix_icon = ft.Icons.CHECK_CIRCLE
            e.control.suffix_icon_color = "green"
        elif len(phone) > 0:
            e.control.error_text = "Geçerli bir cep telefonu giriniz (5XX)"
            e.control.suffix_icon = ft.Icons.ERROR
            e.control.suffix_icon_color = "red"
        else:
            e.control.error_text = None
            e.control.suffix_icon = None
        
        e.control.update()
        self.check_form_validity()
    
    def validate_email(self, e):
        """Email validasyonu"""
        email = e.control.value
        
        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            e.control.error_text = "Geçersiz email formatı"
            e.control.suffix_icon = ft.Icons.ERROR
            e.control.suffix_icon_color = "red"
        elif email:
            e.control.error_text = None
            e.control.suffix_icon = ft.Icons.CHECK_CIRCLE
            e.control.suffix_icon_color = "green"
        else:
            e.control.error_text = None
            e.control.suffix_icon = None
        
        e.control.update()
        self.check_form_validity()
    
    def format_date_input(self, e):
        """Tarih formatını otomatik düzenle"""
        text = e.control.value
        clean_text = "".join(filter(str.isdigit, text))
        
        # GG/AA/YYYY formatı
        if len(clean_text) > 2:
            clean_text = clean_text[:2] + "/" + clean_text[2:]
        if len(clean_text) > 5:
            clean_text = clean_text[:5] + "/" + clean_text[5:]
        
        e.control.value = clean_text[:10]
        
        # Validasyon
        if len(clean_text) == 10:
            try:
                day, month, year = clean_text.split("/")
                date = datetime(int(year), int(month), int(day))
                
                # Gelecek tarih kontrolü
                if date > datetime.now():
                    e.control.error_text = "Gelecek tarih olamaz"
                    e.control.suffix_icon = ft.Icons.ERROR
                    e.control.suffix_icon_color = "red"
                # Çok eski tarih kontrolü (150 yaş üstü)
                elif (datetime.now() - date).days > 150 * 365:
                    e.control.error_text = "Geçersiz tarih"
                    e.control.suffix_icon = ft.Icons.ERROR
                    e.control.suffix_icon_color = "red"
                else:
                    e.control.error_text = None
                    e.control.suffix_icon = ft.Icons.CHECK_CIRCLE
                    e.control.suffix_icon_color = "green"
            except ValueError:
                e.control.error_text = "Geçersiz tarih formatı"
                e.control.suffix_icon = ft.Icons.ERROR
                e.control.suffix_icon_color = "red"
        else:
            e.control.error_text = None
            e.control.suffix_icon = None
        
        e.control.update()
        self.check_form_validity()
    
    def check_form_validity(self):
        """Form geçerliliğini kontrol et"""
        is_valid = True
        errors = []
        
        # Zorunlu alanlar
        if not self.txt_tc.value or len(self.txt_tc.value) != 11:
            is_valid = False
            errors.append("TC Kimlik No eksik veya hatalı")
        elif not self.is_valid_tc(self.txt_tc.value):
            is_valid = False
            errors.append("TC Kimlik No geçersiz")
        
        if not self.txt_name.value or len(self.txt_name.value.strip()) < 3:
            is_valid = False
            errors.append("Ad Soyad eksik")
        
        if not self.txt_phone.value or len(self.txt_phone.value) != 10:
            is_valid = False
            errors.append("Telefon numarası eksik veya hatalı")
        
        if not self.dd_gender.value:
            is_valid = False
            errors.append("Cinsiyet seçilmedi")
        
        if not self.txt_birth_date.value or len(self.txt_birth_date.value) != 10:
            is_valid = False
            errors.append("Doğum tarihi eksik")
        
        # Email kontrolü (opsiyonel ama girildiyse geçerli olmalı)
        if self.txt_email.value and not re.match(r"[^@]+@[^@]+\.[^@]+", self.txt_email.value):
            is_valid = False
            errors.append("Email formatı hatalı")
        
        # Kaydet butonunu aktifleştir/pasifleştir
        self.btn_save.disabled = not is_valid
        
        # Hata mesajlarını göster
        self.validation_messages.controls.clear()
        if errors:
            for error in errors:
                self.validation_messages.controls.append(
                    ft.Row([
                        ft.Icon(ft.Icons.ERROR, color="red", size=16),
                        ft.Text(error, size=12, color="red")
                    ], spacing=5)
                )
            self.validation_messages.parent.visible = True
        else:
            self.validation_messages.parent.visible = False
        
        try:
            self.btn_save.update()
            if self.validation_messages.parent:
                self.validation_messages.parent.update()
        except:
            pass
    
    def save_patient(self, e):
        """Hastayı kaydet"""
        try:
            # Progress göster
            self.progress.visible = True
            self.btn_save.disabled = True
            self.page.update()
            
            # Tarihi düzelt
            birth_date = None
            if self.txt_birth_date.value:
                try:
                    day, month, year = self.txt_birth_date.value.split("/")
                    birth_date = f"{year}-{month}-{day}"
                except:
                    pass
            
            # Verileri şifrele
            encrypted_tc = self.encryption.encrypt(self.txt_tc.value)
            encrypted_name = self.encryption.encrypt(self.txt_name.value.strip())
            encrypted_phone = self.encryption.encrypt(self.txt_phone.value)
            encrypted_address = self.encryption.encrypt(self.txt_address.value) if self.txt_address.value else None
            
            # Patient objesi oluştur
            patient = Patient(
                id=None,
                tc_no=encrypted_tc,
                full_name=encrypted_name,
                phone=encrypted_phone,
                birth_date=birth_date,
                gender=self.dd_gender.value,
                address=encrypted_address,
                status="Yeni",
                source=self.dd_source.value,
                email=self.txt_email.value if self.txt_email.value else None
            )
            
            # Veritabanına kaydet
            patient_id = self.db.add_patient(patient)
            
            # Log kaydı
            app_logger.info(f"New patient added: {patient_id}")
            
            # Audit log
            user_id = self.page.session.get("user_id")
            self.db.add_audit_log(
                user_id=user_id,
                action_type="patient",
                description=f"Yeni hasta eklendi: {self.txt_name.value}",
                ip_address=self.page.session.get("ip_address")
            )
            
            # Başarılı mesajı
            self.page.open(ft.SnackBar(
                ft.Text("✅ Hasta başarıyla kaydedildi!"),
                bgcolor="green"
            ))
            
            # Hasta detay sayfasına yönlendir
            import time
            time.sleep(0.5)
            self.page.go(f"/patient_detail/{patient_id}")
            
        except Exception as ex:
            app_logger.error(f"Save patient error: {ex}")
            self.page.open(ft.SnackBar(
                ft.Text(f"❌ Kayıt hatası: {ex}"),
                bgcolor="red"
            ))
            
            # Progress gizle
            self.progress.visible = False
            self.btn_save.disabled = False
            self.page.update()