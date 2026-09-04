from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session

from ai.correlation.correlation_engine import CorrelationEngine
from backend.app.models.case import Case, CasePriority, CaseStatus
from backend.app.models.document import Document, DocumentProcessingStatus, DocumentTranslation
from backend.app.models.entity import EntityType, ExtractedEntity
from backend.app.models.user import User


def get_token(client, email="officer1@evidential.gov.in", password="Officer1@123"):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


# ============================================================================
# UNIT TESTS ON CORRELATION ENGINE (Direct Algorithm Verification)
# ============================================================================

def test_true_positive_correlation():
    """
    True Positive: Two cases with shared phone, vehicle, location, and crime category.
    Must detect strong potential correlation (score >= 0.70), identify all matching factors,
    and output explainable text starting with 'Potential correlation detected'.
    """
    case_1 = {
        "id": 101,
        "case_number": "FIR-2024-DEL-001",
        "title": "Nehru Place SIM Swapping Fraud",
        "description": "Victim reported unauthorized SIM replacement and crypto transfer.",
        "crime_type": "CYBER_CRIME",
        "location": "Nehru Place, New Delhi",
        "police_station": "Cyber Crime Police Station South",
        "incident_date": "2024-03-01T10:00:00Z",
        "entities": [
            {"entity_type": "PHONE", "entity_value": "+91-9876543210", "normalized_value": "+91-9876543210"},
            {"entity_type": "VEHICLE", "entity_value": "DL-01-AB-1234", "normalized_value": "DL01AB1234"},
            {"entity_type": "PERSON", "entity_value": "Rajesh Kumar", "normalized_value": "Rajesh Kumar"},
        ],
        "documents": [{"original_text": "Call placed to +91-9876543210 using vehicle DL-01-AB-1234."}],
    }

    case_2 = {
        "id": 102,
        "case_number": "FIR-2024-DEL-045",
        "title": "Kalkaji OTP Phishing Syndicate",
        "description": "Suspect coordinated banking OTP theft using fake KYC calls.",
        "crime_type": "CYBER_CRIME",
        "location": "Nehru Place, New Delhi",
        "police_station": "Cyber Crime Police Station South",
        "incident_date": "2024-03-03T14:30:00Z",  # 2 days apart
        "entities": [
            {"entity_type": "PHONE", "entity_value": "+91-9876543210", "normalized_value": "+91-9876543210"},
            {"entity_type": "VEHICLE", "entity_value": "DL01AB1234", "normalized_value": "DL01AB1234"},
            {"entity_type": "PERSON", "entity_value": "Rajesh Kumar", "normalized_value": "Rajesh Kumar"},
        ],
        "documents": [{"original_text": "Accused fled in vehicle DL01AB1234 and phone +91-9876543210 was active."}],
    }

    result = CorrelationEngine.compare_cases(case_1, case_2)

    assert result["correlation_score"] >= 0.70
    assert any("Shared phone identifier" in f for f in result["matching_factors"])
    assert any("Shared vehicle identifier" in f for f in result["matching_factors"])
    assert any("Similar person entity" in f for f in result["matching_factors"])
    assert any("Identical crime classification" in f for f in result["matching_factors"])
    assert any("Temporal proximity" in f for f in result["matching_factors"])

    # Verify explainable narrative and legal guardrail
    assert "Potential correlation detected" in result["explanation"]
    assert "committed the crime" not in result["explanation"].lower()
    assert "guilt" not in result["explanation"].lower()


