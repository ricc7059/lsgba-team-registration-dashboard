import re
import unittest

from scripts import piiscan, render

RESULT = {
    "total": 5,
    "unmatched": 1,
    "teams": {
        "3 Gold": {"grade": 3, "registered": 2, "size": 8},
        "4 Gold": {"grade": 4, "registered": 2, "size": 9},
        "4 Red": {"grade": 4, "registered": 1, "size": 4},
    },
}


def render_default(result=RESULT, stamp="Sep 3, 2026 6:00 PM"):
    return render.render_page(result, stamp)


def panel(html, slug):
    """The markup of one tab panel, from its id to the start of the next."""
    start = html.index('id="panel-%s"' % slug)
    following = html.find('<section class="tab-panel', start)
    end = following if following != -1 else html.index("</main>")
    return html[start:end]


class ShellStructureTests(unittest.TestCase):
    """The left rail + tab-panel shell, copied structurally from the sibling
    dashboard -- these assertions exist so a future edit can't silently drop
    the rail/tab mechanics back to the old single-page layout."""

    def test_has_the_rail_and_main_shell(self):
        html = render_default()
        self.assertIn('class="shell"', html)
        self.assertIn('class="rail"', html)
        self.assertIn('class="main"', html)

    def test_one_tab_button_per_grade_plus_overview(self):
        html = render_default()
        # RESULT has grades 3 and 4 -> Overview, Grade 3, Grade 4 = 3 tabs.
        self.assertEqual(html.count('class="tab-button'), 3)
        self.assertIn('data-slug="overview"', html)
        self.assertIn('data-slug="grade-3"', html)
        self.assertIn('data-slug="grade-4"', html)

    def test_one_tab_panel_per_tab_button_with_matching_ids(self):
        html = render_default()
        self.assertEqual(html.count('class="tab-panel'), 3)
        self.assertIn('id="panel-overview"', html)
        self.assertIn('id="panel-grade-3"', html)
        self.assertIn('id="panel-grade-4"', html)

    def test_overview_is_the_only_active_tab_by_default(self):
        html = render_default()
        self.assertEqual(html.count('class="tab-button is-active"'), 1)
        self.assertEqual(html.count('class="tab-panel is-active"'), 1)
        overview_button = re.search(r'<button class="tab-button[^>]*data-slug="overview"', html)
        self.assertIn("is-active", overview_button.group())

    def test_tab_switching_script_is_present(self):
        html = render_default()
        self.assertIn("tab-button", html)
        self.assertIn("addEventListener", html)
        self.assertIn("classList.add('is-active')", html)

    def test_mobile_breakpoint_is_present(self):
        self.assertIn("@media (max-width:860px)", render_default())


class ScoreboardTests(unittest.TestCase):
    def test_overview_shows_overall_total_and_roster_total(self):
        html = render_default()
        self.assertIn('<p class="board-value">5 / 21', html)  # 8 + 9 + 4 = 21

    def test_overview_shows_percent(self):
        html = render_default()
        self.assertIn("24%", html)  # round(100 * 5 / 21)


class GradeAggregationTests(unittest.TestCase):
    def test_grade_tab_count_sums_all_teams_in_that_grade(self):
        html = render_default()
        # Grade 4 has "4 Gold" (2/9) and "4 Red" (1/4) -> 3/13 combined.
        grade4_button = re.search(r'<button class="tab-button[^"]*" data-slug="grade-4".*?</button>',
                                  html, re.S)
        self.assertIn("3 / 13", grade4_button.group())

    def test_each_teams_own_bar_shows_its_own_count(self):
        html = render_default()
        self.assertIn("2 / 8", html)   # 3 Gold
        self.assertIn("2 / 9", html)   # 4 Gold
        self.assertIn("1 / 4", html)   # 4 Red

    def test_overview_has_one_tile_per_grade_in_a_grid(self):
        overview = panel(render_default(), "overview")
        self.assertEqual(overview.count('class="card-grid"'), 1)
        # RESULT has grades 3 and 4 -> two tiles.
        self.assertEqual(overview.count('<section class="card">'), 2)

    def test_each_tile_headlines_its_own_grade_tally(self):
        overview = panel(render_default(), "overview")
        self.assertIn('<h3>Grade 3 <span class="sub">2 / 8</span></h3>', overview)
        self.assertIn('<h3>Grade 4 <span class="sub">3 / 13</span></h3>', overview)

    def test_each_tile_charts_only_its_own_grades_teams(self):
        overview = panel(render_default(), "overview")
        grade3_tile = overview[overview.index("Grade 3"):overview.index("Grade 4")]
        self.assertEqual(grade3_tile.count('class="vcol"'), 1)
        self.assertNotIn("4 Red", grade3_tile)

    def test_every_team_is_charted_exactly_once_on_overview(self):
        overview = panel(render_default(), "overview")
        self.assertEqual(overview.count('class="vcol"'), 3)

    def test_grade_panel_has_only_its_own_teams(self):
        grade4 = panel(render_default(), "grade-4")
        self.assertEqual(grade4.count('class="vcol"'), 2)
        self.assertNotIn("3 Gold", grade4)


class UnmatchedNoteTests(unittest.TestCase):
    def test_includes_unmatched_note_when_nonzero(self):
        html = render_default()
        self.assertIn("1 registration(s) could not be matched", html)

    def test_omits_unmatched_note_when_zero(self):
        clean = dict(RESULT, unmatched=0)
        html = render_default(clean)
        self.assertNotIn("could not be matched", html)


class SafetyTests(unittest.TestCase):
    def test_output_passes_the_pii_scan(self):
        piiscan.assert_clean(render_default())

    def test_escapes_team_labels(self):
        hostile = {"total": 1, "unmatched": 0, "teams": {
            "<script>3 Gold": {"grade": 3, "registered": 1, "size": 1}}}
        html = render_default(hostile)
        self.assertNotIn("<script>3", html)

    def test_never_uses_green_or_red_fill_colors(self):
        # The sibling dashboard reserves green/red for one specific up/down
        # chart; this page has no such concept and must stay gold-only.
        html = render_default()
        self.assertNotIn("#46AD69", html)
        self.assertNotIn("#CB4D57", html)


if __name__ == "__main__":
    unittest.main()
