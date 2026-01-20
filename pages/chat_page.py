import flet as ft

class ChatPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.user_id = page.session.get("user_id")
        
        # Mesaj Giriş Alanı (Daha şık)
        self.txt_msg = ft.TextField(
            hint_text="Bir mesaj yazın...",
            border_radius=25,
            filled=True,
            bgcolor=ft.Colors.with_opacity(0.05, "black"),
            border_color="transparent",
            content_padding=ft.padding.symmetric(horizontal=20, vertical=10),
            expand=True,
            on_submit=self.send_msg
        )
        
        self.chat_list = ft.ListView(expand=True, spacing=10, auto_scroll=True, padding=20)
        
        # Kişi Seçimi
        self.dd_users = ft.Dropdown(
            label="Kime", width=250, border_radius=12, 
            content_padding=10, text_size=14,
            border_color="transparent", filled=True, bgcolor="white"
        )

    def view(self):
        # Kullanıcıları yükle
        users = self.db.get_users_except(self.user_id)
        self.dd_users.options = [ft.dropdown.Option(key=str(u[0]), text=u[2]) for u in users]
        if users: self.dd_users.value = str(users[0][0])
        self.load_history(update_ui=False)

        # --- ÜST BAR (Header) ---
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CHAT_BUBBLE, color="teal"),
                ft.Text("Klinik İçi Sohbet", size=18, weight="bold"),
                ft.Container(width=20),
                self.dd_users,
                ft.IconButton(ft.Icons.REFRESH, icon_color="grey", on_click=lambda _: self.load_history(True))
            ], alignment=ft.MainAxisAlignment.START),
            padding=15, bgcolor="white",
            border=ft.border.only(bottom=ft.BorderSide(1, "#eeeeee"))
        )

        # --- ALT BAR (Input Area) ---
        input_bar = ft.Container(
            content=ft.Row([
                ft.IconButton(ft.Icons.ATTACH_FILE, icon_color="grey"),
                self.txt_msg,
                ft.IconButton(ft.Icons.SEND_ROUNDED, icon_color="teal", icon_size=30, on_click=self.send_msg)
            ]),
            padding=15, bgcolor="white",
            border=ft.border.only(top=ft.BorderSide(1, "#eeeeee"))
        )

        # --- ANA YAPI ---
        layout = ft.Column([
            header,
            ft.Container(content=self.chat_list, expand=True, bgcolor="#f4f6f8"), # Hafif gri arka plan
            input_bar
        ], spacing=0, expand=True)

        return ft.View("/chat", controls=[layout], padding=0)

    def load_history(self, update_ui=True):
        self.chat_list.controls.clear()
        if not self.dd_users.value: return
        
        try:
            target_id = int(self.dd_users.value)
            msgs = self.db.get_chat_history(self.user_id, target_id)
            
            for m in msgs:
                is_me = (m[0] == self.user_id)
                self.chat_list.controls.append(
                    ft.Row([
                        ft.Container(
                            content=ft.Text(m[1], color="white" if is_me else "#333"),
                            bgcolor="teal" if is_me else "white",
                            padding=ft.padding.symmetric(horizontal=15, vertical=10),
                            border_radius=ft.border_radius.only(
                                top_left=15, top_right=15,
                                bottom_left=15 if is_me else 0,
                                bottom_right=0 if is_me else 15
                            ),
                            shadow=ft.BoxShadow(blur_radius=2, color=ft.Colors.with_opacity(0.1, "black"))
                        )
                    ], alignment=ft.MainAxisAlignment.END if is_me else ft.MainAxisAlignment.START)
                )
            if update_ui: self.chat_list.update()
        except: pass

    def send_msg(self, e):
        if not self.txt_msg.value or not self.dd_users.value: return
        self.db.send_message(self.user_id, int(self.dd_users.value), self.txt_msg.value)
        self.txt_msg.value = ""
        self.load_history(True)
        self.txt_msg.focus()