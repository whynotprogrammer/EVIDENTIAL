from backend.app.models.user import User, UserRole
from backend.app.models.case import Case, CaseStatus, CasePriority
from backend.app.models.document import Document, DocumentTranslation, DocumentProcessingStatus
from backend.app.models.entity import ExtractedEntity, EntityType
from backend.app.models.evidence import Evidence, EvidenceType, VerificationStatus
from backend.app.models.audit import AuditEvent, AuditAction, AuditStatus
from backend.app.core.security import get_password_hash, compute_sha256


def test_user_creation(db_session):
    user = User(
        email="custom_officer@evidential.gov.in",
        hashed_password=get_password_hash("Secret@123"),
        full_name="Custom Officer Test",
        badge_number="TEST-999",
        role=UserRole.INVESTIGATOR,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.email == "custom_officer@evidential.gov.in"
    assert user.role == UserRole.INVESTIGATOR
    assert user.is_active is True


def test_case_and_relationships(db_session):
    user = User(
        email="lead_investigator@evidential.gov.in",
        hashed_password=get_password_hash("Secret@123"),
        full_name="Lead Investigator",
        role=UserRole.INVESTIGATOR,
    )
    db_session.add(user)
    db_session.commit()

    case = Case(
        case_number="FIR-2024-TEST-002",
        title="Armed Robbery at Jewellers",
        crime_type="Armed Robbery",
        status=CaseStatus.UNDER_INVESTIGATION,
        priority=CasePriority.CRITICAL,
        police_station="Kotwali Police Station",
        location="Sector 18 Market",
        assigned_officer_id=user.id,
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    assert case.id is not None
    assert case.assigned_officer.email == "lead_investigator@evidential.gov.in"

    # Add Document
    doc = Document(
        case_id=case.id,
        filename="fir_002_scanned.pdf",
        original_filename="fir_002_scanned.pdf",
        file_path="/storage/uploads/fir_002_scanned.pdf",
        sha256_hash=compute_sha256(b"raw document content"),
        detected_language="Hindi",
        original_text="यह एक प्राथमिकी प्रति है",
        processing_status=DocumentProcessingStatus.COMPLETED,
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    assert doc.id is not None
    assert doc.case_id == case.id
    assert doc.detected_language == "Hindi"

    # Add Translation
    trans = DocumentTranslation(
        document_id=doc.id,
        source_language="Hindi",
        target_language="English",
        translated_text="This is an official first information report copy",
    )
    db_session.add(trans)
    db_session.commit()
    db_session.refresh(trans)

    assert len(doc.translations) == 1
    assert doc.translations[0].translated_text.startswith("This is an official")

    # Add Extracted Entity
    entity = ExtractedEntity(
        case_id=case.id,
        document_id=doc.id,
        entity_type=EntityType.VEHICLE,
        entity_value="UP32AB1234",
        normalized_value="UP32AB1234",
        confidence=0.98,
    )
    db_session.add(entity)
    db_session.commit()

    assert len(case.entities) == 1
    assert case.entities[0].entity_value == "UP32AB1234"

    # Add Evidence with SHA-256
    file_bytes = b"Digital CCTV footage binary dump"
    file_hash = compute_sha256(file_bytes)
    evidence = Evidence(
        case_id=case.id,
        title="CCTV Market Alleyway",
        evidence_type=EvidenceType.VIDEO,
        sha256_hash=file_hash,
        verification_status=VerificationStatus.VALID,
        uploaded_by_id=user.id,
    )
    db_session.add(evidence)
    db_session.commit()

    assert len(case.evidence_items) == 1
    assert case.evidence_items[0].sha256_hash == file_hash


def test_audit_logging(db_session):
    audit = AuditEvent(
        user_email="admin@evidential.gov.in",
        action=AuditAction.CASE_CREATED,
        resource_type="CASE",
        resource_id="1",
        details="New case created",
        status=AuditStatus.SUCCESS,
    )
    db_session.add(audit)
    db_session.commit()
    db_session.refresh(audit)

    assert audit.id is not None
    assert audit.action == AuditAction.CASE_CREATED
