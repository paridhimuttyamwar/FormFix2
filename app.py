import os
import sys
import streamlit as st
from dotenv import load_dotenv

import importlib

# Ensure local services can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import services.ai_service as ai_service_module
    importlib.reload(ai_service_module)
    from services.document_processor import extract_document_text
    from services.ai_service import analyze_document_with_ai, ask_document_ai, get_groq_api_key
    from services.ml_service import assess_document_ml
except ImportError:
    import ai_service as ai_service_module
    importlib.reload(ai_service_module)
    from document_processor import extract_document_text
    from ai_service import analyze_document_with_ai, ask_document_ai, get_groq_api_key
    from ml_service import assess_document_ml

load_dotenv()

# --- Multilingual UI Dictionary ---
UI_STRINGS = {
    "English": {
        "title": "📋 FormFix AI",
        "caption": "Turn complex official notices into clear action plans and trust audits.",
        "lang_label": "🌐 Language",
        "upload_label": "Upload notice or form (PDF, PNG, JPG)",
        "btn_analyze": "🚀 Analyze Document",
        "spinner": "Analyzing document structure, verification signals, and action plan...",
        "btn_upload_new": "🔄 Upload New",
        "doc_type": "Document Type",
        "sec_audit": "🛡️ Document Trust & Urgency Assessment",
        "metric_auth": "🛡️ Notice Authenticity & Trust Score",
        "metric_urg": "⏱️ Filing Urgency & Action Priority",
        "status_label": "Verification Status",
        "timeline_label": "Filing Timeline",
        "expander_findings": "🔍 View Official Pattern Findings",
        "expander_factors": "🔍 View Timeline & Effort Factors",
        "tab_actions": "🎯 What You Need To Do (Action Plan)",
        "tab_warnings": "⚠️ Important Warnings & Restrictions",
        "no_actions": "No specific action items listed in this document.",
        "no_warnings": "✅ No critical risk or fraud warnings detected.",
        "sec_alerts": "🚨 Critical Security & Red Flag Alerts",
        "alert_prefix": "Security Alert:",
        "sec_deadline": "⏰ Important Deadline",
        "sec_docs": "📑 Required Documents",
        "no_docs": "No specific documents required.",
        "sec_fields": "🔍 Confusing Fields Explained",
        "proof_req": "Required Proof",
        "sec_chat": "💬 Ask Questions About This Document",
        "chat_placeholder": "Ask a question about this notice...",
        "chat_spinner": "Finding answer in document..."
    },
    "Hindi": {
        "title": "📋 फॉर्मफिक्स एआई (FormFix AI)",
        "caption": "कठिन सरकारी व शैक्षणिक परिपत्रों को सरल कार्य योजना और सुरक्षा ऑडिट में बदलें।",
        "lang_label": "🌐 भाषा / Language",
        "upload_label": "नोटिस या फॉर्म अपलोड करें (PDF, PNG, JPG)",
        "btn_analyze": "🚀 दस्तावेज़ का विश्लेषण करें",
        "spinner": "दस्तावेज़ की प्रामाणिकता, सुरक्षा संकेतों और कार्य योजना का विश्लेषण किया जा रहा है...",
        "btn_upload_new": "🔄 नया दस्तावेज़ अपलोड करें",
        "doc_type": "दस्तावेज़ का प्रकार",
        "sec_audit": "🛡️ दस्तावेज़ विश्वसनीयता और तात्कालिकता मूल्यांकन",
        "metric_auth": "🛡️ नोटिस प्रामाणिकता और विश्वास स्कोर",
        "metric_urg": "⏱️ आवेदन की तात्कालिकता और प्राथमिकता",
        "status_label": "सत्यापन स्थिति",
        "timeline_label": "आवेदन की समय सीमा",
        "expander_findings": "🔍 आधिकारिक प्रारूप निष्कर्ष देखें",
        "expander_factors": "🔍 समय सीमा और जटिलता कारक देखें",
        "tab_actions": "🎯 आपको क्या करना है (कार्य योजना)",
        "tab_warnings": "⚠️ महत्वपूर्ण सावधानियां और प्रतिबंध",
        "no_actions": "इस दस्तावेज़ में कोई विशिष्ट कार्य सूचीबद्ध नहीं हैं।",
        "no_warnings": "✅ कोई गंभीर जोखिम या धोखाधड़ी की चेतावनी नहीं मिली।",
        "sec_alerts": "🚨 सुरक्षा चेतावनी और रेड फ्लैग्स",
        "alert_prefix": "सुरक्षा अलर्ट:",
        "sec_deadline": "⏰ महत्वपूर्ण अंतिम तिथि (डेडलाइन)",
        "sec_docs": "📑 आवश्यक दस्तावेज़",
        "no_docs": "किसी विशिष्ट दस्तावेज़ की आवश्यकता नहीं है।",
        "sec_fields": "🔍 कठिन शब्दों और फ़ील्ड्स की व्याख्या",
        "proof_req": "आवश्यक प्रमाण",
        "sec_chat": "💬 इस दस्तावेज़ के बारे में प्रश्न पूछें",
        "chat_placeholder": "इस नोटिस के बारे में अपना प्रश्न पूछें...",
        "chat_spinner": "दस्तावेज़ में उत्तर खोजा जा रहा है..."
    },
    "Marathi": {
        "title": "📋 फॉर्मफिक्स एआय (FormFix AI)",
        "caption": "गुंतागुंतीच्या अधिकृत परिपत्रकांचे सोप्या कृती आराखड्यात आणि सुरक्षितता तपासणीत रूपांतर करा.",
        "lang_label": "🌐 भाषा / Language",
        "upload_label": "परिपत्रक किंवा अर्ज अपलोड करा (PDF, PNG, JPG)",
        "btn_analyze": "🚀 दस्तऐवजाचे विश्लेषण करा",
        "spinner": "दस्तऐवजाची सत्यता, सुरक्षा संकेत आणि कृती आराखड्याचे विश्लेषण सुरू आहे...",
        "btn_upload_new": "🔄 नवीन परिपत्रक अपलोड करा",
        "doc_type": "दस्तऐवजाचा प्रकार",
        "sec_audit": "🛡️ दस्तऐवज सत्यता व तातडीचे मूल्यांकन",
        "metric_auth": "🛡️ परिपत्रक सत्यता व विश्वासार्हता गुण",
        "metric_urg": "⏱️ अर्ज करण्याची तातडी व प्राधान्य",
        "status_label": "पडताळणी स्थिती",
        "timeline_label": "अंतिम मुदत कालावधी",
        "expander_findings": "🔍 अधिकृत रचना व तपासणी निष्कर्ष पहा",
        "expander_factors": "🔍 मुदत व श्रम घटक पहा",
        "tab_actions": "🎯 तुम्हाला काय करावे लागेल (कृती योजना)",
        "tab_warnings": "⚠️ महत्त्वाच्या सूचना आणि निर्बंध",
        "no_actions": "या दस्तऐवजात कोणतीही विशिष्ट कृती नमूद केलेली नाही.",
        "no_warnings": "✅ कोणताही गंभीर धोका किंवा फसवणुकीची चेतावणी आढळली नाही.",
        "sec_alerts": "🚨 महत्त्वाचे सुरक्षा धोके आणि इशारे",
        "alert_prefix": "सुरक्षा इशारा:",
        "sec_deadline": "⏰ महत्त्वाची अंतिम मुदत",
        "sec_docs": "📑 आवश्यक कागदपत्रे",
        "no_docs": "कोणत्याही विशिष्ट कागदपत्रांची आवश्यकता नाही.",
        "sec_fields": "🔍 किचकट रकाने व अटींचे स्पष्टीकरण",
        "proof_req": "आवश्यक पुरावा",
        "sec_chat": "💬 या परिपत्रकाबद्दल प्रश्न विचारा",
        "chat_placeholder": "या परिपत्रकाबद्दल प्रश्न विचारा...",
        "chat_spinner": "दस्तऐवजात उत्तर शोधत आहे..."
    }
}

