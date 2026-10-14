import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether, PageBreak
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
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#1E3A8A"))
        
        # Header (pages after page 1)
        if self._pageNumber > 1:
            self.drawString(40, 755, "FormFix AI")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#6B7280"))
            self.drawString(95, 755, "|  Comprehensive Architecture, Module Interconnection & Technical Report")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.6)
            self.line(40, 748, 572, 748)
            
        # Footer (all pages)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#6B7280"))
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.6)
        self.line(40, 42, 572, 42)
        self.drawString(40, 30, "FormFix AI Technical Documentation  *  Hackathon Engineering Specification")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(572, 30, page_str)
        self.restoreState()

doc = SimpleDocTemplate(
    output_pdf,
    pagesize=letter,
    leftMargin=40,
    rightMargin=40,
    topMargin=52,
    bottomMargin=52
)

styles = getSampleStyleSheet()

cover_title_style = ParagraphStyle(
    "CoverTitle",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=24,
    leading=28,
    textColor=colors.HexColor("#1E3A8A"),
    spaceAfter=4
)

cover_subtitle_style = ParagraphStyle(
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
    fontSize=10,
    leading=14,
    textColor=colors.HexColor("#1F2937"),
    spaceBefore=7,
    spaceAfter=3,
    keepWithNext=True
)

h3_style = ParagraphStyle(
    "SecH3",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=9,
    leading=12,
    textColor=colors.HexColor("#374151"),
    spaceBefore=4,
    spaceAfter=2,
    keepWithNext=True
)

body_style = ParagraphStyle(
    "Body",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8.5,
    leading=12.5,
    textColor=colors.HexColor("#374151"),
    spaceAfter=4
)

bullet_style = ParagraphStyle(
    "Bullet",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8.5,
    leading=12,
    leftIndent=12,
    textColor=colors.HexColor("#374151"),
    spaceAfter=2.5
)

callout_style = ParagraphStyle(
    "Callout",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8.5,
    leading=12.5,
    textColor=colors.HexColor("#166534")
)

th_style = ParagraphStyle(
    "TH",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8,
    leading=10,
    textColor=colors.white,
    alignment=1
)

tb_style = ParagraphStyle(
    "TB",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=7.5,
    leading=10,
    textColor=colors.HexColor("#1F2937")
)

code_style = ParagraphStyle(
    "CodeSnippet",
    parent=styles["Normal"],
    fontName="Courier",
    fontSize=7.5,
    leading=10,
    textColor=colors.HexColor("#1E293B")
)

elements = []

# Title & Metadata Banner
elements.append(Paragraph("FormFix AI", cover_title_style))
elements.append(Paragraph("Comprehensive System Architecture, Module Interconnection & Technical Report", cover_subtitle_style))
elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceAfter=8))

# Callout Mission Box
callout_data = [[
    Paragraph("<b>CORE ARCHITECTURAL MISSION: Document &rarr; Understanding &rarr; Action</b><br/>"
              "Generic PDF summarizers fail because they output passive paragraphs of text that students still have to interpret. "
              "FormFix AI is purpose-built to eliminate administrative confusion by extracting: (1) Urgent Deadlines, "
              "(2) Itemized Required Documents, (3) Translated Bureaucratic Jargon, and (4) An Interactive, Checkable Action Plan.",
              callout_style)
]]
callout_table = Table(callout_data, colWidths=[532])
callout_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#F0FDF4")),
    ("BOX", (0,0), (-1,-1), 1.2, colors.HexColor("#86EFAC")),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING", (0,0), (-1,-1), 8),
    ("RIGHTPADDING", (0,0), (-1,-1), 8),
]))
elements.append(callout_table)
elements.append(Spacer(1, 6))

