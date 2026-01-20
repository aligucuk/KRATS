import os
import sqlite3
from database.db_manager import DatabaseManager

def full_reset():
    db_file = "clinic.db"
    
    print("⚠️  DİKKAT: Bu işlem TÜM hastaları, randevuları ve kullanıcıları SİLECEK!")
    confirm = input("Onaylıyor musunuz? (evet/hayır): ")
    
    if confirm.lower() != "evet":
        print("❌ İşlem iptal edildi.")
        return

    # 1. YÖNTEM: Dosyayı fiziksel olarak sil (En temiz yöntem)
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
            print(f"🗑️  Eski veritabanı dosyası ({db_file}) silindi.")
        except Exception as e:
            print(f"⚠️  Dosya silinemedi (Kullanımda olabilir): {e}")
            print("🔄  Alternatif yöntem (Tablo silme) deneniyor...")
            # Dosya silinemezse tabloları düşür
            try:
                db = DatabaseManager()
                db.factory_reset() # Eğer refactor edilmiş kodu kullanıyorsan
            except:
                # Manuel tablo temizliği
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                for table in tables:
                    cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
                conn.commit()
                conn.close()

    # 2. ADIM: Veritabanını Yeniden Başlat (Varsayılan Admin ile)
    print("🔄  Veritabanı yeniden kuruluyor...")
    try:
        # DatabaseManager başlatıldığında init_db otomatik çalışır
        manager = DatabaseManager()
        # Eğer init_db otomatik çağrılmıyorsa manuel çağır:
        # manager.init_db() 
        
        print("\n✅ SIFIRLAMA BAŞARILI!")
        print("==========================================")
        print("🔑  Yeni Giriş Bilgileri:")
        print("👤  Kullanıcı Adı : admin")
        print("🔑  Şifre         : admin")
        print("==========================================")
    except Exception as e:
        print(f"❌  Kurulum sırasında hata oluştu: {e}")

if __name__ == "__main__":
    full_reset()