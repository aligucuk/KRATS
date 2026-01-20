"""
CRM Page - Müşteri İlişkileri Yönetimi
Hasta kaynak analizi, kampanyalar, takip
"""

import flet as ft
from database.db_manager import DatabaseManager
from utils.logger import app_logger


class CRMPage:
    def __init__(self, page: ft.Page, db: DatabaseManager):
        self.page = page
        self.db = db
        
        # UI Components
        self.kpi_row = ft.Row(spacing=20, wrap=True)
        self.source_chart = ft.Container()
        self.status_chart = ft.Container()
        self.campaign_list = ft.Column(spacing=10)
        
    def view(self):
        """Ana görünüm"""
        self.load_data()
        
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.PEOPLE, color="teal", size=30),
                ft.Column([
                    ft.Text("Müşteri İlişkileri Yönetimi", size=24, weight="bold"),
                    ft.Text("Hasta analizi ve kampanya yönetimi", size=12, color="grey")
                ], spacing=0)
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
        
        # Charts Row
        charts_row = ft.Row([
            self.source_chart,
            self.status_chart
        ], spacing=20, wrap=True)
        
        # Campaigns Section
        campaigns_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Aktif Kampanyalar", size=16, weight="bold"),
                    ft.Container(expand=True),
                    ft.IconButton(
                        ft.Icons.ADD,
                        tooltip="Yeni Kampanya",
                        on_click=self.add_campaign
                    )
                ]),
                ft.Divider(),
                self.campaign_list
            ]),
            padding=20,
            bgcolor="white",
            border_radius=15
        )
        
        return ft.View(
            "/crm",
            controls=[
                ft.Container(
                    content=ft.Column([
                        header,
                        kpi_section,
                        charts_row,
                        campaigns_section
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
            self.load_source_chart()
            self.load_status_chart()
            self.load_campaigns()
            
        except Exception as e:
            app_logger.error(f"CRM data loading error: {e}")
    
    def load_kpis(self):
        """KPI'ları yükle"""
        try:
            total_patients = self.db.get_patient_count()
            new_this_month = self.db.get_new_patients_this_month()
            active_patients = len(self.db.get_active_patients())
            conversion_rate = (active_patients / total_patients * 100) if total_patients > 0 else 0
            
            self.kpi_row.controls = [
                self._kpi_card(
                    "Toplam Hasta",
                    str(total_patients),
                    "Kayıtlı",
                    ft.Icons.PEOPLE,
                    "blue"
                ),
                self._kpi_card(
                    "Yeni (Bu Ay)",
                    str(new_this_month),
                    f"%{(new_this_month/total_patients*100):.1f}" if total_patients > 0 else "0%",
                    ft.Icons.PERSON_ADD,
                    "green"
                ),
                self._kpi_card(
                    "Aktif",
                    str(active_patients),
                    "Tedavi gören",
                    ft.Icons.FAVORITE,
                    "orange"
                ),
                self._kpi_card(
                    "Dönüşüm Oranı",
                    f"%{conversion_rate:.1f}",
                    "Yeni → Aktif",
                    ft.Icons.TRENDING_UP,
                    "purple"
                )
            ]
            
        except Exception as e:
            app_logger.error(f"Load KPIs error: {e}")
    
    def _kpi_card(self, title, value, subtitle, icon, color):
        """KPI kartı"""
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
                ft.Text(value, size=32, weight="bold"),
                ft.Text(title, size=12, color="grey")
            ], spacing=5),
            padding=20,
            bgcolor="white",
            border_radius=12,
            border=ft.border.all(1, "#f0f0f0"),
            width=250
        )
    
    def load_source_chart(self):
        """Kaynak dağılımı grafiği"""
        try:
            sources = self.db.get_patient_sources()
            
            if not sources:
                self.source_chart.content = ft.Text("Veri yok", color="grey")
                return
            
            # Pie chart
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
    
    def load_status_chart(self):
        """Durum dağılımı grafiği"""
        try:
            statuses = self.db.get_patient_status_distribution()
            
            if not statuses:
                self.status_chart.content = ft.Text("Veri yok", color="grey")
                return
            
            # Bar chart
            max_value = max([s[1] for s in statuses]) if statuses else 100
            
            bar_groups = []
            for i, (status, count) in enumerate(statuses):
                bar_groups.append(
                    ft.BarChartGroup(
                        x=i,
                        bar_rods=[
                            ft.BarChartRod(
                                from_y=0,
                                to_y=count,
                                width=40,
                                color="teal",
                                tooltip=f"{status}: {count}",
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
                    title=ft.Text("Hasta Sayısı")
                ),
                bottom_axis=ft.ChartAxis(
                    labels=[
                        ft.ChartAxisLabel(
                            value=i,
                            label=ft.Text(statuses[i][0], size=10)
                        ) for i in range(len(statuses))
                    ]
                ),
                horizontal_grid_lines=ft.ChartGridLines(
                    color=ft.Colors.GREY_100,
                    width=1
                ),
                max_y=max_value * 1.2,
                expand=True
            )
            
            self.status_chart.content = ft.Column([
                ft.Text("Hasta Durum Dağılımı", weight="bold"),
                ft.Container(content=chart, height=300)
            ])
            self.status_chart.width = 500
            self.status_chart.padding = 20
            self.status_chart.bgcolor = "white"
            self.status_chart.border_radius = 12
            
        except Exception as e:
            app_logger.error(f"Status chart error: {e}")
    
    def load_campaigns(self):
        """Kampanyaları yükle"""
        try:
            self.campaign_list.controls.clear()
            
            # Demo kampanyalar (DB'de campaign tablosu yoksa)
            campaigns = [
                {
                    "title": "Bahar İndirimi",
                    "description": "Tüm tedavilerde %20 indirim",
                    "end_date": "30.04.2025",
                    "active": True
                },
                {
                    "title": "Diş Temizliği Kampanyası",
                    "description": "İlk muayene ücretsiz",
                    "end_date": "15.05.2025",
                    "active": True
                }
            ]
            
            for camp in campaigns:
                self.campaign_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Row([
                                ft.Icon(
                                    ft.Icons.CAMPAIGN,
                                    color="orange" if camp["active"] else "grey",
                                    size=30
                                ),
                                ft.Column([
                                    ft.Text(camp["title"], weight="bold"),
                                    ft.Text(camp["description"], size=12, color="grey"),
                                    ft.Text(
                                        f"Bitiş: {camp['end_date']}",
                                        size=11,
                                        color="grey"
                                    )
                                ], expand=True, spacing=2),
                                ft.Switch(
                                    value=camp["active"],
                                    active_color="teal"
                                )
                            ]),
                            padding=15
                        )
                    )
                )
            
        except Exception as e:
            app_logger.error(f"Load campaigns error: {e}")
    
    def add_campaign(self, e):
        """Yeni kampanya ekle"""
        self.page.open(ft.SnackBar(
            ft.Text("Kampanya ekleme özelliği yakında eklenecek"),
            bgcolor="blue"
        ))