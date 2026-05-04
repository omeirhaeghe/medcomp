"""Parse the NRMP Specialties Matching Service (SMS) program results PDF text.

Input:  data/raw/sms_program_results.txt (pdftotext -layout output)
Output: data/sms.json

For each program:
- institution name + city + state
- program name + NRMP code
- 5 years (2022-2026) of (quota, filled)
- normalized specialty (program name with year/track suffixes stripped)
"""
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CODE_RE = re.compile(r"\d{4}[A-Z0-9]{3}[FS]\d")
DATA_RE = re.compile(r"^\s*(\S.*?)\s+(\d{4}[A-Z0-9]{3}[FS]\d)\s+(.+?)\s*$")
NUM_RE = re.compile(r"(\d+|--)")
PROGRAM_HEADER_RE = re.compile(r"\bProgram\b.*\b2026\b")
CODE_HEADER_RE = re.compile(r"^(.*?)\s{2,}Code\s+Quota\s+Filled")

STATE_NAME_TO_ABBR = {
    "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR",
    "CALIFORNIA": "CA", "COLORADO": "CO", "CONNECTICUT": "CT", "DELAWARE": "DE",
    "DISTRICT OF COLUMBIA": "DC", "FLORIDA": "FL", "GEORGIA": "GA", "HAWAII": "HI",
    "IDAHO": "ID", "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA", "KANSAS": "KS",
    "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME", "MARYLAND": "MD",
    "MASSACHUSETTS": "MA", "MICHIGAN": "MI", "MINNESOTA": "MN", "MISSISSIPPI": "MS",
    "MISSOURI": "MO", "MONTANA": "MT", "NEBRASKA": "NE", "NEVADA": "NV",
    "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ", "NEW MEXICO": "NM", "NEW YORK": "NY",
    "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND", "OHIO": "OH", "OKLAHOMA": "OK",
    "OREGON": "OR", "PENNSYLVANIA": "PA", "PUERTO RICO": "PR", "RHODE ISLAND": "RI",
    "SOUTH CAROLINA": "SC", "SOUTH DAKOTA": "SD", "TENNESSEE": "TN", "TEXAS": "TX",
    "UTAH": "UT", "VERMONT": "VT", "VIRGINIA": "VA", "WASHINGTON": "WA",
    "WEST VIRGINIA": "WV", "WISCONSIN": "WI", "WYOMING": "WY",
}

YEARS = [2026, 2025, 2024, 2023, 2022]

# Suffixes/qualifiers stripped to normalize program name → specialty.
SUFFIX_RE = re.compile(
    r"\s*[/\-]\s*(\d+\s*y(rs?|ear)?s?|track|ccm\s*track|clinical|research|"
    r"investigator\s+research|clinical\s+investigator(\s+research)?|"
    r"physician\s+scientist|pstp|moffitt\s*cancer\s*ctr|moffitt|tampa|baptist\s*miami|"
    r"academic|community|rural|primary\s*care|hospitalist)\b.*",
    re.IGNORECASE,
)


def parse_numbers(s: str) -> list:
    return [int(n) if n != "--" else None for n in NUM_RE.findall(s)]


def normalize_specialty(name: str) -> str:
    n = name.strip()
    n = SUFFIX_RE.sub("", n).strip()
    n = re.sub(r"\s+", " ", n).strip(" -/")
    return n


