import os
import tempfile
import unittest

from scripts import team_match

ROSTER = {
    "3 Gold": {"grade": 3, "members": [("Ada", "Fake"), ("Bea", "Fake")]},
    "4 Gold": {"grade": 4, "members": [("Cy", "Fake")]},
    "4 Red": {"grade": 4, "members": [("Cy", "Faketon")]},
}


def write_csv(rows, header="First Name,Last Name,Date of Birth,Grade,Email,Order Status"):
    path = tempfile.mktemp(suffix=".csv")
    with open(path, "w") as handle:
        handle.write(header + "\n")
        for row in rows:
            handle.write(row + "\n")
    return path


class NormalizeGradeTests(unittest.TestCase):
    def test_extracts_leading_digits(self):
        self.assertEqual(team_match.normalize_grade("3rd"), 3)
        self.assertEqual(team_match.normalize_grade("8th Grade"), 8)

    def test_no_digits_returns_none(self):
        self.assertIsNone(team_match.normalize_grade("Kindergarten"))
        self.assertIsNone(team_match.normalize_grade(""))


class MatchRegistrantTests(unittest.TestCase):
    def test_matches_on_last_name_and_first_initial(self):
        self.assertEqual(team_match.match_registrant("Ada", "Fake", 3, ROSTER), "3 Gold")

    def test_is_case_insensitive(self):
        self.assertEqual(team_match.match_registrant("ADA", "FAKE", 3, ROSTER), "3 Gold")

    def test_wrong_grade_falls_back_to_full_name_match(self):
        # The exact bug seen live: a registrant's stated grade disagrees with
        # the roster's, but their full name is an unambiguous exact match.
        self.assertEqual(team_match.match_registrant("Ada", "Fake", 4, ROSTER), "3 Gold")

    def test_full_name_fallback_is_case_insensitive(self):
        self.assertEqual(team_match.match_registrant("ADA", "FAKE", 4, ROSTER), "3 Gold")

    def test_no_last_name_match_is_unmatched(self):
        self.assertIsNone(team_match.match_registrant("Zed", "Nobody", 3, ROSTER))

    def test_wrong_grade_with_no_full_name_match_anywhere_is_unmatched(self):
        self.assertIsNone(team_match.match_registrant("Zed", "Nobody", 4, ROSTER))

    def test_grade_none_still_falls_back_to_full_name_match(self):
        self.assertEqual(team_match.match_registrant("Ada", "Fake", None, ROSTER), "3 Gold")

    def test_same_last_name_and_initial_on_two_teams_disambiguates_by_full_name(self):
        # Grade-scoped rule alone can't tell "Cy Fake" from "Cole Fake" apart
        # (same last name, same first initial) -- the full-name fallback
        # resolves it because the two full names actually differ.
        roster = {
            "4 Gold": {"grade": 4, "members": [("Cy", "Fake")]},
            "4 Red": {"grade": 4, "members": [("Cole", "Fake")]},
        }
        self.assertEqual(team_match.match_registrant("Cy", "Fake", 4, roster), "4 Gold")

    def test_identical_full_name_on_two_teams_is_still_ambiguous(self):
        # A genuine data problem (e.g. two same-named kids on different
        # teams) has no rule left to disambiguate it -- neither wins.
        roster = {
            "4 Gold": {"grade": 4, "members": [("Cy", "Fake")]},
            "4 Red": {"grade": 4, "members": [("Cy", "Fake")]},
        }
        self.assertIsNone(team_match.match_registrant("Cy", "Fake", 4, roster))


class ReadRegistrantsTests(unittest.TestCase):
    def test_reads_first_last_and_grade_only(self):
        path = write_csv(['Ada,Fake,01/02/2015,3rd,ada@example.com,Paid'])
        self.addCleanup(os.remove, path)
        rows = team_match.read_registrants(path)
        self.assertEqual(rows, [{"first": "Ada", "last": "Fake", "grade": "3rd"}])

    def test_handles_bom(self):
        path = write_csv(
            ['Ada,Fake,01/02/2015,3rd,ada@example.com,Paid'],
            header='\\uFEFFFirst Name,Last Name,Date of Birth,Grade,Email,Order Status')
        self.addCleanup(os.remove, path)
        rows = team_match.read_registrants(path)
        self.assertEqual(rows[0]["first"], "Ada")

    def test_missing_column_raises(self):
        path = write_csv(["Ada,Fake"], header="First Name,Last Name")
        self.addCleanup(os.remove, path)
        with self.assertRaises(ValueError):
            team_match.read_registrants(path)

    def test_skips_blank_rows(self):
        path = write_csv(['Ada,Fake,01/02/2015,3rd,ada@example.com,Paid', ',,,,,'])
        self.addCleanup(os.remove, path)
        self.assertEqual(len(team_match.read_registrants(path)), 1)


class MatchExportTests(unittest.TestCase):
    def test_counts_registered_per_team(self):
        path = write_csv([
            'Ada,Fake,01/02/2015,3rd,a@example.com,Paid',
            'Bea,Fake,02/03/2016,3rd,b@example.com,Paid',
            'Cy,Fake,03/04/2016,4th,c@example.com,Paid',
        ])
        self.addCleanup(os.remove, path)
        result = team_match.match_export(path, ROSTER)
        self.assertEqual(result["total"], 3)
        self.assertEqual(result["teams"]["3 Gold"]["registered"], 2)
        self.assertEqual(result["teams"]["3 Gold"]["size"], 2)
        self.assertEqual(result["unmatched"], 0)

    def test_unresolvable_registrant_is_unmatched_and_not_named(self):
        path = write_csv(['Zed,Nobody,01/02/2015,3rd,z@example.com,Paid'])
        self.addCleanup(os.remove, path)
        result = team_match.match_export(path, ROSTER)
        self.assertEqual(result["unmatched"], 1)
        self.assertEqual(result["total"], 1)
        self.assertNotIn("Zed", str(result))
        self.assertNotIn("Nobody", str(result))

    def test_last_name_disambiguates_between_two_teams_at_the_same_grade(self):
        path = write_csv(['Cy,Fake,03/04/2016,4th,c@example.com,Paid'])
        self.addCleanup(os.remove, path)
        result = team_match.match_export(path, {
            "4 Gold": {"grade": 4, "members": [("Cy", "Fake")]},
            "4 Red": {"grade": 4, "members": [("Cole", "Faketon")]},
        })
        self.assertEqual(result["teams"]["4 Gold"]["registered"], 1)
        self.assertEqual(result["teams"]["4 Red"]["registered"], 0)

    def test_return_value_carries_no_pii(self):
        path = write_csv(['Ada,Fake,01/02/2015,3rd,a@example.com,Paid'])
        self.addCleanup(os.remove, path)
        result = team_match.match_export(path, ROSTER)
        self.assertNotIn("first", str(result.keys()))
        for key in result:
            self.assertIn(key, {"total", "teams", "unmatched"})


if __name__ == "__main__":
    unittest.main()
