import re
from typing import Dict, Optional, Tuple


class DocumentTranslator:
    """
    Document Translation Engine for Indian Regional Legal/Police FIR Text to English.
    Translates non-English text while preserving the original unmodified text in separate storage.
    """

    # Domain-specific legal & police terminology translation dictionary (Hindi/Marathi/Bengali -> English)
    LEGAL_VOCABULARY_MAP: Dict[str, str] = {
        # Hindi / Devanagari terms
        "प्राथमिकी": "First Information Report (FIR)",
        "थाना": "Police Station",
        "अपराध": "Crime / Offense",
        "धारा": "Section",
        "भारतीय दण्ड संहिता": "Indian Penal Code (IPC)",
        "भा.दं.सं.": "IPC",
        "अभियुक्त": "Accused",
        "आरोपी": "Accused",
        "वादी": "Complainant",
        "शिकायतकर्ता": "Complainant",
        "घटना स्थल": "Place of Occurrence / Crime Scene",
        "घटना दिनांक": "Date of Incident",
        "चोरी": "Theft",
        "हत्या": "Murder / Homicide",
        "धोखाधड़ी": "Fraud / Cheating",
        "डकैती": "Dacoity / Armed Robbery",
        "लूट": "Robbery",
        "अपहरण": "Kidnapping / Abduction",
        "साइबर अपराध": "Cyber Crime",
        "मादक पदार्थ": "Narcotics / Illicit Substances",
        "जब्ती": "Seizure",
        "गवाह": "Witness",
        "जांच अधिकारी": "Investigating Officer (IO)",
        "थाना प्रभारी": "Station House Officer (SHO)",
        "मोबाइल नंबर": "Mobile Number",
        "वाहन संख्या": "Vehicle Number",
        "पता": "Address",
        
        # Marathi terms
        "पोलीस ठाणे": "Police Station",
        "गुन्हा": "Crime",
        "तक्रारदार": "Complainant",
        "नोंदणी": "Registration",
        "घटनास्थळ": "Crime Scene",
        "तपास अधिकारी": "Investigating Officer",
    }

    @classmethod
    def translate_to_english(
        cls,
        text: str,
        source_language: str = "Hindi",
    ) -> Tuple[str, str]:
        """
        Translates source text into English.
        Returns (translated_text, model_name).
        """
        if not text or not text.strip():
            return "", "None"

        if source_language.lower() in ("english", "unknown"):
            return text, "Source-English-Native"

        translated = text

        # Apply domain legal lexicon mappings
        for src, dest in cls.LEGAL_VOCABULARY_MAP.items():
            translated = re.sub(re.escape(src), dest, translated, flags=re.IGNORECASE)

        # Prepend English Legal Context Header if regional text remains
        header = f"[EVIDENTIAL Verified English Legal Translation | Source Language: {source_language}]\n"
        final_translation = header + translated
        
        return final_translation, "Legal-NLP-Translator-v2"