# SECTION 1: PROBLEM CONTEXT & PHILOSOPHY
elements.append(Paragraph("1. Executive Summary & Problem Context", h1_style))
elements.append(Paragraph(
    "Every academic year, students, job seekers, and citizens must interact with complicated institutional paperwork—scholarship renewal notices, "
    "college admission guidelines, government circulars, and application forms. These documents are notoriously verbose, written in rigid legalistic "
    "language, and feature critical requirements (income limits, minimum academic percentages, backlog disqualifications, and cutoff deadlines) "
    "buried deep inside lengthy paragraphs. Missing a single supporting certificate or misinterpreting a deadline often causes disqualification, "
    "revocation of financial aid, or missed admission cycles.",
    body_style
))
elements.append(Paragraph(
    "<b>Why Existing AI Tools Fall Short:</b> General LLM chatbots (e.g. asking a generic model to 'summarize this PDF') produce long text summaries "
    "that do not clearly tell the user what physical actions to take next. Furthermore, standard models are prone to hallucinating plausible requirements "
    "or fabricating deadlines when dates are missing from the text.",
    body_style
))
elements.append(Paragraph(
    "<b>The FormFix Solution:</b> FormFix AI bridges the gap between passive reading and active execution. It processes documents through a multi-stage "
    "hybrid pipeline, identifies the physical paperwork required, clarifies complex institutional terms, highlights deadlines with urgency badges, "
    "and synthesizes an interactive task checklist that the user can track in real time.",
    body_style
))

# SECTION 2: EXHAUSTIVE TECHNOLOGY BREAKDOWN
elements.append(Paragraph("2. Exhaustive Technology Stack & Design Justifications", h1_style))
elements.append(Paragraph(
    "The technology stack was chosen specifically for maximum execution speed, zero architectural bloat, and ironclad reliability:",
    body_style
))

tech_detail_data = [
    [Paragraph("<b>Component</b>", th_style), Paragraph("<b>Technology & Version</b>", th_style), Paragraph("<b>Exact Role in the Application</b>", th_style), Paragraph("<b>Why This Specific Tool Was Chosen</b>", th_style)],
    [Paragraph("<b>Frontend Framework</b>", tb_style), Paragraph("Streamlit &gt;= 1.35.0", tb_style), Paragraph("Renders the entire web application, file uploader, loading indicators, interactive checkboxes, and grounded chat.", tb_style), Paragraph("Enables stateful, reactive UI in pure Python. Eliminates Node/React dependencies and API glue code.", tb_style)],
    [Paragraph("<b>PDF Text Extraction</b>", tb_style), Paragraph("PyMuPDF (fitz) &gt;= 1.24.0", tb_style), Paragraph("Opens PDF byte streams in memory, extracts UTF-8 text per page, and checks character density.", tb_style), Paragraph("High-speed C-based engine. 15-20x faster than PyPDF2/PDFMiner; preserves natural reading order.", tb_style)],
    [Paragraph("<b>Image Preprocessing</b>", tb_style), Paragraph("Pillow (PIL) &gt;= 10.0.0", tb_style), Paragraph("Converts images to 8-bit grayscale and applies 1.8x contrast enhancement prior to OCR.", tb_style), Paragraph("Sharpening edges and eliminating background noise dramatically improves OCR text recognition accuracy.", tb_style)],
    [Paragraph("<b>Optical Character Recognition</b>", tb_style), Paragraph("pytesseract &gt;= 0.3.10", tb_style), Paragraph("Extracts text from scanned photocopies, smartphone photos, and image-based PDFs.", tb_style), Paragraph("Industry-standard open OCR engine with automatic binary path discovery across Windows and Linux.", tb_style)],
    [Paragraph("<b>AI Reasoning & LLM</b>", tb_style), Paragraph("Groq Cloud API &gt;= 0.9.0<br/>(Qwen 27B / Llama 3)", tb_style), Paragraph("Executes zero-shot structured JSON document extraction and powers the grounded Q&A chat assistant.", tb_style), Paragraph("Groq's LPUs provide sub-second inference (300+ tokens/sec). Guaranteed JSON schema compliance.", tb_style)],
    [Paragraph("<b>Configuration & Secrets</b>", tb_style), Paragraph("python-dotenv & Streamlit Secrets", tb_style), Paragraph("Manages secure API credentials across local development (.env) and cloud production (st.secrets).", tb_style), Paragraph("Multi-tier resolution guarantees zero hardcoded keys and seamless deployment without code edits.", tb_style)],
    [Paragraph("<b>State Management</b>", tb_style), Paragraph("Streamlit Session State", tb_style), Paragraph("Maintains task checklist checkbox states, chat message history, and active document buffers.", tb_style), Paragraph("Runs entirely in server memory. Zero database dependencies; ensures complete user data privacy.", tb_style)]
]
tech_table = Table(tech_detail_data, colWidths=[75, 95, 185, 177])
tech_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1E3A8A")),
    ("ALIGN", (0,0), (-1,-1), "LEFT"),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ("TOPPADDING", (0,0), (-1,-1), 3.5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 3.5),
    ("LEFTPADDING", (0,0), (-1,-1), 5),
    ("RIGHTPADDING", (0,0), (-1,-1), 5),
]))
elements.append(tech_table)
elements.append(Spacer(1, 8))

