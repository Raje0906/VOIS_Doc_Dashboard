from fpdf import FPDF
import os

class PDFReportGenerator:
    def __init__(self, output_dir="static/reports"):
        # On Vercel, we can only write to /tmp
        if os.environ.get('VERCEL') == '1':
            self.output_dir = "/tmp"
        else:
            self.output_dir = output_dir
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)

    def generate_prescription_report(self, analysis_text, patient_name, doctor_name, prescription_text):
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "AI Prescription Analysis Report",ln=True, align="C")
        pdf.ln(10)
        
        # Meta Info
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Patient: {patient_name}", ln=True)
        pdf.cell(0, 10, f"Doctor: {doctor_name}", ln=True)
        pdf.ln(5)
        
        # Original Prescription
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Original Prescription Details:", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 10, prescription_text)
        pdf.ln(5)
        
        # AI Analysis
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "AI Analysis & Recommendations:", ln=True)
        pdf.set_font("Arial", "", 11)
        
        # Handle unicode roughly by replacing or using a compatible font (standard fpdf doesn't support unicode well without setup)
        # For simplicity in this demo, we'll encode/decode to ascii to avoid crashes, or use latin-1
        sanitized_analysis = analysis_text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, sanitized_analysis)
        
        # Save
        filename = f"report_{patient_name.replace(' ', '_')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        pdf.output(filepath)
        
        return filepath
    def generate_medicine_report(self, condition, recommendation, doctor_name="Dr. Raje"):
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "AI Medicine Recommendation Report", ln=True, align="C")
        pdf.ln(10)
        
        # Meta Info
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Doctor: {doctor_name}", ln=True)
        pdf.cell(0, 10, f"Condition/Diagnosis: {condition}", ln=True)
        pdf.ln(5)
        
        # Recommendation Section
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Treatment Recommendations & Reasoning:", ln=True)
        pdf.set_font("Arial", "", 11)
        
        # Handle unicode roughly
        sanitized_rec = recommendation.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, sanitized_rec)
        
        # Save
        filename = f"med_rec_{condition[:10].replace(' ', '_')}.pdf"
        # Sanitize filename
        filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in '._-'])
        filepath = os.path.join(self.output_dir, filename)
        pdf.output(filepath)
        
        return filepath