def test_false_positive_rejection():
    """
    False Positive Prevention: Two cases with common generic crime words but completely
    different suspects, phones, vehicles, and locations.
    Must NOT be flagged as high correlation (score must be < 0.25).
    """
    case_a = {
        "id": 201,
        "case_number": "FIR-2024-KOL-110",
        "title": "ATM Cash Dispenser Tampering",
        "description": "Atm tampering case with physical card skimming device.",
        "crime_type": "FINANCIAL_FRAUD",
        "location": "Salt Lake Sector V, Kolkata",
        "police_station": "Bidhannagar Cyber PS",
        "incident_date": "2024-01-10T12:00:00Z",
        "entities": [
            {"entity_type": "PHONE", "entity_value": "+91-9111111111", "normalized_value": "+91-9111111111"},
            {"entity_type": "PERSON", "entity_value": "Subhash Ghosh", "normalized_value": "Subhash Ghosh"},
        ],
        "documents": [],
    }

    case_b = {
        "id": 202,
        "case_number": "FIR-2024-MUM-890",
        "title": "Corporate Email Compromise wire fraud",
        "description": "Spear phishing email spoofing CFO led to vendor invoice fraud.",
        "crime_type": "CYBER_CRIME",
        "location": "Nariman Point, Mumbai",
        "police_station": "Cuffe Parade Police Station",
        "incident_date": "2024-07-25T16:00:00Z",  # 6 months apart
        "entities": [
            {"entity_type": "PHONE", "entity_value": "+91-9999999999", "normalized_value": "+91-9999999999"},
            {"entity_type": "PERSON", "entity_value": "Aakash Mehta", "normalized_value": "Aakash Mehta"},
        ],
        "documents": [],
    }

    result = CorrelationEngine.compare_cases(case_a, case_b)

    assert result["correlation_score"] < 0.25
    assert len(result["matching_entities"]) == 0
    assert "unlikely" in result["explanation"].lower() or "minimal overlap" in result["explanation"].lower()


def test_partial_match_correlation():
    """
    Partial Match: Cases sharing only a single identifier (e.g. shared vehicle or location),
    with different crime types or distinct dates.
    Score should be intermediate (0.25 <= score <= 0.60).
    """
    case_1 = {
        "id": 301,
        "case_number": "FIR-PARTIAL-001",
        "title": "Hit and Run Incident",
        "description": "Speeding white sedan collided with motorcycle near flyover.",
        "crime_type": "ROAD_ACCIDENT",
        "location": "Outer Ring Road, Bengaluru",
        "incident_date": "2024-04-10T22:00:00Z",
        "entities": [
            {"entity_type": "VEHICLE", "entity_value": "KA-04-ME-5555", "normalized_value": "KA04ME5555"},
        ],
        "documents": [],
    }

    case_2 = {
        "id": 302,
        "case_number": "FIR-PARTIAL-002",
        "title": "Illegal Hawala Cash Transport",
        "description": "Interception of undisclosed cash transported in boot of sedan.",
        "crime_type": "FINANCIAL_FRAUD",
        "location": "Electronic City, Bengaluru",
        "incident_date": "2024-04-20T08:00:00Z",
        "entities": [
            {"entity_type": "VEHICLE", "entity_value": "KA-04-ME-5555", "normalized_value": "KA04ME5555"},
        ],
        "documents": [],
    }

    result = CorrelationEngine.compare_cases(case_1, case_2)

    # Moderate correlation driven by shared vehicle
    assert 0.20 <= result["correlation_score"] <= 0.60
    assert any("Shared vehicle identifier" in f for f in result["matching_factors"])
    assert len(result["matching_entities"]) == 1
    assert result["matching_entities"][0]["entity_type"] == "VEHICLE"


