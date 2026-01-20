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
        self.service = None
        
        # Token daha önce alındıysa yükle
        if os.path.exists('token.json'):
            try:
                self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            except Exception as e:
                print(f"Token okuma hatası: {e}")
                self.creds = None
        
        # Token yoksa veya süresi dolduysa yenile
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    print(f"Token yenileme hatası: {e}")
                    self.creds = None
            
            # Eğer hala geçerli kredimiz yoksa, kullanıcıdan giriş iste
            if not self.creds:
                if os.path.exists('credentials.json'):
                    try:
                        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                        self.creds = flow.run_local_server(port=0)
                        # Bir dahaki sefere sormamak için kaydet
                        with open('token.json', 'w') as token:
                            token.write(self.creds.to_json())
                    except Exception as e:
                        print(f"OAuth akış hatası: {e}")
                        return
                else:
                    print("⚠️ UYARI: 'credentials.json' dosyası bulunamadı. Google Sync çalışmaz.")
                    return

        try:
            self.service = build('calendar', 'v3', credentials=self.creds)
        except Exception as e:
            print(f"Google Servis Hatası: {e}")
            self.service = None

    def connect_account(self):
        """
        Google hesabına bağlanır ve durumu döndürür.
        Dönüş: (success: bool, message: str)
        """
        if self.service:
            return True, "✅ Google Takvim başarıyla bağlandı!"
        
        # Credentials dosyası var mı kontrol et
        if not os.path.exists('credentials.json'):
            return False, "❌ credentials.json dosyası bulunamadı. Google Cloud Console'dan indirin."
        
        # Token var mı kontrol et
        if os.path.exists('token.json'):
            return False, "⚠️ Token mevcut ama servis başlatılamadı. Token'ı silip tekrar deneyin."
        
        return False, "❌ Bağlantı başarısız. Lütfen tekrar deneyin."

    def add_appointment(self, title, date_str, time_str, description=""):
        """
        Google Takvim'e etkinlik ekler.
        date_str: '2026-01-20'
        time_str: '14:30'
        """
        if not self.service: 
            return False, "Google Servisi Bağlı Değil"

        try:
            # Tarih ve Saati ISO Formatına Çevir (RFC3339)
            start_datetime_str = f"{date_str}T{time_str}:00"
            start_dt = datetime.datetime.strptime(start_datetime_str, "%Y-%m-%dT%H:%M:%S")
            end_dt = start_dt + datetime.timedelta(minutes=30)  # Varsayılan 30 dk randevu

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
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 30},
                    ],
                },
            }

            event_result = self.service.events().insert(calendarId='primary', body=event).execute()
            return True, f"✅ Google Takvim'e Eklendi! (Link: {event_result.get('htmlLink')})"

        except Exception as e:
            return False, f"❌ Google Hata: {str(e)}"

    def get_events(self, max_results=10):
        """
        Yaklaşan etkinlikleri getirir.
        """
        if not self.service:
            return []
        
        try:
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            return events_result.get('items', [])
        except Exception as e:
            print(f"Etkinlik çekme hatası: {e}")
            return []

    def delete_event(self, event_id):
        """
        Belirtilen etkinliği siler.
        """
        if not self.service:
            return False, "Google Servisi Bağlı Değil"
        
        try:
            self.service.events().delete(calendarId='primary', eventId=event_id).execute()
            return True, "Etkinlik silindi"
        except Exception as e:
            return False, f"Silme hatası: {str(e)}"
