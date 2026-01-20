import flet as ft
import feedparser
import threading
import socket
import requests
import warnings
import time
import re
from datetime import datetime

# SSL ve Timeout Ayarları
warnings.filterwarnings("ignore")
socket.setdefaulttimeout(15.0)

class MedicalNewsPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.offset = 0
        self.limit = 20
        self.loading = False
        self.service_running = False 
        
        # --- AYARLAR ---
        self.refresh_interval = int(self.db.get_setting("news_refresh_interval") or 30)
        self.retention_days = int(self.db.get_setting("news_retention_days") or 2)
        self.show_notifications = (self.db.get_setting("news_notifications") == "1")

        # Kullanıcı Branşı
        user_id = self.page.session.get("user_id")
        self.user_specialty = "Genel"
        if user_id:
            try:
                u = self.db.cursor.execute("SELECT specialty FROM users WHERE id = ?", (user_id,)).fetchone()
                if u and u[0]: 
                    self.user_specialty = u[0]
            except: 
                pass

        self._init_db_force()
        self.clean_old_news()
        
        # --- UI ELEMANLARI ---
        
        # Haber Grid
        self.news_grid = ft.GridView(
            expand=False, 
            runs_count=2, 
            max_extent=500, 
            child_aspect_ratio=0.85,
            spacing=10, 
            run_spacing=10
        )
        self.saved_grid = ft.GridView(
            expand=True, 
            runs_count=2, 
            max_extent=500, 
            child_aspect_ratio=0.85, 
            spacing=10, 
            run_spacing=10
        )
        
        self.btn_load_more = ft.ElevatedButton(
            "Daha Fazla Göster", 
            icon=ft.Icons.DOWNLOAD, 
            bgcolor="#e0e0e0", 
            color="black", 
            on_click=self.load_more_news
        )
        self.txt_log = ft.Text("Sistem Hazır.", size=11, color="grey")
        self.loading_bar = ft.ProgressBar(visible=False, color="teal", height=2)
        
        self.sw_filter = ft.Switch(
            label=f"{self.user_specialty} Filtresi", 
            value=False, 
            active_color="teal", 
            on_change=lambda e: self.reset_and_load()
        )

        # Ayarlar Elemanları
        self.dd_refresh = ft.Dropdown(
            label="Oto Yenileme (Dakika)", 
            width=180, 
            text_size=12, 
            dense=True,
            options=[
                ft.dropdown.Option("0", "Kapalı"), 
                ft.dropdown.Option("1", "1 Dk"), 
                ft.dropdown.Option("5", "5 Dk"), 
                ft.dropdown.Option("15", "15 Dk"), 
                ft.dropdown.Option("30", "30 Dk"), 
                ft.dropdown.Option("60", "1 Saat")
            ],
            value=str(self.refresh_interval) if self.refresh_interval in [0,1,5,15,30,60] else "0",
            on_change=self.save_refresh_settings
        )
        self.txt_custom_interval = ft.TextField(
            label="Özel Dakika", 
            width=100, 
            text_size=12, 
            dense=True, 
            value=str(self.refresh_interval) if self.refresh_interval not in [0,1,5,15,30,60] else "", 
            on_change=self.save_refresh_settings
        )
        self.txt_retention = ft.TextField(
            label="Saklama (Gün)", 
            width=150, 
            text_size=12, 
            dense=True, 
            value=str(self.retention_days), 
            suffix_text="Gün", 
            on_change=self.save_refresh_settings
        )
        self.sw_notification = ft.Switch(
            label="Yeni Haber Bildirimi", 
            value=self.show_notifications, 
            active_color="teal", 
            on_change=self.save_refresh_settings
        )

        # RSS Ekleme
        self.txt_source_name = ft.TextField(
            label="Kaynak Adı", 
            expand=1, 
            border_radius=10, 
            filled=True, 
            text_size=12, 
            dense=True
        )
        self.txt_source_url = ft.TextField(
            label="RSS Linki", 
            expand=2, 
            border_radius=10, 
            filled=True, 
            text_size=12, 
            dense=True
        )
        self.pr_adding = ft.ProgressRing(width=20, height=20, stroke_width=2, visible=False)
        self.sources_list = ft.Column(spacing=5) 

        # Keywords
        self.txt_keyword = ft.TextField(
            label="İlgi Alanı Ekle", 
            border_radius=10, 
            filled=True, 
            expand=True, 
            text_size=12, 
            dense=True, 
            on_submit=self.add_keyword
        )
        self.keywords_wrap = ft.Row(wrap=True, spacing=5)

    def _init_db_force(self):
        try:
            self.db.cursor.execute("""
                CREATE TABLE IF NOT EXISTS news_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    name TEXT, 
                    url TEXT, 
                    is_active INTEGER DEFAULT 1
                )
            """)
            self.db.cursor.execute("""
                CREATE TABLE IF NOT EXISTS medical_news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    title TEXT, 
                    summary TEXT, 
                    link TEXT, 
                    published_date TEXT, 
                    source TEXT, 
                    image_url TEXT, 
                    is_read INTEGER DEFAULT 0, 
                    is_saved INTEGER DEFAULT 0
                )
            """)
            self.db.cursor.execute("""
                CREATE TABLE IF NOT EXISTS news_keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    keyword TEXT
                )
            """)
            self.db.cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY, 
                    value TEXT
                )
            """)
            
            if self.db.cursor.execute("SELECT count(*) FROM news_sources").fetchone()[0] == 0:
                defaults = [
                    ("Google News - Tıp (TR)", "https://news.google.com/rss/search?q=sağlık+tıp+hastane&hl=tr&gl=TR&ceid=TR:tr"),
                    ("ScienceDaily", "https://www.sciencedaily.com/rss/health_medicine.xml"),
                    ("BBC Health", "http://feeds.bbci.co.uk/news/health/rss.xml")
                ]
                self.db.cursor.executemany("INSERT INTO news_sources (name, url) VALUES (?, ?)", defaults)
                self.db.conn.commit()
            
            try: 
                self.db.cursor.execute("SELECT image_url FROM medical_news LIMIT 1")
            except: 
                self.db.cursor.execute("ALTER TABLE medical_news ADD COLUMN image_url TEXT")
                self.db.conn.commit()
        except: 
            pass

    def clean_old_news(self):
        try:
            query = f"DELETE FROM medical_news WHERE is_saved = 0 AND date(published_date) < date('now', '-{self.retention_days} days')"
            self.db.cursor.execute(query)
            self.db.conn.commit()
        except: 
            pass

    def view(self):
        self.reset_and_load()
        self.load_saved_news()
        self.load_sources()
        self.load_keywords()
        self.start_auto_refresh_service()

        # SEKME 1: BÜLTEN
        tab_news = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text("Tıbbi Bülten", size=22, weight="bold"), 
                        self.txt_log
                    ], spacing=2),
                    ft.Row([
                        self.sw_filter, 
                        ft.IconButton(
                            ft.Icons.REFRESH, 
                            tooltip="Yenile", 
                            icon_color="teal", 
                            on_click=self.refresh_news_click
                        )
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                self.loading_bar,
                ft.Column([
                    self.news_grid, 
                    ft.Container(height=10), 
                    ft.Row([self.btn_load_more], alignment=ft.MainAxisAlignment.CENTER), 
                    ft.Container(height=30)
                ], scroll=ft.ScrollMode.AUTO, expand=True)
            ], expand=True), 
            padding=10
        )

        # SEKME 2: LİSTEM
        tab_saved = ft.Container(
            content=ft.Column([
                ft.Text("Okuma Listem", size=20, weight="bold"), 
                ft.Divider(), 
                self.saved_grid
            ], expand=True), 
            padding=20
        )
        
        # SEKME 3: AYARLAR
        tab_sources = ft.Container(
            content=ft.Column([
                ft.Text("Zamanlama & Yapılandırma", size=16, weight="bold", color="teal"),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Column([ft.Text("Hazır Süre:"), self.dd_refresh]), 
                            ft.Column([ft.Text("Özel Dk:"), self.txt_custom_interval])
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(),
                        self.txt_retention, 
                        self.sw_notification
                    ]), 
                    padding=10, 
                    bgcolor="white", 
                    border_radius=10, 
                    border=ft.border.all(1, "#eee")
                ),
                ft.Divider(height=20),
                ft.Text("İlgi Alanı Kelimeleri", size=16, weight="bold", color="teal"),
                ft.Row([
                    self.txt_keyword, 
                    ft.IconButton(
                        ft.Icons.ADD_CIRCLE, 
                        icon_color="teal", 
                        icon_size=35, 
                        on_click=self.add_keyword
                    )
                ]),
                ft.Container(
                    content=self.keywords_wrap, 
                    padding=5, 
                    bgcolor="#f0f0f0", 
                    border_radius=10
                ),
                ft.Divider(height=20),
                ft.Text("RSS Kaynakları", size=16, weight="bold", color="teal"),
                ft.Container(
                    content=ft.Row([
                        self.txt_source_name, 
                        self.txt_source_url, 
                        ft.IconButton(
                            ft.Icons.ADD_CIRCLE, 
                            icon_color="teal", 
                            icon_size=35, 
                            on_click=self.add_source_click
                        ), 
                        self.pr_adding
                    ]), 
                    padding=10, 
                    bgcolor="white", 
                    border_radius=10
                ),
                self.sources_list
            ], expand=True, scroll=ft.ScrollMode.AUTO), 
            padding=20
        )

        return ft.View(
            "/medical_news", 
            controls=[
                ft.Container(
                    content=ft.Tabs(
                        selected_index=0, 
                        indicator_color="teal", 
                        label_color="teal", 
                        tabs=[
                            ft.Tab(text="Bülten", icon=ft.Icons.NEWSPAPER, content=tab_news),
                            ft.Tab(text="Listem", icon=ft.Icons.BOOKMARKS, content=tab_saved),
                            ft.Tab(text="Ayarlar", icon=ft.Icons.TUNE, content=tab_sources)
                        ], 
                        expand=True
                    ), 
                    padding=20, 
                    bgcolor="#f8f9fa", 
                    expand=True
                )
            ], 
            padding=0
        )

    # --- RSS MOTORU ---
    def get_content_safe(self, url):
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://google.com"}
        try: 
            return requests.get(url, headers=headers, timeout=15, verify=True).content
        except: 
            try: 
                return requests.get(url, headers=headers, timeout=15, verify=False).content
            except: 
                return None

    def fetch_rss_logic(self, is_background=False):
        sources = self.db.cursor.execute("SELECT name, url FROM news_sources").fetchall()
        try: 
            existing_links = set(row[0] for row in self.db.cursor.execute("SELECT link FROM medical_news").fetchall())
        except: 
            existing_links = set()
        
        new_items = []
        for sname, url in sources:
            content = self.get_content_safe(url)
            if not content: 
                continue
            try:
                d = feedparser.parse(content)
                for entry in d.entries[:10]:
                    if entry.link in existing_links: 
                        continue
                    summary = re.sub(r'<[^>]+>', '', entry.summary if 'summary' in entry else "")[:250] + "..."
                    img_url = None
                    if 'media_content' in entry: 
                        img_url = entry.media_content[0]['url']
                    elif 'media_thumbnail' in entry: 
                        img_url = entry.media_thumbnail[0]['url']
                    if not img_url and 'src="' in str(entry):
                        try: 
                            match = re.search(r'src="(.*?)"', str(entry))
                            img_url = match.group(1) if match else None
                        except: 
                            pass
                    new_items.append((entry.title, summary, entry.link, datetime.now().strftime("%Y-%m-%d"), sname, img_url))
            except: 
                pass
        
        if new_items:
            try:
                self.db.cursor.executemany(
                    "INSERT INTO medical_news (title, summary, link, published_date, source, image_url, is_read, is_saved) VALUES (?, ?, ?, ?, ?, ?, 0, 0)", 
                    new_items
                )
                self.db.conn.commit()
            except: 
                pass
        
        if not is_background:
            self.loading_bar.visible = False
            self.txt_log.value = f"Son: {datetime.now().strftime('%H:%M')} ({len(new_items)} yeni)"
            self.reset_and_load()
            self.page.update()
            if len(new_items) > 0: 
                self.page.open(ft.SnackBar(ft.Text(f"{len(new_items)} yeni haber!"), bgcolor="green"))
        elif len(new_items) > 0 and self.show_notifications:
            self.reset_and_load()
            self.page.open(ft.SnackBar(content=ft.Text(f"{len(new_items)} yeni haber!"), bgcolor="teal"))
            self.page.update()

    def start_auto_refresh_service(self):
        if self.service_running: 
            return
        self.service_running = True
        
        def loop():
            time.sleep(2)
            self.fetch_rss_logic(is_background=True)
            while True:
                try: 
                    interval = int(self.txt_custom_interval.value)
                except: 
                    interval = int(self.dd_refresh.value)
                if interval <= 0: 
                    time.sleep(10)
                    continue
                for _ in range(interval * 60): 
                    time.sleep(1)
                self.fetch_rss_logic(is_background=True)
        
        threading.Thread(target=loop, daemon=True).start()

    def save_refresh_settings(self, e):
        interval = self.dd_refresh.value
        if self.txt_custom_interval.value and self.txt_custom_interval.value.isdigit(): 
            interval = self.txt_custom_interval.value
        self.db.set_setting("news_refresh_interval", interval)
        self.db.set_setting("news_retention_days", self.txt_retention.value)
        self.db.set_setting("news_notifications", "1" if self.sw_notification.value else "0")
        self.refresh_interval = int(interval)
        self.retention_days = int(self.txt_retention.value)
        self.show_notifications = self.sw_notification.value
        self.page.open(ft.SnackBar(ft.Text("Ayarlar Güncellendi"), bgcolor="green"))

    def refresh_news_click(self, e):
        self.loading_bar.visible = True
        self.txt_log.value = "Taranıyor..."
        self.page.update()
        threading.Thread(target=self.fetch_rss_logic, args=(False,), daemon=True).start()

    def reset_and_load(self):
        self.offset = 0
        self.news_grid.controls.clear()
        self.load_next_batch()

    def load_more_news(self, e):
        self.load_next_batch()

    def load_next_batch(self):
        if self.loading: 
            return
        self.loading = True
        try:
            news = self.db.cursor.execute(
                f"SELECT id, title, summary, link, source, published_date, is_saved, image_url FROM medical_news ORDER BY id DESC LIMIT {self.limit} OFFSET {self.offset}"
            ).fetchall()
            
            if not news:
                if self.offset == 0: 
                    self.news_grid.controls.append(ft.Text("Haber yok.", color="grey"))
                else: 
                    self.btn_load_more.visible = False
                    self.page.update()
                self.loading = False
                return
            
            relevant, other = [], []
            for n in news:
                if self.sw_filter.value and self.is_relevant(n[1], n[2]): 
                    relevant.append(n)
                else: 
                    other.append(n)
            
            for n in relevant + other: 
                self.create_news_card(n, is_priority=(n in relevant), target_grid=self.news_grid)
            
            self.offset += self.limit
            self.loading = False
            self.btn_load_more.visible = True
            self.page.update()
        except: 
            self.loading = False

    def load_saved_news(self):
        """Kaydedilen haberleri yükler"""
        self.saved_grid.controls.clear()
        try:
            news = self.db.cursor.execute(
                "SELECT id, title, summary, link, source, published_date, is_saved, image_url FROM medical_news WHERE is_saved=1 ORDER BY id DESC"
            ).fetchall()
            
            if not news: 
                self.saved_grid.controls.append(ft.Text("Kaydedilen haber yok.", color="grey"))
            else:
                for n in news: 
                    self.create_news_card(n, False, self.saved_grid)
            self.saved_grid.update()
        except: 
            pass

    def is_relevant(self, title, summary):
        """
        Haberin kullanıcının branşıyla ilgili olup olmadığını kontrol eder.
        ✅ EKLENDİ - Bu metod eksikti
        """
        try:
            # Anahtar kelimeleri veritabanından al
            keywords = self.db.cursor.execute("SELECT keyword FROM news_keywords").fetchall()
            keyword_list = [k[0].lower() for k in keywords if k[0]]
            
            # Branş bazlı anahtar kelimeler
            specialty_keywords = {
                "Dis": ["diş", "dental", "ortodonti", "implant", "ağız", "çene", "periodont"],
                "Fizyo": ["fizik tedavi", "rehabilitasyon", "fizyoterapi", "kas", "eklem", "omurga", "manuel terapi"],
                "Diyet": ["beslenme", "diyet", "obezite", "kilo", "metabolizma", "vitamin", "protein"],
                "Psiko": ["psikoloji", "terapi", "anksiyete", "depresyon", "mental", "ruh sağlığı", "stres"],
                "Kardiyo": ["kalp", "kardiyoloji", "damar", "tansiyon", "kolesterol", "ritim", "koroner"],
                "Genel": ["sağlık", "tıp", "hastane", "tedavi", "ilaç", "hastalık"]
            }
            
            # Kullanıcı branşına göre anahtar kelimeler ekle
            if self.user_specialty in specialty_keywords:
                keyword_list.extend(specialty_keywords[self.user_specialty])
            
            # Başlık ve özette anahtar kelime ara
            text = ((title or "") + " " + (summary or "")).lower()
            
            for kw in keyword_list:
                if kw and kw.lower() in text:
                    return True
            
            return False
        except Exception as e:
            print(f"is_relevant hatası: {e}")
            return False

    # --- KART TASARIMI ---
    def create_news_card(self, n, is_priority, target_grid):
        news_id, title, summary, link, source, date, is_saved, img_url = n
        is_saved_bool = (is_saved == 1)
        final_img = img_url if (img_url and len(str(img_url)) > 5) else "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=500&q=80"
        
        badge = ft.Container(
            content=ft.Text("ÖZEL", size=8, color="white", weight="bold"), 
            bgcolor="red", 
            padding=3, 
            border_radius=3
        ) if is_priority else ft.Container()
        
        btn_save = ft.IconButton(
            icon=ft.Icons.BOOKMARK if is_saved_bool else ft.Icons.BOOKMARK_BORDER, 
            icon_color="teal" if is_saved_bool else "grey", 
            icon_size=24, 
            tooltip="Kaydet", 
            on_click=lambda e, nid=news_id: self.toggle_save(e, nid)
        )

        card = ft.Container(
            content=ft.Column([
                ft.Image(
                    src=final_img, 
                    height=180, 
                    width=float("inf"), 
                    fit=ft.ImageFit.COVER, 
                    border_radius=ft.border_radius.only(top_left=10, top_right=10)
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Row([
                                ft.Container(
                                    content=ft.Text(source[:20] if source else "", size=9, color="white", weight="bold"), 
                                    bgcolor="grey", 
                                    padding=2, 
                                    border_radius=3
                                ), 
                                badge
                            ]), 
                            btn_save
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(
                            title, 
                            weight="bold", 
                            size=14, 
                            max_lines=2, 
                            overflow=ft.TextOverflow.ELLIPSIS, 
                            color="teal" if is_priority else "black"
                        ),
                        ft.Text(date[:10] if date else "", size=10, color="grey"),
                        ft.Text(
                            summary, 
                            size=12, 
                            color="#444", 
                            max_lines=3, 
                            overflow=ft.TextOverflow.ELLIPSIS
                        ),
                    ], spacing=3), 
                    padding=8 
                )
            ], spacing=0),
            bgcolor="white", 
            border_radius=10, 
            shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.1, "black")), 
            border=ft.border.all(1, "teal" if is_priority else "#e0e0e0"),
            on_click=lambda e: self.page.launch_url(link),
            animate_scale=ft.Animation(200, ft.AnimationCurve.EASE_OUT), 
            on_hover=lambda e: self.animate_card(e)
        )
        target_grid.controls.append(card)

    def toggle_save(self, e, news_id):
        try:
            cur = self.db.cursor.execute("SELECT is_saved FROM medical_news WHERE id=?", (news_id,)).fetchone()[0]
            new = 0 if cur == 1 else 1
            self.db.cursor.execute("UPDATE medical_news SET is_saved=? WHERE id=?", (new, news_id))
            self.db.conn.commit()
            e.control.icon = ft.Icons.BOOKMARK if new == 1 else ft.Icons.BOOKMARK_BORDER
            e.control.icon_color = "teal" if new == 1 else "grey"
            e.control.update()
        except: 
            pass

    def animate_card(self, e):
        e.control.scale = 1.02 if e.data == "true" else 1.0
        e.control.shadow = ft.BoxShadow(
            blur_radius=15, 
            color=ft.Colors.with_opacity(0.2, "black")
        ) if e.data == "true" else ft.BoxShadow(
            blur_radius=5, 
            color=ft.Colors.with_opacity(0.1, "black")
        )
        e.control.update()

    def add_source_click(self, e):
        name, url = self.txt_source_name.value.strip(), self.txt_source_url.value.strip()
        if not name or not url: 
            return
        self.pr_adding.visible = True
        e.control.disabled = True
        self.page.update()
        threading.Thread(target=self.add_source_logic, args=(name, url)).start()

    def add_source_logic(self, name, url):
        msg = "Hata"
        color = "red"
        content = self.get_content_safe(url)
        if content and (feedparser.parse(content).entries or feedparser.parse(content).feed.get('title')):
            self.db.cursor.execute("INSERT INTO news_sources (name, url) VALUES (?, ?)", (name, url))
            self.db.conn.commit()
            msg = "Eklendi!"
            color = "green"
        else: 
            msg = "Geçersiz RSS."
        
        self.pr_adding.visible = False
        self.txt_source_name.value = ""
        self.txt_source_url.value = ""
        self.page.open(ft.SnackBar(ft.Text(msg), bgcolor=color))
        self.load_sources() 
        self.page.update()

    def delete_source(self, sid):
        self.db.cursor.execute("DELETE FROM news_sources WHERE id=?", (sid,))
        self.db.conn.commit()
        self.load_sources()

    def load_sources(self):
        self.sources_list.controls.clear()
        try:
            for s in self.db.cursor.execute("SELECT id, name, url FROM news_sources").fetchall():
                self.sources_list.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.RSS_FEED, color="teal"), 
                        title=ft.Text(s[1], size=12), 
                        subtitle=ft.Text(s[2], size=10), 
                        trailing=ft.IconButton(
                            ft.Icons.DELETE, 
                            icon_size=18, 
                            icon_color="red", 
                            on_click=lambda e, x=s[0]: self.delete_source(x)
                        ), 
                        dense=True
                    )
                )
            self.sources_list.update()
        except: 
            pass

    def load_keywords(self):
        self.keywords_wrap.controls.clear()
        try:
            for k in self.db.cursor.execute("SELECT id, keyword FROM news_keywords").fetchall():
                self.keywords_wrap.controls.append(
                    ft.Chip(
                        label=ft.Text(k[1], color="white"), 
                        bgcolor="teal", 
                        delete_icon_color="white", 
                        on_delete=lambda e, x=k[0]: self.delete_keyword(x)
                    )
                )
            self.keywords_wrap.update()
        except: 
            pass

    def add_keyword(self, e):
        val = self.txt_keyword.value.strip()
        if val: 
            self.db.cursor.execute("INSERT INTO news_keywords (keyword) VALUES (?)", (val,))
            self.db.conn.commit()
            self.txt_keyword.value = ""
            self.load_keywords()

    def delete_keyword(self, kid):
        self.db.cursor.execute("DELETE FROM news_keywords WHERE id=?", (kid,))
        self.db.conn.commit()
        self.load_keywords()
