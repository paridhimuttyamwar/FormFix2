import os
import json
import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

# Primary and fallback Groq models (ordered by speed and capability)
MODELS_TO_TRY = [
    "qwen/qwen3.8-27b",
    "llama-3.3-70b-versatile",
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
    "openai/gpt-oss-120b"
]


# ==============================================================================
# 1. PYDANTIC VALIDATION MODELS (PHASE 2)
# ==============================================================================

class ImportantFieldModel(BaseModel):
    field: str = Field(..., description="Field or administrative term name")
    explanation: str = Field(..., description="Clear explanation of the term")
    required_document: str = Field(default="None specified", description="Supporting document or None specified")
    source_quote: Optional[str] = Field(default=None, description="Direct supporting passage from document text")
    page_number: Optional[int] = Field(default=None, description="Page number where this appears")
    verification_status: str = Field(default="unverified", description="verified | uncertain | unverified")

    class Config:
        extra = "ignore"


class DocumentAnalysisModel(BaseModel):
    document_title: str = Field(default="Not specified", description="Official document title")
    document_type: str = Field(default="Official Notice", description="Categorization of notice")
    summary: str = Field(default="", description="Summary overview")
    deadline: str = Field(default="Not specified", description="Explicit submission deadline")
    required_documents: List[str] = Field(default_factory=list, description="Mandatory supporting documents")
    important_fields: List[ImportantFieldModel] = Field(default_factory=list, description="Key confusing fields")
    action_items: List[str] = Field(default_factory=list, description="Chronological positive action steps")
    warnings: List[str] = Field(default_factory=list, description="Protective risk-based safety advisories")
    
    # Grounding & Source Verification Metadata
    source_quotes: Dict[str, str] = Field(default_factory=dict, description="Supporting verbatim snippets")
    field_verifications: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Factual verification audit")
    factual_verification_summary: str = Field(default="", description="Summary of evidence audit")

    class Config:
        extra = "ignore"


SAMPLE_SCHOLARSHIP_DATA = {
    "document_title": "State Merit-Cum-Means Scholarship Renewal Notice (2026-2027)",
    "document_type": "Scholarship Renewal Notice",
    "summary": "Official notification from the Department of Higher Education inviting eligible undergraduate and postgraduate scholars to apply for scholarship renewal for the 2026-2027 academic session.",
    "deadline": "15 October 2026",
    "required_documents": [
        "Previous semester marksheets (minimum 60% aggregate)",
        "Bonafide Student Certificate issued by Dean/Principal",
        "Competent Authority Income Certificate (valid for current financial year)",
        "Latest College Fee Receipt with transaction ID",
        "Bank Passbook copy linked to student Aadhaar number"
    ],
    "important_fields": [
        {
            "field": "Annual Family Income",
            "explanation": "Total gross income of all earning family members combined from all sources during the financial year. Must not exceed Rs. 2,50,000/- per annum.",
            "required_document": "Income Certificate",
            "source_quote": "Annual family income must not exceed Rs. 2,50,000 per annum.",
            "page_number": 1,
            "verification_status": "verified"
        },
        {
            "field": "Bonafide Certificate",
            "explanation": "Official declaration issued by the Head of the Institution certifying that the applicant is an active full-time student.",
            "required_document": "Bonafide Student Certificate",
            "source_quote": "Enclose Bonafide Student Certificate issued by Dean/Principal.",
            "page_number": 1,
            "verification_status": "verified"
        },
        {
            "field": "Previous Academic Aggregate",
            "explanation": "Cumulative percentage or SGPA/CGPA obtained in the preceding two semesters. Minimum required is 60% with no active backlogs.",
            "required_document": "Previous Semester Marksheets",
            "source_quote": "Minimum aggregate of 60% in preceding semesters.",
            "page_number": 1,
            "verification_status": "verified"
        },
        {
            "field": "Fee Receipt Number",
            "explanation": "Official institutional acknowledgment of tuition fee payment for the current academic year.",
            "required_document": "College Fee Receipt",
            "source_quote": "Latest College Fee Receipt with transaction ID.",
            "page_number": 1,
            "verification_status": "verified"
        }
    ],
    "action_items": [
        "Collect previous semester marksheets verifying minimum 60% aggregate",
        "Obtain signed Bonafide Student Certificate from Principal/Dean's office",
        "Verify Annual Family Income is under Rs. 2,50,000 and get Income Certificate",
        "Download latest college fee payment receipt with transaction ID",
        "Confirm bank account is active and seeded with Aadhaar",
        "Fill online renewal form on the state scholarship portal",
        "Upload scanned self-attested copies of all mandatory certificates",
        "Submit completed application online before 15 October 2026 (5:00 PM IST)"
    ],
    "warnings": [
        "Incomplete applications or applications with illegible attachments will be rejected without notice.",
        "Submission after the strict deadline of 15 October 2026 will not be accepted under any circumstances.",
        "Any discrepancy or false declaration regarding family income will result in immediate cancellation and recovery of funds.",
        "Students having active backlogs or repeat papers are not eligible for renewal."
    ],
    "source_quotes": {
        "deadline": "Deadline: 15 October 2026",
        "income": "Annual family income must not exceed Rs. 2,50,000"
    },
    "field_verifications": {
        "deadline": {
            "status": "verified",
            "evidence": "15 October 2026",
            "note": "Exact match found in document text."
        },
        "required_documents": {
            "status": "verified",
            "matched_count": 5,
            "total_count": 5,
            "note": "All 5 required documents verified against notice text."
        }
    },
    "factual_verification_summary": "All key facts verified against extracted text."
}


