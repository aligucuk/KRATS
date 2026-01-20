import sys
import time
import zipfile
import os
import shutil
import subprocess

def install_update(zip_path, target_dir):
    # Ana uygulamanın tamamen kapanması için 2 saniye bekle
    print("Güncelleme başlatılıyor, lütfen bekleyin...")
    time.sleep(2)

    try:
        # 1. Zip dosyasını aç
        print(f"Paket açılıyor: {zip_path}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("temp_update")

        # 2. Dosyaları kopyala (Overwrite)
        # GitHub zip dosyaları genellikle bir klasör içinde gelir (Repo-main/), onu bulalım.
        extracted_folder = os.listdir("temp_update")[0]
        source_path = os.path.join("temp_update", extracted_folder)

        print("Dosyalar güncelleniyor...")
        for item in os.listdir(source_path):
            s = os.path.join(source_path, item)
            d = os.path.join(target_dir, item)
            
            # .env veya veritabanı gibi dosyaları ezmemeliyiz!
            if item in [".env", "klinik_db", "assets/uploads", "updater.py"]:
                continue
                
            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d) # Eski klasörü sil
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

        # 3. Temizlik
        print("Temizlik yapılıyor...")
        shutil.rmtree("temp_update")
        os.remove(zip_path)

        print("Güncelleme tamamlandı! Uygulama başlatılıyor...")
        
        # 4. Ana uygulamayı tekrar başlat
        if sys.platform == "win32":
            subprocess.Popen([sys.executable, "main.py"])
        else:
            subprocess.Popen(["python3", "main.py"])
            
    except Exception as e:
        print(f"HATA OLUŞTU: {e}")
        input("Çıkmak için Enter'a basın...")

if __name__ == "__main__":
    # Kullanım: python updater.py update.zip .
    if len(sys.argv) > 1:
        zip_file = sys.argv[1]
        target = os.getcwd()
        install_update(zip_file, target)