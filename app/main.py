"""MedComp — med school match list comparison API."""
import json
from collections import Counter
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "data" / "matches.json").read_text())
SCHOOLS_BY_ID = {s["id"]: s for s in DATA["schools"]}

SMS_PATH = ROOT / "data" / "sms.json"
SMS = json.loads(SMS_PATH.read_text()) if SMS_PATH.exists() else None

app = FastAPI(title="MedComp", description="Medical school match list comparison")
app.mount("/static", StaticFiles(directory=ROOT / "app" / "static"), name="static")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (ROOT / "app" / "templates" / "index.html").read_text()


@app.get("/api/schools")
def list_schools() -> dict:
    return {
        "schools": [
            {
                "id": s["id"],
                "school_id": s["school_id"],
                "school_name": s["school_name"],
                "year": s["year"],
                "class_size": s["class_size"],
            }
            for s in DATA["schools"]
        ]
    }


@app.get("/api/facets")
def facets() -> dict:
    """Return distinct values across all schools for filter dropdowns."""
    metros, regions, states, specialties = set(), set(), set(), set()
    for s in DATA["schools"]:
        for m in s["matches"]:
            metros.add(m["metro"])
            regions.add(m["region"])
            states.add(m["state"])
            specialties.add(m["specialty_category"])
    return {
        "metros": sorted(metros),
        "regions": sorted(regions),
        "states": sorted(states),
        "specialties": sorted(specialties),
    }


def _filter_matches(matches: list[dict], filters: dict) -> list[dict]:
    out = matches
    for field, value in filters.items():
        if value:
            out = [m for m in out if m.get(field) == value]
    return out


@app.get("/api/compare")
def compare(
    schools: str = Query(..., description="Comma-separated school IDs (e.g., cwru_2026,columbia_2024)"),
    metro: str | None = None,
    region: str | None = None,
    state: str | None = None,
    specialty: str | None = None,
) -> dict:
    """Compare schools by counting matches that satisfy the filters."""
    school_ids = [s.strip() for s in schools.split(",") if s.strip()]
    filters = {"metro": metro, "region": region, "state": state, "specialty_category": specialty}

    results = []
    for sid in school_ids:
        school = SCHOOLS_BY_ID.get(sid)
        if not school:
            raise HTTPException(404, f"Unknown school: {sid}")
        filtered = _filter_matches(school["matches"], filters)
        count = len(filtered)
        total = school["class_size"]
        results.append({
            "school_id": sid,
            "school_name": school["school_name"],
            "year": school["year"],
            "class_size": total,
            "matched_count": count,
            "matched_pct": round(count / total * 100, 1) if total else 0,
            "matches": filtered,
        })

    return {"filters": {k: v for k, v in filters.items() if v}, "results": results}


@app.get("/api/sms/summary")
def sms_summary() -> dict:
    if not SMS:
        raise HTTPException(404, "SMS data not loaded")
    return {"years": SMS["years"], "summary": SMS["summary"]}


@app.get("/api/sms/specialties")
def sms_specialties() -> dict:
    """List all NRMP SMS specialties with program counts and aggregate fill rates."""
    if not SMS:
        raise HTTPException(404, "SMS data not loaded")
    rows = []
    for spec, programs in SMS["by_specialty"].items():
        # Aggregate quota and filled across all programs and years
        total_quota = total_filled = 0
        for p in programs:
            for yr in SMS["years"]:
                cell = p["by_year"][str(yr)]
                if cell["quota"] is not None:
                    total_quota += cell["quota"]
                if cell["filled"] is not None:
                    total_filled += cell["filled"]
        rows.append({
            "specialty": spec,
            "program_count": len(programs),
            "total_quota_5yr": total_quota,
            "total_filled_5yr": total_filled,
            "fill_rate_5yr": round(total_filled / total_quota * 100, 1) if total_quota else 0,
        })
    rows.sort(key=lambda r: -r["program_count"])
    return {"specialties": rows}


@app.get("/api/sms/programs")
def sms_programs(specialty: str) -> dict:
    """List all programs for a specialty with 5-year quota/filled and per-year totals."""
    if not SMS:
        raise HTTPException(404, "SMS data not loaded")
    programs = SMS["by_specialty"].get(specialty)
    if programs is None:
        raise HTTPException(404, f"Unknown specialty: {specialty}")

    # Per-year aggregate totals across all programs in this specialty
    totals = {str(yr): {"quota": 0, "filled": 0} for yr in SMS["years"]}
    for p in programs:
        for yr in SMS["years"]:
            cell = p["by_year"][str(yr)]
            if cell["quota"] is not None:
                totals[str(yr)]["quota"] += cell["quota"]
            if cell["filled"] is not None:
                totals[str(yr)]["filled"] += cell["filled"]

    return {
        "specialty": specialty,
        "years": SMS["years"],
        "totals_by_year": totals,
        "programs": programs,
    }


@app.get("/api/breakdown")
def breakdown(
    school: str,
    by: str = Query("metro", regex="^(metro|region|state|specialty_category|institution)$"),
) -> dict:
    """Count placements grouped by a field for a single school."""
    s = SCHOOLS_BY_ID.get(school)
    if not s:
        raise HTTPException(404, f"Unknown school: {school}")
    counts = Counter(m[by] for m in s["matches"])
    total = s["class_size"]
    rows = [
        {"value": k, "count": v, "pct": round(v / total * 100, 1)}
        for k, v in counts.most_common()
    ]
    return {
        "school_id": school,
        "school_name": s["school_name"],
        "year": s["year"],
        "class_size": total,
        "group_by": by,
        "rows": rows,
    }
