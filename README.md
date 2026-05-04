# MedComp

Compare medical school residency match lists by **metro area, US Census region, state, and specialty**.

Answers questions like *"What share of each school's class matched in the Chicago metro?"* or *"How does Columbia's specialty mix compare to Case Western's?"*

Ships with three datasets:

| School | Year | Placements |
|---|---|---|
| Case Western Reserve University SOM | 2026 | 227 |
| Case Western Reserve University SOM | 2025 | 202 |
| Columbia Vagelos College of Physicians and Surgeons | 2024 | 135 |

## Stack

- **FastAPI** — JSON API + static HTML
- **Vanilla JS** — single-page UI, no build step
- **Static JSON** — match data is built once from TSVs at deploy time

## Local development

```bash
pip install -r requirements.txt
python scripts/build.py
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000.

## Adding a new school

1. Drop a TSV in `data/raw/` named `<school_id>_<year>.tsv` (e.g. `harvard_2026.tsv`)
2. Header row must be: `specialty\tinstitution\tcity\tstate`
3. If the school's full name isn't already known, add it to `SCHOOL_NAMES` in `scripts/build.py`
4. Run `python scripts/build.py`
5. Commit and push — Render rebuilds automatically

## Geography

City → metro and state → region mappings live in `app/geo.py`. Metros cover the major US training hubs (NYC, Boston, Chicago, Bay Area, LA, Cleveland, etc.). Cities not in the lookup table fall back to the city name itself; states not in the lookup return `Unknown`.

## API

| Endpoint | Description |
|---|---|
| `GET /api/schools` | List available schools and class sizes |
| `GET /api/facets` | Distinct metros, regions, states, specialties for filter dropdowns |
| `GET /api/compare?schools=cwru_2026,columbia_2024&metro=Chicago` | Count + percentage per school matching the filter |
| `GET /api/breakdown?school=cwru_2026&by=region` | Full distribution for one school grouped by `metro`, `region`, `state`, `specialty_category`, or `institution` |

## Deploy to Render

1. Fork or clone this repo to your GitHub account
2. In Render, create a new **Blueprint** pointing at the repo
3. Render reads `render.yaml`, runs `pip install -r requirements.txt && python scripts/build.py`, then `uvicorn app.main:app`
4. Free tier sleeps after 15 min idle (~30–60s cold start)

## Data sources

- CWRU 2025 / 2026 — match lists published by the Case Western Reserve School of Medicine
- Columbia 2024 — published on the [Vagelos Office of Student Affairs match page](https://www.vagelos.columbia.edu/education/student-resources/office-student-affairs/match-day)

All data is de-identified — institution-level placements only, no student names.

## Caveats

- Columbia's class size shown here (135 placements) reflects the row count on their public match page. Some schools list couples-match or dual-degree placements as separate rows, which can inflate the count above the actual class size.
- Specialty names are normalized to top-level categories for grouping (e.g. "Internal Medicine/Primary Care" → "Internal Medicine"). Original specialty strings are preserved on each row.
