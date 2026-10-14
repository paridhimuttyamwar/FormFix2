"""
FormFix AI — Dual Machine Learning Engine
1. Authenticity Classifier (TF-IDF + Logistic Regression with Contextual Rule-Based Auditing)
2. Tabular Urgency & Risk Engine (Engineered Administrative Risk Features + Logistic Regression)

Phase 3 & Phase 4 Upgrades:
- Pre-trained model loading from models/authenticity_pipeline.joblib
- Decoupled ML probability from rule-based warnings (no arbitrary 28%/72% overrides)
- Contextual regex matching to distinguish scam demands from protective warnings
- Short-document fallback returns None / Unverified instead of fabricated 85%
- Removal of 14-day fabricated deadline fallback (returns None / Unknown urgency)
- Expired deadline detection
- Full multilingual localization (English, Hindi, Marathi)
"""

import os
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_FILE_PATH = PROJECT_ROOT / "models" / "authenticity_pipeline.joblib"


# ==============================================================================
# MULTILINGUAL TRANSLATION TABLE FOR ALL ML OUTPUT STRINGS
# ==============================================================================

_ML_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # ── Authenticity signals ─────────────────────────────────────────────────
    "Official reference/dispatch number format detected": {
        "Hindi":   "आधिकारिक संदर्भ/डिस्पैच नंबर प्रारूप पाया गया",
        "Marathi": "अधिकृत संदर्भ/डिस्पॅच क्रमांक स्वरूप आढळले"
    },
    "Standard administrative designation detected": {
        "Hindi":   "मानक प्रशासनिक पदनाम पाया गया",
        "Marathi": "मानक प्रशासकीय पदनाम आढळले"
    },
    "Formal statutory vocabulary match": {
        "Hindi":   "औपचारिक कानूनी शब्दावली का मिलान हुआ",
        "Marathi": "औपचारिक वैधानिक शब्दसंग्रह जुळला"
    },
    "Official government/academic domain references present": {
        "Hindi":   "आधिकारिक सरकारी/शैक्षणिक डोमेन संदर्भ मौजूद हैं",
        "Marathi": "अधिकृत शासकीय/शैक्षणिक डोमेन संदर्भ आढळले"
    },
    "Standard administrative communication patterns analyzed": {
        "Hindi":   "मानक प्रशासनिक संचार पैटर्न का विश्लेषण किया गया",
        "Marathi": "मानक प्रशासकीय संवाद नमुन्यांचे विश्लेषण केले"
    },
    "Document contains insufficient text for statistical evaluation.": {
        "Hindi":   "दस्तावेज़ में सांख्यिकीय मूल्यांकन के लिए अपर्याप्त पाठ है।",
        "Marathi": "दस्तऐवजात सांख्यिकी मूल्यांकनासाठी अपुरा मजकूर आहे."
    },
    # ── Fraud signals & Contextual Warnings ──────────────────────────────────
    "⚠️ Payment solicitation (UPI/Wallet/Direct Fee) detected": {
        "Hindi":   "⚠️ UPI/वॉलेट/डायरेक्ट शुल्क मांग पाई गई — यह संदिग्ध है",
        "Marathi": "⚠️ UPI/वॉलेट/डायरेक्ट शुल्क मागणी आढळली — हे संशयास्पद आहे"
    },
    "⚠️ Informal social channel redirection (Telegram/WhatsApp)": {
        "Hindi":   "⚠️ अनौपचारिक सोशल चैनल (Telegram/WhatsApp) पर भेजने की कोशिश",
        "Marathi": "⚠️ अनौपचारिक सामाजिक वाहिनी (Telegram/WhatsApp) वर वळवण्याचा प्रयत्न"
    },
    "⚠️ Unrealistic promise or scam trigger phrasing identified": {
        "Hindi":   "⚠️ अवास्तविक वादा या धोखाधड़ी को बढ़ावा देने वाली भाषा पहचानी गई",
        "Marathi": "⚠️ अवास्तव वचन किंवा फसवणूक प्रवृत्त करणारी भाषा ओळखली"
    },
    "🚨 High-risk credential harvesting pattern detected": {
        "Hindi":   "🚨 उच्च जोखिम — बैंकिंग/व्यक्तिगत जानकारी चुराने का पैटर्न पाया गया",
        "Marathi": "🚨 उच्च धोका — बँकिंग/वैयक्तिक माहिती चोरण्याचा नमुना आढळला"
    },
    # ── Verdict labels ───────────────────────────────────────────────────────
    "High Administrative Consistency": {
        "Hindi": "उच्च प्रशासनिक प्रारूप संगति",
        "Marathi": "उच्च प्रशासकीय रचना सुसंगतता"
    },
    "Likely Standard Administrative Format": {
        "Hindi": "संभवतः मानक प्रशासनिक प्रारूप",
        "Marathi": "बहुधा मानक प्रशासकीय रचना"
    },
    "Administrative Format with Security Warnings": {
        "Hindi": "प्रशासनिक प्रारूप (सुरक्षा चेतावनियों सहित)",
        "Marathi": "प्रशासकीय रचना (सुरक्षा सूचनांसह)"
    },
    "Suspicious / Potential Scam Notice": {
        "Hindi": "संदिग्ध / संभावित धोखाधड़ी नोटिस",
        "Marathi": "संशयास्पद / संभाव्य फसवणूक नोटीस"
    },
    "Unverified / Irregular Notice": {
        "Hindi": "असत्यापित / अनियमित नोटिस",
        "Marathi": "असत्यापित / अनियमित नोटीस"
    },
    "Unverified (Document text too short for statistical evaluation)": {
        "Hindi":   "असत्यापित (दस्तावेज़ का पाठ सांख्यिकीय मूल्यांकन के लिए बहुत छोटा है)",
        "Marathi": "अपडताळलेले (दस्तऐवजातील मजकूर सांख्यिकी मूल्यांकनासाठी खूप कमी आहे)"
    },
    "Fictional / Mock Notice": {
        "Hindi": "काल्पनिक / मॉक नोटिस",
        "Marathi": "काल्पनिक / नमुना नोटीस"
    },
    "Official authenticity not established (Demonstration / Mock Notice)": {
        "Hindi": "आधिकारिक प्रामाणिकता स्थापित नहीं (काल्पनिक / परीक्षण दस्तावेज़)",
        "Marathi": "अधिकृत सत्यता प्रस्थापित नाही (काल्पनिक / नमुना दस्तऐवज)"
    },
    "Official authenticity not independently verified": {
        "Hindi": "आधिकारिक प्रामाणिकता स्वतंत्र रूप से सत्यापित नहीं है",
        "Marathi": "अधिकृत सत्यता स्वतंत्रपणे पडताळलेली नाही"
    },
    "Explicit fictional or mock disclaimer detected in document.": {
        "Hindi": "दस्तावेज़ में स्पष्ट रूप से काल्पनिक या मॉक नोटिस अस्वीकरण पाया गया।",
        "Marathi": "दस्तऐवजात स्पष्ट काल्पनिक किंवा नमुना नोटीस अस्वीकरण आढळले."
    },
    # ── Confidence labels ────────────────────────────────────────────────────
    "High Confidence": {
        "Hindi": "उच्च विश्वास", "Marathi": "उच्च विश्वासार्हता"
    },
    "Moderate Confidence": {
        "Hindi": "मध्यम विश्वास", "Marathi": "मध्यम विश्वासार्हता"
    },
    "High Suspicion": {
        "Hindi": "अत्यधिक संदिग्ध", "Marathi": "अत्यंत संशयास्पद"
    },
    "Review Advised": {
        "Hindi": "समीक्षा की सिफारिश की जाती है", "Marathi": "पुनरावलोकन करण्याचा सल्ला"
    },
    "Low": {
        "Hindi": "कम", "Marathi": "कमी"
    },
    "Unavailable": {
        "Hindi": "अनुपलब्ध", "Marathi": "अनुपलब्ध"
    },
    # ── Urgency level labels ─────────────────────────────────────────────────
    "Critical Urgency (Immediate Action)": {
        "Hindi": "अत्यावश्यक (तुरंत कार्रवाई करें)", "Marathi": "अत्यंत तातडीचे (त्वरित कारवाई करा)"
    },
    "Moderate Urgency": {
        "Hindi": "मध्यम तात्कालिकता", "Marathi": "मध्यम तातडी"
    },
    "Routine / Low Urgency": {
        "Hindi": "सामान्य / कम तात्कालिकता", "Marathi": "सामान्य / कमी तातडी"
    },
    "Unknown / Unspecified Deadline": {
        "Hindi": "अज्ञात / अनिर्दिष्ट समय सीमा",
        "Marathi": "अज्ञात / अनिर्दिष्ट मुदत"
    },
    "Deadline Expired": {
        "Hindi": "समय सीमा समाप्त",
        "Marathi": "मुदत संपली"
    },
    # ── Risk factor messages ─────────────────────────────────────────────────
    "No explicit deadline found in notice; verification required from original source": {
        "Hindi":   "नोटिस में कोई स्पष्ट समय सीमा नहीं मिली; मूल स्रोत से सत्यापन आवश्यक है",
        "Marathi": "परिपत्रकात स्पष्ट मुदत आढळली नाही; मूळ स्रोतातून पडताळणी आवश्यक आहे"
    },
    "No valid deadline could be identified in the notice. Please verify the filing date manually from the original document.": {
        "Hindi":   "नोटिस में कोई वैध समय सीमा नहीं मिली। कृपया मूल दस्तावेज़ से अंतिम तिथि स्वयं जांचें।",
        "Marathi": "परिपत्रकात वैध मुदत आढळली नाही. कृपया मूळ कागदपत्रातून अंतिम तारीख तपासा."
    },
    "Deadline has already passed. Immediate inquiry recommended.": {
        "Hindi":   "समय सीमा पहले ही समाप्त हो चुकी है। तत्काल पूछताछ की सिफारिश की जाती है।",
        "Marathi": "मुदत आधीच संपलेली आहे. त्वरित चौकशी करण्याचा सल्ला दिला जातो."
    },
    "Strict disqualification or penalty clause detected": {
        "Hindi":   "सख्त अयोग्यता या जुर्माना खंड पाया गया",
        "Marathi": "कडक अपात्रता किंवा दंड कलम आढळले"
    },
    "Physical compliance barrier (Speed post, physical visit, or notary stamp required)": {
        "Hindi":   "भौतिक अनुपालन बाधा (स्पीड पोस्ट, व्यक्तिगत उपस्थिति, या नोटरी स्टाम्प आवश्यक)",
        "Marathi": "भौतिक अनुपालन अडथळा (स्पीड पोस्ट, प्रत्यक्ष भेट, किंवा नोटरी शिक्का आवश्यक)"
    },
}


