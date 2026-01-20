import requests
import os
import sys
import subprocess

class UpdateManager:
    def __init__(self):
        self.current_version = self.get_local_version()
        # BURAYI KENDİ GITHUB REPO ADRESİNİZLE DEĞİŞTİRİN
        # Örnek: raw.githubusercontent.com/KULLANICI/REPO/main/version.txt
        self.VERSION_URL = "https://raw.githubusercontent.com/aligucuk/krats-updates/main/version.txt"
        self.ZIP_URL = "https://github.com/aligucuk/krats-updates/archive/refs/heads/main.zip"

    def get_local_version(self):
        try:
            with open("version.txt", "r") as f:
                return f.read().strip()
        except:
            return "0.0.0"

    def check_for_updates(self):
        """Sunucudan versiyonu kontrol eder. (Yeni sürüm varsa True döner)"""
        try:
            print(f"Kontrol ediliyor... URL: {self.VERSION_URL}")
            response = requests.get(self.VERSION_URL, timeout=5)
            if response.status_code == 200:
                remote_version = response.text.strip()
                print(f"Yerel: {self.current_version} | Sunucu: {remote_version}")
                
                # Basit bir versiyon kıyaslaması (Daha gelişmişi için 'packaging' kütüphanesi kullanılır)
                if remote_version != self.current_version:
                    return remote_version
            return None
        except Exception as e:
            print(f"Update Check Error: {e}")
            return None

    def download_and_restart(self, progress_callback=None):
        """Güncellemeyi indirir ve updater.py'yi tetikler"""
        try:
            # 1. İndirme
            print("İndirme başlıyor...")
            response = requests.get(self.ZIP_URL, stream=True)
            total_length = response.headers.get('content-length')
            
            save_path = "update_pkg.zip"
            
            with open(save_path, "wb") as f:
                if total_length is None: # İçerik boyutu yoksa direkt yaz
                    f.write(response.content)
                else:
                    dl = 0
                    total_length = int(total_length)
                    for data in response.iter_content(chunk_size=4096):
                        dl += len(data)
                        f.write(data)
                        if progress_callback:
                            progress_callback(dl / total_length) # İlerleme çubuğunu güncelle

            print("İndirme bitti. Updater başlatılıyor...")

            # 2. Updater Scriptini Başlat
            # python updater.py update_pkg.zip
            if sys.platform == "win32":
                subprocess.Popen([sys.executable, "updater.py", save_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([sys.executable, "updater.py", save_path])

            # 3. Ana uygulamayı kapat
            sys.exit(0)

        except Exception as e:
            print(f"Download Error: {e}")
            raise e