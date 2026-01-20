"""
Chat Page - İç Mesajlaşma Sistemi
Personel arası gerçek zamanlı mesajlaşma
"""

import flet as ft
from datetime import datetime
from database.db_manager import DatabaseManager
from database.models import Message
from utils.logger import app_logger


class ChatPage:
    def __init__(self, page: ft.Page, db: DatabaseManager):
        self.page = page
        self.db = db
        
        # Mevcut kullanıcı
        self.current_user_id = self.page.session.get("user_id")
        self.current_user_name = self.page.session.get("user_name")
        
        # Seçili konuşma
        self.selected_receiver_id = None
        self.selected_receiver_name = None
        
        # UI Components
        self.users_list = ft.ListView(spacing=5, expand=True)
        self.chat_messages = ft.ListView(
            spacing=10,
            auto_scroll=True,
            expand=True,
            padding=20
        )
        
        self.txt_message = ft.TextField(
            hint_text="Mesajınızı yazın...",
            border_radius=25,
            filled=True,
            bgcolor=ft.Colors.with_opacity(0.05, "black"),
            border_color="transparent",
            min_lines=1,
            max_lines=3,
            shift_enter=True,
            expand=True,
            on_submit=self.send_message
        )
        
    def view(self):
        """Ana görünüm"""
        self.load_users()
        
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CHAT_BUBBLE, color="teal", size=30),
                ft.Column([
                    ft.Text("İç Mesajlaşma", size=24, weight="bold"),
                    ft.Text("Personel arası iletişim", size=12, color="grey")
                ], spacing=0)
            ]),
            padding=20,
            bgcolor="white",
            border_radius=15
        )
        
        # Sol panel - Kullanıcı listesi
        users_panel = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text(
                        "Kişiler",
                        size=16,
                        weight="bold"
                    ),
                    padding=15,
                    bgcolor="#f8f9fa",
                    border_radius=ft.border_radius.only(top_left=10, top_right=10)
                ),
                ft.Divider(height=1, color="grey"),
                ft.Container(
                    content=self.users_list,
                    expand=True
                )
            ]),
            width=300,
            bgcolor="white",
            border_radius=15,
            border=ft.border.all(1, "#f0f0f0")
        )
        
        # Sağ panel - Sohbet alanı
        chat_header = ft.Container(
            content=ft.Row([
                ft.CircleAvatar(
                    content=ft.Text(
                        self.selected_receiver_name[0].upper() if self.selected_receiver_name else "?",
                        weight="bold"
                    ),
                    bgcolor="teal",
                    radius=20
                ) if self.selected_receiver_id else ft.Container(),
                ft.Text(
                    self.selected_receiver_name or "Bir kişi seçin",
                    size=18,
                    weight="bold"
                ),
                ft.Container(expand=True),
                ft.IconButton(
                    ft.Icons.REFRESH,
                    tooltip="Yenile",
                    on_click=lambda _: self.load_chat_history()
                ) if self.selected_receiver_id else ft.Container()
            ]),
            padding=15,
            bgcolor="#f8f9fa",
            border_radius=ft.border_radius.only(top_left=10, top_right=10)
        )
        
        chat_panel = ft.Container(
            content=ft.Column([
                chat_header,
                ft.Divider(height=1, color="grey"),
                ft.Container(
                    content=self.chat_messages,
                    bgcolor="#f4f6f8",
                    expand=True
                ),
                ft.Container(
                    content=ft.Row([
                        ft.IconButton(
                            ft.Icons.ATTACH_FILE,
                            icon_color="grey"
                        ),
                        self.txt_message,
                        ft.IconButton(
                            ft.Icons.SEND_ROUNDED,
                            icon_color="teal",
                            icon_size=30,
                            on_click=self.send_message,
                            disabled=not self.selected_receiver_id
                        )
                    ]),
                    padding=15,
                    bgcolor="white",
                    border_radius=ft.border_radius.only(bottom_left=10, bottom_right=10)
                )
            ], spacing=0, expand=True),
            bgcolor="white",
            border_radius=15,
            border=ft.border.all(1, "#f0f0f0"),
            expand=True
        )
        
        # Main layout
        main_layout = ft.Row([
            users_panel,
            chat_panel
        ], spacing=20, expand=True)
        
        return ft.View(
            "/chat",
            controls=[
                ft.Container(
                    content=ft.Column([
                        header,
                        main_layout
                    ], spacing=15, expand=True),
                    padding=30,
                    bgcolor="#f8f9fa",
                    expand=True
                )
            ],
            padding=0
        )
    
    def load_users(self):
        """Kullanıcı listesini yükle"""
        try:
            self.users_list.controls.clear()
            
            # Kendisi hariç tüm kullanıcılar
            users = self.db.get_users_except(self.current_user_id)
            
            for user in users:
                # Son mesaj ve okunmamış sayısı
                last_message = self.db.get_last_message(
                    self.current_user_id,
                    user.id
                )
                
                unread_count = self.db.get_unread_message_count(
                    sender_id=user.id,
                    receiver_id=self.current_user_id
                )
                
                # Seçili mi?
                is_selected = (user.id == self.selected_receiver_id)
                
                user_tile = ft.Container(
                    content=ft.Row([
                        ft.CircleAvatar(
                            content=ft.Text(
                                user.full_name[0].upper(),
                                weight="bold"
                            ),
                            bgcolor="teal",
                            radius=20
                        ),
                        ft.Column([
                            ft.Text(
                                user.full_name,
                                weight="bold",
                                size=14
                            ),
                            ft.Text(
                                last_message.message[:30] + "..." if last_message and len(last_message.message) > 30 else last_message.message if last_message else "Henüz mesaj yok",
                                size=12,
                                color="grey",
                                italic=not last_message
                            )
                        ], spacing=2, expand=True),
                        ft.Container(
                            content=ft.Text(
                                str(unread_count),
                                size=12,
                                color="white",
                                weight="bold"
                            ),
                            bgcolor="red",
                            padding=5,
                            border_radius=10,
                            visible=(unread_count > 0)
                        ) if unread_count > 0 else ft.Container()
                    ]),
                    padding=10,
                    bgcolor=ft.Colors.TEAL_50 if is_selected else "transparent",
                    border_radius=10,
                    ink=True,
                    on_click=lambda _, uid=user.id, uname=user.full_name: self.select_user(uid, uname)
                )
                
                self.users_list.controls.append(user_tile)
            
            self.users_list.update()
            
        except Exception as e:
            app_logger.error(f"Load users error: {e}")
    
    def select_user(self, user_id, user_name):
        """Kullanıcı seç ve sohbeti yükle"""
        try:
            self.selected_receiver_id = user_id
            self.selected_receiver_name = user_name
            
            # Kullanıcı listesini güncelle (seçili göster)
            self.load_users()
            
            # Sohbet geçmişini yükle
            self.load_chat_history()
            
            # Mesajları okundu olarak işaretle
            self.db.mark_messages_as_read(
                sender_id=user_id,
                receiver_id=self.current_user_id
            )
            
            # View'ı yenile
            self.page.update()
            
        except Exception as e:
            app_logger.error(f"Select user error: {e}")
    
    def load_chat_history(self):
        """Sohbet geçmişini yükle"""
        try:
            self.chat_messages.controls.clear()
            
            if not self.selected_receiver_id:
                return
            
            # Mesajları çek
            messages = self.db.get_chat_history(
                self.current_user_id,
                self.selected_receiver_id
            )
            
            if not messages:
                self.chat_messages.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, size=60, color="grey"),
                            ft.Text(
                                "Henüz mesaj yok",
                                size=16,
                                color="grey"
                            ),
                            ft.Text(
                                "İlk mesajı gönderin",
                                size=12,
                                color="grey"
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.center,
                        expand=True
                    )
                )
            else:
                current_date = None
                
                for msg in messages:
                    # Tarih ayırıcı
                    msg_date = msg.timestamp.date() if isinstance(msg.timestamp, datetime) else None
                    
                    if msg_date and msg_date != current_date:
                        current_date = msg_date
                        
                        # Bugün mü?
                        if msg_date == datetime.now().date():
                            date_text = "Bugün"
                        # Dün mü?
                        elif msg_date == (datetime.now().date() - timedelta(days=1)):
                            date_text = "Dün"
                        else:
                            date_text = msg_date.strftime("%d.%m.%Y")
                        
                        self.chat_messages.controls.append(
                            ft.Container(
                                content=ft.Text(
                                    date_text,
                                    size=12,
                                    color="grey",
                                    weight="bold"
                                ),
                                alignment=ft.alignment.center,
                                padding=10
                            )
                        )
                    
                    # Mesaj balonu
                    is_me = (msg.sender_id == self.current_user_id)
                    
                    self.chat_messages.controls.append(
                        self._message_bubble(msg, is_me)
                    )
            
            self.chat_messages.update()
            
        except Exception as e:
            app_logger.error(f"Load chat history error: {e}")
    
    def _message_bubble(self, message, is_me):
        """Mesaj balonu"""
        # Zaman
        time_str = message.timestamp.strftime("%H:%M") if isinstance(message.timestamp, datetime) else ""
        
        # Balon rengi
        bubble_color = "teal" if is_me else "white"
        text_color = "white" if is_me else "black"
        
        return ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        message.message,
                        color=text_color,
                        size=14
                    ),
                    ft.Text(
                        time_str,
                        size=10,
                        color=ft.Colors.with_opacity(0.7, text_color)
                    )
                ], spacing=5),
                bgcolor=bubble_color,
                padding=15,
                border_radius=ft.border_radius.only(
                    top_left=15,
                    top_right=15,
                    bottom_left=0 if is_me else 15,
                    bottom_right=15 if is_me else 0
                ),
                shadow=ft.BoxShadow(
                    blur_radius=2,
                    color=ft.Colors.with_opacity(0.1, "black")
                ),
                max_width=500
            )
        ], alignment=ft.MainAxisAlignment.END if is_me else ft.MainAxisAlignment.START)
    
    def send_message(self, e):
        """Mesaj gönder"""
        try:
            message_text = self.txt_message.value.strip()
            
            if not message_text or not self.selected_receiver_id:
                return
            
            # Message objesi oluştur
            message = Message(
                id=None,
                sender_id=self.current_user_id,
                receiver_id=self.selected_receiver_id,
                message=message_text,
                timestamp=datetime.now()
            )
            
            # Veritabanına kaydet
            self.db.send_message(message)
            
            # Input temizle
            self.txt_message.value = ""
            self.txt_message.focus()
            
            # Sohbeti yenile
            self.load_chat_history()
            
            # Kullanıcı listesini yenile (son mesaj güncellendi)
            self.load_users()
            
            self.page.update()
            
        except Exception as e:
            app_logger.error(f"Send message error: {e}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Mesaj gönderme hatası: {e}"),
                bgcolor="red"
            ))