import re
from typing import Tuple, List
from backend.app.schemas.copilot_models import QueryIntent


class PromptInjectionDetectedException(Exception):
    """Raised when an adversarial prompt injection or jailbreak attempt is detected."""
    pass


class QuerySecurityProcessor:
    """Detects prompt injections, sanitizes user queries, and classifies investigative intent."""

    # High-risk instruction override patterns
    INJECTION_PATTERNS = [
        r"(?i)\bignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules|commands)",
        r"(?i)\bdisregard\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules|context)",
        r"(?i)\bforget\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)",
        r"(?i)\byou\s+are\s+now\s+(a|an)?\s*(unrestricted|jailbroken|dan|evil|hacker|rebel)",
        r"(?i)\bact\s+as\s+(a|an)?\s*(unrestricted|jailbroken|dan|evil|hacker)",
        r"(?i)\benter\s+dan\s+mode",
        r"(?i)\bdeveloper\s+mode\s+(enabled|on)",
        r"(?i)\breveal\s+(your\s+)?(system\s+prompt|instructions|initial\s+prompt)",
        r"(?i)\boutput\s+(the\s+)?(above\s+instructions|system\s+prompt)",
        r"(?i)\brepeat\s+(the\s+words\s+above|all\s+text\s+before|system\s+prompt)",
        r"(?i)<\s*/?\s*(system|instruction|context|authorized_document|evidence_data)\s*>",
        r"(?i)\[\s*(system|prompt|override)\s*\]",
        r"(?i)\bnow\s+answer\s+without\s+any\s+restrictions",
    ]

    # Intent classification keywords & regexes
    INTENT_PATTERNS = [
        (QueryIntent.CASE_SUMMARY, [
            r"(?i)\bsummar(y|ize)\b",
            r"(?i)\boverview\b",
            r"(?i)\bbrief(ing)?\b",
            r"(?i)\bwhat\s+is\s+this\s+case\s+about\b",
        ]),
        (QueryIntent.PERSONS_MENTIONED, [
            r"(?i)\bwho\s+are\s+the\s+persons\b",
            r"(?i)\bpersons?\s+mentioned\b",
            r"(?i)\bwho\s+is\s+involved\b",
            r"(?i)\bnames?\s+of\s+(people|persons|suspects|witnesses|victims|officers)\b",
            r"(?i)\bsuspects?\b",
            r"(?i)\bwitness(es)?\b",
            r"(?i)\baccused\b",
            r"(?i)\bcomplainant\b",
        ]),
        (QueryIntent.EVIDENCE_INVENTORY, [
            r"(?i)\bwhat\s+evidence\s+exists\b",
            r"(?i)\bevidence\s+(items|inventory|list|recovered)\b",
            r"(?i)\bphysical\s+evidence\b",
            r"(?i)\bdigital\s+evidence\b",
            r"(?i)\bseized\s+(items|materials|property)\b",
            r"(?i)\bweapon(s)?\b",
        ]),
        (QueryIntent.CHRONOLOGY, [
            r"(?i)\bchronological(ly)?\b",
            r"(?i)\btimeline\b",
            r"(?i)\border\s+of\s+events\b",
            r"(?i)\bsequence\s+of\s+events\b",
            r"(?i)\bwhat\s+happened\s+when\b",
            r"(?i)\bwhat\s+happened\s+chronologically\b",
        ]),
        (QueryIntent.RELATED_FIRS, [
            r"(?i)\brelated\s+fir(s)?\b",
            r"(?i)\bwhich\s+fir(s)?\b",
            r"(?i)\bconnected\s+cases\b",
            r"(?i)\bfirst\s+information\s+report(s)?\b",
            r"(?i)\bfir\s+number(s)?\b",
        ]),
        (QueryIntent.SUPPORTING_DOCS, [
            r"(?i)\bwhich\s+documents\s+support\b",
            r"(?i)\bsupporting\s+documents\b",
            r"(?i)\bwhat\s+docs\b",
            r"(?i)\bcitations?\b",
            r"(?i)\bdocumentary\s+proof\b",
        ]),
        (QueryIntent.LOCATIONS_MENTIONED, [
            r"(?i)\bwhat\s+locations\s+are\s+mentioned\b",
            r"(?i)\blocations?\b",
            r"(?i)\bplaces?\b",
            r"(?i)\bcrime\s+scene\b",
            r"(?i)\baddresses?\b",
            r"(?i)\bwhere\s+did\s+it\s+happen\b",
        ]),
    ]

    @classmethod
    def scan_for_injection(cls, query: str) -> None:
        """Evaluates query against known jailbreak and prompt override patterns.

        Raises PromptInjectionDetectedException if malicious intent is detected.
        """
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, query):
                raise PromptInjectionDetectedException(
                    f"Adversarial prompt injection attempt detected matching security rule: '{pattern}'."
                )

    @classmethod
    def sanitize_query(cls, query: str) -> str:
        """First screens for injection, then removes structural delimiters to avoid prompt boundary breakout."""
        cls.scan_for_injection(query)

        # Normalize whitespace and escape angle brackets to prevent XML tag breakout
        sanitized = query.strip()
        sanitized = re.sub(r"[\r\n\t]+", " ", sanitized)
        # Escape any rogue delimiters
        sanitized = sanitized.replace("<", "&lt;").replace(">", "&gt;")
        return sanitized

    @classmethod
    def classify_intent(cls, query: str) -> QueryIntent:
        """Classifies the investigative intent of the query."""
        for intent, patterns in cls.INTENT_PATTERNS:
            for pattern in patterns:
                if re.search(pattern, query):
                    return intent
        return QueryIntent.GENERAL_GROUNDED

    @classmethod
    def sanitize_untrusted_document_content(cls, content: str) -> str:
        """Sanitizes evidence text from potential indirect prompt injection (e.g.

        evidence files containing embedded commands aimed at hijacking the LLM).
        """
        # Neutralize XML tag spoofing inside document content
        safe_content = content.replace("<authorized_document", "&lt;authorized_document")
        safe_content = safe_content.replace("</authorized_document>", "&lt;/authorized_document&gt;")
        return safe_content
