"""
EVIDENTIAL — Multilingual OCR Test Suite
=========================================
Tests for:
  A. English FIR (digital PDF text / plain text)
  B. Hindi / Devanagari FIR text
  C. Kannada FIR text
  D. Mixed Hindi + English
  E. Mixed Kannada + English

These tests do NOT require a running Tesseract binary or a fully downloaded
PaddleOCR model — they exercise the rule-based components (language detector,
translator) with synthetic text samples that represent real FIR content,
and also verify the OCR engine cascade with plain-text files.

Tests that require PaddleOCR image models are marked @pytest.mark.slow and
are skipped unless run with:  pytest -m slow
"""

import os
import tempfile
import textwrap
from unittest.mock import Mock
import pytest

# ── Path setup ───────────────────────────────────────────────────────────────
import sys
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from ai.nlp.language_detector import LanguageDetector
from ai.nlp.translator import DocumentTranslator
from ai.ocr.ocr_engine import OCREngine, OCREngineResult


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures: synthetic FIR text samples
# ─────────────────────────────────────────────────────────────────────────────

ENGLISH_FIR = textwrap.dedent("""\
    First Information Report (FIR)
    FIR No: 2024/KA/BLR/001
    Police Station: Indiranagar PS, Bengaluru City
    Date of Incident: 15-Mar-2024
    Crime Type: THEFT
    Section: IPC 1860 U/s 379
    Complainant: Ramesh Kumar, S/o Suresh Kumar
    Place of Offence: Indiranagar 12th Main Road, Bengaluru
    Accused: Unknown
    Brief Facts: The complainant reports that his motorcycle bearing
    registration KA-01-AB-1234 was stolen from in front of his residence.
    Investigating Officer: PSI Ananya Sharma, Badge: KA-4521
""")

HINDI_FIR = textwrap.dedent("""\
    प्रथम सूचना रिपोर्ट
    थाना: इंदिरानगर पुलिस थाना, बेंगलुरु
    दिनांक: 15 मार्च 2024
    धारा: भारतीय दण्ड संहिता धारा 379
    अभियुक्त: अज्ञात
    शिकायतकर्ता: रमेश कुमार
    घटना स्थल: 12वीं मुख्य सड़क, इंदिरानगर, बेंगलुरु
    घटना दिनांक: 15-03-2024
    विवरण: शिकायतकर्ता की मोटरसाइकिल नंबर KA-01-AB-1234 उसके
    घर के सामने से चोरी हो गई।
    जांच अधिकारी: एसआई अनन्या शर्मा, बैज: KA-4521
""")

KANNADA_FIR = textwrap.dedent("""\
    ಪ್ರಥಮ ಮಾಹಿತಿ ವರದಿ (ಎಫ್ಐಆರ್)
    ಠಾಣೆ: ಇಂದಿರಾನಗರ ಪೊಲೀಸ್ ಠಾಣೆ, ಬೆಂಗಳೂರು
    ದಿನಾಂಕ: 15 ಮಾರ್ಚ್ 2024
    ಕಲಂ: ಭಾರತೀಯ ದಂಡ ಸಂಹಿತೆ ಕಲಂ 379
    ಆರೋಪಿ: ಅಜ್ಞಾತ
    ದೂರುದಾರ: ರಮೇಶ್ ಕುಮಾರ್
    ಘಟನೆಯ ಸ್ಥಳ: 12ನೇ ಮುಖ್ಯ ರಸ್ತೆ, ಇಂದಿರಾನಗರ, ಬೆಂಗಳೂರು
    ಅಪರಾಧ: ಕಳ್ಳತನ
    ವರದಿ: ದೂರುದಾರರ ಮೋಟಾರ್ ಸೈಕಲ್ ಸಂಖ್ಯೆ KA-01-AB-1234 ಅವರ
    ಮನೆಯ ಮುಂದಿನಿಂದ ಕಳ್ಳತನವಾಗಿದೆ.
    ತನಿಖಾ ಅಧಿಕಾರಿ: ಎಸ್ಐ ಅನನ್ಯ ಶರ್ಮಾ
""")