def parse(text: str) -> dict:
    lines = text.split("\n")
    state = None
    institution = None
    city = None
    last_program = None
    pending_inst = None  # candidate institution name
    institutions = []
    current_programs = []

    def flush_inst():
        nonlocal institution, city, current_programs
        if institution and current_programs:
            institutions.append({
                "name": institution,
                "city": city,
                "state": state,
                "programs": current_programs,
            })
        institution = None
        city = None
        current_programs = []

    for ln in lines:
        if not ln.strip():
            continue
        stripped = ln.strip()
        # Skip footers / running headers
        if stripped.startswith("Page ") and " of " in stripped:
            continue
        if "Reproduction prohibited" in stripped:
            continue
        if "Program Results: Specialties Matching" in stripped:
            continue
        if stripped == "U.S. Programs":
            continue
        # State header (multi-word like "NEW YORK" allowed)
        if stripped.upper() == stripped and stripped in STATE_NAME_TO_ABBR:
            flush_inst()
            state = STATE_NAME_TO_ABBR[stripped]
            pending_inst = None
            last_program = None
            continue
        # Skip the "Program ... 2026 ..." header line
        if PROGRAM_HEADER_RE.search(ln):
            # Confirm pending institution
            if pending_inst:
                flush_inst()
                institution = pending_inst
                pending_inst = None
            last_program = None
            continue
        # "City   Code  Quota  Filled" sub-header — extract city
        m = CODE_HEADER_RE.match(ln)
        if m:
            cand_city = m.group(1).strip()
            if cand_city and cand_city != "Code":
                city = cand_city
            last_program = None
            continue
        # Data row?
        m = DATA_RE.match(ln)
        if m:
            program_name = re.sub(r"\s+", " ", m.group(1).strip())
            code = m.group(2)
            nums = parse_numbers(m.group(3))
            if len(nums) >= 10:
                by_year = {
                    str(YEARS[i]): {"quota": nums[i * 2], "filled": nums[i * 2 + 1]}
                    for i in range(5)
                }
                program = {
                    "name": program_name,
                    "code": code,
                    "specialty_code": code[4:7],
                    "specialty": normalize_specialty(program_name),
                    "by_year": by_year,
                }
                current_programs.append(program)
                last_program = program
            continue
        # Continuation line for last program (no code, no numbers, indented)
        if last_program and ln.startswith(" ") and not CODE_RE.search(ln) and not re.search(r"\b(20\d{2})\b", ln):
            extra = stripped
            last_program["name"] = (last_program["name"] + " " + extra).strip()
            last_program["specialty"] = normalize_specialty(last_program["name"])
            continue
        # Otherwise: candidate institution name (non-indented, no other matches)
        if not ln.startswith(" "):
            pending_inst = stripped
            last_program = None
    # Final flush
    flush_inst()
    return {"institutions": institutions, "years": YEARS}


def build_specialty_index(data: dict) -> dict:
    """Group programs by NRMP specialty code (chars 5-7), then pick most-common name as label."""
    code_to_programs = defaultdict(list)
    code_to_name_counts = defaultdict(lambda: defaultdict(int))

    for inst in data["institutions"]:
        for p in inst["programs"]:
            spec_code = p["specialty_code"]
            normalized = p["specialty"]
            code_to_name_counts[spec_code][normalized] += 1
            code_to_programs[spec_code].append({
                "institution": inst["name"],
                "city": inst["city"],
                "state": inst["state"],
                "program_name": p["name"],
                "code": p["code"],
                "by_year": p["by_year"],
            })

    # Pick the most common normalized name per code
    code_to_label = {}
    for spec_code, name_counts in code_to_name_counts.items():
        label = max(name_counts.items(), key=lambda kv: (kv[1], -len(kv[0])))[0]
        code_to_label[spec_code] = label

    # Build final dict: label -> rows
    spec_to_programs = defaultdict(list)
    for spec_code, rows in code_to_programs.items():
        label = code_to_label[spec_code]
        spec_to_programs[label].extend(rows)

    # Sort each by state then institution
    for k in spec_to_programs:
        spec_to_programs[k].sort(key=lambda r: (r["state"] or "", r["institution"]))
    return dict(sorted(spec_to_programs.items()))


def main() -> None:
    text = (ROOT / "data" / "raw" / "sms_program_results.txt").read_text()
    parsed = parse(text)
    by_specialty = build_specialty_index(parsed)

    # Stats
    n_inst = len(parsed["institutions"])
    n_prog = sum(len(i["programs"]) for i in parsed["institutions"])
    n_spec = len(by_specialty)
    print(f"Parsed {n_inst} institutions, {n_prog} programs, {n_spec} normalized specialties")

    # Final output: just by_specialty (the only query pattern) + summary metadata.
    data = {
        "years": parsed["years"],
        "summary": {
            "institutions": n_inst,
            "programs": n_prog,
            "specialties": n_spec,
        },
        "by_specialty": by_specialty,
    }
    # Top 10 specialties by program count
    top = sorted(
        ((spec, len(rows)) for spec, rows in data["by_specialty"].items()),
        key=lambda x: -x[1],
    )[:10]
    for spec, n in top:
        print(f"  {spec}: {n} programs")

    out = ROOT / "data" / "sms.json"
    out.write_text(json.dumps(data, indent=2))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
