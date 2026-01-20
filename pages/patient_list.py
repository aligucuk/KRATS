import flet as ft

class PatientListPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.active_patients_cache = []
        self.archived_patients_cache = []

        # Stil Tanımları
        self.card_style = {
            "bgcolor": "white",
            "border_radius": 12,
            "padding": 20,
            "shadow": ft.BoxShadow(blur_radius=15, color=ft.Colors.with_opacity(0.04, "black")),
            "border": ft.border.all(1, "#f0f0f0")
        }

        # UI Elemanları
        self.search_active = ft.TextField(
            hint_text="Hasta ara (İsim, TC, Tel...)", 
            prefix_icon=ft.Icons.SEARCH, 
            border_radius=12, 
            bgcolor="#f8f9fa", 
            border_color="transparent",
            filled=True,
            on_change=self.on_search_active,
            content_padding=15
        )
        
        self.search_archive = ft.TextField(
            hint_text="Arşivde ara...", 
            prefix_icon=ft.Icons.HISTORY, 
            border_radius=12,
            bgcolor="#f8f9fa",
            border_color="transparent",
            filled=True,
            on_change=self.on_search_archive
        )

        # Tablolar
        self.table_active = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("TC KİMLİK", size=12, color="grey", weight="bold")),
                ft.DataColumn(ft.Text("AD SOYAD", size=12, color="grey", weight="bold")),
                ft.DataColumn(ft.Text("TELEFON", size=12, color="grey", weight="bold")),
                ft.DataColumn(ft.Text("DURUM", size=12, color="grey", weight="bold")),
                ft.DataColumn(ft.Text("İŞLEMLER", size=12, color="grey", weight="bold")),
            ],
            heading_row_height=40,
            data_row_min_height=50,
            column_spacing=20,
            width=float("inf"),
            heading_row_color="#f8f9fa"
        )
        
        self.table_archive = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(c, size=12, color="grey", weight="bold")) for c in ["TC", "AD SOYAD", "TELEFON", "DURUM", "İŞLEMLER"]],
            heading_row_color="#f8f9fa", width=float("inf")
        )

    def view(self):
        self.load_active_data(update_ui=False)
        self.load_archive_data(update_ui=False)

        # Header Butonu
        add_btn = ft.ElevatedButton(
            "Yeni Hasta Kaydı", 
            icon=ft.Icons.ADD, 
            bgcolor="teal", 
            color="white", 
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=20),
            on_click=lambda _: self.page.go("/add_patient")
        )

        # Sekme İçeriği: Aktif Hastalar
        tab_active_content = ft.Container(
            content=ft.Column([
                ft.Row([self.search_active, add_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(color="transparent", height=10),
                ft.Column([self.table_active], scroll=ft.ScrollMode.AUTO, expand=True)
            ]),
            **self.card_style, expand=True
        )

        # Sekme İçeriği: Arşiv
        tab_archive_content = ft.Container(
            content=ft.Column([
                self.search_archive,
                ft.Divider(color="transparent", height=10),
                ft.Column([self.table_archive], scroll=ft.ScrollMode.AUTO, expand=True)
            ]),
            **self.card_style, expand=True
        )

        # Ana Tablar
        tabs = ft.Tabs(
            selected_index=0, animation_duration=300,
            indicator_color="teal", label_color="teal", unselected_label_color="grey",
            tabs=[
                ft.Tab(text="Aktif Hastalar", icon=ft.Icons.PEOPLE_OUTLINE, content=ft.Container(content=tab_active_content, padding=ft.padding.only(top=20))),
                ft.Tab(text="Arşivlenmiş", icon=ft.Icons.ARCHIVE_OUTLINED, content=ft.Container(content=tab_archive_content, padding=ft.padding.only(top=20)))
            ],
            expand=True
        )

        return ft.View(
            "/patient_list",
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Text("Hasta Listesi", size=24, weight="bold", color="#1a1a1a"),
                        tabs
                    ], expand=True),
                    padding=30, bgcolor="#f8f9fa", expand=True
                )
            ],
            padding=0
        )

    # --- LOJİK ---
    def load_active_data(self, update_ui=True):
        try:
            self.active_patients_cache = self.db.get_active_patients()
            self.render_active_table(self.active_patients_cache, update_ui)
        except: pass

    def load_archive_data(self, update_ui=True):
        try:
            self.archived_patients_cache = self.db.get_archived_patients()
            self.render_archive_table(self.archived_patients_cache, update_ui)
        except: pass

    def render_active_table(self, patients, update_ui=True):
        self.table_active.rows = []
        for p in patients:
            pid = p[0]
            status_text = p[7] if len(p) > 7 else "Aktif"
            
            # Renkli Durum Kutusu
            status_badge = ft.Container(
                content=ft.Text(status_text, size=11, color="green", weight="bold"),
                bgcolor=ft.Colors.GREEN_50, padding=ft.padding.symmetric(horizontal=10, vertical=5), border_radius=5
            )

            self.table_active.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(p[1], font_family="monospace")), # TC
                    ft.DataCell(ft.Row([
                        ft.CircleAvatar(content=ft.Text(p[2][:1]), radius=15, bgcolor="teal"),
                        ft.Text(p[2], weight="bold")
                    ], spacing=10)),
                    ft.DataCell(ft.Text(p[3])),
                    ft.DataCell(status_badge),
                    ft.DataCell(ft.Row([
                        ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_color="blue", tooltip="Detay/Düzenle", on_click=lambda _, x=pid: self.page.go(f"/patient_detail/{x}")),
                        ft.IconButton(ft.Icons.ARCHIVE_OUTLINED, icon_color="grey", tooltip="Arşivle", on_click=lambda _, x=pid: self.archive_patient_action(x))
                    ]))
                ])
            )
        if update_ui: self.table_active.update()

    def render_archive_table(self, patients, update_ui=True):
        self.table_archive.rows = []
        for p in patients:
            pid = p[0]
            self.table_archive.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(p[1], color="grey")),
                    ft.DataCell(ft.Text(p[2], color="grey")),
                    ft.DataCell(ft.Text(p[3], color="grey")),
                    ft.DataCell(ft.Text("Arşiv", italic=True, color="grey")),
                    ft.DataCell(ft.IconButton(ft.Icons.RESTORE, icon_color="green", tooltip="Geri Al", on_click=lambda _, x=pid: self.restore_patient_action(x)))
                ])
            )
        if update_ui: self.table_archive.update()

    def archive_patient_action(self, pid):
        self.db.archive_patient(pid)
        self.load_active_data(); self.load_archive_data()
    def restore_patient_action(self, pid):
        self.db.restore_patient(pid)
        self.load_active_data(); self.load_archive_data()
    def on_search_active(self, e):
        term = self.search_active.value.lower()
        self.render_active_table([p for p in self.active_patients_cache if term in str(p[1]).lower() or term in str(p[2]).lower()])
    def on_search_archive(self, e):
        term = self.search_archive.value.lower()
        self.render_archive_table([p for p in self.archived_patients_cache if term in str(p[1]).lower() or term in str(p[2]).lower()])