def _t(text: str, lang: str) -> str:
    """Translate an ML output string to the target language. Falls back to English."""
    if lang == "English":
        return text
    table = _ML_TRANSLATIONS.get(text, {})
    return table.get(lang, text)


def _t_days(days: int, lang: str) -> str:
    """Translate risk factor strings that contain dynamic day counts."""
    if lang == "English":
        if days < 0:
            return f"Deadline passed {abs(days)} day(s) ago"
        elif days <= 3:
            return f"Immediate deadline: Only {days} day(s) remaining"
        return f"Upcoming deadline: {days} days remaining"
    elif lang == "Hindi":
        if days < 0:
            return f"समय सीमा {abs(days)} दिन पहले समाप्त हो चुकी है"
        elif days <= 3:
            return f"तत्काल समय सीमा: केवल {days} दिन शेष हैं"
        return f"आगामी समय सीमा: {days} दिन शेष हैं"
    elif lang == "Marathi":
        if days < 0:
            return f"मुदत {abs(days)} दिवसांपूर्वी संपली आहे"
        elif days <= 3:
            return f"तातडीची मुदत: फक्त {days} दिवस शिल्लक आहेत"
        return f"आगामी मुदत: {days} दिवस शिल्लक आहेत"
    return f"{days} days remaining"


