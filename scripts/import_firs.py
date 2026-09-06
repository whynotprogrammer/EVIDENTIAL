"""Idempotently import the supplied Karnataka Police FIR CSV into EVIDENTIAL.

The source file has no FIR-number column.  ``source_record_key`` is therefore a
SHA-256 fingerprint of the untouched source row, used solely to make imports
repeatable.  It is not presented as, or intended to replace, an FIR number.
"""

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import inspect, text

from backend.app.db.base import Base
from backend.app.db.session import SessionLocal, engine
from backend.app.models.case import Case, CasePriority, CaseStatus


DEFAULT_CSV = ROOT / "data" / "FIR_Details_500.csv"

# create_all does not add fields to an existing local SQLite database.
CASE_COLUMN_SQL = {
    # Include pre-existing Case columns because early local EVIDENTIAL databases
    # were created before several of the current model fields existed.
    "case_number": "VARCHAR(64)", "title": "VARCHAR(255)", "description": "TEXT",
    "crime_type": "VARCHAR(128)", "status": "VARCHAR(32)", "priority": "VARCHAR(32)",
    "police_station": "VARCHAR(128)", "district": "VARCHAR(128)", "state": "VARCHAR(128)",
    "location": "VARCHAR(255)", "incident_date": "DATETIME", "created_by_id": "INTEGER",
    "assigned_officer_id": "INTEGER", "created_at": "DATETIME", "updated_at": "DATETIME",
    "source_record_key": "VARCHAR(64)", "fir_year": "INTEGER", "fir_month": "INTEGER",
    "fir_day": "INTEGER", "fir_type": "VARCHAR(64)", "fir_stage": "VARCHAR(255)",
    "complaint_mode": "VARCHAR(128)", "crime_head": "VARCHAR(255)", "latitude": "FLOAT",
    "longitude": "FLOAT", "offence_duration": "VARCHAR(128)", "act_section": "TEXT",
    "io_name": "VARCHAR(255)", "kgid": "VARCHAR(64)", "internal_io": "VARCHAR(64)",
    "distance_from_ps": "VARCHAR(255)", "beat_name": "VARCHAR(255)",
    "village_area_name": "VARCHAR(255)", "male": "INTEGER", "female": "INTEGER",
    "boy": "INTEGER", "girl": "INTEGER", "age_0": "INTEGER", "victim_count": "INTEGER",
    "accused_count": "INTEGER", "arrested_male": "INTEGER", "arrested_female": "INTEGER",
    "arrested_count": "INTEGER", "accused_chargesheeted_count": "INTEGER",
    "conviction_count": "INTEGER", "unit_id": "VARCHAR(64)", "source_payload": "JSON",
}


def missing(value: Optional[str]) -> Optional[str]:
    """Convert only empty source cells to NULL; otherwise preserve the value."""
    return None if value is None or value == "" else value


def integer(value: Optional[str]) -> Optional[int]:
    value = missing(value)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def coordinate(value: Optional[str], lower: float, upper: float) -> Optional[float]:
    value = missing(value)
    if value is None:
        return None
    try:
        result = float(value)
    except ValueError:
        return None
    return result if lower <= result <= upper else None


def incident_date(row: dict[str, str]) -> Optional[datetime]:
    try:
        return datetime(int(row["FIR_YEAR"]), int(row["FIR_MONTH"]), int(row["FIR_Day"]))
    except (KeyError, TypeError, ValueError):
        return None


def source_key(row: dict[str, str]) -> str:
    # Compact, ordered JSON is stable for the same CSV row and retains raw values.
    raw = json.dumps(row, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def ensure_case_columns() -> None:
    Base.metadata.create_all(bind=engine)
    existing = {column["name"] for column in inspect(engine).get_columns("cases")}
    with engine.begin() as connection:
        for name, sql_type in CASE_COLUMN_SQL.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE cases ADD COLUMN {name} {sql_type}"))
        connection.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_cases_source_record_key "
            "ON cases (source_record_key)"
        ))


def build_case(row: dict[str, str]) -> Case:
    key = source_key(row)
    return Case(
        # The data source does not contain an FIR ID. This is an internal import key.
        case_number=f"SOURCE-{key[:24]}",
        title=missing(row["CrimeHead_Name"]) or missing(row["CrimeGroup_Name"]) or "Not Available",
        description=None,
        crime_type=missing(row["CrimeGroup_Name"]) or "Not Available",
        # Deliberately distinct from FIR_Stage; FIR_Stage is stored unchanged below.
        status=CaseStatus.IMPORTED,
        priority=CasePriority.MEDIUM,
        police_station=missing(row["UnitName"]),
        district=missing(row["District_Name"]),
        state=None,
        location=missing(row["Place of Offence"]),
        incident_date=incident_date(row),
        source_record_key=key,
        fir_year=integer(row["FIR_YEAR"]), fir_month=integer(row["FIR_MONTH"]), fir_day=integer(row["FIR_Day"]),
        fir_type=missing(row["FIR Type"]), fir_stage=missing(row["FIR_Stage"]),
        complaint_mode=missing(row["Complaint_Mode"]), crime_head=missing(row["CrimeHead_Name"]),
        latitude=coordinate(row["Latitude"], -90, 90), longitude=coordinate(row["Longitude"], -180, 180),
        offence_duration=missing(row["Offence_Duration"]), act_section=missing(row["ActSection"]),
        io_name=missing(row["IOName"]), kgid=missing(row["KGID"]), internal_io=missing(row["Internal_IO"]),
        distance_from_ps=missing(row["Distance from PS"]), beat_name=missing(row["Beat_Name"]),
        village_area_name=missing(row["Village_Area_Name"]), male=integer(row["Male"]),
        female=integer(row["Female"]), boy=integer(row["Boy"]), girl=integer(row["Girl"]),
        age_0=integer(row["Age 0"]), victim_count=integer(row["VICTIM COUNT"]),
        accused_count=integer(row["Accused Count"]), arrested_male=integer(row["Arrested Male"]),
        arrested_female=integer(row["Arrested Female"]), arrested_count=integer(row["Arrested Count\tNo."]),
        accused_chargesheeted_count=integer(row["Accused_ChargeSheeted Count"]),
        conviction_count=integer(row["Conviction Count"]), unit_id=missing(row["Unit_ID"]),
        source_payload=row,
    )


def import_firs(csv_path: Path) -> tuple[int, int]:
    if not csv_path.is_file():
        raise FileNotFoundError(f"FIR CSV not found: {csv_path}")
    ensure_case_columns()
    with csv_path.open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    if len(rows) != 500:
        raise ValueError(f"Expected exactly 500 FIR rows; found {len(rows)}")

    db = SessionLocal()
    imported = skipped = 0
    try:
        for row in rows:
            key = source_key(row)
            if db.query(Case.id).filter(Case.source_record_key == key).first():
                skipped += 1
                continue
            db.add(build_case(row))
            imported += 1
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return imported, skipped


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Path to FIR_Details_500.csv")
    args = parser.parse_args()
    added, existing = import_firs(args.csv)
    print(f"FIR import complete: added={added}, already_present={existing}, expected=500")
