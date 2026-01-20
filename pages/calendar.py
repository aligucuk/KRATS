import flet as ft
import calendar
import datetime

class CalendarPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.today = datetime.date.today()
        self.current_month = self.today.month
        self.current_year = self.today.year
        self.calendar_grid = ft.Column(wrap=True, alignment=ft.MainAxisAlignment.CENTER)

    def get_month_data(self):
        # Ayın ilk ve son gününü bul
        num_days = calendar.monthrange(self.current_year, self.current_month)[1]
        start_date = f"{self.current_year}-{self.current_month:02d}-01"
        end_date = f"{self.current_year}-{self.current_month:02d}-{num_days}"
        
        # O ayki randevuları çek
        raw_data = self.db.get_appointments_by_range(start_date, end_date)
        
        # Veriyi işle: { '2023-10-25': 3 } (O gün 3 randevu var gibi)
        appt_counts = {}
        for dt, status in raw_data:
            d_str = dt.strftime("%Y-%m-%d")
            # Sadece 'Bekliyor' veya 'Tamamlandı' olanları say
            if status != "İptal":
                appt_counts[d_str] = appt_counts.get(d_str, 0) + 1
        return appt_counts

    def build_calendar(self):
        self.calendar_grid.controls.clear()
        
        # Başlıklar (Pzt, Sal...)
        days_tr = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
        header_row = ft.Row(
            controls=[
                ft.Container(content=ft.Text(d, weight="bold", color="primary"), width=50, alignment=ft.alignment.center) 
                for d in days_tr
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )
        self.calendar_grid.controls.append(header_row)

        # Takvim Matrisi
        cal_matrix = calendar.monthcalendar(self.current_year, self.current_month)
        appt_data = self.get_month_data()

        for week in cal_matrix:
            week_row = ft.Row(alignment=ft.MainAxisAlignment.CENTER)
            for day in week:
                if day == 0:
                    # Boş kutu (Ayın öncesi/sonrası)
                    week_row.controls.append(ft.Container(width=50, height=50))
                else:
                    # O günün tarihi
                    date_key = f"{self.current_year}-{self.current_month:02d}-{day:02d}"
                    count = appt_data.get(date_key, 0)
                    
                    # Renklendirme mantığı
                    bg_color = "surfaceVariant"
                    border_color = "transparent"
                    text_color = "onSurface"
                    
                    # Eğer bugünse kenarlık ekle
                    if (day == self.today.day and 
                        self.current_month == self.today.month and 
                        self.current_year == self.today.year):
                        border_color = "primary"

                    # Eğer randevu varsa yeşil yap
                    content_list = [ft.Text(str(day), color=text_color, weight="bold")]
                    if count > 0:
                        bg_color = "green200" # Hafif yeşil
                        content_list.append(
                            ft.Container(
                                content=ft.Text(f"{count}", size=10, color="white"),
                                bgcolor="green", border_radius=10, padding=2, margin=ft.margin.only(top=2)
                            )
                        )

                    day_container = ft.Container(
                        content=ft.Column(content_list, alignment=ft.MainAxisAlignment.CENTER, spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        width=50, height=50,
                        bgcolor=bg_color,
                        border=ft.border.all(2, border_color) if border_color != "transparent" else None,
                        border_radius=8,
                        on_click=lambda e, d=day: self.day_clicked(d),
                        ink=True
                    )
                    week_row.controls.append(day_container)
            
            self.calendar_grid.controls.append(week_row)
        
        self.page.update()

    def day_clicked(self, day):
        # Tıklanan güne git (Tüm Randevular sayfasına yönlendirilebilir veya popup açılabilir)
        # Şimdilik basitçe kullanıcıya bilgi verelim
        date_str = f"{day}.{self.current_month}.{self.current_year}"
        self.page.open(ft.SnackBar(ft.Text(f"{date_str} seçildi. Detaylar için 'Tüm Randevular'a bakınız."), bgcolor="blue"))

    def change_month(self, delta):
        self.current_month += delta
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        elif self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        
        self.txt_month_display.value = f"{calendar.month_name[self.current_month]} {self.current_year}"
        self.build_calendar()

    def view(self):
        # Türkçe Ay İsimleri için basit hack (Locale ile uğraşmamak için)
        tr_months = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        
        self.txt_month_display = ft.Text(
            f"{tr_months[self.current_month]} {self.current_year}", 
            size=20, weight="bold", color="primary"
        )
        
        self.build_calendar()

        return ft.View(
            "/calendar",
            [
                ft.AppBar(title=ft.Text("Ajanda"), bgcolor="background", color="primary", leading=ft.IconButton("arrow_back", icon_color="primary", on_click=lambda _: self.page.go("/dashboard"))),
                
                ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                # Üst Navigasyon
                                ft.Row(
                                    [
                                        ft.IconButton("chevron_left", on_click=lambda _: self.change_month(-1)),
                                        self.txt_month_display,
                                        ft.IconButton("chevron_right", on_click=lambda _: self.change_month(1)),
                                    ], 
                                    alignment=ft.MainAxisAlignment.CENTER
                                ),
                                ft.Divider(),
                                # Takvim Izgarası
                                ft.Container(
                                    content=self.calendar_grid,
                                    padding=20,
                                    bgcolor="surface",
                                    border_radius=15,
                                    shadow=ft.BoxShadow(blur_radius=10, color="#1A000000")
                                ),
                                ft.Container(height=20),
                                ft.Text("* Yeşil kutular randevu olan günleri gösterir.", size=12, color="grey")
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=20, alignment=ft.alignment.center
                        )
                    ],
                    scroll=ft.ScrollMode.AUTO, expand=True
                )
            ], bgcolor="background"
        )