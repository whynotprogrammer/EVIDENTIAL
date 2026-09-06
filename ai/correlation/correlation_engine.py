from datetime import datetime, timezone
import difflib
import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from ai.embeddings.embedder import DocumentEmbedder


class CorrelationEngine:
    """
    Explainable Cross-FIR Correlation Engine for EVIDENTIAL.
    Compares investigation cases across 8 dimensions:
      1. PERSON (Fuzzy & alias matching)
      2. PHONE (Normalized identifier matching)
      3. EMAIL (Normalized digital identifier matching)
      4. VEHICLE (Alphanumeric plate normalization & prefix matching)
      5. LOCATION (Fuzzy geographic & police station matching)
      6. CRIME TYPE (Taxonomy & statutory section overlap)
      7. DATE/TIME (Temporal proximity scoring)
      8. SEMANTIC SIMILARITY (Dense vector cosine similarity via DocumentEmbedder)

    LEGAL & ETHICAL MANDATE:
      - Never outputs "Person X committed the crime" or establishes guilt.
      - Always outputs "Potential correlation detected" or "Potential correlation".
    """

    # Scoring weights for composite correlation score
    WEIGHTS = {
        "PHONE": 0.22,
        "VEHICLE": 0.18,
        "PERSON": 0.15,
        "EMAIL": 0.12,
        "LOCATION": 0.10,
        "CRIME_TYPE": 0.08,
        "SEMANTIC": 0.10,
        "TEMPORAL": 0.05,
    }

    FORBIDDEN_PHRASES = [
        "committed the crime",
        "is guilty",
        "was guilty",
        "perpetrated the crime",
        "is the culprit",
        "guilty of",
        "criminal responsibility established",
    ]

    FIR_WEIGHTS = {
        "CRIME_GROUP": 0.30, "CRIME_HEAD": 0.15, "DISTRICT": 0.15,
        "POLICE_UNIT": 0.12, "YEAR": 0.06, "MONTH": 0.03,
        "GEO": 0.12, "SEMANTIC": 0.07,
    }

    @classmethod
    def normalize_phone(cls, phone: Optional[str]) -> str:
        """Extract only digits from a phone number, preserving last 10 digits for Indian standard."""
        if not phone:
            return ""
        digits = re.sub(r"\D", "", phone)
        if len(digits) > 10:
            return digits[-10:]
        return digits

    @classmethod
    def normalize_vehicle(cls, vehicle: Optional[str]) -> str:
        """Uppercase and strip non-alphanumeric characters from vehicle registration number."""
        if not vehicle:
            return ""
        return re.sub(r"[^A-Z0-9]", "", vehicle.upper())

    @classmethod
    def fuzzy_string_similarity(cls, str1: Optional[str], str2: Optional[str]) -> float:
        """Computes SequenceMatcher ratio between two strings."""
        if not str1 or not str2:
            return 0.0
        s1 = str1.strip().lower()
        s2 = str2.strip().lower()
        if s1 == s2:
            return 1.0
        tokens1 = set(re.findall(r"\w+", s1))
        tokens2 = set(re.findall(r"\w+", s2))
        if tokens1 and tokens2:
            intersection = tokens1.intersection(tokens2)
            if intersection:
                overlap_ratio = len(intersection) / min(len(tokens1), len(tokens2))
                jaccard = len(intersection) / len(tokens1.union(tokens2))
                seq_ratio = difflib.SequenceMatcher(None, s1, s2).ratio()
                if tokens1.issubset(tokens2) or tokens2.issubset(tokens1):
                    return max(seq_ratio, 0.88)
                return max(seq_ratio, jaccard, overlap_ratio * 0.85)
        return difflib.SequenceMatcher(None, s1, s2).ratio()

    @classmethod
    def compute_temporal_proximity(
        cls, date1: Optional[datetime], date2: Optional[datetime]
    ) -> Tuple[float, Optional[int]]:
        """
        Computes temporal proximity score based on incident date differences.
        Score decays with time difference:
          - 0 days (same day): 1.0
          - <= 3 days: 0.9
          - <= 7 days: 0.8
          - <= 14 days: 0.65
          - <= 30 days: 0.50
          - <= 90 days: 0.25
          - > 90 days: 0.05
        """
        if not date1 or not date2:
            return 0.0, None

        diff_days = abs((date1 - date2).days)
        if diff_days == 0:
            return 1.0, 0
        elif diff_days <= 3:
            return 0.9, diff_days
        elif diff_days <= 7:
            return 0.8, diff_days
        elif diff_days <= 14:
            return 0.65, diff_days
        elif diff_days <= 30:
            return 0.5, diff_days
        elif diff_days <= 90:
            return 0.25, diff_days
        else:
            return 0.05, diff_days

    @classmethod
    def compare_cases(
        cls,
        source_case_data: Dict[str, Any],
        related_case_data: Dict[str, Any],
        min_threshold: float = 0.25,
    ) -> Dict[str, Any]:
        """
        Main explainable correlation method comparing source and related case.

        Expected input dict keys:
          - id, case_number, title, description, crime_type, location, police_station, incident_date
          - entities: list of dicts with 'entity_type', 'entity_value', 'normalized_value'
          - documents: list of dicts with 'original_text', 'translated_text'
        """
        # Imported FIRs are compared using their real structured source fields.
        if source_case_data.get("source_record_key") and related_case_data.get("source_record_key"):
            return cls._compare_imported_firs(source_case_data, related_case_data)

        matching_factors: List[str] = []
        matching_entities: List[Dict[str, Any]] = []
        factor_scores: Dict[str, float] = {}

        # 1. PHONE MATCHING
        phones_src = {
            cls.normalize_phone(e["normalized_value"] or e["entity_value"])
            for e in source_case_data.get("entities", [])
            if e.get("entity_type") in ("PHONE", "PHONE_NUMBER")
        }
        phones_rel = {
            cls.normalize_phone(e["normalized_value"] or e["entity_value"])
            for e in related_case_data.get("entities", [])
            if e.get("entity_type") in ("PHONE", "PHONE_NUMBER")
        }
        phones_src.discard("")
        phones_rel.discard("")

        common_phones = phones_src.intersection(phones_rel)
        if common_phones:
            factor_scores["PHONE"] = 1.0
            for ph in common_phones:
                matching_factors.append(f"Shared phone identifier (+91-{ph})")
                matching_entities.append({
                    "entity_type": "PHONE",
                    "source_value": ph,
                    "related_value": ph,
                    "similarity": 1.0,
                    "match_type": "EXACT",
                })
        else:
            factor_scores["PHONE"] = 0.0

        # 2. VEHICLE MATCHING
        vehicles_src = {
            cls.normalize_vehicle(e["normalized_value"] or e["entity_value"]): e["entity_value"]
            for e in source_case_data.get("entities", [])
            if e.get("entity_type") in ("VEHICLE", "VEHICLE_NUMBER")
        }
        vehicles_rel = {
            cls.normalize_vehicle(e["normalized_value"] or e["entity_value"]): e["entity_value"]
            for e in related_case_data.get("entities", [])
            if e.get("entity_type") in ("VEHICLE", "VEHICLE_NUMBER")
        }

        best_veh_score = 0.0
        for v_norm_src, v_orig_src in vehicles_src.items():
            if not v_norm_src:
                continue
            for v_norm_rel, v_orig_rel in vehicles_rel.items():
                if not v_norm_rel:
                    continue
                if v_norm_src == v_norm_rel:
                    best_veh_score = max(best_veh_score, 1.0)
                    matching_factors.append(f"Shared vehicle identifier ({v_orig_src})")
                    matching_entities.append({
                        "entity_type": "VEHICLE",
                        "source_value": v_orig_src,
                        "related_value": v_orig_rel,
                        "similarity": 1.0,
                        "match_type": "EXACT",
                    })
                elif cls.fuzzy_string_similarity(v_norm_src, v_norm_rel) >= 0.85:
                    sim = cls.fuzzy_string_similarity(v_norm_src, v_norm_rel)
                    best_veh_score = max(best_veh_score, sim * 0.9)
                    matching_factors.append(f"Similar vehicle identifier ({v_orig_src} ~ {v_orig_rel})")
                    matching_entities.append({
                        "entity_type": "VEHICLE",
                        "source_value": v_orig_src,
                        "related_value": v_orig_rel,
                        "similarity": round(sim, 3),
                        "match_type": "FUZZY",
                    })
        factor_scores["VEHICLE"] = best_veh_score

        # 3. PERSON MATCHING (Fuzzy, Alias, and Cross-spelling)
        persons_src = [
            e["entity_value"].strip()
            for e in source_case_data.get("entities", [])
            if e.get("entity_type") == "PERSON" and len(e["entity_value"].strip()) > 2
        ]
        persons_rel = [
            e["entity_value"].strip()
            for e in related_case_data.get("entities", [])
            if e.get("entity_type") == "PERSON" and len(e["entity_value"].strip()) > 2
        ]

        best_person_score = 0.0
        for p_src in persons_src:
            for p_rel in persons_rel:
                sim = cls.fuzzy_string_similarity(p_src, p_rel)
                if sim >= 0.80:
                    best_person_score = max(best_person_score, sim)
                    m_type = "EXACT" if sim >= 0.98 else "FUZZY_NAME_VARIANT"
                    matching_factors.append(f"Similar person entity ({p_src} ~ {p_rel})")
                    matching_entities.append({
                        "entity_type": "PERSON",
                        "source_value": p_src,
                        "related_value": p_rel,
                        "similarity": round(sim, 3),
                        "match_type": m_type,
                    })
        factor_scores["PERSON"] = best_person_score

        # 4. EMAIL MATCHING
        emails_src = {
            e["entity_value"].strip().lower()
            for e in source_case_data.get("entities", [])
            if e.get("entity_type") == "EMAIL" and "@" in e["entity_value"]
        }
        emails_rel = {
            e["entity_value"].strip().lower()
            for e in related_case_data.get("entities", [])
            if e.get("entity_type") == "EMAIL" and "@" in e["entity_value"]
        }
        common_emails = emails_src.intersection(emails_rel)
        if common_emails:
            factor_scores["EMAIL"] = 1.0
            for em in common_emails:
                matching_factors.append(f"Shared electronic mail identifier ({em})")
                matching_entities.append({
                    "entity_type": "EMAIL",
                    "source_value": em,
                    "related_value": em,
                    "similarity": 1.0,
                    "match_type": "EXACT",
                })
        else:
            factor_scores["EMAIL"] = 0.0

        # 5. LOCATION MATCHING
        loc_src = source_case_data.get("location") or ""
        loc_rel = related_case_data.get("location") or ""
        ps_src = source_case_data.get("police_station") or ""
        ps_rel = related_case_data.get("police_station") or ""

        loc_entities_src = [
            e["entity_value"]
            for e in source_case_data.get("entities", [])
            if e.get("entity_type") in ("LOCATION", "POLICE_STATION")
        ]
        loc_entities_rel = [
            e["entity_value"]
            for e in related_case_data.get("entities", [])
            if e.get("entity_type") in ("LOCATION", "POLICE_STATION")
        ]

        loc_score = 0.0
        if loc_src and loc_rel:
            sim_loc = cls.fuzzy_string_similarity(loc_src, loc_rel)
            if sim_loc >= 0.70:
                loc_score = max(loc_score, sim_loc)
                matching_factors.append(f"Common geographic location ({loc_src})")

        if ps_src and ps_rel and cls.fuzzy_string_similarity(ps_src, ps_rel) >= 0.80:
            loc_score = max(loc_score, 0.9)
            matching_factors.append(f"Same police station jurisdiction ({ps_src})")

        for le_s in loc_entities_src:
            for le_r in loc_entities_rel:
                sim = cls.fuzzy_string_similarity(le_s, le_r)
                if sim >= 0.85:
                    loc_score = max(loc_score, sim)
                    matching_factors.append(f"Matching landmark/jurisdiction ({le_s})")
                    break

        factor_scores["LOCATION"] = min(loc_score, 1.0)

        # 6. CRIME TYPE MATCHING
        ct_src = (source_case_data.get("crime_type") or "").strip().upper()
        ct_rel = (related_case_data.get("crime_type") or "").strip().upper()

        if ct_src and ct_rel:
            if ct_src == ct_rel:
                factor_scores["CRIME_TYPE"] = 1.0
                matching_factors.append(f"Identical crime classification ({ct_src})")
            elif cls.fuzzy_string_similarity(ct_src, ct_rel) >= 0.70:
                factor_scores["CRIME_TYPE"] = 0.75
                matching_factors.append(f"Related crime taxonomy ({ct_src} ~ {ct_rel})")
            else:
                factor_scores["CRIME_TYPE"] = 0.0
        else:
            factor_scores["CRIME_TYPE"] = 0.0

        # 7. TEMPORAL PROXIMITY
        date_src = source_case_data.get("incident_date")
        date_rel = related_case_data.get("incident_date")

        # Parse string ISO dates if needed
        if isinstance(date_src, str):
            try:
                date_src = datetime.fromisoformat(date_src.replace("Z", "+00:00"))
            except Exception:
                date_src = None
        if isinstance(date_rel, str):
            try:
                date_rel = datetime.fromisoformat(date_rel.replace("Z", "+00:00"))
            except Exception:
                date_rel = None

        temp_score, diff_days = cls.compute_temporal_proximity(date_src, date_rel)
        factor_scores["TEMPORAL"] = temp_score
        if diff_days is not None and diff_days <= 14:
            matching_factors.append(
                f"Temporal proximity: incidents occurred within {diff_days} day{'s' if diff_days != 1 else ''}"
            )

        # 8. SEMANTIC SIMILARITY (Narrative & Document Translation Text)
        text_src_parts = [
            source_case_data.get("title") or "",
            source_case_data.get("description") or "",
        ]
        for d in source_case_data.get("documents", []):
            text_src_parts.append(d.get("translated_text") or d.get("original_text") or "")
        full_text_src = " ".join(text_src_parts).strip()

        text_rel_parts = [
            related_case_data.get("title") or "",
            related_case_data.get("description") or "",
        ]
        for d in related_case_data.get("documents", []):
            text_rel_parts.append(d.get("translated_text") or d.get("original_text") or "")
        full_text_rel = " ".join(text_rel_parts).strip()

        if full_text_src and full_text_rel:
            vec_a = DocumentEmbedder.generate_embedding(full_text_src)
            vec_b = DocumentEmbedder.generate_embedding(full_text_rel)
            sem_sim = DocumentEmbedder.cosine_similarity(vec_a, vec_b)
            factor_scores["SEMANTIC"] = max(0.0, min(sem_sim, 1.0))
            if sem_sim >= 0.65:
                matching_factors.append(f"High semantic narrative correlation (similarity: {sem_sim:.2f})")
        else:
            factor_scores["SEMANTIC"] = 0.0

        # COMPUTE WEIGHTED COMPOSITE SCORE
        # Dynamic weighting based on available dimensions
        composite_score = sum(
            cls.WEIGHTS[dim] * factor_scores[dim] for dim in cls.WEIGHTS
        )
        # Cap at 1.0 and round to 3 decimal places
        final_score = round(min(composite_score, 1.0), 3)

        # GENERATE EXPLAINABLE RATIONALE
        # De-duplicate factors
        unique_factors = list(dict.fromkeys(matching_factors))

        explanation = cls._generate_explanation(
            score=final_score,
            factors=unique_factors,
            has_entities=bool(matching_entities),
        )

        # Enforce legal guardrail check
        cls._assert_ethical_guardrails(explanation)

        return {
            "source_case": {
                "id": source_case_data.get("id"),
                "case_number": source_case_data.get("case_number"),
                "title": source_case_data.get("title"),
                "crime_type": source_case_data.get("crime_type"),
            },
            "related_case": {
                "id": related_case_data.get("id"),
                "case_number": related_case_data.get("case_number"),
                "title": related_case_data.get("title"),
                "crime_type": related_case_data.get("crime_type"),
            },
            "correlation_score": final_score,
            "matching_entities": matching_entities,
            "matching_factors": unique_factors,
            "factor_scores": factor_scores,
            "explanation": explanation,
        }

    @classmethod
    def _fir_representation(cls, case: Dict[str, Any]) -> str:
        """Deterministic local representation from actual FIR source fields."""
        fields = ("district", "police_station", "fir_year", "fir_month", "crime_type", "crime_head", "fir_stage", "location", "fir_type", "act_section")
        return " ".join(str(case[field]) for field in fields if case.get(field) not in (None, ""))

    @staticmethod
    def _coordinate_distance_km(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
        radius_km = 6371.0
        a_lat, a_lon, b_lat, b_lon = map(math.radians, (a_lat, a_lon, b_lat, b_lon))
        d_lat, d_lon = b_lat - a_lat, b_lon - a_lon
        h = math.sin(d_lat / 2) ** 2 + math.cos(a_lat) * math.cos(b_lat) * math.sin(d_lon / 2) ** 2
        return radius_km * 2 * math.asin(math.sqrt(h))

    @classmethod
    def _compare_imported_firs(cls, source: Dict[str, Any], related: Dict[str, Any]) -> Dict[str, Any]:
        """Conservative, explainable similarity over imported FIR data only."""
        factors: List[str] = []
        scores: Dict[str, float] = {key: 0.0 for key in cls.FIR_WEIGHTS}

        def equal(field: str, key: str, label: str) -> None:
            left, right = source.get(field), related.get(field)
            if left not in (None, "") and right not in (None, "") and str(left).strip().casefold() == str(right).strip().casefold():
                scores[key] = 1.0
                factors.append(f"Same {label} ({left})")

        equal("crime_type", "CRIME_GROUP", "crime group")
        equal("crime_head", "CRIME_HEAD", "crime head")
        equal("district", "DISTRICT", "district")
        equal("police_station", "POLICE_UNIT", "police unit")
        equal("fir_year", "YEAR", "FIR year")
        equal("fir_month", "MONTH", "FIR month")

        coordinates = (source.get("latitude"), source.get("longitude"), related.get("latitude"), related.get("longitude"))
        if all(value is not None for value in coordinates):
            distance = cls._coordinate_distance_km(*coordinates)
            if distance <= 5:
                scores["GEO"] = 1.0
                factors.append(f"Recorded coordinates are approximately {distance:.1f} km apart")
            elif distance <= 20:
                scores["GEO"] = 0.5
                factors.append(f"Recorded coordinates are approximately {distance:.1f} km apart")

        semantic = DocumentEmbedder.cosine_similarity(
            DocumentEmbedder.generate_embedding(cls._fir_representation(source)),
            DocumentEmbedder.generate_embedding(cls._fir_representation(related)),
        )
        if semantic >= 0.55:
            scores["SEMANTIC"] = semantic
            factors.append(f"Similar FIR field representation (similarity: {semantic:.2f})")

        structured_match = any(scores[key] > 0 for key in ("CRIME_GROUP", "CRIME_HEAD", "DISTRICT", "POLICE_UNIT", "YEAR", "MONTH", "GEO"))
        score = sum(cls.FIR_WEIGHTS[key] * scores[key] for key in cls.FIR_WEIGHTS) if structured_match else 0.0
        score = round(min(score, 1.0), 3)
        explanation = cls._generate_explanation(score, factors, False)
        cls._assert_ethical_guardrails(explanation)
        return {
            "source_case": {key: source.get(key) for key in ("id", "case_number", "title", "crime_type")},
            "related_case": {key: related.get(key) for key in ("id", "case_number", "title", "crime_type")},
            "correlation_score": score,
            "matching_entities": [], "matching_factors": factors,
            "factor_scores": scores, "explanation": explanation,
        }

    @classmethod
    def _generate_explanation(
        cls, score: float, factors: List[str], has_entities: bool
    ) -> str:
        """
        Generates explainable narrative string strictly compliant with legal guardrails.
        """
        lines: List[str] = []
        if score >= 0.70:
            lines.append("Potential correlation detected (High confidence).")
            lines.append(f"\nScore: {score:.2f}")
        elif score >= 0.40:
            lines.append("Potential correlation detected (Moderate confidence).")
            lines.append(f"\nScore: {score:.2f}")
        elif score >= 0.25:
            lines.append("Potential correlation detected (Low confidence).")
            lines.append(f"\nScore: {score:.2f}")
        else:
            lines.append("Potential correlation unlikely (Minimal overlap).")
            lines.append(f"\nScore: {score:.2f}")

        if factors:
            lines.append("\nReasons:")
            for f in factors:
                lines.append(f"- {f}")
        else:
            lines.append("\nReasons:\n- No significant shared identifiers or narrative overlap identified.")

        lines.append("\n[INVESTIGATIVE NOTICE: System indicates potential correlation only. Legal liability is never established by automated correlation.]")

        return "\n".join(lines)

    @classmethod
    def _assert_ethical_guardrails(cls, text: str):
        """
        Strict runtime assertion to guarantee that guilt or accusations are never produced.
        """
        lowered = text.lower()
        for forbidden in cls.FORBIDDEN_PHRASES:
            if forbidden in lowered:
                raise ValueError(
                    f"ETHICAL GUARDRAIL VIOLATION: Forbidden phrase '{forbidden}' detected in correlation output."
                )
