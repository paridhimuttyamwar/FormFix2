# FormFix AI

> **Don’t just understand the form. Know what to do next.**

FormFix AI is an AI-powered document and form assistant designed to turn complex college circulars, scholarship renewal notices, admission forms, government notifications, and official PDFs into simple explanations, prominent deadlines, required document checklists, and an interactive, step-by-step action plan.

Unlike generic PDF summarizers, FormFix AI is engineered around the principle:
$$\text{Document} \longrightarrow \text{Understanding} \longrightarrow \text{Action}$$

---

## 📌 Problem

Students and applicants frequently face dense, jargon-laden administrative notices (scholarship criteria, university guidelines, government application forms) with buried deadlines and unclear paperwork requirements. Missing an obscure requirement or a single document often leads to disqualified applications, lost financial aid, or delayed admissions.

## 💡 Solution

FormFix AI ingests digital or scanned documents (PDFs, PNG, JPG) and automatically:
1. **Extracts core facts & intent** (title, document classification, plain-English summary).
2. **Surfaces the submission deadline prominently** so critical cutoff dates are never missed.
3. **Decodes confusing fields & jargon** (e.g. "Annual Family Income" ceiling $\rightarrow$ exact meaning and which authority's certificate is required).
4. **Generates an interactive Action Checklist** that users can tick off step-by-step.
5. **Provides a grounded Ask AI assistant** that answers applicant questions strictly using the uploaded document text (preventing hallucinations).

---

## 🚀 Key Features

- **Document Ingestion:** Drag-and-drop support for PDF, PNG, JPG, and JPEG files.
- **Hybrid Extraction Pipeline:** Fast native text extraction via PyMuPDF (`fitz`), with automatic fallback to image OCR (`pytesseract` + Pillow) for scanned documents.
- **Action-First Results Dashboard:**
  - **What You Need to Do (Hero Action Checklist):** Interactive checkboxes with real-time completion progress tracking.
  - **Important Deadline Alert:** High-visibility banner highlighting cutoff dates and submission times.
  - **Required Documents List:** Complete itemized list of mandatory certificates and marksheets.
  - **Confusing Fields Explained:** Breakdown of bureaucratic criteria paired with their corresponding supporting documents.
  - **Warnings & Restrictions:** Clear callouts for disqualification criteria, backlog rules, or penalties.
- **Interactive Ask AI:** Q&A interface with suggested quick-prompt chips ("What is the deadline?", "Which documents do I need?", etc.) and custom questions, strictly grounded in the document.
- **Fail-Safe & Demo Mode:** 1-click built-in test using a pre-packaged, realistic scholarship renewal notice—runs with or without an active Groq API key.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend / UI** | [Streamlit](https://streamlit.io/) |
| **Programming Language** | Python 3.10+ |
| **PDF Text Extraction** | [PyMuPDF](https://pymupdf.readthedocs.io/) |
| **OCR (Optical Character Recognition)** | [pytesseract](https://pypi.org/project/pytesseract/) & [Pillow (PIL)](https://pillow.readthedocs.io/) |
| **Language Model (LLM)** | [Groq API](https://groq.com/) running `llama-3.3-70b-versatile` / `llama-3.1-8b-instant` |
| **Configuration** | `python-dotenv` |

*(No databases, vector databases, microservices, or complex frontend frameworks—strictly adhering to hackathon MVP guidelines.)*

---

## 🏗️ Architecture

```
[ User Document (PDF / Image) ]
               │
               ▼
┌───────────────────────────────┐
│ services/document_processor.py│
│ 1. Extension Detection        │
│ 2. PyMuPDF Native Extraction  │
│ 3. Scanned PDF / Image Check  │
└──────────────┬────────────────┘
               │ (Fallback if scanned / image)
               ▼
┌───────────────────────────────┐
│    services/ocr_service.py    │
│ Grayscale + Contrast Enhance  │
│       Pytesseract OCR         │
└──────────────┬────────────────┘
               │
               ▼ Clean Extracted Text
┌───────────────────────────────┐
│     services/ai_service.py    │
│ Groq API (Llama 3.3 70B JSON) │
│ Grounded Q&A Assistant        │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│             app.py            │
│ Streamlit Interactive Web App │
│ - Action Plan Checklist       │
│ - Deadline & Requirements     │
│ - Grounded Chat (Ask AI)      │
└───────────────────────────────┘
```

---

## 📁 Project Structure

```
FormFix-AI/
├── app.py                      # Main Streamlit web application
├── requirements.txt            # Minimal Python dependencies
├── .env                        # Local environment variables (GROQ_API_KEY)
├── .env.example                # Example environment template
├── .gitignore                  # Git ignore rules protecting keys and cache
├── README.md                   # Complete documentation
├── test_formfix.py             # Automated test suite
│
├── services/
│   ├── __init__.py
│   ├── document_processor.py   # PDF text extraction & scanned detection
│   ├── ocr_service.py          # Image preprocessing & OCR engine integration
│   └── ai_service.py           # Groq LLM client, schema validation & grounded Q&A
│
└── sample_documents/
    └── scholarship_notice.pdf  # Fictional scholarship renewal notice for testing
```

---

## ⚙️ Installation & Setup

### 1. Clone or Navigate to Project Directory
```bash
cd FormFix-AI
```

### 2. Create and Activate a Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the `.env.example` file to `.env`:
```bash
cp .env.example .env
```
Edit `.env` and insert your Groq API key:
```env
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
```
*(You can get a free, ultra-fast API key at [console.groq.com](https://console.groq.com/keys).)*

> **Note on OCR (Optional for scanned documents):**
> If you wish to test OCR on scanned image-based PDFs or JPG/PNG files, ensure Tesseract OCR is installed on your operating system:
> - **Windows:** Download installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki).
> - **Ubuntu/Debian:** `sudo apt-get install tesseract-ocr`
> - **macOS:** `brew install tesseract`
> If Tesseract is not installed, digital PDFs will still process seamlessly, and the app will provide a friendly notice.

---

## 🖥️ How to Run

Launch the Streamlit app:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🧪 Testing & Demo Walkthrough

### 1-Click Instant Demo
1. Launch the app.
2. In the sidebar, click **"📄 Load Sample Scholarship Notice"**.
3. Click **"🧪 Instant Demo Mode (Pre-verified Sample)"** or **"🚀 Analyze Document"** (if Groq key is added).
4. Inspect the:
   - **Deadline:** 15 October 2026.
   - **Required Documents:** Marksheet, Bonafide, Income Certificate, Fee Receipt, Bank Passbook.
   - **Action Plan:** Tick off checklist items.
   - **Ask FormFix AI:** Click "What is the deadline?" or ask "What is the income limit?".

### Automated Test Suite
Run the test suite from the terminal:
```bash
python test_formfix.py
```
Expected output:
```
Ran 8 tests in 0.028s
OK
```

---

## 🔒 Security & Privacy

- **No Hardcoded Credentials:** API keys are never placed in source code or sent to the frontend.
- **Protected Environment:** `.env` is listed in `.gitignore`.
- **Privacy by Design:** Sample documents contain purely fictional names, authorities, and references.

---

## ⚠️ Limitations & Future Scope

### Current MVP Limitations
- Scanned OCR accuracy depends on image quality and local Tesseract availability.
- Multi-page documents with complex table layouts may have flattened tabular text.
- Session state resets on browser tab refresh.

### Future Scope
- Multi-language translation for regional state circulars.
- Automatic calendar sync (Google Calendar / iCal reminder for deadlines).
- PDF fill-in assistant that auto-populates fillable PDF forms based on applicant profile.