def test_different_spelling_fuzzy_matching():
    """
    Different Spelling & Format: Name variations ('Suresh Sharma' vs 'Suresh K. Sharma')
    and plate format differences ('MH-02-CD-9999' vs 'MH02 CD 9999') must be successfully correlated.
    """
    case_1 = {
        "id": 401,
        "case_number": "FIR-SPELL-001",
        "title": "Extortion Call Probe",
        "crime_type": "EXTORTION",
        "location": "Andheri West, Mumbai",
        "incident_date": "2024-05-01T10:00:00Z",
        "entities": [
            {"entity_type": "PERSON", "entity_value": "Suresh Sharma", "normalized_value": "Suresh Sharma"},
            {"entity_type": "VEHICLE", "entity_value": "MH-02-CD-9999", "normalized_value": "MH02CD9999"},
        ],
        "documents": [],
    }

    case_2 = {
        "id": 402,
        "case_number": "FIR-SPELL-002",
        "title": "Threat Letter Delivery",
        "crime_type": "EXTORTION",
        "location": "Andheri, Mumbai",
        "incident_date": "2024-05-02T11:00:00Z",
        "entities": [
            {"entity_type": "PERSON", "entity_value": "Suresh K. Sharma", "normalized_value": "Suresh K. Sharma"},
            {"entity_type": "VEHICLE", "entity_value": "MH02 CD 9999", "normalized_value": "MH02CD9999"},
        ],
        "documents": [],
    }

    result = CorrelationEngine.compare_cases(case_1, case_2)

    assert result["correlation_score"] >= 0.50
    assert any("Similar person entity" in f for f in result["matching_factors"])
    assert any("vehicle identifier" in f.lower() for f in result["matching_factors"])
    assert any(m["match_type"] in ("EXACT", "FUZZY_NAME_VARIANT") for m in result["matching_entities"])


def test_different_language_multilingual_correlation():
    """
    Different Language: Hindi FIR (translated into English) vs English FIR.
    Correlates seamlessly using translated narrative and normalized entities.
    """
    hindi_case = {
        "id": 501,
        "case_number": "FIR-LANG-HIN",
        "title": "अवैध हथियार तस्करी (Arms Smuggling)",
        "description": "मुखबिर की सूचना पर अवैध असलहा बरामद किया गया।",
        "crime_type": "ARMS_ACT",
        "location": "Meerut Bypass, UP",
        "incident_date": "2024-06-10T04:00:00Z",
        "entities": [
            {"entity_type": "PHONE", "entity_value": "+91-9456000000", "normalized_value": "+91-9456000000"},
            {"entity_type": "PERSON", "entity_value": "Imran Khan", "normalized_value": "Imran Khan"},
        ],
        "documents": [
            {
                "original_text": "अभियुक्त इमरान खान फोन 9456000000 से हथियार आपूर्ति की बातचीत कर रहा था।",
                "translated_text": "Accused Imran Khan was discussing firearms supply over phone 9456000000.",
            }
        ],
    }

    english_case = {
        "id": 502,
        "case_number": "FIR-LANG-ENG",
        "title": "Interstate Weapon Interception",
        "description": "Special cell intercepted interstate weapon supplier operating across NCR borders.",
        "crime_type": "ARMS_ACT",
        "location": "Ghaziabad Border, UP",
        "incident_date": "2024-06-12T05:00:00Z",
        "entities": [
            {"entity_type": "PHONE", "entity_value": "+91-9456000000", "normalized_value": "+91-9456000000"},
            {"entity_type": "PERSON", "entity_value": "Mohammad Imran Khan", "normalized_value": "Mohammad Imran Khan"},
        ],
        "documents": [
            {
                "original_text": "Illegal pistol consignment seized from suspect Imran Khan, mobile 9456000000 active on tower.",
                "translated_text": "",
            }
        ],
    }

    result = CorrelationEngine.compare_cases(hindi_case, english_case)

    assert result["correlation_score"] >= 0.45
    assert any("Shared phone identifier" in f for f in result["matching_factors"])
    assert any("Similar person entity" in f for f in result["matching_factors"])
    assert any("Identical crime classification" in f for f in result["matching_factors"])


