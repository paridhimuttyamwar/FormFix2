import os
import sys
import unittest
from pathlib import Path
from PIL import Image

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.document_processor import (
    extract_document_text,
    extract_document_pages,
    process_pdf_pages,
    deduplicate_mixed_text,
    clean_whitespace,
    DocumentProcessingError
)
from services.ocr_service import preprocess_image, preprocess_image_cv
from services.ai_service import (
    get_demo_analysis,
    is_groq_configured,
    clean_json_response,
    DocumentAnalysisModel,
    verify_analysis_grounding
)
from services.ml_service import (
    NoticeAuthenticityModel,
    UrgencyRiskModel,
    assess_document_ml,
    extract_fictional_disclaimer
)


class TestFormFixAI(unittest.TestCase):

    # ── Phase 1: OCR & Page-Level Extraction Tests ───────────────────────────

    def test_digital_pdf_text_extraction(self):
        """Test 1: Normal PDF text extraction with PyMuPDF."""
        import pymupdf
        doc = pymupdf.open()
        page = doc.new_page()
        test_content = (
            "STATE DEPARTMENT OF HIGHER EDUCATION\n"
            "NOTIFICATION: SCHOLARSHIP RENEWAL APPLICATION (2026-2027)\n"
            "Deadline: 15 October 2026\n"
            "Required Documents: Bonafide Certificate, Income Certificate, Marksheet\n"
        )
        page.insert_text((50, 72), test_content)
        pdf_bytes = doc.tobytes()

        extracted_text = extract_document_text("test_notice.pdf", pdf_bytes)
        self.assertIsInstance(extracted_text, str)
        self.assertIn("SCHOLARSHIP RENEWAL APPLICATION", extracted_text)
        self.assertIn("15 October 2026", extracted_text)
        self.assertIn("Bonafide Certificate", extracted_text)
        self.assertIn("Income Certificate", extracted_text)
        print("  [PASS] Test 1: Digital PDF extracted successfully.")

    def test_multipage_preservation(self):
        """Test Phase 1: Multi-page document preserves page numbers and text per page."""
        import pymupdf
        doc = pymupdf.open()
        p1 = doc.new_page()
        p1.insert_text((50, 72), "Section 1: General Circular Information and Guidelines for Admission.")
        p2 = doc.new_page()
        p2.insert_text((50, 72), "Section 2: Fee Structure and Document Submission Verification.")
        pdf_bytes = doc.tobytes()

        pages = process_pdf_pages(pdf_bytes)
        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[0].page_num, 1)
        self.assertEqual(pages[1].page_num, 2)
        self.assertEqual(pages[0].extraction_method, "digital")
        self.assertEqual(pages[1].extraction_method, "digital")

        combined = extract_document_text("multipage.pdf", pdf_bytes)
        self.assertIn("--- [Page 1] ---", combined)
        self.assertIn("--- [Page 2] ---", combined)
        print("  [PASS] Multi-page text preservation passed.")

    def test_mixed_page_deduplication(self):
        """Test Phase 1: Prevents duplicate text when combining digital text with OCR."""
        digital_text = "OFFICE OF THE REGISTRAR. Memo No: 402/2026. Submission deadline is 15 October 2026."
        ocr_text = (
            "OFFICE OF THE REGISTRAR. Memo No: 402/2026.\n"
            "Official Stamp: Approved by Director General of Examinations."
        )
        deduped = deduplicate_mixed_text(digital_text, ocr_text)
        self.assertIn("Approved by Director General", deduped)
        self.assertEqual(deduped.count("Memo No: 402/2026"), 1)
        print("  [PASS] Mixed-page deduplication passed.")

    def test_whitespace_cleaner(self):
        """Test whitespace normalization."""
        raw = "Line 1   with    extra    spaces\n\n\n\n\nLine 2\n\n"
        cleaned = clean_whitespace(raw)
        self.assertEqual(cleaned, "Line 1 with extra spaces\n\nLine 2")
        print("  [PASS] Whitespace normalization passed.")

    def test_unsupported_file_type(self):
        """Test unsupported file type rejection."""
        with self.assertRaises(DocumentProcessingError) as ctx:
            extract_document_text("test.docx", b"some binary data")
        self.assertIn("Unsupported file type", str(ctx.exception))
        print("  [PASS] Unsupported file handling passed.")

    def test_empty_file_handling(self):
        """Test empty content handling."""
        with self.assertRaises(DocumentProcessingError):
            extract_document_text("empty.pdf", b"")
        print("  [PASS] Empty document handling passed.")

    def test_ocr_image_preprocessing(self):
        """Test OCR image preprocessor with OpenCV contrast and CLAHE."""
        img = Image.new("RGB", (200, 200), color="blue")
        processed = preprocess_image(img)
        self.assertEqual(processed.mode, "L")
        print("  [PASS] OCR image preprocessing passed.")

    # ── Phase 2: Pydantic Validation & Source-Grounded Verification ─────────

    def test_demo_analysis_schema(self):
        """Test Phase 2: Verify Pydantic validation of analysis schema."""
        demo_data = get_demo_analysis()
        model = DocumentAnalysisModel.model_validate(demo_data)
        self.assertEqual(model.deadline, "15 October 2026")
        self.assertGreaterEqual(len(model.required_documents), 3)
        self.assertGreaterEqual(len(model.action_items), 4)
        for field in model.important_fields:
            self.assertTrue(bool(field.field))
            self.assertTrue(bool(field.explanation))
        print("  [PASS] Pydantic schema validation passed.")

    def test_source_grounded_factual_verification(self):
        """Test Phase 2: Deterministic verification corroborates text against extracted source."""
        doc_text = (
            "DEPARTMENT OF SOCIAL JUSTICE NOTIFICATION\n"
            "Final date of submission: 25 November 2026.\n"
            "Application fee: Rs 250 payable online.\n"
            "Mandatory Certificates: Income Certificate, Caste Certificate."
        )
        analysis = {
            "document_title": "Social Justice Notice",
            "document_type": "Scholarship",
            "summary": "Notification",
            "deadline": "25 November 2026",
            "required_documents": ["Income Certificate", "Caste Certificate", "Passport Photo"],
            "important_fields": [
                {"field": "Application Fee", "explanation": "Statutory fee", "source_quote": "Application fee: Rs 250"}
            ],
            "source_quotes": {"deadline": "Final date of submission: 25 November 2026"}
        }

        verified = verify_analysis_grounding(analysis, doc_text)
        vf = verified["field_verifications"]
        self.assertEqual(vf["deadline"]["status"], "verified")
        self.assertEqual(vf["required_documents"]["verified_count"], 2)
        self.assertIn("Passport Photo", vf["required_documents"]["uncertain_items"])
        self.assertEqual(vf["fees"]["status"], "verified")
        print("  [PASS] Source-grounded factual verification passed.")

    def test_json_cleaner(self):
        """Test markdown code fence stripping from LLM responses."""
        fenced = "```json\n{\"document_title\": \"Test\"}\n```"
        cleaned = clean_json_response(fenced)
        self.assertEqual(cleaned, '{"document_title": "Test"}')
        print("  [PASS] JSON fence cleaner passed.")

    # ── Phase 3: Authenticity Classifier & Decoupled Rules ───────────────────

    def test_ml_authenticity_classifier(self):
        """Test Phase 3: Authenticity Classifier using trained TF-IDF + Logistic Regression."""
        model = NoticeAuthenticityModel()

        official_text = (
            "GOVERNMENT NOTIFICATION Ref: DHE/SCH/2026/894. "
            "In exercise of powers, eligible candidates are notified to submit application "
            "for scholarship renewal through the official government portal."
        )
        res_official = model.predict(official_text)
        self.assertTrue(res_official["is_authentic"])
        self.assertGreaterEqual(res_official["authenticity_score"], 50.0)
        self.assertNotIn("Verified Official Notice", res_official["verdict"])

        scam_text = (
            "URGENT!! Win free laptop and Rs 50,000 cash! Transfer Rs 499 registration fee "
            "via Google Pay UPI immediately. Join our Telegram group now!"
        )
        res_scam = model.predict(scam_text)
        self.assertFalse(res_scam["is_authentic"])
        self.assertGreaterEqual(res_scam["fraud_risk_score"], 60.0)
        print("  [PASS] ML Model 1 (Authenticity & Scam Logistic Regression) passed.")

    def test_short_document_authenticity_returns_none(self):
        """Test Phase 3: Insufficient document text returns None / Unverified instead of 85%."""
        model = NoticeAuthenticityModel()
        short_res = model.predict("Notice too brief.")
        self.assertIsNone(short_res["authenticity_score"])
        self.assertIsNone(short_res["is_authentic"])
        self.assertIn("too short", short_res["verdict"].lower())
        self.assertEqual(short_res["confidence"], "Unavailable")
        print("  [PASS] Short document returns None/Unverified passed.")

    def test_ml_probability_decoupled_from_regex_override(self):
        """Test Phase 3: Warning signals do NOT force ML probability to 28%."""
        model = NoticeAuthenticityModel()
        text_with_flag = (
            "GOVERNMENT NOTIFICATION Ref: DHE/SCH/2026/894. "
            "In exercise of powers conferred under Section 12, eligible candidates are notified to submit application "
            "for scholarship renewal through the official government portal pursuant to Academic Council Resolution. "
            "Gazette notification published. Directorate of Technical Education invites online applications. "
            "Note: Transfer verification fee of Rs 10 to upi id portal@upi for testing."
        )
        res = model.predict(text_with_flag)
        self.assertNotEqual(res["authenticity_score"], 28.0)
        self.assertGreaterEqual(res["authenticity_score"], 50.0)
        self.assertIn("Administrative Format with Security Warnings", res["verdict"])
        self.assertTrue(res["has_security_red_flags"])
        print("  [PASS] Decoupled ML probability (no fixed 28% clamp) passed.")

    def test_contextual_security_warning_not_false_alarm(self):
        """Test Phase 3: Legitimate protective notice ('Do not share OTP') is NOT flagged as scam."""
        model = NoticeAuthenticityModel()
        protective_text = (
            "PUBLIC ADVISORY: Candidates are strictly instructed: Do NOT share your OTP, "
            "PIN, or bank password with unauthorized persons. Official portal will never ask for credentials."
        )
        _, warning_signals = model.extract_contextual_signals(protective_text)
        self.assertEqual(len(warning_signals), 0)
        print("  [PASS] Contextual security warning test passed (no false positive).")

    # ── Phase 4: Urgency Model & Missing Deadline Handling ───────────────────

    def test_missing_deadline_produces_none_urgency(self):
        """Test Phase 4: Missing or unparseable deadline returns urgency_score=None (no 14-day fallback)."""
        urgency_model = UrgencyRiskModel()
        res = urgency_model.predict(
            deadline_text="Not specified",
            required_docs=["Aadhaar", "Marksheet"],
            action_items=["Apply online"],
            full_text="University circular with no deadline mentioned."
        )
        self.assertIsNone(res["urgency_score"])
        self.assertIsNone(res["days_left"])
        self.assertIn("Unknown", res["urgency_level"])
        self.assertIn("No valid deadline", res["explanation"])
        print("  [PASS] Missing deadline produces None urgency score passed.")

    def test_expired_deadline_handling(self):
        """Test Phase 4: Expired deadline is detected with 100% urgency alert."""
        urgency_model = UrgencyRiskModel()
        res = urgency_model.predict(
            deadline_text="01 January 2020",
            required_docs=["Aadhaar"],
            action_items=["Apply"],
            full_text="Circular from 2020."
        )
        self.assertTrue(res["is_expired"])
        self.assertEqual(res["urgency_score"], 100.0)
        self.assertIn("Expired", res["urgency_level"])
        print("  [PASS] Expired deadline detection passed.")

    def test_valid_deadline_urgency_prediction(self):
        """Test Phase 4: Valid deadline computes normal Logistic Regression urgency."""
        urgency_model = UrgencyRiskModel()
        res = urgency_model.predict(
            deadline_text="2 days remaining",
            required_docs=["Income Certificate", "Caste Certificate", "Bonafide", "Marksheet", "Affidavit"],
            action_items=["Get notary", "Submit offline", "Pay fee", "Upload scan", "Send speed post"],
            full_text="Hard copy must be sent by speed post. Late submissions will be summarily rejected."
        )
        self.assertIsNotNone(res["urgency_score"])
        self.assertGreaterEqual(res["urgency_score"], 60.0)
        self.assertIn("Critical", res["urgency_level"])
        print("  [PASS] Valid deadline urgency calculation passed.")

    def test_ml_full_assessment(self):
        """Test full dual-model assessment function."""
        sample_text = "STATE UNIVERSITY Memo No: 124. Deadline: 15 October 2026. Required Documents: Marksheet."
        sample_analysis = {
            "deadline": "15 October 2026",
            "required_documents": ["Marksheet"],
            "action_items": ["Collect marksheet", "Submit online"]
        }
        assessment = assess_document_ml(sample_text, sample_analysis)
        self.assertIn("authenticity", assessment)
        self.assertIn("urgency", assessment)
        self.assertIn("authenticity_score", assessment["authenticity"])
        self.assertIn("urgency_score", assessment["urgency"])
    # ── Phase 5: Fictional Document Status & Misclassification Fix ──────────

    def test_scholarship_notice_fictional_classification(self):
        """Test Fictional Fix: Scholarship notice has ML score ~74% but status Fictional."""
        import pymupdf as fitz
        pdf_path = PROJECT_ROOT / "Scholarship_Application_Notice(1).pdf"
        if pdf_path.exists():
            doc = fitz.open(pdf_path)
            pdf_text = doc[0].get_text("text")
            model = NoticeAuthenticityModel()
            res = model.predict(pdf_text)

            self.assertTrue(res["is_fictional"])
            self.assertEqual(res["document_status"], "Fictional / Mock Notice")
            self.assertEqual(res["verdict"], "Fictional / Mock Notice")
            # Raw ML probability must be preserved (~74%)
            self.assertAlmostEqual(res["authenticity_score"], 74.4, delta=3.0)
            self.assertIsNotNone(res["fictional_evidence"])
            self.assertTrue(
                "Fictional notice" in res["fictional_evidence"] or "MOCK NOTICE" in res["fictional_evidence"]
            )
            self.assertEqual(res["fictional_page"], 1)
            self.assertIn("not established", res["official_authenticity"].lower())
            self.assertFalse(res["has_security_red_flags"])  # Not flagged as scam
            print("  [PASS] Scholarship notice correctly identified as Fictional with raw ML score ~74%.")

    def test_legitimate_notice_discussing_fictional_literature(self):
        """Test Fictional Fix: Legitimate notice discussing fictional literature is NOT flagged as fictional."""
        model = NoticeAuthenticityModel()
        lit_text = (
            "STATE UNIVERSITY EXAMINATION BOARD Ref: EXAM/2026/782. "
            "Syllabus for the Master of Arts in English Literature includes questions on "
            "fictional literature, short stories, and Renaissance drama. "
            "All registered candidates must download their admit cards from the official portal."
        )
        res = model.predict(lit_text)
        self.assertFalse(res["is_fictional"])
        self.assertIsNone(res["fictional_evidence"])
        self.assertTrue(res["is_authentic"])
        self.assertNotEqual(res["document_status"], "Fictional / Mock Notice")
        print("  [PASS] Literature/case study exclusion passed (no false positive).")

    def test_protective_warning_against_fake_notices(self):
        """Test Fictional Fix: Protective notice warning against fake/mock circulars is NOT flagged as fictional."""
        model = NoticeAuthenticityModel()
        warning_text = (
            "PUBLIC ADVISORY No: ADM/2026/09. "
            "Candidates are hereby advised: Beware of fake or fictional notices circulating on social media. "
            "No recruitment is conducted via informal channels. Always refer to the official government portal."
        )
        res = model.predict(warning_text)
        self.assertFalse(res["is_fictional"])
        self.assertIsNone(res["fictional_evidence"])
        self.assertTrue(res["is_authentic"])
        print("  [PASS] Protective notice warning against fake notices passed.")

    def test_fictional_notice_without_word_mock(self):
        """Test Fictional Fix: Fictional notice without the word 'mock' is correctly detected."""
        model = NoticeAuthenticityModel()
        demo_text = (
            "DEPARTMENT OF SOCIAL SERVICES.\n"
            "This document is fictional. No real recruitment, event or scholarship is advertised.\n"
            "Applications are invited for the Student Welfare Grant 2026.\n"
            "Eligible applicants must submit income certificates before 15 November 2026."
        )
        res = model.predict(demo_text)
        self.assertTrue(res["is_fictional"])
        self.assertEqual(res["document_status"], "Fictional / Mock Notice")
        self.assertIn("fictional", res["fictional_evidence"].lower())
        print("  [PASS] Fictional notice without 'mock' keyword detected.")

    def test_fraudulent_notice_without_disclaimer(self):
        """Test Fictional Fix: Fraudulent notice is classified as scam, NOT fictional."""
        model = NoticeAuthenticityModel()
        scam_text = (
            "URGENT SELECTION! You have been selected for Railway Group D direct appointment. "
            "Pay Rs 1,500 registration charge immediately via PhonePe or Google Pay to 9876543210. "
            "Join our Telegram channel now."
        )
        res = model.predict(scam_text)
        self.assertFalse(res["is_fictional"])
        self.assertFalse(res["is_authentic"])
        self.assertEqual(res["document_status"], "Suspicious / Potential Scam Notice")
        self.assertTrue(res["has_security_red_flags"])
        print("  [PASS] Fraudulent notice correctly categorized as scam, not fictional.")

    def test_sample_copy_marksheet_not_flagged(self):
        """Test Fictional Fix: Legitimate notice requesting sample copy of certificate is NOT flagged as fictional."""
        model = NoticeAuthenticityModel()
        sample_doc_text = (
            "STAFF SELECTION COMMISSION Memo No: SSC/2026/512. "
            "Candidates must submit a sample copy of their high school marksheet and caste certificate. "
            "Detailed instructions are published on the official commission website."
        )
        res = model.predict(sample_doc_text)
        self.assertFalse(res["is_fictional"])
        self.assertIsNone(res["fictional_evidence"])
        self.assertTrue(res["is_authentic"])
        print("  [PASS] Unrelated 'sample copy' context passed without false detection.")


if __name__ == "__main__":
    unittest.main()
