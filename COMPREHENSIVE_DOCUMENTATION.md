# FormFix AI - Comprehensive Technical Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [File-by-File Explanation](#file-by-file-explanation)
5. [Code Flow and Architecture](#code-flow-and-architecture)
6. [Library Explanations](#library-explanations)
7. [Machine Learning Models](#machine-learning-models)
8. [Testing](#testing)
9. [Deployment](#deployment)

---

## Project Overview

FormFix AI is an AI-powered document and form assistant designed to transform complex official documents (college circulars, scholarship notices, admission forms, government notifications) into clear, actionable information. The system follows the principle: **Document → Understanding → Action**.

### Key Features
- **Multi-format Document Support**: PDF, PNG, JPG, JPEG
- **Hybrid Text Extraction**: Native PDF text extraction with OCR fallback for scanned documents
- **Multilingual Support**: English, Hindi, Marathi
- **AI-Powered Analysis**: Extracts deadlines, required documents, action items, and warnings
- **Machine Learning Models**: 
  - Document authenticity and fraud detection
  - Urgency and risk assessment
- **Interactive Q&A**: Grounded chat assistant for document-specific questions
- **Security Focus**: Detects fraudulent patterns and warns users about potential scams

---

## Technology Stack

### Core Technologies

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend/UI** | Streamlit (≥1.35.0) | Web application framework for interactive UI |
| **Programming Language** | Python 3.10+ | Core application logic |
| **PDF Processing** | PyMuPDF (≥1.24.0) | Native PDF text extraction |
| **OCR** | pytesseract (≥0.3.10) + Pillow (≥10.0.0) | Optical character recognition for scanned documents |
| **AI/LLM** | Groq API (qwen/qwen3.8-27b, llama-3.3-70b-versatile) | Document analysis and Q&A |
| **Machine Learning** | scikit-learn (≥1.3.0) + numpy (≥1.24.0) | Logistic regression models for authenticity and urgency |
| **Configuration** | python-dotenv (≥1.0.0) | Environment variable management |

### No Complex Infrastructure
- No databases
- No vector databases
- No microservices
- No complex frontend frameworks
- Strict adherence to hackathon MVP guidelines

---

## Project Structure

```
FormFix-AI/
├── app.py                              # Main Streamlit application (v1 - simpler UI)
├── app1.py                             # Enhanced Streamlit application (v2 - rich UI)
├── ai_service.py                       # AI service (root level - backup)
├── ml_service.py                       # ML service (root level - backup)
├── ocr_service.py                      # OCR service (root level - backup)
├── requirements.txt                    # Python dependencies
├── .env                                # Environment variables (API keys)
├── .env.example                        # Environment template
├── .gitignore                          # Git ignore rules
├── README.md                           # Project documentation
├── test_formfix.py                     # Automated test suite
├── create_fake_notice_pdf.py           # Utility to create test PDFs
├── generate_detailed_report.py         # Report generation utility
├── generate_executive_summary.py       # Summary generation utility
├── generate_exhaustive_report.py       # Comprehensive report generator
│
├── services/                           # Service layer (primary location)
│   ├── __init__.py                     # Package initialization
│   ├── document_processor.py           # PDF/image text extraction
│   ├── ocr_service.py                  # OCR engine integration
│   ├── ai_service.py                   # Groq LLM client and analysis
│   └── ml_service.py                   # ML models (authenticity & urgency)
│
├── .streamlit/                         # Streamlit configuration directory
└── Fake_Govt_Job_Recruitment_Notice.pdf # Sample test document
```

---

## File-by-File Explanation

### 1. Configuration Files

#### `requirements.txt`
**Purpose**: Lists all Python package dependencies required for the project.

**Key Dependencies**:
- `streamlit` - Web UI framework
- `groq` - AI/LLM API client for Groq
- `python-dotenv` - Environment variable management
- `PyMuPDF` - PDF text extraction library
- `pytesseract` - OCR engine wrapper
- `Pillow` - Image processing library
- `scikit-learn` - Machine learning library
- `numpy` - Numerical computing library

#### `.env.example`
**Purpose**: Template for environment variables.

**Content**: Contains the GROQ_API_KEY placeholder. Users copy this to `.env` and add their actual API key from Groq console.

#### `.gitignore`
**Purpose**: Protects sensitive files and excludes build artifacts from version control.

**Excludes**: `.env` (API keys), `__pycache__/` (Python bytecode), `*.pyc`, `.streamlit/`, `venv/`, and uploaded PDFs.

---

### 2. Service Layer (Primary)

#### `services/__init__.py`
**Purpose**: Marks the `services` directory as a Python package, enabling imports like `from services.document_processor import ...`.

---

#### `services/document_processor.py`
**Purpose**: Handles document text extraction from PDFs and images.

**Key Functions**:

1. **Custom Exception** - `DocumentProcessingError` for user-facing error messages.

2. **Whitespace Cleaner** - Normalizes whitespace by removing extra spaces, tabs, and collapsing multiple newlines.

3. **PDF Processing** - Extracts text from PDFs using PyMuPDF. Includes a heuristic to detect scanned PDFs (average < 40 characters per page) and automatically falls back to OCR for scanned documents.

4. **Image Processing** - Extracts text from uploaded images using OCR.

5. **Main Entry Point** - `extract_document_text()` routes files based on extension: PDFs go to PDF processor, images (PNG, JPG, JPEG) go to image processor, and unsupported types raise an error.

**Library Used**: PyMuPDF (imported as `fitz`) for PDF handling, Pillow for image operations.

---

#### `services/ocr_service.py`
**Purpose**: Provides OCR capabilities for scanned documents and images.

**Key Functions**:

1. **Tesseract Configuration** - Automatically locates Tesseract OCR executable by checking system PATH, environment variables, and common Windows installation paths.

2. **Image Preprocessing** - Converts images to grayscale and enhances contrast to improve OCR accuracy.

3. **Text Extraction** - Runs Tesseract OCR on preprocessed images with multi-language support (English, Hindi, Marathi).

**Libraries Used**: 
- `pytesseract` - Python wrapper for Tesseract OCR engine
- `Pillow` (PIL) - Image processing and manipulation

**Error Handling**: Raises informative errors if Tesseract is not installed or OCR fails.

---

#### `services/ai_service.py`
**Purpose**: Integrates Groq LLM for document analysis and Q&A functionality.

**Key Functions**:

1. **Model Configuration** - Defines primary and fallback Groq models for reliability. If one model fails, the system tries the next in the list.

2. **Sample Data** - Contains pre-verified scholarship notice data for demo mode without requiring API calls.

3. **API Key Management** - Retrieves Groq API key from multiple sources in priority order: Streamlit Cloud secrets, local `.env` file, environment variables, or raw key parsing.

4. **JSON Response Cleaner** - Strips markdown code fences from LLM responses to extract pure JSON.

5. **Document Analysis** - Sends document text to Groq LLM with a structured system prompt that instructs the AI to:
   - Extract document title, type, summary, deadline
   - List required documents
   - Explain confusing fields
   - Generate action items (constructive steps)
   - Provide protective warnings (fraud detection for UPI payments, credential harvesting, informal channels)
   - Return structured JSON

6. **Q&A Assistant** - Answers user questions strictly grounded in the uploaded document text, maintaining chat history for context.

7. **Demo Analysis** - Returns pre-verified sample data for testing without API key.

**Library Used**: `groq` - Python client for Groq API, providing fast LLM inference.

**Security Features**: The system prompt includes fraud detection instructions to warn users about suspicious payment requests, credential harvesting, and informal communication channels.

---

#### `services/ml_service.py`
**Purpose**: Implements dual Logistic Regression models for document intelligence.

**Architecture**:
- **Model 1**: Notice Authenticity & Fraud/Spam Detector using NLP + TF-IDF
- **Model 2**: Deadline Urgency & Action Risk Engine using tabular features

**Key Components**:

1. **Multilingual Translation Table** - Dictionary that translates all ML output strings to English, Hindi, or Marathi.

2. **Translation Helper Functions** - Utility functions for translating static text, dynamic day counts, and document counts.

3. **Model 1: Notice Authenticity Model**
   - **Training Data**: 20 samples (10 authentic government/university notices, 10 scam/fraud notices)
   - **Model Pipeline**: TF-IDF vectorization (unigrams and bigrams, top 800 features) → Logistic Regression classifier
   - **Prediction Process**:
     - Predicts authenticity probability
     - Extracts linguistic cues via regex patterns (authentic cues: reference numbers, official domains, statutory vocabulary; fraud cues: payment solicitations, social channels, unrealistic promises, credential harvesting)
     - Applies heuristic calibration (caps authenticity at 28% if fraud signals detected)
     - Determines verdict based on score (Verified Official, Likely Official, Suspicious/Scam, Unverified)
     - Translates output to target language
   - **Output**: Authenticity score, fraud risk score, verdict, confidence, signals list, badge color

4. **Model 2: Urgency Risk Model**
   - **Training Data**: 24 scenarios (12 high urgency, 12 low urgency) with engineered features
   - **Model Architecture**: StandardScaler → Logistic Regression
   - **Feature Extraction**:
     - Days remaining (parses dates, calculates difference from today)
     - Document count (number of required documents)
     - Penalty clause (binary: presence of strict rejection/penalty keywords)
     - Offline requirement (binary: presence of physical submission keywords)
     - Action items count (number of steps required)
   - **Prediction Process**:
     - Extracts features and generates risk factors
     - Scales features using StandardScaler
     - Predicts urgency probability
     - Categorizes urgency level (Critical, Moderate, Routine)
     - Generates recommendations
     - Translates to target language
   - **Output**: Urgency score, urgency level, badge color, days left, risk factors, recommendation

5. **Global Singleton Management** - Lazy initialization of ML models to keep startup fast.

6. **Full Assessment Function** - `assess_document_ml()` runs both models and returns combined results.

**Libraries Used**:
- `scikit-learn` - Machine learning library (TF-IDF, Logistic Regression, StandardScaler)
- `numpy` - Numerical computing for feature arrays

---

### 3. Application Layer

#### `app.py` (Simpler UI Version)
**Purpose**: Main Streamlit web application with simplified, clean UI.

**Key Features**:
- Multilingual support (English, Hindi, Marathi) with UI string dictionary
- Session state management for analysis results, document text, ML evaluation, and chat history
- Document upload interface supporting PDF, PNG, JPG, JPEG
- Language change detection that re-runs analysis in new language
- Results dashboard with:
  - Trust & Urgency assessment scores
  - Action plan and warnings tabs
  - Deadlines and required documents sections
  - Confusing fields explained (expandable cards)
  - Interactive Q&A chat interface with document grounding

**Library Used**: `streamlit` - Web application framework

---

#### `app1.py` (Enhanced UI Version)
**Purpose**: Enhanced Streamlit application with rich custom styling and additional features.

**Additional Features Over app.py**:
- Custom CSS styling (hides sidebar, custom colors, card designs)
- 3-step process cards explaining the workflow
- Progress bar during document analysis with status updates
- Rich ML intelligence cards with color-coded badges
- File metadata display (name, type, size)
- Enhanced visual design with gradients and shadows

**Library Used**: `streamlit` with custom HTML/CSS injection

---

### 4. Root-Level Backup Files

#### `ai_service.py`, `ml_service.py`, `ocr_service.py`
**Purpose**: Backup copies of service files at root level.

**Why**: Fallback if `services/` package import fails (as seen in app.py import logic). Identical to `services/` versions.

---

### 5. Testing

#### `test_formfix.py`
**Purpose**: Automated test suite for all components.

**Test Coverage**:
1. Digital PDF text extraction using PyMuPDF
2. Whitespace normalization
3. Unsupported file type rejection
4. Empty file handling
5. OCR image preprocessing
6. Demo analysis schema validation
7. JSON response cleaning
8. ML authenticity classifier (official vs scam detection)
9. ML urgency risk model (critical vs low urgency)
10. Full dual-model assessment pipeline

**Running Tests**: `python test_formfix.py`

**Expected Output**: All tests pass with OK status.

**Library Used**: `unittest` - Python's built-in testing framework

---

### 6. Utility Scripts

#### `create_fake_notice_pdf.py`
**Purpose**: Generates test PDF documents for testing the application.

#### `generate_detailed_report.py`
**Purpose**: Generates detailed project reports.

#### `generate_executive_summary.py`
**Purpose**: Generates executive summaries.

#### `generate_exhaustive_report.py`
**Purpose**: Generates comprehensive project documentation.

---

## Code Flow and Architecture

### Overall Architecture

```
User Interface (Streamlit: app.py / app1.py)
         ↓
Document Processing Layer (services/document_processor.py)
  - PDF text extraction (PyMuPDF)
  - Scanned PDF detection
  - Image processing (Pillow)
         ↓ (if scanned/image)
OCR Layer (services/ocr_service.py)
  - Image preprocessing (grayscale, contrast)
  - Tesseract OCR integration
  - Multi-language support
         ↓ (cleaned text)
AI Analysis Layer (services/ai_service.py)
  - Groq LLM integration
  - Document structure analysis
  - JSON schema extraction
  - Fraud detection in prompts
  - Multilingual output
         ↓ (structured JSON)
Machine Learning Layer (services/ml_service.py)
  Model 1: Authenticity Detector (TF-IDF + LogReg)
  Model 2: Urgency Risk Engine (Tabular + LogReg)
         ↓ (ML predictions)
Q&A Layer (services/ai_service.py)
  - Grounded question answering
  - Chat history management
  - Multilingual responses
         ↓
Results Display (Streamlit Dashboard)
  - Trust & Urgency scores
  - Action plan checklist
  - Warnings & security alerts
  - Required documents list
  - Confusing fields explained
  - Interactive chat interface
```

### Document Upload Flow

1. User uploads file via Streamlit file uploader
2. File type detection (.pdf, .png, .jpg, .jpeg)
3. Route to appropriate processor:
   - PDF: Open with PyMuPDF, extract native text, check if scanned (heuristic: < 40 chars/page)
   - If scanned: Convert pages to images, apply OCR
   - Image: Direct OCR processing
4. Clean text (whitespace normalization)
5. Return cleaned text for analysis

### AI Analysis Flow

1. Receive cleaned document text
2. Check Groq API key configuration
3. Construct system prompt with:
   - Role definition (Expert AI Document Action Assistant)
   - Language instruction (if not English)
   - Security instructions (fraud detection patterns)
   - JSON schema specification
4. Send to Groq LLM with model fallback
5. Receive response
6. Clean JSON (remove markdown fences)
7. Parse and validate JSON
8. Return structured analysis

### ML Assessment Flow

1. Receive document text and AI analysis
2. Initialize ML models (lazy load)
3. Run Model 1 (Authenticity):
   - TF-IDF vectorization
   - Logistic Regression prediction
   - Regex pattern matching (authentic + fraud cues)
   - Heuristic calibration
   - Verdict determination
   - Translation to target language
4. Run Model 2 (Urgency):
   - Feature extraction (days, docs, penalty, offline, actions)
   - StandardScaler normalization
   - Logistic Regression prediction
   - Urgency level categorization
   - Risk factor generation
   - Recommendation generation
   - Translation to target language
5. Return combined ML result

### Q&A Flow

1. User asks question via chat interface
2. Retrieve document text from session state
3. Retrieve chat history (last 4 messages)
4. Construct system prompt with grounded rules
5. Add language instruction (if not English)
6. Build message array (system, history, document, question)
7. Send to Groq LLM
8. Receive response
9. Display in chat interface
10. Append to chat history

### Language Change Flow

1. User changes language selector
2. Detect language change (current_lang vs target_language)
3. Re-run AI analysis with new language instruction
4. Re-run ML assessment with translation helpers
5. Reset chat history (language changed)
6. Update current_lang in session state
7. Rerun Streamlit app

---

## Library Explanations

### Streamlit
**Purpose**: Web application framework for building interactive data apps.

**Key Features Used**:
- File uploader for document upload
- Session state management
- Progress bars and spinners
- Chat interface components
- Tabs and expanders
- Custom CSS injection
- Metrics and columns for layout

**Why Chosen**: Rapid development, no frontend knowledge required, perfect for data/ML applications.

---

### PyMuPDF (fitz)
**Purpose**: PDF text extraction and manipulation library.

**Key Features Used**:
- Open PDF from bytes
- Extract native text from pages
- Convert pages to images (for OCR)
- Calculate text length for scanned detection

**Why Chosen**: Fast, reliable, supports both digital and scanned PDFs.

---

### Pillow (PIL)
**Purpose**: Image processing library.

**Key Features Used**:
- Open images from bytes
- Convert to grayscale
- Enhance contrast
- Image format validation

**Why Chosen**: Standard Python image library, works seamlessly with Tesseract OCR.

---

### pytesseract
**Purpose**: Python wrapper for Tesseract OCR engine.

**Key Features Used**:
- Run Tesseract OCR on images
- Multi-language support (eng+hin+mar)
- Path configuration for different OS

**Why Chosen**: Opensource OCR, supports multiple languages, reliable text extraction.

---

### Groq
**Purpose**: Python client for Groq API providing fast LLM inference.

**Key Features Used**:
- Chat completions API
- Multiple model support with fallback
- JSON response format
- Low latency inference

**Why Chosen**: Fast inference speeds, cost-effective, multiple model options, easy integration.

---

### scikit-learn
**Purpose**: Machine learning library for Python.

**Key Features Used**:
- TF-IDF vectorization (text to numerical features)
- Logistic Regression classifier
- StandardScaler for feature normalization
- Pipeline for model composition

**Why Chosen**: Industry-standard ML library, reliable, well-documented, easy to use.

---

### numpy
**Purpose**: Numerical computing library.

**Key Features Used**:
- Numerical arrays for feature vectors
- Array operations and transformations

**Why Chosen**: Efficient numerical operations, standard in ML workflows.

---

### python-dotenv
**Purpose**: Environment variable management from .env files.

**Key Features Used**:
- Load environment variables from .env
- Override existing environment variables
- Multiple .env file support

**Why Chosen**: Secure API key management, easy configuration, standard practice.

---

## Machine Learning Models

### Model 1: Notice Authenticity & Fraud Detector

**Purpose**: Classify documents as authentic official notices or potential scams/fraud.

**Approach**: NLP + TF-IDF + Logistic Regression + Regex Pattern Matching

**Training Data**:
- 10 authentic government/university notices
- 10 scam/fraud notices
- Balanced dataset (50/50)

**Model Pipeline**:
1. TF-IDF Vectorization
   - Unigrams and bigrams (captures phrases)
   - Top 800 features
   - Stop words removal
   - Log-scaled term frequency

2. Logistic Regression Classifier
   - Regularization strength (C=1.5)
   - Maximum iterations (300)
   - Predicts probability of authentic class

**Prediction Process**:
1. Predict authenticity probability using trained model
2. Extract linguistic cues via regex patterns:
   - Authentic patterns: reference numbers, official domains, statutory vocabulary, administrative designations
   - Fraud patterns: payment solicitations, social channels, unrealistic promises, credential harvesting
3. Apply heuristic calibration (cap authenticity at 28% if fraud signals detected)
4. Determine verdict based on score thresholds
5. Translate output to target language

**Output Interpretation**:
- ≥ 80%: Verified Official Notice (Green)
- 50-79%: Likely Official Circular (Blue)
- < 50% with fraud ≥ 70%: Suspicious/Scam (Red)
- < 50% with fraud < 70%: Unverified/Irregular (Amber)

---

### Model 2: Urgency Risk Engine

**Purpose**: Predict deadline urgency and submission risk level.

**Approach**: Tabular Feature Engineering + Logistic Regression

**Training Data**:
- 12 high urgency scenarios (tight deadlines, heavy requirements, penalties, offline)
- 12 low urgency scenarios (ample time, digital, fewer requirements)
- Balanced dataset

**Feature Engineering**:
1. Days Remaining
   - Parse date from deadline text (multiple formats)
   - Calculate days until deadline
   - Support relative dates (today, tomorrow, 3 days)
   - Default: 14 days if not found

2. Document Count
   - Number of required documents
   - Risk factor if ≥ 5 docs

3. Penalty Clause (Binary)
   - Presence of strict rejection/penalty keywords

4. Offline Requirement (Binary)
   - Presence of physical submission keywords

5. Action Items Count
   - Number of steps required

**Model Architecture**:
1. StandardScaler - Normalizes features to zero mean, unit variance
2. Logistic Regression - Predicts probability of high urgency class

**Prediction Process**:
1. Extract features from document analysis
2. Generate risk factors based on feature values
3. Scale features using StandardScaler
4. Predict urgency probability
5. Categorize urgency level based on score and days
6. Generate recommendation
7. Translate to target language

**Output Interpretation**:
- ≥ 70% or ≤ 3 days: Critical Urgency (Red) - Start gathering documents today
- 38-69%: Moderate Urgency (Amber) - Plan within next few days
- < 38%: Routine/Low Urgency (Green) - Comfortable window, regular preparation

---

## Testing

### Test Strategy

The test suite covers all major components:
- Document processing (PDF extraction, OCR, whitespace cleaning)
- AI service (schema validation, JSON cleaning, API configuration)
- Machine learning (authenticity classifier, urgency model, full assessment)

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate.ps1  # Windows

# Run tests
python test_formfix.py
```

### Test Interpretation

All tests should pass with "OK" status. Each test validates a specific component's functionality.

---

## Deployment

### Local Development

**Setup Steps**:
1. Clone repository
2. Create virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Configure environment: Copy `.env.example` to `.env`, add Groq API key
5. Run application: `streamlit run app.py` or `streamlit run app1.py`
6. Access at http://localhost:8501

### Streamlit Cloud Deployment

**Requirements**:
- Repository on GitHub
- Groq API key in Streamlit secrets

**Steps**:
1. Push code to GitHub
2. Go to share.streamlit.io
3. Connect repository
4. Add secret: `GROQ_API_KEY` = your key
5. Deploy

**Environment Variable Priority**:
1. Streamlit Cloud secrets
2. Local .env file
3. Environment variable
4. Raw key in .env (fallback)

### Optional: Tesseract OCR Installation

**For local development with scanned documents**:

**Windows**: Download from UB-Mannheim/tesseract GitHub
**Linux**: `sudo apt-get install tesseract-ocr tesseract-ocr-hin tesseract-ocr-mar`
**macOS**: `brew install tesseract`

**Note**: Digital PDFs work without Tesseract. OCR only needed for scanned documents.

---

## Security Considerations

### API Key Management
- Never hardcoded in source code
- Stored in `.env` (gitignored)
- Streamlit Cloud secrets for deployment
- Multiple fallback mechanisms

### Fraud Detection
- AI prompt engineering detects scam patterns
- ML model 1 classifies authenticity
- Both layers provide warnings to users

### Privacy
- Documents processed in memory only
- No persistent storage
- No database
- Session-based (resets on refresh)

### Input Validation
- File type restrictions (PDF, PNG, JPG, JPEG)
- File size limits (Streamlit default: 200MB)
- Empty file handling
- Corrupted file handling

### Error Handling
- User-friendly error messages
- Graceful degradation (OCR fallback)
- Model fallback (multiple Groq models)
- Language-specific error messages

---

## Performance Optimization

### Lazy Loading
ML models are loaded on first use to keep startup fast, not on import.

### Model Fallback
System tries multiple Groq models in sequence if one fails, ensuring reliability.

### Progress Feedback
Visual progress bar during analysis with status updates for better user experience.

---

## Limitations and Future Scope

### Current Limitations

1. **OCR Accuracy**: Depends on image quality, requires Tesseract installation, limited to eng+hin+mar
2. **Document Complexity**: Multi-page complex tables may flatten, handwritten text not supported
3. **Session State**: Resets on browser refresh, no persistent storage, single-user sessions
4. **ML Models**: Small training dataset (20 samples each), static models, limited to English pattern matching

### Future Enhancements

1. **Multi-language Translation**: Support for regional state circulars, automatic language detection
2. **Calendar Integration**: Google Calendar sync, iCal export, deadline reminders
3. **PDF Form Filling**: Auto-populate fillable PDFs, applicant profile integration
4. **Enhanced ML**: Larger training datasets, online learning from feedback, sophisticated models (BERT)
5. **Persistence**: User accounts, document history, saved analysis
6. **Batch Processing**: Multiple document upload, bulk analysis, comparison features

---

## Conclusion

FormFix AI is a comprehensive document intelligence system combining:

- **Traditional NLP**: Text extraction, OCR, pattern matching
- **Modern AI**: LLM-powered analysis via Groq
- **Machine Learning**: Dual Logistic Regression models for authenticity and urgency
- **User Experience**: Multilingual, interactive Streamlit interface
- **Security**: Fraud detection and risk assessment

The system follows clean architecture with clear separation of concerns across document processing, AI analysis, machine learning, and application layers. All components work together to transform complex official documents into clear, actionable insights while protecting users from fraud and scams.

---

## Quick Reference

### Key Files Summary

| File | Purpose | Key Functions |
|------|---------|---------------|
| `app.py` | Main Streamlit app (simple UI) | Upload, analysis, display |
| `app1.py` | Enhanced Streamlit app (rich UI) | Custom styling, progress bars |
| `services/document_processor.py` | Text extraction | PDF/image processing, OCR routing |
| `services/ocr_service.py` | OCR integration | Tesseract configuration, image preprocessing |
| `services/ai_service.py` | LLM integration | Document analysis, Q&A assistant |
| `services/ml_service.py` | ML models | Authenticity detection, urgency prediction |
| `test_formfix.py` | Test suite | Component validation |

### Key Functions

**Document Processing**:
- `extract_document_text(file_name, file_bytes)` - Main entry point for text extraction
- `process_pdf(file_bytes)` - PDF text extraction with OCR fallback
- `process_image(file_bytes)` - Image OCR processing

**AI Analysis**:
- `analyze_document_with_ai(text, target_language, api_key)` - Structured JSON analysis
- `ask_document_ai(text, question, chat_history, target_language, api_key)` - Grounded Q&A

**Machine Learning**:
- `assess_document_ml(text, analysis, target_language)` - Full ML assessment
- `NoticeAuthenticityModel.predict(text, target_language)` - Authenticity score
- `UrgencyRiskModel.predict(deadline, docs, actions, text, target_language)` - Urgency score

### Configuration

**Environment Variables**:
- `GROQ_API_KEY`: Groq API key (required for AI features)
- `TESSERACT_CMD`: Optional Tesseract path (for OCR)

**Run Commands**:
```bash
# Development
streamlit run app.py
streamlit run app1.py

# Testing
python test_formfix.py

# Dependencies
pip install -r requirements.txt
```

---

*Documentation generated for FormFix AI project - Comprehensive technical reference for developers and contributors.*
