"""Offline structural checks. No geocoding, uploads or factual verification."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime
import json
import math
from pathlib import Path
import re
import sys
import unicodedata
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ROOT = Path(__file__).resolve().parents[1]
ENUMS = {
    "record_kind": {"source_reported_real_place"},
    "name_status": {"source_reported"},
    "category_provisional": {"community_reading_and_cultural_space", "unknown"},
    "crs": {None, "WGS84", "GCJ-02", "BD-09"},
    "current_operation_status": {"unable_to_verify", "reported_active", "reported_closed"},
    "verification_status": {"historically_reported_location_unverified", "reviewed_with_evidence"},
    "location_status": {"missing_evidence", "source_recorded", "reviewed"},
    "spatial_precision": {"unknown", "approximate", "entrance"},
    "map_release_status": {"pending_review", "approved", "withheld"},
    "privacy_review_status": {"pending_review", "approved", "withheld"},
}
LISTS = ("aliases_verified", "coordinate_source_ids", "source_ids", "claim_ids")
DATES = ("source_published_on", "source_checked_on", "observed_on", "last_verified_on")
NULLABLE_TEXT = ("reported_address", "verified_address", "admin_village_verified")
REQUIRED = set(ENUMS) | set(LISTS) | set(DATES) | set(NULLABLE_TEXT) | {
    "place_id", "display_name", "longitude", "latitude", "notes"
}


def read_json(path):
    def reject_constant(value):
        raise ValueError(f"Non-JSON constant: {value}")
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), parse_constant=reject_constant)


def iso_day(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def string_list(value):
    return isinstance(value, list) and all(isinstance(x, str) and x.strip() for x in value)


def normal_name(value):
    return "".join(unicodedata.normalize("NFKC", value).casefold().split())


def map_eligible(row):
    """Eligibility is structural only; approval values require human evidence."""
    x, y = row.get("longitude"), row.get("latitude")
    return (
        finite_number(x) and finite_number(y) and -180 <= x <= 180 and -90 <= y <= 90
        and row.get("crs") == "WGS84"
        and bool(row.get("coordinate_source_ids"))
        and iso_day(row.get("last_verified_on"))
        and row.get("location_status") == "reviewed"
        and row.get("map_release_status") == "approved"
        and row.get("privacy_review_status") == "approved"
    )


def validate(places, sources, claims, issues):
    errors, limitations = [], []
    groups = {"places": places, "sources": sources, "claims": claims, "issues": issues}
    for label, values in groups.items():
        if not isinstance(values, list) or not all(isinstance(v, dict) for v in values):
            errors.append(f"{label}: expected an array of objects")
    if errors:
        return {"errors": errors, "limitations": limitations, "map_eligible_ids": []}

    keys = {"places": "place_id", "sources": "source_id", "claims": "claim_id", "issues": "issue_id"}
    for label, values in groups.items():
        field = keys[label]
        ids = [v.get(field) for v in values]
        if not all(isinstance(v, str) and v.strip() for v in ids):
            errors.append(f"{label}: missing or invalid {field}")
        good_ids = [v for v in ids if isinstance(v, str)]
        for value, count in Counter(good_ids).items():
            if count > 1:
                errors.append(f"{label}: duplicate ID {value}")

    source_ids = {s.get("source_id") for s in sources if isinstance(s.get("source_id"), str)}
    place_ids = {p.get("place_id") for p in places if isinstance(p.get("place_id"), str)}
    claim_map = {c.get("claim_id"): c for c in claims if isinstance(c.get("claim_id"), str)}

    def refs(record, field, allowed, label, nonempty=False):
        values = record.get(field)
        if not string_list(values) or (nonempty and not values):
            errors.append(f"{label}: invalid or empty {field}")
            return
        if len(values) != len(set(values)):
            errors.append(f"{label}: duplicate reference in {field}")
        for value in values:
            if value not in allowed:
                errors.append(f"{label}: unknown {field} reference {value}")

    for source in sources:
        label = str(source.get("source_id"))
        for field in ("published_on", "checked_on"):
            value = source.get(field)
            if (field == "checked_on" or value is not None) and not iso_day(value):
                errors.append(f"{label}: invalid {field}")
        a, b = source.get("published_on"), source.get("checked_on")
        if iso_day(a) and iso_day(b) and a > b:
            errors.append(f"{label}: publication after source check")
        for field in ("kind", "title", "access_status", "locator", "summary", "limitations", "reuse"):
            if not isinstance(source.get(field), str) or not source[field].strip():
                errors.append(f"{label}: missing {field}")
        if source.get("url") is not None and not (
            isinstance(source["url"], str) and source["url"].startswith("https://")
        ):
            errors.append(f"{label}: invalid URL")

    for claim in claims:
        label = str(claim.get("claim_id"))
        refs(claim, "source_ids", source_ids, label, True)
        if claim.get("place_id") not in place_ids:
            errors.append(f"{label}: unknown place_id")
        if not iso_day(claim.get("checked_on")):
            errors.append(f"{label}: invalid checked_on")
        for field in ("field", "judgment", "scope"):
            if not isinstance(claim.get(field), str) or not claim[field].strip():
                errors.append(f"{label}: missing {field}")

    names = {}
    for row in places:
        label = str(row.get("place_id"))
        missing = sorted(REQUIRED - row.keys())
        if missing:
            errors.append(f"{label}: missing fields {', '.join(missing)}")
        for field, choices in ENUMS.items():
            value = row.get(field)
            if not (value is None or isinstance(value, str)) or value not in choices:
                errors.append(f"{label}: invalid {field}")
        for field in NULLABLE_TEXT:
            value = row.get(field)
            if value is not None and not (isinstance(value, str) and value.strip()):
                errors.append(f"{label}: invalid {field}")
        for field in ("display_name", "notes"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"{label}: invalid {field}")
        name = row.get("display_name")
        if isinstance(name, str):
            key = normal_name(name)
            if key in names:
                limitations.append(f"{label}: possible name duplicate with {names[key]}; manual identity review, no merge")
            names[key] = label
        for field in LISTS:
            if not string_list(row.get(field)):
                errors.append(f"{label}: invalid {field}")
        refs(row, "source_ids", source_ids, label, True)
        refs(row, "coordinate_source_ids", source_ids, label)
        refs(row, "claim_ids", set(claim_map), label, True)
        for claim_id in row.get("claim_ids", []) if string_list(row.get("claim_ids")) else []:
            if claim_id in claim_map and claim_map[claim_id].get("place_id") != label:
                errors.append(f"{label}: claim {claim_id} belongs to another place")
        if row.get("aliases_verified"):
            limitations.append(f"{label}: alias evidence requires manual review; no automatic name equivalence")
        for field in DATES:
            value = row.get(field)
            if (field == "source_checked_on" or value is not None) and not iso_day(value):
                errors.append(f"{label}: invalid {field}")
            if field != "source_checked_on" and iso_day(value) and iso_day(row.get("source_checked_on")):
                if value > row["source_checked_on"]:
                    errors.append(f"{label}: {field} is after source_checked_on")
        x, y = row.get("longitude"), row.get("latitude")
        if (x is None) != (y is None):
            errors.append(f"{label}: coordinates must be a pair or both null")
        if x is not None or y is not None:
            if not (finite_number(x) and finite_number(y) and -180 <= x <= 180 and -90 <= y <= 90):
                errors.append(f"{label}: invalid coordinates")
            if row.get("crs") is None:
                errors.append(f"{label}: coordinates without known CRS")
            if not row.get("coordinate_source_ids"):
                errors.append(f"{label}: coordinates without coordinate evidence")
        else:
            limitations.append(f"{label}: coordinates unavailable; no point may be inferred")
        if row.get("current_operation_status") == "unable_to_verify":
            limitations.append(f"{label}: current operation unknown; historical reporting is not current verification")
        if row.get("map_release_status") == "approved" and not map_eligible(row):
            errors.append(f"{label}: map approval lacks reviewed WGS84 location, date, evidence or privacy approval")

    for issue in issues:
        label = str(issue.get("issue_id"))
        refs(issue, "place_ids", place_ids, label)
        refs(issue, "evidence_ids", source_ids, label, True)
        if issue.get("kind") not in {"real_evidence_gap", "real_material_limitation"}:
            errors.append(f"{label}: synthetic issues must not be mixed into real issues")
        if issue.get("status") not in {"open", "resolved", "withdrawn"}:
            errors.append(f"{label}: invalid status")
        if not iso_day(issue.get("opened_on")):
            errors.append(f"{label}: invalid opened_on")

    return {
        "scope": "Saved draft only; structural validity is not geographic accuracy or release permission.",
        "counts": {k: len(v) for k, v in groups.items()},
        "errors": errors,
        "limitations": limitations,
        "map_eligible_ids": [r.get("place_id") for r in places if map_eligible(r)] if not errors else [],
        "open_real_issues": [i.get("issue_id") for i in issues if i.get("status") == "open"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, help="Optional path for a JSON receipt; no upload")
    args = parser.parse_args()
    try:
        result = validate(
            read_json(ROOT / "data/places.json"), read_json(ROOT / "evidence/sources.json"),
            read_json(ROOT / "evidence/claims.json"), read_json(ROOT / "quality/issues.json"),
        )
    except (OSError, ValueError, TypeError) as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 1
    # Windows may not have the IANA timezone database; +08:00 is Shanghai's offset for this run.
    try:
        now = datetime.now(ZoneInfo("Asia/Shanghai"))
    except ZoneInfoNotFoundError:
        from datetime import timezone, timedelta
        now = datetime.now(timezone(timedelta(hours=8)))
    result["checked_at"] = now.isoformat(timespec="seconds")
    result["timezone"] = "Asia/Shanghai"
    result["publication_approved_by_program"] = False
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