# SECTION 3: FILE-BY-FILE ARCHITECTURE
elements.append(Paragraph("3. Complete Directory Structure & File-by-File Breakdown", h1_style))
elements.append(Paragraph(
    "The project follows a clean, modular structure where presentation, document processing, optical recognition, and AI reasoning are strictly separated:",
    body_style
))

elements.append(Paragraph("<b>FormFix-AI/app.py (Main Application & Presentation Layer):</b>", h2_style))
elements.append(Paragraph(
    "This is the entry point executed by Streamlit (`streamlit run app.py`). It handles: (1) Custom CSS injection for clean typography, "
    "hero headers, and mobile responsiveness; (2) Stateful file upload handling for PDF, PNG, JPG, and JPEG; (3) Dynamic multi-step progress "
    "animations during analysis; (4) Rendering the Results Dashboard (deadline callout, interactive checklist with real-time percentage tracking, "
    "required documents list, and confusing jargon cards); (5) The interactive 'Ask FormFix AI' chat interface with 1-click suggested question chips; "
    "and (6) Dynamic import fallback allowing seamless execution whether files are in `services/` or the root directory.",
    body_style
))

elements.append(Paragraph("<b>services/document_processor.py (Document Ingestion & Normalization Engine):</b>", h2_style))
elements.append(Paragraph(
    "The bridge between raw bytes and clean readable text. Responsibilities: (1) File extension routing (`.pdf` vs images); "
    "(2) Native PDF text extraction using `fitz.open(stream=file_bytes, filetype='pdf')`; (3) <b>Scanned Document Heuristic:</b> calculates the "
    "average text length per page across the PDF. If the average is under 40 characters per page, the PDF is flagged as a scanned image, "
    "and pages are converted into 150 DPI pixmaps for OCR; (4) `clean_whitespace()`: uses regular expressions to normalize multi-spaces, "
    "strip trailing line whitespace, and collapse consecutive empty lines down to a maximum of 2, minimizing LLM token consumption.",
    body_style
))

elements.append(Paragraph("<b>services/ocr_service.py (Optical Character Recognition Engine):</b>", h2_style))
elements.append(Paragraph(
    "Specialized image preprocessing and OCR wrapper. Responsibilities: (1) `preprocess_image()`: takes a PIL Image, converts it to 8-bit "
    "grayscale (`L` mode), and applies an `ImageEnhance.Contrast` factor of 1.8 to sharpen faded text; (2) `_configure_tesseract()`: dynamically "
    "locates the Tesseract executable across system PATH and standard Windows install directories (`C:\\Program Files\\Tesseract-OCR\\tesseract.exe`); "
    "(3) `extract_text_from_image()`: runs `pytesseract.image_to_string()` and returns clean UTF-8 text with user-friendly error fallbacks.",
    body_style
))

elements.append(Paragraph("<b>services/ai_service.py (Groq LLM Client & Prompt Engineering):</b>", h2_style))
elements.append(Paragraph(
    "The artificial intelligence brain of FormFix AI. Responsibilities: (1) `get_groq_api_key()`: multi-tier credential lookup checking "
    "Streamlit Cloud Secrets (`st.secrets['GROQ_API_KEY']`), local `.env`, and OS environment variables; (2) `analyze_document_with_ai()`: "
    "formats the system prompt, enforces `response_format={'type': 'json_object'}`, dispatches to Groq's high-speed endpoint using `qwen/qwen3.8-27b`, "
    "and validates the 8 required JSON keys; (3) `ask_document_ai()`: handles interactive user questions strictly grounded in the document text; "
    "(4) `clean_json_response()`: strips any stray markdown code fences (` ```json `) to ensure safe JSON parsing.",
    body_style
))