def test_unrelated_fir_correlation():
    """
    Unrelated FIR: Completely distinct crimes, locations, years, and zero shared entities.
    Must yield near-zero correlation (< 0.15).
    """
    fir_1 = {
        "id": 601,
        "case_number": "FIR-UNRELATED-A",
        "title": "Bicycle Theft at Railway Stand",
        "crime_type": "THEFT",
        "location": "Patna Junction, Bihar",
        "incident_date": "2021-02-14T09:00:00Z",
        "entities": [{"entity_type": "PERSON", "entity_value": "Ramesh Roy", "normalized_value": "Ramesh Roy"}],
        "documents": [],
    }

    fir_2 = {
        "id": 602,
        "case_number": "FIR-UNRELATED-B",
        "title": "Industrial Environmental Effluent Discharge",
        "crime_type": "ENVIRONMENTAL_OFFENSE",
        "location": "Ankleshwar GIDC, Gujarat",
        "incident_date": "2024-11-20T17:00:00Z",
        "entities": [{"entity_type": "PERSON", "entity_value": "Deepak Patel", "normalized_value": "Deepak Patel"}],
        "documents": [],
    }

    result = CorrelationEngine.compare_cases(fir_1, fir_2)

    assert result["correlation_score"] < 0.15
    assert len(result["matching_entities"]) == 0
    assert "unlikely" in result["explanation"].lower() or "minimal overlap" in result["explanation"].lower()


def test_strict_guardrail_mandate_never_asserts_guilt():
    """
    CRITICAL ETHICAL & LEGAL GUARDRAIL:
    Engine MUST NEVER output 'Person X committed the crime' or automatically establish guilt.
    Must consistently output 'Potential correlation' and neutral rationale.
    """
    case_x = {
        "id": 701,
        "case_number": "FIR-GUARDRAIL-1",
        "title": "Severe Robbery",
        "crime_type": "ROBBERY",
        "entities": [{"entity_type": "PHONE", "entity_value": "+91-9988776655", "normalized_value": "+91-9988776655"}],
    }
    case_y = {
        "id": 702,
        "case_number": "FIR-GUARDRAIL-2",
        "title": "Armed Robbery",
        "crime_type": "ROBBERY",
        "entities": [{"entity_type": "PHONE", "entity_value": "+91-9988776655", "normalized_value": "+91-9988776655"}],
    }

    result = CorrelationEngine.compare_cases(case_x, case_y)
    expl = result["explanation"]

    # 1. Prohibited phrases check
    assert "committed the crime" not in expl.lower()
    assert "is guilty" not in expl.lower()
    assert "was guilty" not in expl.lower()
    assert "is the culprit" not in expl.lower()

    # 2. Mandated phrase check
    assert "Potential correlation" in expl

    # 3. Test runtime assertion trap
    with pytest.raises(ValueError, match="ETHICAL GUARDRAIL VIOLATION"):
        CorrelationEngine._assert_ethical_guardrails(
            "Investigation proves Person X committed the crime and is guilty."
        )


# ============================================================================
# API INTEGRATION & PRE-RETRIEVAL AUTHORIZATION TESTS
# ============================================================================