MIXED_HINDI_ENGLISH = textwrap.dedent("""\
    First Information Report — प्राथमिकी
    Police Station: Koramangala PS / कोरमंगला पुलिस थाना
    Date: 12-Feb-2024 | दिनांक: 12 फरवरी 2024
    Section: IPC 1860 U/s 380, 420 | धारा: भारतीय दण्ड संहिता 380, 420
    Accused: Vikram Singh (आरोपी: विक्रम सिंह)
    Complainant: Priya Devi (शिकायतकर्ता: प्रिया देवी)
    Place of Offence: MG Road, Bengaluru | घटना स्थल: एमजी रोड, बेंगलुरु
    Investigating Officer: PSI Rajan | जांच अधिकारी: पीएसआई राजन
""")

MIXED_KANNADA_ENGLISH = textwrap.dedent("""\
    First Information Report / ಪ್ರಥಮ ಮಾಹಿತಿ ವರದಿ
    Police Station: Whitefield PS / ವೈಟ್‌ಫೀಲ್ಡ್ ಪೊಲೀಸ್ ಠಾಣೆ
    Date: 20-Jan-2024 | ದಿನಾಂಕ: 20 ಜನವರಿ 2024
    Section: IPC 1860 U/s 379 | ಕಲಂ: ಕಳ್ಳತನ ಕಲಂ 379
    Accused: Unknown / ಆರೋಪಿ: ಅಜ್ಞಾತ
    Complainant: Suresh Rao / ದೂರುದಾರ: ಸುರೇಶ್ ರಾವ್
    Place: ITPL Road, Bengaluru / ಸ್ಥಳ: ಐಟಿಪಿಎಲ್ ರಸ್ತೆ, ಬೆಂಗಳೂರು
    IO: SI Meera Krishnamurthy / ತನಿಖಾ ಅಧಿಕಾರಿ: ಎಸ್ಐ ಮೀರಾ ಕೃಷ್ಣಮೂರ್ತಿ
""")


# ─────────────────────────────────────────────────────────────────────────────
# A. English FIR
# ─────────────────────────────────────────────────────────────────────────────

class TestEnglishFIR:
    def test_language_detection(self):
        lang, conf = LanguageDetector.detect_language(ENGLISH_FIR)
        assert lang == "English", f"Expected English, got {lang}"
        assert conf >= 0.60, f"Confidence too low: {conf}"

    def test_ocr_text_extraction_via_txt_file(self):
        """OCR engine should read a .txt file directly via Text-Direct path."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", encoding="utf-8", delete=False
        ) as fh:
            fh.write(ENGLISH_FIR)
            tmp_path = fh.name
        try:
            result = OCREngine.extract_text(tmp_path)
            assert result.engine == "Text-Direct"
            assert "First Information Report" in result.text
            assert result.confidence >= 0.99
        finally:
            os.unlink(tmp_path)

    def test_translation_passthrough(self):
        """English text should be returned as-is (no translation applied)."""
        translated, model = DocumentTranslator.translate_to_english(
            ENGLISH_FIR, source_language="English"
        )
        assert translated == ENGLISH_FIR
        assert model == "Source-English-Native"

    def test_script_mix(self):
        mix = LanguageDetector.script_mix(ENGLISH_FIR)
        assert mix.get("English", 0) > 0.5, "English should dominate the script mix"


# ─────────────────────────────────────────────────────────────────────────────
# B. Hindi / Devanagari FIR
# ─────────────────────────────────────────────────────────────────────────────

class TestHindiFIR:
    def test_language_detection(self):
        lang, conf = LanguageDetector.detect_language(HINDI_FIR)
        assert lang == "Hindi", f"Expected Hindi, got {lang}"
        assert conf >= 0.60

    def test_devanagari_text_preserved_in_ocr(self):
        """Text-Direct path must preserve Devanagari codepoints unchanged."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", encoding="utf-8", delete=False
        ) as fh:
            fh.write(HINDI_FIR)
            tmp_path = fh.name
        try:
            result = OCREngine.extract_text(tmp_path)
            # Devanagari characters must survive the pipeline
            assert any(
                "\u0900" <= ch <= "\u097F" for ch in result.text
            ), "No Devanagari characters found in OCR output"
            assert result.confidence >= 0.90
        finally:
            os.unlink(tmp_path)

    def test_translation_hindi_terms(self):
        """Known Hindi legal terms must be replaced with English equivalents."""
        translated, model = DocumentTranslator.translate_to_english(
            HINDI_FIR, source_language="Hindi"
        )
        assert "First Information Report" in translated, \
            "प्रथम सूचना रिपोर्ट not translated"
        assert "Police Station" in translated, \
            "थाना not translated"
        assert "Accused" in translated, \
            "अभियुक्त not translated"
        assert "Investigating Officer" in translated, \
            "जांच अधिकारी not translated"
        assert model in {
            "OPUS-MT-Inc-En",
            "Legal-NLP-Translator-v3-Fallback",
        }

    def test_original_text_not_modified_by_translation(self):
        """The original Hindi text must not be changed by translate_to_english."""
        original_copy = HINDI_FIR
        translated, _ = DocumentTranslator.translate_to_english(
            HINDI_FIR, source_language="Hindi"
        )
        # Original string object must still contain Devanagari
        assert any("\u0900" <= ch <= "\u097F" for ch in HINDI_FIR)
        # Translated text should contain English
        assert "First Information Report" in translated

    def test_script_mix_devanagari_dominant(self):
        mix = LanguageDetector.script_mix(HINDI_FIR)
        assert mix.get("Hindi", 0) > 0.3, \
            f"Devanagari should be dominant, mix={mix}"