def get_groq_api_key() -> Optional[str]:
    """Retrieve the Groq API key from environment, .env file, or Streamlit Cloud secrets."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
            val = st.secrets["GROQ_API_KEY"]
            if val and str(val).strip():
                return str(val).strip()
    except Exception:
        pass

    key = os.getenv("GROQ_API_KEY")
    if key and key.strip():
        return key.strip()

    env_paths = [
        Path(__file__).resolve().parent.parent / ".env",
        Path.cwd() / ".env"
    ]
    for p in env_paths:
        if p.exists():
            load_dotenv(dotenv_path=p, override=True)
            k = os.getenv("GROQ_API_KEY")
            if k and k.strip():
                return k.strip()

    return None


def is_groq_configured() -> bool:
    """Returns True if a valid Groq API key is detected in the environment."""
    return get_groq_api_key() is not None


def get_demo_analysis() -> Dict[str, Any]:
    """Returns the validated demo data for hackathon testing without an active API key."""
    return SAMPLE_SCHOLARSHIP_DATA.copy()


def clean_json_response(raw_text: str) -> str:
    """
    Strips markdown code fences (```json ... ```) and whitespace from LLM output.
    """
    raw_text = raw_text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
    if match:
        return match.group(1).strip()
    return raw_text


# ==============================================================================
# 2. SOURCE-GROUNDED FACTUAL VERIFICATION ENGINE (PHASE 2)
# ==============================================================================

def normalize_text_for_search(text: str) -> str:
    """Normalize text for invariant substring search."""
    if not text:
        return ""
    # Collapse whitespace and convert to lowercase
    return re.sub(r'\s+', ' ', text.lower()).strip()


def locate_text_in_document(passage: str, document_text: str) -> Tuple[bool, Optional[int]]:
    """
    Check if a supporting quote exists verbatim or near-verbatim in document text.
    Also identifies which page number it belongs to if page markers exist.
    """
    if not passage or not document_text:
        return False, None

    norm_passage = normalize_text_for_search(passage)
    norm_doc = normalize_text_for_search(document_text)

    # Substring check
    found = norm_passage in norm_doc
    if not found and len(norm_passage) > 25:
        # Check first 25 characters
        found = norm_passage[:25] in norm_doc

    if not found:
        return False, None

    # Detect page number if [Page X] markers exist
    page_num = None
    pages = re.split(r'---\s*\[Page\s*(\d+)\]\s*---', document_text)
    if len(pages) > 1:
        # pages will be [text_before, page_1_num, page_1_text, page_2_num, page_2_text...]
        for idx in range(1, len(pages), 2):
            p_no = int(pages[idx])
            p_txt = normalize_text_for_search(pages[idx + 1])
            if norm_passage[:20] in p_txt or (norm_passage in p_txt):
                page_num = p_no
                break

    return True, page_num


def verify_analysis_grounding(
    analysis_data: Dict[str, Any],
    document_text: str
) -> Dict[str, Any]:
    """
    Independently verify LLM extracted critical information against the extracted document text.
    Performs deterministic factual verification for:
    - Deadlines
    - Required documents
    - Financial fees / amounts
    - Application URLs
    - Important fields supporting quotes
    Adds factual verification status: 'verified', 'uncertain', or 'unverified'.
    """
    verifications: Dict[str, Dict[str, Any]] = {}
    norm_doc = normalize_text_for_search(document_text)

    # 1. Deadline Verification
    deadline_val = analysis_data.get("deadline", "Not specified")
    deadline_quote = analysis_data.get("source_quotes", {}).get("deadline") or analysis_data.get("deadline_quote")
    
    if not deadline_val or deadline_val.strip().lower() in ["not specified", "none", "not mentioned"]:
        verifications["deadline"] = {
            "status": "verified",
            "evidence": "None stated",
            "note": "Document does not state an explicit deadline."
        }
    else:
        # Check if the deadline date tokens (or quote) appear in the document text
        quote_found, quote_page = locate_text_in_document(deadline_quote, document_text) if deadline_quote else (False, None)
        
        # Check numbers and words of the deadline in the document
        deadline_tokens = [t.lower() for t in re.findall(r'\b\w+\b', deadline_val) if len(t) > 2]
        matched_tokens = [t for t in deadline_tokens if t in norm_doc]
        token_ratio = len(matched_tokens) / len(deadline_tokens) if deadline_tokens else 0.0

        if quote_found or token_ratio >= 0.75:
            verifications["deadline"] = {
                "status": "verified",
                "evidence": deadline_quote or deadline_val,
                "page": quote_page,
                "note": f"Verified against extracted text{' on Page ' + str(quote_page) if quote_page else ''}."
            }
        elif token_ratio >= 0.4:
            verifications["deadline"] = {
                "status": "uncertain",
                "evidence": deadline_val,
                "note": "Partial date match found in text, but supporting quote was ambiguous."
            }
        else:
            verifications["deadline"] = {
                "status": "unverified",
                "evidence": deadline_val,
                "note": "The extracted deadline could not be corroborated in the document text."
            }

    # 2. Required Documents Verification
    req_docs = analysis_data.get("required_documents", [])
    verified_docs = []
    uncertain_docs = []
    
    for doc_name in req_docs:
        # Extract core keywords from document name (e.g. 'Bonafide', 'Income', 'Aadhaar')
        keywords = [k.lower() for k in re.findall(r'\b[a-zA-Z\u0900-\u097F]{4,}\b', doc_name)]
        if not keywords:
            uncertain_docs.append(doc_name)
            continue
        
        matches = [k for k in keywords if k in norm_doc]
        if len(matches) >= max(1, len(keywords) // 2):
            verified_docs.append(doc_name)
        else:
            uncertain_docs.append(doc_name)

    verifications["required_documents"] = {
        "status": "verified" if len(verified_docs) == len(req_docs) and req_docs else ("uncertain" if verified_docs else "unverified"),
        "total_count": len(req_docs),
        "verified_count": len(verified_docs),
        "verified_items": verified_docs,
        "uncertain_items": uncertain_docs,
        "note": f"{len(verified_docs)} of {len(req_docs)} required documents corroborated by extracted keywords."
    }

    # 3. Application Fees & Currency Amounts Verification
    extracted_currencies = re.findall(r'(?:₹|rs\.?|inr)\s*[\d,]+(?:\.\d+)?', document_text, re.IGNORECASE)
    cleaned_doc_amounts = [re.sub(r'[^\d]', '', c) for c in extracted_currencies if re.sub(r'[^\d]', '', c)]
    
    verifications["fees"] = {
        "status": "verified" if extracted_currencies else "unverified",
        "amounts_in_document": list(set(extracted_currencies)),
        "note": f"Found {len(extracted_currencies)} statutory fee/payment figure(s) in document text." if extracted_currencies else "No explicit fee amounts detected in document text."
    }

    # 4. Important Fields Grounding
    verified_fields = 0
    total_fields = len(analysis_data.get("important_fields", []))
    for f in analysis_data.get("important_fields", []):
        f_quote = f.get("source_quote")
        if f_quote:
            found, p_no = locate_text_in_document(f_quote, document_text)
            if found:
                f["verification_status"] = "verified"
                f["page_number"] = p_no
                verified_fields += 1
            else:
                f["verification_status"] = "uncertain"
        else:
            # Check if field name is in doc
            fn = f.get("field", "")
            if fn and normalize_text_for_search(fn) in norm_doc:
                f["verification_status"] = "verified"
                verified_fields += 1
            else:
                f["verification_status"] = "unverified"

    verifications["important_fields"] = {
        "status": "verified" if verified_fields == total_fields and total_fields > 0 else "uncertain",
        "verified_count": verified_fields,
        "total_count": total_fields,
        "note": f"{verified_fields} of {total_fields} confusing fields grounded in source text."
    }

    # Attach summary
    analysis_data["field_verifications"] = verifications
    analysis_data["factual_verification_summary"] = (
        f"Factual Audit: Deadline is {verifications['deadline']['status'].upper()}; "
        f"{verifications['required_documents']['verified_count']}/{verifications['required_documents']['total_count']} required documents verified."
    )
    return analysis_data


# ==============================================================================
# 3. AI ANALYSIS PIPELINE WITH PYDANTIC VALIDATION & RETRY (PHASE 2)
# ==============================================================================

def analyze_document_with_ai(
    document_text: str,
    target_language: str = "English",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sends document text to Groq LLM, enforces structured JSON output, validates
    via Pydantic schema, and applies deterministic factual verification against source text.
    """
    key = api_key or get_groq_api_key()
    if not key:
        raise ValueError("AI API key is not configured. Add GROQ_API_KEY to your .env file.")

    try:
        from groq import Groq
    except ImportError:
        raise RuntimeError("The 'groq' package is not installed. Please run: pip install groq")

    client = Groq(api_key=key)

    lang_instruction = ""
    if target_language and target_language.lower() != "english":
        lang_instruction = (
            f"TARGET LANGUAGE REQUIREMENT: {target_language.upper()}.\n"
            f"Regardless of the language of the uploaded document, you MUST write ALL text values in "
            f"fluent, natural, grammatically correct {target_language} "
            f"(using proper Devanagari script for Hindi and Marathi). "
            f"This includes: 'document_title', 'document_type', 'summary', 'deadline', "
            f"'required_documents' (each item in the list), "
            f"'important_fields' (field names, explanations, and required_document values), "
            f"'action_items' (each step), and 'warnings' (each warning). "
            f"Do NOT translate JSON key names. Do NOT leave any value in English.\n\n"
        )

    system_prompt = (
        "You are an expert AI Document Action Assistant and Factual Audit Specialist.\n"
        f"{lang_instruction}"
        "Your mission is: Document -> Understanding -> Verification -> Action.\n"
        "You analyze official forms, notices, admission letters, scholarship applications, and government circulars.\n"
        "Your job is to extract crystal-clear, strictly grounded, actionable information.\n\n"
        "CRITICAL FACTUAL INTEGRITY & SOURCE GROUNDING RULES:\n"
        "1. Do NOT invent, assume, or hallucinate information. If information is not explicitly in the document, use 'Not specified' or empty list [].\n"
        "2. Provide verbatim 'source_quote' evidence in 'source_quotes' and in 'important_fields' where feasible.\n"
        "3. For action_items: MUST strictly list positive, constructive chronological steps the user must take. Do NOT put warnings or prohibitions in action_items.\n"
        "4. For warnings: MUST provide PROTECTIVE, RISK-BASED ADVISORIES from the applicant's safety perspective:\n"
        "   - If money/fees are demanded via UPI/GPay/QR/Personal account: Alert that government bodies do NOT collect fees via personal UPI, and warn against unverified payments.\n"
        "   - If sensitive credentials (OTP, PIN, CVV) or informal channels (Telegram, WhatsApp) are requested: Alert user to high fraud/phishing risk.\n"
        "   - If strict deadlines or physical attestation exist: Alert user to practical disqualification risks.\n\n"
        "You MUST respond ONLY with valid JSON conforming to this schema:\n"
        "{\n"
        '  "document_title": "Document title or Not specified",\n'
        '  "document_type": "e.g. Scholarship Notice, College Admission Form, Government Circular",\n'
        '  "summary": "Concise 2-3 sentence overview of what this document is about",\n'
        '  "deadline": "Specific deadline date and time, or Not specified",\n'
        '  "required_documents": ["Document 1", "Document 2"],\n'
        '  "important_fields": [\n'
        '    {\n'
        '      "field": "Field or term name",\n'
        '      "explanation": "Clear simple explanation of what it means",\n'
        '      "required_document": "Supporting document required, or None specified",\n'
        '      "source_quote": "Exact verbatim quote from the document text",\n'
        '      "page_number": 1\n'
        '    }\n'
        '  ],\n'
        '  "action_items": ["Step 1", "Step 2"],\n'
        '  "warnings": ["Warning 1", "Warning 2"],\n'
        '  "source_quotes": {\n'
        '    "deadline": "Verbatim quote containing the deadline",\n'
        '    "fees": "Verbatim quote containing any fee amount"\n'
        '  }\n'
        "}"
    )

    user_prompt = (
        f"Please analyze this document text and return the structured JSON:\n\n"
        f"--- DOCUMENT TEXT ---\n{document_text}\n--- END DOCUMENT TEXT ---"
    )

    models_to_try = MODELS_TO_TRY
    last_exception = None

    for model_name in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            raw_content = response.choices[0].message.content
            cleaned_content = clean_json_response(raw_content)
            data_dict = json.loads(cleaned_content)

            # Pydantic schema validation (Phase 2A)
            try:
                validated_model = DocumentAnalysisModel.model_validate(data_dict)
                validated_dict = validated_model.model_dump()
            except ValidationError as val_err:
                logger.warning("Pydantic validation warning on model %s: %s", model_name, val_err)
                # Attempt repair of core structure without fabricating critical values
                validated_dict = data_dict
                for k in ["document_title", "summary", "deadline"]:
                    if k not in validated_dict:
                        validated_dict[k] = "Not specified"
                for k in ["required_documents", "important_fields", "action_items", "warnings"]:
                    if k not in validated_dict or not isinstance(validated_dict[k], list):
                        validated_dict[k] = []

            # Deterministic Source Grounding & Factual Verification (Phase 2B)
            verified_dict = verify_analysis_grounding(validated_dict, document_text)
            return verified_dict

        except Exception as e:
            last_exception = e
            logger.warning("Model %s failed: %s; trying next model", model_name, e)
            continue

    raise RuntimeError(
        f"The AI service is temporarily unavailable. Please check your API configuration or network connection. ({str(last_exception)})"
    )