def _t_docs(count: int, lang: str) -> str:
    """Translate risk factor strings that contain document counts."""
    if lang == "English":
        return f"Heavy documentation burden ({count} mandatory certificates/documents required)"
    elif lang == "Hindi":
        return f"दस्तावेज़ों का भारी भार ({count} अनिवार्य प्रमाणपत्र/दस्तावेज़ आवश्यक)"
    elif lang == "Marathi":
        return f"कागदपत्रांचा मोठा भार ({count} अनिवार्य प्रमाणपत्रे/कागदपत्रे आवश्यक)"
    return f"{count} documents required"


# ==============================================================================
# 1. NLP MODEL: NOTICE AUTHENTICITY & LINGUISTIC PATTERN CLASSIFIER
# ==============================================================================

# Domain training samples for administrative circular pattern recognition
_AUTHENTIC_SAMPLES = [
    "GOVERNMENT NOTIFICATION Ref: DHE/SCH/2026/894. In exercise of powers conferred under Section 12, eligible candidates are notified to submit application for scholarship renewal through the official government portal.",
    "OFFICE MEMORANDUM No. 42/18/2026-Estt. The Competent Authority has approved the revised guidelines for recruitment of administrative officers in accordance with statutory recruitment rules.",
    "UNIVERSITY CIRCULAR No. Exam/Reg/2026/012. It is hereby informed to all affiliated colleges and recognized institutes that the semester examination schedule has been finalized pursuant to Academic Council Resolution.",
    "PUBLIC NOTICE: Directorate of Technical Education invites online applications for admission to postgraduate diploma programmes. Detailed information brochure available on official website dte.gov.in.",
    "STATE SCHOLARSHIP NOTIFICATION: Department of Social Welfare. Sanction is hereby accorded for disbursement of pre-matric and post-matric financial assistance for eligible beneficiaries for academic session.",
    "OFFICIAL GAZETTE EXTRAORDINARY: The following regulation passed by the Senate is hereby promulgated for general information of the university community and statutory bodies.",
    "ADMISSION NOTICE 2026: Online portal for centralized admission process (CAP) will commence from next Monday. Candidates must upload self-attested copies of qualifying examination marksheets.",
    "EMPLOYMENT ADVERTISEMENT Ref No. REC/04/2026. Applications are invited from Indian citizens for appointment to the sanctioned vacant posts of Junior Assistant in pay matrix level 4.",
    "BOARD NOTIFICATION: Revised timetable for Higher Secondary Certificate examination 2026. Divisional boards, principals and examination centers to note the modified sequence of subjects.",
    "REVISED CIRCULAR: Submission of institutional annual performance appraisal reports. All heads of departments are requested to forward verified dossiers through administrative clearance channel."
]

