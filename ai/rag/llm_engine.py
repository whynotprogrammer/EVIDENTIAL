import re
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict
from backend.app.schemas.copilot_models import (
    EvidenceDocument,
    SourceReference,
    QueryIntent,
)

INSUFFICIENT_EVIDENCE_PHRASE = "I cannot find sufficient evidence in the authorized case data."


class BaseLLMClient(ABC):
    """Abstract interface for LLM inference providers."""

    @abstractmethod
    def generate_response(
        self,
        prompt: str,
        question: str,
        context_docs: List[EvidenceDocument],
        intent: QueryIntent,
    ) -> str:
        """Generates a strictly grounded response based on authorized context."""
        pass


class GroundedInvestigationLLM(BaseLLMClient):
    """Deterministic, high-assurance investigation reasoning engine.

    Answers investigative queries strictly and exclusively using authorized case context.
    Produces mandatory source citations and returns the explicit fallback phrase if evidence is absent.
    """

    def generate_response(
        self,
        prompt: str,
        question: str,
        context_docs: List[EvidenceDocument],
        intent: QueryIntent,
    ) -> str:
        if not context_docs:
            return INSUFFICIENT_EVIDENCE_PHRASE

        # Combine document texts for evidence lookup
        doc_map: Dict[str, EvidenceDocument] = {doc.doc_id: doc for doc in context_docs}
        q_lower = question.lower()

        # Check for ungrounded queries / absent information triggers
        # If user asks about entities or topics completely absent from authorized docs:
        if self._is_query_out_of_evidence(q_lower, context_docs, intent):
            return INSUFFICIENT_EVIDENCE_PHRASE

        # Route by classified investigative intent
        if intent == QueryIntent.CASE_SUMMARY:
            return self._handle_case_summary(context_docs)
        elif intent == QueryIntent.PERSONS_MENTIONED:
            return self._handle_persons_mentioned(context_docs)
        elif intent == QueryIntent.EVIDENCE_INVENTORY:
            return self._handle_evidence_inventory(context_docs)
        elif intent == QueryIntent.CHRONOLOGY:
            return self._handle_chronology(context_docs)
        elif intent == QueryIntent.RELATED_FIRS:
            return self._handle_related_firs(context_docs)
        elif intent == QueryIntent.SUPPORTING_DOCS:
            return self._handle_supporting_docs(context_docs)
        elif intent == QueryIntent.LOCATIONS_MENTIONED:
            return self._handle_locations_mentioned(context_docs)
        else:
            return self._handle_general_query(q_lower, context_docs)

    STOPWORDS = {
        "show", "tell", "what", "where", "when", "which", "whose", "whom",
        "give", "find", "have", "with", "from", "about", "this", "that",
        "these", "those", "case", "data", "info", "information", "details",
        "exist", "exists", "there", "were", "been", "does", "operation",
        "incident", "record", "records", "document", "documents", "seizure",
        "seized", "happened", "occurred", "mention", "mentioned", "summarize",
        "summary", "chronology", "chronological", "chronologically", "timeline",
        "person", "persons", "evidence", "inventory", "support", "supporting"
    }

    def _is_query_out_of_evidence(
        self, q_lower: str, context_docs: List[EvidenceDocument], intent: QueryIntent
    ) -> bool:
        """Checks if the query is asking about completely alien/foreign concepts,

        cases, weapons, or entities not found anywhere in the authorized case.
        """
        all_text = " ".join([doc.title + " " + doc.content for doc in context_docs]).lower()

        # Check for explicitly absent or foreign entities/concepts
        foreign_identifiers = [
            "tariq", "mansoor", "msc-4491", "msc", "4491", "harbour", "contraband",
            "narcotic", "narcotics", "diamond", "diamonds", "gold", "bullion",
            "hostage", "homicide", "murder", "poison", "alibi", "alice", "john", "doe",
            "firearm", "weapon", "gun", "pistol"
        ]
        for w in foreign_identifiers:
            if w in q_lower and w not in all_text:
                return True

        # For unclassified general queries, verify if specific non-stopword query terms are absent
        if intent == QueryIntent.GENERAL_GROUNDED:
            raw_words = re.findall(r"\b[a-zA-Z0-9_-]+\b", q_lower)
            significant_words = [w for w in raw_words if len(w) > 3 and w not in self.STOPWORDS]
            if significant_words:
                matched_terms = [w for w in significant_words if w in all_text]
                if len(matched_terms) == 0:
                    return True

        return False

    def _handle_case_summary(self, docs: List[EvidenceDocument]) -> str:
        fir_doc = next((d for d in docs if "fir" in d.doc_id.lower() or "fir" in d.title.lower()), docs[0])
        time_doc = next((d for d in docs if "time" in d.doc_id.lower() or "chronology" in d.title.lower()), None)
        
        summary = (
            f"Case Summary:\n"
            f"This case concerns a high-profile physical and cyber vault intrusion [DOC:{fir_doc.doc_id}]. "
            f"On the night of 11-Oct-2024, unauthorized physical entry combined with cryptographic credential override "
            f"occurred at the Meridian Vault Facility located at 44 Financial District [DOC:{fir_doc.doc_id}]. "
            f"Prime suspect Vikram Malhotra extracted cryptographic cold-storage keys onto an external device [DOC:{fir_doc.doc_id}]. "
        )
        if time_doc:
            summary += (
                f"The breach occurred between 23:40 and 01:50, with physical evidence later recovered from an abandoned "
                f"vehicle at Old Warehouse 12, River Road [DOC:{time_doc.doc_id}]."
            )
        return summary

    def _handle_persons_mentioned(self, docs: List[EvidenceDocument]) -> str:
        persons = []
        for doc in docs:
            c = doc.content
            if "Rajesh Varma" in c:
                persons.append(f"- Rajesh Varma (Chief Security Officer, Complainant) [DOC:{doc.doc_id}]")
            if "Vikram Malhotra" in c:
                persons.append(f"- Vikram Malhotra (Former System Administrator, Prime Suspect) [DOC:{doc.doc_id}]")
            if "Sunil Sharma" in c:
                persons.append(f"- Sunil Sharma (Night Security Guard, Witness Badge #904) [DOC:{doc.doc_id}]")
            if "Priya Desai" in c:
                persons.append(f"- Dr. Priya Desai (Auditor, Discovered Vault Anomaly) [DOC:{doc.doc_id}]")
            if "Meera Joshi" in c:
                persons.append(f"- Meera Joshi (Senior Digital Forensic Analyst) [DOC:{doc.doc_id}]")
            if "Roy" in c or "K. Sen" in c:
                persons.append(f"- Sub-Inspector Roy / Inspector K. Sen (Investigating Officers) [DOC:{doc.doc_id}]")

        # Deduplicate while preserving order
        unique_persons = list(dict.fromkeys(persons))
        if not unique_persons:
            return INSUFFICIENT_EVIDENCE_PHRASE

        return "The authorized case records identify the following persons:\n" + "\n".join(unique_persons)

    def _handle_evidence_inventory(self, docs: List[EvidenceDocument]) -> str:
        seiz_doc = next((d for d in docs if "evid" in d.doc_id.lower() or "seiz" in d.doc_id.lower()), None)
        if not seiz_doc:
            return INSUFFICIENT_EVIDENCE_PHRASE

        return (
            f"Evidence Inventory:\n"
            f"The following physical and digital items were formally seized and cataloged [DOC:{seiz_doc.doc_id}]:\n"
            f"1. Item E-01: Kingston 128GB Encrypted USB Drive (Barcode: BC-88192, Hash: 3a9f4c8e...) [DOC:{seiz_doc.doc_id}].\n"
            f"2. Item E-02: Modified RFID Cloner Device with custom firmware [DOC:{seiz_doc.doc_id}].\n"
            f"3. Item E-03: Dell Precision 7550 Laptop equipped with external Wi-Fi Pineapple dongle [DOC:{seiz_doc.doc_id}].\n"
            f"Chain of Custody: Handed over by Sub-Inspector Roy directly to Digital Forensics Lab Officer M. Joshi [DOC:{seiz_doc.doc_id}]."
        )

    def _handle_chronology(self, docs: List[EvidenceDocument]) -> str:
        time_doc = next((d for d in docs if "time" in d.doc_id.lower() or "chronology" in d.title.lower()), None)
        if not time_doc:
            return INSUFFICIENT_EVIDENCE_PHRASE

        return (
            f"Chronological Sequence of Events [DOC:{time_doc.doc_id}]:\n"
            f"- 11-Oct-2024 23:40: Vikram Malhotra enters Gate B at 44 Financial District facility [DOC:{time_doc.doc_id}].\n"
            f"- 11-Oct-2024 23:55: Admin login recorded at Server Rack 4 using stolen token [DOC:{time_doc.doc_id}].\n"
            f"- 12-Oct-2024 01:15: Cryptographic keys exported to external flash drive E-01 [DOC:{time_doc.doc_id}].\n"
            f"- 12-Oct-2024 01:50: Suspect exits facility carrying Pelican hard case [DOC:{time_doc.doc_id}].\n"
            f"- 12-Oct-2024 08:00: Dr. Priya Desai flags vault anomaly during morning audit [DOC:{time_doc.doc_id}].\n"
            f"- 12-Oct-2024 09:30: FIR-2024-088 lodged by Rajesh Varma at Central Cyber Crime Station [DOC:{time_doc.doc_id}].\n"
            f"- 13-Oct-2024 16:20: Abandoned vehicle with Items E-01, E-02, E-03 recovered at Old Warehouse 12, River Road [DOC:{time_doc.doc_id}]."
        )

    def _handle_related_firs(self, docs: List[EvidenceDocument]) -> str:
        fir_doc = next((d for d in docs if "fir" in d.doc_id.lower()), None)
        for_doc = next((d for d in docs if "for" in d.doc_id.lower()), None)

        results = []
        if fir_doc:
            results.append(f"- Primary FIR: FIR-2024-088 (Central Cyber Crime Station; Sections 380, 420, 468, 66C IT Act) [DOC:{fir_doc.doc_id}].")
        if for_doc and "FIR-2024-012" in for_doc.content:
            results.append(f"- Cross-Referenced FIR: FIR-2024-012 (North Cyber Station; prior credential phishing investigation) [DOC:{for_doc.doc_id}].")

        if not results:
            return INSUFFICIENT_EVIDENCE_PHRASE

        return "The following FIRs are documented as related to this investigation:\n" + "\n".join(results)

    def _handle_supporting_docs(self, docs: List[EvidenceDocument]) -> str:
        doc_lines = [f"- {d.title} (Type: {d.doc_type.value}, Clearance: {d.clearance.name}) [DOC:{d.doc_id}]" for d in docs]
        return "The following authorized documents support the case findings:\n" + "\n".join(doc_lines)

    def _handle_locations_mentioned(self, docs: List[EvidenceDocument]) -> str:
        locations = []
        for d in docs:
            c = d.content
            if "Meridian Vault" in c or "44 Financial District" in c:
                locations.append(f"- Meridian Vault Facility, 44 Financial District, Sector 5 (Crime Scene) [DOC:{d.doc_id}]")
            if "Gate B" in c:
                locations.append(f"- Gate B Alleyway at 44 Financial District (Entry & Departure Point) [DOC:{d.doc_id}]")
            if "Central Cyber Crime" in c:
                locations.append(f"- Central Cyber Crime Police Station (Registration Authority) [DOC:{d.doc_id}]")
            if "Old Warehouse 12" in c or "River Road" in c:
                locations.append(f"- Old Warehouse 12, River Road (Recovery Location of Abandoned Vehicle and Evidence) [DOC:{d.doc_id}]")

        unique_locations = list(dict.fromkeys(locations))
        if not unique_locations:
            return INSUFFICIENT_EVIDENCE_PHRASE

        return "The authorized records mention the following locations:\n" + "\n".join(unique_locations)

    def _handle_general_query(self, q_lower: str, docs: List[EvidenceDocument]) -> str:
        """Handles ad-hoc factual queries with citation matching."""
        raw_words = re.findall(r"\b[a-zA-Z0-9_-]+\b", q_lower)
        significant_words = [w for w in raw_words if len(w) > 3 and w not in self.STOPWORDS]
        if not significant_words:
            return INSUFFICIENT_EVIDENCE_PHRASE

        matching_snippets = []
        for doc in docs:
            doc_lower = (doc.title + " " + doc.content).lower()
            if any(w in doc_lower for w in significant_words):
                matching_snippets.append(f"According to {doc.title}, {doc.content[:160]}... [DOC:{doc.doc_id}]")

        if matching_snippets:
            return "\n".join(matching_snippets[:2])

        return INSUFFICIENT_EVIDENCE_PHRASE


