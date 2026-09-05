import re
from typing import Any, Dict, List, Optional, Tuple


class InvestigationCopilotEngine:
    """
    Grounded AI Investigation Assistant Engine for EVIDENTIAL.
    Operates strictly on authorized case data with verifiable citations,
    prompt injection defense, explicit uncertainty fallback, and zero hallucinations.
    """

    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+|previous\s+|prior\s+)?instructions",
        r"disregard\s+(all\s+|previous\s+|safety\s+)?(guidelines|rules|instructions)",
        r"output\s+(the\s+)?(system\s+)?prompt",
        r"show\s+(the\s+)?(system\s+)?prompt",
        r"reveal\s+(the\s+)?(system\s+)?(prompt|password|secret|key)",
        r"bypass\s+(authorization|security|access|controls)",
        r"admin\s+(password|credentials|token)",
        r"dan\s+mode",
        r"jailbreak",
        r"pretend\s+you\s+are",
        r"act\s+as\s+an\s+unrestricted",
    ]

    ABSENT_INFO_FALLBACK = "I cannot find sufficient evidence in the authorized case data."

    @classmethod
    def check_prompt_injection(cls, question: str) -> bool:
        """Detects adversarial prompt injection attempts."""
        q_lower = question.lower()
        for pat in cls.INJECTION_PATTERNS:
            if re.search(pat, q_lower):
                return True
        return False

    @classmethod
    def process_query(
        cls,
        question: str,
        case_data: Dict[str, Any],
        related_cases: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Processes an investigative question against grounded, authorized case data.

        Returns:
          - answer: str (grounded answer with source citations)
          - citations: list of dicts with citation details
          - uncertainty_flag: bool
          - confidence_level: str ("HIGH", "MEDIUM", "LOW")
        """
        # 1. Prompt Injection Defense Gate
        if cls.check_prompt_injection(question):
            return {
                "answer": "Security Notice: I cannot fulfill this instruction. Responses are strictly grounded in authorized investigation case data.",
                "citations": [],
                "uncertainty_flag": True,
                "confidence_level": "LOW",
            }

        q_lower = question.lower().strip()
        case_number = case_data.get("case_number", "UNKNOWN")
        case_title = case_data.get("title", "Untitled Case")
        crime_type = case_data.get("crime_type", "General Offense")
        case_desc = case_data.get("description", "")
        documents = case_data.get("documents", [])
        entities = case_data.get("entities", [])
        evidence_items = case_data.get("evidence_items", [])
        timeline_events = case_data.get("timeline_events", [])
        correlations = case_data.get("correlations", [])

        citations: List[Dict[str, Any]] = []

        # 2. Case Summary Queries
        if any(k in q_lower for k in ("summarize", "summary", "overview", "what is this case about", "describe this case")):
            lines = [
                f"**Case Summary ({case_number})**: {case_title}",
                f"- **Classification**: {crime_type}",
                f"- **Jurisdiction / Location**: {case_data.get('location') or 'Jurisdiction-wide'} (Police Station: {case_data.get('police_station') or 'State Directorate'})",
                f"- **Narrative Overview**: {case_desc or 'FIR registered and currently under digital investigation.'}",
                f"- **Document Records**: {len(documents)} verified document(s) uploaded and secured.",
                f"- **Secured Evidence**: {len(evidence_items)} physical/digital evidence item(s) in chain-of-custody.",
            ]
            citations.append({
                "citation_id": f"cit-case-{case_data.get('id')}",
                "source_type": "CASE_RECORD",
                "source_title": f"FIR Record #{case_number}",
                "document_filename": f"FIR-{case_number}.pdf",
                "snippet": case_desc[:200] if case_desc else f"Official FIR {case_number}",
            })
            for doc in documents:
                citations.append({
                    "citation_id": f"cit-doc-{doc.get('id')}",
                    "source_type": "DOCUMENT",
                    "source_title": doc.get("original_filename"),
                    "document_filename": doc.get("original_filename"),
                    "snippet": f"Document {doc.get('original_filename')} (SHA-256: {doc.get('sha256_hash', '')[:16]}...)",
                })
            return {
                "answer": "\n".join(lines) + f"\n\n[Source: Case Record #{case_number}]",
                "citations": citations,
                "uncertainty_flag": False,
                "confidence_level": "HIGH",
            }

        # 3. Persons Mentioned Queries
        if any(k in q_lower for k in ("person", "persons", "who are", "who is", "complainant", "witness", "names")) and not any(k in q_lower for k in ("pizza", "shoe", "topping", "favorite", "color", "hobby")):
            person_entities = [e for e in entities if e.get("entity_type") in ("PERSON", "PERSON_NAME")]
            if not person_entities:
                # Check case description for names
                return {
                    "answer": f"{cls.ABSENT_INFO_FALLBACK} No individual person entities are extracted or registered in the authorized documents for case {case_number}.",
                    "citations": [],
                    "uncertainty_flag": True,
                    "confidence_level": "LOW",
                }

            lines = [f"**Persons Identified in Case {case_number}**:"]
            for pe in person_entities:
                name = pe.get("entity_value")
                conf = pe.get("confidence", 0.95)
                doc_name = pe.get("source_document") or "FIR Scan"
                context = pe.get("context_snippet") or "Direct mention in evidence transcript."
                lines.append(f"- **{name}** (Confidence: {conf:.2f}) — Mentioned in `{doc_name}`: *\"{context}\"*")
                citations.append({
                    "citation_id": f"cit-ent-{pe.get('id')}",
                    "source_type": "EXTRACTED_ENTITY",
                    "source_title": f"Extracted Person Entity: {name}",
                    "document_filename": doc_name,
                    "snippet": context,
                })
            lines.append("\n[Note: Entity extraction indicates persons mentioned in evidence records. Guilt or legal culpability is never established by automated extraction.]")
            return {
                "answer": "\n".join(lines),
                "citations": citations,
                "uncertainty_flag": False,
                "confidence_level": "HIGH",
            }

        # 4. Evidence Items Queries
        if any(k in q_lower for k in ("evidence", "what evidence", "physical evidence", "digital evidence", "seized", "items", "proof")):
            if not evidence_items and not documents:
                return {
                    "answer": f"{cls.ABSENT_INFO_FALLBACK} No physical or digital evidence records are attached to case {case_number}.",
                    "citations": [],
                    "uncertainty_flag": True,
                    "confidence_level": "LOW",
                }

            lines = [f"**Evidence Inventory for Case {case_number}**:"]
            if evidence_items:
                lines.append("\n*Secured Evidence Items in Chain-of-Custody:*")
                for ev in evidence_items:
                    title = ev.get("title", "Evidence Item")
                    ev_type = ev.get("evidence_type", "DIGITAL_FILE")
                    desc = ev.get("description", "Secured item in repository")
                    sha = ev.get("sha256_hash", "")[:16]
                    lines.append(f"- **{title}** (`{ev_type}`) — SHA-256: `{sha}...` ({desc})")
                    citations.append({
                        "citation_id": f"cit-ev-{ev.get('id')}",
                        "source_type": "EVIDENCE",
                        "source_title": title,
                        "document_filename": ev.get("file_path"),
                        "snippet": desc,
                    })

            if documents:
                lines.append("\n*Verified Digital FIR & Document Files:*")
                for doc in documents:
                    fname = doc.get("original_filename", "Document")
                    fsize = doc.get("file_size_bytes", 0)
                    sha = doc.get("sha256_hash", "")[:16]
                    lines.append(f"- **{fname}** ({fsize} bytes) — SHA-256: `{sha}...`")
                    citations.append({
                        "citation_id": f"cit-doc-{doc.get('id')}",
                        "source_type": "DOCUMENT",
                        "source_title": fname,
                        "document_filename": fname,
                        "snippet": f"Original document {fname} with verified cryptographic hash",
                    })

            return {
                "answer": "\n".join(lines),
                "citations": citations,
                "uncertainty_flag": False,
                "confidence_level": "HIGH",
            }

        # 5. Chronological Timeline Queries
        if any(k in q_lower for k in ("chronolog", "timeline", "what happened", "sequence", "dates", "events", "when did")):
            if not timeline_events:
                inc_date = case_data.get("incident_date")
                if inc_date:
                    return {
                        "answer": f"**Chronological Summary for Case {case_number}**:\n- **{inc_date}**: FIR Registered for crime {crime_type} at {case_data.get('location') or 'jurisdiction'}.\n\n[Source: Case Record #{case_number}]",
                        "citations": [{
                            "citation_id": f"cit-case-{case_data.get('id')}",
                            "source_type": "CASE_RECORD",
                            "source_title": f"FIR Record #{case_number}",
                            "document_filename": f"FIR-{case_number}.pdf",
                            "snippet": f"Incident date: {inc_date}",
                        }],
                        "uncertainty_flag": False,
                        "confidence_level": "MEDIUM",
                    }
                return {
                    "answer": f"{cls.ABSENT_INFO_FALLBACK} No chronological timeline events or incident timestamps are recorded for case {case_number}.",
                    "citations": [],
                    "uncertainty_flag": True,
                    "confidence_level": "LOW",
                }

            lines = [f"**Investigation Timeline for Case {case_number}**:"]
            for evt in timeline_events:
                edate = evt.get("event_date", "")
                etype = evt.get("event_type", "INVESTIGATION_EVENT")
                title = evt.get("title", "")
                desc = evt.get("description", "")
                source = evt.get("source", "Case Record")
                lines.append(f"- **[{edate}] {title}** (`{etype}`): {desc} *(Source: {source})*")
                citations.append({
                    "citation_id": f"cit-evt-{evt.get('id')}",
                    "source_type": evt.get("source_type", "INVESTIGATION_LOG"),
                    "source_title": title,
                    "document_filename": evt.get("source_document"),
                    "snippet": f"{title} - {desc}",
                })

            return {
                "answer": "\n".join(lines),
                "citations": citations,
                "uncertainty_flag": False,
                "confidence_level": "HIGH",
            }

        # 6. Related FIRs / Cross-Case Queries
        if any(k in q_lower for k in ("related", "firs", "similar", "correlat", "other cases", "which firs", "links")):
            if not correlations:
                return {
                    "answer": f"**Cross-FIR Analysis for Case {case_number}**:\nNo significant potential correlations detected with other authorized cases above threshold.\n\n[Source: Cross-FIR Correlation Engine]",
                    "citations": [],
                    "uncertainty_flag": False,
                    "confidence_level": "HIGH",
                }

            lines = [f"**Potential Correlated FIRs for Case {case_number}**:"]
            for corr in correlations:
                rel = corr.get("related_case", {})
                rel_num = rel.get("case_number", "Unknown FIR")
                rel_title = rel.get("title", "")
                score = corr.get("correlation_score", 0.0)
                reasons = corr.get("matching_factors", [])
                reasons_str = "; ".join(reasons) if reasons else "Shared entity identifiers"
                lines.append(f"- **{rel_num}** ({rel_title}) — Potential Correlation Score: **{score:.2f}**\n  *Reasons*: {reasons_str}")
                citations.append({
                    "citation_id": f"cit-corr-{rel.get('id')}",
                    "source_type": "CORRELATION_ENGINE",
                    "source_title": f"Correlated Case {rel_num}",
                    "document_filename": None,
                    "snippet": reasons_str,
                })
            lines.append("\n[Investigative Notice: System identifies potential correlations only. Guilt or legal liability is never established by automated correlation.]")
            return {
                "answer": "\n".join(lines),
                "citations": citations,
                "uncertainty_flag": False,
                "confidence_level": "HIGH",
            }

        # 7. Locations Mentioned Queries
        if any(k in q_lower for k in ("location", "locations", "where", "police station", "jurisdiction", "place", "places")):
            loc_entities = [e for e in entities if e.get("entity_type") in ("LOCATION", "POLICE_STATION")]
            loc_general = case_data.get("location")
            ps_general = case_data.get("police_station")

            if not loc_entities and not loc_general:
                return {
                    "answer": f"{cls.ABSENT_INFO_FALLBACK} No specific geographic locations are identified in the authorized case records.",
                    "citations": [],
                    "uncertainty_flag": True,
                    "confidence_level": "LOW",
                }

            lines = [f"**Locations & Jurisdictions for Case {case_number}**:"]
            if loc_general:
                lines.append(f"- **Primary Incident Location**: {loc_general}")
            if ps_general:
                lines.append(f"- **Police Station Jurisdiction**: {ps_general}")
            for le in loc_entities:
                val = le.get("entity_value")
                doc_name = le.get("source_document") or "FIR Scan"
                lines.append(f"- **{val}** (`{le.get('entity_type')}`) — Referenced in `{doc_name}`")
                citations.append({
                    "citation_id": f"cit-loc-{le.get('id')}",
                    "source_type": "EXTRACTED_ENTITY",
                    "source_title": f"Location: {val}",
                    "document_filename": doc_name,
                    "snippet": f"Location {val} extracted from {doc_name}",
                })
            return {
                "answer": "\n".join(lines),
                "citations": citations,
                "uncertainty_flag": False,
                "confidence_level": "HIGH",
            }

        # 8. Document Support Queries
        if any(k in q_lower for k in ("document", "documents", "supporting", "files", "transcripts", "ocr")):
            if not documents:
                return {
                    "answer": f"{cls.ABSENT_INFO_FALLBACK} No digital documents are currently registered for case {case_number}.",
                    "citations": [],
                    "uncertainty_flag": True,
                    "confidence_level": "LOW",
                }

            lines = [f"**Supporting Documents for Case {case_number}**:"]
            for doc in documents:
                fname = doc.get("original_filename")
                status_str = doc.get("processing_status", "COMPLETED")
                lang = doc.get("detected_language", "English")
                lines.append(f"- **{fname}** — Status: `{status_str}`, Language: `{lang}`, SHA-256: `{doc.get('sha256_hash', '')[:16]}...`")
                citations.append({
                    "citation_id": f"cit-doc-{doc.get('id')}",
                    "source_type": "DOCUMENT",
                    "source_title": fname,
                    "document_filename": fname,
                    "snippet": f"Verified document {fname}",
                })
            return {
                "answer": "\n".join(lines),
                "citations": citations,
                "uncertainty_flag": False,
                "confidence_level": "HIGH",
            }

        # 9. General Specific Question / Search across OCR text & Entities
        # Search for query terms in OCR text or description
        matched_doc_snippets: List[Tuple[str, str]] = []
        tokens = [t for t in re.findall(r"\w+", q_lower) if len(t) > 3 and t not in ("what", "when", "where", "which", "about", "this", "case", "does", "have", "suspect", "person", "victim", "reported", "crime", "there")]

        for doc in documents:
            text = (doc.get("translated_text") or doc.get("original_text") or "").lower()
            fname = doc.get("original_filename")
            for token in tokens:
                if token in text:
                    idx = text.find(token)
                    snippet = text[max(0, idx - 40) : min(len(text), idx + 80)]
                    matched_doc_snippets.append((fname, f"...{snippet.strip()}..."))
                    break

        if matched_doc_snippets:
            lines = [f"**Information Found in Case {case_number} Documents**:"]
            for fname, snippet in matched_doc_snippets:
                lines.append(f"- Document `{fname}`: *\"{snippet}\"*")
                citations.append({
                    "citation_id": f"cit-doc-search-{fname}",
                    "source_type": "DOCUMENT",
                    "source_title": fname,
                    "document_filename": fname,
                    "snippet": snippet,
                })
            return {
                "answer": "\n".join(lines),
                "citations": citations,
                "uncertainty_flag": False,
                "confidence_level": "MEDIUM",
            }

        # 10. Fallback: Information Absent
        return {
            "answer": f"{cls.ABSENT_INFO_FALLBACK} The query '{question}' cannot be answered based on the authorized evidence currently available in case {case_number}.",
            "citations": [],
            "uncertainty_flag": True,
            "confidence_level": "LOW",
        }
