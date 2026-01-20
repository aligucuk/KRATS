"""
Statistics Page - Gelişmiş İstatistikler ve Raporlama
GİZLİ ÖZELLİK - Sadece admin ve muhasebe erişebilir
"""

import flet as ft
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from utils.logger import app_logger
import calendar


class StatisticsPage:
    def __init__(self, page: ft.Page, db: DatabaseManager):
        self.page = page
        self.db = db
        
        # Tarih seçici
        self.date_picker = ft.DatePicker(
            on_change=self.on_date_change,
            first_date=datetime(2020, 1, 1),
            last_date=datetime(2030, 12, 31)
        )
        self.page.overlay.append(self.date_picker)
        
        # Tarih aralığı
        self.start_date = datetime.now() - timedelta(days=30)
        self.end_date = datetime.now()
        
        # UI Components
        self.kpi_row = ft.Row(spacing=20, wrap=True)
        self.revenue_chart = ft.Container()
        self.patient_chart = ft.Container()
        self.source_chart = ft.Container()
        self.appointment_chart = ft.Container()
        
    def view(self):
        """Ana görünüm"""
        # Yetki kontrolü
        user_role = self.page.session.get("role")
        if user_role not in ["admin", "muhasebe"]:
            return ft.View(
                "/statistics",
                controls=[
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.LOCK, size=80, color="red"),
                            ft.Text("Yetkisiz Erişim", size=24, weight="bold"),
                            ft.Text("Bu sayfaya sadece yetkili personel erişebilir."),
                            ft.ElevatedButton(
                                "Geri Dön",
                                on_click=lambda _: self.page.go("/doctor_home")
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.center,
                        expand=True
                    )
                ],
                padding=20
            )
        
        self.load_data()
        
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.BAR_CHART, color="teal", size=30),
                ft.Column([
                    ft.Text("Gelişmiş İstatistikler", size=24, weight="bold"),
                    ft.Text(
                        f"{self.start_date.strftime('%d.%m.%Y')} - {self.end_date.strftime('%d.%m.%Y')}",
                        size=12,
                        color="grey"
                    )
                ], spacing=0),
                ft.Container(expand=True),
                ft.Row([
                    ft.ElevatedButton(
                        "Tarih Aralığı",
                        icon=ft.Icons.DATE_RANGE,
                        on_click=lambda _: self.date_picker.pick_date()
                    ),
                    ft.IconButton(
                        ft.Icons.REFRESH,
                        tooltip="Yenile",
                        on_click=lambda _: self.load_data()
                    ),
                    ft.IconButton(
                        ft.Icons.DOWNLOAD,
                        tooltip="PDF Rapor",
                        on_click=self.generate_pdf_report
                    )
                ])
            ]),
            padding=20,
            bgcolor="white",
            border_radius=15
        )
        
        # KPI Cards
        kpi_section = ft.Container(
            content=ft.Column([
                ft.Text("Anahtar Performans Göstergeleri", weight="bold"),
                self.kpi_row
            ], spacing=10),
            padding=20,
            bgcolor="white",
            border_radius=15
        )
        
        # Charts Grid
        charts_grid = ft.Container(
            content=ft.Column([
                ft.Row([
                    self.revenue_chart,
                    self.patient_chart
                ], spacing=20, wrap=True),
                ft.Row([
                    self.source_chart,
                    self.appointment_chart
                ], spacing=20, wrap=True)
            ], spacing=20),
            padding=20,
            bgcolor="white",
            border_radius=15
        )
        
        return ft.View(
            "/statistics",
            controls=[
                ft.Container(
                    content=ft.Column([
                        header,
                        kpi_section,
                        charts_grid
                    ], spacing=15, expand=True, scroll=ft.ScrollMode.AUTO),
                    padding=30,
                    bgcolor="#f8f9fa",
                    expand=True
                )
            ],
            padding=0
        )
    
    def load_data(self):
        """Tüm verileri yükle"""
        try:
            self.load_kpis()
            self.load_revenue_chart()
            self.load_patient_chart()
            self.load_source_chart()
            self.load_appointment_chart()
            
            self.page.update()
            
        except Exception as e:
            app_logger.error(f"Data loading error: {e}")
            self.page.open(ft.SnackBar(ft.Text(f"Veri yükleme hatası: {e}"), bgcolor="red"))
    
    def load_kpis(self):
        """KPI kartlarını yükle"""
        try:
            # Verile çek
            total_revenue = self.db.get_total_revenue(self.start_date, self.end_date)
            total_patients = self.db.get_patient_count_range(self.start_date, self.end_date)
            total_appointments = self.db.get_appointment_count_range(self.start_date, self.end_date)
            avg_revenue_per_patient = total_revenue / total_patients if total_patients > 0 else 0
            
            # Önceki dönemle karşılaştırma
            prev_start = self.start_date - (self.end_date - self.start_date)
            prev_end = self.start_date
            prev_revenue = self.db.get_total_revenue(prev_start, prev_end)
            revenue_change = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
            
            self.kpi_row.controls = [
                self._kpi_card(
                    "Toplam Gelir",
                    f"₺{total_revenue:,.2f}",
                    f"%{revenue_change:+.1f}",
                    ft.Icons.ATTACH_MONEY,
                    "green" if revenue_change >= 0 else "red"
                ),
                self._kpi_card(
                    "Yeni Hasta",
                    str(total_patients),
                    "Bu dönem",
                    ft.Icons.PERSON_ADD,
                    "blue"
                ),
                self._kpi_card(
                    "Randevu",
                    str(total_appointments),
                    f"Ortalama: {total_appointments / 30:.1f}/gün",
                    ft.Icons.CALENDAR_MONTH,
                    "orange"
                ),
                self._kpi_card(
                    "Hasta Başına Gelir",
                    f"₺{avg_revenue_per_patient:,.2f}",
                    "Ortalama",
                    ft.Icons.TRENDING_UP,
                    "purple"
                )
            ]
            
        except Exception as e:
            app_logger.error(f"KPI loading error: {e}")
    
    def _kpi_card(self, title, value, subtitle, icon, color):
        """KPI kartı oluştur"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, color=color, size=30),
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Text(subtitle, size=10, color=color),
                        bgcolor=ft.Colors.with_opacity(0.1, color),
                        padding=5,
                        border_radius=5
                    )
                ]),
                ft.Text(value, size=28, weight="bold"),
                ft.Text(title, size=12, color="grey")
            ], spacing=5),
            padding=20,
            bgcolor="white",
            border_radius=12,
            border=ft.border.all(1, "#f0f0f0"),
            width=250
        )
    
    def load_revenue_chart(self):
        """Gelir grafiğini yükle"""
        try:
            # Günlük gelir verilerini çek
            daily_revenue = self.db.get_daily_revenue(self.start_date, self.end_date)
            
            if not daily_revenue:
                self.revenue_chart.content = ft.Text("Veri yok", color="grey")
                return
            
            # Bar chart oluştur
            max_value = max([r[1] for r in daily_revenue]) if daily_revenue else 100
            
            bar_groups = []
            for i, (date, amount) in enumerate(daily_revenue[:30]):  # Son 30 gün
                bar_groups.append(
                    ft.BarChartGroup(
                        x=i,
                        bar_rods=[
                            ft.BarChartRod(
                                from_y=0,
                                to_y=amount,
                                width=15,
                                color="teal",
                                tooltip=f"{date.strftime('%d.%m')}: ₺{amount:,.2f}",
                                border_radius=5
                            )
                        ]
                    )
                )
            
            chart = ft.BarChart(
                bar_groups=bar_groups,
                border=ft.border.all(1, ft.Colors.GREY_200),
                left_axis=ft.ChartAxis(
                    labels_size=40,
                    title=ft.Text("Gelir (₺)")
                ),
                bottom_axis=ft.ChartAxis(
                    labels=[
                        ft.ChartAxisLabel(
                            value=i,
                            label=ft.Text(daily_revenue[i][0].strftime("%d"), size=10)
                        ) for i in range(0, len(daily_revenue[:30]), 5)
                    ]
                ),
                horizontal_grid_lines=ft.ChartGridLines(
                    color=ft.Colors.GREY_100,
                    width=1
                ),
                max_y=max_value * 1.2,
                expand=True
            )
            
            self.revenue_chart.content = ft.Column([
                ft.Text("Günlük Gelir Trendi", weight="bold"),
                ft.Container(content=chart, height=300)
            ])
            self.revenue_chart.width = 600
            self.revenue_chart.padding = 20
            self.revenue_chart.bgcolor = "white"
            self.revenue_chart.border_radius = 12
            
        except Exception as e:
            app_logger.error(f"Revenue chart error: {e}")
    
    def load_patient_chart(self):
        """Hasta grafiğini yükle"""
        try:
            # Aylık hasta sayıları
            monthly_patients = self.db.get_monthly_patient_count(self.start_date, self.end_date)
            
            if not monthly_patients:
                self.patient_chart.content = ft.Text("Veri yok", color="grey")
                return
            
            # Line chart oluştur
            data_points = []
            for i, (month, count) in enumerate(monthly_patients):
                data_points.append(
                    ft.LineChartDataPoint(i, count)
                )
            
            chart = ft.LineChart(
                data_series=[
                    ft.LineChartData(
                        data_points=data_points,
                        stroke_width=3,
                        color="blue",
                        curved=True,
                        stroke_cap_round=True,
                    )
                ],
                border=ft.border.all(1, ft.Colors.GREY_200),
                left_axis=ft.ChartAxis(
                    labels_size=40,
                    title=ft.Text("Hasta Sayısı")
                ),
                bottom_axis=ft.ChartAxis(
                    labels=[
                        ft.ChartAxisLabel(
                            value=i,
                            label=ft.Text(
                                calendar.month_abbr[monthly_patients[i][0].month],
                                size=10
                            )
                        ) for i in range(len(monthly_patients))
                    ]
                ),
                horizontal_grid_lines=ft.ChartGridLines(
                    color=ft.Colors.GREY_100,
                    width=1
                ),
                expand=True
            )
            
            self.patient_chart.content = ft.Column([
                ft.Text("Hasta Kayıt Trendi", weight="bold"),
                ft.Container(content=chart, height=300)
            ])
            self.patient_chart.width = 600
            self.patient_chart.padding = 20
            self.patient_chart.bgcolor = "white"
            self.patient_chart.border_radius = 12
            
        except Exception as e:
            app_logger.error(f"Patient chart error: {e}")
    
    def load_source_chart(self):
        """Kaynak dağılımı grafiğini yükle"""
        try:
            # Hasta kaynak dağılımı
            sources = self.db.get_patient_sources_range(self.start_date, self.end_date)
            
            if not sources:
                self.source_chart.content = ft.Text("Veri yok", color="grey")
                return
            
            # Pie chart oluştur
            colors = [
                ft.Colors.BLUE,
                ft.Colors.ORANGE,
                ft.Colors.GREEN,
                ft.Colors.RED,
                ft.Colors.PURPLE,
                ft.Colors.AMBER
            ]
            
            sections = []
            for i, (source, count) in enumerate(sources):
                sections.append(
                    ft.PieChartSection(
                        value=count,
                        title=f"{source}\n{count}",
                        color=colors[i % len(colors)],
                        radius=100,
                        title_style=ft.TextStyle(
                            size=12,
                            weight="bold",
                            color="white"
                        )
                    )
                )
            
            chart = ft.PieChart(
                sections=sections,
                sections_space=2,
                center_space_radius=50,
                expand=True
            )
            
            self.source_chart.content = ft.Column([
                ft.Text("Hasta Kaynak Dağılımı", weight="bold"),
                ft.Container(content=chart, height=300)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            self.source_chart.width = 400
            self.source_chart.padding = 20
            self.source_chart.bgcolor = "white"
            self.source_chart.border_radius = 12
            
        except Exception as e:
            app_logger.error(f"Source chart error: {e}")
    
    def load_appointment_chart(self):
        """Randevu durum grafiğini yükle"""
        try:
            # Randevu durumları
            statuses = self.db.get_appointment_statuses(self.start_date, self.end_date)
            
            if not statuses:
                self.appointment_chart.content = ft.Text("Veri yok", color="grey")
                return
            
            # Pie chart
            status_colors = {
                "Tamamlandı": ft.Colors.GREEN,
                "Bekliyor": ft.Colors.ORANGE,
                "İptal": ft.Colors.RED,
                "Görüşülüyor": ft.Colors.BLUE
            }
            
            sections = []
            for status, count in statuses:
                sections.append(
                    ft.PieChartSection(
                        value=count,
                        title=f"{status}\n{count}",
                        color=status_colors.get(status, ft.Colors.GREY),
                        radius=100,
                        title_style=ft.TextStyle(
                            size=12,
                            weight="bold",
                            color="white"
                        )
                    )
                )
            
            chart = ft.PieChart(
                sections=sections,
                sections_space=2,
                center_space_radius=50,
                expand=True
            )
            
            self.appointment_chart.content = ft.Column([
                ft.Text("Randevu Durumları", weight="bold"),
                ft.Container(content=chart, height=300)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            self.appointment_chart.width = 400
            self.appointment_chart.padding = 20
            self.appointment_chart.bgcolor = "white"
            self.appointment_chart.border_radius = 12
            
        except Exception as e:
            app_logger.error(f"Appointment chart error: {e}")
    
    def on_date_change(self, e):
        """Tarih değişimi"""
        if self.date_picker.value:
            # Başlangıç veya bitiş tarihini güncelle
            # Basit implementasyon: son seçilen tarihi bitiş olarak al
            self.end_date = self.date_picker.value
            self.start_date = self.end_date - timedelta(days=30)
            self.load_data()
    
    def generate_pdf_report(self, e):
        """PDF rapor oluştur"""
        try:
            from services.pdf_service import PDFService
            
            pdf_service = PDFService(self.db)
            filename = pdf_service.generate_statistics_report(
                self.start_date,
                self.end_date
            )
            
            self.page.open(ft.SnackBar(
                ft.Text(f"Rapor oluşturuldu: {filename}"),
                bgcolor="green"
            ))
            
            # Dosyayı aç
            import os
            import subprocess
            if os.name == 'nt':  # Windows
                os.startfile(filename)
            else:  # Mac/Linux
                subprocess.call(('open', filename))
                
        except Exception as e:
            app_logger.error(f"PDF generation error: {e}")
            self.page.open(ft.SnackBar(
                ft.Text(f"PDF oluşturma hatası: {e}"),
                bgcolor="red"
            ))