class Localization:
    # Dil Sözlüğü
    TEXTS = {
        "TR": {
            "welcome": "Hoş Geldiniz",
            "save": "Kaydet",
            "cancel": "İptal",
            "patient_add": "Yeni Hasta Ekle",
            "name": "Ad Soyad",
            "tc": "TC / Pasaport No",
            "phone": "Telefon",
            "address": "Adres",
            "crm_title": "Müşteri İlişkileri (CRM)",
            "status": "Durum",
            "source": "Kaynak",
            "wa_send": "WhatsApp Mesajı Gönder",
            "settings": "Ayarlar"
        },
        "EN": { # UK ve US için
            "welcome": "Welcome",
            "save": "Save",
            "cancel": "Cancel",
            "patient_add": "Add New Patient",
            "name": "Full Name",
            "tc": "ID / Passport No",
            "phone": "Phone",
            "address": "Address",
            "crm_title": "Customer Relations (CRM)",
            "status": "Status",
            "source": "Source",
            "wa_send": "Send WhatsApp Message",
            "settings": "Settings"
        },
        "DE": { # Almanya için
            "welcome": "Willkommen",
            "save": "Speichern",
            "cancel": "Abbrechen",
            "patient_add": "Neuen Patienten hinzufügen",
            "name": "Vorname Nachname",
            "tc": "Ausweisnummer",
            "phone": "Telefon",
            "address": "Adresse",
            "crm_title": "Kundenbeziehungen (CRM)",
            "status": "Status",
            "source": "Quelle",
            "wa_send": "WhatsApp Nachricht senden",
            "settings": "Einstellungen"
        }
    }

    @staticmethod
    def get(key, country_code="TR"):
        # Ülke koduna göre dili seç
        lang = "TR"
        if country_code in ["UK", "US"]: lang = "EN"
        elif country_code == "DE": lang = "DE"
        elif country_code == "KKTC": lang = "TR"
        
        return Localization.TEXTS.get(lang, {}).get(key, key)