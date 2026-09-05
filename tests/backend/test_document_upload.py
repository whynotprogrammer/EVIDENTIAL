import io
import os
import uuid
import pytest


def get_token(client, email, password):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture
def test_case(client):
    token = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    unique_case_num = f"FIR-2024-DOC-{uuid.uuid4().hex[:8]}"
    res = client.post(
        "/api/v1/cases",
        json={
            "case_number": unique_case_num,
            "title": "Document Upload Validation Case",
            "crime_type": "Digital Forensic Intake",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    return res.json()


def test_valid_pdf_upload(client, test_case):
    """Verify valid PDF upload computes SHA-256 and creates Document and DocumentVersion."""
    token = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token}"}
    case_id = test_case["id"]

    pdf_content = b"%PDF-1.5\n%Valid simulated police FIR report content binary payload"
    files = {"file": ("official_fir_copy.pdf", io.BytesIO(pdf_content), "application/pdf")}

    response = client.post(f"/api/v1/cases/{case_id}/documents/upload", files=files, headers=headers)
    assert response.status_code == 201
    data = response.json()

    assert data["original_filename"] == "official_fir_copy.pdf"
    assert data["case_id"] == case_id
    assert data["mime_type"] == "application/pdf"
    assert data["processing_status"] == "PENDING"
    assert len(data["sha256_hash"]) == 64
    assert len(data["versions"]) == 1
    assert data["versions"][0]["version_number"] == 1
    assert data["versions"][0]["sha256_hash"] == data["sha256_hash"]


def test_valid_image_uploads_jpg_png(client, test_case):
    """Verify valid JPEG and PNG uploads succeed."""
    token = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token}"}
    case_id = test_case["id"]

    # 1. Valid JPG (SOI marker \xff\xd8\xff)
    jpg_content = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00\x60\x00\x60\x00\x00"
    files_jpg = {"file": ("scanned_fir.jpg", io.BytesIO(jpg_content), "image/jpeg")}
    res_jpg = client.post(f"/api/v1/cases/{case_id}/documents/upload", files=files_jpg, headers=headers)
    assert res_jpg.status_code == 201
    assert res_jpg.json()["mime_type"] == "image/jpeg"

    # 2. Valid PNG (PNG magic bytes)
    png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    files_png = {"file": ("fir_evidence.png", io.BytesIO(png_content), "image/png")}
    res_png = client.post(f"/api/v1/cases/{case_id}/documents/upload", files=files_png, headers=headers)
    assert res_png.status_code == 201
    assert res_png.json()["mime_type"] == "image/png"


def test_malformed_file_rejected(client, test_case):
    """Verify files with spoofed extensions or corrupted headers are rejected."""
    token = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token}"}
    case_id = test_case["id"]

    # Spoofed PDF (has .pdf extension but content is random plaintext without %PDF header)
    fake_pdf = b"This is a fake document without magic PDF signature"
    files = {"file": ("corrupted.pdf", io.BytesIO(fake_pdf), "application/pdf")}
    res = client.post(f"/api/v1/cases/{case_id}/documents/upload", files=files, headers=headers)
    assert res.status_code == 400
    assert "File header is corrupted" in res.json()["detail"]


def test_disallowed_extension_rejected(client, test_case):
    """Verify dangerous or unsupported file types (e.g. .exe, .sh) are rejected."""
    token = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token}"}
    case_id = test_case["id"]

    exe_bytes = b"MZ\x90\x00\x03\x00\x00\x00"
    files = {"file": ("malware_payload.exe", io.BytesIO(exe_bytes), "application/x-msdownload")}
    res = client.post(f"/api/v1/cases/{case_id}/documents/upload", files=files, headers=headers)
    assert res.status_code == 400
    assert "Unsupported file extension" in res.json()["detail"]


def test_empty_file_rejected(client, test_case):
    """Verify 0-byte file is rejected."""
    token = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token}"}
    case_id = test_case["id"]

    files = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}
    res = client.post(f"/api/v1/cases/{case_id}/documents/upload", files=files, headers=headers)
    assert res.status_code == 400
    assert "File cannot be empty" in res.json()["detail"]


def test_unauthorized_document_upload(client, test_case):
    """Verify unassigned officer cannot upload documents to another officer's case."""
    token_off2 = get_token(client, "officer2@evidential.gov.in", "Officer2@123")
    headers = {"Authorization": f"Bearer {token_off2}"}
    case_id = test_case["id"]

    pdf_content = b"%PDF-1.4\nUnauthorized document upload payload"
    files = {"file": ("unauthorized.pdf", io.BytesIO(pdf_content), "application/pdf")}
    res = client.post(f"/api/v1/cases/{case_id}/documents/upload", files=files, headers=headers)
    assert res.status_code == 403
    assert "Unauthorized" in res.json()["detail"]


def test_document_listing_and_download(client, test_case):
    """Verify documents can be listed and downloaded."""
    token = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token}"}
    case_id = test_case["id"]

    pdf_content = b"%PDF-1.4\nDownloadable verified FIR report payload"
    files = {"file": ("fir_to_download.pdf", io.BytesIO(pdf_content), "application/pdf")}
    upload_res = client.post(f"/api/v1/cases/{case_id}/documents/upload", files=files, headers=headers)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # 1. List case documents
    list_res = client.get(f"/api/v1/cases/{case_id}/documents", headers=headers)
    assert list_res.status_code == 200
    docs = list_res.json()
    assert len(docs) >= 1
    assert any(d["id"] == doc_id for d in docs)

    # 2. Download document
    dl_res = client.get(f"/api/v1/documents/{doc_id}/download", headers=headers)
    assert dl_res.status_code == 200
    assert dl_res.content == pdf_content


def test_document_immutability(client, test_case):
    """Verify re-uploading documents never overwrites existing documents or files."""
    token = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token}"}
    case_id = test_case["id"]

    content1 = b"%PDF-1.4\nDocument Version 1 Content"
    files1 = {"file": ("report.pdf", io.BytesIO(content1), "application/pdf")}
    res1 = client.post(f"/api/v1/cases/{case_id}/documents/upload", files=files1, headers=headers)
    assert res1.status_code == 201
    doc1_data = res1.json()

    content2 = b"%PDF-1.4\nDocument Version 2 New Content"
    files2 = {"file": ("report.pdf", io.BytesIO(content2), "application/pdf")}
    res2 = client.post(f"/api/v1/cases/{case_id}/documents/upload", files=files2, headers=headers)
    assert res2.status_code == 201
    doc2_data = res2.json()

    # Both documents exist independently with unique filenames and different SHA-256 hashes
    assert doc1_data["id"] != doc2_data["id"]
    assert doc1_data["filename"] != doc2_data["filename"]
    assert doc1_data["sha256_hash"] != doc2_data["sha256_hash"]
    assert os.path.exists(doc1_data["file_path"])
    assert os.path.exists(doc2_data["file_path"])
