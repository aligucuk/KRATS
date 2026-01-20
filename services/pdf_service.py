import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from utils.logger import get_logger

logger = get_logger(__name__)

class PDFService:
    def __init__(self):
        # Raporların kaydedileceği klasör
        self.reports_dir = "reports"
        os.makedirs(self.reports_dir, exist_ok=True)
        
    def generate_medical_report(self, patient_name, details):
        """
        Basit bir tıbbi rapor PDF'i oluşturur.
        """
        try:
            # Dosya ismi oluştur (Benzersiz olması için tarih ekliyoruz)
            filename = f"Rapor_{patient_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(self.reports_dir, filename)
            
            # PDF Dokümanı ayarları
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = []
            
            # Başlık
            title_style = styles['Title']
            elements.append(Paragraph(f"Tıbbi Detay Raporu", title_style))
            elements.append(Spacer(1, 12))
            
            # Hasta Bilgisi
            elements.append(Paragraph(f"<b>Hasta Adı:</b> {patient_name}", styles['Normal']))
            elements.append(Paragraph(f"<b>Tarih:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles['Normal']))
            elements.append(Spacer(1, 20))
            
            # Detaylar Tablosu (Varsa)
            if isinstance(details, dict):
                table_data = [["Alan", "Bilgi"]] # Başlıklar
                for key, value in details.items():
                    table_data.append([str(key), str(value)])
                
                t = Table(table_data, colWidths=[150, 300])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.teal),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(t)
            else:
                # Düz metin ise
                elements.append(Paragraph(str(details), styles['Normal']))
                
            # PDF'i oluştur
            doc.build(elements)
            logger.info(f"PDF başarıyla oluşturuldu: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"PDF oluşturma hatası: {e}")
            return None