# ─────────────────────────────────────────────────────────────────────────────
# C. Kannada FIR
# ─────────────────────────────────────────────────────────────────────────────

class TestKannadaFIR:
    def test_language_detection(self):
        lang, conf = LanguageDetector.detect_language(KANNADA_FIR)
        assert lang == "Kannada", f"Expected Kannada, got {lang}"
        assert conf >= 0.60

    def test_kannada_unicode_preserved(self):
        """Kannada Unicode characters must be preserved through the text pipeline."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", encoding="utf-8", delete=False
        ) as fh:
            fh.write(KANNADA_FIR)
            tmp_path = fh.name
        try:
            result = OCREngine.extract_text(tmp_path)
            assert any(
                "\u0C80" <= ch <= "\u0CFF" for ch in result.text
            ), "No Kannada characters found in OCR output"
        finally:
            os.unlink(tmp_path)

    def test_translation_kannada_terms(self):
        """Known Kannada legal terms must be translated to English."""
        translated, model = DocumentTranslator.translate_to_english(
            KANNADA_FIR, source_language="Kannada"
        )
        assert "First Information Report" in translated, \
            "ಪ್ರಥಮ ಮಾಹಿತಿ ವರದಿ not translated"
        assert "Police Station" in translated, \
            "ಪೊಲೀಸ್ ಠಾಣೆ not translated"
        assert "Accused" in translated, \
            "ಆರೋಪಿ not translated"
        assert "Investigating Officer" in translated, \
            "ತನಿಖಾ ಅಧಿಕಾರಿ not translated"
        assert "Theft" in translated, \
            "ಕಳ್ಳತನ not translated"
        assert model in {
            "OPUS-MT-Dra-En",
            "Legal-NLP-Translator-v3-Fallback",
        }

    def test_bengaluru_translation(self):
        translated, _ = DocumentTranslator.translate_to_english(
            KANNADA_FIR, source_language="Kannada"
        )
        assert "Bengaluru" in translated, "ಬೆಂಗಳೂರು not translated"

    def test_script_mix_kannada_dominant(self):
        mix = LanguageDetector.script_mix(KANNADA_FIR)
        assert mix.get("Kannada", 0) > 0.3, \
            f"Kannada script should dominate, mix={mix}"


# ─────────────────────────────────────────────────────────────────────────────
# D. Mixed Hindi + English
# ─────────────────────────────────────────────────────────────────────────────

class TestMixedHindiEnglish:
    def test_both_scripts_preserved(self):
        """Both Devanagari and Latin characters must survive the file read."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", encoding="utf-8", delete=False
        ) as fh:
            fh.write(MIXED_HINDI_ENGLISH)
            tmp_path = fh.name
        try:
            result = OCREngine.extract_text(tmp_path)
            has_devanagari = any("\u0900" <= ch <= "\u097F" for ch in result.text)
            has_latin = any("A" <= ch <= "z" for ch in result.text)
            assert has_devanagari, "Devanagari lost in mixed Hindi+English doc"
            assert has_latin, "Latin lost in mixed Hindi+English doc"
        finally:
            os.unlink(tmp_path)

    def test_dominant_scripts_both_detected(self):
        scripts = LanguageDetector.dominant_scripts(MIXED_HINDI_ENGLISH, threshold=0.05)
        assert "Hindi" in scripts, f"Hindi not detected in mix; found: {scripts}"
        assert "English" in scripts, f"English not detected in mix; found: {scripts}"

    def test_language_detection_returns_dominant(self):
        lang, conf = LanguageDetector.detect_language(MIXED_HINDI_ENGLISH)
        # Must be one of the two languages present
        assert lang in ("Hindi", "English", "Marathi"), \
            f"Unexpected language: {lang}"
        assert conf >= 0.30

    def test_translation_preserves_english_and_translates_hindi(self):
        translated, _ = DocumentTranslator.translate_to_english(
            MIXED_HINDI_ENGLISH, source_language="Hindi"
        )
        # English already present should remain
        assert "Koramangala PS" in translated
        # Hindi terms should now be in English
        assert "Police Station" in translated