# --- Page Setup ---
st.set_page_config(page_title="FormFix AI (Multilingual)", page_icon="📋", layout="wide")

# Top Header with Language Selector
header_col, lang_col = st.columns([3, 1])

with lang_col:
    lang_display = st.selectbox(
        "🌐 Language / भाषा",
        ["English", "हिन्दी (Hindi)", "मराठी (Marathi)"],
        index=0
    )

LANG_MAP = {
    "English": "English",
    "हिन्दी (Hindi)": "Hindi",
    "मराठी (Marathi)": "Marathi"
}
target_language = LANG_MAP[lang_display]
ui = UI_STRINGS[target_language]

with header_col:
    st.title(ui["title"])
    st.caption(ui["caption"])

# --- Session State Management ---
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "doc_text" not in st.session_state:
    st.session_state.doc_text = None
if "ml_eval" not in st.session_state:
    st.session_state.ml_eval = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_lang" not in st.session_state:
    st.session_state.current_lang = target_language

# --- Upload Section ---
if not st.session_state.analysis:
    uploaded_file = st.file_uploader(
        ui["upload_label"],
        type=["pdf", "png", "jpg", "jpeg"]
    )

    if uploaded_file and st.button(ui["btn_analyze"], type="primary", use_container_width=True):
        api_key = get_groq_api_key()
        if not api_key:
            st.error("Please configure GROQ_API_KEY in your .env or Streamlit Secrets.")
            st.stop()

        with st.spinner(ui["spinner"]):
            # Step 1: Extract Text
            text = extract_document_text(uploaded_file.name, uploaded_file.getvalue())
            st.session_state.doc_text = text

            # Step 2: Generative AI Analysis with Target Language
            try:
                ai_data = analyze_document_with_ai(
                    document_text=text,
                    target_language=target_language,
                    api_key=api_key
                )
            except TypeError:
                ai_data = analyze_document_with_ai(
                    document_text=text,
                    api_key=api_key
                )
            st.session_state.analysis = ai_data
            st.session_state.current_lang = target_language

            # Step 3: Machine Learning Evaluation
            ml_data = assess_document_ml(text, ai_data, target_language=target_language)
            st.session_state.ml_eval = ml_data

            # Step 4: Ready to display
            st.session_state.chat_history = []
            st.rerun()

