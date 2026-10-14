import io
import os
import re
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image

try:
    import pymupdf as fitz
except ImportError:
    import fitz

try:
    from services.ocr_service import (
        extract_text_from_image,
        extract_text_with_confidence,
        preprocess_image
    )
except ImportError:
    from ocr_service import (
        extract_text_from_image,
        extract_text_with_confidence,
        preprocess_image
    )

logger = logging.getLogger(__name__)


class DocumentProcessingError(Exception):
    """Custom exception for user-facing document processing errors."""
    pass


@dataclass
class PageExtraction:
    page_num: int
    text: str
    extraction_method: str  # "digital", "ocr", "mixed", "unreadable"
    ocr_confidence: Optional[float] = None
    char_count: int = 0
    word_count: int = 0
    warning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def clean_whitespace(text: str) -> str:
    """Normalize whitespace and collapse multiple linebreaks to max 2."""
    if not text:
        return ""
    # Normalize tabs and multiple spaces to a single space
    text = re.sub(r'[ \t]+', ' ', text)
    # Strip leading/trailing space from each line
    lines = [line.strip() for line in text.splitlines()]
    joined = "\n".join(lines)
    # Collapse 3 or more consecutive newlines into 2 (one blank line between paragraphs)
    cleaned = re.sub(r'\n{3,}', '\n\n', joined)
    return cleaned.strip()


def normalize_line_for_dedup(line: str) -> str:
    """Normalize line by lowercasing and removing non-alphanumeric characters."""
    return re.sub(r'[^a-zA-Z0-9\u0900-\u097F]', '', line.lower())


def deduplicate_mixed_text(digital_text: str, ocr_text: str) -> str:
    """
    Combine digital text and OCR text from a mixed page without duplicating content.
    Digital text is preferred for accuracy; unique lines from OCR are appended.
    """
    cleaned_digital = clean_whitespace(digital_text)
    cleaned_ocr = clean_whitespace(ocr_text)

    if not cleaned_digital:
        return cleaned_ocr
    if not cleaned_ocr:
        return cleaned_digital

    digital_lines = [l.strip() for l in cleaned_digital.splitlines() if l.strip()]
    normalized_digital = {normalize_line_for_dedup(l) for l in digital_lines if len(normalize_line_for_dedup(l)) >= 4}

    unique_ocr_lines = []
    for ocr_line in cleaned_ocr.splitlines():
        trimmed = ocr_line.strip()
        if not trimmed:
            continue
        norm = normalize_line_for_dedup(trimmed)
        if len(norm) < 4:
            continue
        # Check if already present or highly overlapping in digital text
        if norm in normalized_digital:
            continue
        # Check substring containment
        if any(norm in d_norm or d_norm in norm for d_norm in normalized_digital if len(d_norm) >= 8):
            continue
        unique_ocr_lines.append(trimmed)

    if unique_ocr_lines:
        combined = cleaned_digital + "\n\n" + "\n".join(unique_ocr_lines)
        return clean_whitespace(combined)
    return cleaned_digital


def detect_page_mode(page: fitz.Page) -> Tuple[str, str, float]:
    """
    Inspect a single PDF page to classify it as 'digital', 'scanned', or 'mixed'.
    Returns: (mode, digital_text, image_coverage_ratio)
    """
    digital_text = (page.get_text("text") or "").strip()
    image_list = page.get_images(full=True)
    rect = page.rect
    page_area = (rect.width * rect.height) if rect else 1.0

    # Calculate image area coverage
    total_img_area = 0.0
    for img_info in image_list:
        xref = img_info[0]
        try:
            rects = page.get_image_rects(xref)
            for r in rects:
                total_img_area += (r.width * r.height)
        except Exception:
            pass

    coverage = min(1.0, total_img_area / page_area) if page_area > 0 else 0.0
    char_len = len(digital_text)

    # Decision tree:
    # 1. Pure digital: abundant text and low/no image coverage
    if char_len >= 120 and coverage < 0.25:
        return "digital", digital_text, coverage

    # 2. Scanned: sparse or 0 digital text
    if char_len < 40:
        return "scanned", digital_text, coverage

    # 3. Mixed: has both readable digital text AND substantial image coverage
    if coverage >= 0.25 and char_len >= 40:
        return "mixed", digital_text, coverage

    # 4. Moderate text with small graphics -> treat as digital to avoid unnecessary OCR latency
    return "digital", digital_text, coverage