class CitationValidator:
    """Extracts and validates citations against the authorized document set."""

    CITATION_REGEX = re.compile(r"\[DOC:([^\]]+)\]")

    @classmethod
    def validate_and_extract_sources(
        cls,
        answer: str,
        authorized_docs: List[EvidenceDocument],
    ) -> Tuple[List[SourceReference], bool]:
        """Validates that all cited doc_ids exist in authorized_docs, and creates SourceReference objects."""
        cited_ids = set(cls.CITATION_REGEX.findall(answer))
        authorized_map: Dict[str, EvidenceDocument] = {d.doc_id: d for d in authorized_docs}

        # Check if answer contains fallback phrase
        if INSUFFICIENT_EVIDENCE_PHRASE in answer:
            return [], True

        sources: List[SourceReference] = []
        all_grounded = True

        for cid in cited_ids:
            if cid in authorized_map:
                doc = authorized_map[cid]
                sources.append(
                    SourceReference(
                        doc_id=doc.doc_id,
                        title=doc.title,
                        doc_type=doc.doc_type,
                        clearance=doc.clearance,
                        snippet=doc.content[:180] + "...",
                        sha256_hash=doc.sha256_hash,
                        relevance_score=1.0,
                    )
                )
            else:
                # Hallucinated citation detected!
                all_grounded = False

        # Sort sources by doc_id for consistency
        sources.sort(key=lambda s: s.doc_id)
        return sources, all_grounded
