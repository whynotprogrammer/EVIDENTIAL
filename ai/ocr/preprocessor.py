import io
import math
import os
from typing import List, Optional, Tuple, Union
import numpy as np
from PIL import Image

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


class DocumentPreprocessor:
    """
    OpenCV and PIL-based document preprocessing pipeline for legal & FIR scans.
    Optimizes contrast, binarization, deskewing, and noise reduction for OCR engines.
    """

    # Expose availability for external capability checks
    HAS_OPENCV: bool = HAS_OPENCV

    @classmethod
    def load_image(cls, image_input: Union[str, bytes, Image.Image, np.ndarray]) -> np.ndarray:
        """Loads an image into a BGR/Grayscale NumPy array."""
        if isinstance(image_input, np.ndarray):
            return image_input.copy()
        
        if isinstance(image_input, Image.Image):
            rgb = np.array(image_input.convert("RGB"))
            if HAS_OPENCV:
                return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            return rgb
        
        if isinstance(image_input, bytes):
            pil_img = Image.open(io.BytesIO(image_input))
            rgb = np.array(pil_img.convert("RGB"))
            if HAS_OPENCV:
                return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            return rgb
        
        if isinstance(image_input, str) and os.path.exists(image_input):
            if HAS_OPENCV:
                img = cv2.imread(image_input)
                if img is not None:
                    return img
            pil_img = Image.open(image_input)
            rgb = np.array(pil_img.convert("RGB"))
            if HAS_OPENCV:
                return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            return rgb
        
        raise ValueError(f"Unsupported or invalid image input: {type(image_input)}")

    @classmethod
    def to_grayscale(cls, img: np.ndarray) -> np.ndarray:
        """Converts image to 8-bit single-channel grayscale."""
        if len(img.shape) == 2:
            return img
        if HAS_OPENCV:
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # PIL/NumPy fallback
        return np.dot(img[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.uint8)

    @classmethod
    def denoise(cls, gray_img: np.ndarray) -> np.ndarray:
        """Applies noise reduction suitable for degraded carbon copies and scans."""
        if HAS_OPENCV:
            # Median blur preserves character edges while removing salt-and-pepper noise
            return cv2.medianBlur(gray_img, 3)
        return gray_img

    @classmethod
    def enhance_contrast(cls, gray_img: np.ndarray) -> np.ndarray:
        """Applies Contrast Limited Adaptive Histogram Equalization (CLAHE)."""
        if HAS_OPENCV:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            return clahe.apply(gray_img)
        # Fallback linear normalization
        min_v, max_v = np.min(gray_img), np.max(gray_img)
        if max_v > min_v:
            return (((gray_img - min_v) / (max_v - min_v)) * 255).astype(np.uint8)
        return gray_img

    @classmethod
    def binarize_adaptive(cls, gray_img: np.ndarray) -> np.ndarray:
        """Applies Otsu + Adaptive Gaussian thresholding for optimal OCR text clarity."""
        if HAS_OPENCV:
            # First attempt Otsu thresholding
            _, otsu = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            return otsu
        
        # NumPy thresholding fallback
        thresh = int(np.mean(gray_img))
        binary = np.where(gray_img > thresh, 255, 0).astype(np.uint8)
        return binary

    @classmethod
    def detect_and_correct_skew(cls, gray_img: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Detects skew angle of text lines using OpenCV contour analysis and rotates the image.
        Returns (corrected_image, angle_degrees).
        """
        if not HAS_OPENCV:
            return gray_img, 0.0

        try:
            # Invert colors: text = white, background = black
            thresh = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
            coords = np.column_stack(np.where(thresh > 0))
            if len(coords) < 50:
                return gray_img, 0.0

            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            elif angle > 45:
                angle = 90 - angle
            else:
                angle = -angle

            # Restrict skew corrections to reasonable document angles (-20 to +20 degrees)
            if abs(angle) > 25 or abs(angle) < 0.2:
                return gray_img, 0.0

            (h, w) = gray_img.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(
                gray_img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
            )
            return rotated, float(angle)
        except Exception:
            return gray_img, 0.0

    @classmethod
    def preprocess_image(cls, image_input: Union[str, bytes, Image.Image, np.ndarray]) -> Tuple[np.ndarray, dict]:
        """
        Executes full OpenCV preprocessing pipeline.
        Returns (processed_image_ndarray, metadata_dict).
        """
        img = cls.load_image(image_input)
        gray = cls.to_grayscale(img)
        denoised = cls.denoise(gray)
        enhanced = cls.enhance_contrast(denoised)
        deskewed, skew_angle = cls.detect_and_correct_skew(enhanced)
        binarized = cls.binarize_adaptive(deskewed)

        metadata = {
            "original_shape": img.shape,
            "processed_shape": binarized.shape,
            "skew_angle_deg": round(skew_angle, 2),
            "engine": "OpenCV-Adaptive" if HAS_OPENCV else "PIL-Fallback",
        }
        return binarized, metadata

    @classmethod
    def extract_pdf_images_or_text(cls, pdf_path_or_bytes: Union[str, bytes]) -> List[Image.Image]:
        """
        Extracts pages or embedded images from a PDF file as PIL Images for OCR.
        """
        images: List[Image.Image] = []
        
        try:
            if HAS_PYPDF:
                reader = (
                    pypdf.PdfReader(pdf_path_or_bytes)
                    if isinstance(pdf_path_or_bytes, str)
                    else pypdf.PdfReader(io.BytesIO(pdf_path_or_bytes))
                )
                for page in reader.pages:
                    for img_file in page.images:
                        pil_img = Image.open(io.BytesIO(img_file.data))
                        images.append(pil_img)
        except Exception:
            pass

        return images