def process_pdf_pages(file_bytes: bytes) -> List[PageExtraction]:
    """
    Page-level extraction pipeline:
    - Evaluates each page independently
    - Extracts digital text directly when possible (zero OCR latency)
    - Conditionally runs OCR only on scanned or mixed pages
    - Preserves page numbering and extraction metadata
    - Gracefully handles missing Tesseract
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise DocumentProcessingError(f"Failed to read PDF file: {str(e)}")

    if len(doc) == 0:
        raise DocumentProcessingError("The uploaded PDF has no pages.")

    pages_result: List[PageExtraction] = []
    ocr_unavailable = False

    for page_idx in range(len(doc)):
        page_num = page_idx + 1
        page = doc[page_idx]
        mode, digital_text, coverage = detect_page_mode(page)

        if mode == "digital":
            pages_result.append(
                PageExtraction(
                    page_num=page_num,
                    text=clean_whitespace(digital_text),
                    extraction_method="digital",
                    char_count=len(digital_text),
                    word_count=len(digital_text.split())
                )
            )
            continue

        # Page requires OCR (scanned or mixed)
        ocr_text = ""
        ocr_conf = None
        warning_msg = None

        try:
            pix = page.get_pixmap(dpi=180)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            ocr_text, ocr_conf = extract_text_with_confidence(img)
        except RuntimeError as re_err:
            ocr_unavailable = True
            warning_msg = str(re_err)
            logger.warning("OCR unavailable on page %d: %s", page_num, re_err)
        except Exception as ocr_ex:
            warning_msg = f"OCR failed: {str(ocr_ex)}"
            logger.warning("OCR exception on page %d: %s", page_num, ocr_ex)

        if mode == "scanned":
            if ocr_text:
                cleaned = clean_whitespace(ocr_text)
                pages_result.append(
                    PageExtraction(
                        page_num=page_num,
                        text=cleaned,
                        extraction_method="ocr",
                        ocr_confidence=ocr_conf,
                        char_count=len(cleaned),
                        word_count=len(cleaned.split()),
                        warning=warning_msg
                    )
                )
            else:
                pages_result.append(
                    PageExtraction(
                        page_num=page_num,
                        text=clean_whitespace(digital_text),
                        extraction_method="unreadable",
                        char_count=len(digital_text),
                        word_count=len(digital_text.split()),
                        warning=warning_msg or "Page appears scanned but text could not be recognized."
                    )
                )
        elif mode == "mixed":
            combined = deduplicate_mixed_text(digital_text, ocr_text)
            cleaned = clean_whitespace(combined)
            pages_result.append(
                PageExtraction(
                    page_num=page_num,
                    text=cleaned,
                    extraction_method="mixed" if ocr_text else "digital",
                    ocr_confidence=ocr_conf,
                    char_count=len(cleaned),
                    word_count=len(cleaned.split()),
                    warning=warning_msg
                )
            )

    # Final sanity check across entire document
    total_text_chars = sum(p.char_count for p in pages_result)
    if total_text_chars == 0:
        if ocr_unavailable:
            raise DocumentProcessingError(
                "This appears to be a scanned document, but Tesseract OCR is not installed or configured in system PATH. "
                "Please install Tesseract OCR (https://github.com/UB-Mannheim/tesseract/wiki) or upload a digital PDF with selectable text."
            )
        raise DocumentProcessingError("We couldn’t find readable text in this document.")

    return pages_result


def process_pdf(file_bytes: bytes) -> str:
    """
    Extract text from PDF using PyMuPDF and page-level hybrid OCR.
    Formats multi-page documents with clean page indicators so page references are preserved.
    """
    page_extractions = process_pdf_pages(file_bytes)
    
    if len(page_extractions) == 1:
        return page_extractions[0].text

    # Multi-page formatting
    formatted_parts = []
    for p in page_extractions:
        if p.text:
            formatted_parts.append(f"--- [Page {p.page_num}] ---\n{p.text}")
    
    combined = "\n\n".join(formatted_parts)
    return clean_whitespace(combined)


def process_image(file_bytes: bytes) -> str:
    """Extract text from an uploaded image using enhanced OCR with confidence retry."""
    try:
        image = Image.open(io.BytesIO(file_bytes))
    except Exception:
        raise DocumentProcessingError("Unsupported or corrupted image file.")

    try:
        text, _ = extract_text_with_confidence(image)
        cleaned = clean_whitespace(text)
        if not cleaned:
            raise DocumentProcessingError("We couldn’t read this image clearly. Please upload a clearer document.")
        return cleaned
    except RuntimeError as e:
        raise DocumentProcessingError(str(e))
    except Exception:
        raise DocumentProcessingError("We couldn’t read this image clearly. Please upload a clearer document.")


def extract_document_pages(file_name: str, file_bytes: bytes) -> List[Dict[str, Any]]:
    """
    Extract document text structured as individual pages with extraction metadata.
    Used for page-grounded factual verification.
    """
    if not file_name or not file_bytes:
        raise DocumentProcessingError("No file or content was provided.")

    ext = os.path.splitext(file_name)[1].lower()
    if ext == ".pdf":
        extractions = process_pdf_pages(file_bytes)
        return [p.to_dict() for p in extractions]
    elif ext in [".png", ".jpg", ".jpeg"]:
        text = process_image(file_bytes)
        return [{
            "page_num": 1,
            "text": text,
            "extraction_method": "ocr",
            "ocr_confidence": None,
            "char_count": len(text),
            "word_count": len(text.split()),
            "warning": None
        }]
    else:
        raise DocumentProcessingError("Unsupported file type. Please upload PDF, JPG or PNG.")


def extract_document_text(file_name: str, file_bytes: bytes) -> str:
    """
    Main entry point for document text extraction.
    Detects file extension and routes to appropriate processor.
    Preserves complete backward compatibility.
    """
    if not file_name or not file_bytes:
        raise DocumentProcessingError("No file or content was provided.")

    ext = os.path.splitext(file_name)[1].lower()
    if ext == ".pdf":
        return process_pdf(file_bytes)
    elif ext in [".png", ".jpg", ".jpeg"]:
        return process_image(file_bytes)
    else:
        raise DocumentProcessingError("Unsupported file type. Please upload PDF, JPG or PNG.")