# ─────────────────────────────────────────────────────────────────────────────
# E. Mixed Kannada + English
# ─────────────────────────────────────────────────────────────────────────────

class TestMixedKannadaEnglish:
    def test_both_scripts_preserved(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", encoding="utf-8", delete=False
        ) as fh:
            fh.write(MIXED_KANNADA_ENGLISH)
            tmp_path = fh.name
        try:
            result = OCREngine.extract_text(tmp_path)
            has_kannada = any("\u0C80" <= ch <= "\u0CFF" for ch in result.text)
            has_latin = any("A" <= ch <= "z" for ch in result.text)
            assert has_kannada, "Kannada lost in mixed Kannada+English doc"
            assert has_latin, "Latin lost in mixed Kannada+English doc"
        finally:
            os.unlink(tmp_path)

    def test_dominant_scripts_both_detected(self):
        scripts = LanguageDetector.dominant_scripts(MIXED_KANNADA_ENGLISH, threshold=0.05)
        assert "Kannada" in scripts, f"Kannada not detected; found: {scripts}"
        assert "English" in scripts, f"English not detected; found: {scripts}"

    def test_translation_kannada_english(self):
        translated, _ = DocumentTranslator.translate_to_english(
            MIXED_KANNADA_ENGLISH, source_language="Kannada"
        )
        assert "Police Station" in translated, "ಪೊಲೀಸ್ ಠಾಣೆ not translated"
        assert "Whitefield PS" in translated, "English text missing"
        assert "Accused" in translated, "ಆರೋಪಿ not translated"


class TestKannadaNeuralTranslation:
    def test_actual_kannada_sentence_uses_neural_provider(self, monkeypatch):
        """A full Kannada FIR sentence must use neural translation, not markers."""
        source = "ದೂರುದಾರರು 15-03-2024 ರಂದು ಠಾಣೆಗೆ ಬಂದು ಮೋಟಾರ್ ಸೈಕಲ್ ಕಳ್ಳತನವಾಗಿದೆ ಎಂದು ತಿಳಿಸಿದ್ದಾರೆ."
        monkeypatch.setattr(
            DocumentTranslator,
            "_translate_with_opus",
            classmethod(lambda cls, text, source_language: (
                "The complainant came to the police station on 15-03-2024 "
                "and reported that the motorcycle was stolen."
            )),
        )

        translated, model = DocumentTranslator.translate_to_english(source, "Kannada")

        assert model == "OPUS-MT-Dra-En"
        assert "The complainant came to the police station" in translated
        assert "15-03-2024" in translated
        assert "[UNTRANSLATED:" not in translated

    @pytest.mark.neural_translation
    def test_real_kannada_sentence_translation(self):
        """Runs the installed local model; no mocked translation is accepted."""
        source = "ಈ ಪ್ರಕರಣವು ಬೆಂಗಳೂರಿನಲ್ಲಿ ನಡೆದಿದೆ."
        translated, model = DocumentTranslator.translate_to_english(source, "Kannada")

        assert model == "OPUS-MT-Dra-En"
        normalized = translated.lower()
        assert "case" in normalized
        assert "bengaluru" in normalized or "bangalore" in normalized
        assert any(word in normalized for word in ("occurred", "happened", "took place"))
        assert "[UNTRANSLATED:" not in translated

    def test_identifier_protection_preserves_vehicle_and_fir_numbers(self):
        text = "FIR KA-01-AB-1234, IPC 379, ದಿನಾಂಕ 15-03-2024"
        protected, identifiers = DocumentTranslator._protect_identifiers(text)
        restored = DocumentTranslator._restore_identifiers(protected, identifiers)
        assert restored == text