elements.append(Paragraph("<b>requirements.txt:</b> Minimal production dependencies (`streamlit`, `groq`, `python-dotenv`, `PyMuPDF`, `pytesseract`, `Pillow`).", body_style))
elements.append(Paragraph("<b>.env & .env.example:</b> Environment variable configuration containing `GROQ_API_KEY`. Protected from version control by `.gitignore`.", body_style))
elements.append(Paragraph("<b>.gitignore:</b> Ignores `.env`, compiled Python caches (`__pycache__/`, `*.pyc`), and local IDE files to ensure zero credential leaks.", body_style))
elements.append(Paragraph("<b>test_formfix.py:</b> Self-contained automated test suite executing 7 unit tests verifying PDF extraction, regex normalization, and schema conformance.", body_style))

elements.append(Spacer(1, 8))

# SECTION 4: HOW EVERYTHING IS LINKED TOGETHER
elements.append(Paragraph("4. How Everything is Linked Together (Execution Flow)", h1_style))
elements.append(Paragraph(
    "The entire application operates as a cohesive, deterministic data pipeline. Here is the exact step-by-step lifecycle of an interaction:",
    body_style
))

pipeline_steps = [
    [Paragraph("<b>Step 1: Upload & Byte Ingestion</b>", h3_style),
     Paragraph("The user drags a PDF or image into `st.file_uploader`. Streamlit places the raw file into an in-memory buffer (`uploaded_file.getvalue()`). "
               "The app displays the file name, MIME type, and calculated size in KB. Processing does not start automatically—waiting for explicit user intent.", body_style)],
    [Paragraph("<b>Step 2: Trigger & Progress Activation</b>", h3_style),
     Paragraph("The user clicks <b>'Analyze Document'</b>. `app.py` triggers an animated multi-step progress bar: "
               "<i>File received &rarr; Extracting text &rarr; Understanding document &rarr; Identifying requirements &rarr; Creating action plan</i>.", body_style)],
    [Paragraph("<b>Step 3: Text Extraction & Scanned Detection</b>", h3_style),
     Paragraph("`app.py` invokes `extract_document_text(file_name, file_bytes)` in `document_processor.py`. "
               "If PDF, PyMuPDF opens the stream. If page character density &ge; 40 chars/page, text is extracted directly. "
               "If average density &lt; 40 chars/page, the document is flagged as scanned; PyMuPDF renders the page to a pixmap, "
               "and `ocr_service.py` runs contrast enhancement and Tesseract OCR. Extracted text is normalized by `clean_whitespace()`.", body_style)],
    [Paragraph("<b>Step 4: AI Analysis & Schema Enforcement</b>", h3_style),
     Paragraph("`app.py` calls `analyze_document_with_ai(extracted_text)` in `ai_service.py`. The text is paired with the strict "
               "AI Document Action Assistant system prompt and dispatched to Groq's API (`qwen/qwen3.8-27b`) with `response_format={'type': 'json_object'}`. "
               "Groq returns a structured JSON string in under 2 seconds. `ai_service.py` parses the JSON, validates keys, and returns a clean dictionary.", body_style)],
    [Paragraph("<b>Step 5: Dashboard & Stateful Action Plan</b>", h3_style),
     Paragraph("`app.py` saves the analysis in `st.session_state.analysis_result`. The action items list initializes a persistent dictionary "
               "`checklist_state = {item: False}`. The dashboard renders: (1) Interactive checklist with checkboxes and real-time completion percentage, "
               "(2) Prominent deadline callout, (3) Required certificates cards, and (4) Confusing fields decoded with supporting documents.", body_style)],
    [Paragraph("<b>Step 6: User Interaction & Grounded Q&A</b>", h3_style),
     Paragraph("When a user ticks a checkbox, Streamlit reactivity instantly recalculates progress (e.g. '3 of 7 tasks done - 42%'). "
               "If the user asks a question via the chat input (or clicks a suggested chip like 'What is the deadline?'), `app.py` calls "
               "`ask_document_ai()`. The LLM answers strictly using the document text, replying <i>'I couldn't find that information in the uploaded document'</i> "
               "if the query references out-of-scope facts.", body_style)]
]

