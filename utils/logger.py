import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(log_level=logging.INFO, log_file=None):
    """
    Uygulama genelinde loglama yapılandırması
    """
    # Log formatı
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Formatter oluştur
    formatter = logging.Formatter(log_format, datefmt=date_format)
    
    # Root logger'ı yapılandır
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Mevcut handler'ları temizle
    root_logger.handlers.clear()
    
    # Console handler ekle
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Dosya handler ekle (isteğe bağlı)
    if log_file:
        try:
            # Logs klasörünü oluştur
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            # Log dosyası yolu
            log_path = log_dir / log_file
            
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"Log dosyası oluşturulamadı: {e}")
    
    return root_logger

def get_logger(name):
    """
    Belirli bir modül için logger döndür
    
    Args:
        name (str): Logger adı (genellikle __name__)
    
    Returns:
        logging.Logger: Yapılandırılmış logger instance
    """
    return logging.getLogger(name)

# Varsayılan yapılandırma
if not logging.getLogger().handlers:
    setup_logging(
        log_level=logging.INFO,
        log_file=f"krats_{datetime.now().strftime('%Y%m%d')}.log"
    )
