import re
from typing import Dict, List, Tuple


class ClassificationResult:
    def __init__(
        self,
        primary_category: str,
        confidence: float,
        matched_sections: List[str],
        recommended_priority: str,
        category_scores: Dict[str, float],
    ):
        self.primary_category = primary_category
        self.confidence = float(confidence)
        self.matched_sections = matched_sections
        self.recommended_priority = recommended_priority
        self.category_scores = category_scores

    def to_dict(self) -> Dict:
        return {
            "primary_category": self.primary_category,
            "confidence": round(self.confidence, 4),
            "matched_sections": self.matched_sections,
            "recommended_priority": self.recommended_priority,
            "category_scores": {k: round(v, 4) for k, v in self.category_scores.items()},
        }


class DocumentClassifier:
    """
    Crime Category & Severity Classification Engine based on Indian Legal Statutes and Context.
    """

    TAXONOMY = {
        "CYBER_CRIME": {
            "sections": ["66", "66C", "66D", "66E", "43", "72", "420", "318"],
            "keywords": ["cyber", "phishing", "otp", "sim swap", "malware", "hacked", "online transfer", "crypto", "ransomware", "unauthorized debit", "fake website", "whatsapp fraud", "telegram task"],
            "priority": "HIGH",
            "base_weight": 1.2,
        },
        "FINANCIAL_FRAUD": {
            "sections": ["420", "406", "467", "468", "471", "120B", "318", "316", "336", "338"],
            "keywords": ["cheating", "fraud", "forgery", "embezzlement", "ponzi", "bank account", "cheque bounce", "loan default", "counterfeit", "fake document", "misappropriation"],
            "priority": "HIGH",
            "base_weight": 1.1,
        },
        "VIOLENT_CRIME": {
            "sections": ["302", "307", "323", "324", "326", "376", "392", "394", "395", "397", "364", "365", "103", "109", "115"],
            "keywords": ["murder", "assault", "homicide", "stabbing", "gunshot", "robbery", "dacoity", "kidnapping", "grievous hurt", "attack", "blood", "threat to life"],
            "priority": "CRITICAL",
            "base_weight": 1.4,
        },
        "PROPERTY_CRIME": {
            "sections": ["379", "380", "454", "457", "411", "303", "305", "331"],
            "keywords": ["theft", "stolen", "burglary", "housebreaking", "stolen vehicle", "jewellery stolen", "trespass", "pickpocket"],
            "priority": "MEDIUM",
            "base_weight": 1.0,
        },
        "NARCOTICS": {
            "sections": ["8", "20", "21", "22", "27A", "29", "NDPS"],
            "keywords": ["narcotics", "contraband", "ganja", "heroin", "cocaine", "mdma", "smuggling", "meth", "drug peddling", "substance"],
            "priority": "CRITICAL",
            "base_weight": 1.3,
        },
        "ORGANIZED_CRIME": {
            "sections": ["384", "386", "387", "120B", "Arms Act", "MCOCA", "308"],
            "keywords": ["extortion", "protection money", "gang", "syndicate", "firearms", "illegal weapon", "pistol", "cartridge", "blackmail"],
            "priority": "HIGH",
            "base_weight": 1.2,
        },
    }

    @classmethod
    def classify_document(cls, text: str, law_sections: List[str] = None) -> ClassificationResult:
        """
        Classifies document text into crime categories and determines priority.
        """
        if not text:
            return ClassificationResult(
                primary_category="GENERAL_OFFENSE",
                confidence=0.50,
                matched_sections=[],
                recommended_priority="LOW",
                category_scores={"GENERAL_OFFENSE": 0.50},
            )

        text_lower = text.lower()
        sections_found: List[str] = list(law_sections) if law_sections else []
        
        # Also scan text for sections if not passed
        sec_matches = re.findall(r"(?:Section|Sec\.?|धारा)\s*([\d\w/]+)", text, re.IGNORECASE)
        sections_found.extend([s.upper() for s in sec_matches])
        sections_found = list(set(sections_found))

        scores: Dict[str, float] = {}

        for category, config in cls.TAXONOMY.items():
            cat_score = 0.0

            # 1. Check legal sections (strong signal)
            for target_sec in config["sections"]:
                for found_sec in sections_found:
                    if target_sec in found_sec:
                        cat_score += 2.5

            # 2. Check keywords
            for kw in config["keywords"]:
                count = len(re.findall(rf"\b{re.escape(kw)}\b", text_lower))
                if count > 0:
                    cat_score += min(count, 3) * 0.8

            # Apply domain weight
            cat_score *= config["base_weight"]
            scores[category] = cat_score

        # Find best category
        best_cat = max(scores, key=scores.get)
        best_raw_score = scores[best_cat]

        if best_raw_score == 0.0:
            return ClassificationResult(
                primary_category="GENERAL_OFFENSE",
                confidence=0.60,
                matched_sections=sections_found,
                recommended_priority="MEDIUM",
                category_scores={"GENERAL_OFFENSE": 0.60},
            )

        # Normalize confidence to [0.65, 0.98]
        confidence = min(0.98, max(0.65, 0.65 + (best_raw_score / 20.0)))
        recommended_priority = cls.TAXONOMY.get(best_cat, {}).get("priority", "MEDIUM")

        return ClassificationResult(
            primary_category=best_cat,
            confidence=confidence,
            matched_sections=sections_found,
            recommended_priority=recommended_priority,
            category_scores=scores,
        )
