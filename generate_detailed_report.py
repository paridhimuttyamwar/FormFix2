import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

output_pdf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "FormFix_AI_Detailed_Project_Report.pdf")

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#6B7280"))
        
        # Header (pages after page 1)
        if self._pageNumber > 1:
            self.drawString(40, 755, "FormFix AI - Technical Architecture & Detailed Report")
            self.setStrokeColor(colors.HexColor("#E5E7EB"))
            self.setLineWidth(0.5)
            self.line(40, 750, 572, 750)
            
        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#E5E7EB"))
        self.setLineWidth(0.5)
        self.line(40, 42, 572, 42)
        self.drawString(40, 30, "FormFix AI - Hackathon MVP & System Documentation")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(572, 30, page_str)
        self.restoreState()

doc = SimpleDocTemplate(
    output_pdf,
    pagesize=letter,
    leftMargin=40,
    rightMargin=40,
    topMargin=50,
    bottomMargin=50
)

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "CoverTitle",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=22,
    leading=26,
    textColor=colors.HexColor("#1E3A8A"),
    spaceAfter=4
)

subtitle_style = ParagraphStyle(
    "CoverSubtitle",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=11,
    leading=15,
    textColor=colors.HexColor("#2563EB"),
    spaceAfter=12
)

h1_style = ParagraphStyle(
    "SecH1",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=13,
    leading=17,
    textColor=colors.HexColor("#1E3A8A"),
    spaceBefore=12,
    spaceAfter=5,
    keepWithNext=True
)

h2_style = ParagraphStyle(
    "SecH2",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=10.5,
    leading=14,
    textColor=colors.HexColor("#1F2937"),
    spaceBefore=7,
    spaceAfter=3,
    keepWithNext=True
)

body_style = ParagraphStyle(
    "Body",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=9,
    leading=13.5,
    textColor=colors.HexColor("#374151"),
    spaceAfter=5
)

bullet_style = ParagraphStyle(
    "Bullet",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=9,
    leading=13,
    leftIndent=14,
    textColor=colors.HexColor("#374151"),
    spaceAfter=3
)

callout_style = ParagraphStyle(
    "Callout",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=9,
    leading=13.5,
    textColor=colors.HexColor("#166534")
)

table_header_style = ParagraphStyle(
    "TH",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8.5,
    leading=11,
    textColor=colors.white,
    alignment=1
)

table_body_style = ParagraphStyle(
    "TB",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8,
    leading=11,
    textColor=colors.HexColor("#1F2937")
)

elements = []

# Title & Metadata Banner
elements.append(Paragraph("FormFix AI", title_style))
elements.append(Paragraph("Comprehensive System Architecture, Pipeline Flow & Technical Report", subtitle_style))
elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceAfter=10))

# Callout Mission Box
callout_data = [[
    Paragraph("<b>CORE PRINCIPLE: Document &rarr; Understanding &rarr; Action</b><br/>"
              "Unlike conventional PDF summarizers that produce generic summaries, FormFix AI transforms "
              "opaque institutional notices into actionable outcomes: (1) Urgent Deadlines, (2) Mandatory Paperwork Checklist, "
              "(3) Plain-English Field Explanations, and (4) An Interactive Action Plan.",
              callout_style)
]]
callout_table = Table(callout_data, colWidths=[532])
callout_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#F0FDF4")),
    ("BOX", (0,0), (-1,-1), 1.2, colors.HexColor("#86EFAC")),
    ("TOPPADDING", (0,0), (-1,-1), 6),
    ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ("LEFTPADDING", (0,0), (-1,-1), 10),
    ("RIGHTPADDING", (0,0), (-1,-1), 10),
]))
elements.append(callout_table)
elements.append(Spacer(1, 8))

