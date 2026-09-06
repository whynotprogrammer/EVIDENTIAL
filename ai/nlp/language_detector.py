"""
EVIDENTIAL Multilingual Language Detector
==========================================
Unicode script range frequency analysis optimised for Indian Police/FIR documents.
Supports 12 language scripts with vocabulary-based disambiguation for closely
related scripts (Hindi vs. Marathi, Kannada vs. Telugu).

Returns: (primary_language, confidence_score)
Also provides script_mix() for mixed-language document analysis.
"""

import re
from typing import Dict, List, Tuple


class LanguageDetector:
    """
    Multilingual Language Detection Engine for Indian Police / FIR documents.
    """

    # -------------------------------------------------------------------------
    # Unicode script ranges — (start, end) inclusive
    # -------------------------------------------------------------------------
    SCRIPT_RANGES: Dict[str, Tuple[int, int]] = {
        "Hindi":     (0x0900, 0x097F),   # Devanagari
        "Bengali":   (0x0980, 0x09FF),
        "Punjabi":   (0x0A00, 0x0A7F),   # Gurmukhi
        "Gujarati":  (0x0A80, 0x0AFF),
        "Odia":      (0x0B00, 0x0B7F),
        "Tamil":     (0x0B80, 0x0BFF),
        "Telugu":    (0x0C00, 0x0C7F),
        "Kannada":   (0x0C80, 0x0CFF),
        "Malayalam": (0x0D00, 0x0D7F),
        "Urdu":      (0x0600, 0x06FF),   # Arabic / Perso-Arabic
        "Sinhala":   (0x0D80, 0x0DFF),
        "English":   (0x0041, 0x007A),   # Latin A-Z / a-z
    }

    # Vocabulary hints for Devanagari-script disambiguation (Hindi vs. Marathi)
    MARATHI_INDICATORS = frozenset({
        "आहे", "नाही", "पोलीस", "गुन्हा", "तक्रार",
        "दिनांक", "नोंदणी", "कायद्यानुसार", "पुरावा",
        "फिर्यादी", "न्यायालय", "अटक",
    })
    HINDI_INDICATORS = frozenset({
        "थाना", "अपराध", "प्राथमिकी", "दर्ज", "अभियुक्त",
        "धारा", "वादी", "घटना", "भारतीय", "दण्ड",
        "जांच", "गवाह", "बयान", "जिला",
    })

    # Vocabulary hints for Kannada vs. Telugu disambiguation
    KANNADA_INDICATORS = frozenset({
        "ಠಾಣೆ", "ಅಪರಾಧ", "ದೂರು", "ಆರೋಪಿ", "ಕಳ್ಳತನ",
        "ದಿನಾಂಕ", "ಜಿಲ್ಲೆ", "ಸ್ಥಳ", "ವರದಿ", "ಬಂಧನ",
    })
    TELUGU_INDICATORS = frozenset({
        "పోలీసు", "నేరం", "ఫిర్యాదు", "నిందితుడు", "దొంగతనం",
        "తేదీ", "జిల్లా", "స్థానం", "నివేదిక",
    })

    # Minimum character threshold before script analysis is trusted
    _MIN_CHARS = 5

    # -------------------------------------------------------------------------
    # Core detection
    # -------------------------------------------------------------------------
    @classmethod
    def detect_language(cls, text: str) -> Tuple[str, float]:
        """
        Detect primary language from extracted document text.

        Returns:
            (language_name, confidence_score)  0.0 ≤ confidence ≤ 1.0
        """
        if not text or not text.strip():
            return "Unknown", 0.0

        clean = text.strip()
        counts: Dict[str, int] = {lang: 0 for lang in cls.SCRIPT_RANGES}
        total_letters = 0

        for char in clean:
            code = ord(char)
            for lang, (lo, hi) in cls.SCRIPT_RANGES.items():
                if lo <= code <= hi:
                    counts[lang] += 1
                    total_letters += 1
                    break

        if total_letters < cls._MIN_CHARS:
            # Mostly numbers / punctuation — treat as English
            return "English", 0.70

        dominant = max(counts, key=lambda k: counts[k])
        dom_count = counts[dominant]
        confidence = min(0.99, max(0.60, dom_count / total_letters))

        # ── Devanagari: Hindi vs. Marathi ───────────────────────────────────
        if dominant == "Hindi":
            m_score = sum(1 for w in cls.MARATHI_INDICATORS if w in clean)
            h_score = sum(1 for w in cls.HINDI_INDICATORS  if w in clean)
            if m_score > h_score:
                dominant = "Marathi"

        # ── Kannada vs. Telugu ───────────────────────────────────────────────
        # Both sit in adjacent Unicode ranges; Kannada range is 0x0C80–0x0CFF,
        # Telugu is 0x0C00–0x0C7F.  If vocabulary hints are available, refine.
        if dominant in ("Kannada", "Telugu"):
            ka_score = sum(1 for w in cls.KANNADA_INDICATORS if w in clean)
            te_score = sum(1 for w in cls.TELUGU_INDICATORS  if w in clean)
            if ka_score > te_score:
                dominant = "Kannada"
            elif te_score > ka_score:
                dominant = "Telugu"
            # else keep what the range analysis found

        return dominant, round(confidence, 4)

    # -------------------------------------------------------------------------
    # Script-mix analysis (used by OCR engine for multi-language routing)
    # -------------------------------------------------------------------------
    @classmethod
    def script_mix(cls, text: str) -> Dict[str, float]:
        """
        Return proportion of each detected script in the text.

        Useful for identifying mixed-language FIR documents.
        """
        if not text:
            return {}
        counts: Dict[str, int] = {}
        total = 0
        for char in text:
            code = ord(char)
            for lang, (lo, hi) in cls.SCRIPT_RANGES.items():
                if lo <= code <= hi:
                    counts[lang] = counts.get(lang, 0) + 1
                    total += 1
                    break
        if total == 0:
            return {}
        return {lang: round(cnt / total, 4) for lang, cnt in counts.items()}

    # -------------------------------------------------------------------------
    # Convenience: list scripts that exceed a threshold proportion
    # -------------------------------------------------------------------------
    @classmethod
    def dominant_scripts(cls, text: str, threshold: float = 0.05) -> List[str]:
        """Return language names whose script proportion exceeds `threshold`."""
        return [
            lang
            for lang, prop in cls.script_mix(text).items()
            if prop >= threshold
        ]
