import flet as ft
import threading
import time
from datetime import datetime

class TVDisplayPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.is_running = True 
        
        # UI Elemanları
        self.current_card_content = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.next_patients_list = ft.Column(spacing=15)
        self.lbl_time = ft.Text(size=40, weight="bold", color="white")

    def view(self):
        self.page.title = "Klinik Bekleme Ekranı"
        self.page.on_route_change = self._handle_route_change
        
        # --- Sol Panel (Aktif Hasta) - Tasarım İyileştirildi ---
        left_panel = ft.Container(
            content=ft.Column([
                ft.Text("ŞU AN GÖRÜŞÜLEN", size=24, weight="w300", color="white70"),
                ft.Container(height=20),
                self.current_card_content,
                ft.Container(expand=True),
                ft.Divider(color="white24"),
                ft.Row([
                    ft.Icon(ft.Icons.ACCESS_TIME, size=30, color="teal"),
                    self.lbl_time
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=6, 
            bgcolor="#111827", # Çok koyu lacivert/siyah
            padding=50, 
            border_radius=0, # Sol taraf tam kaplasın
        )

        # --- Sağ Panel (Bekleyenler) - Tasarım İyileştirildi ---
        right_panel = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text("SIRADAKİ HASTALAR", size=20, weight="bold", color="#111827"),
                    bgcolor="teal", padding=15, border_radius=10, alignment=ft.alignment.center
                ),
                ft.Container(height=20),
                self.next_patients_list
            ]),
            expand=4, 
            bgcolor="#f3f4f6", # Açık gri kontrast
            padding=30, 
            border_radius=0
        )

        if not any(t.name == "TVLoop" for t in threading.enumerate()):
            threading.Thread(target=self.update_loop, name="TVLoop", daemon=True).start()

        return ft.View(
            "/tv_display",
            [ft.Row([left_panel, right_panel], expand=True, spacing=0)],
            padding=0
        )

    def _handle_route_change(self, e):
        if self.page.route != "/tv_display":
            self.is_running = False

    def update_loop(self):
        while self.is_running:
            if self.page.route != "/tv_display": break
                
            try:
                now_str = datetime.now().strftime("%H:%M")
                appointments = self.db.get_todays_appointments()
                
                current_p = None
                waiting_list = []

                if appointments:
                    for app in appointments:
                        if app[3] == "Görüşülüyor":
                            current_p = app
                            break
                    if not current_p:
                        for app in appointments:
                            if app[3] == "Bekliyor":
                                current_p = app
                                break 
                    
                    for app in appointments:
                        if app[3] == "Bekliyor" and (not current_p or app[0] != current_p[0]):
                            waiting_list.append(app)

                self.lbl_time.value = now_str
                self._update_ui_components(current_p, waiting_list)
                self.page.update()

            except Exception as e:
                print(f"TV Error: {e}")
            
            time.sleep(5) 

    def _update_ui_components(self, current, waiting):
        # Aktif Hasta Kartı (Modern)
        if current:
            self.current_card_content.controls = [
                ft.Container(
                    content=ft.Text(str(current[1])[0], size=60, weight="bold", color="white"),
                    bgcolor="teal", width=120, height=120, border_radius=60, alignment=ft.alignment.center,
                    shadow=ft.BoxShadow(blur_radius=20, color="teal")
                ),
                ft.Container(height=30),
                ft.Text(current[1], size=50, weight="bold", color="white", text_align="center"),
                ft.Text("Lütfen İçeri Giriniz", color="teal", size=24, weight="w300"),
            ]
        else:
            self.current_card_content.controls = [
                ft.Icon(ft.Icons.COFFEE, size=100, color="white24"),
                ft.Container(height=20),
                ft.Text("Bekleyen hasta yok", size=24, color="white24")
            ]

        # Bekleyenler Listesi (Modern Kartlar)
        self.next_patients_list.controls.clear()
        if not waiting:
            self.next_patients_list.controls.append(ft.Text("Liste boş.", color="grey"))
        else:
            for i, p in enumerate(waiting[:5]):
                try: t_str = p[2].strftime("%H:%M") 
                except: t_str = str(p[2])[-5:] 
                
                self.next_patients_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Row([
                                ft.Container(
                                    content=ft.Text(str(i+1), weight="bold", color="white"),
                                    bgcolor="black", width=30, height=30, border_radius=15, alignment=ft.alignment.center
                                ),
                                ft.Text(p[1], size=18, weight="bold", color="#111827", expand=True),
                                ft.Text(t_str, size=16, weight="bold", color="teal"),
                            ]),
                            padding=15
                        ),
                        elevation=2,
                        color="white"
                    )
                )