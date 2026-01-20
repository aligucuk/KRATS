import flet as ft
import datetime
import calendar

class CalendarPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.user_id = page.session.get("user_id")
        self.user_name = page.session.get("user_name")
        self.year = datetime.date.today().year
        self.month = datetime.date.today().month
        self.selected_date = datetime.date.today()
        
        # Tema Rengini Al (BUG FIX: Tema Rengi)
        self.theme_color = self.db.get_setting("theme_color") or "teal"
        
        self.calendar_grid = ft.Column(wrap=True, width=350, spacing=5)
        self.notes_view = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    def view(self):
        # Asistan Listesi (Not paylaşımı için)
        assistants = [ft.dropdown.Option(str(u[0]), u[2]) for u in self.db.get_all_users() if u[3] == "sekreter"]
        self.dd_share = ft.Dropdown(label="Asistana Gönder", options=assistants, width=200, text_size=12)

        # Header (BUG FIX: Yıl ve Ay Doğru Gösterim)
        self.lbl_month = ft.Text(f"{calendar.month_name[self.month]} {self.year}", size=20, weight="bold", color=self.theme_color)
        header = ft.Row([
            ft.IconButton(ft.Icons.CHEVRON_LEFT, on_click=lambda _: self.change_month(-1), icon_color=self.theme_color),
            self.lbl_month,
            ft.IconButton(ft.Icons.CHEVRON_RIGHT, on_click=lambda _: self.change_month(1), icon_color=self.theme_color),
        ], alignment=ft.MainAxisAlignment.CENTER)

        self.build_calendar()

        self.txt_note = ft.TextField(label="Not Ekle", multiline=True, min_lines=2, border_radius=10)
        btn_add = ft.ElevatedButton("Kaydet / Gönder", bgcolor=self.theme_color, color="white", on_click=self.save_note)

        # Sağ Panel
        right_panel = ft.Container(
            content=ft.Column([
                ft.Text(f"Seçili: {self.selected_date.strftime('%d.%m.%Y')}", weight="bold", color=self.theme_color),
                ft.Divider(),
                ft.Text("Ajanda & Randevular:", weight="bold"),
                ft.Container(content=self.notes_view, height=300, border=ft.border.all(1, "grey"), border_radius=10, padding=10),
                ft.Divider(),
                self.txt_note,
                self.dd_share,
                btn_add
            ]),
            padding=20, bgcolor="white", border_radius=15, expand=True, shadow=ft.BoxShadow(blur_radius=10, color="grey")
        )

        return ft.View(
            "/calendar",
            [
                ft.AppBar(title=ft.Text("Ajanda"), bgcolor=self.theme_color, leading=ft.IconButton("arrow_back", on_click=lambda _: self.page.go("/doctor_home"))),
                ft.Container(
                    content=ft.Row([
                        ft.Container(content=ft.Column([header, self.calendar_grid]), width=400, padding=20, bgcolor="white", border_radius=15),
                        right_panel
                    ], expand=True, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START),
                    padding=20, expand=True
                )
            ], bgcolor="#f5f7f8"
        )

    def change_month(self, delta):
        # BUG FIX: Yıl değişimi
        self.month += delta
        if self.month > 12:
            self.month = 1
            self.year += 1
        elif self.month < 1:
            self.month = 12
            self.year -= 1
        
        self.lbl_month.value = f"{calendar.month_name[self.month]} {self.year}"
        self.lbl_month.update()
        self.build_calendar()

    def build_calendar(self):
        self.calendar_grid.controls.clear()
        days = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
        self.calendar_grid.controls.append(ft.Row([ft.Container(content=ft.Text(d, weight="bold"), width=40, alignment=ft.alignment.center) for d in days], alignment=ft.MainAxisAlignment.CENTER))

        cal = calendar.monthcalendar(self.year, self.month)
        for week in cal:
            row_controls = []
            for day in week:
                if day == 0:
                    row_controls.append(ft.Container(width=40, height=40))
                else:
                    d_str = f"{self.year}-{self.month:02d}-{day:02d}"
                    is_today = (d_str == datetime.date.today().strftime("%Y-%m-%d"))
                    is_selected = (d_str == self.selected_date.strftime("%Y-%m-%d"))
                    
                    # BUG FIX: Hem Notları Hem Randevuları Kontrol Et
                    has_note = bool(self.db.get_notes_by_date(self.user_id, d_str))
                    # Randevu kontrolü için basit bir query (DB manager'a eklemesek de buradan çağırabiliriz veya get_appointments kullanabiliriz)
                    # Performans için db_manager'a get_daily_counts eklenebilir ama şimdilik basit tutalım:
                    has_app = False 
                    # (Burada her gün için sorgu atmak yavaşlatabilir, o yüzden sadece not rengi bırakıyorum, detay sağda çıkacak)

                    bg = self.theme_color if is_selected else ("#ffcdd2" if has_note else "white")
                    txt_col = "white" if is_selected else "black"

                    btn = ft.Container(
                        content=ft.Text(str(day), color=txt_col, weight="bold"),
                        width=40, height=40, bgcolor=bg, border_radius=20 if is_today else 5,
                        alignment=ft.alignment.center,
                        border=ft.border.all(2, "blue") if is_today else ft.border.all(1, "#eee"),
                        on_click=lambda _, d=day: self.select_day(d), ink=True
                    )
                    row_controls.append(btn)
            self.calendar_grid.controls.append(ft.Row(row_controls, alignment=ft.MainAxisAlignment.CENTER))
        if self.calendar_grid.page: self.calendar_grid.update()
        self.load_day_details()

    def select_day(self, day):
        self.selected_date = datetime.date(self.year, self.month, day)
        self.build_calendar() # Rengi güncelle

    def save_note(self, e):
        d_str = self.selected_date.strftime("%Y-%m-%d")
        if self.dd_share.value:
            # Paylaşımlı Not
            target_id = self.dd_share.value
            self.db.add_shared_note(self.user_name, target_id, d_str, self.txt_note.value)
            self.page.open(ft.SnackBar(ft.Text("Not asistana iletildi."), bgcolor="orange"))
        else:
            # Kendine Not
            self.db.add_note(self.user_id, d_str, self.txt_note.value, False)
            self.page.open(ft.SnackBar(ft.Text("Not kaydedildi."), bgcolor="green"))
        
        self.txt_note.value = ""
        self.load_day_details()

    def load_day_details(self):
        self.notes_view.controls.clear()
        d_str = self.selected_date.strftime("%Y-%m-%d")
        
        # 1. Notlar
        notes = self.db.get_notes_by_date(self.user_id, d_str)
        if notes:
            self.notes_view.controls.append(ft.Text("📌 Notlar:", size=12, color="grey"))
            for n in notes:
                # n: (text, is_shared, sender_name)
                sender = f" ({n[2]} gönderdi)" if n[2] else ""
                self.notes_view.controls.append(ft.Container(content=ft.Text(f"• {n[0]}{sender}"), padding=5, bgcolor="#fff9c4", border_radius=5))

        # 2. Randevular (BUG FIX: Randevuları da göster)
        # DB Manager'a 'get_appointments_by_date' eklemediysek tümünü çekip filtreleyelim (Hızlı çözüm)
        # Doğrusu SQL ile çekmektir ama kod bütünlüğünü bozmamak için:
        all_apps = self.db.get_appointments_by_doctor(self.user_id) # Bu fonksiyon var
        # all_apps: (id, patient_name, date, status, notes, pid)
        
        daily_apps = [a for a in all_apps if a[2].strftime("%Y-%m-%d") == d_str]
        
        if daily_apps:
            self.notes_view.controls.append(ft.Divider())
            self.notes_view.controls.append(ft.Text("📅 Randevular:", size=12, color="grey"))
            for a in daily_apps:
                time_s = a[2].strftime("%H:%M")
                self.notes_view.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(time_s, weight="bold", color="teal"),
                            ft.Text(a[1]),
                            ft.Container(content=ft.Text(a[3], size=10, color="white"), bgcolor="green" if a[3]=="Tamamlandı" else "orange", padding=3, border_radius=3)
                        ]),
                        padding=5, border=ft.border.all(1, "#eee"), border_radius=5
                    )
                )

        if not notes and not daily_apps:
            self.notes_view.controls.append(ft.Text("Bugün boş.", italic=True, color="grey"))
            
        if self.notes_view.page: self.notes_view.update()