# 1. Problem Statement & Mission
elements.append(Paragraph("1. Executive Summary & Problem Context", h1_style))
elements.append(Paragraph(
    "Every academic year, millions of students and citizens navigate bureaucratic documents such as scholarship applications, "
    "college admission notices, exam guidelines, and government circulars. These documents are notoriously dense, structured with "
    "legal jargon, and feature critical conditions (backlog restrictions, income ceilings, certification requirements) buried deep within the text. "
    "Missing a single requirement or deadline leads to rejected applications and lost financial aid.",
    body_style
))
elements.append(Paragraph(
    "<b>The FormFix Solution:</b> FormFix AI bridges the gap between passive reading and active execution. The system parses official documents, "
    "extracts verifiable dates and required supporting certificates, and translates them into an interactive checkbox action plan that users can check off step-by-step.",
    body_style
))

# 2. Technology Stack Table
elements.append(Paragraph("2. Technology Stack & Component Breakdown", h1_style))
elements.append(Paragraph(
    "The architecture emphasizes simplicity, reliability, and low latency without unnecessary microservices, databases, or container bloat:",
    body_style
))

tech_data = [
    [Paragraph("<b>Layer</b>", table_header_style), Paragraph("<b>Technology</b>", table_header_style), Paragraph("<b>Function in FormFix AI</b>", table_header_style), Paragraph("<b>Design Rationale</b>", table_header_style)],
    [Paragraph("<b>Frontend & UI</b>", table_body_style), Paragraph("Streamlit 1.35+", table_body_style), Paragraph("Full-width reactive web UI, file uploader, progress bar, action checklist, chat assistant.", table_body_style), Paragraph("Pure Python reactivity; instant rendering; zero frontend build step required.", table_body_style)],
    [Paragraph("<b>PDF Text Engine</b>", table_body_style), Paragraph("PyMuPDF (fitz)", table_body_style), Paragraph("High-speed native C-level text and metadata extraction from digital PDFs.", table_body_style), Paragraph("Extremely fast (10-20x faster than PyPDF2) with superior typography preservation.", table_body_style)],
    [Paragraph("<b>OCR Fallback</b>", table_body_style), Paragraph("pytesseract & Pillow", table_body_style), Paragraph("Contrast enhancement and optical character recognition for scanned/rasterized documents.", table_body_style), Paragraph("Guarantees scanned notices and phone camera photos can still be processed.", table_body_style)],
    [Paragraph("<b>AI / LLM Cloud</b>", table_body_style), Paragraph("Groq Cloud API", table_body_style), Paragraph("Ultra-fast inference (Qwen 27B / Llama 3) for JSON schema extraction and grounded Q&A.", table_body_style), Paragraph("Near-instant response times (300+ tokens/sec) providing smooth user experience.", table_body_style)],
    [Paragraph("<b>State & Secrets</b>", table_body_style), Paragraph("Session State & .env", table_body_style), Paragraph("In-memory task checklist tracking, chat history, and multi-tier key resolution.", table_body_style), Paragraph("No persistent database required; privacy-by-design; zero cloud data storage.", table_body_style)]
]
tech_table = Table(tech_data, colWidths=[78, 92, 192, 170])
tech_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1E3A8A")),
    ("ALIGN", (0,0), (-1,-1), "LEFT"),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F9FAFB")]),
    ("TOPPADDING", (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
    ("RIGHTPADDING", (0,0), (-1,-1), 6),
]))
elements.append(tech_table)
elements.append(Spacer(1, 8))

