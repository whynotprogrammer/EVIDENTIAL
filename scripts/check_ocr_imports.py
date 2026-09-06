"""Quick import check script — run from project root."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

print("Importing OCR engine...")
from ai.ocr.ocr_engine import OCREngine
caps = OCREngine.available_engines()
print(f"  pypdf={caps['pypdf']}  opencv={caps['opencv']}  paddle={caps['paddleocr']}  tesseract={caps['pytesseract']}")

print("Importing language detector...")
from ai.nlp.language_detector import LanguageDetector
lang, conf = LanguageDetector.detect_language("Hello FIR Bengaluru Police Station")
print(f"  English test: lang={lang} conf={conf:.2f}")
lang2, conf2 = LanguageDetector.detect_language("ಪ್ರಥಮ ಮಾಹಿತಿ ವರದಿ ಠಾಣೆ ಆರೋಪಿ ಕಳ್ಳತನ")
print(f"  Kannada test: lang={lang2} conf={conf2:.2f}")
lang3, conf3 = LanguageDetector.detect_language("प्रथम सूचना रिपोर्ट थाना अभियुक्त धारा")
print(f"  Hindi test  : lang={lang3} conf={conf3:.2f}")

print("Importing translator...")
from ai.nlp.translator import DocumentTranslator
print(f"  Supported: {DocumentTranslator.supported_languages()}")
t, m = DocumentTranslator.translate_to_english("ಪ್ರಥಮ ಮಾಹಿತಿ ವರದಿ ಪೊಲೀಸ್ ಠಾಣೆ ಆರೋಪಿ", "Kannada")
print(f"  Kannada->EN: model={m}")
assert "First Information Report" in t, "Kannada FIR term not translated"
assert "Police Station" in t, "ಠಾಣೆ not translated"
print("  Translation assertions PASSED")

print("Importing AI pipeline...")
from ai.pipeline import DocumentAIPipeline
print("  OK")

print("Importing FastAPI application...")
from backend.app.main import app
print(f"  FastAPI app loaded, routes: {len(app.routes)}")

print()
print("=" * 50)
print("ALL IMPORTS OK — backend is ready to start")
print("=" * 50)
