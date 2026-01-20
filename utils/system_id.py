import subprocess
import platform
import uuid
import hashlib

def get_raw_hwid():
    """İşletim sisteminden ham UUID verisini çeker."""
    system = platform.system()
    try:
        if system == "Windows":
            # Windows'ta UUID çekme komutu
            cmd = "wmic csproduct get uuid"
            output = subprocess.check_output(cmd, shell=True).decode()
            # Çıktıyı temizle (Header ve boşlukları at)
            lines = output.split("\n")
            for line in lines:
                if "UUID" not in line and len(line.strip()) > 5:
                    return line.strip()
            return str(uuid.getnode()) # Fallback

        elif system == "Darwin": # macOS
            # Mac'te IOPlatformUUID çekme
            cmd = "ioreg -d2 -c IOPlatformExpertDevice | awk -F\\\" '/IOPlatformUUID/{print $(NF-1)}'"
            return subprocess.check_output(cmd, shell=True).decode().strip()
        
        else:
            # Linux vs. için basit MAC adresi
            return str(uuid.getnode())
    except Exception as e:
        print(f"HWID Hatası: {e}")
        return str(uuid.getnode())

def get_device_fingerprint():
    """
    Ham UUID'yi alır ve kısa, güvenli bir MD5 Hash'ine dönüştürür.
    Çıktı Örneği: 'd41d8cd98f00b204e9800998ecf8427e'
    """
    raw_id = get_raw_hwid()
    
    # Ham veriyi şifrele (Hash'le)
    hashed = hashlib.md5(raw_id.encode()).hexdigest()
    
    return hashed

# Test Etmek İçin
if __name__ == "__main__":
    print(f"Ham UUID: {get_raw_hwid()}")
    print(f"Lisans Parmak İzi: {get_device_fingerprint()}")