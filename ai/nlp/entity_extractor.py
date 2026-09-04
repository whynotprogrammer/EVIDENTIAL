import re
from typing import Dict, List, Optional


class ExtractedEntityData:
    def __init__(
        self,
        entity_type: str,
        entity_value: str,
        normalized_value: Optional[str] = None,
        confidence: float = 0.90,
        context_snippet: Optional[str] = None,
    ):
        self.entity_type = entity_type
        self.entity_value = entity_value.strip()
        self.normalized_value = (normalized_value or entity_value).strip()
        self.confidence = float(confidence)
        self.context_snippet = context_snippet.strip() if context_snippet else None

    def to_dict(self) -> Dict:
        return {
            "entity_type": self.entity_type,
            "entity_value": self.entity_value,
            "normalized_value": self.normalized_value,
            "confidence": round(self.confidence, 4),
            "context_snippet": self.context_snippet,
        }


class EntityExtractor:
    """
    Rule-based & Contextual Named Entity Recognition (NER) for Indian Legal & Police FIRs.
    Extracts 11 distinct entity categories with normalization and context extraction.
    """

    # 1. Phone Numbers (Indian format: +91, 0, or 10-digit starting with 6-9)
    PHONE_REGEX = re.compile(
        r"(?:(?:\+91|0)[\s-]?)?[6-9]\d{4}[\s-]?\d{5}\b|\b\d{3,5}[\s-]?\d{6,8}\b"
    )

    # 2. Email Addresses
    EMAIL_REGEX = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )

    # 3. Dates (DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY, DD Month YYYY)
    DATE_REGEX = re.compile(
        r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*,?\s*\d{2,4})\b",
        re.IGNORECASE,
    )

    # 4. Vehicle Registration Numbers (Indian standard: State code + District code + Series + 4 digits)
    VEHICLE_REGEX = re.compile(
        r"\b(?:[A-Z]{2}[-\s]?[0-9]{1,2}[-\s]?[A-Z]{1,3}[-\s]?[0-9]{4}|[A-Z]{2}[-\s]?[0-9]{2}[-\s]?[0-9]{4})\b"
    )

    # 5. Law Sections (IPC, BNS, IT Act, NDPS, Arms Act)
    LAW_SECTION_REGEX = re.compile(
        r"\b(?:(?:Section|Sec\.?|u/s|U/S|धारा)\s*[\d\w,\s/&]+(?:\s*(?:IPC|BNS|I\.P\.C\.|CrPC|IT Act|Information Technology Act|NDPS|Arms Act|POCSO))?|(?:IPC|BNS)\s*[\d\w,\s/&]+)\b",
        re.IGNORECASE,
    )

    # 6. Case Numbers & FIR Identifiers
    CASE_NUMBER_REGEX = re.compile(
        r"\b(?:FIR\s*(?:No\.?|Number)?[\s:/#-]*\d+[\w/-]*|Case\s*(?:No\.?|Number)?[\s:/#-]*\d+[\w/-]*|Crime\s*(?:No\.?|Number)?[\s:/#-]*\d+[\w/-]*|CR[\s-]*\d+/\d{2,4})\b",
        re.IGNORECASE,
    )

    # 7. Police Stations
    POLICE_STATION_REGEX = re.compile(
        r"\b(?:[A-Z][A-Za-z\s]+(?:\s+Police\s+Station|\s+P\.S\.|\s+PS|\s+Kotwali|\s+Thana|\s+ठाणा|\s+थाना))\b"
    )

    # 8. Organizations (Banks, Telecoms, Agencies)
    KNOWN_ORGANIZATIONS = [
        "State Bank of India", "SBI", "HDFC Bank", "HDFC", "ICICI Bank", "ICICI",
        "Axis Bank", "Punjab National Bank", "PNB", "Bank of Baroda",
        "Reserve Bank of India", "RBI", "Central Bureau of Investigation", "CBI",
        "National Investigation Agency", "NIA", "Enforcement Directorate", "ED",
        "Airtel", "Jio", "Reliance Jio", "Vodafone Idea", "VI", "BSNL",
        "WhatsApp", "Telegram", "Google", "Facebook", "Instagram", "Paytm", "PhonePe",
        "Cyber Crime Cell", "Interpol", "UIDAI"
    ]

    # 9. Locations / Cities / States
    KNOWN_LOCATIONS = [
        "New Delhi", "Delhi", "Mumbai", "Bengaluru", "Bangalore", "Kolkata", "Chennai",
        "Hyderabad", "Pune", "Ahmedabad", "Jaipur", "Surat", "Lucknow", "Kanpur",
        "Nagpur", "Indore", "Thane", "Bhopal", "Visakhapatnam", "Patna", "Vadodara",
        "Ghaziabad", "Ludhiana", "Agra", "Nashik", "Faridabad", "Meerut", "Rajkot",
        "Varanasi", "Srinagar", "Aurangabad", "Dhanbad", "Amritsar", "Navi Mumbai",
        "Allahabad", "Prayagraj", "Ranchi", "Howrah", "Coimbatore", "Jabalpur", "Gwalior",
        "Vijayawada", "Jodhpur", "Madurai", "Raipur", "Kota", "Guwahati", "Chandigarh",
        "Connaught Place", "Bandra", "Whitefield", "Indiranagar", "Koramangala", "Cyber City",
        "Noida", "Gurugram", "Gurgaon", "Salt Lake", "T Nagar", "Aliganj", "Hauz Khas"
    ]

    # 10. Crime Types
    CRIME_TYPES = [
        "CYBER_FRAUD", "ONLINE_PHISHING", "FINANCIAL_FRAUD", "ARMED_ROBBERY",
        "THEFT", "BURGLARY", "EXTORTION", "HOMICIDE", "MURDER", "ASSAULT",
        "NARCOTICS_TRAFFICKING", "ILLEGAL_FIREARMS", "KIDNAPPING", "FORGERY",
        "CRIMINAL_BREACH_OF_TRUST", "IDENTITY_THEFT", "CHEATING", "CORRUPTION"
    ]

    @classmethod
    def _extract_context(cls, text: str, match_start: int, match_end: int, window: int = 50) -> str:
        start = max(0, match_start - window)
        end = min(len(text), match_end + window)
        snippet = text[start:end].replace("\n", " ").strip()
        return f"...{snippet}..."

    @classmethod
    def extract_entities(cls, text: str) -> List[ExtractedEntityData]:
        """
        Extracts all 11 required entity categories from document text.
        """
        if not text or not text.strip():
            return []

        entities: List[ExtractedEntityData] = []
        seen_keys = set()

        def add_entity(entity_type: str, value: str, normalized: str = None, conf: float = 0.90, ctx: str = None):
            norm = (normalized or value).strip()
            key = (entity_type, norm.lower())
            if key not in seen_keys and len(norm) > 1:
                seen_keys.add(key)
                entities.append(ExtractedEntityData(
                    entity_type=entity_type,
                    entity_value=value.strip(),
                    normalized_value=norm,
                    confidence=conf,
                    context_snippet=ctx
                ))

        # 1. PHONE
        for match in cls.PHONE_REGEX.finditer(text):
            val = match.group().strip()
            # Clean digits
            digits = re.sub(r"\D", "", val)
            if 10 <= len(digits) <= 12:
                ctx = cls._extract_context(text, match.start(), match.end())
                norm_phone = digits[-10:]
                add_entity("PHONE", val, f"+91-{norm_phone}", 0.95, ctx)

        # 2. EMAIL
        for match in cls.EMAIL_REGEX.finditer(text):
            val = match.group().strip()
            ctx = cls._extract_context(text, match.start(), match.end())
            add_entity("EMAIL", val, val.lower(), 0.98, ctx)

        # 3. DATE
        for match in cls.DATE_REGEX.finditer(text):
            val = match.group().strip()
            ctx = cls._extract_context(text, match.start(), match.end())
            add_entity("DATE", val, val, 0.92, ctx)

        # 4. VEHICLE
        for match in cls.VEHICLE_REGEX.finditer(text):
            val = match.group().strip().upper()
            # Must look like an Indian plate format
            if len(re.sub(r"[\s-]", "", val)) >= 8:
                ctx = cls._extract_context(text, match.start(), match.end())
                clean_plate = re.sub(r"[\s-]", "", val)
                add_entity("VEHICLE", val, clean_plate, 0.94, ctx)

        # 5. LAW_SECTION
        for match in cls.LAW_SECTION_REGEX.finditer(text):
            val = match.group().strip()
            ctx = cls._extract_context(text, match.start(), match.end())
            add_entity("LAW_SECTION", val, val.upper(), 0.96, ctx)

        # 6. CASE_NUMBER
        for match in cls.CASE_NUMBER_REGEX.finditer(text):
            val = match.group().strip()
            ctx = cls._extract_context(text, match.start(), match.end())
            add_entity("CASE_NUMBER", val, val.upper(), 0.96, ctx)

        # 7. POLICE_STATION
        ps_label_matches = re.finditer(
            r"(?:Police\s+Station|P\.S\.|PS|Thana|थाना|ठाणे)\s*:\s*([A-Za-z\u0900-\u097F\s]+?)(?=[,\n\r]|\s+Incident|\s+Date|$)",
            text,
            re.IGNORECASE,
        )
        for match in ps_label_matches:
            val = match.group(1).strip()
            if len(val) > 2:
                ctx = cls._extract_context(text, match.start(), match.end())
                add_entity("POLICE_STATION", val, val.title(), 0.95, ctx)

        for match in cls.POLICE_STATION_REGEX.finditer(text):
            val = match.group().strip()
            if len(val) > 4:
                ctx = cls._extract_context(text, match.start(), match.end())
                add_entity("POLICE_STATION", val, val.title(), 0.93, ctx)

        # 8. ORGANIZATION
        for org in cls.KNOWN_ORGANIZATIONS:
            pattern = re.compile(rf"\b{re.escape(org)}\b", re.IGNORECASE)
            for match in pattern.finditer(text):
                val = match.group().strip()
                ctx = cls._extract_context(text, match.start(), match.end())
                add_entity("ORGANIZATION", val, org, 0.94, ctx)

        # 9. LOCATION
        for loc in cls.KNOWN_LOCATIONS:
            pattern = re.compile(rf"\b{re.escape(loc)}\b", re.IGNORECASE)
            for match in pattern.finditer(text):
                val = match.group().strip()
                ctx = cls._extract_context(text, match.start(), match.end())
                add_entity("LOCATION", val, loc, 0.92, ctx)

        # 10. CRIME_TYPE
        for crime in cls.CRIME_TYPES:
            crime_clean = crime.replace("_", " ")
            pattern = re.compile(rf"\b{re.escape(crime_clean)}\b|\b{re.escape(crime)}\b", re.IGNORECASE)
            for match in pattern.finditer(text):
                val = match.group().strip()
                ctx = cls._extract_context(text, match.start(), match.end())
                add_entity("CRIME_TYPE", val, crime, 0.90, ctx)

        # 11. PERSON (Contextual extraction: Complainant / Accused / Informant / Shri / Mr / Smt / Officer)
        person_patterns = [
            r"(?:Complainant|Accused|Informant|Victim|Witness|Officer|Inspector|Sub-Inspector|SI|SHO|Shri|Mr\.?|Mrs\.?|Smt\.?|Dr\.?|Constable)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
            r"(?:वादी|अभियुक्त|आरोपी|शिकायतकर्ता|श्री|श्रीमती)\s*:?\s*([\u0900-\u097F]+(?:\s+[\u0900-\u097F]+){1,3})",
        ]
        for pat in person_patterns:
            for match in re.finditer(pat, text):
                val = match.group(1).strip()
                # Exclude false positives that matched known locations or orgs
                if val not in cls.KNOWN_LOCATIONS and val not in cls.KNOWN_ORGANIZATIONS and len(val) > 3:
                    ctx = cls._extract_context(text, match.start(), match.end())
                    add_entity("PERSON", val, val.title(), 0.88, ctx)

        return entities
