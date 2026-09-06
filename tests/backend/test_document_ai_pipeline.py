import io
import os
import pytest
import numpy as np
from PIL import Image

from ai.classification.classifier import DocumentClassifier
from ai.nlp.entity_extractor import EntityExtractor
from ai.nlp.language_detector import LanguageDetector
from ai.nlp.translator import DocumentTranslator
from ai.ocr.preprocessor import DocumentPreprocessor
from ai.pipeline import DocumentAIPipeline
from backend.app.models.case import Case, CasePriority, CaseStatus
from backend.app.models.document import Document, DocumentProcessingStatus, DocumentTranslation
from backend.app.models.entity import ExtractedEntity, EntityType
from backend.app.models.user import User, UserRole


def test_opencv_preprocessing_suite():
    """Test OpenCV preprocessing transformations: grayscale, denoising, binarization, and deskewing."""
    # Create test RGB image
    img_array = np.zeros((100, 100, 3), dtype=np.uint8)
    img_array[30:70, 30:70] = [255, 255, 255]

    # Preprocessing
    processed, meta = DocumentPreprocessor.preprocess_image(img_array)
    assert processed is not None
    assert len(processed.shape) == 2  # Grayscale/binary
    assert "skew_angle_deg" in meta
    assert "engine" in meta


def test_language_detection_multilingual():
    """Test script and language detection across Indian regional languages."""
    # 1. English
    lang, conf = LanguageDetector.detect_language("First Information Report filed at Cyber Police Station New Delhi.")
    assert lang == "English"
    assert conf >= 0.70

    # 2. Hindi (Devanagari)
    hindi_text = "थाना कोतवाली में भारतीय दण्ड संहिता की धारा 420 के तहत अपराध दर्ज किया गया।"
    lang, conf = LanguageDetector.detect_language(hindi_text)
    assert lang == "Hindi"
    assert conf >= 0.70

    # 3. Marathi
    marathi_text = "पोलीस ठाणे येथे गुन्हा नोंदणी करण्यात आली आहे. तक्रारदार उपस्थित आहेत."
    lang, conf = LanguageDetector.detect_language(marathi_text)
    assert lang == "Marathi"
    assert conf >= 0.70

    # 4. Bengali
    bengali_text = "কলকাতা পুলিশ থানায় অভিযোগ দায়ের করা হয়েছে।"
    lang, conf = LanguageDetector.detect_language(bengali_text)
    assert lang == "Bengali"
    assert conf >= 0.70


def get_token(client, email="officer1@evidential.gov.in", password="Officer1@123"):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_legal_translation_separation(db_session):
    """Test that regional document translation translates legal vocabulary while leaving original text intact."""
    hindi_fir = "प्राथमिकी संख्या 108/2024 थाना साइबर सेल। अभियुक्त: राजेश कुमार। धारा 420 भा.दं.सं. एवं 66D IT Act।"
    
    translated, model = DocumentTranslator.translate_to_english(hindi_fir, source_language="Hindi")
    assert "First Information Report" in translated or "Police Station" in translated or "Accused" in translated
    assert model in {
        "OPUS-MT-Inc-En",
        "Legal-NLP-Translator-v3-Fallback",
    }


def test_entity_extraction_all_11_types():
    """Test comprehensive extraction of all 11 required entity categories."""
    synthetic_fir_text = """
    FIRST INFORMATION REPORT
    FIR Number: FIR-2024-8849
    Police Station: Cyber Crime Police Station, New Delhi
    Incident Date: 15/08/2024
    
    Complainant: Shri Rajesh Sharma, Email: rajesh.sharma@example.com, Mobile: +91-9876543210
    Accused: Suresh Verma, operating with Vehicle Number DL-01-AB-1234
    
    Crime Summary:
    The accused committed CYBER_FRAUD by duping victims into transferring funds from State Bank of India
    to illicit bank accounts in Connaught Place, New Delhi.
    
    Offense Registered Under: Section 420 IPC and Section 66D IT Act.
    """

    entities = EntityExtractor.extract_entities(synthetic_fir_text)
    entity_types_found = {e.entity_type for e in entities}

    # Verify that all 11 entity types are detected
    assert "CASE_NUMBER" in entity_types_found
    assert "POLICE_STATION" in entity_types_found
    assert "DATE" in entity_types_found
    assert "PERSON" in entity_types_found
    assert "EMAIL" in entity_types_found
    assert "PHONE" in entity_types_found
    assert "VEHICLE" in entity_types_found
    assert "CRIME_TYPE" in entity_types_found
    assert "ORGANIZATION" in entity_types_found
    assert "LOCATION" in entity_types_found
    assert "LAW_SECTION" in entity_types_found

    # Check specific values
    phone_ent = next(e for e in entities if e.entity_type == "PHONE")
    assert "9876543210" in phone_ent.normalized_value

    vehicle_ent = next(e for e in entities if e.entity_type == "VEHICLE")
    assert "DL01AB1234" in vehicle_ent.normalized_value or "DL-01-AB-1234" in vehicle_ent.entity_value

    law_ent = next(e for e in entities if e.entity_type == "LAW_SECTION")
    assert "420" in law_ent.normalized_value or "66D" in law_ent.normalized_value


