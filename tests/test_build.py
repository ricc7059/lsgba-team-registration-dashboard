import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

from scripts import build, state

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

ROSTER = {
    "3 Gold": {"grade": 3, "members": [("Ada", "Fake"), ("Bea", "Fake")]},
    "4 Gold": {"grade": 4, "members": [("Cy", "Fake")]},
}


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.work, True)
        self.downloads = os.path.join(self.work, "Downloads")
        os.makedirs(self.downloads)
        self.export_name = "lsgba-team-registration-2026-09-03-1800.csv"
        shutil.copy(os.path.join(FIXTURES, "team_registration_sample.csv"),
                    os.path.join(self.downloads, self.export_name))
        # find_roster_pdf just needs a matching filename; its content is never
        # read because load_roster is mocked in every test below.
        open(os.path.join(self.downloads, "2026-2027 LSGBA Travel Roster.pdf"), "w").close()

        self.state_path = os.path.join(self.work, "state.json")
        data = state.load(self.state_path)
        state.record_export(data, build.REG_ID, "2026-2027 LSGBA Travel Roster Acceptance and Registration",
                            3, self.export_name)
        state.save(self.state_path, data)

        self.out_path = os.path.join(self.work, "index.html")

    def run_build(self, state_path=None):
        argv = sys.argv
        sys.argv = ["build.py", "--downloads", self.downloads,
                    "--state", state_path or self.state_path, "--out", self.out_path]
        try:
            with contextlib.redirect_stdout(io.StringIO()) as out, \
                    contextlib.redirect_stderr(io.StringIO()) as err:
                code = build.main()
            return code, out.getvalue(), err.getvalue()
        finally:
            sys.argv = argv

    @mock.patch("scripts.build.roster_mod.load_roster", return_value=ROSTER)
    def test_writes_a_page_with_the_expected_counts(self, _mock_roster):
        code, out, _err = self.run_build()
        self.assertEqual(code, 0)
        with open(self.out_path) as handle:
            html = handle.read()
        self.assertIn("3 / 3", html)  # 3 CSV rows total, roster holds 3 spots
        self.assertIn("2 / 2", html)  # 3 Gold: both Ada and Bea registered

    @mock.patch("scripts.build.roster_mod.load_roster", return_value=ROSTER)
    def test_reports_unmatched_count(self, _mock_roster):
        self.run_build()
        with open(self.out_path) as handle:
            html = handle.read()
        self.assertIn("1 registration(s) could not be matched", html)

    def test_missing_export_exits_nonzero(self):
        os.remove(os.path.join(self.downloads, self.export_name))
        code, _out, err = self.run_build()
        self.assertEqual(code, 1)
        self.assertIn("missing export", err)

    def test_no_recorded_export_exits_nonzero(self):
        empty_state = os.path.join(self.work, "empty.json")
        state.save(empty_state, state.load(empty_state))
        code, _out, err = self.run_build(state_path=empty_state)
        self.assertEqual(code, 1)
        self.assertIn("no recorded export", err)

    @mock.patch("scripts.build.roster_mod.load_roster", return_value=ROSTER)
    def test_count_mismatch_is_warned_but_not_fatal(self, _mock_roster):
        data = state.load(self.state_path)
        data["registrations"][build.REG_ID]["lastCount"] = 999
        state.save(self.state_path, data)
        code, _out, err = self.run_build()
        self.assertEqual(code, 0)
        self.assertIn("WARNING", err)

    def test_no_roster_pdf_in_downloads_exits_nonzero(self):
        os.remove(os.path.join(self.downloads, "2026-2027 LSGBA Travel Roster.pdf"))
        with self.assertRaises(FileNotFoundError):
            self.run_build()


if __name__ == "__main__":
    unittest.main()
