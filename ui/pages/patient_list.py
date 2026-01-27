"""
Patient List Page - Hasta Listesi
Gelişmiş arama, filtreleme ve toplu işlemler
"""

import flet as ft
from database.db_manager import DatabaseManager
from utils.logger import app_logger
from utils.encryption_manager import EncryptionManager



class PatientListPage:
    def __init__(self, page: ft.Page, db: DatabaseManager):
        self.page = page
        self.db = db
        self.encryption = EncryptionManager()
        
        # Filtreler
        self.current_filter = "active"
        self.search_term = ""
        self.selected_source = "all"
        self.selected_gender = "all"
        
        # Cache
        self.all_patients = []
        self.filtered_patients = []
        
        # UI Components
        self.search_field = ft.TextField(
            hint_text="Hasta ara (İsim, TC, Telefon...)",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=12,
            bgcolor="#f8f9fa",
            border_color="transparent",
            filled=True,
            on_change=self.on_search,
            expand=True
        )
        
        self.filter_tabs = ft.Tabs(
            selected_index=0,
            on_change=self.on_tab_change,
            tabs=[
                ft.Tab(text="Aktif Hastalar", icon=ft.Icons.PERSON),
                ft.Tab(text="Arşiv", icon=ft.Icons.ARCHIVE)
            ]
        )
        
        self.source_filter = ft.Dropdown(
            label="Kaynak",
            options=[
                ft.dropdown.Option("all", "Tümü"),
                ft.dropdown.Option("Google", "Google"),
                ft.dropdown.Option("Sosyal Medya", "Sosyal Medya"),
                ft.dropdown.Option("Tavsiye", "Tavsiye"),
                ft.dropdown.Option("Diğer", "Diğer")
            ],
            value="all",
            width=200,
            on_change=self.on_filter_change
        )
        
        self.gender_filter = ft.Dropdown(
            label="Cinsiyet",
            options=[
                ft.dropdown.Option("all", "Tümü"),
                ft.dropdown.Option("Erkek", "Erkek"),
                ft.dropdown.Option("Kadın", "Kadın")
            ],
            value="all",
            width=150,
            on_change=self.on_filter_change
        )
        
        self.patient_grid = ft.GridView(
            expand=True,
            runs_count=3,
            max_extent=400,
            child_aspect_ratio=1.2,
            spacing=15,
            run_spacing=15
        )
        
        self.stats_row = ft.Row(spacing=15)
        
    def view(self):
        """Ana görünüm"""
        self.load_patients()
        self.load_stats()
        
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.PEOPLE, color="teal", size=30),
                ft.Column([
                    ft.Text("Hasta Yönetimi", size=24, weight="bold"),
                    ft.Text(
                        f"{len(self.all_patients)} hasta kayıtlı",
                        size=12,
                        color="grey"
                    )
                ], spacing=0),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Yeni Hasta Ekle",
                    icon=ft.Icons.PERSON_ADD,
                    bgcolor="teal",
                    color="white",
                    on_click=lambda _: self.page.go("/add_patient")
                )
            ]),
            padding=20,
            bgcolor="white",
            border_radius=15
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
        
        # Filters
        filters_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    self.search_field,
                    self.source_filter,
                    self.gender_filter,
                    ft.IconButton(
                        ft.Icons.FILTER_ALT_OFF,
                        tooltip="Filtreleri Temizle",
                        on_click=self.clear_filters
                    )
                ]),
                self.filter_tabs
            ], spacing=10),
            padding=20,
            bgcolor="white",
            border_radius=15
        )
        
        # Patient Grid
        grid_container = ft.Container(
            content=self.patient_grid,
            padding=20,
            bgcolor="white",
            border_radius=15,
            expand=True
        )
        
        return ft.View(
            "/patient_list",
            controls=[
                ft.Container(
                    content=ft.Column([
                        header,
                        stats_section,
                        filters_section,
                        grid_container
                    ], spacing=15, expand=True),
                    padding=30,
                    bgcolor="#f8f9fa",
                    expand=True
                )
            ],
            padding=0
        )
    
    def load_patients(self):
        """Hastaları yükle"""
        try:
            # Veritabanından çek (already decrypted by db_manager)
            if self.current_filter == "active":
                self.all_patients = self.db.get_active_patients()
            else:
                self.all_patients = self.db.get_archived_patients()

            # No need to decrypt - get_active_patients() already returns decrypted dict data
            self.apply_filters()

        except Exception as e:
            app_logger.error(f"Load patients error: {e}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Hasta yükleme hatası: {e}"),
                bgcolor="red"
            ))
    
    def apply_filters(self):
        """Filtreleri uygula"""
        try:
            self.filtered_patients = self.all_patients
            
            # Arama
            if self.search_term:
                term = self.search_term.lower()
                self.filtered_patients = [
                    p for p in self.filtered_patients
                    if term in (p.get('full_name', '') or '').lower() or
                       term in (p.get('tc_no', '') or '').lower() or
                       term in (p.get('phone', '') or '').lower()
                ]

            # Kaynak filtresi
            if self.selected_source != "all":
                self.filtered_patients = [
                    p for p in self.filtered_patients
                    if p.get('source') == self.selected_source
                ]

            # Cinsiyet filtresi
            if self.selected_gender != "all":
                self.filtered_patients = [
                    p for p in self.filtered_patients
                    if p.get('gender') == self.selected_gender
                ]
            
            self.render_patients()
            
        except Exception as e:
            app_logger.error(f"Apply filters error: {e}")
    
    def render_patients(self):
        """Hastaları göster"""
        try:
            self.patient_grid.controls.clear()
            
            if not self.filtered_patients:
                self.patient_grid.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.SEARCH_OFF, size=80, color="grey"),
                            ft.Text("Hasta bulunamadı", size=18, color="grey"),
                            ft.Text(
                                "Arama terimini değiştirin veya yeni hasta ekleyin",
                                size=12,
                                color="grey"
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.center,
                        expand=True
                    )
                )
            else:
                for patient in self.filtered_patients:
                    self.patient_grid.controls.append(
                        self._patient_card(patient)
                    )
            
            self.patient_grid.update()
            
        except Exception as e:
            app_logger.error(f"Render patients error: {e}")
    
    def _patient_card(self, patient):
        """Hasta kartı oluştur"""
        # Patient is now a dict, use dict access
        full_name = patient.get('full_name', '')
        initial = full_name[0].upper() if full_name else "?"

        # Yaş hesapla
        age = ""
        birth_date = patient.get('birth_date')
        if birth_date:
            try:
                from datetime import datetime
                birth = datetime.strptime(str(birth_date), "%Y-%m-%d")
                age_years = (datetime.now() - birth).days // 365
                age = f"{age_years} yaş"
            except:
                pass

        # Durum rengi
        status_colors = {
            "Yeni": "blue",
            "Aktif": "green",
            "Beklemede": "orange",
            "Arşiv": "grey"
        }
        status = patient.get('status', 'Aktif')
        status_color = status_colors.get(status, "grey")

        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    # Header
                    ft.Row([
                        ft.CircleAvatar(
                            content=ft.Text(initial, size=20, weight="bold"),
                            bgcolor="teal",
                            radius=25
                        ),
                        ft.Container(expand=True),
                        ft.Container(
                            content=ft.Text(status, size=10, color="white"),
                            bgcolor=status_color,
                            padding=5,
                            border_radius=5
                        )
                    ]),
                    ft.Divider(),
                    # Bilgiler
                    ft.Column([
                        ft.Text(full_name, size=16, weight="bold"),
                        ft.Row([
                            ft.Icon(ft.Icons.PHONE, size=14, color="grey"),
                            ft.Text(patient.get('phone') or "-", size=12, color="grey")
                        ], spacing=5),
                        ft.Row([
                            ft.Icon(ft.Icons.CAKE, size=14, color="grey"),
                            ft.Text(age or "-", size=12, color="grey")
                        ], spacing=5),
                        ft.Row([
                            ft.Icon(ft.Icons.SOURCE, size=14, color="grey"),
                            ft.Text(patient.get('source') or "-", size=12, color="grey")
                        ], spacing=5)
                    ], spacing=5),
                    ft.Container(expand=True),
                    # Aksiyonlar
                    ft.Row([
                        ft.TextButton(
                            "Detay",
                            icon=ft.Icons.VISIBILITY,
                            on_click=lambda _, pid=patient.get('id'): self.page.go(f"/patient_detail/{pid}")
                        ),
                        ft.Container(expand=True),
                        ft.IconButton(
                            ft.Icons.ARCHIVE if self.current_filter == "active" else ft.Icons.UNARCHIVE,
                            tooltip="Arşivle" if self.current_filter == "active" else "Geri Al",
                            on_click=lambda _, pid=patient.get('id'): self.toggle_archive(pid)
                        )
                    ])
                ], spacing=10),
                padding=15
            ),
            elevation=2
        )
    
    def load_stats(self):
        """İstatistikleri yükle"""
        try:
            total = len(self.all_patients)
            new_count = len([p for p in self.all_patients if p.get('status') == "Yeni"])
            active_count = len([p for p in self.all_patients if p.get('status') == "Aktif"])

            # Kaynak dağılımı
            sources = {}
            for p in self.all_patients:
                source = p.get('source', 'Bilinmiyor')
                sources[source] = sources.get(source, 0) + 1

            top_source = max(sources.items(), key=lambda x: x[1]) if sources else ("", 0)
            
            self.stats_row.controls = [
                self._stat_badge("Toplam", str(total), "blue"),
                self._stat_badge("Yeni", str(new_count), "green"),
                self._stat_badge("Aktif", str(active_count), "orange"),
                self._stat_badge("En Çok", f"{top_source[0]} ({top_source[1]})", "purple")
            ]
            
        except Exception as e:
            app_logger.error(f"Load stats error: {e}")
    
    def _stat_badge(self, label, value, color):
        """İstatistik rozeti"""
        return ft.Container(
            content=ft.Column([
                ft.Text(value, size=20, weight="bold", color=color),
                ft.Text(label, size=12, color="grey")
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            padding=15,
            bgcolor=ft.Colors.with_opacity(0.1, color),
            border_radius=10,
            border=ft.border.all(1, color)
        )
    
    def on_search(self, e):
        """Arama"""
        self.search_term = e.control.value
        self.apply_filters()
    
    def on_tab_change(self, e):
        """Sekme değişimi"""
        self.current_filter = "active" if e.control.selected_index == 0 else "archived"
        self.load_patients()
        self.load_stats()
    
    def on_filter_change(self, e):
        """Filtre değişimi"""
        self.selected_source = self.source_filter.value
        self.selected_gender = self.gender_filter.value
        self.apply_filters()
    
    def clear_filters(self, e):
        """Filtreleri temizle"""
        self.search_field.value = ""
        self.source_filter.value = "all"
        self.gender_filter.value = "all"
        self.search_term = ""
        self.selected_source = "all"
        self.selected_gender = "all"
        self.apply_filters()
        self.page.update()
    
    def toggle_archive(self, patient_id):
        """Arşivleme durumunu değiştir"""
        try:
            if self.current_filter == "active":
                self.db.archive_patient(patient_id)
                message = "Hasta arşivlendi"
            else:
                self.db.restore_patient(patient_id)
                message = "Hasta geri alındı"
            
            self.load_patients()
            self.load_stats()
            
            self.page.open(ft.SnackBar(
                ft.Text(message),
                bgcolor="green"
            ))
            
        except Exception as e:
            app_logger.error(f"Toggle archive error: {e}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Hata: {e}"),
                bgcolor="red"
            ))