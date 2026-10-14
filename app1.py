import os
import sys
import time
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

# Ensure local services package is importable first
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import importlib

try:
    import services.ai_service as ai_service_module
    importlib.reload(ai_service_module)
    from services.document_processor import extract_document_text, DocumentProcessingError
    from services.ai_service import (
        analyze_document_with_ai,
        ask_document_ai,
        is_groq_configured,
        get_groq_api_key,
        get_demo_analysis
    )
    from services.ml_service import assess_document_ml
except ImportError:
    import ai_service as ai_service_module
    importlib.reload(ai_service_module)
    from document_processor import extract_document_text, DocumentProcessingError
    from ai_service import (
        analyze_document_with_ai,
        ask_document_ai,
        is_groq_configured,
        get_groq_api_key,
        get_demo_analysis
    )
    from ml_service import assess_document_ml

# Load environment dynamically
env_file_path = Path(__file__).resolve().parent / ".env"
if env_file_path.exists():
    load_dotenv(dotenv_path=env_file_path, override=True)
else:
    load_dotenv(override=True)

# Page Configuration
st.set_page_config(
    page_title="FormFix AI | Don't just understand the form. Know what to do next.",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Styling
st.markdown("""
<style>
    /* Hide Streamlit Sidebar Completely */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    section[data-testid="stSidebar"] {
        display: none !important;
    }

    /* Global styles */
    .main-header {
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
    }
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .tagline {
        font-size: 1.35rem;
        font-weight: 600;
        color: #1F2937;
        margin-bottom: 0.5rem;
    }
    .hero-desc {
        font-size: 1.05rem;
        color: #4B5563;
        max-width: 780px;
        margin: 0 auto 1.5rem auto;
        line-height: 1.6;
    }
    
    /* Feature cards on Landing Page */
    .step-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1.25rem 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        height: 100%;
        text-align: left;
    }
    .step-number {
        font-size: 1.5rem;
        font-weight: 800;
        color: #2563EB;
        margin-bottom: 0.3rem;
    }
    .step-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0.3rem;
    }
    .step-text {
        font-size: 0.92rem;
        color: #4B5563;
        line-height: 1.45;
    }

    /* Dashboard result cards */
    .hero-action-card {
        background: linear-gradient(180deg, #F0FDF4 0%, #DCFCE7 100%);
        border: 2px solid #86EFAC;
        border-radius: 14px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .hero-action-title {
        font-size: 1.4rem;
        font-weight: 800;
        color: #166534;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .deadline-card {
        background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
        border: 2px solid #FCA5A5;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        margin-bottom: 1.2rem;
    }
    .deadline-title {
        font-size: 0.9rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #991B1B;
    }
    .deadline-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #B91C1C;
        margin-top: 0.2rem;
    }

    .info-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .field-card {
        background: #F9FAFB;
        border-left: 4px solid #2563EB;
        border-radius: 6px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.75rem;
    }
    .field-name {
        font-size: 1.05rem;
        font-weight: 700;
        color: #1E3A8A;
    }
    .field-desc {
        font-size: 0.93rem;
        color: #374151;
        margin: 0.25rem 0;
    }
    .field-doc {
        font-size: 0.85rem;
        font-weight: 600;
        color: #047857;
    }

    .warning-box {
        background-color: #FFFBEB;
        border-left: 5px solid #F59E0B;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "document_text" not in st.session_state:
    st.session_state.document_text = None
if "document_name" not in st.session_state:
    st.session_state.document_name = None
if "checklist_state" not in st.session_state:
    st.session_state.checklist_state = {}
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "is_demo_mode" not in st.session_state:
    st.session_state.is_demo_mode = False
if "custom_groq_key" not in st.session_state:
    st.session_state.custom_groq_key = ""
if "ml_assessment" not in st.session_state:
    st.session_state.ml_assessment = None


# Top bar with Language Selector
col_brand, col_lang = st.columns([4, 1.3])
with col_lang:
    selected_lang_choice = st.selectbox(
        "🌐 Language / भाषा",
        ["English", "हिन्दी (Hindi)", "मराठी (Marathi)"],
        index=0,
        key="app_lang_choice"
    )

LANG_MAP = {
    "English": "English",
    "हिन्दी (Hindi)": "Hindi",
    "मराठी (Marathi)": "Marathi"
}
target_language = LANG_MAP[selected_lang_choice]
st.session_state.target_language = target_language

# Header / Landing Hero
with col_brand:
    st.markdown("""
    <div class="main-header" style="margin-bottom: 0.5rem; text-align: left;">
        <div class="main-title">FormFix AI</div>
        <div class="tagline">Don’t just understand the form. Know what to do next.</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="hero-desc" style="margin-bottom: 1.5rem;">
    Upload a complicated form, notice, circular, or official document and let AI turn it into simple explanations, prominent deadlines, required documents, and an actionable step-by-step checklist.
</div>
""", unsafe_allow_html=True)

# 3-Step Process Cards
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="step-card">
        <div class="step-number">01</div>
        <div class="step-title">Upload</div>
        <div class="step-text">Upload your college notice, scholarship form, circular PDF, or scanned document image.</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="step-card">
        <div class="step-number">02</div>
        <div class="step-title">Understand</div>
        <div class="step-text">AI extracts clear facts, decodes confusing bureaucratic fields, and highlights critical deadlines.</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="step-card">
        <div class="step-number">03</div>
        <div class="step-title">Take Action</div>
        <div class="step-text">Get an interactive, prioritized checklist of every single step and supporting document needed.</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Document Upload Section (Shown when no analysis or when user wants to analyze)
with st.container():
    st.markdown("### 📥 Upload Your Document")

    uploaded_file = st.file_uploader(
        "Choose a file to analyze (PDF, PNG, JPG, JPEG)",
        type=["pdf", "png", "jpg", "jpeg"],
        help="Upload official PDF forms, admission circulars, scholarship guidelines, or clear photos."
    )

    # Determine file source (either direct upload or sample document preloaded)
    file_to_process = None
    file_name = None
    file_bytes = None

    if uploaded_file is not None:
        file_name = uploaded_file.name
        file_bytes = uploaded_file.getvalue()
        file_size_kb = len(file_bytes) / 1024
        file_type = uploaded_file.type or Path(file_name).suffix.upper()

        # File Metadata Display
        meta_col1, meta_col2, meta_col3 = st.columns(3)
        with meta_col1:
            st.metric("File Name", file_name)
        with meta_col2:
            st.metric("File Type", file_type)
        with meta_col3:
            st.metric("File Size", f"{file_size_kb:.1f} KB")

        # Analyze Button
        analyze_clicked = st.button("🚀 Analyze Document", type="primary", use_container_width=True)

        effective_key = get_groq_api_key()

        # Handle Live AI Analysis Execution
        if analyze_clicked:
            if not effective_key:
                st.error("⚠️ AI service is not configured. Please ensure GROQ_API_KEY is in your .env file.")
            else:
                progress_container = st.container()
                with progress_container:
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    try:
                        # Step 1: File received
                        status_text.markdown("⏳ **File received...**")
                        progress_bar.progress(15)
                        time.sleep(0.3)

                        # Step 2: Extracting text
                        status_text.markdown("📄 **Extracting text from document...**")
                        progress_bar.progress(35)
                        extracted_text = extract_document_text(file_name, file_bytes)
                        st.session_state.document_text = extracted_text
                        time.sleep(0.3)

                        # Step 3: Understanding document
                        status_text.markdown("🧠 **Understanding document with AI (Llama-3 via Groq)...**")
                        progress_bar.progress(60)
                        time.sleep(0.3)

                        # Step 4: Identifying requirements & JSON analysis
                        status_text.markdown("🔍 **Identifying requirements and confusing fields...**")
                        progress_bar.progress(85)
                        try:
                            result = analyze_document_with_ai(
                                document_text=extracted_text,
                                target_language=target_language,
                                api_key=effective_key
                            )
                        except TypeError:
                            result = analyze_document_with_ai(
                                document_text=extracted_text,
                                api_key=effective_key
                            )
                        time.sleep(0.2)

                        # Step 5: Machine Learning Evaluation (Authenticity & Urgency via Logistic Regression)
                        status_text.markdown("🤖 **Running Machine Learning Risk & Authenticity Analysis (Logistic Regression)...**")
                        progress_bar.progress(92)
                        ml_evaluation = assess_document_ml(extracted_text, result, target_language=target_language)
                        st.session_state.ml_assessment = ml_evaluation
                        time.sleep(0.2)

                        # Step 6: Finalizing action plan
                        status_text.markdown("✅ **Finalizing your personalized action plan...**")
                        progress_bar.progress(100)
                        time.sleep(0.2)

                        # Save to session state
                        st.session_state.analysis_result = result
                        st.session_state.document_name = file_name
                        st.session_state.is_demo_mode = False
                        st.session_state.checklist_state = {item: False for item in result.get("action_items", [])}
                        st.session_state.chat_messages = []
                        st.session_state.current_lang = target_language  # Track language at analysis time

                        status_text.empty()
                        progress_bar.empty()
                        st.rerun()

                    except DocumentProcessingError as dpe:
                        status_text.empty()
                        progress_bar.empty()
                        st.error(f"❌ {str(dpe)}")
                    except ValueError as ve:
                        status_text.empty()
                        progress_bar.empty()
                        st.error(f"⚠️ {str(ve)}")
                    except Exception as e:
                        status_text.empty()
                        progress_bar.empty()
                        st.error(f"The AI service is temporarily unavailable. Details: {str(e)}")

# ==========================================
# RESULTS DASHBOARD
# ==========================================
if st.session_state.analysis_result:
    res = st.session_state.analysis_result

    # --- Language-Change Detection: Re-run AI analysis if language switched ---
    if st.session_state.get("current_lang") != target_language and st.session_state.get("document_text"):
        with st.spinner("Translating analysis to selected language..."):
            try:
                new_result = analyze_document_with_ai(
                    document_text=st.session_state.document_text,
                    target_language=target_language,
                    api_key=st.session_state.get("custom_groq_key") or os.getenv("GROQ_API_KEY", "")
                )
            except TypeError:
                new_result = analyze_document_with_ai(
                    document_text=st.session_state.document_text,
                    api_key=st.session_state.get("custom_groq_key") or os.getenv("GROQ_API_KEY", "")
                )
            st.session_state.analysis_result = new_result
            # Re-run ML with new language so signals/verdicts translate too
            st.session_state.ml_assessment = assess_document_ml(
                st.session_state.document_text,
                new_result,
                target_language=target_language
            )
            st.session_state.current_lang = target_language
            st.session_state.checklist_state = {item: False for item in new_result.get("action_items", [])}
            st.session_state.chat_messages = []
            st.rerun()

    st.markdown("---")

    # Header with title and action button
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.subheader("📊 Document Intelligence Dashboard")
    with header_col2:
        if st.button("🔄 Upload New Document", use_container_width=True):
            st.session_state.analysis_result = None
            st.session_state.document_text = None
            st.session_state.document_name = None
            st.session_state.checklist_state = {}
            st.session_state.chat_messages = []
            st.session_state.ml_assessment = None
            st.rerun()

    # MACHINE LEARNING INTELLIGENCE: DUAL LOGISTIC REGRESSION MODELS
    if not st.session_state.get("ml_assessment") and st.session_state.get("document_text"):
        st.session_state.ml_assessment = assess_document_ml(st.session_state.document_text, res, target_language=target_language)

    ml_eval = st.session_state.get("ml_assessment")
    if ml_eval:
        auth_data = ml_eval.get("authenticity", {})
        urg_data = ml_eval.get("urgency", {})

        #st.markdown("#### 🤖 Machine Learning Intelligence *(Logistic Regression)*")
        ml_col1, ml_col2 = st.columns(2)

        with ml_col1:
            auth_score = auth_data.get("authenticity_score")
            auth_color = auth_data.get("badge_color", "#10B981")
            verdict = auth_data.get("verdict", "Verified Notice")
            confidence = auth_data.get("confidence", "High Confidence")
            auth_score_text = f"{auth_score}%" if auth_score is not None else ("अनुपलब्ध" if target_language == "Hindi" else ("अनुपलब्ध" if target_language == "Marathi" else "N/A"))
            signals_html = "".join(f"<li style='margin-bottom: 2px;'>{sig}</li>" for sig in auth_data.get("signals", []))

            is_fic = auth_data.get("is_fictional", False)
            fic_evidence = auth_data.get("fictional_evidence")
            fic_page = auth_data.get("fictional_page", 1)
            doc_status = auth_data.get("document_status", verdict)
            official_auth = auth_data.get("official_authenticity", "Official authenticity not independently verified")

            if is_fic:
                fic_header = {
                    "Hindi": f"⚠️ **काल्पनिक / मॉक नोटिस (गैर-आधिकारिक)**\n\n**पहचाना गया अस्वीकरण (पृष्ठ {fic_page}):** *\"{fic_evidence}\"*\n\n**आधिकारिक प्रामाणिकता:** {official_auth}",
                    "Marathi": f"⚠️ **काल्पनिक / नमुना नोटीस (अनधिकृत प्रात्यक्षिक)**\n\n**आढळलेले अस्वीकरण (पृष्ठ {fic_page}):** *\"{fic_evidence}\"*\n\n**अधिकृत सत्यता:** {official_auth}",
                    "English": f"⚠️ **Fictional / Mock Notice (Non-Official Demonstration)**\n\n**Detected Disclaimer (Page {fic_page}):** *\"{fic_evidence}\"*\n\n**Official Authenticity:** {official_auth}"
                }.get(target_language, f"⚠️ **Fictional / Mock Notice** (Page {fic_page}): *\"{fic_evidence}\"*")
                st.warning(fic_header)

            if is_fic:
                _auth_title = {"English": "📊 ML Text Consistency Score", "Hindi": "📊 एमएल पाठ प्रारूप संगति स्कोर", "Marathi": "📊 एमएल मजकूर रचना सुसंगतता गुण"}.get(target_language, "📊 ML Text Consistency Score")
            else:
                _auth_title = {"English": "🛡️ Notice Authenticity & Trust Score", "Hindi": "🛡️ नोटिस प्रामाणिकता और विश्वास स्कोर", "Marathi": "🛡️ परिपत्रक सत्यता व विश्वासार्हता गुण"}.get(target_language, "🛡️ Notice Authenticity & Trust Score")

            _findings_title = {"English": "Verification Findings:", "Hindi": "सत्यापन निष्कर्ष:", "Marathi": "पडताळणी निष्कर्ष:"}.get(target_language, "Verification Findings:")
            _check_label = {"English": "Check: <strong>Statutory Pattern & Verification Audit</strong>", "Hindi": "जांच: <strong>वैधानिक प्रारूप और सत्यापन ऑडिट</strong>", "Marathi": "तपासणी: <strong>वैधानिक रचना व सत्यापन ऑडिट</strong>"}.get(target_language, "Check: <strong>Statutory Pattern & Verification Audit</strong>")
            _auth_status_label = {"English": "Official Authenticity", "Hindi": "आधिकारिक प्रामाणिकता", "Marathi": "अधिकृत सत्यता"}.get(target_language, "Official Authenticity")
            _doc_status_title = {"English": "Document Status", "Hindi": "दस्तावेज़ स्थिति", "Marathi": "दस्तऐवज स्थिती"}.get(target_language, "Document Status")

            st.markdown(f"""
            <div style="background: #FFFFFF; border: 1.5px solid {auth_color}45; border-top: 4px solid {auth_color}; border-radius: 12px; padding: 1.1rem; margin-bottom: 1.2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                    <span style="font-weight: 700; font-size: 0.98rem; color: #1E293B;">{_auth_title}</span>
                    <span style="background: {auth_color}18; color: {auth_color}; font-size: 0.75rem; font-weight: 700; padding: 2px 8px; border-radius: 9999px;">{confidence}</span>
                </div>
                <div style="display: flex; align-items: baseline; gap: 0.5rem; margin-bottom: 0.3rem;">
                    <span style="font-size: 1.7rem; font-weight: 800; color: {auth_color};">{auth_score_text}</span>
                    <span style="font-size: 0.92rem; font-weight: 600; color: #334155;">{doc_status}</span>
                </div>
                <div style="font-size: 0.8rem; color: #64748B; margin-bottom: 0.4rem;">
                    {_check_label}
                </div>
                <div style="font-size: 0.8rem; color: #475569; margin-bottom: 0.5rem; background: #F8FAFC; padding: 4px 8px; border-radius: 6px;">
                    <strong>{_auth_status_label}:</strong> {official_auth}
                </div>
                <div style="font-size: 0.85rem; color: #475569;">
                    <strong>{_findings_title}</strong>
                    <ul style="margin: 0.25rem 0 0 1.1rem; padding: 0;">
                        {signals_html}
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with ml_col2:
            urg_score = urg_data.get("urgency_score")
            urg_color = urg_data.get("badge_color", "#F59E0B")
            urg_level = urg_data.get("urgency_level", "Moderate Urgency")
            urg_score_text = f"{urg_score}%" if urg_score is not None else ("अज्ञात" if target_language == "Hindi" else ("अज्ञात" if target_language == "Marathi" else "Unknown / N/A"))
            days_left = urg_data.get("days_left")
            if days_left is not None:
                if target_language == "Hindi":
                    days_label = f"{days_left} दिन शेष"
                elif target_language == "Marathi":
                    days_label = f"{days_left} दिवस शिल्लक"
                else:
                    days_label = f"{days_left} days left"
            else:
                if target_language == "Hindi":
                    days_label = "अनिर्दिष्ट समय सीमा"
                elif target_language == "Marathi":
                    days_label = "अनिर्दिष्ट मुदत"
                else:
                    days_label = "Unspecified Deadline"
            risk_factors_html = "".join(f"<li style='margin-bottom: 2px;'>{rf}</li>" for rf in urg_data.get("risk_factors", []))
            _urg_title = {"English": "⏱️ Filing Urgency & Action Priority", "Hindi": "⏱️ आवेदन की तात्कालिकता और प्राथमिकता", "Marathi": "⏱️ अर्ज करण्याची तातडी व प्राधान्य"}.get(target_language, "⏱️ Filing Urgency & Action Priority")
            _factors_title = {"English": "Filing Timeline & Requirement Burden:", "Hindi": "समय सीमा और आवश्यकता भार:", "Marathi": "मुदत व आवश्यकता भार:"}.get(target_language, "Filing Timeline & Requirement Burden:")
            _risk_drivers_label = {"English": "Risk Drivers:", "Hindi": "जोखिम कारक:", "Marathi": "धोका घटक:"}.get(target_language, "Risk Drivers:")

            st.markdown(f"""
            <div style="background: #FFFFFF; border: 1.5px solid {urg_color}45; border-top: 4px solid {urg_color}; border-radius: 12px; padding: 1.1rem; margin-bottom: 1.2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                    <span style="font-weight: 700; font-size: 0.98rem; color: #1E293B;">{_urg_title}</span>
                    <span style="background: {urg_color}18; color: {urg_color}; font-size: 0.75rem; font-weight: 700; padding: 2px 8px; border-radius: 9999px;">{days_label}</span>
                </div>
                <div style="display: flex; align-items: baseline; gap: 0.5rem; margin-bottom: 0.3rem;">
                    <span style="font-size: 1.7rem; font-weight: 800; color: {urg_color};">{urg_score_text}</span>
                    <span style="font-size: 0.92rem; font-weight: 600; color: #334155;">{urg_level}</span>
                </div>
                <div style="font-size: 0.8rem; color: #64748B; margin-bottom: 0.5rem;">
                    {_factors_title}
                </div>
                <div style="font-size: 0.85rem; color: #475569;">
                    <strong>{_risk_drivers_label}</strong>
                    <ul style="margin: 0.25rem 0 0 1.1rem; padding: 0;">
                        {risk_factors_html}
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # 1. HERO SECTION: WHAT YOU NEED TO DO (Action Checklist)
    action_items = res.get("action_items", [])
    if action_items:
        # Calculate completion rate
        total_actions = len(action_items)
        completed_actions = sum(1 for item in action_items if st.session_state.checklist_state.get(item, False))
        percent_done = int((completed_actions / total_actions) * 100) if total_actions > 0 else 0

        action_plan_title = {"English": "WHAT YOU NEED TO DO (YOUR ACTION PLAN)", "Hindi": "आपको क्या करना है (आपकी कार्य योजना)", "Marathi": "तुम्हाला काय करावे (तुमची कृती योजना)"}.get(target_language, "WHAT YOU NEED TO DO (YOUR ACTION PLAN)")
        progress_subtitle = {"English": "Check off each task as you complete it. Your progress is saved during this session.", "Hindi": "प्रत्येक कार्य को पूरा करने के बाद उसे चेक करें। आपकी प्रगति इस सत्र के दौरान सहेजी जाती है।", "Marathi": "प्रत्येक कार्य पूर्ण केल्यावर त्यावर टिक करा. तुमची प्रगती या सत्रात जतन केली जाते."}.get(target_language, "Check off each task as you complete it. Your progress is saved during this session.")
        st.markdown(f"""
        <div class="hero-action-card">
            <div class="hero-action-title">
                <span>🎯</span> {action_plan_title}
            </div>
            <p style="color: #15803D; font-size: 0.95rem; margin-top: 0.2rem; margin-bottom: 0.8rem;">
                {progress_subtitle}
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.progress(percent_done / 100)
        progress_label = {"English": "Progress", "Hindi": "प्रगति", "Marathi": "प्रगती"}.get(target_language, "Progress")
        of_label = {"English": "of", "Hindi": "में से", "Marathi": "पैकी"}.get(target_language, "of")
        tasks_label = {"English": "tasks completed", "Hindi": "कार्य पूर्ण", "Marathi": "कार्य पूर्ण"}.get(target_language, "tasks completed")
        st.caption(f"**{progress_label}:** {completed_actions} {of_label} {total_actions} {tasks_label} ({percent_done}%)")

        # Checklist Items
        for idx, item in enumerate(action_items):
            # Checkbox with persistent state
            current_checked = st.session_state.checklist_state.get(item, False)
            new_checked = st.checkbox(
                item,
                value=current_checked,
                key=f"check_item_{idx}"
            )
            if new_checked != current_checked:
                st.session_state.checklist_state[item] = new_checked
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. KEY HIGHLIGHTS: DEADLINE & REQUIRED DOCUMENTS
    col_left, col_right = st.columns([1, 2])

    with col_left:
        # IMPORTANT DEADLINE
        deadline_text = res.get("deadline", "Not specified")
        if not deadline_text or deadline_text.strip().lower() in ["not specified", "none", "unknown"]:
            disp_deadline = "Deadline not specified in the document"
            is_urgent = False
        else:
            disp_deadline = deadline_text
            is_urgent = True

        deadline_title = {"English": "Important Deadline", "Hindi": "महत्वपूर्ण अंतिम तिथि", "Marathi": "महत्त्वाची अंतिम मुदत"}.get(target_language, "Important Deadline")
        st.markdown(f"""
        <div class="deadline-card">
            <div class="deadline-title">⏰ {deadline_title}</div>
            <div class="deadline-value" style="font-size: {'1.4rem' if not is_urgent else '1.75rem'};">
                {disp_deadline}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # DOCUMENT OVERVIEW
        with st.container():
            st.markdown("""<div class="info-card">""", unsafe_allow_html=True)
            doc_overview_title = {"English": "Document Overview", "Hindi": "दस्तावेज़ अवलोकन", "Marathi": "दस्तऐवज अवलोकन"}.get(target_language, "Document Overview")
            title_label = {"English": "Title", "Hindi": "शीर्षक", "Marathi": "शीर्षक"}.get(target_language, "Title")
            type_label = {"English": "Type", "Hindi": "प्रकार", "Marathi": "प्रकार"}.get(target_language, "Type")
            summary_label = {"English": "Summary", "Hindi": "सारांश", "Marathi": "सारांश"}.get(target_language, "Summary")
            st.markdown(f"#### 📄 {doc_overview_title}")
            st.markdown(f"**{title_label}:** {res.get('document_title', 'Not specified')}")
            st.markdown(f"**{type_label}:** `{res.get('document_type', 'Official Document')}`")
            st.markdown(f"**{summary_label}:** {res.get('summary', 'No summary available.')}")
            st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        # REQUIRED DOCUMENTS
        req_docs = res.get("required_documents", [])
        with st.container():
            st.markdown("""<div class="info-card">""", unsafe_allow_html=True)
            req_docs_title = {"English": "Required Documents to Submit", "Hindi": "जमा करने के लिए आवश्यक दस्तावेज़", "Marathi": "सादर करण्यासाठी आवश्यक कागदपत्रे"}.get(target_language, "Required Documents to Submit")
            st.markdown(f"#### 📑 {req_docs_title}")
            if req_docs:
                for doc_item in req_docs:
                    st.markdown(f"- 🗂️ **{doc_item}**")
            else:
                no_docs_msg = {"English": "No specific supporting documents are required according to this document.", "Hindi": "इस दस्तावेज़ के अनुसार कोई विशिष्ट सहायक दस्तावेज़ आवश्यक नहीं हैं।", "Marathi": "या दस्तऐवजानुसार कोणतीही विशिष्ट सहायक कागदपत्रे आवश्यक नाहीत."}.get(target_language, "No specific supporting documents are required according to this document.")
                st.info(no_docs_msg)
            st.markdown("</div>", unsafe_allow_html=True)

    # 3. CONFUSING FIELDS EXPLAINED
    important_fields = res.get("important_fields", [])
    if important_fields:
        fields_title = {"English": "Confusing Fields & Requirements Explained", "Hindi": "कठिन फ़ील्ड और आवश्यकताओं की व्याख्या", "Marathi": "किचकट रकाने व आवश्यकतांचे स्पष्टीकरण"}.get(target_language, "Confusing Fields & Requirements Explained")
        fields_subtitle = {"English": "We translate complex institutional jargon into simple explanations and show the exact certificate needed.", "Hindi": "हम जटिल संस्थागत शब्दावली को सरल स्पष्टीकरण में बदलते हैं और आवश्यक प्रमाणपत्र दिखाते हैं।", "Marathi": "आपण जटिल संस्थात्मक शब्दावलीचे सोपे स्पष्टीकरण करतो आणि आवश्यक प्रमाणपत्र दाखवतो."}.get(target_language, "We translate complex institutional jargon into simple explanations and show the exact certificate needed.")
        st.markdown(f"### 💡 {fields_title}")
        st.caption(fields_subtitle)

        for f_idx, field_info in enumerate(important_fields):
            fname = field_info.get("field", "Field")
            fexp = field_info.get("explanation", "No explanation available.")
            fdoc = field_info.get("required_document", "None specified")

            supporting_doc_label = {"English": "Supporting Document", "Hindi": "सहायक दस्तावेज़", "Marathi": "सहायक कागदपत्र"}.get(target_language, "Supporting Document")
            doc_badge = f"<span class='field-doc'>📎 {supporting_doc_label}: {fdoc}</span>" if fdoc and fdoc.lower() not in ["none specified", "none", "not specified"] else ""
            what_it_means = {"English": "What it means", "Hindi": "इसका मतलब", "Marathi": "याचा अर्थ"}.get(target_language, "What it means")

            st.markdown(f"""
            <div class="field-card">
                <div class="field-name">{fname}</div>
                <div class="field-desc"><b>{what_it_means}:</b> {fexp}</div>
                {doc_badge}
            </div>
            """, unsafe_allow_html=True)

    # 4. WARNINGS & PENALTIES
    warnings = res.get("warnings", [])
    if warnings and any(w.strip() for w in warnings):
        warnings_title = {"English": "Important Warnings & Restrictions", "Hindi": "महत्वपूर्ण चेतावनियां और प्रतिबंध", "Marathi": "महत्त्वाच्या सूचना आणि निर्बंध"}.get(target_language, "Important Warnings & Restrictions")
        st.markdown(f"### ⚠️ {warnings_title}")
        for warn in warnings:
            if warn.strip():
                warning_label = {"English": "Warning", "Hindi": "चेतावनी", "Marathi": "चेतावणी"}.get(target_language, "Warning")
                st.markdown(f"""
                <div class="warning-box">
                    <b>{warning_label}:</b> {warn}
                </div>
                """, unsafe_allow_html=True)

    # ==========================================
    # ASK FORMFIX AI (Grounded Chat Interface)
    # ==========================================
    st.markdown("---")
    chat_title = {"English": "Ask FormFix AI About This Document", "Hindi": "इस दस्तावेज़ के बारे में FormFix AI से पूछें", "Marathi": "या दस्तऐवजाबद्दल FormFix AI कडून विचारा"}.get(target_language, "Ask FormFix AI About This Document")
    chat_subtitle = {"English": "Ask questions strictly based on the uploaded document. The AI will never invent facts outside the text.", "Hindi": "केवल अपलोड किए गए दस्तावेज़ के आधार पर प्रश्न पूछें। AI कभी भी पाठ के बाहर तथ्य नहीं बनाएगा।", "Marathi": "फक्त अपलोड केलेल्या दस्तऐवजाच्या आधारावर प्रश्न विचारा. AI कधीही मजकुराबाहेर तथ्ये तयार करणार नाही."}.get(target_language, "Ask questions strictly based on the uploaded document. The AI will never invent facts outside the text.")
    st.markdown(f"### 💬 {chat_title}")
    st.caption(chat_subtitle)

    # Suggested Questions Chips
    suggested_q_label = {"English": "Suggested Questions", "Hindi": "सुझाए गए प्रश्न", "Marathi": "सुचवलेले प्रश्न"}.get(target_language, "Suggested Questions")
    st.markdown(f"**{suggested_q_label}:**")
    chip_col1, chip_col2, chip_col3, chip_col4, chip_col5 = st.columns(5)

    prompt_to_send = None

    q_deadline = {"English": "What is the deadline?", "Hindi": "डेडलाइन क्या है?", "Marathi": "अंतिम मुदत काय आहे?"}.get(target_language, "What is the deadline?")
    q_docs = {"English": "Which documents do I need?", "Hindi": "मुझे कौन से दस्तावेज़ चाहिए?", "Marathi": "मला कोणती कागदपत्रे हवी?"}.get(target_language, "Which documents do I need?")
    q_income = {"English": "Do I need income certificate?", "Hindi": "क्या मुझे आय प्रमाणपत्र चाहिए?", "Marathi": "मला उत्पन्न प्रमाणपत्र हवे का?"}.get(target_language, "Do I need income certificate?")
    q_first = {"English": "What should I do first?", "Hindi": "मुझे सबसे पहले क्या करना चाहिए?", "Marathi": "मला सर्वप्रथम काय करावे?"}.get(target_language, "What should I do first?")
    q_simple = {"English": "Explain in simple words", "Hindi": "सरल शब्दों में समझाएं", "Marathi": " Simple शब्दांत स्पष्ट करा"}.get(target_language, "Explain in simple words")
    with chip_col1:
        if st.button(f"⏰ {q_deadline}", key="chip_deadline", use_container_width=True):
            prompt_to_send = q_deadline
    with chip_col2:
        if st.button(f"📑 {q_docs}", key="chip_docs", use_container_width=True):
            prompt_to_send = q_docs
    with chip_col3:
        if st.button(f"💰 {q_income}", key="chip_income", use_container_width=True):
            prompt_to_send = q_income
    with chip_col4:
        if st.button(f"🏁 {q_first}", key="chip_first", use_container_width=True):
            prompt_to_send = q_first
    with chip_col5:
        if st.button(f"📝 {q_simple}", key="chip_simple", use_container_width=True):
            prompt_to_send = q_simple

    # Display Chat History
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    chat_placeholder = {"English": "Ask any question about your uploaded document...", "Hindi": "अपलोड किए गए दस्तावेज़ के बारे में कोई भी प्रश्न पूछें...", "Marathi": "अपलोड केलेल्या दस्तऐवजाबद्दल कोणताही प्रश्न विचारा..."}.get(target_language, "Ask any question about your uploaded document...")
    user_query = st.chat_input(chat_placeholder)

    if user_query:
        prompt_to_send = user_query

    if prompt_to_send:
        # Add user message to history
        st.session_state.chat_messages.append({"role": "user", "content": prompt_to_send})
        with st.chat_message("user"):
            st.markdown(prompt_to_send)

        # Generate Grounded Answer
        with st.chat_message("assistant"):
            with st.spinner("Searching document for answer..."):
                doc_text = st.session_state.document_text or ""
                active_api_key = get_groq_api_key()

                if not active_api_key:
                    reply = "AI service is not configured. Please ensure GROQ_API_KEY is in your .env file."
                else:
                    try:
                        reply = ask_document_ai(
                            document_text=doc_text,
                            question=prompt_to_send,
                            chat_history=st.session_state.chat_messages,
                            target_language=st.session_state.get("target_language", "English"),
                            api_key=active_api_key
                        )
                    except TypeError:
                        reply = ask_document_ai(
                            document_text=doc_text,
                            question=prompt_to_send,
                            chat_history=st.session_state.chat_messages,
                            api_key=active_api_key
                        )

                st.markdown(reply)
                st.session_state.chat_messages.append({"role": "assistant", "content": reply})