# --- Results Dashboard ---
else:
    res = st.session_state.analysis
    ml = st.session_state.ml_eval

    # --- Language-Change Detection: Re-run AI analysis if language switched ---
    if st.session_state.get("current_lang") != target_language and st.session_state.get("doc_text"):
        with st.spinner(ui["spinner"]):
            try:
                new_ai_data = analyze_document_with_ai(
                    document_text=st.session_state.doc_text,
                    target_language=target_language,
                    api_key=get_groq_api_key()
                )
            except TypeError:
                new_ai_data = analyze_document_with_ai(
                    document_text=st.session_state.doc_text,
                    api_key=get_groq_api_key()
                )
            st.session_state.analysis = new_ai_data
            # Also re-run ML with new language so signals/verdicts translate too
            st.session_state.ml_eval = assess_document_ml(
                st.session_state.doc_text,
                new_ai_data,
                target_language=target_language
            )
            st.session_state.current_lang = target_language
            st.session_state.chat_history = []   # Reset chat — language changed
            st.rerun()

    # Header & Reset Button
    col_head, col_btn = st.columns([4, 1])
    with col_head:
        st.subheader(f"📄 {res.get('document_title', 'Document Analysis')}")
        st.caption(f"**{ui['doc_type']}:** {res.get('document_type', 'Official Notice')}")
    with col_btn:
        if st.button(ui["btn_upload_new"], use_container_width=True):
            st.session_state.analysis = None
            st.session_state.doc_text = None
            st.session_state.ml_eval = None
            st.session_state.chat_history = []
            st.rerun()

    st.divider()

    # --- 1. Trust & Urgency Assessment ---
    st.markdown(f"### {ui['sec_audit']}")
    eval_col1, eval_col2 = st.columns(2)

    with eval_col1:
        auth = ml.get("authenticity", {})
        _auth_score = auth.get("authenticity_score")
        if _auth_score is not None:
            _auth_val_str = f"{_auth_score}%"
        else:
            _auth_val_str = "अनुपलब्ध" if target_language == "Hindi" else ("अनुपलब्ध" if target_language == "Marathi" else "N/A (Unverified)")

        st.metric(
            label=ui["metric_auth"],
            value=_auth_val_str,
            delta=auth.get("verdict", "Unknown")
        )
        st.caption(f"**{ui['status_label']}:** {auth.get('confidence', 'Normal')}")
        with st.expander(ui["expander_findings"]):
            for sig in auth.get("signals", []):
                st.write(f"- {sig}")
            if auth.get("rule_warnings"):
                st.markdown("---")
                st.markdown("**⚠️ " + ("सुरक्षा चेतावनियां:" if target_language == "Hindi" else ("सुरक्षा सूचना:" if target_language == "Marathi" else "Security Advisories:")) + "**")
                for rw in auth.get("rule_warnings", []):
                    st.write(f"- {rw}")

    with eval_col2:
        urg = ml.get("urgency", {})
        _urg_score = urg.get("urgency_score")
        if _urg_score is not None:
            _urg_val_str = f"{_urg_score}%"
        else:
            _urg_val_str = "अज्ञात" if target_language == "Hindi" else ("अज्ञात" if target_language == "Marathi" else "Unknown / N/A")

        _days_left = urg.get("days_left")
        if _days_left is not None:
            if target_language == "Hindi":
                days_str = f"{_days_left} दिन"
            elif target_language == "Marathi":
                days_str = f"{_days_left} दिवस"
            else:
                days_str = f"{_days_left} days"
        else:
            if target_language == "Hindi":
                days_str = "अनिर्दिष्ट समय सीमा (मूल नोटिस जांचें)"
            elif target_language == "Marathi":
                days_str = "अनिर्दिष्ट मुदत (मूळ कागदपत्र तपासा)"
            else:
                days_str = "Unspecified (Manual Check Required)"

        st.metric(
            label=ui["metric_urg"],
            value=_urg_val_str,
            delta=urg.get("urgency_level", "Moderate")
        )
        st.caption(f"**{ui['timeline_label']}:** {days_str}")
        if urg.get("explanation"):
            st.caption(f"ℹ️ {urg.get('explanation')}")
        with st.expander(ui["expander_factors"]):
            for rf in urg.get("risk_factors", []):
                st.write(f"- {rf}")

    st.divider()

    # --- 2. Action Plan & Warnings Tabs ---
    tab_actions, tab_warnings = st.tabs([
        ui["tab_actions"],
        ui["tab_warnings"]
    ])

    with tab_actions:
        items = res.get("action_items", [])
        if items:
            for idx, item in enumerate(items, 1):
                st.write(f"**{idx}.** {item}")
        else:
            st.info(ui["no_actions"])

    with tab_warnings:
        # Protective Risk & Safety Advisories
        warnings = res.get("warnings", [])
        if warnings and any(isinstance(w, str) and w.strip() for w in warnings):
            for warn in warnings:
                if isinstance(warn, str) and warn.strip():
                    st.warning(f"⚠️ {warn}")
        else:
            st.success(ui["no_warnings"])

        # Critical Security & Red Flag Alerts
        if ml:
            fraud_signals = [s for s in ml.get("authenticity", {}).get("signals", []) if "⚠️" in s or "🚨" in s]
            if fraud_signals:
                st.markdown(f"##### {ui['sec_alerts']}")
                for fs in fraud_signals:
                    clean_fs = fs.replace("⚠️", "").replace("🚨", "").strip()
                    st.error(f"**{ui['alert_prefix']}** {clean_fs}")

    st.divider()

    # --- 3. Deadlines & Required Documents ---
    col_dline, col_docs = st.columns([1, 2])
    with col_dline:
        st.markdown(f"### {ui['sec_deadline']}")
        deadline = res.get("deadline", "Not specified")
        st.info(f"### {deadline}")

    with col_docs:
        st.markdown(f"### {ui['sec_docs']}")
        docs = res.get("required_documents", [])
        if docs:
            for d in docs:
                st.write(f"📁 **{d}**")
        else:
            st.write(ui["no_docs"])

    st.divider()

    # --- 4. Confusing Fields Explained ---
    fields = res.get("important_fields", [])
    if fields:
        st.markdown(f"### {ui['sec_fields']}")
        for f in fields:
            with st.expander(f"📌 {f.get('field', 'Field')}"):
                st.write(f.get("explanation", ""))
                if f.get("required_document"):
                    st.caption(f"{ui['proof_req']}: **{f.get('required_document')}**")

    st.divider()

    # --- 5. Ask FormFix AI (Grounded Q&A Chat in Selected Language) ---
    st.markdown(f"### {ui['sec_chat']}")

    # Display past chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Chat input box
    query = st.chat_input(ui["chat_placeholder"])
    if query:
        st.session_state.chat_history.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.write(query)

        with st.chat_message("assistant"):
            with st.spinner(ui["chat_spinner"]):
                try:
                    ans = ask_document_ai(
                        document_text=st.session_state.doc_text,
                        question=query,
                        chat_history=st.session_state.chat_history,
                        target_language=target_language,
                        api_key=get_groq_api_key()
                    )
                except TypeError:
                    ans = ask_document_ai(
                        document_text=st.session_state.doc_text,
                        question=query,
                        chat_history=st.session_state.chat_history,
                        api_key=get_groq_api_key()
                    )
                st.write(ans)
                st.session_state.chat_history.append({"role": "assistant", "content": ans})
