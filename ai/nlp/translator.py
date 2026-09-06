"""
EVIDENTIAL Document Translation Engine
=======================================
Local neural machine translation for Indian regional languages → English, with
a narrowly-scoped legal vocabulary fallback when the local model is unavailable.

The primary provider is AI4Bharat IndicTrans2's Indic→English model. Original
OCR text is never mutated: callers persist it separately from translation.
"""

import logging
import os
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("evidential.translation")


class NeuralTranslationUnavailable(RuntimeError):
    """Raised when the optional local IndicTrans2 runtime cannot be used."""


class DocumentTranslator:
    """
    Document Translation Engine for Indian Regional Legal/Police FIR Text.
    Translates non-English text while preserving the original unmodified text
    in a separate database field.
    """

    # -------------------------------------------------------------------------
    # Hindi / Devanagari legal & police vocabulary
    # -------------------------------------------------------------------------
    HINDI_VOCABULARY: Dict[str, str] = {
        "प्राथमिकी": "First Information Report (FIR)",
        "प्रथम सूचना रिपोर्ट": "First Information Report (FIR)",
        "थाना": "Police Station",
        "पुलिस थाना": "Police Station",
        "अपराध": "Crime / Offense",
        "धारा": "Section",
        "भारतीय दण्ड संहिता": "Indian Penal Code (IPC)",
        "भारतीय दंड संहिता": "Indian Penal Code (IPC)",
        "भा.दं.सं.": "IPC",
        "अभियुक्त": "Accused",
        "आरोपी": "Accused",
        "वादी": "Complainant",
        "शिकायतकर्ता": "Complainant",
        "घटना स्थल": "Place of Occurrence / Crime Scene",
        "घटना दिनांक": "Date of Incident",
        "घटना की तारीख": "Date of Incident",
        "चोरी": "Theft",
        "हत्या": "Murder / Homicide",
        "धोखाधड़ी": "Fraud / Cheating",
        "डकैती": "Dacoity / Armed Robbery",
        "लूट": "Robbery",
        "अपहरण": "Kidnapping / Abduction",
        "साइबर अपराध": "Cyber Crime",
        "मादक पदार्थ": "Narcotics / Illicit Substances",
        "जब्ती": "Seizure",
        "जब्त": "Seized",
        "गवाह": "Witness",
        "साक्षी": "Witness",
        "जांच अधिकारी": "Investigating Officer (IO)",
        "अन्वेषण अधिकारी": "Investigating Officer (IO)",
        "थाना प्रभारी": "Station House Officer (SHO)",
        "मोबाइल नंबर": "Mobile Number",
        "वाहन संख्या": "Vehicle Number",
        "पता": "Address",
        "दिनांक": "Date",
        "समय": "Time",
        "रिपोर्ट": "Report",
        "जिला": "District",
        "राज्य": "State",
        "पीड़ित": "Victim",
        "न्यायालय": "Court",
        "मजिस्ट्रेट": "Magistrate",
        "गिरफ्तारी": "Arrest",
        "गिरफ्तार": "Arrested",
        "चार्जशीट": "Charge Sheet",
        "आरोप पत्र": "Charge Sheet",
        "साक्ष्य": "Evidence",
        "बयान": "Statement",
    }

    # -------------------------------------------------------------------------
    # Marathi terms (Devanagari but distinct vocabulary)
    # -------------------------------------------------------------------------
    MARATHI_VOCABULARY: Dict[str, str] = {
        "पोलीस ठाणे": "Police Station",
        "पोलिस ठाणे": "Police Station",
        "गुन्हा": "Crime",
        "तक्रारदार": "Complainant",
        "नोंदणी": "Registration",
        "घटनास्थळ": "Crime Scene",
        "तपास अधिकारी": "Investigating Officer",
        "आहे": "is",
        "नाही": "is not",
        "दिनांक": "Date",
        "वेळ": "Time",
        "जिल्हा": "District",
        "न्यायालय": "Court",
        "अटक": "Arrest",
        "पुरावा": "Evidence",
        "साक्षीदार": "Witness",
        "आरोपी": "Accused",
        "फिर्यादी": "Complainant",
    }

    # -------------------------------------------------------------------------
    # Kannada legal & police vocabulary (ಕನ್ನಡ)
    # -------------------------------------------------------------------------
    KANNADA_VOCABULARY: Dict[str, str] = {
        # Core FIR terms
        "ಮೊದಲ ಮಾಹಿತಿ ವರದಿ": "First Information Report (FIR)",
        "ಪ್ರಥಮ ಮಾಹಿತಿ ವರದಿ": "First Information Report (FIR)",
        "ಎಫ್ಐಆರ್": "FIR",
        "ಪೊಲೀಸ್ ಠಾಣೆ": "Police Station",
        "ಠಾಣೆ": "Police Station",
        "ಪೊಲೀಸ್ ನಿಲ್ದಾಣ": "Police Station",
        # Crime
        "ಅಪರಾಧ": "Crime",
        "ಗುನ್ನೆ": "Offence",
        "ಕಳ್ಳತನ": "Theft",
        "ದರೋಡೆ": "Robbery / Dacoity",
        "ಹತ್ಯೆ": "Murder",
        "ವಂಚನೆ": "Fraud / Cheating",
        "ಅಪಹರಣ": "Kidnapping / Abduction",
        "ಅತ್ಯಾಚಾರ": "Rape",
        "ಮಾದಕ ವಸ್ತು": "Narcotics",
        "ಸೈಬರ್ ಅಪರಾಧ": "Cyber Crime",
        # Persons
        "ಆರೋಪಿ": "Accused",
        "ದೂರುದಾರ": "Complainant",
        "ದೂರು ನೀಡಿದವರು": "Complainant",
        "ಸಾಕ್ಷಿ": "Witness",
        "ಸಾಕ್ಷಿಗಾರ": "Witness",
        "ಪೀಡಿತ": "Victim",
        "ತನಿಖಾ ಅಧಿಕಾರಿ": "Investigating Officer (IO)",
        "ಐಒ": "Investigating Officer (IO)",
        # Procedural
        "ಕಲಂ": "Section",
        "ಧಾರಾ": "Section",
        "ಭಾರತೀಯ ದಂಡ ಸಂಹಿತೆ": "Indian Penal Code (IPC)",
        "ಭಾ.ದಂ.ಸಂ": "IPC",
        "ದಿನಾಂಕ": "Date",
        "ಸಮಯ": "Time",
        "ವಿಳಾಸ": "Address",
        "ಸ್ಥಳ": "Location / Place",
        "ಘಟನೆಯ ಸ್ಥಳ": "Place of Occurrence",
        "ಜಿಲ್ಲೆ": "District",
        "ರಾಜ್ಯ": "State",
        "ದಾಖಲೆ": "Record / Document",
        "ವರದಿ": "Report",
        "ಹೇಳಿಕೆ": "Statement",
        "ಸಾಕ್ಷ್ಯ": "Evidence",
        "ವಶಪಡಿಸಿಕೊಳ್ಳಲಾಯಿತು": "Seized",
        "ಜಪ್ತಿ": "Seizure",
        "ಬಂಧನ": "Arrest",
        "ಬಂಧಿಸಲಾಗಿದೆ": "Arrested",
        "ಆರೋಪ ಪಟ್ಟಿ": "Charge Sheet",
        "ನ್ಯಾಯಾಲಯ": "Court",
        "ಮ್ಯಾಜಿಸ್ಟ್ರೇಟ್": "Magistrate",
        "ವಾಹನ ಸಂಖ್ಯೆ": "Vehicle Number",
        "ಮೊಬೈಲ್ ಸಂಖ್ಯೆ": "Mobile Number",
        # Karnataka-specific
        "ಕರ್ನಾಟಕ": "Karnataka",
        "ಬೆಂಗಳೂರು": "Bengaluru",
        "ಮೈಸೂರು": "Mysuru",
        "ಹುಬ್ಬಳ್ಳಿ": "Hubballi",
        "ಮಂಗಳೂರು": "Mangaluru",
    }

    # -------------------------------------------------------------------------
    # Merged lookup built from all three dictionaries
    # -------------------------------------------------------------------------
    _VOCAB_MAP: Optional[Dict[str, str]] = None
    _neural_model = None
    _neural_tokenizer = None
    _neural_model_id: Optional[str] = None

    # Public, credential-free OPUS-MT neural models. The first supports the
    # Dravidian source family (including Kannada); the second covers Hindi and
    # Marathi. Unlike the original IndicTrans2 checkpoint, neither is gated.
    KANNADA_MODEL = os.getenv(
        "EVIDENTIAL_KANNADA_EN_MODEL", "Helsinki-NLP/opus-mt-dra-en"
    )
    INDIC_MODEL = os.getenv(
        "EVIDENTIAL_INDIC_EN_MODEL", "Helsinki-NLP/opus-mt-inc-en"
    )
    _LANGUAGE_MODELS = {
        "kannada": (KANNADA_MODEL, "OPUS-MT-Dra-En"),
        "hindi": (INDIC_MODEL, "OPUS-MT-Inc-En"),
        "marathi": (INDIC_MODEL, "OPUS-MT-Inc-En"),
    }
    _IDENTIFIER_PATTERN = re.compile(
        r"\b(?:[A-Z]{1,4}[-/]?\d{1,6}(?:[-/]?[A-Z0-9]{1,8})*|"
        r"\d{1,4}[/-]\d{1,2}[/-]\d{2,4}|"
        r"\+?\d[\d -]{7,}\d|"
        r"(?:IPC|BNS)\s*(?:U/?s\.?|Section)?\s*\d+[A-Za-z]?)\b",
        re.IGNORECASE,
    )

    @classmethod
    def _get_vocab(cls) -> Dict[str, str]:
        if cls._VOCAB_MAP is None:
            cls._VOCAB_MAP = {
                **cls.HINDI_VOCABULARY,
                **cls.MARATHI_VOCABULARY,
                **cls.KANNADA_VOCABULARY,
            }
        return cls._VOCAB_MAP

    @classmethod
    def _protect_identifiers(cls, text: str) -> Tuple[str, List[str]]:
        """Mask identifiers so neural translation cannot alter evidentiary IDs."""
        values: List[str] = []

        def replace(match: re.Match) -> str:
            values.append(match.group(0))
            # Do not add whitespace: raw punctuation/spacing is evidence too,
            # and a round trip without a neural model must be byte-for-byte
            # equivalent to the original identifier context.
            return f"__EVIDENTIAL_ID_{len(values) - 1}__"

        return cls._IDENTIFIER_PATTERN.sub(replace, text), values

    @staticmethod
    def _restore_identifiers(text: str, values: List[str]) -> str:
        for index, value in enumerate(values):
            # Accommodate common harmless spacing/case changes made by models.
            text = re.sub(
                rf"_+\s*EVIDENTIAL\s*_?\s*ID\s*_?\s*{index}\s*_+",
                value,
                text,
                flags=re.IGNORECASE,
            )
        return text

    @classmethod
    def _load_opus(cls, source_language: str):
        """Lazily load the local neural model, downloading it only when allowed."""
        try:
            model_id, model_label = cls._LANGUAGE_MODELS[source_language.lower()]
        except KeyError as exc:
            raise NeuralTranslationUnavailable(
                f"No OPUS-MT language mapping for {source_language}."
            ) from exc

        if cls._neural_model is not None and cls._neural_model_id == model_id:
            return cls._neural_model, cls._neural_tokenizer

        try:
            import torch
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        except ImportError as exc:
            raise NeuralTranslationUnavailable(
                "OPUS-MT translation dependencies are not installed. "
                "Install backend requirements to enable neural translation."
            ) from exc

        local_only = os.getenv("EVIDENTIAL_TRANSLATION_LOCAL_ONLY", "false").lower() == "true"
        try:
            tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                local_files_only=local_only,
            )
            model = AutoModelForSeq2SeqLM.from_pretrained(
                model_id,
                local_files_only=local_only,
            )
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = model.to(device)
            model.eval()
            cls._neural_model = model
            cls._neural_tokenizer = tokenizer
            cls._neural_model_id = model_id
            return model, tokenizer
        except Exception as exc:
            raise NeuralTranslationUnavailable(
                f"{model_label} model is unavailable: {type(exc).__name__}"
            ) from exc

    @classmethod
    def _translate_with_opus(cls, text: str, source_language: str) -> str:
        model, tokenizer = cls._load_opus(source_language)
        protected_text, identifiers = cls._protect_identifiers(text)
        try:
            import torch
            device = next(model.parameters()).device
            inputs = tokenizer(
                [protected_text],
                truncation=True,
                padding=True,
                max_length=512,
                return_tensors="pt",
            ).to(device)
            with torch.no_grad():
                generated = model.generate(
                    **inputs,
                    num_beams=4,
                    max_new_tokens=384,
                    early_stopping=True,
                )
            decoded = tokenizer.batch_decode(
                generated,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True,
            )
            translated = decoded[0]
            return cls._restore_identifiers(translated, identifiers)
        except Exception as exc:
            raise NeuralTranslationUnavailable(
                f"OPUS-MT inference failed: {type(exc).__name__}"
            ) from exc

    @classmethod
    def _dictionary_fallback(cls, text: str, source_language: str) -> Tuple[str, str]:
        """Last-resort offline fallback; markers only cover genuinely unresolved spans."""
        translated = text
        for term in sorted(cls._get_vocab().keys(), key=len, reverse=True):
            translated = translated.replace(term, cls._get_vocab()[term])
        translated = re.sub(
            r"([\u0900-\u097F\u0C80-\u0CFF]{4,})",
            r"[UNTRANSLATED:\1]",
            translated,
        )
        return (
            f"[EVIDENTIAL Translation Fallback | Source Language: {source_language} | "
            "Neural provider unavailable]\n" + translated,
            "Legal-NLP-Translator-v3-Fallback",
        )

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------
    @classmethod
    def translate_to_english(
        cls,
        text: str,
        source_language: str = "Hindi",
    ) -> Tuple[str, str]:
        """
        Translate with the local IndicTrans2 neural model. If it is unavailable,
        use the explicit dictionary fallback without altering original OCR text.

        Returns (translated_text, model_name).

        The original OCR text is NEVER modified by this function — the caller
        must store them in separate fields (original_text vs translated_text).
        """
        if not text or not text.strip():
            return "", "None"

        if source_language.lower() in ("english", "unknown"):
            return text, "Source-English-Native"

        try:
            translated = cls._translate_with_opus(text, source_language)
            _, model_label = cls._LANGUAGE_MODELS[source_language.lower()]
            header = (
                f"[EVIDENTIAL Neural Translation | Source Language: {source_language} | "
                f"Model: {model_label}]\n"
            )
            return header + translated, model_label
        except NeuralTranslationUnavailable as exc:
            logger.warning("Neural translation unavailable: %s", exc)
            return cls._dictionary_fallback(text, source_language)

    @classmethod
    def supported_languages(cls) -> list:
        return ["Hindi", "Marathi", "Kannada"]
