"""Build non-geolocated browser review data. Standard library; no upload."""
from pathlib import Path
import json
import re
import sys

from qa import read_json, validate

ROOT = Path(__file__).resolve().parents[1]
INPUTS = {
    "places": "data/places.json", "sources": "evidence/sources.json",
    "cases": "data/evaluations.json", "materials": "data/materials.json",
    "issues": "quality/issues.json",
}
PRIVATE_PATH = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]|file://|/Users/|/home/|\\\\")


def build():
    data = {key: read_json(ROOT / name) for key, name in INPUTS.items()}
    report = validate(data["places"], data["sources"],
                      read_json(ROOT / "evidence/claims.json"), data["issues"])
    if report["errors"]:
        raise ValueError("Source data failed qa.py; run it for details")
    source_ids = {row["source_id"] for row in data["sources"]}
    for group in ("cases", "materials"):
        rows = data[group]
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"{group}: expected a nonempty object array")
        ids = [row.get("id") for row in rows if isinstance(row, dict)]
        if len(ids) != len(rows) or not all(isinstance(x, str) and x for x in ids):
            raise ValueError(f"{group}: every record needs a nonempty id")
        if len(set(ids)) != len(ids):
            raise ValueError(f"{group}: duplicate id")
        for row in rows:
            refs = row.get("source_ids", [])
            if not isinstance(refs, list) or not all(isinstance(x, str) and x in source_ids for x in refs):
                raise ValueError(f"{group}: unknown source_ids")
            if group == "cases" and not refs:
                raise ValueError("cases: every case needs a source reference")
    if any(row.get("longitude") is not None or row.get("latitude") is not None for row in data["places"]):
        raise ValueError("This review version has no released geometry; review coordinates before changing the build policy")
    data["release"] = {"status": "pending_review", "geojson_features": 0}
    output = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if PRIVATE_PATH.search(output):
        raise ValueError("A private filesystem path was found; remove it from public review data")
    target = ROOT / "site/review-data.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(output, encoding="utf-8")
    print(f"Built site/review-data.json: {len(data['places'])} place record(s), "
          f"{len(data['cases'])} case draft(s), {len(data['materials'])} material record(s); no coordinates released")


if __name__ == "__main__":
    try:
        build()
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"Build failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
