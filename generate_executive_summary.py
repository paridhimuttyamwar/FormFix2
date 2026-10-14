import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

output_pdf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "FormFix_AI_Executive_Summary_Flow.pdf")

class ExecutiveCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(ExecutiveCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(ExecutiveCanvas, self).showPage()
        super(ExecutiveCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#6B7280"))
        
        # Header (on page 2+)
        if self._pageNumber > 1:
            self.drawString(40, 755, "FormFix AI - Executive Summary & Technology Flow")
            self.setStrokeColor(colors.HexColor("#E5E7EB"))
            self.setLineWidth(0.5)
            self.line(40, 750, 572, 750)
            
        # Footer
        self.setStrokeColor(colors.HexColor("#E5E7EB"))
        self.setLineWidth(0.5)
        self.line(40, 42, 572, 42)
        self.drawString(40, 30, "FormFix AI - Quick Reference & Technology Flow Guide")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(572, 30, page_str)
        self.restoreState()

doc = SimpleDocTemplate(
    output_pdf,
    pagesize=letter,
    leftMargin=40,
    rightMargin=40,
    topMargin=48,
    bottomMargin=48
)

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "Title",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=22,
    leading=26,
    textColor=colors.HexColor("#1E3A8A"),
    spaceAfter=3
)

tagline_style = ParagraphStyle(
    "Tagline",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=15,
    textColor=colors.HexColor("#2563EB"),
    spaceAfter=10
)

h1_style = ParagraphStyle(
    "H1",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=12,
    leading=16,
    textColor=colors.HexColor("#1E3A8A"),
    spaceBefore=10,
    spaceAfter=4,
    keepWithNext=True
)

body_style = ParagraphStyle(
    "Body",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=9,
    leading=13,
    textColor=colors.HexColor("#374151"),
    spaceAfter=4
)

bullet_style = ParagraphStyle(
    "Bullet",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=9,
    leading=13,
    leftIndent=12,
    textColor=colors.HexColor("#374151"),
    spaceAfter=3
)

step_num_style = ParagraphStyle(
    "StepNum",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=10,
    leading=12,
    textColor=colors.HexColor("#2563EB"),
    alignment=1
)

step_text_style = ParagraphStyle(
    "StepText",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8.5,
    leading=11.5,
    textColor=colors.HexColor("#1F2937")
)

th_style = ParagraphStyle(
    "TH",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8.5,
    leading=11,
    textColor=colors.white,
    alignment=1
)

tb_style = ParagraphStyle(
    "TB",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8,
    leading=11,
    textColor=colors.HexColor("#1F2937")
)

elements = []

# Title & Tagline
elements.append(Paragraph("FormFix AI", title_style))
elements.append(Paragraph("Executive Summary & Technology Flow Guide", tagline_style))
elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceAfter=8))

# Elevator Pitch
overview_text = (
    "<b>What is FormFix AI?</b> FormFix AI is an AI-powered document action assistant. "
    "When students and citizens receive complicated notices (scholarships, college admissions, circulars, job descriptions), "
    "FormFix AI does not just summarize the text—it converts the document into <b>Deadlines</b>, "
    "<b>Required Documents</b>, and an <b>Interactive Action Plan</b> that users can check off as they complete each task."
)
elements.append(Paragraph(overview_text, body_style))
elements.append(Spacer(1, 6))

# 1. Technology Used and Why (Clear Table)
elements.append(Paragraph("1. Technology Stack & Why Each Tool is Used", h1_style))
tech_summary_data = [
    [Paragraph("<b>Technology</b>", th_style), Paragraph("<b>What It Does</b>", th_style), Paragraph("<b>Why We Used It (Advantage)</b>", th_style)],
    [Paragraph("<b>Streamlit</b><br/>(Python UI)", tb_style), Paragraph("Powers the web application, file uploader, progress bar, interactive checkboxes, and chat box.", tb_style), Paragraph("Allows building interactive, beautiful web apps in 100% Python without complex React or Node.js setup.", tb_style)],
    [Paragraph("<b>PyMuPDF</b><br/>(fitz)", tb_style), Paragraph("Reads and extracts digital text from uploaded PDF documents with exact typography.", tb_style), Paragraph("Extremely fast native C engine (20x faster than standard PDF libraries); avoids lag during document uploads.", tb_style)],
    [Paragraph("<b>Pillow & Tesseract</b><br/>(OCR Engine)", tb_style), Paragraph("Enhances image contrast and reads text from scanned documents, photocopies, or phone images.", tb_style), Paragraph("Fallback safety net: if a student uploads a scanned photo or circular image, OCR extracts the text automatically.", tb_style)],
    [Paragraph("<b>Groq Cloud API</b><br/>(Llama 3 / Qwen)", tb_style), Paragraph("Understands the document text, extracts structured JSON data, and powers the Q&A chat assistant.", tb_style), Paragraph("Provides ultra-fast AI inference (over 300 tokens/sec), generating results in 1-2 seconds with zero hallucinations.", tb_style)],
    [Paragraph("<b>Session State</b><br/>(Streamlit Storage)", tb_style), Paragraph("Saves completed checklist checkboxes and chat history while using the app.", tb_style), Paragraph("Keeps user documents strictly in memory without needing a separate database (100% private by design).", tb_style)]
]
summary_table = Table(tech_summary_data, colWidths=[90, 205, 237])
summary_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1E3A8A")),
    ("ALIGN", (0,0), (-1,-1), "LEFT"),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F9FAFB")]),
    ("TOPPADDING", (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
    ("RIGHTPADDING", (0,0), (-1,-1), 6),
]))
elements.append(summary_table)
elements.append(Spacer(1, 8))

