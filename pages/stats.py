import flet as ft

class StatsPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db

    def view(self):
        # 1. Kaynak Analizi (Pie Chart - İyileştirilmiş)
        try:
            source_data = self.db.get_patient_sources() # [(Source, Count), ...]
        except: source_data = []

        pie_sections = []
        colors = [ft.Colors.BLUE, ft.Colors.ORANGE, ft.Colors.GREEN, ft.Colors.RED, ft.Colors.PURPLE]
        
        if not source_data:
            pie_sections.append(ft.PieChartSection(100, title="Veri Yok", color=ft.Colors.GREY_300))
        else:
            for i, (source, count) in enumerate(source_data):
                pie_sections.append(
                    ft.PieChartSection(
                        value=count,
                        title=f"{source}\n({count})",
                        color=colors[i % len(colors)],
                        radius=80,
                        title_style=ft.TextStyle(size=12, weight="bold", color="white")
                    )
                )

        chart_source = ft.Container(
            content=ft.Column([
                ft.Text("Hasta Kaynak Dağılımı", size=16, weight="bold", color="teal"),
                ft.PieChart(
                    sections=pie_sections, 
                    sections_space=2, 
                    center_space_radius=40, 
                    expand=True
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=400, height=350, bgcolor="white", padding=20, border_radius=15, 
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, "black"))
        )

        # 2. Gelir Analizi (REAL BarChart)
        try:
            income_data = self.db.get_monthly_income_stats() # [(Ay, Tutar), ...]
        except: income_data = []

        bar_groups = []
        if income_data:
            # En yüksek değeri bul (Grafiğin tavanı için)
            max_y = max([amount for _, amount in income_data]) * 1.2
            
            for i, (date_str, amount) in enumerate(income_data):
                bar_groups.append(
                    ft.BarChartGroup(
                        x=i,
                        bar_rods=[
                            ft.BarChartRod(
                                from_y=0, to_y=amount, width=20, 
                                color="teal", tooltip=f"{date_str}: {amount} ₺",
                                border_radius=5
                            )
                        ]
                    )
                )
            
            # X ekseni etiketleri (Alt taraf)
            bottom_axis = ft.ChartAxis(
                labels=[ft.ChartAxisLabel(value=i, label=ft.Text(data[0][:3], size=10)) for i, data in enumerate(income_data)]
            )
        else:
            max_y = 100
            bottom_axis = None

        chart_income = ft.Container(
            content=ft.Column([
                ft.Text("Aylık Gelir Grafiği", size=16, weight="bold", color="teal"),
                ft.BarChart(
                    bar_groups=bar_groups,
                    border=ft.border.all(1, ft.Colors.GREY_200),
                    left_axis=ft.ChartAxis(labels_size=40, title=ft.Text("Tutar (TL)")),
                    bottom_axis=bottom_axis,
                    horizontal_grid_lines=ft.ChartGridLines(color=ft.Colors.GREY_100),
                    max_y=max_y,
                    expand=True
                ) if income_data else ft.Text("Görüntülenecek veri yok.", color="grey")
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=500, height=350, bgcolor="white", padding=20, border_radius=15, 
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, "black"))
        )

        return ft.View(
            "/stats",
            [
                ft.AppBar(title=ft.Text("İstatistikler"), bgcolor="teal", color="white", leading=ft.IconButton(ft.Icons.ARROW_BACK, icon_color="white", on_click=lambda _: self.page.go("/doctor_home"))),
                ft.Column([
                    ft.Text("Klinik Performans Paneli", size=24, weight="bold", color="teal"),
                    ft.Container(height=20),
                    ft.Row(
                        [chart_source, chart_income], 
                        alignment=ft.MainAxisAlignment.CENTER, 
                        wrap=True, spacing=20
                    )
                ], scroll=ft.ScrollMode.AUTO, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            ],
            bgcolor="#f5f7f8"
        )