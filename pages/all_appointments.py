import flet as ft
import openpyxl
import datetime

class AllAppointmentsPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        # Dosya Kaydetme Penceresi (FilePicker)
        self.file_picker = ft.FilePicker(on_result=self.save_excel)
        # Pencereyi sayfaya gizlice ekliyoruz ki kullanabilelim
        if self.file_picker not in page.overlay:
            page.overlay.append(self.file_picker)

    def get_data(self):
        if not self.db.conn: return []
        with self.db.conn.cursor() as cur:
            cur.execute("""
                SELECT a.id, p.full_name, p.tc_no, a.appointment_date, a.status, a.notes
                FROM appointments a JOIN patients p ON a.patient_id = p.id
                ORDER BY a.appointment_date DESC
            """)
            return cur.fetchall()

    def save_excel(self, e: ft.FilePickerResultEvent):
        """Kullanıcı kaydetme yerini seçince burası çalışır"""
        if not e.path: return # Vazgeçtiyse işlem yapma

        try:
            # 1. Yeni bir Excel Çalışma Kitabı oluştur
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Randevular"

            # 2. Başlıkları Ekle
            headers = ["Tarih", "Saat", "Hasta Adı", "TC Kimlik", "Durum", "Notlar"]
            ws.append(headers)

            # Başlıkları Kalın Yap
            for cell in ws[1]:
                cell.font = openpyxl.styles.Font(bold=True)

            # 3. Verileri Veritabanından Çek ve Yaz
            data = self.get_data()
            for row in data:
                # row = (id, name, tc, datetime, status, notes)
                # Bizim Excel sıramız: Tarih, Saat, İsim, TC, Durum, Not
                dt = row[3]
                date_str = dt.strftime("%d.%m.%Y")
                time_str = dt.strftime("%H:%M")
                
                ws.append([date_str, time_str, row[1], row[2], row[4], row[5]])

            # 4. Dosyayı Kaydet
            # Eğer kullanıcı uzantı yazmadıysa .xlsx ekle
            file_path = e.path
            if not file_path.endswith(".xlsx"):
                file_path += ".xlsx"
                
            wb.save(file_path)
            
            self.page.open(ft.SnackBar(ft.Text("Excel dosyası başarıyla kaydedildi!"), bgcolor="green"))
            
        except Exception as ex:
            self.page.open(ft.SnackBar(ft.Text(f"Hata oluştu: {ex}"), bgcolor="red"))

    def view(self):
        self.db.auto_update_status()
        appointments = self.get_data()
        rows = []
        for appt in appointments:
            aid, p_name, p_tc, date_time, status, notes = appt
            badge_bg = "blue" if status == "Tamamlandı" else ("green" if status == "Bekliyor" else "red")
            
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(date_time.strftime("%d.%m.%Y"), color="onSurface")),
                ft.DataCell(ft.Text(date_time.strftime("%H:%M"), color="onSurface")),
                ft.DataCell(ft.Text(p_name, weight="bold", color="onSurface")),
                ft.DataCell(ft.Text(p_tc, color="onSurfaceVariant")),
                ft.DataCell(ft.Container(content=ft.Text(status, color="white", size=12), bgcolor=badge_bg, padding=5, border_radius=5)),
                ft.DataCell(ft.Text(notes, italic=True, color="onSurfaceVariant")),
            ]))

        return ft.View(
            "/all_appointments",
            [
                # AppBar'a İndirme Butonu Eklendi
                ft.AppBar(
                    title=ft.Text("Tüm Randevular"), 
                    bgcolor="background", color="primary", 
                    leading=ft.IconButton("arrow_back", icon_color="primary", on_click=lambda _: self.page.go("/dashboard")),
                    actions=[
                        ft.IconButton(
                            icon="download", 
                            icon_color="primary", 
                            tooltip="Excel'e Aktar", 
                            on_click=lambda _: self.file_picker.save_file(
                                dialog_title="Excel Olarak Kaydet", 
                                file_name="RNDV4_Rapor.xlsx"
                            )
                        ),
                        ft.Container(width=10) # Sağdan biraz boşluk
                    ]
                ),
                
                # ANA KAPLAYICI
                ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Randevu Geçmişi", size=24, weight="bold", color="primary"),
                                ft.Divider(),
                                
                                # Tablo
                                ft.Container(
                                    content=ft.DataTable(
                                        columns=[
                                            ft.DataColumn(ft.Text("Tarih", color="primary")),
                                            ft.DataColumn(ft.Text("Saat", color="primary")),
                                            ft.DataColumn(ft.Text("Hasta Adı", color="primary")),
                                            ft.DataColumn(ft.Text("TC No", color="primary")),
                                            ft.DataColumn(ft.Text("Durum", color="primary")),
                                            ft.DataColumn(ft.Text("Notlar", color="primary")),
                                        ],
                                        rows=rows, heading_row_color="surfaceVariant", border=ft.border.all(1, "outlineVariant"),
                                    ),
                                    bgcolor="surface", padding=10, border_radius=10,
                                    alignment=ft.alignment.center
                                )
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=20, alignment=ft.alignment.center
                        )
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER, # Sayfayı ortala
                    expand=True
                )
            ], bgcolor="background"
        )