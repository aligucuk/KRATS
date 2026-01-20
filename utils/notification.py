import flet as ft
import time
import threading

class NotificationManager:
    def __init__(self, page: ft.Page):
        self.page = page
        # Bildirimlerin üst üste bineceği dikey yığın (Stack)
        self.notification_column = ft.Column(
            right=20,
            top=20,
            spacing=10,
            width=350,
            alignment=ft.MainAxisAlignment.START,
            animate_opacity=300,
        )
        # Bu yığını sayfanın overlay (katman) kısmına ekliyoruz
        if self.notification_column not in self.page.overlay:
            self.page.overlay.append(self.notification_column)
            self.page.update()

    def show(self, message: str, type: str = "info", duration: int = 4):
        """
        Bildirim gösterir.
        type: "success", "error", "warning", "info"
        """
        
        # Renk ve İkon Ayarları
        colors = {
            "success": ("#E8F5E9", "#2E7D32", "check_circle"), # Yeşil
            "error": ("#FFEBEE", "#C62828", "error"),           # Kırmızı
            "warning": ("#FFF3E0", "#EF6C00", "warning"),       # Turuncu
            "info": ("#E3F2FD", "#1565C0", "info")              # Mavi
        }
        
        bg_color, text_color, icon_name = colors.get(type, colors["info"])

        # Bildirim Kartı Tasarımı (macOS Style)
        notification_card = ft.Container(
            content=ft.Row([
                ft.Icon(icon_name, color=text_color, size=24),
                ft.Container(width=10),
                ft.Column([
                    ft.Text(type.capitalize(), weight="bold", color=text_color, size=14),
                    ft.Text(message, color="black87", size=13, no_wrap=False, max_lines=2),
                ], spacing=2, expand=True),
                # Kapatma Butonu
                ft.IconButton(
                    icon="close", 
                    icon_size=16, 
                    icon_color="grey",
                    on_click=lambda e: self.close_notification(notification_card)
                )
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            
            bgcolor="white", # Hafif şeffaflık için: ft.colors.with_opacity(0.95, "white")
            padding=15,
            border_radius=10,
            border=ft.border.only(left=ft.BorderSide(5, text_color)),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.colors.with_opacity(0.2, "black"),
                offset=ft.Offset(0, 4)
            ),
            # Animasyon Başlangıcı (Sağdan kayarak gelme efekti için offset kullanılabilir ama Flet'te opacity daha stabil)
            opacity=0,
            animate_opacity=300,
            offset=ft.transform.Offset(0.5, 0), # Sağdan gelsin
            animate_offset=ft.animation.Animation(300, "easeOut"),
        )

        # Listeye ekle
        self.notification_column.controls.insert(0, notification_card)
        self.notification_column.update()

        # Animasyonu Tetikle (Görünür yap ve yerine kaydır)
        time.sleep(0.05) # Render için minik bekleme
        notification_card.opacity = 1
        notification_card.offset = ft.transform.Offset(0, 0)
        notification_card.update()

        # Otomatik Kapanma Zamanlayıcısı
        def auto_close():
            time.sleep(duration)
            try:
                self.close_notification(notification_card)
            except:
                pass # Sayfa kapandıysa hata vermesin

        threading.Thread(target=auto_close, daemon=True).start()

    def close_notification(self, card):
        """Bildirimi animasyonla kapatır ve listeden siler"""
        try:
            card.opacity = 0
            card.offset = ft.transform.Offset(0.5, 0) # Sağa kayarak kaybol
            card.update()
            time.sleep(0.3) # Animasyon süresi kadar bekle
            if card in self.notification_column.controls:
                self.notification_column.controls.remove(card)
                self.notification_column.update()
        except:
            pass