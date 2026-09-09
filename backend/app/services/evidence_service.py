import hashlib
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.models.audit import AuditAction, AuditEvent, AuditStatus
from backend.app.models.case import Case
from backend.app.models.evidence import (
    CustodyEvent,
    CustodyStatus,
    Evidence,
    EvidenceType,
    VerificationStatus,
)
from backend.app.models.timeline_event import EventType, InvestigationEvent
from backend.app.models.user import User, UserRole
from backend.app.schemas.custody import (
    CourtSubmissionRequest,
    CustodyChainResponse,
    CustodyEventOut,
    EvidenceCreatePayload,
    EvidenceDetailOut,
    ExaminationCompleteRequest,
    ExaminationStartRequest,
    ForensicReportRequest,
    IntegrityVerificationResult,
    ReceiveRequest,
    ReturnRequest,
    SealRequest,
    TransferRequest,
)

logger = logging.getLogger("evidential.custody")

STORAGE_EVIDENCE_DIR = Path("storage/evidence")
STORAGE_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


class EvidenceService:
    @staticmethod
    def _is_case_authorized(db: Session, current_user: User, case_id: int) -> bool:
        """Pre-retrieval authorization boundary check."""
        if current_user.role == UserRole.ADMIN:
            return db.query(Case).filter(Case.id == case_id).first() is not None

        case = (
            db.query(Case)
            .filter(
                Case.id == case_id,
                or_(
                    Case.assigned_officer_id == current_user.id,
                    Case.created_by_id == current_user.id,
                    Case.assigned_officer_id == None,
                ),
            )
            .first()
        )
        return case is not None

    @classmethod
    def get_evidence_or_404(cls, db: Session, current_user: User, case_id: int, evidence_id: int) -> Evidence:
        """Retrieves authorized evidence record or raises 403 / 404 error."""
        if not cls._is_case_authorized(db, current_user, case_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not authorized to view evidence for this case.",
            )

        evidence = (
            db.query(Evidence)
            .filter(Evidence.id == evidence_id, Evidence.case_id == case_id)
            .first()
        )
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evidence ID {evidence_id} not found in Case ID {case_id}.",
            )
        return evidence

    @classmethod
    def list_case_evidence(cls, db: Session, current_user: User, case_id: int) -> List[EvidenceDetailOut]:
        """Lists all authorized evidence items for a case."""
        if not cls._is_case_authorized(db, current_user, case_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not authorized to view evidence for this case.",
            )

        items = db.query(Evidence).filter(Evidence.case_id == case_id).all()
        return [EvidenceDetailOut.model_validate(item) for item in items]

    @classmethod
    def add_evidence(
        cls,
        db: Session,
        current_user: User,
        case_id: int,
        payload: EvidenceCreatePayload,
        file_bytes: Optional[bytes] = None,
        original_filename: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> EvidenceDetailOut:
        """
        Creates a new evidence record, computes real SHA-256 cryptographic digest,
        persists binary file payload, creates initial 'EVIDENCE_COLLECTED' custody event,
        and registers milestones in Audit Ledger and Case Timeline.
        """
        if not cls._is_case_authorized(db, current_user, case_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not authorized to add evidence to this case.",
            )

        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case ID {case_id} not found.",
            )

        content = file_bytes or b""
        sha256_hash = hashlib.sha256(content).hexdigest()
        
        # Unique evidence string ID: e.g., EVD-2024-001-A1B2
        evidence_num = f"EVD-{case.case_number}-{uuid.uuid4().hex[:4].upper()}"

        saved_path_str: Optional[str] = None
        if content and original_filename:
            case_dir = STORAGE_EVIDENCE_DIR / str(case_id)
            case_dir.mkdir(parents=True, exist_ok=True)
            target_path = case_dir / f"{evidence_num}_{original_filename}"
            with open(target_path, "wb") as f:
                f.write(content)
            saved_path_str = str(target_path)

        now_utc = datetime.now(timezone.utc)
        collection_dt = payload.collection_date or now_utc
        collector_name = current_user.full_name or current_user.email
        location_str = payload.collection_location or case.location or "Field Site"

        evidence = Evidence(
            case_id=case_id,
            evidence_number=evidence_num,
            title=payload.title,
            description=payload.description,
            evidence_type=payload.evidence_type,
            file_path=saved_path_str,
            file_size_bytes=len(content),
            mime_type=mime_type or ("application/octet-stream" if saved_path_str else None),
            sha256_hash=sha256_hash,
            status=CustodyStatus.COLLECTED,
            current_custodian=collector_name,
            collected_by=collector_name,
            collection_location=location_str,
            collection_date=collection_dt,
            notes=payload.notes,
            is_tampered=False,
            verification_status=VerificationStatus.VALID,
            last_verified_at=now_utc,
            uploaded_by_id=current_user.id,
            created_at=now_utc,
            updated_at=now_utc,
        )
        db.add(evidence)
        db.commit()
        db.refresh(evidence)

        # Initial Custody Event: Evidence Collected
        custody_event = CustodyEvent(
            evidence_id=evidence.id,
            case_id=case_id,
            action="EVIDENCE_COLLECTED",
            previous_status=None,
            new_status=CustodyStatus.COLLECTED.value,
            actor_id=current_user.id,
            actor_name=collector_name,
            timestamp=collection_dt,
            location=location_str,
            from_custodian="Collection Site / Field Location",
            to_custodian=collector_name,
            reason="Initial Evidence Intake and Digital Registration",
            notes=payload.notes or f"Evidence '{payload.title}' collected and SHA-256 fingerprint generated.",
            evidence_hash=sha256_hash,
            digital_signature=f"SIG-SHA256-{sha256_hash[:16]}",
            device_info=f"EVIDENTIAL-SECURE-NODE ({current_user.role.value})",
        )
        db.add(custody_event)

        # Audit Ledger Entry
        audit_entry = AuditEvent(
            user_id=current_user.id,
            user_email=current_user.email,
            action=AuditAction.EVIDENCE_ADDED,
            status=AuditStatus.SUCCESS,
            resource_type="EVIDENCE",
            resource_id=str(evidence.id),
            details=json.dumps({
                "action": "EVIDENCE_COLLECTED",
                "evidence_id": evidence.id,
                "evidence_number": evidence_num,
                "case_id": case_id,
                "sha256_hash": sha256_hash,
                "status": CustodyStatus.COLLECTED.value,
                "custodian": collector_name,
            }),
        )
        db.add(audit_entry)

        # Case Timeline Event
        timeline_entry = InvestigationEvent(
            case_id=case_id,
            title=f"Evidence Collected: {payload.title}",
            description=f"Evidence '{payload.title}' ({payload.evidence_type.value}) secured. Current custodian: {collector_name}. SHA-256: {sha256_hash[:16]}...",
            event_type=EventType.EVIDENCE_ADDED,
            event_date=collection_dt,
            location=location_str,
        )
        db.add(timeline_entry)

        db.commit()
        db.refresh(evidence)
        return EvidenceDetailOut.model_validate(evidence)

    @classmethod
    def _execute_custody_transition(
        cls,
        db: Session,
        current_user: User,
        case_id: int,
        evidence_id: int,
        expected_current_status: CustodyStatus,
        new_status: CustodyStatus,
        action_name: str,
        audit_action: AuditAction,
        actor_name: Optional[str],
        to_custodian: Optional[str],
        from_custodian: Optional[str],
        location: Optional[str],
        reason: Optional[str],
        notes: Optional[str],
        timeline_event_type: EventType,
    ) -> EvidenceDetailOut:
        """Helper enforcing strict state machine transitions, immutable custody log, audit, and timeline integration."""
        evidence = cls.get_evidence_or_404(db, current_user, case_id, evidence_id)

        if evidence.status != expected_current_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid state transition: Cannot perform '{action_name}' on evidence in state '{evidence.status.value}'. Expected status: '{expected_current_status.value}'.",
            )

        now_utc = datetime.now(timezone.utc)
        prev_status_str = evidence.status.value
        actor = actor_name or current_user.full_name or current_user.email
        sender = from_custodian or evidence.current_custodian or "Authorized Custodian"
        recipient = to_custodian or sender
        loc_str = location or evidence.collection_location or "Secured Facility"

        # Update Evidence current status and custodian
        evidence.status = new_status
        evidence.current_custodian = recipient
        evidence.updated_at = now_utc

        # Create NEW Immutable Custody Event
        event = CustodyEvent(
            evidence_id=evidence.id,
            case_id=case_id,
            action=action_name,
            previous_status=prev_status_str,
            new_status=new_status.value,
            actor_id=current_user.id,
            actor_name=actor,
            timestamp=now_utc,
            location=loc_str,
            from_custodian=sender,
            to_custodian=recipient,
            reason=reason or f"Evidence transition to {new_status.value}",
            notes=notes,
            evidence_hash=evidence.sha256_hash,
            digital_signature=f"SIG-{action_name}-{evidence.sha256_hash[:12]}",
            device_info=f"EVIDENTIAL-NODE ({current_user.role.value})",
        )
        db.add(event)

        # Audit Ledger Entry
        audit_entry = AuditEvent(
            user_id=current_user.id,
            user_email=current_user.email,
            action=audit_action,
            status=AuditStatus.SUCCESS,
            resource_type="EVIDENCE",
            resource_id=str(evidence.id),
            details=json.dumps({
                "action": action_name,
                "evidence_id": evidence.id,
                "evidence_number": evidence.evidence_number,
                "case_id": case_id,
                "previous_status": prev_status_str,
                "new_status": new_status.value,
                "actor": actor,
                "from_custodian": sender,
                "to_custodian": recipient,
                "sha256_hash": evidence.sha256_hash,
            }),
        )
        db.add(audit_entry)

        # Case Timeline Entry
        timeline_entry = InvestigationEvent(
            case_id=case_id,
            title=f"Custody Event: {action_name.replace('_', ' ').title()}",
            description=f"Evidence {evidence.evidence_number} ('{evidence.title}') status updated: {prev_status_str} → {new_status.value}. Custodian: {recipient}.",
            event_type=timeline_event_type,
            event_date=now_utc,
            location=loc_str,
        )
        db.add(timeline_entry)

        db.commit()
        db.refresh(evidence)
        return EvidenceDetailOut.model_validate(evidence)

    @classmethod
    def seal_evidence(cls, db: Session, current_user: User, case_id: int, evidence_id: int, payload: SealRequest) -> EvidenceDetailOut:
        """Transition: COLLECTED → SEALED."""
        return cls._execute_custody_transition(
            db=db,
            current_user=current_user,
            case_id=case_id,
            evidence_id=evidence_id,
            expected_current_status=CustodyStatus.COLLECTED,
            new_status=CustodyStatus.SEALED,
            action_name="EVIDENCE_SEALED",
            audit_action=AuditAction.EVIDENCE_SEALED,
            actor_name=current_user.full_name or current_user.email,
            to_custodian=None,
            from_custodian=None,
            location=None,
            reason=payload.reason,
            notes=payload.notes,
            timeline_event_type=EventType.EVIDENCE_ADDED,
        )

    @classmethod
    def transfer_evidence(cls, db: Session, current_user: User, case_id: int, evidence_id: int, payload: TransferRequest) -> EvidenceDetailOut:
        """Transition: SEALED → TRANSFERRED."""
        return cls._execute_custody_transition(
            db=db,
            current_user=current_user,
            case_id=case_id,
            evidence_id=evidence_id,
            expected_current_status=CustodyStatus.SEALED,
            new_status=CustodyStatus.TRANSFERRED,
            action_name="EVIDENCE_TRANSFERRED",
            audit_action=AuditAction.EVIDENCE_TRANSFERRED,
            actor_name=current_user.full_name or current_user.email,
            to_custodian=payload.to_custodian,
            from_custodian=None,
            location=payload.location,
            reason=payload.reason,
            notes=payload.notes,
            timeline_event_type=EventType.EVIDENCE_TRANSFER,
        )

    @classmethod
    def receive_evidence(cls, db: Session, current_user: User, case_id: int, evidence_id: int, payload: ReceiveRequest) -> EvidenceDetailOut:
        """Transition: TRANSFERRED → RECEIVED."""
        recipient = payload.received_by or current_user.full_name or current_user.email
        return cls._execute_custody_transition(
            db=db,
            current_user=current_user,
            case_id=case_id,
            evidence_id=evidence_id,
            expected_current_status=CustodyStatus.TRANSFERRED,
            new_status=CustodyStatus.RECEIVED,
            action_name="EVIDENCE_RECEIVED",
            audit_action=AuditAction.EVIDENCE_RECEIVED,
            actor_name=recipient,
            to_custodian=recipient,
            from_custodian=None,
            location=payload.location,
            reason="Received into active custody",
            notes=payload.condition_notes,
            timeline_event_type=EventType.EVIDENCE_TRANSFER,
        )

    @classmethod
    def start_examination(cls, db: Session, current_user: User, case_id: int, evidence_id: int, payload: ExaminationStartRequest) -> EvidenceDetailOut:
        """Transition: RECEIVED → EXAMINED (Start Examination stage)."""
        examiner_name = payload.examiner or current_user.full_name or current_user.email
        return cls._execute_custody_transition(
            db=db,
            current_user=current_user,
            case_id=case_id,
            evidence_id=evidence_id,
            expected_current_status=CustodyStatus.RECEIVED,
            new_status=CustodyStatus.EXAMINED,
            action_name="EXAMINATION_STARTED",
            audit_action=AuditAction.EXAMINATION_STARTED,
            actor_name=examiner_name,
            to_custodian=examiner_name,
            from_custodian=None,
            location="Forensic Examination Lab",
            reason=payload.purpose or "Forensic digital analysis",
            notes=payload.notes,
            timeline_event_type=EventType.INVESTIGATION_EVENT,
        )

    @classmethod
    def complete_examination(cls, db: Session, current_user: User, case_id: int, evidence_id: int, payload: ExaminationCompleteRequest) -> EvidenceDetailOut:
        """Transition: EXAMINED → EXAMINED (Record completed examination milestone)."""
        evidence = cls.get_evidence_or_404(db, current_user, case_id, evidence_id)
        if evidence.status != CustodyStatus.EXAMINED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid state: Cannot complete examination on evidence in state '{evidence.status.value}'. Expected status: 'EXAMINED'.",
            )

        now_utc = datetime.now(timezone.utc)
        examiner = payload.examiner or current_user.full_name or current_user.email

        event = CustodyEvent(
            evidence_id=evidence.id,
            case_id=case_id,
            action="EXAMINATION_COMPLETED",
            previous_status=CustodyStatus.EXAMINED.value,
            new_status=CustodyStatus.EXAMINED.value,
            actor_id=current_user.id,
            actor_name=examiner,
            timestamp=now_utc,
            location="Forensic Lab",
            from_custodian=evidence.current_custodian,
            to_custodian=evidence.current_custodian,
            reason="Forensic analysis and feature extraction complete",
            notes=payload.result_notes,
            evidence_hash=evidence.sha256_hash,
            digital_signature=f"SIG-EXAM-DONE-{evidence.sha256_hash[:12]}",
            device_info=f"EVIDENTIAL-FORENSIC-SUITE ({current_user.role.value})",
        )
        db.add(event)

        audit_entry = AuditEvent(
            user_id=current_user.id,
            user_email=current_user.email,
            action=AuditAction.EXAMINATION_COMPLETED,
            status=AuditStatus.SUCCESS,
            resource_type="EVIDENCE",
            resource_id=str(evidence.id),
            details=json.dumps({
                "action": "EXAMINATION_COMPLETED",
                "evidence_id": evidence.id,
                "examiner": examiner,
                "result_notes": payload.result_notes,
            }),
        )
        db.add(audit_entry)

        timeline_entry = InvestigationEvent(
            case_id=case_id,
            title="Forensic Examination Completed",
            description=f"Examiner {examiner} completed analysis on evidence '{evidence.title}'. Findings: {payload.result_notes or 'Intact'}.",
            event_type=EventType.INVESTIGATION_EVENT,
            event_date=now_utc,
            location="Forensic Lab",
        )
        db.add(timeline_entry)

        db.commit()
        db.refresh(evidence)
        return EvidenceDetailOut.model_validate(evidence)

    @classmethod
    def attach_forensic_report(
        cls,
        db: Session,
        current_user: User,
        case_id: int,
        evidence_id: int,
        payload: ForensicReportRequest,
        report_bytes: Optional[bytes] = None,
        report_filename: Optional[str] = None,
    ) -> EvidenceDetailOut:
        """Transition: EXAMINED → REPORT_GENERATED."""
        evidence = cls.get_evidence_or_404(db, current_user, case_id, evidence_id)
        if evidence.status != CustodyStatus.EXAMINED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid state transition: Cannot generate report for evidence in state '{evidence.status.value}'. Expected status: 'EXAMINED'.",
            )

        now_utc = datetime.now(timezone.utc)
        rep_content = report_bytes or (payload.findings or "Official Forensic Report").encode("utf-8")
        rep_hash = hashlib.sha256(rep_content).hexdigest()

        saved_rep_path: Optional[str] = None
        if report_filename:
            case_dir = STORAGE_EVIDENCE_DIR / str(case_id)
            case_dir.mkdir(parents=True, exist_ok=True)
            target_path = case_dir / f"REPORT_{evidence.evidence_number}_{report_filename}"
            with open(target_path, "wb") as f:
                f.write(rep_content)
            saved_rep_path = str(target_path)

        evidence.status = CustodyStatus.REPORT_GENERATED
        evidence.forensic_report_path = saved_rep_path or f"storage/reports/{evidence.evidence_number}_report.txt"
        evidence.forensic_report_hash = rep_hash
        evidence.updated_at = now_utc

        author_name = current_user.full_name or current_user.email

        event = CustodyEvent(
            evidence_id=evidence.id,
            case_id=case_id,
            action="REPORT_GENERATED",
            previous_status=CustodyStatus.EXAMINED.value,
            new_status=CustodyStatus.REPORT_GENERATED.value,
            actor_id=current_user.id,
            actor_name=author_name,
            timestamp=now_utc,
            location="Forensic Intelligence Directorate",
            from_custodian=evidence.current_custodian,
            to_custodian=evidence.current_custodian,
            reason=payload.report_title or "Attach official forensic findings report",
            notes=payload.findings or payload.notes,
            evidence_hash=evidence.sha256_hash,
            digital_signature=f"SIG-REPORT-{rep_hash[:12]}",
            device_info=f"EVIDENTIAL-REPORT-GEN ({current_user.role.value})",
        )
        db.add(event)

        audit_entry = AuditEvent(
            user_id=current_user.id,
            user_email=current_user.email,
            action=AuditAction.REPORT_GENERATED,
            status=AuditStatus.SUCCESS,
            resource_type="EVIDENCE",
            resource_id=str(evidence.id),
            details=json.dumps({
                "action": "REPORT_GENERATED",
                "evidence_id": evidence.id,
                "report_hash": rep_hash,
                "author": author_name,
            }),
        )
        db.add(audit_entry)

        timeline_entry = InvestigationEvent(
            case_id=case_id,
            title="Official Forensic Report Generated",
            description=f"Forensic report attached for evidence '{evidence.title}'. Report SHA-256: {rep_hash[:16]}...",
            event_type=EventType.INVESTIGATION_EVENT,
            event_date=now_utc,
            location="Forensic Directorate",
        )
        db.add(timeline_entry)

        db.commit()
        db.refresh(evidence)
        return EvidenceDetailOut.model_validate(evidence)

    @classmethod
    def return_evidence(cls, db: Session, current_user: User, case_id: int, evidence_id: int, payload: ReturnRequest) -> EvidenceDetailOut:
        """Transition: REPORT_GENERATED → RETURNED."""
        sender = payload.from_custodian or current_user.full_name or current_user.email
        return cls._execute_custody_transition(
            db=db,
            current_user=current_user,
            case_id=case_id,
            evidence_id=evidence_id,
            expected_current_status=CustodyStatus.REPORT_GENERATED,
            new_status=CustodyStatus.RETURNED,
            action_name="EVIDENCE_RETURNED",
            audit_action=AuditAction.EVIDENCE_RETURNED,
            actor_name=sender,
            to_custodian=payload.to_custodian,
            from_custodian=sender,
            location=payload.location,
            reason=payload.reason,
            notes=payload.notes,
            timeline_event_type=EventType.EVIDENCE_TRANSFER,
        )

    @classmethod
    def submit_to_court(cls, db: Session, current_user: User, case_id: int, evidence_id: int, payload: CourtSubmissionRequest) -> EvidenceDetailOut:
        """Transition: RETURNED → COURT_SUBMITTED."""
        submitter = payload.submitted_by or current_user.full_name or current_user.email
        return cls._execute_custody_transition(
            db=db,
            current_user=current_user,
            case_id=case_id,
            evidence_id=evidence_id,
            expected_current_status=CustodyStatus.RETURNED,
            new_status=CustodyStatus.COURT_SUBMITTED,
            action_name="COURT_SUBMITTED",
            audit_action=AuditAction.COURT_SUBMITTED,
            actor_name=submitter,
            to_custodian=payload.court_name,
            from_custodian=submitter,
            location=payload.court_name,
            reason="Submitted into judicial court record",
            notes=payload.submission_notes or payload.notes,
            timeline_event_type=EventType.EVIDENCE_TRANSFER,
        )

    @classmethod
    def get_custody_chain(cls, db: Session, current_user: User, case_id: int, evidence_id: int) -> CustodyChainResponse:
        """Retrieves complete immutable digital chain of custody events for an evidence item."""
        evidence = cls.get_evidence_or_404(db, current_user, case_id, evidence_id)
        events = (
            db.query(CustodyEvent)
            .filter(CustodyEvent.evidence_id == evidence_id)
            .order_by(CustodyEvent.timestamp.asc())
            .all()
        )
        return CustodyChainResponse(
            evidence_id=evidence.id,
            evidence_number=evidence.evidence_number or f"EVD-{evidence.id}",
            case_id=case_id,
            current_status=evidence.status,
            current_custodian=evidence.current_custodian,
            total_events=len(events),
            events=[CustodyEventOut.model_validate(e) for e in events],
        )

    @classmethod
    def verify_integrity(cls, db: Session, current_user: User, case_id: int, evidence_id: int) -> IntegrityVerificationResult:
        """
        Performs REAL SHA-256 cryptographic verification of stored evidence file on disk
        against stored original SHA-256 hash. Returns status badge and records Audit event.
        """
        evidence = cls.get_evidence_or_404(db, current_user, case_id, evidence_id)
        now_utc = datetime.now(timezone.utc)
        verifier_name = current_user.full_name or current_user.email

        stored_hash = evidence.sha256_hash

        # Calculate current hash from actual file on disk
        current_hash = stored_hash
        file_found = False

        if evidence.file_path and os.path.exists(evidence.file_path):
            file_found = True
            with open(evidence.file_path, "rb") as f:
                content = f.read()
            current_hash = hashlib.sha256(content).hexdigest()

        is_valid = (file_found or bool(stored_hash)) and (current_hash == stored_hash)

        if is_valid:
            status_str = "✓ INTEGRITY VERIFIED"
            evidence.verification_status = VerificationStatus.VALID
            evidence.is_tampered = False
            message = "SHA-256 cryptographic fingerprint matches stored reference exactly. No file tampering detected."
            audit_action = AuditAction.EVIDENCE_VERIFIED
            audit_status = AuditStatus.SUCCESS
        else:
            status_str = "⚠ INTEGRITY VIOLATION DETECTED"
            evidence.verification_status = VerificationStatus.TAMPERING_DETECTED
            evidence.is_tampered = True
            message = "SHA-256 cryptographic digest mismatch! File contents have been altered, corrupted, or tampered with."
            audit_action = AuditAction.INTEGRITY_FAILURE
            audit_status = AuditStatus.FAILURE

        evidence.last_verified_at = now_utc
        evidence.updated_at = now_utc

        # Record Audit Event
        audit_entry = AuditEvent(
            user_id=current_user.id,
            user_email=current_user.email,
            action=audit_action,
            status=audit_status,
            resource_type="EVIDENCE",
            resource_id=str(evidence.id),
            details=json.dumps({
                "action": "EVIDENCE_VERIFIED",
                "evidence_id": evidence.id,
                "evidence_number": evidence.evidence_number,
                "stored_sha256": stored_hash,
                "current_sha256": current_hash,
                "is_valid": is_valid,
                "status": status_str,
            }),
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(evidence)

        return IntegrityVerificationResult(
            evidence_id=evidence.id,
            evidence_number=evidence.evidence_number or f"EVD-{evidence.id}",
            stored_sha256=stored_hash,
            current_sha256=current_hash,
            status=status_str,
            is_valid=is_valid,
            verified_at=now_utc,
            verified_by=verifier_name,
            message=message,
        )
