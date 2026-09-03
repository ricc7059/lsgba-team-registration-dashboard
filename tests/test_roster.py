import unittest

from scripts import roster


def word(text, xmin, ymin, width=30.0, height=13.0):
    return {"text": text, "xMin": xmin, "xMax": xmin + width,
            "yMin": ymin, "yMax": ymin + height}


def header_words(number, colour, xmin, ymin=114.0):
    return [word(number, xmin, ymin, width=8.0), word(colour, xmin + 12, ymin, width=35.0)]


def name_words(first, last, xmin, ymin):
    first_word = word(first, xmin, ymin, width=len(first) * 6)
    last_word = word(last, first_word["xMax"] + 4, ymin, width=len(last) * 6)
    return [first_word, last_word]


class SingleRowTests(unittest.TestCase):
    def setUp(self):
        # Two columns, matching this roster's real column spacing (~150pt apart).
        self.words = []
        self.words += header_words("3", "Gold", xmin=80.0)
        self.words += header_words("4", "Gold", xmin=230.0)
        self.words += name_words("Ada", "Fake", xmin=70.0, ymin=150.0)
        self.words += name_words("Bea", "Fake", xmin=70.0, ymin=170.0)
        self.words += name_words("Cy", "Fake", xmin=220.0, ymin=150.0)

    def test_finds_both_teams(self):
        teams = roster.group_into_teams(self.words)
        self.assertEqual(set(teams), {"3 Gold", "4 Gold"})

    def test_assigns_grade_from_leading_digit(self):
        teams = roster.group_into_teams(self.words)
        self.assertEqual(teams["3 Gold"]["grade"], 3)
        self.assertEqual(teams["4 Gold"]["grade"], 4)

    def test_members_land_in_the_correct_column(self):
        teams = roster.group_into_teams(self.words)
        self.assertEqual(teams["3 Gold"]["members"], [("Ada", "Fake"), ("Bea", "Fake")])
        self.assertEqual(teams["4 Gold"]["members"], [("Cy", "Fake")])

    def test_no_headers_raises(self):
        with self.assertRaises(ValueError):
            roster.group_into_teams([word("Ada", 70.0, 150.0)])


class SameRowYPositionTests(unittest.TestCase):
    """The real roster's row-1 entries for every team share one exact yMin --
    a line must split on x-gap, not just y, or every column's row-1 collapses
    into a single false 'line'."""

    def test_shared_row_y_does_not_merge_columns(self):
        words = []
        words += header_words("3", "Gold", xmin=80.0)
        words += header_words("4", "Gold", xmin=230.0)
        words += header_words("5", "Red", xmin=380.0)
        same_y = 150.0
        words += name_words("Ada", "Fake", xmin=70.0, ymin=same_y)
        words += name_words("Bea", "Fake", xmin=220.0, ymin=same_y)
        words += name_words("Cy", "Fake", xmin=370.0, ymin=same_y)

        teams = roster.group_into_teams(words)
        self.assertEqual(teams["3 Gold"]["members"], [("Ada", "Fake")])
        self.assertEqual(teams["4 Gold"]["members"], [("Bea", "Fake")])
        self.assertEqual(teams["5 Red"]["members"], [("Cy", "Fake")])


class UnfilledSlotTests(unittest.TestCase):
    """A later row of headers may not fill every column slot an earlier row
    established -- content sitting in that gap (like the real roster's
    decorative 'Go South!' cell) must be dropped, not swept into a neighbour."""

    def test_content_in_an_unheadered_slot_is_dropped(self):
        words = []
        # Row 1 establishes 3 slots.
        words += header_words("3", "Gold", xmin=80.0)
        words += header_words("4", "Gold", xmin=230.0)
        words += header_words("5", "Gold", xmin=380.0)
        words += name_words("Ada", "Fake", xmin=70.0, ymin=150.0)
        words += name_words("Bea", "Fake", xmin=220.0, ymin=150.0)
        words += name_words("Cy", "Fake", xmin=370.0, ymin=150.0)
        # Row 2 only fills the first 2 of those 3 slots.
        words += header_words("6", "Gold", xmin=80.0, ymin=300.0)
        words += header_words("6", "Red", xmin=230.0, ymin=300.0)
        words += name_words("Dee", "Fake", xmin=70.0, ymin=340.0)
        # Decorative two-word content sitting in the 3rd (unheadered, in row
        # 2) slot -- same shape as a name, to actually exercise slot-drop
        # rather than being incidentally filtered out for some other reason.
        words += name_words("Go", "Home", xmin=370.0, ymin=340.0)

        teams = roster.group_into_teams(words)
        self.assertEqual(set(teams), {"3 Gold", "4 Gold", "5 Gold", "6 Gold", "6 Red"})
        self.assertEqual(teams["6 Gold"]["members"], [("Dee", "Fake")])
        self.assertEqual(teams["6 Red"]["members"], [])


class HyphenatedAndMultiWordNameTests(unittest.TestCase):
    def test_splits_on_the_last_space(self):
        words = header_words("4", "Gold", xmin=80.0)
        words += name_words("Ari", "Gutierrez-Camacho", xmin=70.0, ymin=150.0)
        first_word = word("Mary", 70.0, 170.0, width=30)
        jane_word = word("Jane", 104.0, 170.0, width=30)
        smith_word = word("Smith", 138.0, 170.0, width=35)
        words += [first_word, jane_word, smith_word]

        teams = roster.group_into_teams(words)
        members = teams["4 Gold"]["members"]
        self.assertIn(("Ari", "Gutierrez-Camacho"), members)
        self.assertIn(("Mary Jane", "Smith"), members)


if __name__ == "__main__":
    unittest.main()