_FRAUD_SCAM_SAMPLES = [
    "URGENT!! You have won direct cash prize of Rs 50,000 from State Welfare Board. Click bit.ly/claim-prize now and enter bank account number and OTP immediately to receive money.",
    "Job Offer Guaranteed without exam! Railway group D recruitment direct selection. Send Rs 1,500 registration charge via Google Pay / PhonePe to mobile number 9876543210 right now.",
    "Special grace marks bonus: Pay Rs 1,200 evaluation charges directly via UPI QR code before midnight to update your university marksheet instantly and clear backlogs.",
    "Govt subsidy loan scheme approved! 80% subsidy with zero interest. Send Aadhaar card photo, bank OTP, and Rs 2,000 file charge to private email govt-loan-scheme@gmail.com for instant transfer.",
    "Guaranteed selection in upcoming police recruitment. Only 10 seats left. DM on Telegram @recruitment_head for secret selection list. Rs 5,000 advance required via PhonePe.",
    "Notice: Student scholarship fund release. Your payment is on hold. Click bit.ly/claim-scholarship-cash and enter debit card PIN and CVV to claim Rs 15,000 scholarship right now.",
    "Official Alert!! Final warning: Your exam registration will be blocked today. Transfer Rs 750 late clearance penalty directly to UPI merchant id immediately to unblock.",
    "Direct admission in medical college without NEET. Limited management quota seats. Pay advance booking fee of Rs 25,000 to personal account. Contact on WhatsApp only.",
    "Earn Rs 3,000 per day government certified part-time typing job from home. No experience needed. Deposit Rs 999 security fee to UPI ID jobportal@upi immediately.",
    "Congratulation! Your phone number selected for free smartphone distribution scheme. Pay delivery courier charge Rs 350 to QR code to receive parcel."
]


_FICTIONAL_DISCLAIMER_PATTERNS = [
    # Explicit fictional document statements
    re.compile(r'\b(?:this\s+(?:document|notice|circular|form)\s+is\s+fictional)\b', re.IGNORECASE),
    re.compile(r'\b(?:fictional\s+(?:notice|circular|document|advertisement|post|form|announcement))\b', re.IGNORECASE),
    re.compile(r'\bno\s+real\s+(?:recruitment|event|scholarship|job|admission|vacancy|post|examination)\s+(?:is\s+)?(?:advertised|offered|conducted|intended|provided)\b', re.IGNORECASE),
    # Mock / Testing / Demo document statements
    re.compile(r'\bmock\s+(?:notice|circular|document|form|announcement|advertisement)\b', re.IGNORECASE),
    re.compile(r'\b(?:this\s+is\s+(?:a\s+)?)?(?:mock|dummy|synthetic)\s+(?:notice|circular|document|form|announcement)\b', re.IGNORECASE),
    re.compile(r'\bfor\s+(?:[\w\s\-]+)?testing\s+(?:purposes?\s+)?only\b', re.IGNORECASE),
    re.compile(r'\bfor\s+(?:demonstration|demo|simulation|evaluative)\s+purposes?\s+only\b', re.IGNORECASE),
    re.compile(r'\bcreated\s+for\s+(?:demonstration|demo|testing|evaluation)\s+purposes?\b', re.IGNORECASE),
    re.compile(r'\bnot\s+an\s+official\s+(?:notice|circular|document|announcement)\b', re.IGNORECASE),
    # Sample notice specifically
    re.compile(r'\bthis\s+is\s+(?:a\s+)?sample\s+(?:application\s+)?(?:notice|circular|form)\b', re.IGNORECASE),
    re.compile(r'\bsample\s+(?:application\s+)?(?:notice|circular)\s*[-—:]?\s*(?:not\s+for\s+official\s+use|for\s+(?:illustration|demonstration)\s+only)\b', re.IGNORECASE),
    # Hindi / Marathi
    re.compile(r'काल्पनिक\s+(?:नोटिस|परिपत्रक?|दस्तावेज़|विज्ञापन)', re.IGNORECASE),
    re.compile(r'यह\s+(?:दस्तावेज़|नोटिस|परिपत्रक)\s+काल्पनिक\s+है', re.IGNORECASE),
    re.compile(r'केवल\s+(?:परीक्षण|प्रदर्शन|टेस्टिंग)\s+(?:के\s+लिए|हेतु)', re.IGNORECASE),
    re.compile(r'कोई\s+वास्तविक\s+(?:भर्ती|छात्रवृत्ति|नौकरी|प्रवेश)\s+नहीं', re.IGNORECASE),
    re.compile(r'काल्पनिक\s+(?:नोटीस|परिपत्रक|कागदपत्र)', re.IGNORECASE),
    re.compile(r'हे\s+(?:परिपत्रक|कागदपत्र|नोटीस)\s+काल्पनिक\s+आहे', re.IGNORECASE),
    re.compile(r'केवळ\s+(?:चाचणीसाठी|प्रात्यक्षिकासाठी|नमुन्यासाठी)', re.IGNORECASE),
    re.compile(r'कोणतीही\s+खरी\s+(?:भरती|शिष्यवृत्ती|नोकरी|प्रवेश)\s+नाही', re.IGNORECASE)
]


