import flet as ft
from datetime import datetime

class FinancePage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db

        # Input Stilleri
        self.input_style = {
            "border_radius": 10, "filled": True, 
            "bgcolor": "#f8f9fa", "border_color": "transparent", "content_padding": 15
        }
        
        self.txt_amount = ft.TextField(label="Tutar", suffix_text="₺", keyboard_type=ft.KeyboardType.NUMBER, width=150, **self.input_style)
        self.txt_desc = ft.TextField(label="Açıklama (Örn: Kira, Muayene)", expand=True, **self.input_style)
        self.dd_type = ft.Dropdown(
            options=[ft.dropdown.Option("Gelir"), ft.dropdown.Option("Gider")],
            value="Gelir", width=120, **self.input_style
        )
        
        self.table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("TARİH", size=11, color="grey", weight="bold")),
                ft.DataColumn(ft.Text("TÜR", size=11, color="grey", weight="bold")),
                ft.DataColumn(ft.Text("AÇIKLAMA", size=11, color="grey", weight="bold")),
                ft.DataColumn(ft.Text("TUTAR", size=11, color="grey", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("İŞLEM", size=11, color="grey", weight="bold")),
            ],
            width=float("inf"), heading_row_color="#f8f9fa",
        )

    def view(self):
        self.load_data()

        # --- ÜST BİLGİ KARTLARI ---
        self.card_income = self._summary_card("Toplam Gelir", "₺0", "green", ft.Icons.ARROW_UPWARD)
        self.card_expense = self._summary_card("Toplam Gider", "₺0", "red", ft.Icons.ARROW_DOWNWARD)
        self.card_net = self._summary_card("Net Durum", "₺0", "blue", ft.Icons.ACCOUNT_BALANCE)

        summary_row = ft.Row([self.card_income, self.card_expense, self.card_net], spacing=20)

        # --- İŞLEM EKLEME PANELİ ---
        add_panel = ft.Container(
            content=ft.Row([
                self.dd_type,
                self.txt_amount,
                self.txt_desc,
                ft.ElevatedButton("Ekle", icon=ft.Icons.ADD, bgcolor="teal", color="white", style=ft.ButtonStyle(padding=20, shape=ft.RoundedRectangleBorder(radius=10)), on_click=self.add_transaction)
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=20, bgcolor="white", border_radius=15,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.05, "black"))
        )

        # --- TABLO ALANI ---
        table_card = ft.Container(
            content=ft.Column([
                ft.Text("Son İşlemler", size=16, weight="bold"),
                ft.Divider(color="#f0f0f0"),
                ft.Column([self.table], scroll=ft.ScrollMode.AUTO, expand=True)
            ]),
            padding=20, bgcolor="white", border_radius=15, expand=True,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.05, "black"))
        )

        return ft.View(
            "/finance",
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Text("Finans Yönetimi", size=28, weight="bold", color="#1a1a1a"),
                        summary_row,
                        add_panel,
                        table_card
                    ], spacing=20, expand=True),
                    padding=30, bgcolor="#f8f9fa", expand=True
                )
            ], padding=0
        )

    def _summary_card(self, title, value, color, icon):
        return ft.Container(
            content=ft.Row([
                ft.Container(content=ft.Icon(icon, color=color), padding=10, bgcolor=ft.Colors.with_opacity(0.1, color), border_radius=10),
                ft.Column([
                    ft.Text(title, size=12, color="grey"),
                    ft.Text(value, size=20, weight="bold", color=color)
                ], spacing=0)
            ]),
            padding=20, bgcolor="white", border_radius=12, expand=1,
            shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.05, "black"))
        )

    def load_data(self):
        self.table.rows = []
        transactions = self.db.get_transactions()
        income = 0
        expense = 0
        
        for t in transactions:
            # t: id, type, cat, amount, desc, date
            amount = t[3]
            is_income = (t[1] == "Gelir")
            
            if is_income: income += amount
            else: expense += amount
            
            color = "green" if is_income else "red"
            icon = ft.Icons.ARROW_UPWARD if is_income else ft.Icons.ARROW_DOWNWARD

            self.table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(t[5][:10], size=12)),
                    ft.DataCell(ft.Container(
                        content=ft.Row([ft.Icon(icon, size=12, color=color), ft.Text(t[1], color=color, size=12)], spacing=5),
                        bgcolor=ft.Colors.with_opacity(0.1, color), padding=5, border_radius=5
                    )),
                    ft.DataCell(ft.Text(t[4], size=13)),
                    ft.DataCell(ft.Text(f"{amount:,.2f} ₺", weight="bold", color="#333")),
                    ft.DataCell(ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="red", icon_size=18, on_click=lambda e, tid=t[0]: self.delete_trans(tid)))
                ])
            )
        
        # Kartları güncelle
        net = income - expense
        if hasattr(self, 'card_income'):
            self.card_income.content.controls[1].controls[1].value = f"₺{income:,.2f}"
            self.card_expense.content.controls[1].controls[1].value = f"₺{expense:,.2f}"
            self.card_net.content.controls[1].controls[1].value = f"₺{net:,.2f}"
            self.card_net.content.controls[1].controls[1].color = "green" if net >=0 else "red"
            self.card_income.update()
            self.card_expense.update()
            self.card_net.update()

        try: self.table.update()
        except: pass

    def add_transaction(self, e):
        try:
            val = float(self.txt_amount.value)
            self.db.add_transaction(self.dd_type.value, "Genel", val, self.txt_desc.value, datetime.now())
            self.txt_amount.value = ""
            self.txt_desc.value = ""
            self.load_data()
        except: pass

    def delete_trans(self, tid):
        self.db.delete_transaction(tid)
        self.load_data()