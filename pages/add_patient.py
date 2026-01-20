import flet as ft

class AddPatientPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db

        # 1. Validasyonlu İsim Alanı (Sayı Girilemez)
        self.name = ft.TextField(
            label="Ad Soyad", 
            border_radius=10,
            input_filter=ft.InputFilter(
                allow=True, 
                regex_string=r"[a-zA-Z\sğüşıöçĞÜŞİÖÇ]", 
                replacement_string=""
            )
        )
        
        self.tc = ft.TextField(
            label="TC Kimlik No", 
            max_length=11, 
            border_radius=10,
            keyboard_type=ft.KeyboardType.NUMBER,
            input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string="")
        )
        
        # 2. Validasyonlu Telefon (Sadece Rakam)
        self.phone = ft.TextField(
            label="Telefon", 
            prefix_text="+90 ", 
            border_radius=10,
            keyboard_type=ft.KeyboardType.PHONE,
            input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string="")
        )
        
        self.email = ft.TextField(label="E-Posta", icon=ft.Icons.EMAIL, border_radius=10)
        
        self.gender = ft.Dropdown(
            label="Cinsiyet",
            options=[ft.dropdown.Option("Erkek"), ft.dropdown.Option("Kadın")],
            border_radius=10
        )
        
        # 3. Akıllı Tarih Alanı (Otomatik Slash Koyar)
        self.birth_date = ft.TextField(
            label="Doğum Tarihi (GG/AA/YYYY)", 
            icon=ft.Icons.CALENDAR_MONTH, 
            border_radius=10,
            keyboard_type=ft.KeyboardType.NUMBER,
            max_length=10,
            on_change=self.format_date_input
        )
        
        self.address = ft.TextField(label="Adres", multiline=True, max_lines=3, border_radius=10)
        self.source = ft.Dropdown(
            label="Bizi Nereden Duydu?",
            options=[
                ft.dropdown.Option("Google"),
                ft.dropdown.Option("Sosyal Medya"),
                ft.dropdown.Option("Tavsiye"),
                ft.dropdown.Option("Diğer"),
            ],
            border_radius=10
        )

    def format_date_input(self, e):
        """Kullanıcı yazdıkça otomatik / işareti ekler"""
        text = e.control.value
        clean_text = "".join(filter(str.isdigit, text)) # Sadece rakamları al
        
        if len(clean_text) > 2:
            clean_text = clean_text[:2] + "/" + clean_text[2:]
        if len(clean_text) > 5:
            clean_text = clean_text[:5] + "/" + clean_text[5:]
            
        e.control.value = clean_text[:10]
        e.control.update()

    def view(self):
        header = ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: self.page.go("/patient_list")),
            ft.Text("Yeni Hasta Kaydı", size=24, weight="bold", color="teal")
        ])

        form_content = ft.Column([
            ft.Row([self.tc, self.name]),
            ft.Row([self.phone, self.email]),
            ft.Row([self.gender, self.birth_date]),
            self.source,
            self.address,
            ft.Container(height=20),
            ft.ElevatedButton(
                "KAYDET", 
                icon=ft.Icons.SAVE, 
                bgcolor="teal", color="white", 
                style=ft.ButtonStyle(padding=20),
                width=200,
                on_click=self.save_patient
            )
        ], spacing=20, scroll=ft.ScrollMode.AUTO)

        return ft.View(
            "/add_patient",
            controls=[
                ft.Container(
                    content=ft.Column([header, ft.Divider(), form_content]),
                    padding=40, bgcolor="white", border_radius=10
                )
            ],
            padding=20
        )

    def save_patient(self, e):
        try:
            if not self.tc.value or not self.name.value:
                self.page.open(ft.SnackBar(ft.Text("TC ve İsim zorunludur!"), bgcolor="red"))
                return

            # Tarih formatını DB için YYYY-MM-DD'ye çevirebilirsin veya olduğu gibi saklayabilirsin
            # Şimdilik olduğu gibi gönderiyoruz
            self.db.add_patient(
                self.tc.value, self.name.value, self.phone.value, 
                self.birth_date.value, self.gender.value, 
                self.address.value, self.email.value, self.source.value
            )
            self.page.open(ft.SnackBar(ft.Text("Hasta başarıyla eklendi!"), bgcolor="green"))
            self.page.go("/patient_list")
            
        except Exception as ex:
            self.page.open(ft.SnackBar(ft.Text(f"Hata: {ex}"), bgcolor="red"))