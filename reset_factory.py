import os
import shutil
from datetime import datetime

def factory_reset():
    print("⚠️  FABRİKA AYARLARINA DÖNÜLÜYOR... ⚠️")
    print("-" * 40)

    # 1. Lisans ve Google Oturumunu SİL (Kalıcı)
    files_to_delete = ["license.key", "token.json"]
    
    for filename in files_to_delete:
        if os.path.exists(filename):
            try:
                os.remove(filename)
                print(f"✅ SİLİNDİ: {filename}")
            except Exception as e:
                print(f"❌ SİLİNEMEDİ {filename}: {e}")
        else:
            print(f"⚪ Zaten yok: {filename}")

    # 2. Veritabanını YEDEKLE ve SAKLA (Silmek yerine ismini değiştirir)
    db_file = "krats.db"
    if os.path.exists(db_file):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"krats_YEDEK_{timestamp}.db"
        try:
            os.rename(db_file, backup_name)
            print(f"📦 YEDEKLENDİ: {db_file} -> {backup_name} (Sıfır DB oluşturulacak)")
        except Exception as e:
            print(f"❌ DB HATA: {e}")
    else:
        print("⚪ Veritabanı zaten yok.")

    print("-" * 40)
    print("🚀 İŞLEM TAMAM! Programı (main.py) şimdi açarsan sıfırdan kurulum yapacak.")

if __name__ == "__main__":
    confirm = input("TÜM VERİLER VE LİSANS SIFIRLANACAK. Emin misin? (e/h): ")
    if confirm.lower() == "e":
        factory_reset()
    else:
        print("İptal edildi.")