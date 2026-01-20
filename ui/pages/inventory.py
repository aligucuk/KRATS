"""
Inventory Page - Stok Yönetimi
Malzeme takibi, düşük stok uyarıları, stok hareketleri
"""

import flet as ft
from datetime import datetime
from database.db_manager import DatabaseManager
from database.models import Product, InventoryLog
from utils.logger import app_logger


class InventoryPage:
    def __init__(self, page: ft.Page, db: DatabaseManager):
        self.page = page
        self.db = db
        
        # UI Components
        self.alert_container = ft.Column(spacing=10)
        self.products_grid = ft.GridView(
            expand=True,
            runs_count=3,
            max_extent=350,
            child_aspect_ratio=1.1,
            spacing=15,
            run_spacing=15
        )
        
        self.stats_row = ft.Row(spacing=15)
        
        # Yeni ürün form alanları
        self.txt_product_name = ft.TextField(
            label="Ürün Adı *",
            width=300
        )
        
        self.dd_unit = ft.Dropdown(
            label="Birim *",
            options=[
                ft.dropdown.Option("Adet"),
                ft.dropdown.Option("Kutu"),
                ft.dropdown.Option("Paket"),
                ft.dropdown.Option("Litre"),
                ft.dropdown.Option("Kilogram")
            ],
            value="Adet",
            width=150
        )
        
        self.txt_quantity = ft.TextField(
            label="Miktar *",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=150
        )
        
        self.txt_threshold = ft.TextField(
            label="Kritik Stok Seviyesi *",
            keyboard_type=ft.KeyboardType.NUMBER,
            value="10",
            width=150,
            hint_text="Bu değerin altında uyarı"
        )
        
    def view(self):
        """Ana görünüm"""
        self.load_data()
        
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.INVENTORY_2, color="teal", size=30),
                ft.Column([
                    ft.Text("Stok Yönetimi", size=24, weight="bold"),
                    ft.Text("Malzeme ve ürün takibi", size=12, color="grey")
                ], spacing=0),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Yeni Ürün Ekle",
                    icon=ft.Icons.ADD,
                    bgcolor="teal",
                    color="white",
                    on_click=self.open_new_product_dialog
                )
            ]),
            padding=20,
            bgcolor="white",
            border_radius=15
        )
        
        # Alerts (Düşük stok uyarıları)
        alerts_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.WARNING, color="orange", size=20),
                    ft.Text("Stok Uyarıları", weight="bold")
                ], spacing=10),
                ft.Divider(),
                self.alert_container
            ]),
            padding=20,
            bgcolor=ft.Colors.ORANGE_50,
            border_radius=15,
            visible=False  # Sadece uyarı varsa görünür
        )
        
        # Stats
        stats_section = ft.Container(
            content=ft.Column([
                ft.Text("İstatistikler", weight="bold"),
                self.stats_row
            ], spacing=10),
            padding=20,
            bgcolor="white",
            border_radius=15
        )
        
        # Products Grid
        products_section = ft.Container(
            content=ft.Column([
                ft.Text("Ürün Listesi", size=16, weight="bold"),
                ft.Divider(),
                self.products_grid
            ]),
            padding=20,
            bgcolor="white",
            border_radius=15,
            expand=True
        )
        
        return ft.View(
            "/inventory",
            controls=[
                ft.Container(
                    content=ft.Column([
                        header,
                        alerts_section,
                        stats_section,
                        products_section
                    ], spacing=15, expand=True),
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
            self.load_alerts()
            self.load_stats()
            self.load_products()
            
        except Exception as e:
            app_logger.error(f"Inventory data loading error: {e}")
    
    def load_alerts(self):
        """Düşük stok uyarılarını yükle"""
        try:
            self.alert_container.controls.clear()
            
            low_stock_products = self.db.get_low_stock_products()
            
            if not low_stock_products:
                self.alert_container.parent.visible = False
                return
            
            self.alert_container.parent.visible = True
            
            for product in low_stock_products:
                self.alert_container.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.WARNING_AMBER, color="orange", size=20),
                            ft.Text(
                                f"{product.name} - Kalan: {product.quantity} {product.unit}",
                                weight="bold"
                            ),
                            ft.Container(expand=True),
                            ft.TextButton(
                                "Stok Ekle",
                                on_click=lambda _, pid=product.id: self.quick_add_stock(pid)
                            )
                        ]),
                        padding=10,
                        bgcolor="white",
                        border_radius=8
                    )
                )
            
        except Exception as e:
            app_logger.error(f"Load alerts error: {e}")
    
    def load_stats(self):
        """İstatistikleri yükle"""
        try:
            products = self.db.get_all_products()
            
            total_products = len(products)
            low_stock_count = len(self.db.get_low_stock_products())
            total_value = sum([p.quantity * 10 for p in products])  # Demo fiyat
            
            self.stats_row.controls = [
                self._stat_badge("Toplam Ürün", str(total_products), "blue"),
                self._stat_badge("Kritik Seviye", str(low_stock_count), "orange"),
                self._stat_badge("Tahmini Değer", f"₺{total_value:,.0f}", "green")
            ]
            
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
            width=150
        )
    
    def load_products(self):
        """Ürünleri yükle"""
        try:
            self.products_grid.controls.clear()
            
            products = self.db.get_all_products()
            
            if not products:
                self.products_grid.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.INVENTORY, size=60, color="grey"),
                            ft.Text("Henüz ürün eklenmemiş", color="grey")
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.center,
                        expand=True
                    )
                )
            else:
                for product in products:
                    self.products_grid.controls.append(
                        self._product_card(product)
                    )
            
            self.products_grid.update()
            
        except Exception as e:
            app_logger.error(f"Load products error: {e}")
    
    def _product_card(self, product):
        """Ürün kartı"""
        # Stok durumu
        is_low = product.quantity <= product.threshold
        stock_color = "red" if is_low else "green"
        stock_status = "KRİTİK" if is_low else "Yeterli"
        
        # Stok çubuğu
        stock_percentage = min((product.quantity / product.threshold * 100) if product.threshold > 0 else 100, 100)
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    # Header
                    ft.Row([
                        ft.Icon(ft.Icons.INVENTORY_2, color="teal", size=30),
                        ft.Container(expand=True),
                        ft.Container(
                            content=ft.Text(stock_status, size=10, color="white"),
                            bgcolor=stock_color,
                            padding=5,
                            border_radius=5
                        )
                    ]),
                    ft.Divider(),
                    # Ürün bilgileri
                    ft.Text(product.name, size=16, weight="bold"),
                    ft.Row([
                        ft.Icon(ft.Icons.INVENTORY, size=14, color="grey"),
                        ft.Text(f"{product.quantity} {product.unit}", size=14, color="grey")
                    ], spacing=5),
                    # Stok çubuğu
                    ft.Column([
                        ft.Row([
                            ft.Text("Stok Durumu", size=11, color="grey"),
                            ft.Container(expand=True),
                            ft.Text(f"%{stock_percentage:.0f}", size=11, color="grey")
                        ]),
                        ft.ProgressBar(
                            value=stock_percentage / 100,
                            color=stock_color,
                            bgcolor="#f0f0f0",
                            height=8,
                            border_radius=4
                        )
                    ], spacing=5),
                    ft.Container(expand=True),
                    # Aksiyonlar
                    ft.Row([
                        ft.IconButton(
                            ft.Icons.ADD_CIRCLE,
                            tooltip="Stok Ekle",
                            icon_color="green",
                            on_click=lambda _, pid=product.id: self.quick_add_stock(pid)
                        ),
                        ft.IconButton(
                            ft.Icons.REMOVE_CIRCLE,
                            tooltip="Stok Çıkar",
                            icon_color="orange",
                            on_click=lambda _, pid=product.id: self.quick_remove_stock(pid)
                        ),
                        ft.Container(expand=True),
                        ft.IconButton(
                            ft.Icons.DELETE,
                            tooltip="Sil",
                            icon_color="red",
                            on_click=lambda _, pid=product.id: self.delete_product(pid)
                        )
                    ], spacing=5)
                ], spacing=10),
                padding=15
            ),
            elevation=2
        )
    
    def open_new_product_dialog(self, e):
        """Yeni ürün dialogu"""
        # Form sıfırla
        self.txt_product_name.value = ""
        self.txt_quantity.value = ""
        self.txt_threshold.value = "10"
        self.dd_unit.value = "Adet"
        
        dialog = ft.AlertDialog(
            title=ft.Text("Yeni Ürün Ekle"),
            content=ft.Container(
                content=ft.Column([
                    self.txt_product_name,
                    ft.Row([
                        self.txt_quantity,
                        self.dd_unit
                    ], spacing=10),
                    self.txt_threshold
                ], tight=True),
                width=400
            ),
            actions=[
                ft.TextButton("İptal", on_click=lambda _: self.page.close(dialog)),
                ft.ElevatedButton(
                    "Ekle",
                    icon=ft.Icons.SAVE,
                    bgcolor="teal",
                    color="white",
                    on_click=lambda _: self.save_product(dialog)
                )
            ]
        )
        
        self.page.open(dialog)
    
    def save_product(self, dialog):
        """Ürünü kaydet"""
        try:
            # Validasyon
            if not self.txt_product_name.value:
                self.page.open(ft.SnackBar(
                    ft.Text("Lütfen ürün adı girin"),
                    bgcolor="red"
                ))
                return
            
            if not self.txt_quantity.value:
                self.page.open(ft.SnackBar(
                    ft.Text("Lütfen miktar girin"),
                    bgcolor="red"
                ))
                return
            
            try:
                quantity = int(self.txt_quantity.value)
                threshold = int(self.txt_threshold.value)
            except ValueError:
                self.page.open(ft.SnackBar(
                    ft.Text("Miktar ve eşik değeri sayısal olmalı"),
                    bgcolor="red"
                ))
                return
            
            # Product objesi oluştur
            product = Product(
                id=None,
                name=self.txt_product_name.value,
                unit=self.dd_unit.value,
                quantity=quantity,
                threshold=threshold
            )
            
            # Veritabanına kaydet
            product_id = self.db.add_product(product)
            
            # Stok hareketi kaydı
            log = InventoryLog(
                id=None,
                product_id=product_id,
                user_id=self.page.session.get("user_id"),
                patient_id=None,
                quantity=quantity,
                date=datetime.now()
            )
            self.db.add_inventory_log(log)
            
            # Dialog kapat ve verileri yenile
            self.page.close(dialog)
            self.load_data()
            
            self.page.open(ft.SnackBar(
                ft.Text("✅ Ürün başarıyla eklendi"),
                bgcolor="green"
            ))
            
        except Exception as e:
            app_logger.error(f"Save product error: {e}")
            self.page.open(ft.SnackBar(
                ft.Text(f"❌ Kayıt hatası: {e}"),
                bgcolor="red"
            ))
    
    def quick_add_stock(self, product_id):
        """Hızlı stok ekleme"""
        txt_qty = ft.TextField(
            label="Eklenecek Miktar",
            keyboard_type=ft.KeyboardType.NUMBER,
            autofocus=True
        )
        
        def add(e):
            try:
                qty = int(txt_qty.value)
                self.db.update_product_quantity(product_id, qty, add=True)
                
                # Log kaydı
                product = self.db.get_product_by_id(product_id)
                log = InventoryLog(
                    id=None,
                    product_id=product_id,
                    user_id=self.page.session.get("user_id"),
                    patient_id=None,
                    quantity=qty,
                    date=datetime.now()
                )
                self.db.add_inventory_log(log)
                
                self.page.close(dialog)
                self.load_data()
                
                self.page.open(ft.SnackBar(
                    ft.Text(f"Stok güncellendi: +{qty}"),
                    bgcolor="green"
                ))
                
            except Exception as ex:
                app_logger.error(f"Add stock error: {ex}")
                self.page.open(ft.SnackBar(
                    ft.Text(f"Hata: {ex}"),
                    bgcolor="red"
                ))
        
        dialog = ft.AlertDialog(
            title=ft.Text("Stok Ekle"),
            content=txt_qty,
            actions=[
                ft.TextButton("İptal", on_click=lambda _: self.page.close(dialog)),
                ft.ElevatedButton("Ekle", bgcolor="green", color="white", on_click=add)
            ]
        )
        
        self.page.open(dialog)
    
    def quick_remove_stock(self, product_id):
        """Hızlı stok çıkarma"""
        txt_qty = ft.TextField(
            label="Çıkarılacak Miktar",
            keyboard_type=ft.KeyboardType.NUMBER,
            autofocus=True
        )
        
        def remove(e):
            try:
                qty = int(txt_qty.value)
                self.db.update_product_quantity(product_id, qty, add=False)
                
                # Log kaydı
                log = InventoryLog(
                    id=None,
                    product_id=product_id,
                    user_id=self.page.session.get("user_id"),
                    patient_id=None,
                    quantity=-qty,
                    date=datetime.now()
                )
                self.db.add_inventory_log(log)
                
                self.page.close(dialog)
                self.load_data()
                
                self.page.open(ft.SnackBar(
                    ft.Text(f"Stok güncellendi: -{qty}"),
                    bgcolor="orange"
                ))
                
            except Exception as ex:
                app_logger.error(f"Remove stock error: {ex}")
                self.page.open(ft.SnackBar(
                    ft.Text(f"Hata: {ex}"),
                    bgcolor="red"
                ))
        
        dialog = ft.AlertDialog(
            title=ft.Text("Stok Çıkar"),
            content=txt_qty,
            actions=[
                ft.TextButton("İptal", on_click=lambda _: self.page.close(dialog)),
                ft.ElevatedButton("Çıkar", bgcolor="orange", color="white", on_click=remove)
            ]
        )
        
        self.page.open(dialog)
    
    def delete_product(self, product_id):
        """Ürünü sil"""
        def confirm_delete(e):
            try:
                self.db.delete_product(product_id)
                
                self.page.close(dialog)
                self.load_data()
                
                self.page.open(ft.SnackBar(
                    ft.Text("Ürün silindi"),
                    bgcolor="green"
                ))
                
            except Exception as ex:
                app_logger.error(f"Delete product error: {ex}")
                self.page.open(ft.SnackBar(
                    ft.Text(f"Silme hatası: {ex}"),
                    bgcolor="red"
                ))
        
        dialog = ft.AlertDialog(
            title=ft.Text("Ürünü Sil"),
            content=ft.Text("Bu ürünü silmek istediğinizden emin misiniz?"),
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