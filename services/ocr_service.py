import os
import shutil
import logging
from typing import Tuple, Optional, List
from PIL import Image, ImageEnhance

try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

import pytesseract

logger = logging.getLogger(__name__)

# Common Windows installation locations for Tesseract-OCR
COMMON_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
]


def _configure_tesseract() -> bool:
    """Attempt to configure pytesseract with the binary location."""
    # Check if tesseract is already in PATH
    if shutil.which("tesseract"):
        return True

    # Check environment variable
    custom_cmd = os.getenv("TESSERACT_CMD")
    if custom_cmd and os.path.isfile(custom_cmd):
        pytesseract.pytesseract.tesseract_cmd = custom_cmd
        return True

    # Search standard paths
    for path in COMMON_TESSERACT_PATHS:
        if os.path.isfile(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return True

    return False


def get_available_tesseract_languages() -> List[str]:
    """Return list of available Tesseract language codes, or ['eng'] fallback."""
    if not _configure_tesseract():
        return ["eng"]
    try:
        langs = pytesseract.get_languages(config="")
        return langs if langs else ["eng"]
    except Exception:
        return ["eng"]


def get_optimal_ocr_language_string(requested_langs: Optional[List[str]] = None) -> str:
    """
    Build a safe Tesseract language parameter string (e.g., 'eng+hin+mar')
    including only languages that are actually installed.
    """
    if requested_langs is None:
        requested_langs = ["eng", "hin", "mar"]

    available = set(get_available_tesseract_languages())
    active = [lang for lang in requested_langs if lang in available]
    if not active:
        # If none matched, default to eng
        return "eng"
    return "+".join(active)


# ==============================================================================
# OpenCV Preprocessing Pipeline
# ==============================================================================

def deskew_image_cv(gray_img: "np.ndarray") -> "np.ndarray":
    """
    Estimate text orientation and rotate image to deskew.
    Safe bounded rotation: only corrects skew between -45 and +45 degrees.
    """
    if not HAS_OPENCV:
        return gray_img

    try:
        # Invert colors so text is foreground (white)
        thresh = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        coords = np.column_stack(np.where(thresh > 0))
        if coords.shape[0] < 50:
            return gray_img

        angle = cv2.minAreaRect(coords)[-1]
        # Adjust angle from OpenCV convention
        if angle < -45:
            angle = -(90 + angle)
        elif angle > 45:
            angle = 90 - angle
        else:
            angle = -angle

        # Only deskew if meaningful tilt detected
        if 0.5 <= abs(angle) <= 45.0:
            (h, w) = gray_img.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(
                gray_img, M, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            return rotated
    except Exception as e:
        logger.debug("Deskew failed: %s", e)

    return gray_img


def preprocess_image_cv(
    image: Image.Image,
    mode: str = "clahe",
    do_deskew: bool = True
) -> Image.Image:
    """
    Conditional OpenCV preprocessing pipeline:
    - Grayscale conversion
    - Contrast improvement via CLAHE (Contrast Limited Adaptive Histogram Equalization)
    - Denoising (fastNlMeans or median filtering)
    - Conditional deskewing
    - Optional thresholding (Otsu binarization or adaptive Gaussian)
    Falls back gracefully to PIL enhancement if OpenCV is unavailable.
    """
    if not HAS_OPENCV:
        return preprocess_image_pil(image)

    try:
        # Convert PIL Image to RGB -> OpenCV BGR -> Grayscale
        rgb = np.array(image.convert("RGB"))
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

        # 1. Deskew
        if do_deskew:
            gray = deskew_image_cv(gray)

        # 2. Denoise
        denoised = cv2.fastNlMeansDenoising(gray, h=7, templateWindowSize=7, searchWindowSize=21)

        # 3. Contrast & Thresholding variants
        if mode == "clahe":
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            processed = clahe.apply(denoised)
        elif mode == "otsu":
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            _, processed = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        elif mode == "adaptive":
            processed = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 5
            )
        else:
            processed = denoised

        return Image.fromarray(processed)
    except Exception as e:
        logger.warning("OpenCV preprocessing failed: %s; falling back to PIL", e)
        return preprocess_image_pil(image)


def preprocess_image_pil(image: Image.Image) -> Image.Image:
    """
    Lightweight PIL fallback image preprocessing:
    Convert to grayscale and enhance contrast for clearer text edges.
    """
    try:
        gray = image.convert("L")
        enhancer = ImageEnhance.Contrast(gray)
        enhanced = enhancer.enhance(1.8)
        return enhanced
    except Exception:
        return image


def preprocess_image(image: Image.Image) -> Image.Image:
    """Standard preprocessing entry point (backward compatible)."""
    return preprocess_image_cv(image, mode="clahe", do_deskew=True)


# ==============================================================================
# OCR Extraction with Confidence & Retry Logic
# ==============================================================================

def extract_text_with_confidence(
    image: Image.Image,
    target_language: str = "eng"
) -> Tuple[str, float]:
    """
    Extract text with word-level confidence calculation and adaptive retry logic.
    Returns (cleaned_text, average_confidence).
    """
    is_available = _configure_tesseract()
    if not is_available:
        raise RuntimeError(
            "Tesseract OCR engine is not installed or not found in system PATH. "
            "For scanned documents or images, please install Tesseract OCR from "
            "https://github.com/UB-Mannheim/tesseract/wiki, or upload a digital PDF."
        )

    # Determine safe language string
    lang_param = get_optimal_ocr_language_string([target_language, "eng"])

    def _run_pass(processed_img: Image.Image) -> Tuple[str, float, int]:
        try:
            data = pytesseract.image_to_data(
                processed_img,
                lang=lang_param,
                output_type=pytesseract.Output.DICT
            )
        except Exception:
            # Fallback to pure english if combined string failed
            data = pytesseract.image_to_data(
                processed_img,
                lang="eng",
                output_type=pytesseract.Output.DICT
            )

        words = []
        confidences = []
        n_boxes = len(data.get("text", []))
        for i in range(n_boxes):
            word = (data["text"][i] or "").strip()
            conf = data["conf"][i]
            if word and conf != "-1":
                try:
                    c_val = float(conf)
                    if c_val >= 0:
                        words.append(word)
                        confidences.append(c_val)
                except (ValueError, TypeError):
                    words.append(word)

        text = " ".join(words)
        mean_conf = (sum(confidences) / len(confidences)) if confidences else 0.0
        return text, mean_conf, len(words)

    # Pass 1: CLAHE with Deskew
    pass1_img = preprocess_image_cv(image, mode="clahe", do_deskew=True)
    text1, conf1, count1 = _run_pass(pass1_img)

    # If confidence is good (>= 65%) and words were detected, return immediately
    if conf1 >= 65.0 and count1 >= 5:
        return text1.strip(), round(conf1, 2)

    # Pass 2: Retry with Otsu binarization
    pass2_img = preprocess_image_cv(image, mode="otsu", do_deskew=False)
    text2, conf2, count2 = _run_pass(pass2_img)

    # Pick the better extraction
    if conf2 > conf1 and count2 >= count1:
        return text2.strip(), round(conf2, 2)
    elif count2 > count1 * 1.5:
        # Significantly more text extracted
        return text2.strip(), round(conf2, 2)
    else:
        return text1.strip(), round(conf1, 2)


def extract_text_from_image(image: Image.Image) -> str:
    """
    Extract text from a PIL Image using pytesseract with confidence retry.
    Returns cleaned text string.
    Raises RuntimeError if Tesseract is not available or readable text cannot be extracted.
    """
    text, _ = extract_text_with_confidence(image)
    return text