# ─────────────────────────────────────────────────────────────────────────────
# F. Engine capability sanity checks
# ─────────────────────────────────────────────────────────────────────────────

class TestEngineCapabilities:
    def test_paddle_v37_mapping_result_preserves_kannada_text(self):
        """PaddleOCR 3.7 mapping output must not be discarded by the adapter."""
        paddle = Mock()
        paddle.predict.return_value = [{
            "rec_texts": ["ಪ್ರಥಮ ಮಾಹಿತಿ ವರದಿ", "ಬೆಂಗಳೂರು"],
            "rec_scores": [0.96, 0.94],
        }]
        image = __import__("numpy").zeros((24, 24), dtype="uint8")

        result = OCREngine._run_paddle_instance(paddle, image, "KA-v3")

        assert result is not None
        assert result.engine == "PaddleOCR-KA-v3"
        assert "ಪ್ರಥಮ ಮಾಹಿತಿ ವರದಿ" in result.text
        assert result.confidence == pytest.approx(0.95)

    def test_pypdf_available(self):
        caps = OCREngine.available_engines()
        assert caps["pypdf"] is True, "pypdf should be installed"

    def test_opencv_available(self):
        caps = OCREngine.available_engines()
        assert caps["opencv"] is True, "opencv should be installed"

    def test_paddleocr_available(self):
        caps = OCREngine.available_engines()
        assert caps["paddleocr"] is True, \
            "paddleocr should be installed (paddlepaddle + paddleocr)"

    def test_pytesseract_importable(self):
        caps = OCREngine.available_engines()
        assert caps["pytesseract"] is True, \
            "pytesseract Python binding should be installed"

    def test_ocr_result_never_none(self):
        """extract_text must NEVER return None."""
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".bin", delete=False
        ) as fh:
            fh.write(b"\x00\x01\x02\x03")   # Non-text binary blob
            tmp_path = fh.name
        try:
            result = OCREngine.extract_text(tmp_path)
            assert result is not None
            assert isinstance(result, OCREngineResult)
            assert isinstance(result.text, str)
        finally:
            os.unlink(tmp_path)

    def test_digital_pdf_extraction(self):
        """PDF with native text layer should use PDF-DigitalStream engine."""
        try:
            import pypdf
            from pypdf import PdfWriter
            import io as _io
            # Create a minimal digital PDF in memory
            writer = PdfWriter()
            page = writer.add_blank_page(width=200, height=200)
            buf = _io.BytesIO()
            writer.write(buf)
            pdf_bytes = buf.getvalue()
        except Exception:
            pytest.skip("pypdf cannot create test PDF")

        # An empty PDF has no text stream — should fall through to image path
        result = OCREngine.extract_text(pdf_bytes, mime_type="application/pdf")
        assert result is not None

    def test_empty_text_gives_unknown_language(self):
        lang, conf = LanguageDetector.detect_language("")
        assert lang == "Unknown"
        assert conf == 0.0

    def test_supported_translation_languages(self):
        langs = DocumentTranslator.supported_languages()
        assert "Hindi" in langs
        assert "Kannada" in langs
        assert "Marathi" in langs


# ─────────────────────────────────────────────────────────────────────────────
# G. Error handling
# ─────────────────────────────────────────────────────────────────────────────

class TestErrorHandling:
    def test_nonexistent_file_returns_fallback(self):
        """Missing file should not raise — should return a fallback result."""
        result = OCREngine.extract_text("/nonexistent/path/fir.pdf")
        assert result is not None
        assert result.engine in ("Raster-Fallback", "Binary-String-Extractor")

    def test_empty_bytes_returns_result(self):
        result = OCREngine.extract_text(b"")
        assert result is not None

    def test_translation_empty_string(self):
        translated, model = DocumentTranslator.translate_to_english("", "Kannada")
        assert translated == ""
        assert model == "None"

    def test_language_detection_whitespace_only(self):
        lang, conf = LanguageDetector.detect_language("   \n\t  ")
        assert lang == "Unknown"
