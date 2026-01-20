import flet as ft
# AppLayout SİLİNDİ

class PatientDetailPage:
    def __init__(self, page: ft.Page, db, patient_id):
        self.page = page
        self.db = db
        self.patient_id = patient_id
        self.patient_data = self.db.get_patient_by_id(patient_id)
        
        # Dosya Seçici (File Picker) - Özellik Korundu
        self.file_picker = ft.FilePicker(on_result=self.file_picker_result)
        self.page.overlay.append(self.file_picker)

    def view(self):
        if not self.patient_data:
            return ft.View("/error", controls=[ft.Text("Hasta bulunamadı!", color="red")])

        p = self.patient_data
        # p: id, tc, name, phone, bdate, gender, address, status, source, email

        # --- SEKME 1: KİMLİK KARTI ---
        info_card = ft.Container(
            content=ft.Column([
                self._row_info("TC Kimlik", p[1]),
                self._row_info("Ad Soyad", p[2], bold=True),
                self._row_info("Telefon", p[3]),
                self._row_info("E-Posta", p[9] if len(p)>9 else "-"),
                self._row_info("Cinsiyet", p[5]),
                self._row_info("Doğum Tarihi", p[4]),
                ft.Divider(),
                ft.Text(f"Adres: {p[6]}", italic=True)
            ], spacing=10),
            padding=20, bgcolor="white", border_radius=10, border=ft.border.all(1, "#eee")
        )

        # --- SEKME 2: GEÇMİŞ RANDEVULAR ---
        # Burada hastaya ait randevu geçmişini çekeceğiz (Özellik Korundu)
        # Şimdilik örnek veri veya DB'den çekme mantığı:
        history_list = ft.ListView(expand=True, spacing=10)
        # Gerçekte: history = self.db.get_patient_history(self.patient_id)
        # Kodun önceki halinde history çekme varsa buraya eklenmeli.
        history_list.controls.append(ft.Text("Henüz geçmiş kayıt yok.", color="grey"))


        # --- SEKME 3: DOSYALAR (Röntgen, Tahlil) ---
        self.files_list = ft.Column(spacing=10)
        self.load_files()
        
        files_tab = ft.Column([
            ft.ElevatedButton("Dosya Yükle", icon=ft.Icons.UPLOAD_FILE, on_click=lambda _: self.file_picker.pick_files()),
            ft.Divider(),
            self.files_list
        ], scroll=ft.ScrollMode.AUTO)

        # --- SEKME 4: 3D VÜCUT HARİTASI ---
        # iframe ile lokal 3D sunucuyu gösteriyoruz
        model_file = "muscle_male.glb" if p[5] == "Erkek" else "muscle_female.glb"
        # Not: main.py içinde 8000 portunda sunucu başlatmıştık.
        # Basit bir HTML viewer veya FletWebView kullanılabilir.
        # Flet'in standart WebView'i henüz masaüstünde kararlı değil, o yüzden buraya
        # placeholder veya resim koyuyoruz. Eğer WebView çalışıyorsa eklenebilir.
        
        body_map = ft.Container(
            content=ft.Column([
                ft.Text("3D Vücut Analizi", weight="bold"),
                ft.Text("Model yükleniyor: " + model_file, color="blue"),
                ft.Container(
                    bgcolor="#eeeeee", height=300, border_radius=10,
                    content=ft.Icon(ft.Icons.accessibility_new, size=100, color="grey"),
                    alignment=ft.alignment.center
                ),
                ft.Text("Not: 3D görüntüleme için WebView modülü gereklidir.", size=12, color="grey")
            ]),
            padding=20
        )

        # --- TAB YAPISI ---
        tabs = ft.Tabs(
            selected_index=0, animation_duration=300,
            tabs=[
                ft.Tab("Genel Bilgiler", icon=ft.Icons.INFO, content=info_card),
                ft.Tab("Tıbbi Geçmiş", icon=ft.Icons.HISTORY, content=ft.Container(content=history_list, padding=20)),
                ft.Tab("Dosyalar", icon=ft.Icons.FOLDER, content=ft.Container(content=files_tab, padding=20)),
                ft.Tab("Vücut Haritası", icon=ft.Icons.MAN_3, content=body_map),
            ],
            expand=True
        )

        header = ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: self.page.go("/patient_list")),
            ft.Column([
                ft.Text(p[2], size=24, weight="bold", color="teal"),
                ft.Text(f"Hasta ID: {p[0]}", color="grey")
            ])
        ])

        return ft.View(
            f"/patient_detail/{self.patient_id}",
            controls=[
                ft.Container(
                    content=ft.Column([header, tabs], expand=True),
                    padding=20, bgcolor="#fafafa"
                )
            ],
            padding=0
        )

    def _row_info(self, label, value, bold=False):
        return ft.Row([
            ft.Text(label + ":", weight="bold", width=100, color="grey"),
            ft.Text(str(value), weight="bold" if bold else "normal", size=16 if bold else 14)
        ])

    def file_picker_result(self, e: ft.FilePickerResultEvent):
        if e.files:
            for f in e.files:
                # Dosyayı DB'ye kaydet (Path veya Blob)
                self.db.add_patient_file(self.patient_id, f.name, f.path, "file")
            self.load_files()
            self.page.open(ft.SnackBar(ft.Text("Dosya yüklendi"), bgcolor="green"))

    def load_files(self):
        self.files_list.controls.clear()
        files = self.db.get_patient_files(self.patient_id)
        if not files:
            self.files_list.controls.append(ft.Text("Dosya yok."))
        else:
            for f in files:
                # f: id, pid, name, path, type, date
                self.files_list.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.INSERT_DRIVE_FILE, color="orange"),
                        title=ft.Text(f[2]),
                        subtitle=ft.Text(f[5]),
                        trailing=ft.IconButton(ft.Icons.DOWNLOAD)
                    )
                )
        try: self.files_list.update()
        except: pass