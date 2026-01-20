import flet as ft

class InventoryPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        
        # Form
        self.p_name = ft.TextField(label="Ürün Adı", expand=2, border_radius=10, filled=True, bgcolor="#f8f9fa", border_color="transparent")
        self.p_qty = ft.TextField(label="Adet", expand=1, border_radius=10, filled=True, bgcolor="#f8f9fa", border_color="transparent", keyboard_type=ft.KeyboardType.NUMBER)
        
        # DÜZELTME: Varsayılan seçili değil, Hint Text var
        self.p_unit = ft.Dropdown(
            options=[ft.dropdown.Option("Adet"), ft.dropdown.Option("Kutu"), ft.dropdown.Option("Lt")], 
            label="Birim",
            hint_text="Seçiniz...",
            value=None, 
            expand=1, border_radius=10, filled=True, bgcolor="#f8f9fa", border_color="transparent"
        )
        
        # YENİ ALAN: Kritik Stok Girişi
        self.p_min = ft.TextField(
            label="Min. Stok", 
            value="10", 
            expand=1, 
            border_radius=10, filled=True, bgcolor="#f8f9fa", border_color="transparent",
            keyboard_type=ft.KeyboardType.NUMBER,
            helper_text="Uyarı sınırı"
        )

        self.table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ÜRÜN ADI", weight="bold")),
                ft.DataColumn(ft.Text("STOK", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("BİRİM", weight="bold")),
                ft.DataColumn(ft.Text("DURUM", weight="bold")),
                ft.DataColumn(ft.Text("SİL", weight="bold")),
            ],
            width=float("inf"), heading_row_color="#f8f9fa"
        )
        
        self.alert_container = ft.Column()

    def view(self):
        self.load_data()
        
        add_card = ft.Container(
            content=ft.Row([
                self.p_name, self.p_qty, self.p_unit, self.p_min, # Min stok eklendi
                ft.ElevatedButton("Stok Ekle", icon=ft.Icons.ADD, bgcolor="teal", color="white", style=ft.ButtonStyle(padding=20, shape=ft.RoundedRectangleBorder(radius=10)), on_click=self.add_product)
            ]),
            padding=20, bgcolor="white", border_radius=15,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.05, "black"))
        )

        return ft.View(
            "/inventory",
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Text("Stok Takibi", size=28, weight="bold", color="#1a1a1a"),
                        self.alert_container,
                        add_card,
                        ft.Container(
                            content=self.table,
                            padding=20, bgcolor="white", border_radius=15, expand=True,
                            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.05, "black"))
                        )
                    ], spacing=20, expand=True),
                    padding=30, bgcolor="#f8f9fa", expand=True
                )
            ], padding=0
        )

    def load_data(self):
        self.table.rows = []
        self.alert_container.controls.clear()
        
        products = self.db.get_inventory()
        critical_items = []

        for p in products:
            # p: id, name, unit, qty, threshold
            qty = p[3]
            threshold = p[4] if len(p) > 4 else 10 # DB'den geliyorsa al, yoksa 10
            
            is_low = qty <= threshold
            if is_low: critical_items.append(p[1])

            status_color = "red" if is_low else "green"
            status_text = "KRİTİK" if is_low else "Yeterli"

            self.table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(p[1], weight="bold")),
                    ft.DataCell(ft.Text(str(qty), size=16, color=status_color, weight="bold")),
                    ft.DataCell(ft.Text(p[2])),
                    ft.DataCell(ft.Container(content=ft.Text(status_text, size=10, color="white"), bgcolor=status_color, padding=5, border_radius=5)),
                    ft.DataCell(ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="red", on_click=lambda e, pid=p[0]: self.del_product(pid)))
                ])
            )
        
        if critical_items:
            self.alert_container.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.WARNING, color="orange"),
                        ft.Text(f"Dikkat: {len(critical_items)} ürün kritik seviyenin altında!", weight="bold", color="orange")
                    ]),
                    padding=15, bgcolor=ft.Colors.ORANGE_50, border_radius=10, border=ft.border.all(1, "orange")
                )
            )

        try: 
            self.table.update()
            self.alert_container.update()
        except: pass

    def add_product(self, e):
        try:
            qty = int(self.p_qty.value)
            threshold = int(self.p_min.value) # Kullanıcının girdiği eşik değeri
            if not self.p_unit.value:
                self.page.open(ft.SnackBar(ft.Text("Lütfen birim seçin!"), bgcolor="red"))
                return
                
            self.db.add_product(self.p_name.value, self.p_unit.value, qty, threshold)
            
            # Temizlik
            self.p_name.value = ""
            self.p_qty.value = ""
            self.p_min.value = "10"
            self.p_unit.value = None
            self.load_data()
        except Exception as ex: 
            print(ex)
            self.page.open(ft.SnackBar(ft.Text("Hata: Sayısal değerleri kontrol edin"), bgcolor="red"))

    def del_product(self, pid):
        self.db.delete_product(pid)
        self.load_data()