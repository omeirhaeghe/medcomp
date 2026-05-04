"""Build matches.json from raw TSVs in data/raw/.

Each TSV must have header: specialty, institution, city, state.
Filename convention: <school_id>_<year>.tsv (e.g., cwru_2026.tsv).
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.geo import metro_for, region_for

SCHOOL_NAMES = {
    "cwru": "Case Western Reserve University SOM",
    "columbia": "Columbia Vagelos College of Physicians and Surgeons",
}


def specialty_category(specialty: str) -> str:
    """Normalize specialty into a top-level category for grouping."""
    s = specialty.strip()
    s_low = s.lower()
    # Map slash-variants and prefixed forms to base category
    if s_low.startswith("internal medicine-pediatrics") or s_low.startswith("internal medicine/pediatrics") or s_low.startswith("medicine - pediatrics"):
        return "Internal Medicine-Pediatrics"
    if s_low.startswith("internal medicine"):
        return "Internal Medicine"
    if s_low.startswith("medicine - emergency"):
        return "Emergency Medicine"
    if s_low.startswith("emergency medicine"):
        return "Emergency Medicine"
    if s_low.startswith("vascular surgery"):
        return "Vascular Surgery"
    if s_low.startswith("plastic surgery"):
        return "Plastic Surgery"
    if s_low.startswith("neurological surgery"):
        return "Neurological Surgery"
    if s_low.startswith("surgery - general") or s_low.startswith("surgery-general") or s_low.startswith("general surgery") or s_low == "surgery" or s_low.startswith("surgery (prelim)") or s_low.startswith("surgery/"):
        return "General Surgery"
    if s_low.startswith("surgery - thoracic") or s_low.startswith("thoracic surgery"):
        return "Thoracic Surgery"
    if s_low.startswith("radiology - diagnostic") or s_low.startswith("radiology-diagnostic") or s_low == "radiology":
        return "Radiology-Diagnostic"
    if s_low.startswith("radiology - interventional") or s_low.startswith("radiology-interventional") or s_low.startswith("interventional radiology"):
        return "Interventional Radiology"
    if s_low.startswith("orthopedic") or s_low.startswith("orthopaedic"):
        return "Orthopaedic Surgery"
    if s_low.startswith("oral"):
        return "Oral Maxillofacial Surgery"
    if s_low.startswith("dermatology"):
        return "Dermatology"
    if s_low.startswith("anesthesiology"):
        return "Anesthesiology"
    if s_low.startswith("psychiatry"):
        return "Psychiatry"
    if s_low.startswith("neurology (child)") or s_low.startswith("child neurology"):
        return "Child Neurology"
    if s_low.startswith("neurology"):
        return "Neurology"
    if s_low.startswith("pediatrics-medical genetics"):
        return "Pediatrics"
    if s_low.startswith("pediatrics"):
        return "Pediatrics"
    if s_low.startswith("pathology"):
        return "Pathology"
    if s_low.startswith("obstetrics") or s_low.startswith("ob/gyn"):
        return "Obstetrics-Gynecology"
    if s_low.startswith("ophthalmology"):
        return "Ophthalmology"
    if s_low.startswith("otolaryngology"):
        return "Otolaryngology"
    if s_low.startswith("urology"):
        return "Urology"
    if s_low.startswith("family medicine"):
        return "Family Medicine"
    if s_low.startswith("physical medicine"):
        return "Physical Medicine & Rehabilitation"
    return s


def load_tsv(path: Path) -> list[dict]:
    rows = []
    with path.open() as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            specialty = r["specialty"].strip()
            city = r["city"].strip()
            state = r["state"].strip().upper()
            rows.append({
                "specialty": specialty,
                "specialty_category": specialty_category(specialty),
                "institution": r["institution"].strip(),
                "city": city,
                "state": state,
                "metro": metro_for(city, state),
                "region": region_for(state),
            })
    return rows


def main() -> None:
    raw_dir = ROOT / "data" / "raw"
    out_path = ROOT / "data" / "matches.json"

    schools = []
    for tsv in sorted(raw_dir.glob("*.tsv")):
        school_id, year = tsv.stem.rsplit("_", 1)
        rows = load_tsv(tsv)
        schools.append({
            "id": tsv.stem,
            "school_id": school_id,
            "school_name": SCHOOL_NAMES.get(school_id, school_id.upper()),
            "year": int(year),
            "class_size": len(rows),
            "matches": rows,
        })
        print(f"  {tsv.stem}: {len(rows)} placements")

    out_path.write_text(json.dumps({"schools": schools}, indent=2))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