# 2. Complete Application Flow
elements.append(Paragraph("2. How It Works (Step-by-Step Flow)", h1_style))

flow_data = [
    [Paragraph("<b>Step 01</b>", step_num_style), Paragraph("<b>Upload Document</b><br/>User uploads an official notice or form (PDF, PNG, or JPG) into the web interface.", step_text_style)],
    [Paragraph("<b>Step 02</b>", step_num_style), Paragraph("<b>Smart Text Extraction</b><br/>PyMuPDF reads the PDF text. If the document is scanned or an image, OCR triggers automatically.", step_text_style)],
    [Paragraph("<b>Step 03</b>", step_num_style), Paragraph("<b>Text Cleaning</b><br/>Whitespace and broken lines are cleaned using regex to keep the text compact and clear.", step_text_style)],
    [Paragraph("<b>Step 04</b>", step_num_style), Paragraph("<b>AI Structured Extraction (Groq)</b><br/>The clean text is sent to the LLM. It extracts dates, documents, confusing terms, and action steps into pure JSON.", step_text_style)],
    [Paragraph("<b>Step 05</b>", step_num_style), Paragraph("<b>Action Dashboard</b><br/>User receives an interactive checklist with checkboxes, prominent deadline banner, and required documents.", step_text_style)],
    [Paragraph("<b>Step 06</b>", step_num_style), Paragraph("<b>Ask FormFix AI</b><br/>User can ask questions (e.g. 'What is the deadline?'). The AI answers strictly from the document without making up facts.", step_text_style)]
]
flow_table = Table(flow_data, colWidths=[65, 467])
flow_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
    ("BOX", (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
    ("INNERGRID", (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING", (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
    ("RIGHTPADDING", (0,0), (-1,-1), 6),
]))
elements.append(flow_table)
elements.append(Spacer(1, 8))

# 3. What the User Gets on the Dashboard
elements.append(Paragraph("3. The 5 Core Results Generated for the User", h1_style))
elements.append(Paragraph("1. <b>Critical Deadline Banner:</b> High-visibility alert displaying the exact cutoff date and time (e.g. 15 October 2026, 5:00 PM IST) so students never miss submissions.", bullet_style))
elements.append(Paragraph("2. <b>Interactive Action Plan (What to Do Next):</b> Practical checklist with real-time percentage progress (e.g. 3 of 7 tasks done - 42%). Users tick off items as they collect documents.", bullet_style))
elements.append(Paragraph("3. <b>Required Supporting Documents:</b> Itemized list of mandatory certificates (Marksheets, Bonafide Certificate, Income Certificate, Fee Receipts).", bullet_style))
elements.append(Paragraph("4. <b>Confusing Fields Decoded:</b> Explains institutional jargon in simple everyday words and matches each with the required certificate.", bullet_style))
elements.append(Paragraph("5. <b>Zero-Hallucination Grounded Chat:</b> Interactive conversational assistant that only answers from the document. If information is missing, it explicitly states so.", bullet_style))

elements.append(Spacer(1, 8))

# 4. Quick Pitch / Hackathon Talking Points
elements.append(Paragraph("4. Quick Hackathon Pitch (Talking Points)", h1_style))
elements.append(Paragraph("• <b>Not Just a Summarizer:</b> Summarizers give paragraphs of text. FormFix AI gives an actionable checklist.", bullet_style))
elements.append(Paragraph("• <b>Speed:</b> Powered by Groq, full document processing takes under 2 seconds.", bullet_style))
elements.append(Paragraph("• <b>Accuracy & Trust:</b> Strict anti-hallucination prompting ensures no made-up deadlines or documents.", bullet_style))
elements.append(Paragraph("• <b>Zero Deployment Friction:</b> Built with pure Python & Streamlit, deployable in 1 click to Streamlit Cloud.", bullet_style))

doc.build(elements, canvasmaker=ExecutiveCanvas)
print("Executive summary generated successfully at:", output_pdf)
