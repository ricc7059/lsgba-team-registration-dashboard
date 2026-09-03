import unittest

from scripts import piiscan, render

RESULT = {
    "total": 5,
    "unmatched": 1,
    "teams": {
        "3 Gold": {"grade": 3, "registered": 2, "size": 8},
        "4 Gold": {"grade": 4, "registered": 3, "size": 9},
    },
}


class RenderPageTests(unittest.TestCase):
    def test_includes_overall_total_and_roster_total(self):
        html = render.render_page(RESULT, "Sep 3, 2026 6:00 PM")
        self.assertIn("5 / 17", html)

    def test_includes_each_teams_running_count(self):
        html = render.render_page(RESULT, "Sep 3, 2026 6:00 PM")
        self.assertIn("2 / 8", html)
        self.assertIn("3 / 9", html)

    def test_includes_unmatched_note_when_nonzero(self):
        html = render.render_page(RESULT, "Sep 3, 2026 6:00 PM")
        self.assertIn("1 registration(s) could not be matched", html)

    def test_omits_unmatched_note_when_zero(self):
        clean = dict(RESULT, unmatched=0)
        html = render.render_page(clean, "Sep 3, 2026 6:00 PM")
        self.assertNotIn("could not be matched", html)

    def test_groups_teams_by_grade_heading(self):
        html = render.render_page(RESULT, "Sep 3, 2026 6:00 PM")
        self.assertIn("Grade 3", html)
        self.assertIn("Grade 4", html)

    def test_output_passes_the_pii_scan(self):
        piiscan.assert_clean(render.render_page(RESULT, "Sep 3, 2026 6:00 PM"))

    def test_escapes_team_labels(self):
        hostile = {"total": 1, "unmatched": 0, "teams": {
            "<script>3 Gold": {"grade": 3, "registered": 1, "size": 1}}}
        html = render.render_page(hostile, "Sep 3, 2026 6:00 PM")
        self.assertNotIn("<script>3", html)


if __name__ == "__main__":
    unittest.main()
