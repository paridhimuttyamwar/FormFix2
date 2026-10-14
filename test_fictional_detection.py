import re
import pymupdf as fitz

_DISCLAIMER_PATTERNS = [
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

def extract_fictional_disclaimer(text: str):
    if not text:
        return False, None, None
    lines = text.splitlines()
    for line in lines:
        trimmed = line.strip()
        if not trimmed or len(trimmed) < 6:
            continue
        # Check for protective warning / advisory against external fake notices
        if re.search(r'\b(?:beware\s+of|alert|warning|advisory|scam\s+alert|do\s+not\s+(?:fall\s+for|trust|believe))\b', trimmed, re.IGNORECASE):
            # Only ignore if not explicitly stating the current document itself is fictional
            if not re.search(r'\b(?:this\s+(?:document|notice)\s+is\s+fictional|mock\s+notice)\b', trimmed, re.IGNORECASE):
                continue
        # Check for negation: 'not fictional', 'not a mock', etc.
        if re.search(r'\b(?:is\s+not\s+fictional|not\s+a\s+mock|no\s+fake\s+notice)\b', trimmed, re.IGNORECASE):
            continue
        for pat in _DISCLAIMER_PATTERNS:
            match = pat.search(trimmed)
            if match:
                # Exclusion: literature, mock test, sample paper, sample marksheet/copy/certificate
                if re.search(r'\b(?:literature|poetry|novel|story|case\s+study|mock\s+(?:test|exam|interview|drill)|sample\s+(?:paper|copy|certificate|marksheet))\b', trimmed, re.IGNORECASE):
                    # Check if there is an explicit document-level disclaimer overriding the exclusion
                    if not re.search(r'\b(?:fictional\s+(?:notice|circular|document)|for\s+(?:[\w\s\-]+)?testing\s+(?:purposes?\s+)?only|no\s+real\s+(?:recruitment|scholarship|admission)|mock\s+notice)\b', trimmed, re.IGNORECASE):
                        continue
                page_no = 1
                pages_split = re.split(r'---\s*\[Page\s*(\d+)\]\s*---', text)
                if len(pages_split) > 1:
                    for p_i in range(1, len(pages_split), 2):
                        if match.group(0).lower() in pages_split[p_i + 1].lower():
                            page_no = int(pages_split[p_i])
                            break
                return True, trimmed, page_no
    return False, None, None

tests = [
    ('MOCK NOTICE — FOR FORMFIX AI TESTING ONLY', True),
    ('Fictional notice. No real recruitment, event or scholarship is advertised.', True),
    ('This document is fictional and created for demonstration purposes only.', True),
    ('This is a sample application notice — for illustration only.', True),
    ('For testing purposes only. No real admission is offered.', True),
    ('This is a mock notice.', True),
    ('This is a dummy circular.', True),
    ('Synthetic notice for evaluation purposes only.', True),
    ('Not an official notice — for demonstration only.', True),
    ('काल्पनिक नोटिस - केवल परीक्षण हेतु', True),
    ('कोणतीही खरी भरती नाही - केवळ चाचणीसाठी', True),
    ('हे परिपत्रक काल्पनिक आहे', True),
    ('The examination will include 20 questions on fictional literature and classical poetry.', False),
    ('Students must prepare a case study on fictional corporate scenarios.', False),
    ('Mandatory mock test will be held on 25th October in the examination hall.', False),
    ('Mock interview schedule for shortlisted candidates is attached.', False),
    ('Please submit a sample copy of your high school leaving certificate.', False),
    ('Download the sample question paper from the university website.', False),
    ('Public Advisory: Beware of fake or fictional notices circulating on WhatsApp.', False),
    ('Warning: Candidates are advised not to fall for fake or mock advertisements.', False),
    ('This notice is not fictional; all dates are legally binding.', False),
    ('This is not a mock notice. Real application fees apply.', False),
    ('विद्यार्थ्यांनी काल्पनिक कथेवर निबंध लिहावा.', False)
]

for inp, exp in tests:
    res, ev, pg = extract_fictional_disclaimer(inp)
    assert res == exp, f"FAILED: '{inp}' => got {res}, expected {exp}"

# Also test on actual PDF
doc = fitz.open('Scholarship_Application_Notice(1).pdf')
pdf_text = doc[0].get_text('text')
is_fic, ev, p = extract_fictional_disclaimer(pdf_text)
assert is_fic == True
assert 'Fictional notice' in ev or 'MOCK NOTICE' in ev
print('ALL 23 TESTS INCLUDING SCHOLARSHIP NOTICE PASSED!')
