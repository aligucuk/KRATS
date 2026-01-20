import requests
import json

# Senin R2 Güncelleme URL'in
REMOTE_CONFIG_URL = "https://update.baseguc.com/config.json"

# İnternet yoksa kullanılacak varsayılan ayarlar (Yedek Paraşüt)
DEFAULT_CONFIG = {
    "maintenance_mode": False,
    "maintenance_message": "",
    "min_version": "1.0.0",
    "hsys": {
        "api_url": "https://sys.saglik.gov.tr/SYS/SYS.asmx",
        "soap_action": "http://saglik.gov.tr/SYSSendMessage"
    }
}

def get_app_config():
    """
    Önce buluttaki config.json dosyasını okumaya çalışır.
    Başarısız olursa (internet yoksa) varsayılan ayarları döndürür.
    """
    print("🌍 Bulut yapılandırması kontrol ediliyor...")
    
    try:
        response = requests.get(REMOTE_CONFIG_URL, timeout=6)
        
        if response.status_code == 200:
            remote_data = response.json()
            print("✅ Güncel ayarlar buluttan çekildi!")
            return remote_data
        else:
            print(f"⚠️ Sunucu hatası: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"🔌 İnternet bağlantısı yok veya sunucuya ulaşılamadı. Offline mod.")
    
    # Hata durumunda varsayılanı döndür
    return DEFAULT_CONFIG