def extract_fictional_disclaimer(text: str) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Evidence-based document status detector.
    Identifies explicit disclaimers indicating a document is fictional, mock, or a test sample.
    Returns: (is_fictional, disclaimer_passage, page_number)
    """
    if not text:
        return False, None, None

    lines = text.splitlines()
    for line in lines:
        trimmed = line.strip()
        if not trimmed or len(trimmed) < 6:
            continue

        # Protective warnings: ignore warnings advising against external fake notices
        if re.search(r'\b(?:beware\s+of|alert|warning|advisory|scam\s+alert|do\s+not\s+(?:fall\s+for|trust|believe))\b', trimmed, re.IGNORECASE):
            if not re.search(r'\b(?:this\s+(?:document|notice)\s+is\s+fictional|mock\s+notice)\b', trimmed, re.IGNORECASE):
                continue

        # Negation checks: e.g. 'not fictional', 'not a mock'
        if re.search(r'\b(?:is\s+not\s+fictional|not\s+a\s+mock|no\s+fake\s+notice)\b', trimmed, re.IGNORECASE):
            continue

        for pat in _FICTIONAL_DISCLAIMER_PATTERNS:
            match = pat.search(trimmed)
            if match:
                # Exclusion filters: literature, mock test, sample certificate/paper
                if re.search(r'\b(?:literature|poetry|novel|story|case\s+study|mock\s+(?:test|exam|interview|drill)|sample\s+(?:paper|copy|certificate|marksheet))\b', trimmed, re.IGNORECASE):
                    if not re.search(r'\b(?:fictional\s+(?:notice|circular|document)|for\s+(?:[\w\s\-]+)?testing\s+(?:purposes?\s+)?only|no\s+real\s+(?:recruitment|scholarship|admission)|mock\s+notice)\b', trimmed, re.IGNORECASE):
                        continue

                # Locate page number if available in multi-page document
                page_no = 1
                pages_split = re.split(r'---\s*\[Page\s*(\d+)\]\s*---', text)
                if len(pages_split) > 1:
                    for p_i in range(1, len(pages_split), 2):
                        if match.group(0).lower() in pages_split[p_i + 1].lower():
                            page_no = int(pages_split[p_i])
                            break

                return True, trimmed, page_no

    return False, None, None


class NoticeAuthenticityModel:
    """
    TF-IDF + Logistic Regression Classifier with transparent rule-based auditing.
    Loads serialized pre-trained model if available, falling back to domain-trained model.
    """

    def __init__(self):
        self.pipeline: Optional[Pipeline] = None
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """Load trained pipeline from disk, or train in-memory fallback."""
        if MODEL_FILE_PATH.exists():
            try:
                self.pipeline = joblib.load(MODEL_FILE_PATH)
                logger.info("Loaded pre-trained authenticity pipeline from %s", MODEL_FILE_PATH)
                return
            except Exception as e:
                logger.warning("Failed to load serialized pipeline from %s: %s; training fallback", MODEL_FILE_PATH, e)

        # In-memory domain training fallback
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=1200,
                stop_words='english',
                sublinear_tf=True
            )),
            ('clf', LogisticRegression(
                C=1.5,
                max_iter=400,
                random_state=42
            ))
        ])
        X = _AUTHENTIC_SAMPLES + _FRAUD_SCAM_SAMPLES
        # 1 = Authentic, 0 = Fraud/Scam
        y = [1] * len(_AUTHENTIC_SAMPLES) + [0] * len(_FRAUD_SCAM_SAMPLES)
        self.pipeline.fit(X, y)

    def extract_contextual_signals(self, text: str) -> Tuple[List[str], List[str]]:
        """
        Extract structural official cues and contextual security warning signals.
        Differentiates between legitimate protective warnings and actual scam demands.
        """
        text_lower = text.lower()
        authentic_signals: List[str] = []
        warning_signals: List[str] = []

        # ── 1. Authentic Structural Cues ─────────────────────────────────────
        if re.search(r'\b(ref|memo|no|notification)\s*[:./\-]?\s*[\w\-/]+', text_lower):
            authentic_signals.append("Official reference/dispatch number format detected")
        if re.search(r'\b(registrar|controller|director|secretary|competent authority|examinations)\b', text_lower):
            authentic_signals.append("Standard administrative designation detected")
        if re.search(r'\b(gazette|resolution|act|stipulated|pursuant|ordinance|annexure)\b', text_lower):
            authentic_signals.append("Formal statutory vocabulary match")
        if re.search(r'\b(\.gov\.in|\.nic\.in|\.ac\.in|\.edu)\b', text_lower):
            authentic_signals.append("Official government/academic domain references present")

        # ── 2. Context-Aware Fraud / Security Warnings ───────────────────────
        # Check if text is giving a safety warning rather than demanding payment
        is_protective_payment_context = bool(re.search(
            r'\b(do not pay|beware of|fraudulent fee|no fee is charged|never pay|official portal only)\b',
            text_lower
        ))
        
        # Scam payment solicitation
        has_payment_solicitation = bool(re.search(
            r'\b(transfer|pay|deposit|send)\s*(?:fee|amount|money|charge|rs\.?|₹)?\s*[\w\s]{0,20}\b(upi|gpay|phonepe|paytm|qr code|wallet)\b',
            text_lower
        ) or re.search(r'\b(upi id|upi qr|scan qr to pay)\b', text_lower))
        
        if has_payment_solicitation and not is_protective_payment_context:
            warning_signals.append("⚠️ Payment solicitation (UPI/Wallet/Direct Fee) detected")

        # Informal social channel redirection
        has_social_redirect = bool(re.search(
            r'\b(join\s+(?:our\s+)?telegram|dm\s+on\s+telegram|t\.me/|whatsapp\s+group\s+link|call\s+on\s+whatsapp\s+for\s+selection)\b',
            text_lower
        ))
        if has_social_redirect:
            warning_signals.append("⚠️ Informal social channel redirection (Telegram/WhatsApp)")

        # Unrealistic promises
        if re.search(r'\b(guaranteed selection|no exam direct selection|free laptop scheme|lottery prize|cash reward of ₹?[\d,]+)\b', text_lower):
            warning_signals.append("⚠️ Unrealistic promise or scam trigger phrasing identified")

        # Credential harvesting
        is_protective_credential_context = bool(re.search(
            r'\b(do not share|never share|will never ask for|beware of sharing)\s*(?:your)?\s*(?:otp|pin|cvv|password)\b',
            text_lower
        ))
        has_credential_request = bool(re.search(
            r'\b(send|enter|provide|verify)\s*(?:your)?\s*(?:otp|cvv|debit card pin|atm pin|netbanking password)\b',
            text_lower
        ))
        if has_credential_request and not is_protective_credential_context:
            warning_signals.append("🚨 High-risk credential harvesting pattern detected")

        return authentic_signals, warning_signals

    def predict(self, text: str, target_language: str = "English") -> Dict[str, Any]:
        """
        Predict authenticity using pure ML probability, transparently supplemented by rule-based auditing
        and evidence-based document status detection.
        All output strings are returned in target_language.
        """
        # Handle short or empty document text (Phase 3 Requirement 8 & 9)
        if not text or len(text.strip()) < 50:
            return {
                "is_authentic": None,
                "authenticity_score": None,
                "fraud_risk_score": None,
                "ml_authenticity_score": None,
                "verdict": _t("Unverified (Document text too short for statistical evaluation)", target_language),
                "confidence": _t("Unavailable", target_language),
                "signals": [_t("Document contains insufficient text for statistical evaluation.", target_language)],
                "rule_warnings": [],
                "badge_color": "#64748B",
                "is_fictional": False,
                "document_status": _t("Unverified (Document text too short for statistical evaluation)", target_language),
                "fictional_evidence": None,
                "fictional_page": None,
                "official_authenticity": _t("Unavailable", target_language)
            }

        # Predict pure probability of class 1 (Authentic) from ML model
        proba_authentic = float(self.pipeline.predict_proba([text])[0][1])
        ml_auth_percent = round(proba_authentic * 100, 1)
        ml_fraud_percent = round((1.0 - proba_authentic) * 100, 1)

        # Extract contextual rules and security cues
        authentic_signals_en, warning_signals_en = self.extract_contextual_signals(text)

        # Evidence-based document status detection (Fictional / Mock Notice)
        is_fictional, fictional_evidence, fictional_page = extract_fictional_disclaimer(text)

        if is_fictional:
            # Document explicitly identifies itself as fictional or a mock test notice
            is_authentic = False
            verdict_en = "Fictional / Mock Notice"
            document_status_en = "Fictional / Mock Notice"
            confidence_en = "High Confidence"
            badge_color = "#8B5CF6"  # Royal Purple for mock / demonstration notice
            official_authenticity_en = "Official authenticity not established (Demonstration / Mock Notice)"

            # Build signals list with explicit evidence
            disclaimer_sig = f"Explicit fictional/mock disclaimer detected (Page {fictional_page}): \"{fictional_evidence}\""
            all_signals_en = [disclaimer_sig] + authentic_signals_en
        else:
            # Transparent classification: DO NOT artificially override the learned ML probability
            is_authentic = ml_auth_percent >= 50.0

            # Formulate non-misleading, evidence-based verdict
            if is_authentic:
                if warning_signals_en:
                    # Authentic structure but contains red flags
                    verdict_en = "Administrative Format with Security Warnings"
                    confidence_en = "Review Advised"
                    badge_color = "#F59E0B"  # Amber
                elif ml_auth_percent >= 80:
                    verdict_en = "High Administrative Consistency"
                    confidence_en = "High Confidence"
                    badge_color = "#10B981"  # Emerald Green
                else:
                    verdict_en = "Likely Standard Administrative Format"
                    confidence_en = "Moderate Confidence"
                    badge_color = "#3B82F6"  # Blue
            else:
                if ml_fraud_percent >= 70 or warning_signals_en:
                    verdict_en = "Suspicious / Potential Scam Notice"
                    confidence_en = "High Suspicion"
                    badge_color = "#EF4444"  # Red
                else:
                    verdict_en = "Unverified / Irregular Notice"
                    confidence_en = "Review Advised"
                    badge_color = "#F59E0B"  # Amber

            document_status_en = verdict_en
            official_authenticity_en = "Official authenticity not independently verified"

            # Combine signals for display
            all_signals_en = authentic_signals_en + warning_signals_en
            if not all_signals_en:
                all_signals_en.append("Standard administrative communication patterns analyzed")

        # Translate output strings
        signals = [_t(s, target_language) for s in all_signals_en]
        rule_warnings = [_t(w, target_language) for w in warning_signals_en]
        verdict = _t(verdict_en, target_language)
        document_status = _t(document_status_en, target_language)
        confidence = _t(confidence_en, target_language)
        official_authenticity = _t(official_authenticity_en, target_language)

        return {
            "is_authentic": is_authentic,
            "authenticity_score": ml_auth_percent,
            "fraud_risk_score": ml_fraud_percent,
            "ml_authenticity_score": ml_auth_percent,
            "verdict": verdict,
            "confidence": confidence,
            "signals": signals,
            "rule_warnings": rule_warnings,
            "has_security_red_flags": len(warning_signals_en) > 0 and not is_fictional,
            "badge_color": badge_color,
            "is_fictional": is_fictional,
            "document_status": document_status,
            "fictional_evidence": fictional_evidence,
            "fictional_page": fictional_page,
            "official_authenticity": official_authenticity
        }


# ==============================================================================
# 2. TABULAR MODEL: DEADLINE URGENCY & ACTION RISK ENGINE
# ==============================================================================

_URGENCY_TRAINING_X = np.array([
    # High Urgency scenarios (Tight timeline, heavy requirements, penalties, offline)
    [1.0, 5.0, 1.0, 1.0, 8.0],
    [2.0, 4.0, 1.0, 0.0, 6.0],
    [3.0, 6.0, 1.0, 1.0, 7.0],
    [2.0, 2.0, 1.0, 0.0, 4.0],
    [4.0, 5.0, 1.0, 1.0, 8.0],
    [5.0, 7.0, 1.0, 1.0, 9.0],
    [3.0, 3.0, 0.0, 1.0, 5.0],
    [1.0, 1.0, 1.0, 0.0, 3.0],
    [4.0, 4.0, 1.0, 0.0, 6.0],
    [6.0, 8.0, 1.0, 1.0, 10.0],
    [5.0, 5.0, 1.0, 0.0, 7.0],
    [2.0, 7.0, 0.0, 1.0, 8.0],

    # Moderate / Low Urgency scenarios (Ample time, digital submissions, fewer requirements)
    [14.0, 2.0, 0.0, 0.0, 3.0],
    [21.0, 3.0, 0.0, 0.0, 4.0],
    [30.0, 4.0, 1.0, 0.0, 5.0],
    [25.0, 2.0, 0.0, 0.0, 3.0],
    [45.0, 3.0, 0.0, 0.0, 4.0],
    [18.0, 1.0, 0.0, 0.0, 2.0],
    [35.0, 5.0, 0.0, 1.0, 6.0],
    [28.0, 3.0, 1.0, 0.0, 4.0],
    [60.0, 4.0, 0.0, 0.0, 5.0],
    [20.0, 2.0, 0.0, 0.0, 3.0],
    [15.0, 3.0, 0.0, 0.0, 4.0],
    [40.0, 1.0, 0.0, 0.0, 2.0],
])

_URGENCY_TRAINING_Y = np.array([
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,  # High Urgency
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0   # Low / Moderate Urgency
])


class UrgencyRiskModel:
    """
    Tabular Logistic Regression classifier trained on engineered administrative risk features.
    Accurately handles missing deadlines without fabricating 14-day defaults (Phase 4).
    """

    def __init__(self):
        self.scaler = StandardScaler()
        self.clf = LogisticRegression(C=1.2, random_state=42)
        self._train()

    def _train(self):
        X_scaled = self.scaler.fit_transform(_URGENCY_TRAINING_X)
        self.clf.fit(X_scaled, _URGENCY_TRAINING_Y)

    def _estimate_days_left(self, deadline_text: str) -> Optional[int]:
        """
        Parse deadline date text and calculate days remaining from today.
        Returns None if missing, unparseable, or non-specific.
        """
        if not deadline_text or deadline_text.strip().lower() in ["not specified", "none", "n/a", "no deadline", "not mentioned"]:
            return None

        clean_text = deadline_text.strip()

        # Match relative statements like "within 7 days", "in 3 days"
        rel_match = re.search(r'(\d+)\s*(?:days?|working days?)', clean_text, re.IGNORECASE)
        if rel_match and ("within" in clean_text.lower() or "remaining" in clean_text.lower() or "in " in clean_text.lower()):
            return int(rel_match.group(1))

        # Date parsing patterns
        date_patterns = [
            r'(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})',
            r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
            r'(\d{4})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})'
        ]

        now = datetime.now()

        for pattern in date_patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                try:
                    matched_str = match.group(0)
                    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d %B %Y", "%Y-%m-%d"):
                        try:
                            parsed_date = datetime.strptime(matched_str, fmt)
                            delta = (parsed_date - now).days
                            return delta
                        except ValueError:
                            continue
                except Exception:
                    continue

        return None

    def extract_features(
        self,
        deadline_text: str,
        required_docs: List[str],
        action_items: List[str],
        full_text: str,
        target_language: str = "English"
    ) -> Tuple[Optional[np.ndarray], Optional[int], List[str]]:
        """
        Transform raw document analysis into quantitative feature vector.
        If deadline cannot be parsed, days_left is None and feature_vector is None (Phase 4).
        """
        risk_factors = []
        text_lower = full_text.lower()

        # Feature 1: Days remaining to deadline
        days_left = self._estimate_days_left(deadline_text)
        if days_left is not None:
            if days_left < 0:
                risk_factors.append(_t_days(days_left, target_language))
                risk_factors.append(_t("Deadline has already passed. Immediate inquiry recommended.", target_language))
            elif days_left <= 7:
                risk_factors.append(_t_days(days_left, target_language))
        else:
            # Phase 4: Do NOT fabricate 14 days. Explicitly note absence.
            risk_factors.append(_t("No explicit deadline found in notice; verification required from original source", target_language))

        # Feature 2: Required document count
        doc_count = len(required_docs) if required_docs else 0
        if doc_count >= 3:
            risk_factors.append(_t_docs(doc_count, target_language))

        # Feature 3: Penalty / Disqualification clauses
        has_penalty = 1.0 if re.search(
            r'\b(summarily rejected|late fee|forfeited|disqualified|no extension|invalidated|debarred|penalty)\b',
            text_lower
        ) else 0.0
        if has_penalty:
            risk_factors.append(_t("Strict disqualification or penalty clause detected", target_language))

        # Feature 4: Offline / Postal / Notary requirement
        is_offline = 1.0 if re.search(
            r'\b(speed post|registered post|hard copy|physical submission|in person|by hand|notary|stamp paper|affidavit)\b',
            text_lower
        ) else 0.0
        if is_offline:
            risk_factors.append(_t("Physical compliance barrier (Speed post, physical visit, or notary stamp required)", target_language))

        # Feature 5: Action items count
        action_count = len(action_items) if action_items else 4

        # If deadline is missing, we do not pass a fabricated deadline into the model (Phase 4)
        if days_left is None:
            return None, None, risk_factors

        feature_vector = np.array([[float(days_left), float(doc_count), has_penalty, is_offline, float(action_count)]])
        return feature_vector, days_left, risk_factors

    def predict(
        self,
        deadline_text: str,
        required_docs: List[str],
        action_items: List[str],
        full_text: str,
        target_language: str = "English"
    ) -> Dict[str, Any]:
        """
        Calculate urgency score and classification.
        Returns urgency_score=None when deadline is missing or unparseable (Phase 4).
        """
        feat_vector, days_left, risk_factors = self.extract_features(
            deadline_text, required_docs, action_items, full_text, target_language
        )

        # ── Case A: Deadline Missing / Unparseable (Phase 4) ──────────────────
        if days_left is None or feat_vector is None:
            return {
                "urgency_score": None,
                "days_left": None,
                "urgency_level": _t("Unknown / Unspecified Deadline", target_language),
                "explanation": _t("No valid deadline could be identified in the notice. Please verify the filing date manually from the original document.", target_language),
                "risk_factors": risk_factors,
                "badge_color": "#64748B",  # Slate Gray (Neutral)
                "is_expired": False
            }

        # ── Case B: Deadline Expired ──────────────────────────────────────────
        if days_left < 0:
            return {
                "urgency_score": 100.0,
                "days_left": days_left,
                "urgency_level": _t("Deadline Expired", target_language),
                "explanation": _t("Deadline has already passed. Immediate inquiry recommended.", target_language),
                "risk_factors": risk_factors,
                "badge_color": "#DC2626",  # Red
                "is_expired": True
            }

        # ── Case C: Valid Deadline Available ─────────────────────────────────
        feat_scaled = self.scaler.transform(feat_vector)
        proba_urgent = float(self.clf.predict_proba(feat_scaled)[0][1])
        urgency_score = round(proba_urgent * 100, 1)

        if urgency_score >= 70.0 or days_left <= 3:
            urgency_level = _t("Critical Urgency (Immediate Action)", target_language)
            badge_color = "#DC2626"  # Red
        elif urgency_score >= 38.0:
            urgency_level = _t("Moderate Urgency", target_language)
            badge_color = "#F59E0B"  # Amber
        else:
            urgency_level = _t("Routine / Low Urgency", target_language)
            badge_color = "#10B981"  # Green

        return {
            "urgency_score": urgency_score,
            "days_left": days_left,
            "urgency_level": urgency_level,
            "risk_factors": risk_factors,
            "badge_color": badge_color,
            "is_expired": False
        }


# ==============================================================================
# SINGLETON WRAPPERS & PUBLIC INTERFACE
# ==============================================================================

_authenticity_model = None
_urgency_model = None


def get_authenticity_model() -> NoticeAuthenticityModel:
    global _authenticity_model
    if _authenticity_model is None:
        _authenticity_model = NoticeAuthenticityModel()
    return _authenticity_model


def get_urgency_model() -> UrgencyRiskModel:
    global _urgency_model
    if _urgency_model is None:
        _urgency_model = UrgencyRiskModel()
    return _urgency_model


def assess_document_ml(
    document_text: str,
    ai_analysis_data: Dict[str, Any],
    target_language: str = "English"
) -> Dict[str, Any]:
    """
    Public entry point for full dual-model machine learning evaluation.
    Evaluates:
    1. Authenticity & Format Consistency (TF-IDF + Logistic Regression)
    2. Filing Urgency & Action Risk (Tabular Engineered Features + Logistic Regression)
    """
    auth_clf = get_authenticity_model()
    urg_clf = get_urgency_model()

    auth_result = auth_clf.predict(document_text, target_language=target_language)

    deadline_str = ai_analysis_data.get("deadline", "")
    req_docs = ai_analysis_data.get("required_documents", [])
    action_items = ai_analysis_data.get("action_items", [])

    urgency_result = urg_clf.predict(
        deadline_text=deadline_str,
        required_docs=req_docs,
        action_items=action_items,
        full_text=document_text,
        target_language=target_language
    )

    return {
        "authenticity": auth_result,
        "urgency": urgency_result
    }