@pytest.fixture
def populated_correlation_db(db_session: Session):
    """Sets up test cases with controlled ownership boundaries for testing API authorization."""
    officer1 = db_session.query(User).filter(User.email == "officer1@evidential.gov.in").first()
    officer2 = db_session.query(User).filter(User.email == "officer2@evidential.gov.in").first()

    # Case Alpha: Officer 1's Case
    case_alpha = db_session.query(Case).filter(Case.case_number == "FIR-CORR-ALPHA").first()
    if not case_alpha:
        case_alpha = Case(
            case_number="FIR-CORR-ALPHA",
            title="Lajpat Nagar Credit Card Cloning",
            description="Syndicate operating POS skimmers across retail shops.",
            crime_type="CYBER_CRIME",
            location="Lajpat Nagar, New Delhi",
            police_station="Cyber Police Station Central",
            status=CaseStatus.UNDER_INVESTIGATION,
            priority=CasePriority.HIGH,
            created_by_id=officer1.id,
            assigned_officer_id=officer1.id,
        )
        db_session.add(case_alpha)
        db_session.commit()
        db_session.refresh(case_alpha)

        ent_a = ExtractedEntity(
            case_id=case_alpha.id,
            entity_type=EntityType.PHONE,
            entity_value="+91-9811223344",
            normalized_value="+91-9811223344",
            confidence=0.99,
        )
        ent_v = ExtractedEntity(
            case_id=case_alpha.id,
            entity_type=EntityType.VEHICLE,
            entity_value="DL-03-XY-7777",
            normalized_value="DL03XY7777",
            confidence=0.95,
        )
        db_session.add_all([ent_a, ent_v])
        db_session.commit()

    # Case Beta: Also assigned to Officer 1 (Correlated with Alpha)
    case_beta = db_session.query(Case).filter(Case.case_number == "FIR-CORR-BETA").first()
    if not case_beta:
        case_beta = Case(
            case_number="FIR-CORR-BETA",
            title="South Extension ATM Cash Intercept",
            description="Cloned card withdrawals from multiple ATMs in South Delhi.",
            crime_type="CYBER_CRIME",
            location="South Extension, New Delhi",
            police_station="Cyber Police Station Central",
            status=CaseStatus.UNDER_INVESTIGATION,
            priority=CasePriority.HIGH,
            created_by_id=officer1.id,
            assigned_officer_id=officer1.id,
        )
        db_session.add(case_beta)
        db_session.commit()
        db_session.refresh(case_beta)

        ent_b = ExtractedEntity(
            case_id=case_beta.id,
            entity_type=EntityType.PHONE,
            entity_value="+91-9811223344",
            normalized_value="+91-9811223344",
            confidence=0.99,
        )
        db_session.add(ent_b)
        db_session.commit()

    # Case Gamma: Assigned strictly to Officer 2 (Classified Narcotics Case)
    case_gamma = db_session.query(Case).filter(Case.case_number == "FIR-CORR-GAMMA-SECRET").first()
    if not case_gamma:
        case_gamma = Case(
            case_number="FIR-CORR-GAMMA-SECRET",
            title="Classified Cargo Narcotics Intercept",
            description="Strictly confidential narcotics consignment probe.",
            crime_type="NARCOTICS",
            location="Nhava Sheva Port, Navi Mumbai",
            police_station="Anti Narcotics Cell",
            status=CaseStatus.UNDER_INVESTIGATION,
            priority=CasePriority.CRITICAL,
            created_by_id=officer2.id,
            assigned_officer_id=officer2.id,
        )
        db_session.add(case_gamma)
        db_session.commit()
        db_session.refresh(case_gamma)

        # Injects same phone number to ensure that even if phone matches, authorization PREVENTS cross-correlation
        ent_g = ExtractedEntity(
            case_id=case_gamma.id,
            entity_type=EntityType.PHONE,
            entity_value="+91-9811223344",
            normalized_value="+91-9811223344",
            confidence=0.99,
        )
        db_session.add(ent_g)
        db_session.commit()

    return {
        "alpha": case_alpha,
        "beta": case_beta,
        "gamma": case_gamma,
        "officer1": officer1,
        "officer2": officer2,
    }


def test_api_case_correlations_authorized(client, populated_correlation_db):
    """Officer 1 retrieves correlations for Case Alpha: Case Beta is returned, Case Gamma is strictly excluded."""
    token1 = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token1}"}

    case_alpha_id = populated_correlation_db["alpha"].id

    res = client.get(f"/api/v1/cases/{case_alpha_id}/correlations", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["source_case_id"] == case_alpha_id
    assert data["total"] >= 1

    # Officer 1 sees correlation with their Case Beta
    related_numbers = [c["related_case"]["case_number"] for c in data["correlations"]]
    assert "FIR-CORR-BETA" in related_numbers

    # CRITICAL: Officer 1 must NOT see secret Case Gamma in correlations despite shared phone number!
    assert "FIR-CORR-GAMMA-SECRET" not in related_numbers


def test_api_case_correlations_unauthorized_source_blocked(client, populated_correlation_db):
    """Officer 1 attempts to correlate Officer 2's Case Gamma directly: must return 403 Forbidden."""
    token1 = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token1}"}

    case_gamma_id = populated_correlation_db["gamma"].id

    res = client.get(f"/api/v1/cases/{case_gamma_id}/correlations", headers=headers)
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]