def test_crime_classification_taxonomy():
    """Test document and crime taxonomy classification."""
    # Cyber crime text
    cyber_text = "Phishing attack and unauthorized OTP debit of Rs 500,000 under Section 66D IT Act and 420 IPC."
    cyber_res = DocumentClassifier.classify_document(cyber_text)
    assert cyber_res.primary_category == "CYBER_CRIME"
    assert cyber_res.confidence >= 0.70

    # Violent crime text
    violent_text = "Homicide and armed robbery with fatal gunshot wounds registered under Section 302 IPC and 394 IPC."
    violent_res = DocumentClassifier.classify_document(violent_text)
    assert violent_res.primary_category == "VIOLENT_CRIME"
    assert violent_res.recommended_priority == "CRITICAL"


def test_full_ai_pipeline_execution(client, db_session):
    """End-to-end integration test: Case -> Document Upload -> Process AI Pipeline -> Output Verification."""
    investigator = db_session.query(User).filter(User.email == "officer1@evidential.gov.in").first()

    # 1. Create a Case
    case = Case(
        case_number="FIR-AI-2024-001",
        title="Cross-Jurisdiction Banking Scam",
        crime_type="CYBER_CRIME",
        status=CaseStatus.UNDER_INVESTIGATION,
        priority=CasePriority.HIGH,
        created_by_id=investigator.id,
        assigned_officer_id=investigator.id,
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    # 2. Register Document
    sample_fir = """
    FIRST INFORMATION REPORT (FIR)
    FIR Number: FIR-2024-9901
    Police Station: Cyber Crime Cell, Bengaluru
    Incident Date: 12/07/2024
    
    Complainant: Smt Anita Desai, Mobile: 9845012345, Email: anita.desai@gov.in
    Accused: Vikram Singh, driving vehicle KA-05-MN-9999
    
    Offense:
    The accused orchestrated ONLINE_PHISHING and fraud targeting HDFC Bank customer accounts in Indiranagar, Bengaluru.
    Charges: Section 420 IPC and Section 66C IT Act.
    """

    doc = Document(
        case_id=case.id,
        filename="fir_sample.pdf",
        original_filename="fir_sample.pdf",
        file_path="storage/uploads/fir_sample.pdf",
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        uploaded_by_id=investigator.id,
        processing_status=DocumentProcessingStatus.QUEUED,
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    # 3. Process via DocumentAIPipeline
    processed = DocumentAIPipeline.process_document(
        document_id=doc.id,
        db=db_session,
        actor_user=investigator,
        override_text=sample_fir,
    )

    assert processed.processing_status == DocumentProcessingStatus.COMPLETED
    assert processed.detected_language == "English"
    assert processed.original_text is not None
    assert "FIR-2024-9901" in processed.original_text
    assert processed.error_message is None

    # Check entities in database
    db_entities = db_session.query(ExtractedEntity).filter(ExtractedEntity.document_id == doc.id).all()
    assert len(db_entities) >= 7

    found_types = {e.entity_type.value for e in db_entities}
    assert "PERSON" in found_types
    assert "PHONE" in found_types
    assert "EMAIL" in found_types
    assert "VEHICLE" in found_types
    assert "POLICE_STATION" in found_types
    assert "ORGANIZATION" in found_types


def test_pipeline_api_endpoint(client, db_session):
    """Test HTTP POST /api/v1/documents/{document_id}/process endpoint."""
    token = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token}"}
    investigator = db_session.query(User).filter(User.email == "officer1@evidential.gov.in").first()

    case = Case(
        case_number="FIR-API-2024-002",
        title="Securities Forgery Investigation",
        crime_type="FINANCIAL_FRAUD",
        created_by_id=investigator.id,
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    # Create dummy file
    os.makedirs("storage/uploads", exist_ok=True)
    test_file_path = "storage/uploads/test_scan.txt"
    sample_text = "FIR Number: FIR-2024-5555. Section 420 IPC cheating case at Kotwali Police Station, New Delhi on 10/01/2024."
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(sample_text)

    doc = Document(
        case_id=case.id,
        filename="test_scan.txt",
        original_filename="test_scan.txt",
        file_path=test_file_path,
        sha256_hash="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        uploaded_by_id=investigator.id,
        processing_status=DocumentProcessingStatus.QUEUED,
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    response = client.post(
        f"/api/v1/documents/{doc.id}/process",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["processing_status"] == "COMPLETED"
    assert data["detected_language"] == "English"
    assert len(data["entities"]) >= 3


def test_pipeline_error_handling_and_failed_status(client, db_session):
    """Test that missing or unreadable files mark status as FAILED and record error_message."""
    token = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token}"}
    investigator = db_session.query(User).filter(User.email == "officer1@evidential.gov.in").first()

    case = Case(
        case_number="FIR-ERR-2024-999",
        title="Malformed File Case",
        crime_type="OTHER",
        created_by_id=investigator.id,
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    # Document pointing to a non-existent file
    doc = Document(
        case_id=case.id,
        filename="non_existent.pdf",
        original_filename="non_existent.pdf",
        file_path="storage/uploads/non_existent_file_path_12345.pdf",
        sha256_hash="0000000000000000000000000000000000000000000000000000000000000000",
        uploaded_by_id=investigator.id,
        processing_status=DocumentProcessingStatus.QUEUED,
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    response = client.post(
        f"/api/v1/documents/{doc.id}/process",
        headers=headers,
    )
    assert response.status_code == 500

    db_session.refresh(doc)
    assert doc.processing_status == DocumentProcessingStatus.FAILED
    assert doc.error_message is not None
    assert "not found" in doc.error_message.lower()
