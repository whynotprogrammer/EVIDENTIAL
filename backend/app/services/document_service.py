import os
import re
import uuid
from typing import Tuple
from fastapi import HTTPException, UploadFile, status

from backend.app.core.config import settings
from backend.app.core.security import compute_sha256

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/pjpeg"}

MAGIC_BYTES = {
    "pdf": [b"%PDF"],
    "jpeg": [b"\xff\xd8\xff"],
    "png": [b"\x89PNG\r\n\x1a\n"],
}


def sanitize_filename(filename: str) -> str:
    """Sanitize original filename to prevent path traversal and shell injections."""
    # Strip directory components
    clean_name = os.path.basename(filename)
    # Remove null bytes, control chars, and path separators
    clean_name = re.sub(r"[\x00-\x1f\x7f/\\]", "", clean_name)
    # Replace whitespace and unsafe characters with underscores
    clean_name = re.sub(r"[^a-zA-Z0-9._-]", "_", clean_name)
    if not clean_name:
        clean_name = f"document_{uuid.uuid4().hex[:8]}"
    return clean_name


def validate_file(file: UploadFile, file_bytes: bytes) -> Tuple[str, str]:
    """
    Perform deep validation on uploaded FIR document:
    1. Check file size (> 0 and <= MAX_FILE_SIZE_MB)
    2. Check filename extension
    3. Check MIME content-type
    4. Inspect magic bytes header to detect malformed or disguised files
    """
    # 1. Size check
    file_size = len(file_bytes)
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File validation failed: File cannot be empty (0 bytes).",
        )
    
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File validation failed: File size ({file_size / (1024 * 1024):.1f} MB) exceeds maximum allowed limit of {settings.MAX_FILE_SIZE_MB} MB.",
        )

    # 2. Filename & extension check
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File validation failed: Missing filename.",
        )
    
    sanitized_name = sanitize_filename(file.filename)
    _, ext = os.path.splitext(sanitized_name.lower())
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File validation failed: Unsupported file extension '{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}.",
        )

    # 3. MIME Content-Type Check
    content_type = (file.content_type or "application/octet-stream").lower()
    if content_type not in ALLOWED_MIME_TYPES and content_type != "application/octet-stream":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File validation failed: Disallowed content-type '{content_type}'.",
        )

    # 4. Magic Bytes Inspection
    is_valid_header = False
    if ext == ".pdf":
        is_valid_header = file_bytes.startswith(b"%PDF")
    elif ext in [".jpg", ".jpeg"]:
        is_valid_header = file_bytes.startswith(b"\xff\xd8\xff")
    elif ext == ".png":
        is_valid_header = file_bytes.startswith(b"\x89PNG\r\n\x1a\n")

    if not is_valid_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File validation failed: File header is corrupted or does not match extension '{ext}'.",
        )

    return sanitized_name, ext


def save_fir_document(case_id: int, original_name: str, ext: str, file_bytes: bytes) -> Tuple[str, str, str]:
    """
    Store FIR document immutably on disk.
    Returns (unique_filename, relative_file_path, sha256_hash).
    """
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_hash = compute_sha256(file_bytes)
    
    unique_id = uuid.uuid4().hex[:12]
    stored_filename = f"case_{case_id}_{unique_id}_{original_name}"
    full_path = os.path.join(settings.UPLOAD_DIR, stored_filename)

    with open(full_path, "wb") as f:
        f.write(file_bytes)

    return stored_filename, full_path, file_hash