# 3. End-to-End System Pipeline Flow
elements.append(Paragraph("3. End-to-End Processing Flow (Life of a Document)", h1_style))
elements.append(Paragraph("The system implements a reliable, deterministic 6-stage lifecycle for every uploaded document:", body_style))
elements.append(Paragraph("<b>Stage 1 &mdash; Ingestion & Validation:</b> User uploads a document (PDF, PNG, JPG, JPEG). The file metadata (name, MIME type, size in KB) is extracted and verified.", bullet_style))
elements.append(Paragraph("<b>Stage 2 &mdash; Hybrid Extraction (document_processor.py):</b> For PDFs, PyMuPDF opens the document in memory. An automated character density heuristic evaluates whether the PDF contains selectable text (averaging &ge; 40 characters per page). If character density is low, the document is classified as scanned, and pages are rendered into high-resolution pixmaps for OCR. For direct image uploads, it routes to Pillow for grayscale and contrast enhancement, followed by pytesseract OCR.", bullet_style))
elements.append(Paragraph("<b>Stage 3 &mdash; Whitespace Normalization:</b> Raw text is filtered through regex routines to eliminate excessive spaces, tabs, and multi-line breaks, maintaining clean paragraph context while minimizing token consumption.", bullet_style))
elements.append(Paragraph("<b>Stage 4 &mdash; Structured AI Analysis (ai_service.py):</b> The sanitized text is dispatched to Groq's high-speed inference engine using a specialized system prompt enforcing a strict JSON schema. The model extracts: Title, Document Type, Summary, Deadline, Required Documents, Confusing Fields, Action Items, and Warnings.", bullet_style))
elements.append(Paragraph("<b>Stage 5 &mdash; Interactive Dashboard Rendering (app.py):</b> The parsed JSON generates an actionable UI: prominent red deadline badge, interactive task checklist with real-time percentage completion progress, required certificates cards, and confusing jargon explanations.", bullet_style))
elements.append(Paragraph("<b>Stage 6 &mdash; Grounded Q&A Assistant (Ask FormFix AI):</b> Users can query the document via suggested quick-chips or custom questions. The assistant is strictly grounded in the document text, preventing hallucinations by returning <i>\"I couldn't find that information in the uploaded document\"</i> if the query references out-of-scope details.", bullet_style))

elements.append(Spacer(1, 8))

# 4. Codebase Architecture
elements.append(Paragraph("4. Codebase Architecture & File Roles", h1_style))
elements.append(Paragraph("<b>app.py:</b> Main Streamlit application orchestrating the UI layout, file upload state, progress bar animations, interactive checkboxes, and conversational chat interface. Uses dynamic path discovery to seamlessly run whether modules are in services/ or root directory.", body_style))
elements.append(Paragraph("<b>services/document_processor.py:</b> The document ingestion engine. Manages file type detection, PyMuPDF text extraction, scanned page density heuristics, image pixmap rendering, and regex whitespace cleaning.", body_style))
elements.append(Paragraph("<b>services/ocr_service.py:</b> Image enhancement module. Applies Pillow-based grayscale conversion and contrast sharpening. Features automatic binary path resolution for Windows and Linux Tesseract executables.", body_style))
elements.append(Paragraph("<b>services/ai_service.py:</b> AI communication client. Manages Groq API calls with multi-model fallback hierarchy (Qwen-27B / Llama-3), JSON code-fence stripping, schema validation, and multi-tier credential lookup (Streamlit Cloud st.secrets, .env, and OS environment).", body_style))
elements.append(Paragraph("<b>test_formfix.py:</b> Self-contained automated test suite executing 7 unit tests covering PDF extraction, whitespace cleaning, schema compliance, and OCR preprocessing.", body_style))

elements.append(Spacer(1, 8))

# 5. Security & Deployment
elements.append(Paragraph("5. Security, Deployment & Production Readiness", h1_style))
elements.append(Paragraph("• <b>Credential Isolation:</b> Secret keys are never committed to GitHub or exposed in frontend code. The application uses .env locally and Streamlit Cloud Secrets (st.secrets) in production.", bullet_style))
elements.append(Paragraph("• <b>Cloud Deployment:</b> Seamless continuous deployment connected to GitHub (main branch). Every Git push automatically triggers a fast cloud rebuild on Streamlit Community Cloud (share.streamlit.io).", bullet_style))
elements.append(Paragraph("• <b>Anti-Hallucination Guardrails:</b> Strict system prompting forces the LLM to output \"Not specified\" or empty arrays whenever requirements or deadlines are absent in the source document.", bullet_style))

doc.build(elements, canvasmaker=NumberedCanvas)
print("Detailed report generated successfully at:", output_pdf)
