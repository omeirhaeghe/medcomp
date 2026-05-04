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
