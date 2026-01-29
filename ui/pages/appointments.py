"""
Appointments Page - Randevu Yönetimi
Google Calendar entegrasyonu ile senkronizasyon
"""

import flet as ft
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from database.models import Appointment
from services.google_calendar_service import GoogleCalendarService
from services.notification_service import NotificationService
from utils.logger import app_logger


class AppointmentsPage:
    def __init__(self, page: ft.Page, db: DatabaseManager):
        self.page = page
        self.db = db
        self.google_service = GoogleCalendarService(db)
        self.notification_service = NotificationService(db)
        
        # Seçili tarih
        self.selected_date = datetime.now().date()
        
        # Date picker
        self.date_picker = ft.DatePicker(
            on_change=self.on_date_changed,
            first_date=datetime(2020, 1, 1),
            last_date=datetime(2030, 12, 31)
        )
        self.page.overlay.append(self.date_picker)
        
        # UI Components
        self.date_display = ft.Text(
            self.selected_date.strftime("%d %B %Y"),
            size=18,
            weight="bold"
        )
        self.appointments_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        self.stats_row = ft.Row(spacing=15)
        
        # Yeni randevu form alanları
        self.dd_patient = ft.Dropdown(
            label="Hasta Seçin *",
            width=300,
            on_change=self.on_patient_selected
        )
        
        self.dd_doctor = ft.Dropdown(
            label="Doktor *",
            width=300
        )
        
        self.txt_time = ft.TextField(
            label="Saat *",
            hint_text="HH:MM (örn: 14:30)",
            width=150,
            keyboard_type=ft.KeyboardType.NUMBER,
            max_length=5,
            on_change=self.format_time_input
        )
        
        self.txt_duration = ft.Dropdown(
            label="Süre",
            options=[
                ft.dropdown.Option("15", "15 dk"),
                ft.dropdown.Option("30", "30 dk"),
                ft.dropdown.Option("45", "45 dk"),
                ft.dropdown.Option("60", "1 saat")
            ],
            value="30",
            width=150
        )
        
        self.txt_notes = ft.TextField(
            label="Notlar",
            multiline=True,
            min_lines=2,
            max_lines=4
        )
        
        self.sw_google_sync = ft.Switch(
            label="Google Takvim'e Ekle",
            value=True,
            active_color="teal"
        )
        
        self.sw_send_notification = ft.Switch(
            label="SMS/Email Bildirimi Gönder",
            value=True,
            active_color="teal"
        )
        
    def view(self):
        """Ana görünüm"""
        self.load_patients()
        self.load_doctors()
        self.load_appointments()
        self.load_stats()
        
        # Pre-selected hasta varsa
        preselected_patient_id = self.page.session.get("selected_patient_id")
        if preselected_patient_id:
            self.dd_patient.value = str(preselected_patient_id)
            self.page.session.set("selected_patient_id", None)
        
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CALENDAR_MONTH, color="teal", size=30),
                ft.Column([
                    ft.Text("Randevu Yönetimi", size=24, weight="bold"),
                    ft.Text("Takvim ve randevu planlama", size=12, color="grey")
                ], spacing=0),
                ft.Container(expand=True),
                ft.Row([
                    ft.IconButton(
                        ft.Icons.CHEVRON_LEFT,
                        tooltip="Önceki Gün",
                        on_click=self.previous_day
                    ),
                    self.date_display,
                    ft.IconButton(
                        ft.Icons.CHEVRON_RIGHT,
                        tooltip="Sonraki Gün",
                        on_click=self.next_day
                    ),
                    ft.IconButton(
                        ft.Icons.CALENDAR_TODAY,
                        tooltip="Tarih Seç",
                        on_click=lambda _: self.date_picker.pick_date()
                    ),
                    ft.ElevatedButton(
                        "Yeni Randevu",
                        icon=ft.Icons.ADD,
                        bgcolor="teal",
                        color="white",
                        on_click=self.open_new_appointment_dialog
                    )
                ])
            ]),
            padding=20,
            bgcolor="white",
            border_radius=15
        )
        
        # Stats
        stats_section = ft.Container(
            content=ft.Column([
                ft.Text("Bugünün Özeti", weight="bold"),
                self.stats_row
            ], spacing=10),
            padding=20,
            bgcolor="white",
            border_radius=15
        )
        
        # Appointments List
        appointments_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Randevu Listesi", size=16, weight="bold"),
                    ft.Container(expand=True),
                    ft.IconButton(
                        ft.Icons.REFRESH,
                        tooltip="Yenile",
                        on_click=lambda _: self.load_appointments()
                    )
                ]),
                ft.Divider(),
                ft.Container(
                    content=self.appointments_list,
                    height=500
                )
            ]),
            padding=20,
            bgcolor="white",
            border_radius=15,
            expand=True
        )
        
        return ft.View(
            "/appointments",
            controls=[
                ft.Container(
                    content=ft.Column([
                        header,
                        stats_section,
                        appointments_section
                    ], spacing=15, expand=True),
                    padding=30,
                    bgcolor="#f8f9fa",
                    expand=True
                )
            ],
            padding=0
        )
    
    def load_patients(self):
        """Hasta listesini yükle"""
        try:
            patients = self.db.get_active_patients()
            
            self.dd_patient.options = [
                ft.dropdown.Option(
                    key=str(p.id),
                    text=p.full_name
                ) for p in patients
            ]
            
        except Exception as e:
            app_logger.error(f"Load patients error: {e}")
    
    def load_doctors(self):
        """Doktor listesini yükle"""
        try:
            doctors = self.db.get_users_by_role("doktor")
            
            self.dd_doctor.options = [
                ft.dropdown.Option(
                    key=str(d.id),
                    text=d.full_name
                ) for d in doctors
            ]
            
            # Oturum açan kullanıcı doktorsa otomatik seç
            current_user_id = self.page.session.get("user_id")
            current_role = self.page.session.get("role")
            
            if current_role == "doktor":
                self.dd_doctor.value = str(current_user_id)
            
        except Exception as e:
            app_logger.error(f"Load doctors error: {e}")
    
    def load_appointments(self):
        """Randevuları yükle"""
        try:
            self.appointments_list.controls.clear()

            # Seçili tarihteki randevuları çek
            appointments = self.db.get_appointments_by_date(self.selected_date)

            if not appointments:
                self.appointments_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.EVENT_BUSY, size=60, color="grey"),
                            ft.Text(
                                "Bu tarihte randevu yok",
                                size=16,
                                color="grey"
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=40,
                        alignment=ft.alignment.center
                    )
                )
            else:
                # Randevuları saate göre sırala
                appointments.sort(key=lambda x: x.appointment_date)

                for appt in appointments:
                    self.appointments_list.controls.append(
                        self._appointment_card(appt)
                    )

            # Sadece sayfa bağlıysa güncelle (ilk yüklemede sayfa henüz bağlı değil)
            if self.appointments_list.page:
                self.appointments_list.update()

        except Exception as e:
            app_logger.error(f"Load appointments error: {e}")
            if self.page:
                self.page.open(ft.SnackBar(
                    ft.Text(f"Randevu yükleme hatası: {e}"),
                    bgcolor="red"
                ))
    
    def _appointment_card(self, appt):
        """Randevu kartı"""
        # Hasta ve doktor bilgilerini çek
        patient = self.db.get_patient_by_id(appt.patient_id)
        doctor = self.db.get_user_by_id(appt.doctor_id)
        
        patient_name = patient.full_name if patient else "Bilinmeyen"
        doctor_name = f"Dr. {doctor.full_name}" if doctor else "Bilinmeyen"
        
        # Durum renkleri
        status_colors = {
            "Bekliyor": "orange",
            "Tamamlandı": "green",
            "İptal": "red",
            "Görüşülüyor": "blue"
        }
        status_color = status_colors.get(appt.status, "grey")
        
        # Saat
        time_str = appt.appointment_date.strftime("%H:%M")
        
        return ft.Card(
            content=ft.Container(
                content=ft.Row([
                    # Sol: Saat ve durum göstergesi
                    ft.Container(
                        content=ft.Column([
                            ft.Text(time_str, size=20, weight="bold", color="teal"),
                            ft.Container(
                                width=60,
                                height=4,
                                bgcolor=status_color,
                                border_radius=2
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                        width=80
                    ),
                    # Orta: Bilgiler
                    ft.Column([
                        ft.Text(patient_name, size=16, weight="bold"),
                        ft.Row([
                            ft.Icon(ft.Icons.PERSON, size=14, color="grey"),
                            ft.Text(doctor_name, size=12, color="grey")
                        ], spacing=5),
                        ft.Row([
                            ft.Icon(ft.Icons.NOTES, size=14, color="grey"),
                            ft.Text(
                                appt.notes[:50] + "..." if appt.notes and len(appt.notes) > 50 else appt.notes or "Not yok",
                                size=12,
                                color="grey"
                            )
                        ], spacing=5) if appt.notes else ft.Container()
                    ], expand=True, spacing=5),
                    # Sağ: Durum ve aksiyonlar
                    ft.Column([
                        ft.Container(
                            content=ft.Text(appt.status, size=11, color="white"),
                            bgcolor=status_color,
                            padding=8,
                            border_radius=8
                        ),
                        ft.PopupMenuButton(
                            items=[
                                ft.PopupMenuItem(
                                    text="Görüşmeye Başla",
                                    icon=ft.Icons.PLAY_ARROW,
                                    on_click=lambda _, aid=appt.id: self.update_status(aid, "Görüşülüyor")
                                ),
                                ft.PopupMenuItem(
                                    text="Tamamla",
                                    icon=ft.Icons.CHECK_CIRCLE,
                                    on_click=lambda _, aid=appt.id: self.update_status(aid, "Tamamlandı")
                                ),
                                ft.PopupMenuItem(
                                    text="İptal Et",
                                    icon=ft.Icons.CANCEL,
                                    on_click=lambda _, aid=appt.id: self.update_status(aid, "İptal")
                                ),
                                ft.PopupMenuItem(),  # Divider
                                ft.PopupMenuItem(
                                    text="Düzenle",
                                    icon=ft.Icons.EDIT,
                                    on_click=lambda _, aid=appt.id: self.edit_appointment(aid)
                                ),
                                ft.PopupMenuItem(
                                    text="Sil",
                                    icon=ft.Icons.DELETE,
                                    on_click=lambda _, aid=appt.id: self.delete_appointment(aid)
                                )
                            ]
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.END)
                ]),
                padding=15
            ),
            elevation=2
        )
    
    def load_stats(self):
        """Günlük istatistikleri yükle"""
        try:
            appointments = self.db.get_appointments_by_date(self.selected_date)

            total = len(appointments)
            waiting = len([a for a in appointments if a.status == "Bekliyor"])
            completed = len([a for a in appointments if a.status == "Tamamlandı"])
            cancelled = len([a for a in appointments if a.status == "İptal"])

            self.stats_row.controls = [
                self._stat_badge("Toplam", str(total), "blue"),
                self._stat_badge("Bekliyor", str(waiting), "orange"),
                self._stat_badge("Tamamlandı", str(completed), "green"),
                self._stat_badge("İptal", str(cancelled), "red")
            ]

            # Sadece sayfa bağlıysa güncelle
            if self.stats_row.page:
                self.stats_row.update()

        except Exception as e:
            app_logger.error(f"Load stats error: {e}")
    
    def _stat_badge(self, label, value, color):
        """İstatistik rozeti"""
        return ft.Container(
            content=ft.Column([
                ft.Text(value, size=24, weight="bold", color=color),
                ft.Text(label, size=12, color="grey")
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            padding=15,
            bgcolor=ft.Colors.with_opacity(0.1, color),
            border_radius=10,
            border=ft.border.all(1, color),
            width=120
        )
    
    def previous_day(self, e):
        """Önceki güne git"""
        self.selected_date = self.selected_date - timedelta(days=1)
        self.date_display.value = self.selected_date.strftime("%d %B %Y")
        self.load_appointments()
        self.load_stats()
        self.page.update()
    
    def next_day(self, e):
        """Sonraki güne git"""
        self.selected_date = self.selected_date + timedelta(days=1)
        self.date_display.value = self.selected_date.strftime("%d %B %Y")
        self.load_appointments()
        self.load_stats()
        self.page.update()
    
    def on_date_changed(self, e):
        """Tarih değiştiğinde"""
        if self.date_picker.value:
            self.selected_date = self.date_picker.value.date()
            self.date_display.value = self.selected_date.strftime("%d %B %Y")
            self.load_appointments()
            self.load_stats()
            self.page.update()
    
    def open_new_appointment_dialog(self, e):
        """Yeni randevu dialogu"""
        # Form sıfırla
        self.txt_time.value = ""
        self.txt_notes.value = ""
        
        dialog = ft.AlertDialog(
            title=ft.Text("Yeni Randevu Oluştur"),
            content=ft.Container(
                content=ft.Column([
                    self.dd_patient,
                    self.dd_doctor,
                    ft.Row([
                        self.txt_time,
                        self.txt_duration
                    ], spacing=10),
                    self.txt_notes,
                    ft.Divider(),
                    self.sw_google_sync,
                    self.sw_send_notification
                ], tight=True, scroll=ft.ScrollMode.AUTO),
                width=500,
                height=400
            ),
            actions=[
                ft.TextButton("İptal", on_click=lambda _: self.page.close(dialog)),
                ft.ElevatedButton(
                    "Randevu Oluştur",
                    icon=ft.Icons.CHECK,
                    bgcolor="teal",
                    color="white",
                    on_click=lambda _: self.save_appointment(dialog)
                )
            ]
        )
        
        self.page.open(dialog)
    
    def format_time_input(self, e):
        """Saat formatını otomatik düzenle"""
        text = e.control.value
        clean_text = "".join(filter(str.isdigit, text))
        
        # HH:MM formatı
        if len(clean_text) >= 2:
            clean_text = clean_text[:2] + ":" + clean_text[2:]
        
        e.control.value = clean_text[:5]
        e.control.update()
    
    def on_patient_selected(self, e):
        """Hasta seçildiğinde (ek bilgiler göster)"""
        # TODO: Hastanın son randevusu, notlar vb.
        pass
    
    def save_appointment(self, dialog):
        """Randevuyu kaydet"""
        try:
            # Validasyon
            if not self.dd_patient.value:
                self.page.open(ft.SnackBar(
                    ft.Text("Lütfen hasta seçin"),
                    bgcolor="red"
                ))
                return
            
            if not self.dd_doctor.value:
                self.page.open(ft.SnackBar(
                    ft.Text("Lütfen doktor seçin"),
                    bgcolor="red"
                ))
                return
            
            if not self.txt_time.value or len(self.txt_time.value) != 5:
                self.page.open(ft.SnackBar(
                    ft.Text("Lütfen geçerli bir saat girin (HH:MM)"),
                    bgcolor="red"
                ))
                return
            
            # Tarih ve saat birleştir
            try:
                hour, minute = map(int, self.txt_time.value.split(":"))
                appointment_datetime = datetime.combine(
                    self.selected_date,
                    datetime.min.time().replace(hour=hour, minute=minute)
                )
            except ValueError:
                self.page.open(ft.SnackBar(
                    ft.Text("Geçersiz saat formatı"),
                    bgcolor="red"
                ))
                return
            
            # Appointment objesi oluştur
            appointment = Appointment(
                id=None,
                patient_id=int(self.dd_patient.value),
                doctor_id=int(self.dd_doctor.value),
                appointment_date=appointment_datetime,
                status="Bekliyor",
                notes=self.txt_notes.value,
                reminder_sent=False,
                active_user_id=self.page.session.get("user_id")
            )
            
            # Veritabanına kaydet
            appt_id = self.db.add_appointment(appointment)
            
            # Google Calendar'a ekle
            if self.sw_google_sync.value:
                try:
                    patient = self.db.get_patient_by_id(appointment.patient_id)
                    doctor = self.db.get_user_by_id(appointment.doctor_id)
                    
                    event_title = f"Randevu: {patient.full_name}"
                    event_description = f"Doktor: Dr. {doctor.full_name}\n"
                    if appointment.notes:
                        event_description += f"Notlar: {appointment.notes}"
                    
                    duration = int(self.txt_duration.value)
                    
                    success, message = self.google_service.create_event(
                        title=event_title,
                        description=event_description,
                        start_time=appointment_datetime,
                        duration_minutes=duration
                    )
                    
                    if not success:
                        app_logger.warning(f"Google Calendar sync failed: {message}")
                    
                except Exception as ge:
                    app_logger.error(f"Google Calendar error: {ge}")
            
            # Bildirim gönder
            if self.sw_send_notification.value:
                try:
                    self.notification_service.send_appointment_notification(appt_id)
                except Exception as ne:
                    app_logger.error(f"Notification error: {ne}")
            
            # Audit log
            self.db.add_audit_log(
                user_id=self.page.session.get("user_id"),
                action_type="appointment",
                description=f"Yeni randevu oluşturuldu: #{appt_id}",
                ip_address=self.page.session.get("ip_address")
            )
            
            # Dialog kapat ve listeyi yenile
            self.page.close(dialog)
            self.load_appointments()
            self.load_stats()
            
            self.page.open(ft.SnackBar(
                ft.Text("✅ Randevu başarıyla oluşturuldu"),
                bgcolor="green"
            ))
            
        except Exception as e:
            app_logger.error(f"Save appointment error: {e}")
            self.page.open(ft.SnackBar(
                ft.Text(f"❌ Kayıt hatası: {e}"),
                bgcolor="red"
            ))
    
    def update_status(self, appointment_id, new_status):
        """Randevu durumunu güncelle"""
        try:
            self.db.update_appointment_status(appointment_id, new_status)
            
            self.load_appointments()
            self.load_stats()
            
            self.page.open(ft.SnackBar(
                ft.Text(f"Durum güncellendi: {new_status}"),
                bgcolor="blue"
            ))
            
        except Exception as e:
            app_logger.error(f"Update status error: {e}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Güncelleme hatası: {e}"),
                bgcolor="red"
            ))
    
    def edit_appointment(self, appointment_id):
        """Randevuyu düzenle"""
        # TODO: Düzenleme dialogu
        self.page.open(ft.SnackBar(
            ft.Text("Düzenleme özelliği yakında eklenecek"),
            bgcolor="blue"
        ))
    
    def delete_appointment(self, appointment_id):
        """Randevuyu sil"""
        def confirm_delete(e):
            try:
                self.db.delete_appointment(appointment_id)
                
                self.page.close(dialog)
                self.load_appointments()
                self.load_stats()
                
                self.page.open(ft.SnackBar(
                    ft.Text("Randevu silindi"),
                    bgcolor="green"
                ))
                
            except Exception as ex:
                app_logger.error(f"Delete appointment error: {ex}")
                self.page.open(ft.SnackBar(
                    ft.Text(f"Silme hatası: {ex}"),
                    bgcolor="red"
                ))
        
        dialog = ft.AlertDialog(
            title=ft.Text("Randevuyu Sil"),
            content=ft.Text("Bu randevuyu silmek istediğinizden emin misiniz?"),
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