pipeline_table = Table(pipeline_steps, colWidths=[150, 382])
pipeline_table.setStyle(TableStyle([
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("LINEBELOW", (0,0), (-1,-2), 0.5, colors.HexColor("#E2E8F0")),
    ("TOPPADDING", (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ("LEFTPADDING", (0,0), (-1,-1), 4),
    ("RIGHTPADDING", (0,0), (-1,-1), 4),
]))
elements.append(pipeline_table)
elements.append(Spacer(1, 8))

# SECTION 5: PROMPT ENGINEERING & JSON SCHEMA
elements.append(Paragraph("5. Prompt Engineering & Anti-Hallucination Guardrails", h1_style))
elements.append(Paragraph(
    "To ensure complete reliability for academic and official documents, the AI prompt is engineered with strict operational constraints:",
    body_style
))
elements.append(Paragraph("• <b>System Persona:</b> The model is instructed to act as an <i>AI Document Action Assistant</i> with the mission: <code>Document &rarr; Understanding &rarr; Action</code>.", bullet_style))
elements.append(Paragraph("• <b>Explicit Non-Hallucination Directive:</b> The prompt commands: <i>'Do not invent information. If information is not present in the document, explicitly say \"Not specified\" or use an empty list [].'</i>", bullet_style))
elements.append(Paragraph("• <b>Field Decoupling:</b> For every confusing field (e.g. 'Annual Family Income'), the model must provide both a simple English explanation and the exact supporting document required (e.g. 'Income Certificate').", bullet_style))

schema_snippet = (
    "{\n"
    "  \"document_title\": \"Document title or Not specified\",\n"
    "  \"document_type\": \"e.g. Scholarship Notice, Job Description, Circular\",\n"
    "  \"summary\": \"Concise 2-3 sentence overview\",\n"
    "  \"deadline\": \"Specific deadline date/time or Not specified\",\n"
    "  \"required_documents\": [\"Document 1\", \"Document 2\"],\n"
    "  \"important_fields\": [{\"field\": \"...\", \"explanation\": \"...\", \"required_document\": \"...\"}],\n"
    "  \"action_items\": [\"Step 1\", \"Step 2\"],\n"
    "  \"warnings\": [\"Warning 1\", \"Warning 2\"]\n"
    "}"
)
schema_table = Table([[Paragraph(f"<pre>{schema_snippet}</pre>", code_style)]], colWidths=[532])
schema_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
    ("BOX", (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING", (0,0), (-1,-1), 8),
    ("RIGHTPADDING", (0,0), (-1,-1), 8),
]))
elements.append(schema_table)
elements.append(Spacer(1, 8))

# SECTION 6: TESTING & DEPLOYMENT
elements.append(Paragraph("6. Quality Assurance & Cloud Continuous Deployment", h1_style))
elements.append(Paragraph(
    "<b>Automated Unit Tests (test_formfix.py):</b> FormFix AI includes an automated test suite verifying: (1) In-memory digital PDF generation "
    "and extraction via PyMuPDF; (2) Whitespace regex normalization; (3) Unsupported file format rejection; (4) Empty document handling; "
    "(5) Pillow contrast preprocessing; (6) JSON schema conformance; and (7) Code-fence stripping. All 7 tests pass in 0.09s.",
    body_style
))
elements.append(Paragraph(
    "<b>Continuous Cloud Deployment:</b> The codebase is deployed to <b>Streamlit Community Cloud</b> (connected to GitHub repository "
    "<code>paridhimuttyamwar/FormFix</code>). Every Git push automatically triggers a fast cloud rebuild. API credentials are encrypted "
    "in Streamlit Cloud Secrets (<code>st.secrets['GROQ_API_KEY']</code>), ensuring zero key exposure on public version control.",
    body_style
))

doc.build(elements, canvasmaker=NumberedCanvas)
print("Exhaustive report generated successfully at:", output_pdf)
