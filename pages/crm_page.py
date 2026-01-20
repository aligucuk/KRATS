import flet as ft

class CRMPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db

    def view(self):
        # Verileri Çek
        patient_count = self.db.get_patient_count()
        sources = self.db.get_patient_sources() # [(Google, 10), (Tavsiye, 5)]

        # --- KPI KARTLARI (Helper) ---
        def kpi_card(title, value, subtitle, icon, color):
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(content=ft.Icon(icon, color=color), padding=10, bgcolor=ft.Colors.with_opacity(0.1, color), border_radius=10),
                        ft.Container(expand=True)
                    ]),
                    ft.Text(value, size=28, weight="bold", color="#1a1a1a"),
                    ft.Text(title, size=14, color="grey", weight="bold"),
                    ft.Container(height=5),
                    ft.Text(subtitle, size=12, color=color)
                ], spacing=5),
                padding=20, bgcolor="white", border_radius=15,
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.05, "black")),
                expand=1
            )

        kpi_row = ft.Row([
            kpi_card("Toplam Hasta", str(patient_count), "%15 Artış (Bu Ay)", ft.Icons.PEOPLE, "blue"),
            kpi_card("Randevu Doluluğu", "%82", "Son 7 gün ortalaması", ft.Icons.TIMELAPSE, "orange"),
            kpi_card("Dönüşüm Oranı", "%12", "Bekleyen -> Tedavi", ft.Icons.TRENDING_UP, "green"),
        ], spacing=20)

        # --- KAYNAK ANALİZİ (Progress Bars) ---
        source_column = ft.Column(spacing=20)
        
        if not sources:
            source_column.controls.append(ft.Text("Henüz veri yok.", italic=True, color="grey"))
        else:
            max_val = max([s[1] for s in sources]) if sources else 1
            colors = ["teal", "blue", "orange", "purple", "red"]
            
            for i, (name, count) in enumerate(sources):
                color = colors[i % len(colors)]
                ratio = count / max_val
                
                source_column.controls.append(
                    ft.Column([
                        ft.Row([
                            ft.Text(name, weight="bold"),
                            ft.Text(f"{count} Hasta", color="grey", size=12)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.ProgressBar(value=ratio, color=color, bgcolor="#f0f0f0", height=10, border_radius=5)
                    ], spacing=5)
                )

        analysis_card = ft.Container(
            content=ft.Column([
                ft.Text("Hasta Kaynak Dağılımı", size=18, weight="bold"),
                ft.Divider(color="#f0f0f0"),
                ft.Container(height=10),
                source_column
            ]),
            padding=25, bgcolor="white", border_radius=15,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.05, "black")),
            expand=True
        )

        # Sağ taraf için (Örneğin Kampanyalar) boş bir placeholder kart
        campaign_card = ft.Container(
            content=ft.Column([
                ft.Text("Aktif Kampanyalar", size=18, weight="bold"),
                ft.Divider(color="#f0f0f0"),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.CAMPAIGN, color="orange"),
                    title=ft.Text("Bahar İndirimi"),
                    subtitle=ft.Text("Bitiş: 30 Nisan 2024"),
                    trailing=ft.Switch(value=True)
                ),
                 ft.ListTile(
                    leading=ft.Icon(ft.Icons.CAMPAIGN, color="grey"),
                    title=ft.Text("Diş Temizliği Kampanyası"),
                    subtitle=ft.Text("Bitiş: Geçmiş"),
                    trailing=ft.Switch(value=False)
                )
            ]),
            padding=25, bgcolor="white", border_radius=15,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.05, "black")),
            expand=True
        )

        return ft.View(
            "/crm",
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Text("CRM & Analiz", size=28, weight="bold", color="#1a1a1a"),
                        kpi_row,
                        ft.Container(height=10),
                        ft.Row([analysis_card, campaign_card], spacing=20, vertical_alignment=ft.CrossAxisAlignment.START)
                    ], spacing=20, scroll=ft.ScrollMode.AUTO),
                    padding=30, bgcolor="#f8f9fa", expand=True
                )
            ], padding=0
        )