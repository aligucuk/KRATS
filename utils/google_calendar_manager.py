import os.path
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Google'ın izin yetkileri (Okuma ve Yazma)
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarManager:
    def __init__(self):
        self.creds = None
        # Token daha önce alındıysa yükle
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # Token yoksa veya süresi dolduysa yenile
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except:
                    self.creds = None # Yenilenemedi, baştan al
            
            # Eğer hala geçerli kredimiz yoksa, kullanıcıdan giriş iste
            if not self.creds:
                if os.path.exists('credentials.json'):
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                    self.creds = flow.run_local_server(port=0)
                    # Bir dahaki sefere sormamak için kaydet
                    with open('token.json', 'w') as token:
                        token.write(self.creds.to_json())
                else:
                    print("⚠️ UYARI: 'credentials.json' dosyası bulunamadı. Google Sync çalışmaz.")
                    return

        try:
            self.service = build('calendar', 'v3', credentials=self.creds)
        except Exception as e:
            print(f"Google Servis Hatası: {e}")
            self.service = None

    def add_appointment(self, title, date_str, time_str, description=""):
        """
        Google Takvim'e etkinlik ekler.
        date_str: '2026-01-20'
        time_str: '14:30'
        """
        if not self.service: return False, "Google Servisi Bağlı Değil"

        try:
            # Tarih ve Saati ISO Formatına Çevir (RFC3339)
            # Örn: '2026-01-20T14:30:00'
            start_datetime_str = f"{date_str}T{time_str}:00"
            start_dt = datetime.datetime.strptime(start_datetime_str, "%Y-%m-%dT%H:%M:%S")
            end_dt = start_dt + datetime.timedelta(minutes=30) # Varsayılan 30 dk randevu

            event = {
                'summary': f"Randevu: {title}",
                'location': 'Klinik',
                'description': description,
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': 'Europe/Istanbul',
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': 'Europe/Istanbul',
                },
            }

            event_result = self.service.events().insert(calendarId='primary', body=event).execute()
            return True, f"Google Takvim'e Eklendi! (Link: {event_result.get('htmlLink')})"

        except Exception as e:
            return False, f"Google Hata: {str(e)}"