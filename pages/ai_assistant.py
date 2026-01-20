import flet as ft
import threading
import google.generativeai as genai
from openai import OpenAI
import anthropic

class AIAssistantPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        
        # 1. VERİTABANI GÜNCELLEMESİ (Sütun Kontrolü)
        # Eğer 'is_read' sütunu yoksa ekle (Otomatik Migration)
        try:
            self.db.cursor.execute("SELECT is_read FROM medical_news LIMIT 1")
        except:
            try:
                self.db.cursor.execute("ALTER TABLE medical_news ADD COLUMN is_read INTEGER DEFAULT 0")
                self.db.connection.commit()
                print("DB Bilgisi: Haber tablosuna 'okundu' sütunu eklendi.")
            except: pass

        # 2. OKUNMAMIŞ HABERLERİ ÇEK
        news_context = ""
        self.unread_count = 0
        try:
            unread_data = self.db.cursor.execute("SELECT title, summary FROM medical_news WHERE is_read = 0 ORDER BY id DESC").fetchall()
            self.unread_count = len(unread_data)
            
            if unread_data:
                news_list = [f"- {n[0]}: {n[1]}" for n in unread_data]
                news_context = "KULLANICININ HENÜZ OKUMADIĞI YENİ HABERLER:\n" + "\n".join(news_list)
            else:
                news_context = "Şu an sistemde okunmamış yeni bir tıbbi haber yok."
        except Exception as e:
            news_context = f"Haber verisi çekilemedi: {e}"

        # 3. SİSTEM TALİMATI (Dinamik Haber Beslemesi)
        self.system_instruction = f"""
        Sen 'KRATS Klinik OS' asistanısın. Kullanıcın bir Tıp Doktoru.
        ASLA 'doktora danışın' deme. Tıbbi terminoloji kullan.
        
        {news_context}
        
        KURALLAR:
        1. Kullanıcı "yeni ne var?", "bültende ne var?" derse YUKARIDAKİ OKUNMAMIŞ listeyi özetle.
        2. Eğer okunmamış haber yoksa, "Yeni bir gelişme yok" de.
        3. Doğrudan tanı, tedavi, dozaj ve literatür bilgisi sun.
        """

        self.keys = {
            "google": self.db.get_setting("ai_key_google"),
            "openai": self.db.get_setting("ai_key_openai"),
            "anthropic": self.db.get_setting("ai_key_anthropic")
        }
        
        self.models = [
            {"id": "gemini-2.5-flash",      "label": "Gemini 2.5 Flash",     "provider": "google"},
            {"id": "gemini-3-flash-preview", "label": "Gemini 3.0 Flash",     "provider": "google"},
            {"id": "gemini-3-pro-preview",   "label": "Gemini 3.0 Pro",       "provider": "google"},
            {"id": "gemini-2.5-pro",        "label": "Gemini 2.5 Pro",       "provider": "google"},
            {"id": "gpt-4o",                "label": "GPT-4o",               "provider": "openai"},
            {"id": "claude-3-opus-20240229","label": "Claude 3 Opus",        "provider": "anthropic"},
        ]

        self.dd_model = ft.Dropdown(
            options=[ft.dropdown.Option(key=m["id"], text=m["label"]) for m in self.models],
            value="gemini-2.5-flash",
            width=200, text_size=13, content_padding=10, filled=True, bgcolor="#f8f9fa",
            border_radius=10, border_color="transparent", prefix_icon=ft.Icons.TUNE
        )
        
        self.chat_history_ui = ft.ListView(expand=True, spacing=15, auto_scroll=True)
        
        # Session Yönetimi
        if not self.page.session.get("ai_messages_log"):
            self.page.session.set("ai_messages_log", [])
            self.page.session.set("ai_ui_cache", [])

        self.txt_input = ft.TextField(
            hint_text="Vaka analizi, 'Bültende ne var?' veya literatür...",
            border_radius=25, filled=True, bgcolor=ft.Colors.with_opacity(0.05, "black"),
            min_lines=1, max_lines=3, shift_enter=True,
            expand=True, on_submit=self.send_message, disabled=False
        )
        self.loading_indicator = ft.ProgressBar(width=None, color="teal", visible=False)
        
        # Okundu İşaretle Butonu (Sadece okunmamış haber varsa görünür)
        self.btn_mark_read = ft.IconButton(
            ft.Icons.MARK_EMAIL_READ, 
            tooltip="Haberleri Okundu Say", 
            icon_color="teal",
            visible=(self.unread_count > 0),
            on_click=self.mark_news_as_read
        )

    def view(self):
        saved_ui = self.page.session.get("ai_ui_cache")
        if saved_ui:
            for msg in saved_ui:
                self.add_message_to_ui(msg["role"], msg["text"], save_to_session=False)

        # Header Tasarımı
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.AUTO_AWESOME, color="purple", size=24),
                ft.Column([
                    ft.Text("AI Konsültasyon", size=18, weight="bold"),
                    # Okunmamış haber sayısı uyarısı
                    ft.Text(f"{self.unread_count} Yeni Haber" if self.unread_count > 0 else "Bülten Güncel", 
                            size=10, color="red" if self.unread_count > 0 else "green", weight="bold")
                ], spacing=0),
                
                ft.Container(expand=True),
                
                self.btn_mark_read, # Haberleri okundu sayma butonu
                self.dd_model,
                ft.IconButton(ft.Icons.SETTINGS, icon_size=20, tooltip="Ayarlar", on_click=self.open_settings_dialog),
                ft.IconButton(ft.Icons.DELETE_SWEEP, icon_size=20, tooltip="Sohbeti Temizle", icon_color="red", on_click=self.clear_chat)
            ]),
            padding=15, bgcolor="white", border_radius=15,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.05, "black"))
        )

        chat_container = ft.Container(
            content=ft.Column([self.chat_history_ui, self.loading_indicator]),
            expand=True, padding=20, bgcolor="white", border_radius=15, border=ft.border.all(1, "#f0f0f0")
        )

        input_area = ft.Container(
            content=ft.Row([
                self.txt_input,
                ft.IconButton(ft.Icons.SEND_ROUNDED, icon_color="teal", icon_size=30, on_click=self.send_message)
            ]),
            padding=10, bgcolor="white", border_radius=15,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.05, "black"))
        )

        if not self.chat_history_ui.controls:
            user = self.page.session.get('user_name') or 'Meslektaşım'
            if not any(self.keys.values()):
                self.add_message_to_ui("Sistem", "Lütfen ayarlardan API anahtarlarınızı giriniz.")
            else:
                news_msg = f"**{self.unread_count}** adet okunmamış bülten haberi var." if self.unread_count > 0 else "Tüm bülten haberlerini incelediniz."
                self.add_message_to_ui("AI", f"Sayın Dr. {user}, {news_msg} Hazırım.")

        return ft.View("/ai_assistant", controls=[ft.Container(content=ft.Column([header, chat_container, input_area], expand=True, spacing=15), padding=20)], padding=0)

    def mark_news_as_read(self, e):
        """Tüm haberleri okundu olarak işaretler ve UI'ı günceller"""
        try:
            self.db.cursor.execute("UPDATE medical_news SET is_read = 1 WHERE is_read = 0")
            self.db.connection.commit()
            
            self.unread_count = 0
            self.btn_mark_read.visible = False
            self.add_message_to_ui("Sistem", "✅ Tüm bülten haberleri 'Okundu' olarak işaretlendi. Artık bu haberler önünüze gelmeyecek.")
            
            # Sistem talimatını güncelle (Haberleri sil)
            self.system_instruction = self.system_instruction.replace("KULLANICININ HENÜZ OKUMADIĞI YENİ HABERLER:", "Şu an sistemde okunmamış yeni bir tıbbi haber yok.")
            self.page.update()
        except Exception as err:
            self.page.open(ft.SnackBar(ft.Text(f"Hata: {err}"), bgcolor="red"))

    def add_message_to_ui(self, sender, text, save_to_session=True):
        is_ai = (sender == "AI" or sender == "Sistem")
        bubble_color = ft.Colors.TEAL_50 if is_ai else ft.Colors.BLUE_50
        icon = ft.Icons.MEDICAL_SERVICES if is_ai else ft.Icons.PERSON
        
        if save_to_session:
            current_cache = self.page.session.get("ai_ui_cache")
            current_cache.append({"role": sender, "text": text})
            api_role = "assistant" if is_ai else "user"
            if sender != "Sistem":
                current_logs = self.page.session.get("ai_messages_log")
                current_logs.append({"role": api_role, "content": text})

        message_content = ft.Container(
            content=ft.Markdown(
                text, 
                selectable=True, 
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                on_tap_link=lambda e: self.page.launch_url(e.data)
            ),
            bgcolor=bubble_color, padding=15,
            border_radius=ft.border_radius.only(
                top_left=0 if is_ai else 15, top_right=15 if is_ai else 0,
                bottom_left=15, bottom_right=15
            ),
            width=550, 
        )

        avatar = ft.CircleAvatar(radius=16, bgcolor="teal" if is_ai else "blue", content=ft.Icon(icon, size=16, color="white"))

        if is_ai:
            row = ft.Row([avatar, message_content], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START)
        else:
            row = ft.Row([message_content, avatar], alignment=ft.MainAxisAlignment.END, vertical_alignment=ft.CrossAxisAlignment.START)

        self.chat_history_ui.controls.append(row)
        try: self.page.update()
        except: pass

    def send_message(self, e):
        prompt = self.txt_input.value
        if not prompt: return

        selected_model_id = self.dd_model.value
        model_info = next((m for m in self.models if m["id"] == selected_model_id), None)
        provider = model_info["provider"] if model_info else "google"

        if not self.keys.get(provider):
            self.open_settings_dialog(None)
            self.page.open(ft.SnackBar(ft.Text(f"{provider.capitalize()} API Anahtarı eksik!"), bgcolor="red"))
            return

        self.add_message_to_ui("Dr.", prompt)
        self.txt_input.value = ""
        self.txt_input.disabled = True
        self.loading_indicator.visible = True
        self.page.update()

        history = self.page.session.get("ai_messages_log")
        threading.Thread(target=self.fetch_response, args=(prompt, selected_model_id, provider, history), daemon=True).start()

    def fetch_response(self, prompt, model_id, provider, history):
        response_text = ""
        try:
            if provider == "google":
                genai.configure(api_key=self.keys["google"])
                model = genai.GenerativeModel(model_id, system_instruction=self.system_instruction)
                gemini_history = []
                for msg in history[:-1]:
                    role = "user" if msg["role"] == "user" else "model"
                    gemini_history.append({"role": role, "parts": [msg["content"]]})

                chat = model.start_chat(history=gemini_history)
                res = chat.send_message(prompt)
                response_text = res.text

            elif provider == "openai":
                client = OpenAI(api_key=self.keys["openai"])
                messages = [{"role": "system", "content": self.system_instruction}] + history
                completion = client.chat.completions.create(model=model_id, messages=messages)
                response_text = completion.choices[0].message.content

            elif provider == "anthropic":
                client = anthropic.Anthropic(api_key=self.keys["anthropic"])
                message = client.messages.create(
                    model=model_id, max_tokens=2000, 
                    system=self.system_instruction,
                    messages=history
                )
                response_text = message.content[0].text

            self.txt_input.disabled = False
            self.loading_indicator.visible = False
            
            model_label = next((m['label'] for m in self.models if m['id'] == model_id), model_id)
            final_text = f"{response_text}\n\n*Kaynak: {model_label}*"
            self.add_message_to_ui("AI", final_text)

        except Exception as e:
            self.txt_input.disabled = False
            self.loading_indicator.visible = False
            
            raw_error = str(e)
            friendly_error = f"Hata: {raw_error}"
            
            if "404" in raw_error or "not found" in raw_error:
                friendly_error = f"⚠️ **Model Bulunamadı ({model_id})**"
            elif "429" in raw_error or "Quota exceeded" in raw_error:
                friendly_error = (
                    f"⚠️ **Kota Sınırı / Abonelik Hatası ({model_id})**\n\n"
                    "1. Günlük ücretsiz kullanım kotanız dolmuştur.\n"
                    "2. **Aboneliğiniz bu üst düzey modeli desteklemiyor olabilir.**\n\n"
                    "👉 Çözüm: Lütfen farklı bir modeli seçip tekrar deneyin."
                )

            self.add_message_to_ui("Sistem", friendly_error, save_to_session=False)
            self.page.update()

    def clear_chat(self, e):
        self.page.session.set("ai_messages_log", [])
        self.page.session.set("ai_ui_cache", [])
        self.chat_history_ui.controls.clear()
        self.add_message_to_ui("Sistem", "Sohbet hafızası temizlendi.", save_to_session=False)

    def open_settings_dialog(self, e):
        txt_google = ft.TextField(label="Google API Key", password=True, can_reveal_password=True, value=self.keys["google"] or "")
        txt_openai = ft.TextField(label="OpenAI API Key", password=True, can_reveal_password=True, value=self.keys["openai"] or "")
        txt_anthropic = ft.TextField(label="Anthropic API Key", password=True, can_reveal_password=True, value=self.keys["anthropic"] or "")

        def save(e):
            self.keys["google"] = txt_google.value
            self.keys["openai"] = txt_openai.value
            self.keys["anthropic"] = txt_anthropic.value
            self.db.set_setting("ai_key_google", txt_google.value)
            self.db.set_setting("ai_key_openai", txt_openai.value)
            self.db.set_setting("ai_key_anthropic", txt_anthropic.value)
            self.page.close(dlg)
            self.page.open(ft.SnackBar(ft.Text("Anahtarlar kaydedildi!"), bgcolor="green"))

        dlg = ft.AlertDialog(
            title=ft.Text("AI Sağlayıcı Ayarları"),
            content=ft.Column([ft.Text("Servis Anahtarlarını Girin:"), txt_google, txt_openai, txt_anthropic], tight=True, width=400),
            actions=[ft.ElevatedButton("Kaydet", on_click=save)]
        )
        self.page.open(dlg)