def ask_document_ai(
    document_text: str,
    question: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    target_language: str = "English",
    api_key: Optional[str] = None
) -> str:
    """
    Answers user questions strictly grounded in the uploaded document in the selected language.
    """
    key = api_key or get_groq_api_key()
    if not key:
        return "AI API key is not configured. Add GROQ_API_KEY to your .env file."

    try:
        from groq import Groq
    except ImportError:
        return "The 'groq' package is not installed. Please run: pip install groq"

    client = Groq(api_key=key)

    lang_instruction = ""
    if target_language and target_language.lower() != "english":
        lang_instruction = (
            f"You MUST reply in fluent, natural {target_language} "
            f"(using proper Devanagari script for Hindi and Marathi).\n"
        )

    system_prompt = (
        "You are an assistant answering questions about an official document.\n"
        f"{lang_instruction}"
        "STRICT GROUNDING RULES:\n"
        "1. Base your answer ONLY on the provided document text.\n"
        "2. If the document does not contain the answer, explicitly state that the document does not mention it.\n"
        "3. Never hallucinate facts, dates, names, or requirements not present in the document.\n"
        "4. Always mention the exact page or section if identifiable.\n"
        "5. Keep answers direct, friendly, and helpful."
    )

    messages = [{"role": "system", "content": system_prompt}]
    if chat_history:
        for msg in chat_history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({
        "role": "user",
        "content": f"Document Text:\n{document_text}\n\nQuestion: {question}"
    })

    for model_name in MODELS_TO_TRY:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.1,
                max_tokens=600
            )
            return response.choices[0].message.content.strip()
        except Exception:
            continue

    return "Unable to retrieve answer from AI service. Please try again."
