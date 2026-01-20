import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Veritabanı sunucusuna bağlan (Varsayılan 'postgres' veritabanına)
# Şifre kısmına kendi PostgreSQL şifreni yaz (genelde 1234, admin123 veya boş)
try:
    con = psycopg2.connect(
        dbname='postgres', 
        user='postgres', 
        host='localhost', 
        password='1234' # <-- BURAYI KENDİ ŞİFRENLE GÜNCELLE
    )
    
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = con.cursor()
    
    # Veritabanını oluştur
    cursor.execute("CREATE DATABASE klinik_db;")
    print("✅ klinik_db Başarıyla Oluşturuldu!")
    
except Exception as e:
    print(f"❌ Hata: {e}")

finally:
    if 'con' in locals():
        con.close()