import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

class PDFManager:
    def __init__(self, filename):
        # Raporları 'reports' klasörüne kaydet
        self.report_dir = "reports"
        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)
            
        self.filepath = os.path.join(self.report_dir, filename)
        self.c = canvas.Canvas(self.filepath, pagesize=A4)
        self.width, self.height = A4
        self.has_unicode_font = False
        
        # Fonksiyonu çağır
        self._register_fonts()

    def _register_fonts(self):
        """
        Font yüklemeyi dener. Mac/Windows uyumlu çalışır.
        """
        # İşletim sistemine göre olası font yolları
        font_paths = [
            os.path.join("assets", "arial.ttf"), # Önce proje içine bak
            "/Library/Fonts/Arial.ttf",          # Mac
            "/System/Library/Fonts/Helvetica.ttc", # Mac Alternatif
            "C:/Windows/Fonts/arial.ttf",        # Windows
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" # Linux
        ]
        
        selected_font = None
        for path in font_paths:
            if os.path.exists(path):
                selected_font = path
                break
        
        try:
            if selected_font:
                # Font adını 'TrFont' olarak kaydediyoruz
                pdfmetrics.registerFont(TTFont('TrFont', selected_font))
                self.font_reg = 'TrFont'
                self.font_bold = 'TrFont' 
                self.has_unicode_font = True
                print(f"✅ PDF Fontu yüklendi: {selected_font}")
            else:
                raise Exception("Font dosyası bulunamadı")
        except Exception as e:
            print(f"⚠️ Font uyarısı: {e}. Standart font (Helvetica) kullanılıyor.")
            self.font_reg = 'Helvetica'
            self.font_bold = 'Helvetica-Bold'
            self.has_unicode_font = False

    def _clean_text(self, text):
        """Eğer Türkçe font yoksa karakterleri temizle"""
        if not text: return ""
        if self.has_unicode_font:
            return str(text)
        # Türkçe karakterleri İngilizceye çevir
        replacements = str.maketrans("ğĞıİşŞüÜöÖçÇ", "gGiIsSuUoOcC")
        return str(text).translate(replacements)

    def create_prescription(self, doctor, patient, diagnosis, content):
        # Header
        self.c.setFont(self.font_bold, 18)
        self.c.drawString(50, 800, "KRATS KLINIK SISTEMI")
        
        # Tarih
        self.c.setFont(self.font_reg, 10)
        self.c.drawString(450, 800, f"Tarih: {datetime.date.today()}")
        self.c.line(50, 790, 550, 790)

        # Bilgiler
        y = 750
        self.c.setFont(self.font_bold, 12)
        self.c.drawString(50, y, f"Doktor: {self._clean_text(doctor)}")
        self.c.drawString(50, y-20, f"Hasta: {self._clean_text(patient)}")
        
        # İçerik
        y -= 60
        self.c.setFont(self.font_bold, 12)
        self.c.drawString(50, y, "TANI / NOTLAR:")
        self.c.setFont(self.font_reg, 11)
        self.c.drawString(50, y-20, self._clean_text(diagnosis))
        
        y -= 60
        self.c.setFont(self.font_bold, 12)
        self.c.drawString(50, y, "RECETE / TEDAVI:")
        
        # Çok satırlı metin (Text Object)
        text_obj = self.c.beginText(50, y-20)
        text_obj.setFont(self.font_reg, 11)
        
        lines = content.split('\n')
        for line in lines:
            text_obj.textLine(self._clean_text(line))
            
        self.c.drawText(text_obj)
        
        # Footer
        self.c.setFont(self.font_reg, 8)
        self.c.drawCentredString(300, 50, "Bu belge elektronik olarak uretilmistir.")
        
        self.c.save()
        return self.filepath

def create_prescription_pdf(doctor_name, patient_name, diagnosis, prescription):
    # Wrapper fonksiyon
    filename = f"recete_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf = PDFManager(filename)
    path = pdf.create_prescription(doctor_name, patient_name, diagnosis, prescription)
    
    return path