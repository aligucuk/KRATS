"""
AI Assistant Page - Yapay Zeka Asistanı
Multi-provider: Google Gemini, OpenAI GPT, Anthropic Claude
"""

import flet as ft
from datetime import datetime
from database.db_manager import DatabaseManager
from services.ai_service import AIService
from utils.logger import app_logger
import threading


class AIAssistantPage:
    def __init__(self, page: ft.Page, db: DatabaseManager):
        self.page = page
        self.db = db
        self.ai_service = AIService(db)
        
        # Sistem talimatı
        self.system_instruction = """
        Sen 'KRATS Klinik OS' asistanısın. Kullanıcın bir Tıp Doktoru.
        ASLA 'doktora danışın' deme. Tıbbi terminoloji kullan.
        
        KURALLAR:
        1. Doğrudan tanı, tedavi, dozaj ve literatür bilgisi sun.
        2. Medikal sorulara profesyonel cevap ver.
        3. Türkçe dilinde yanıt ver.
        """
        
        # Sohbet geçmişi
        if not self.page.session.get("ai_chat_history"):
            self.page.session.set("ai_chat_history", [])
        
        # UI Components
        self.chat_display = ft.ListView(
            expand=True,
            spacing=15,
            auto_scroll=True,
            padding=20
        )
        
        self.txt_input = ft.TextField(
            hint_text="Sorunuzu yazın...",
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
        
        self.dd_provider = ft.Dropdown(
            label="AI Provider",
            options=[
                ft.dropdown.Option("gemini", "Google Gemini"),
                ft.dropdown.Option("openai", "OpenAI GPT-4"),
                ft.dropdown.Option("claude", "Anthropic Claude")
            ],
            value="gemini",
            width=200
        )
        
        self.dd_model = ft.Dropdown(
            label="Model",
            width=250,
            on_change=self.on_provider_changed
        )
        
        self.loading_indicator = ft.ProgressBar(
            width=None,
            color="teal",
            visible=False
        )
        
        self.load_models()
        
    def view(self):
        """Ana görünüm"""
        # İlk mesaj
        if not self.page.session.get("ai_chat_history"):
            self.add_message("AI", "Merhaba! Size nasıl yardımcı olabilirim?", save=True)
        else:
            # Önceki sohbeti yükle
            for msg in self.page.session.get("ai_chat_history"):
                self.add_message(msg["role"], msg["content"], save=False)
        
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.AUTO_AWESOME, color="purple", size=30),
                ft.Column([
                    ft.Text("AI Konsültasyon", size=24, weight="bold"),
                    ft.Text("Yapay zeka destekli tıbbi asistan", size=12, color="grey")
                ], spacing=0),
                ft.Container(expand=True),
                ft.Row([
                    self.dd_provider,
                    self.dd_model,
                    ft.IconButton(
                        ft.Icons.SETTINGS,
                        tooltip="API Ayarları",
                        on_click=self.open_settings
                    ),
                    ft.IconButton(
                        ft.Icons.DELETE_SWEEP,
                        tooltip="Sohbeti Temizle",
                        icon_color="red",
                        on_click=self.clear_chat
                    )
                ])
            ]),
            padding=20,
            bgcolor="white",
            border_radius=15
        )
        
        # Chat area
        chat_area = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=self.chat_display,
                    bgcolor="#f4f6f8",
                    border_radius=15,
                    expand=True
                ),
                self.loading_indicator
            ], spacing=10, expand=True),
            padding=20,
            bgcolor="white",
            border_radius=15,
            expand=True
        )
        
        # Input area
        input_area = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    ft.Icons.ATTACH_FILE,
                    icon_color="grey"
                ),
                self.txt_input,
                ft.IconButton(
                    ft.Icons.SEND_ROUNDED,
                    icon_color="teal",
                    icon_size=30,
                    on_click=self.send_message
                )
            ]),
            padding=15,
            bgcolor="white",
            border_radius=15
        )
        
        return ft.View(
            "/ai_assistant",
            controls=[
                ft.Container(
                    content=ft.Column([
                        header,
                        chat_area,
                        input_area
                    ], spacing=15, expand=True),
                    padding=30,
                    bgcolor="#f8f9fa",
                    expand=True
                )
            ],
            padding=0
        )
    
    def load_models(self):
        """Modelleri yükle"""
        provider = self.dd_provider.value
        
        if provider == "gemini":
            models = [
                ("gemini-2.0-flash-exp", "Gemini 2.0 Flash"),
                ("gemini-1.5-pro", "Gemini 1.5 Pro"),
                ("gemini-1.5-flash", "Gemini 1.5 Flash")
            ]
        elif provider == "openai":
            models = [
                ("gpt-4o", "GPT-4o"),
                ("gpt-4-turbo", "GPT-4 Turbo"),
                ("gpt-3.5-turbo", "GPT-3.5 Turbo")
            ]
        else:  # claude
            models = [
                ("claude-3-opus-20240229", "Claude 3 Opus"),
                ("claude-3-sonnet-20240229", "Claude 3 Sonnet"),
                ("claude-3-haiku-20240307", "Claude 3 Haiku")
            ]
        
        self.dd_model.options = [
            ft.dropdown.Option(key=m[0], text=m[1]) for m in models
        ]
        self.dd_model.value = models[0][0]
    
    def on_provider_changed(self, e):
        """Provider değiştiğinde"""
        self.load_models()
        self.dd_model.update()
    
    def add_message(self, role, content, save=True):
        """Mesaj ekle"""
        is_ai = (role == "AI")
        
        # Balun rengi
        bubble_color = ft.Colors.TEAL_50 if is_ai else ft.Colors.BLUE_50
        text_color = "#1a1a1a"
        icon = ft.Icons.AUTO_AWESOME if is_ai else ft.Icons.PERSON
        
        message_bubble = ft.Container(
            content=ft.Row([
                ft.CircleAvatar(
                    content=ft.Icon(icon, size=20, color="white"),
                    bgcolor="teal" if is_ai else "blue",
                    radius=20
                ) if is_ai else ft.Container(),
                ft.Container(
                    content=ft.Markdown(
                        content,
                        selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                        on_tap_link=lambda e: self.page.launch_url(e.data)
                    ),
                    bgcolor=bubble_color,
                    padding=15,
                    border_radius=15,
                    width=600
                ),
                ft.CircleAvatar(
                    content=ft.Icon(icon, size=20, color="white"),
                    bgcolor="blue",
                    radius=20
                ) if not is_ai else ft.Container()
            ], alignment=ft.MainAxisAlignment.START if is_ai else ft.MainAxisAlignment.END)
        )
        
        self.chat_display.controls.append(message_bubble)
        
        # Session'a kaydet
        if save:
            chat_history = self.page.session.get("ai_chat_history")
            chat_history.append({
                "role": "assistant" if is_ai else "user",
                "content": content
            })
    
    def send_message(self, e):
        """Mesaj gönder"""
        user_message = self.txt_input.value.strip()
        
        if not user_message:
            return
        
        # Kullanıcı mesajını ekle
        self.add_message("User", user_message, save=True)
        
        # Input temizle
        self.txt_input.value = ""
        self.txt_input.disabled = True
        
        # Loading göster
        self.loading_indicator.visible = True
        self.page.update()
        
        # AI'dan yanıt al (thread'de)
        chat_history = self.page.session.get("ai_chat_history")
        
        threading.Thread(
            target=self.get_ai_response,
            args=(user_message, chat_history),
            daemon=True
        ).start()
    
    def get_ai_response(self, user_message, chat_history):
        """AI'dan yanıt al"""
        try:
            provider = self.dd_provider.value
            model = self.dd_model.value
            
            # AI servisini kullan
            response = self.ai_service.generate_response(
                provider=provider,
                model=model,
                messages=chat_history,
                system_instruction=self.system_instruction
            )
            
            # Yanıtı ekle
            self.add_message("AI", response, save=True)
            
        except Exception as e:
            error_msg = str(e)
            
            # Kullanıcı dostu hata mesajları
            if "API key" in error_msg or "authentication" in error_msg.lower():
                friendly_error = f"❌ **API Anahtarı Hatası**\n\nLütfen ayarlardan {provider.upper()} API anahtarınızı kontrol edin."
            elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
                friendly_error = f"⚠️ **Kota Aşıldı**\n\n{provider.upper()} servisinizin kotası dolmuş. Farklı bir model veya provider deneyin."
            else:
                friendly_error = f"❌ **Hata**\n\n{error_msg}"
            
            self.add_message("AI", friendly_error, save=False)
            app_logger.error(f"AI response error: {e}")
        
        finally:
            # Loading gizle, input aktif
            self.txt_input.disabled = False
            self.loading_indicator.visible = False
            self.txt_input.focus()
            self.page.update()
    
    def clear_chat(self, e):
        """Sohbeti temizle"""
        self.page.session.set("ai_chat_history", [])
        self.chat_display.controls.clear()
        self.add_message("AI", "Sohbet temizlendi. Yeni bir konuşmaya başlayalım!", save=True)
        self.page.update()
    
    def open_settings(self, e):
        """API ayarları dialogu"""
        # Mevcut ayarları yükle
        gemini_key = self.db.get_setting("ai_key_google") or ""
        openai_key = self.db.get_setting("ai_key_openai") or ""
        claude_key = self.db.get_setting("ai_key_anthropic") or ""
        
        txt_gemini = ft.TextField(
            label="Google Gemini API Key",
            password=True,
            can_reveal_password=True,
            value=gemini_key,
            hint_text="AIzaSy..."
        )
        
        txt_openai = ft.TextField(
            label="OpenAI API Key",
            password=True,
            can_reveal_password=True,
            value=openai_key,
            hint_text="sk-..."
        )
        
        txt_claude = ft.TextField(
            label="Anthropic Claude API Key",
            password=True,
            can_reveal_password=True,
            value=claude_key,
            hint_text="sk-ant-..."
        )
        
        def save_keys(e):
            try:
                self.db.set_setting("ai_key_google", txt_gemini.value)
                self.db.set_setting("ai_key_openai", txt_openai.value)
                self.db.set_setting("ai_key_anthropic", txt_claude.value)
                
                # AI servisini yenile
                self.ai_service = AIService(self.db)
                
                self.page.close(dialog)
                self.page.open(ft.SnackBar(
                    ft.Text("✅ API anahtarları kaydedildi"),
                    bgcolor="green"
                ))
                
            except Exception as ex:
                app_logger.error(f"Save API keys error: {ex}")
                self.page.open(ft.SnackBar(
                    ft.Text(f"Kayıt hatası: {ex}"),
                    bgcolor="red"
                ))
        
        dialog = ft.AlertDialog(
            title=ft.Text("AI Sağlayıcı Ayarları"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("API Anahtarlarınızı Girin:", weight="bold"),
                    ft.Divider(),
                    txt_gemini,
                    ft.Text(
                        "Google AI Studio'dan alın: https://aistudio.google.com",
                        size=10,
                        color="grey"
                    ),
                    ft.Divider(),
                    txt_openai,
                    ft.Text(
                        "OpenAI Platform'dan alın: https://platform.openai.com",
                        size=10,
                        color="grey"
                    ),
                    ft.Divider(),
                    txt_claude,
                    ft.Text(
                        "Anthropic Console'dan alın: https://console.anthropic.com",
                        size=10,
                        color="grey"
                    )
                ], tight=True, scroll=ft.ScrollMode.AUTO),
                width=500,
                height=500
            ),
            actions=[
                ft.TextButton("İptal", on_click=lambda _: self.page.close(dialog)),
                ft.ElevatedButton(
                    "Kaydet",
                    bgcolor="teal",
                    color="white",
                    on_click=save_keys
                )
            ]
        )
        
        self.page.open(dialog)
