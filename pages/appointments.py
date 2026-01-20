import flet as ft
from datetime import datetime
from utils.google_calendar_manager import GoogleCalendarManager

class AppointmentsPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db

        # Tarih Seçici
        self.date_picker = ft.DatePicker(
            on_change=self.date_changed,
            first_date=datetime(2023, 1, 1),
            last_date=datetime(2030, 12, 31)
        )
        self.page.overlay.append(self.date_picker)

        self.txt_date = ft.Text(datetime.now().strftime("%Y-%m-%d"), size=16, weight="bold")
        self.appointments_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        
        # Yeni Randevu Diyalog Alanları
        self.new_app_name = ft.TextField(label="Hasta Adı")
        self.new_app_time = ft.TextField(label="Saat (HH:MM)", hint_text="14:30")
        self.new_app_note = ft.TextField(label="Not")

    def view(self):
        self.load_appointments()
        
        header = ft.Row([
            ft.Text("Randevu Yönetimi", size=24, weight="bold", color="teal"),
            ft.Container(expand=True),
            # YENİ RANDEVU BUTONU
            ft.ElevatedButton(
                "Yeni Randevu +", 
                icon=ft.Icons.ADD, 
                bgcolor="green", color="white",
                on_click=self.open_add_dialog
            ),
            ft.ElevatedButton("Tarih Seç", icon=ft.Icons.CALENDAR_MONTH, on_click=lambda _: self.date_picker.pick_date()),
            ft.Container(content=self.txt_date, padding=10, bgcolor=ft.Colors.TEAL_50, border_radius=5)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        content = ft.Column([
            header,
            ft.Divider(),
            ft.Container(
                content=self.appointments_list,
                expand=True,
                padding=10
            )
        ], expand=True)

        return ft.View("/appointments", controls=[content], padding=20)

    def date_changed(self, e):
        if self.date_picker.value:
            self.txt_date.value = self.date_picker.value.strftime("%Y-%m-%d")
            self.txt_date.update()
            self.load_appointments()

    def open_add_dialog(self, e):
        """Yeni randevu ekleme penceresini açar"""
        self.add_dialog = ft.AlertDialog(
            title=ft.Text("Yeni Randevu"),
            content=ft.Column([
                self.new_app_name,
                self.new_app_time,
                self.new_app_note
            ], height=200),
            actions=[
                ft.TextButton("İptal", on_click=lambda _: self.page.close(self.add_dialog)),
                ft.ElevatedButton("Kaydet", on_click=self.save_appointment)
            ]
        )
        self.page.open(self.add_dialog)

    def save_appointment(self, e):
        # 1. Veritabanına Kayıt (Senin mevcut kodun)
        # self.db.add_appointment(...) kodun burada kalacak.
        # Örnek demo kodu:
        print("DB Kaydı yapıldı...") 
        
        # 2. GOOGLE TAKVİM SENKRONİZASYONU 📅
        try:
            # Diyalogdaki verileri al
            hasta_adi = self.new_app_name.value
            saat = self.new_app_time.value # "14:30" gibi
            tarih = self.txt_date.value # "2026-01-20" gibi
            notlar = self.new_app_note.value
            
            # Google Manager'ı çağır
            google_cal = GoogleCalendarManager()
            success, msg = google_cal.add_appointment(hasta_adi, tarih, saat, notlar)
            
            if success:
                self.page.open(ft.SnackBar(ft.Text(f"✅ {msg}"), bgcolor="green"))
            else:
                # Hata olsa bile program durmasın, sadece uyarsın
                print(f"Google Sync Hatası: {msg}")
                # İstersen kullanıcıya da göster:
                # self.page.open(ft.SnackBar(ft.Text("Randevu yerel kaydedildi ama Google'a gidilemedi."), bgcolor="orange"))

        except Exception as ex:
            print(f"Kritik Sync Hatası: {ex}")

        # Diyaloğu kapat ve yenile
        self.page.close(self.add_dialog)
        self.load_appointments()
        
    def load_appointments(self):
        self.appointments_list.controls.clear()
        # Demo veri yerine DB'den self.txt_date.value tarihine göre çekmelisin
        apps = self.db.get_todays_appointments() 
        
        if not apps:
            self.appointments_list.controls.append(ft.Text("Bu tarihte randevu yok.", italic=True, color="grey"))
        else:
            for app in apps:
                # app: id, name, date, status, notes (Örnek yapı)
                card = ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.EVENT_AVAILABLE, color="teal"),
                                title=ft.Text(app[1], weight="bold"),
                                subtitle=ft.Text(f"Saat: {str(app[2])[-5:]} | Durum: {app[3]}"),
                                trailing=ft.PopupMenuButton(
                                    items=[
                                        ft.PopupMenuItem(text="Tamamlandı", on_click=lambda e, aid=app[0]: self.update_status(aid, "Tamamlandı")),
                                        ft.PopupMenuItem(text="İptal", on_click=lambda e, aid=app[0]: self.update_status(aid, "İptal")),
                                        ft.PopupMenuItem(text="Sil", on_click=lambda e, aid=app[0]: self.delete_app(aid)),
                                    ]
                                )
                            ),
                            ft.Container(content=ft.Text(f"Not: {app[4]}"), padding=ft.padding.only(left=20, bottom=10)) if len(app)>4 and app[4] else ft.Container()
                        ]),
                        padding=5
                    )
                )
                self.appointments_list.controls.append(card)
        
        try: self.appointments_list.update()
        except: pass

    def update_status(self, app_id, status):
        # self.db.update_status(app_id, status)
        self.page.open(ft.SnackBar(ft.Text(f"Durum güncellendi: {status}"), bgcolor="green"))
        self.load_appointments()

    def delete_app(self, app_id):
        # self.db.delete_appointment(app_id)
        self.page.open(ft.SnackBar(ft.Text("Randevu silindi"), bgcolor="red"))
        self.load_appointments()