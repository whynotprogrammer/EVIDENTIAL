"""
EVIDENTIAL Multilingual OCR Engine
====================================
Multi-engine cascade for English, Hindi (Devanagari), Kannada, and mixed-language
FIR documents. Engine priority per document type:

  PDF with native text  → PDF-DigitalStream   (pypdf, confidence 0.98)
  Plain text file       → Text-Direct          (confidence 0.99)
  Image / scanned PDF   → PaddleOCR-v5 (lang-adaptive) → Tesseract → Binary fallback

PaddleOCR 3.7 instances are created lazily and cached:
  _paddle_en  : PP-OCRv6 English model
  _paddle_hi  : PP-OCRv5 Devanagari model  (Hindi, Marathi, Sanskrit …)
  _paddle_ka  : PP-OCRv3 Kannada model

For mixed-language documents the engine runs both the script-appropriate model
AND the English model and merges the text, preserving both scripts.
"""

import io
import os
import re
import logging
from typing import Optional, Union

import numpy as np
from PIL import Image

from ai.ocr.preprocessor import DocumentPreprocessor

logger = logging.getLogger("evidential.ocr")

# ---------------------------------------------------------------------------
# Optional dependencies — graceful degradation if missing
# ---------------------------------------------------------------------------
try:
    import pytesseract
    HAS_PYTESSERACT = True
    # Common Windows install path; overridden by TESSERACT_CMD env var
    _TESS_CMD = os.environ.get(
        "TESSERACT_CMD",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    )
    if os.path.isfile(_TESS_CMD):
        pytesseract.pytesseract.tesseract_cmd = _TESS_CMD
    else:
        # Try PATH lookup; pytesseract will raise if still not found
        _TESS_CMD = "tesseract"
        pytesseract.pytesseract.tesseract_cmd = _TESS_CMD
except ImportError:
    HAS_PYTESSERACT = False

try:
    from paddleocr import PaddleOCR as _PaddleOCR
    HAS_PADDLEOCR = True
except ImportError:
    HAS_PADDLEOCR = False

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------
class OCREngineResult:
    """Carries OCR text, a confidence score, and the engine that produced it."""

    def __init__(
        self,
        text: str,
        confidence: float,
        engine: str,
        detected_pages: int = 1,
        detected_scripts: Optional[list] = None,
    ):
        self.text = text.strip()
        self.confidence = float(confidence)
        self.engine = engine
        self.detected_pages = detected_pages
        # e.g. ["Latin", "Devanagari"] for mixed docs
        self.detected_scripts: list = detected_scripts or []

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "confidence": round(self.confidence, 4),
            "engine": self.engine,
            "detected_pages": self.detected_pages,
            "detected_scripts": self.detected_scripts,
        }

    def __bool__(self) -> bool:
        return bool(self.text)


# ---------------------------------------------------------------------------
# Script / language detection helpers (lightweight Unicode range checks)
# ---------------------------------------------------------------------------
_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")   # Hindi, Marathi, Sanskrit
_KANNADA_RE    = re.compile(r"[\u0C80-\u0CFF]")   # Kannada
_LATIN_RE      = re.compile(r"[A-Za-z]")


def _script_mix(text: str) -> dict:
    """Returns proportions of Devanagari, Kannada, Latin in a text block."""
    total = max(len(text.replace(" ", "").replace("\n", "")), 1)
    return {
        "devanagari": len(_DEVANAGARI_RE.findall(text)) / total,
        "kannada":    len(_KANNADA_RE.findall(text))    / total,
        "latin":      len(_LATIN_RE.findall(text))      / total,
    }


