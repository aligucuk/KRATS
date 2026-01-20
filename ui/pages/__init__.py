# ui/pages/__init__.py

from .login import LoginPage
from .doctor_home import DoctorHomePage
from .patient_list import PatientListPage
from .add_patient import AddPatientPage
from .patient_detail import PatientDetailPage
from .appointments import AppointmentsPage
from .crm_page import CRMPage
from .finance import FinancePage
from .inventory import InventoryPage
from .chat_page import ChatPage
from .ai_assistant import AIAssistantPage
from .medical_news import MedicalNewsPage
from .settings import SettingsPage
from .tv_display import TVDisplayPage
from .medical_detail import MedicalDetailPage

# ACTIVATED HIDDEN FEATURES
from .backup import BackupPage
from .audit_logs import AuditLogsPage
from .statistics import StatisticsPage

__all__ = [
    "LoginPage",
    "DoctorHomePage",
    "PatientListPage",
    "AddPatientPage",
    "PatientDetailPage",
    "AppointmentsPage",
    "CRMPage",
    "FinancePage",
    "InventoryPage",
    "ChatPage",
    "AIAssistantPage",
    "MedicalNewsPage",
    "SettingsPage",
    "TVDisplayPage",
    "MedicalDetailPage",
    "BackupPage",
    "AuditLogsPage",
    "StatisticsPage"
]