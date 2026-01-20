import sqlite3
import os
import zipfile
import datetime
import threading
import shutil

class BackupManager:
    def __init__(self, db_manager):
        self.db = db_manager
        self.backup_dir = "backups"
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def create_backup(self, on_complete=None):
        """
        Yedekleme işlemini ayrı bir thread'de başlatır.
        on_complete: İşlem bitince çağrılacak callback fonksiyonu (success, message)
        """
        thread = threading.Thread(target=self._backup_worker, args=(on_complete,))
        thread.start()

    def _backup_worker(self, callback):
        success = False
        msg = ""
        temp_backup_file = f"temp_backup_{datetime.datetime.now().strftime('%H%M%S')}.db"
        
        try:
            # 1. Veritabanı dosyasının adını al (Clinic.db)
            source_db = self.db.db_name
            
            # 2. SQLite Online Backup API'sini kullan (Veri kaybı olmadan kopyalar)
            # Mevcut bağlantıyı kullanmak yerine yeni bir bağlantı açıp backup alıyoruz
            src = sqlite3.connect(source_db)
            dst = sqlite3.connect(temp_backup_file)
            
            with dst:
                src.backup(dst)
            
            dst.close()
            src.close()

            # 3. Dosyayı ZIP'le
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
            zip_filename = os.path.join(self.backup_dir, f"KRATS_Backup_{timestamp}.zip")
            
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(temp_backup_file, os.path.basename(source_db))
                
            # Ekstra dosyaları da (örneğin yüklenen resimler) ekleyebiliriz
            # if os.path.exists("uploads"): ...

            success = True
            msg = f"Yedek oluşturuldu: {zip_filename}"

        except Exception as e:
            success = False
            msg = f"Yedekleme Hatası: {str(e)}"
        
        finally:
            # Geçici dosyayı temizle
            if os.path.exists(temp_backup_file):
                os.remove(temp_backup_file)
            
            # Callback ile UI'a haber ver
            if callback:
                callback(success, msg)