class LanguageManager:
    def __init__(self, lang_code="tr"):
        self.current_lang = lang_code
        self.translations = {
            "tr": {
                "app_title": "RNDV4 Klinik",
                "login_title": "Güvenli Giriş",
                "login_subtitle": "Klinik Yönetim Sistemi",
                "username": "Kullanıcı Adı",
                "password": "Şifre",
                "login_btn": "GİRİŞ YAP",
                "select_lang": "Dil",
                "error_login": "Hatalı Kullanıcı Adı veya Şifre!",
                "success_login": "Giriş Başarılı, Yönlendiriliyorsunuz..."
            },
            "en": {
                "app_title": "RNDV4 Clinic",
                "login_title": "Secure Login",
                "login_subtitle": "Clinic Management System",
                "username": "Username",
                "password": "Password",
                "login_btn": "LOGIN",
                "select_lang": "Language",
                "error_login": "Invalid Username or Password!",
                "success_login": "Login Successful, Redirecting..."
            },
            "de": {
                "app_title": "RNDV4 Klinik",
                "login_title": "Sichere Anmeldung",
                "login_subtitle": "Klinikmanagementsystem",
                "username": "Benutzername",
                "password": "Passwort",
                "login_btn": "ANMELDEN",
                "select_lang": "Sprache",
                "error_login": "Ungültiger Benutzername oder Passwort!",
                "success_login": "Anmeldung erfolgreich..."
            }
        }

    def get(self, key):
        return self.translations.get(self.current_lang, self.translations["tr"]).get(key, key)

    def set_language(self, lang_code):
        self.current_lang = lang_code

    def __getitem__(self, key):
        return self.get(key)

# KRİTİK NOKTA: Bu satır olmazsa main.py hata verir
TR = LanguageManager()