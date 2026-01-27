# services/google_calendar_service.py

import os
from datetime import datetime, timedelta
from typing import Tuple, Optional
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import settings
from utils.logger import get_logger
from utils.exceptions import IntegrationException

logger = get_logger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar']


class GoogleCalendarService:
    """Google Calendar integration service"""
    
    def __init__(self, *args, **kwargs):
        """Initialize Google Calendar service"""
        self.creds = None
        self.service = None
        self.token_path = settings.BASE_DIR / "token.json"
        self.credentials_path = settings.BASE_DIR / "credentials.json"
        
        if settings.GOOGLE_CALENDAR_ENABLED:
            self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        try:
            # Load existing token
            if self.token_path.exists():
                self.creds = Credentials.from_authorized_user_file(
                    str(self.token_path), SCOPES
                )
            
            # Refresh or get new token
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    try:
                        self.creds.refresh(Request())
                        logger.info("Google Calendar token refreshed")
                    except Exception as e:
                        logger.warning(f"Token refresh failed: {e}")
                        self.creds = None
                
                # Get new credentials
                if not self.creds and self.credentials_path.exists():
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path), SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)
                    
                    # Save token
                    with open(self.token_path, 'w') as token:
                        token.write(self.creds.to_json())
                    
                    logger.info("New Google Calendar credentials obtained")
            
            # Build service
            if self.creds:
                self.service = build('calendar', 'v3', credentials=self.creds)
                logger.info("Google Calendar service initialized")
            else:
                logger.warning("Google Calendar credentials not available")
        
        except Exception as e:
            logger.error(f"Google Calendar authentication failed: {e}")
            self.service = None
    
    def add_appointment(
        self, title: str, date_str: str, time_str: str,
        description: str = "", duration_minutes: int = 30
    ) -> Tuple[bool, str]:
        """Add appointment to Google Calendar
        
        Args:
            title: Event title
            date_str: Date in YYYY-MM-DD format
            time_str: Time in HH:MM format
            description: Event description
            duration_minutes: Event duration in minutes
            
        Returns:
            Tuple of (success, message/event_link)
        """
        if not self.service:
            return False, "Google Calendar servisi bağlı değil"
        
        try:
            # Parse datetime
            start_datetime_str = f"{date_str}T{time_str}:00"
            start_dt = datetime.strptime(start_datetime_str, "%Y-%m-%dT%H:%M:%S")
            end_dt = start_dt + timedelta(minutes=duration_minutes)
            
            # Create event
            event = {
                'summary': title,
                'location': 'Klinik',
                'description': description,
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': settings.TIMEZONE,
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': settings.TIMEZONE,
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 60},
                        {'method': 'email', 'minutes': 1440},  # 24 hours
                    ],
                },
            }
            
            # Insert event
            result = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            event_link = result.get('htmlLink', '')
            logger.info(f"Event added to Google Calendar: {title}")
            
            return True, event_link
        
        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return False, f"Google API hatası: {e.reason}"
        except Exception as e:
            logger.error(f"Failed to add event: {e}")
            return False, f"Etkinlik eklenemedi: {str(e)}"
    
    def is_connected(self) -> bool:
        """Check if Google Calendar is connected"""
        return self.service is not None
    
    def disconnect(self) -> bool:
        """Disconnect Google Calendar (remove token)"""
        try:
            if self.token_path.exists():
                self.token_path.unlink()
            
            self.creds = None
            self.service = None
            
            logger.info("Google Calendar disconnected")
            return True
        
        except Exception as e:
            logger.error(f"Failed to disconnect: {e}")
            return False


# Global instance
google_calendar_service = GoogleCalendarService()
