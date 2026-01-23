# scripts/download_skrs_resources.py
"""
SKRS/E-Nabız Kaynak İndirme ve Güncelleme Scripti
==================================================

Kullanım:
    python download_skrs_resources.py --all
    python download_skrs_resources.py --icd
    python download_skrs_resources.py --medications
    python download_skrs_resources.py --sut

Gereksinimler:
    pip install requests pandas openpyxl --break-system-packages
"""

import os
import sys
import argparse
import requests
from datetime import datetime
from pathlib import Path

# Proje kök dizinini ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_manager import DatabaseManager
from services.skrs_service import SKRSService
from utils.logger import get_logger

logger = get_logger(__name__)


class SKRSResourceDownloader:
    """SKRS kaynaklarını indir ve veritabanına aktar"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.skrs = SKRSService(db)
        self.download_dir = Path("downloads") / f"skrs_{datetime.now().strftime('%Y%m%d')}"
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Download directory: {self.download_dir}")
    
    # ==================== ICD-10 ====================
    
    def download_icd_codes(self, force: bool = False) -> bool:
        """
        ICD-10 kodlarını SKRS API'den çek
        
        Args:
            force: True ise cache'i ignore et
            
        Returns:
            bool: Başarılı mı
        """
        try:
            logger.info("Downloading ICD-10 codes from SKRS API...")
            
            # API'den çek ve veritabanına kaydet
            added, updated = self.skrs.sync_icd10_to_db(max_pages=100)
            
            logger.info(f"ICD-10 sync completed: {added} added, {updated} updated")
            
            # Özet rapor
            total = added + updated
            if total > 0:
                self._save_report("icd10_download_report.txt", {
                    "timestamp": datetime.now().isoformat(),
                    "added": added,
                    "updated": updated,
                    "total": total,
                    "source": "SKRS API"
                })
                print(f"\n✅ ICD-10 İndirme Başarılı!")
                print(f"   Yeni: {added}")
                print(f"   Güncellenen: {updated}")
                print(f"   Toplam: {total}")
                return True
            else:
                print(f"\n⚠️  ICD-10 güncel (değişiklik yok)")
                return True
                
        except Exception as e:
            logger.error(f"ICD-10 download failed: {e}")
            print(f"\n❌ ICD-10 İndirme Hatası: {e}")
            return False
    
    # ==================== MEDICATIONS ====================
    
    def download_medications(self, force: bool = False) -> bool:
        """
        İlaç listesini SKRS API'den çek
        
        Args:
            force: True ise cache'i ignore et
            
        Returns:
            bool: Başarılı mı
        """
        try:
            logger.info("Downloading medications from SKRS API...")
            
            # API'den çek ve veritabanına kaydet
            added, updated = self.skrs.sync_medications_to_db(max_pages=50)
            
            logger.info(f"Medications sync completed: {added} added, {updated} updated")
            
            # Özet rapor
            total = added + updated
            if total > 0:
                self._save_report("medications_download_report.txt", {
                    "timestamp": datetime.now().isoformat(),
                    "added": added,
                    "updated": updated,
                    "total": total,
                    "source": "SKRS API"
                })
                print(f"\n✅ İlaç Listesi İndirme Başarılı!")
                print(f"   Yeni: {added}")
                print(f"   Güncellenen: {updated}")
                print(f"   Toplam: {total}")
                return True
            else:
                print(f"\n⚠️  İlaç listesi güncel (değişiklik yok)")
                return True
                
        except Exception as e:
            logger.error(f"Medications download failed: {e}")
            print(f"\n❌ İlaç Listesi İndirme Hatası: {e}")
            return False
    
    # ==================== SUT ====================
    
    def download_sut_codes(self) -> bool:
        """
        SUT kodlarını SGK sitesinden indir (manuel)
        
        Not: SUT Excel dosyaları manuel olarak indirilmelidir
        Bu fonksiyon sadece talimat verir
        """
        print("\n📋 SUT KOD LİSTESİ İNDİRME TALİMATI\n")
        print("SUT kodları SGK resmi sitesinden manuel olarak indirilmelidir:")
        print()
        print("1. Adrese git: https://www.sgk.gov.tr/Arama/Index/sut")
        print()
        print("2. En güncel 'Değişiklik Tebliği İşlenmiş' dosyasını bul")
        print("   Örn: '26/04/2025 SUT Değişiklik Tebliği'")
        print()
        print("3. ZIP dosyasını indir ve aç")
        print()
        print("4. Şu dosyaları kullan:")
        print("   - EK-2B_Hizmet_Basi_Islem_Puan_Listesi.xlsx")
        print("   - EK-2C_Dis_Tedavileri.xlsx")
        print()
        print("5. Excel dosyalarını şu klasöre kopyala:")
        print(f"   {self.download_dir}")
        print()
        print("6. Ardından şu komutu çalıştır:")
        print(f"   python {__file__} --import-sut")
        print()
        
        return False
    
    def import_sut_excel(self, excel_path: str) -> bool:
        """
        SUT Excel dosyasını veritabanına aktar
        
        Args:
            excel_path: Excel dosya yolu
            
        Returns:
            bool: Başarılı mı
        """
        try:
            import pandas as pd
            from database.models import SKRSProcedure
            
            logger.info(f"Importing SUT codes from {excel_path}")
            
            # Excel'i oku
            df = pd.read_excel(excel_path)
            
            # Sütun adlarını kontrol et (dosyaya göre değişebilir)
            # Örnek: KOD, İŞLEM ADI, PUAN, FİYAT
            
            added = 0
            updated = 0
            
            with self.db.get_session() as session:
                for _, row in df.iterrows():
                    try:
                        code = str(row.get('KOD') or row.get('Kod') or '').strip()
                        name = str(row.get('İŞLEM ADI') or row.get('İslem Adı') or '').strip()
                        points = float(row.get('PUAN') or row.get('Puan') or 0)
                        
                        if not code or not name:
                            continue
                        
                        # Mevcut var mı?
                        existing = session.query(SKRSProcedure).filter_by(code=code).first()
                        
                        if existing:
                            existing.name = name
                            existing.points = points
                            existing.is_active = True
                            updated += 1
                        else:
                            new_proc = SKRSProcedure(
                                code=code,
                                name=name,
                                points=points,
                                is_active=True
                            )
                            session.add(new_proc)
                            added += 1
                            
                    except Exception as e:
                        logger.error(f"Row import error: {e}")
                        continue
                
                session.commit()
            
            print(f"\n✅ SUT Kodları İçe Aktarıldı!")
            print(f"   Yeni: {added}")
            print(f"   Güncellenen: {updated}")
            
            return True
            
        except Exception as e:
            logger.error(f"SUT import failed: {e}")
            print(f"\n❌ SUT İçe Aktarma Hatası: {e}")
            return False
    
    # ==================== USVS ====================
    
    def download_usvs_pdf(self) -> bool:
        """USVS 2.0 PDF'ini indir"""
        try:
            url = "https://verisozlugu.saglik.gov.tr/files/USVS_2.0.pdf"
            filename = self.download_dir / "USVS_2.0.pdf"
            
            logger.info(f"Downloading USVS PDF from {url}")
            
            response = requests.get(url, timeout=60)
            
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                print(f"\n✅ USVS PDF İndirildi!")
                print(f"   Dosya: {filename}")
                print(f"   Boyut: {len(response.content) / 1024 / 1024:.2f} MB")
                return True
            else:
                print(f"\n❌ USVS PDF İndirilemedi (HTTP {response.status_code})")
                return False
                
        except Exception as e:
            logger.error(f"USVS download failed: {e}")
            print(f"\n❌ USVS İndirme Hatası: {e}")
            return False
    
    # ==================== ALL ====================
    
    def download_all(self, force: bool = False) -> bool:
        """Tüm kaynakları indir"""
        print("\n" + "="*60)
        print("SKRS KAYNAK İNDİRME - BAŞLATILIYOR")
        print("="*60)
        
        results = {}
        
        # 1. ICD-10
        print("\n[1/4] ICD-10 Kodları indiriliyor...")
        results['icd10'] = self.download_icd_codes(force)
        
        # 2. Medications
        print("\n[2/4] İlaç Listesi indiriliyor...")
        results['medications'] = self.download_medications(force)
        
        # 3. SUT (Manuel)
        print("\n[3/4] SUT Kodları (Manuel)...")
        results['sut'] = self.download_sut_codes()
        
        # 4. USVS PDF
        print("\n[4/4] USVS PDF indiriliyor...")
        results['usvs'] = self.download_usvs_pdf()
        
        # Özet
        print("\n" + "="*60)
        print("ÖZET RAPOR")
        print("="*60)
        for name, success in results.items():
            status = "✅ Başarılı" if success else "❌ Başarısız"
            print(f"{name.upper():15} : {status}")
        
        print("\n" + "="*60)
        
        return all(results.values())
    
    # ==================== UTILITIES ====================
    
    def _save_report(self, filename: str, data: dict):
        """İndirme raporunu kaydet"""
        report_path = self.download_dir / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"SKRS İndirme Raporu\n")
            f.write(f"{'='*50}\n\n")
            for key, value in data.items():
                f.write(f"{key}: {value}\n")
        
        logger.info(f"Report saved: {report_path}")
    
    def get_status(self) -> dict:
        """Mevcut durum bilgisi"""
        status = self.skrs.get_sync_status()
        
        print("\n📊 MEVCUT DURUM\n")
        print(f"Son Senkronizasyon: {status.get('last_sync', 'Hiç')}")
        print(f"ICD-10 Kayıt Sayısı: {status.get('icd_count', 0)}")
        print(f"İlaç Kayıt Sayısı: {status.get('medication_count', 0)}")
        print(f"Güncelleme Gerekli: {'Evet' if status.get('needs_update') else 'Hayır'}")
        print()
        
        return status


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="SKRS/E-Nabız Kaynak İndirme Aracı"
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Tüm kaynakları indir'
    )
    
    parser.add_argument(
        '--icd',
        action='store_true',
        help='Sadece ICD-10 kodlarını indir'
    )
    
    parser.add_argument(
        '--medications',
        action='store_true',
        help='Sadece ilaç listesini indir'
    )
    
    parser.add_argument(
        '--sut',
        action='store_true',
        help='SUT indirme talimatını göster'
    )
    
    parser.add_argument(
        '--usvs',
        action='store_true',
        help='USVS PDF indir'
    )
    
    parser.add_argument(
        '--import-sut',
        type=str,
        metavar='EXCEL_FILE',
        help='SUT Excel dosyasını içe aktar'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Mevcut durum bilgisi'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Cache\'i ignore et, zorla güncelle'
    )
    
    args = parser.parse_args()
    
    # En az bir argüman gerekli
    if not any(vars(args).values()):
        parser.print_help()
        return 1
    
    # Database başlat
    try:
        db = DatabaseManager()
        downloader = SKRSResourceDownloader(db)
    except Exception as e:
        print(f"❌ Veritabanı hatası: {e}")
        return 1
    
    # Komutları çalıştır
    try:
        if args.status:
            downloader.get_status()
        
        elif args.all:
            success = downloader.download_all(force=args.force)
            return 0 if success else 1
        
        elif args.icd:
            success = downloader.download_icd_codes(force=args.force)
            return 0 if success else 1
        
        elif args.medications:
            success = downloader.download_medications(force=args.force)
            return 0 if success else 1
        
        elif args.sut:
            downloader.download_sut_codes()
            return 0
        
        elif args.usvs:
            success = downloader.download_usvs_pdf()
            return 0 if success else 1
        
        elif args.import_sut:
            success = downloader.import_sut_excel(args.import_sut)
            return 0 if success else 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  İşlem kullanıcı tarafından iptal edildi")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n❌ Beklenmeyen hata: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