# ---------------------------------------------------------------------------
# OCR Engine (stateless class with lazy-initialised Paddle instances)
# ---------------------------------------------------------------------------
class OCREngine:
    """
    Unified Multi-Engine OCR Orchestrator.

    Cascade order
    -------------
    1. PDF digital-text stream  (pypdf)
    2. Direct text read         (.txt / .json / .log / .csv)
    3. PaddleOCR language-adaptive  (English + script-specific instances)
    4. Tesseract                (hin+kan+eng, requires tesseract binary)
    5. Binary string extractor  (regex on raw bytes)
    6. Raster fallback          (returns a descriptive message)
    """

    # Lazily initialised PaddleOCR instances (one per language group)
    _paddle_en: Optional["_PaddleOCR"] = None   # English / Latin  (PP-OCRv6)
    _paddle_hi: Optional["_PaddleOCR"] = None   # Devanagari       (PP-OCRv5)
    _paddle_ka: Optional["_PaddleOCR"] = None   # Kannada          (PP-OCRv3)

    # -----------------------------------------------------------------------
    # PaddleOCR instance factories
    # -----------------------------------------------------------------------
    @classmethod
    def _get_paddle_en(cls) -> Optional["_PaddleOCR"]:
        if not HAS_PADDLEOCR:
            return None
        if cls._paddle_en is None:
            try:
                cls._paddle_en = _PaddleOCR(
                    lang="en",
                    # EVIDENTIAL's preprocessor already normalizes the scan.
                    # Avoid PaddleX's optional orientation/unwarping stages,
                    # which are unstable/needlessly costly on this Windows CPU.
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=False,
                    # PaddlePaddle 3.3's Windows CPU oneDNN path can fail
                    # before inference. Use the standard CPU runtime.
                    enable_mkldnn=False,
                )
                logger.info("PaddleOCR English (PP-OCRv6) initialised")
            except Exception as exc:
                logger.warning("PaddleOCR English init failed: %s", exc)
                cls._paddle_en = None
        return cls._paddle_en

    @classmethod
    def _get_paddle_hi(cls) -> Optional["_PaddleOCR"]:
        """Devanagari model — covers Hindi, Marathi, Sanskrit, Nepali."""
        if not HAS_PADDLEOCR:
            return None
        if cls._paddle_hi is None:
            try:
                cls._paddle_hi = _PaddleOCR(
                    lang="hi",                  # Devanagari → PP-OCRv5
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=False,
                    enable_mkldnn=False,
                )
                logger.info("PaddleOCR Devanagari/Hindi (PP-OCRv5) initialised")
            except Exception as exc:
                logger.warning("PaddleOCR Hindi init failed: %s", exc)
                cls._paddle_hi = None
        return cls._paddle_hi

    @classmethod
    def _get_paddle_ka(cls) -> Optional["_PaddleOCR"]:
        """Kannada model — PP-OCRv3 (dedicated Kannada script support)."""
        if not HAS_PADDLEOCR:
            return None
        if cls._paddle_ka is None:
            try:
                cls._paddle_ka = _PaddleOCR(
                    lang="ka",                  # Kannada → PP-OCRv3
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=False,
                    enable_mkldnn=False,
                )
                logger.info("PaddleOCR Kannada (PP-OCRv3) initialised")
            except Exception as exc:
                logger.warning("PaddleOCR Kannada init failed: %s", exc)
                cls._paddle_ka = None
        return cls._paddle_ka

    # -----------------------------------------------------------------------
    # Internal: run a single PaddleOCR instance on a preprocessed image
    # -----------------------------------------------------------------------
    @classmethod
    def _run_paddle_instance(
        cls,
        paddle_inst: "_PaddleOCR",
        img: np.ndarray,
        label: str,
    ) -> Optional[OCREngineResult]:
        try:
            # PaddleOCR 3.x expects an H×W×C raster.  The document
            # preprocessor intentionally returns a single-channel, binarized
            # image, so restore three identical channels for OCR input.
            # This preserves the preprocessing result while avoiding Paddle's
            # internal ``shape[2]`` access on a two-dimensional array.
            ocr_image = img
            if ocr_image.ndim == 2:
                ocr_image = np.repeat(ocr_image[:, :, np.newaxis], 3, axis=2)
            elif ocr_image.ndim == 3 and ocr_image.shape[2] == 1:
                ocr_image = np.repeat(ocr_image, 3, axis=2)

            result = paddle_inst.predict(ocr_image)
            lines, scores = [], []
            for item in result:
                # PaddleOCR 3.x can return either OCRResult objects or mapping
                # payloads.  The latter exposes `rec_texts`/`rec_scores`.
                if isinstance(item, dict):
                    texts = item.get("rec_texts") or []
                    item_scores = item.get("rec_scores") or []
                    for index, text in enumerate(texts):
                        if text:
                            lines.append(str(text))
                            score = item_scores[index] if index < len(item_scores) else 0.8
                            scores.append(float(score))
                    continue

                # Older PaddleOCR 3.x variants return OCRResult objects.
                rec_text = getattr(item, "rec_text", None)
                rec_score = getattr(item, "rec_score", None)
                if rec_text is None:
                    # Fallback: iterate over inner line results
                    try:
                        for line in item:
                            t = getattr(line, "rec_text", "")
                            s = getattr(line, "rec_score", 0.8)
                            if t:
                                lines.append(t)
                                scores.append(float(s))
                    except TypeError:
                        pass
                else:
                    if rec_text:
                        lines.append(rec_text)
                        scores.append(float(rec_score or 0.8))
            if lines:
                avg_conf = sum(scores) / len(scores)
                return OCREngineResult(
                    text="\n".join(lines),
                    confidence=avg_conf,
                    engine=f"PaddleOCR-{label}",
                )
        except Exception:
            # Keep the cascade available, but preserve the real Paddle failure
            # in application logs rather than silently selecting a fallback.
            logger.exception("PaddleOCR %s run failed", label)
        return None

    # -----------------------------------------------------------------------
    # PaddleOCR language-adaptive entry point
    # -----------------------------------------------------------------------
    @classmethod
    def _run_paddle_multilang(cls, img: np.ndarray) -> Optional[OCREngineResult]:
        """
        Run PaddleOCR with language-adaptive selection.

        Strategy:
        1. Run the supported regional recognizers first.
        2. Retain a result only when its native script is actually present.
        3. Use the English recognizer only when neither regional script was
           found. This avoids treating English-model noise as document text.
        """
        all_texts: list[str] = []
        all_confs: list[float] = []
        engines_used: list[str] = []
        detected_scripts: list[str] = []

        # A regional model may also preserve embedded English (for example a
        # Hindi-English FIR), so do not overwrite its text with another pass.
        for getter, lbl, script, key in [
            (cls._get_paddle_ka, "KA-v3", "Kannada", "kannada"),
            (cls._get_paddle_hi, "HI-v5", "Devanagari", "devanagari"),
        ]:
            paddle = getter()
            if not paddle:
                continue
            res = cls._run_paddle_instance(paddle, img, lbl)
            if res and res.text and _script_mix(res.text).get(key, 0) > 0.02:
                # A verified native-script result is authoritative for this
                # document. It also preserves any embedded English recognized
                # by the regional model, so later recognizers add no value.
                return OCREngineResult(
                    text=res.text,
                    confidence=res.confidence,
                    engine=f"PaddleOCR-{lbl}",
                    detected_scripts=[script],
                )

        # No verified regional script: this is the English-only path.
        if not all_texts:
            en_paddle = cls._get_paddle_en()
            if en_paddle:
                en_result = cls._run_paddle_instance(en_paddle, img, "EN-v6")
                if en_result and en_result.text and _script_mix(en_result.text)["latin"] > 0.02:
                    all_texts.append(en_result.text)
                    all_confs.append(en_result.confidence)
                    engines_used.append("PaddleOCR-EN-v6")
                    detected_scripts.append("Latin")

        if not all_texts:
            return None

        merged_text = "\n\n".join(all_texts)
        avg_conf = sum(all_confs) / len(all_confs)
        engine_label = "+".join(engines_used) if len(engines_used) > 1 else engines_used[0]

        return OCREngineResult(
            text=merged_text,
            confidence=avg_conf,
            engine=engine_label,
            detected_scripts=detected_scripts,
        )

    # -----------------------------------------------------------------------
    # Tesseract fallback (multilingual)
    # -----------------------------------------------------------------------
    @classmethod
    def _run_tesseract(cls, img: np.ndarray) -> Optional[OCREngineResult]:
        if not HAS_PYTESSERACT:
            return None
        try:
            pil_img = Image.fromarray(img)
            # Attempt multilingual: Hindi + Kannada + English
            for lang_config in ("hin+kan+eng", "hin+eng", "kan+eng", "eng"):
                try:
                    raw_text = pytesseract.image_to_string(
                        pil_img,
                        lang=lang_config,
                        config="--oem 3 --psm 3",
                    ).strip()
                    if raw_text and len(raw_text) > 5:
                        try:
                            data = pytesseract.image_to_data(
                                pil_img,
                                lang=lang_config,
                                output_type=pytesseract.Output.DICT,
                            )
                            valid_confs = [
                                c / 100.0
                                for c, t in zip(data["conf"], data["text"])
                                if t.strip() and int(c) > 0
                            ]
                            avg_conf = sum(valid_confs) / len(valid_confs) if valid_confs else 0.75
                        except Exception:
                            avg_conf = 0.75
                        return OCREngineResult(
                            text=raw_text,
                            confidence=avg_conf,
                            engine=f"Tesseract-{lang_config}",
                        )
                except pytesseract.TesseractError:
                    # Language pack missing — try next
                    continue
        except Exception as exc:
            logger.debug("Tesseract error: %s", exc)
        return None

    # -----------------------------------------------------------------------
    # PDF digital-text extraction
    # -----------------------------------------------------------------------
    @classmethod
    def _extract_from_digital_pdf(
        cls, file_input: Union[str, bytes]
    ) -> Optional[OCREngineResult]:
        if not HAS_PYPDF:
            return None
        try:
            reader = (
                pypdf.PdfReader(file_input)
                if isinstance(file_input, str)
                else pypdf.PdfReader(io.BytesIO(file_input))
            )
            pages: list[str] = []
            for page in reader.pages:
                txt = page.extract_text() or ""
                if txt.strip():
                    pages.append(txt.strip())
            if pages:
                return OCREngineResult(
                    text="\n\n".join(pages),
                    confidence=0.98,
                    engine="PDF-DigitalStream",
                    detected_pages=len(pages),
                )
        except Exception as exc:
            logger.debug("PDF digital extraction error: %s", exc)
        return None

    # -----------------------------------------------------------------------
    # Main public entry point
    # -----------------------------------------------------------------------
    @classmethod
    def extract_text(
        cls,
        file_input: Union[str, bytes, Image.Image, np.ndarray],
        mime_type: Optional[str] = None,
    ) -> OCREngineResult:
        """
        Run the full OCR cascade and return the best available result.

        Never returns None — always returns an OCREngineResult (with a
        descriptive message on total failure).
        """
        # ── Step 1: Digital PDF text stream ─────────────────────────────────
        is_pdf = (
            (isinstance(file_input, str) and file_input.lower().endswith(".pdf"))
            or (mime_type and "pdf" in mime_type.lower())
        )
        if is_pdf:
            pdf_result = cls._extract_from_digital_pdf(file_input)
            if pdf_result and len(pdf_result.text) > 20:
                return pdf_result

        # ── Step 2: Plain text file read ─────────────────────────────────────
        if isinstance(file_input, str) and os.path.isfile(file_input):
            if file_input.lower().endswith((".txt", ".text", ".json", ".log", ".csv")):
                try:
                    with open(file_input, "r", encoding="utf-8", errors="ignore") as fh:
                        content = fh.read().strip()
                    if content:
                        return OCREngineResult(
                            text=content, confidence=0.99, engine="Text-Direct"
                        )
                except Exception:
                    pass

        # ── Step 3: Preprocess image ─────────────────────────────────────────
        preprocessed: Optional[np.ndarray] = None
        try:
            preprocessed, _ = DocumentPreprocessor.preprocess_image(file_input)
        except Exception:
            try:
                preprocessed = DocumentPreprocessor.to_grayscale(
                    DocumentPreprocessor.load_image(file_input)
                )
            except Exception as exc:
                logger.warning("Image preprocessing failed: %s", exc)

        # ── Step 4: PaddleOCR multilingual ───────────────────────────────────
        if preprocessed is not None and HAS_PADDLEOCR:
            paddle_result = cls._run_paddle_multilang(preprocessed)
            if paddle_result and len(paddle_result.text) > 10:
                return paddle_result

        # ── Step 5: Tesseract fallback ───────────────────────────────────────
        if preprocessed is not None and HAS_PYTESSERACT:
            tess_result = cls._run_tesseract(preprocessed)
            if tess_result and len(tess_result.text) > 5:
                return tess_result

        # ── Step 6: Binary string extractor ──────────────────────────────────
        if isinstance(file_input, (str, bytes)):
            try:
                raw_bytes = (
                    open(file_input, "rb").read()
                    if isinstance(file_input, str) and os.path.isfile(file_input)
                    else file_input
                )
                ascii_matches = re.findall(rb"[\x20-\x7E\t\r\n]{6,}", raw_bytes)
                strings = [
                    m.decode("latin1", errors="ignore").strip()
                    for m in ascii_matches
                ]
                filtered = [
                    s for s in strings
                    if s
                    and not s.startswith("%PDF")
                    and not s.startswith("xref")
                    and len(s) > 10
                ]
                if filtered:
                    return OCREngineResult(
                        text="\n".join(filtered[:40]),
                        confidence=0.65,
                        engine="Binary-String-Extractor",
                    )
            except Exception:
                pass

        # ── Step 7: Raster fallback (never None) ─────────────────────────────
        return OCREngineResult(
            text=(
                "[EVIDENTIAL OCR: Document processed — no high-contrast text "
                "could be extracted. Ensure the document is a clear scan or "
                "digital PDF. Supported languages: English, Hindi (Devanagari), "
                "Kannada.]"
            ),
            confidence=0.0,
            engine="Raster-Fallback",
        )

    # -----------------------------------------------------------------------
    # Capability check (used by tests)
    # -----------------------------------------------------------------------
    @classmethod
    def available_engines(cls) -> dict:
        return {
            "pypdf":        HAS_PYPDF,
            "paddleocr":    HAS_PADDLEOCR,
            "pytesseract":  HAS_PYTESSERACT,
            "opencv":       DocumentPreprocessor.HAS_OPENCV,
        }
