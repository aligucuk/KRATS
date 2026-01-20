import sys
import os

# Proje yolunu ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from database.models import User, UserRole
from utils.security_manager import SecurityManager

def reset_admin_bcrypt():
    print("--- ADMIN ŞİFRESİ SIFIRLANIYOR (BCRYPT) ---")
    
    try:
        db = DatabaseManager()
        sec_manager = SecurityManager()
        
        # Şifre: admin
        password_plain = "admin"
        
        # Yeni bcrypt hash'ini oluştur
        password_hash = sec_manager.hash_password(password_plain)
        
        with db.get_session() as session:
            user = session.query(User).filter_by(username="admin").first()
            
            if user:
                print("Kullanıcı güncelleniyor...")
                user.password = password_hash
                user.role = UserRole.ADMIN
                user.is_active = True
            else:
                print("Kullanıcı oluşturuluyor...")
                new_user = User(
                    username="admin",
                    password=password_hash,
                    full_name="Sistem Yöneticisi",
                    role=UserRole.ADMIN,
                    commission_rate=0,
                    specialty="Genel",
                    is_active=True
                )
                session.add(new_user)
            
            session.commit()
            
        print("✅ İŞLEM BAŞARILI!")
        print(f"Yeni şifreniz (admin) güvenli BCrypt formatında kaydedildi.")
        print(f"Hash Örneği (Veritabanındaki hali): {password_hash[:10]}...")
        
    except Exception as e:
        print(f"❌ HATA: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reset_admin_bcrypt()