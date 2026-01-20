import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# ✅ Düzeltildi: Şifre environment variable'dan okunuyor
DB_PASSWORD = os.getenv('DB_PASSWORD', '1234')  # Varsayılan: 1234

# Veritabanı sunucusuna bağlan (Varsayılan 'postgres' veritabanına)
try:
    con = psycopg2.connect(
        dbname='postgres', 
        user='postgres', 
        host='localhost', 
        password=DB_PASSWORD
    )
    
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = con.cursor()
    
    # Veritabanını oluştur
    cursor.execute("CREATE DATABASE klinik_db;")
    print("✅ klinik_db Başarıyla Oluşturuldu!")
    
except psycopg2.errors.DuplicateDatabase:
    print("⚠️  klinik_db zaten mevcut.")
except Exception as e:
    print(f"❌ Hata: {e}")
    print("\n💡 İpucu: PostgreSQL şifrenizi .env dosyasına ekleyin:")
    print("   DB_PASSWORD=your_password")

finally:
    if 'con' in locals():
        con.close()