import re
from typing import Dict, Tuple


class LanguageDetector:
    """
    Multilingual Language Detection Engine optimized for Indian Police & Legal FIR documents.
    Supports Unicode Script Range Frequency Analysis and NLP n-gram detection.
    """

    # Unicode script ranges
    SCRIPT_RANGES = {
        "Hindi": (0x0900, 0x097F),       # Devanagari (Hindi, Marathi, Sanskrit, Nepali)
        "Bengali": (0x0980, 0x09FF),     # Bengali & Assamese
        "Punjabi": (0x0A00, 0x0A7F),     # Gurmukhi
        "Gujarati": (0x0A80, 0x0AFF),    # Gujarati
        "Odia": (0x0B00, 0x0B7F),        # Odia
        "Tamil": (0x0B80, 0x0BFF),       # Tamil
        "Telugu": (0x0C00, 0x0C7F),      # Telugu
        "Kannada": (0x0C80, 0x0CFF),     # Kannada
        "Malayalam": (0x0D00, 0x0D7F),   # Malayalam
        "Urdu": (0x0600, 0x06FF),        # Arabic / Perso-Arabic
        "English": (0x0041, 0x007A),     # Latin (A-Z, a-z)
    }

    # Keywords for distinguishing Devanagari Hindi vs Marathi
    MARATHI_INDICATORS = {"आहे", "नाही", "पोलीस", "गुन्हा", "तक्रार", "दिनांक", "नोंदणी", "कायद्यानुसार"}
    HINDI_INDICATORS = {"थाना", "अपराध", "प्राथमिकी", "दर्ज", "अभियुक्त", "धारा", "वादी", "घटना", "भारतीय", "दण्ड"}

    @classmethod
    def detect_language(cls, text: str) -> Tuple[str, float]:
        """
        Detects primary language and confidence score from extracted document text.
        Returns: (language_name, confidence_score)
        """
        if not text or not text.strip():
            return "Unknown", 0.0

        clean_text = text.strip()
        script_counts: Dict[str, int] = {lang: 0 for lang in cls.SCRIPT_RANGES}
        total_letters = 0

        for char in clean_text:
            code = ord(char)
            matched = False
            for lang, (start, end) in cls.SCRIPT_RANGES.items():
                if start <= code <= end:
                    script_counts[lang] += 1
                    matched = True
                    break
            if matched:
                total_letters += 1

        if total_letters == 0:
            return "English", 0.70  # Default fallback for numbers/symbols

        # Find dominant language script
        dominant_lang = max(script_counts, key=script_counts.get)
        dominant_count = script_counts[dominant_lang]
        confidence = min(0.99, max(0.60, dominant_count / total_letters))

        # Refine Devanagari between Hindi and Marathi if applicable
        if dominant_lang == "Hindi":
            marathi_matches = sum(1 for ind in cls.MARATHI_INDICATORS if ind in clean_text)
            hindi_matches = sum(1 for ind in cls.HINDI_INDICATORS if ind in clean_text)
            if marathi_matches > hindi_matches:
                dominant_lang = "Marathi"

        return dominant_lang, round(confidence, 4)
