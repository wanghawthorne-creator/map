"""Synthetic mutations for code validation only; no new real POIs or accuracy claims."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("qa", ROOT / "scripts/qa.py")
qa = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qa)


class StructuralChecks(unittest.TestCase):
    def setUp(self):
        self.places = qa.read_json(ROOT / "data/places.json")
        self.sources = qa.read_json(ROOT / "evidence/sources.json")
        self.claims = qa.read_json(ROOT / "evidence/claims.json")
        self.issues = qa.read_json(ROOT / "quality/issues.json")

    def result(self):
        return qa.validate(self.places, self.sources, self.claims, self.issues)

    def test_unknown_values_are_accepted_but_not_mappable(self):
        result = self.result()
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["map_eligible_ids"], [])
        self.assertTrue(result["limitations"])

    def test_duplicate_id_rejected(self):
        self.places.append(deepcopy(self.places[0]))
        self.assertTrue(any("duplicate ID" in x for x in self.result()["errors"]))

    def test_broken_source_reference_rejected(self):
        self.places[0]["source_ids"] = ["SIM-MISSING-SOURCE"]
        self.assertTrue(any("unknown source_ids" in x for x in self.result()["errors"]))

    def test_invalid_calendar_date_rejected(self):
        self.places[0]["source_checked_on"] = "2026-02-30"
        self.assertTrue(any("invalid source_checked_on" in x for x in self.result()["errors"]))

    def test_partial_coordinates_rejected(self):
        self.places[0]["longitude"] = 0  # synthetic schema probe, not a place coordinate
        self.assertTrue(any("pair" in x for x in self.result()["errors"]))

    def test_nonfinite_and_boolean_coordinates_rejected(self):
        for value in (float("nan"), float("inf"), True):
            with self.subTest(value=value):
                self.places[0]["longitude"] = value
                self.places[0]["latitude"] = value
                self.assertTrue(any("invalid coordinates" in x for x in self.result()["errors"]))

    def test_unknown_crs_and_coordinate_provenance_rejected(self):
        self.places[0]["longitude"] = self.places[0]["latitude"] = 0
        errors = self.result()["errors"]
        self.assertTrue(any("known CRS" in x for x in errors))
        self.assertTrue(any("coordinate evidence" in x for x in errors))

    def test_approval_cannot_bypass_location_and_privacy(self):
        self.places[0]["map_release_status"] = "approved"
        self.assertTrue(any("map approval" in x for x in self.result()["errors"]))

    def test_synthetic_issue_cannot_enter_real_log(self):
        self.issues[0]["kind"] = "synthetic_demo"
        self.assertTrue(any("synthetic" in x for x in self.result()["errors"]))

    def test_similar_names_are_flagged_without_merge(self):
        other = deepcopy(self.places[0])
        other["place_id"] = "SIM-SECOND-ROW"
        other["display_name"] = " 老太沟书苑 "
        self.places.append(other)
        original = deepcopy(self.places)
        result = self.result()
        self.assertTrue(any("possible name duplicate" in x for x in result["limitations"]))
        self.assertEqual(self.places, original)

    def test_non_json_constants_rejected_when_loading(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "synthetic.json"
            path.write_text("[NaN]", encoding="utf-8")
            with self.assertRaises(ValueError):
                qa.read_json(path)


if __name__ == "__main__":
    unittest.main()
