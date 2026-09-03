"""Parse the private team-roster PDF into {team_label: {"grade", "members"}}.

The roster PDF (a Google-Docs-rendered table, one column per team) contains
children's full names and must never be committed -- see the design doc under
docs/superpowers/specs/. This module's job stops at producing team rosters
for scripts/team_match.py to match against; it never writes the PDF's content
anywhere but memory.

Split into two layers on purpose:

- extract_words(): a thin subprocess wrapper around `pdftotext -bbox`. Not
  unit tested -- there is no PDF-authoring tool in this environment to build
  a synthetic fixture PDF, and this layer has nothing but I/O in it. Verified
  manually against the real file each season.
- group_into_teams(): a pure function over the word list extract_words()
  produces. Fully unit tested against synthetic word lists shaped the same
  way, so the actual column/header/name-splitting logic is covered even
  though the PDF-reading step is not.
"""

import re
import subprocess
import xml.etree.ElementTree as ET

COLOR_TOKENS = {"gold", "red", "white", "blue", "black", "green"}

# Header rows and name rows never share a line, so a generous vertical
# tolerance for "same line" is safe and forgiving of sub-pixel PDF jitter.
LINE_TOLERANCE = 3.0


def extract_words(pdf_path):
    """Run `pdftotext -bbox` and return a flat list of word dicts."""
    output = subprocess.run(
        ["pdftotext", "-bbox", pdf_path, "-"],
        check=True, capture_output=True, text=True,
    ).stdout
    # stdlib ET is fine here: this XML is our own subprocess's output from a
    # local file the user downloaded themselves, not untrusted network input.
    root = ET.fromstring(output)
    ns = {"h": "http://www.w3.org/1999/xhtml"}
    words = root.findall(".//h:word", ns) or root.findall(".//word")
    return [
        {
            "text": (w.text or "").strip(),
            "xMin": float(w.get("xMin")),
            "xMax": float(w.get("xMax")),
            "yMin": float(w.get("yMin")),
            "yMax": float(w.get("yMax")),
        }
        for w in words
        if (w.text or "").strip()
    ]


def _same_line(a, b, tolerance=LINE_TOLERANCE):
    return abs(a["yMin"] - b["yMin"]) <= tolerance


# Every column in this table shares the same row y-positions (row 1 of every
# team lands at the identical yMin, etc.), so a line cannot be found by y
# alone -- that would merge one whole table row (every column at once) into a
# single "line". A word belongs to the same line as its neighbour only when
# it is also close in x; a same-row word from the next column over is tens of
# points away, an order of magnitude past a real within-name gap (~3-4pt).
X_GAP = 15.0


def _cluster_by_line(words, x_gap=X_GAP):
    """Group words into visual text lines, breaking on either a y jump or an
    x gap -- so entries that share a row's y-position but sit in different
    table columns land in separate lines."""
    ordered = sorted(words, key=lambda w: (w["yMin"], w["xMin"]))
    lines = []
    current = []
    for word in ordered:
        if current and _same_line(current[-1], word) and (word["xMin"] - current[-1]["xMax"]) <= x_gap:
            current.append(word)
        else:
            if current:
                lines.append(current)
            current = [word]
    if current:
        lines.append(current)
    return lines


def _find_headers(words):
    """Return header dicts: {label, grade, xMin, xMax, yMin, yMax}.

    A header is a line made of exactly a digit token followed by a colour
    token (e.g. "3" "Gold"). Any other line -- name rows, the title, the
    decorative "Go South!" cell -- never matches this shape.
    """
    headers = []
    for line in _cluster_by_line(words):
        if len(line) != 2:
            continue
        digit_word, colour_word = line
        if not re.fullmatch(r"\d+", digit_word["text"]):
            continue
        if colour_word["text"].lower() not in COLOR_TOKENS:
            continue
        headers.append({
            "label": "%s %s" % (digit_word["text"], colour_word["text"]),
            "grade": int(digit_word["text"]),
            "xMin": digit_word["xMin"],
            "xMax": colour_word["xMax"],
            "yMin": digit_word["yMin"],
            "yMax": digit_word["yMax"],
        })
    return sorted(headers, key=lambda h: (h["yMin"], h["xMin"]))


def _header_rows(headers):
    """Cluster headers into rows (there may be more than one row of teams)."""
    rows = []
    for header in headers:
        placed = False
        for row in rows:
            if _same_line(row[0], header):
                row.append(header)
                placed = True
                break
        if not placed:
            rows.append([header])
    for row in rows:
        row.sort(key=lambda h: h["xMin"])
    return sorted(rows, key=lambda row: row[0]["yMin"])


def _page_column_slots(headers, tolerance=25.0):
    """Cluster every header's x-centre, across all rows, into a shared page-wide
    grid of column slots, sorted left to right.

    A later row of teams need not fill every slot the grid has room for (this
    roster's second row has 4 team headers against a 5-column grid the first
    row established) -- pooling slots across rows, rather than deriving them
    fresh per row, is what lets an unfilled slot stay unfilled instead of
    silently absorbing whatever decorative content sits in it (this roster's
    "Go South!" cell falls exactly in such a slot).
    """
    centres = sorted((h["xMin"] + h["xMax"]) / 2.0 for h in headers)
    slots = []
    for centre in centres:
        if slots and centre - slots[-1][-1] <= tolerance:
            slots[-1].append(centre)
        else:
            slots.append([centre])
    return [sum(group) / len(group) for group in slots]


def _slot_bounds(slots):
    """Voronoi-style x-boundaries between adjacent page-wide column slots."""
    bounds = []
    for i in range(len(slots)):
        left = -float("inf") if i == 0 else (slots[i - 1] + slots[i]) / 2.0
        right = float("inf") if i == len(slots) - 1 else (slots[i] + slots[i + 1]) / 2.0
        bounds.append((left, right))
    return bounds


def _nearest_slot(x_centre, slots):
    return min(range(len(slots)), key=lambda i: abs(slots[i] - x_centre))


def group_into_teams(words):
    """{"3 Gold": {"grade": 3, "members": [(first, last), ...]}, ...}."""
    headers = _find_headers(words)
    if not headers:
        raise ValueError("no team headers found -- roster PDF layout may have changed")
    rows = _header_rows(headers)
    header_texts = {(h["xMin"], h["yMin"]) for h in headers}

    slots = _page_column_slots(headers)
    bounds = _slot_bounds(slots)

    teams = {h["label"]: {"grade": h["grade"], "members": []} for h in headers}

    for row_index, row in enumerate(rows):
        y_top = row[0]["yMax"]
        y_bottom = rows[row_index + 1][0]["yMin"] if row_index + 1 < len(rows) else float("inf")

        # Only the slots this row's own headers occupy get a team; any other
        # slot in the grid is unfilled for this row and words landing in it
        # are dropped rather than mis-assigned to a neighbour.
        row_slot_labels = {}
        for header in row:
            centre = (header["xMin"] + header["xMax"]) / 2.0
            row_slot_labels[_nearest_slot(centre, slots)] = header["label"]

        section_words = [
            w for w in words
            if y_top < w["yMin"] < y_bottom and (w["xMin"], w["yMin"]) not in header_texts
        ]
        for line in _cluster_by_line(section_words):
            line_centre = (line[0]["xMin"] + line[-1]["xMax"]) / 2.0
            slot_index = next(
                (i for i, (left, right) in enumerate(bounds) if left <= line_centre < right),
                None)
            label = row_slot_labels.get(slot_index)
            if label is None:
                continue  # e.g. the decorative "Go South!" cell -- no header owns its slot
            full_name = " ".join(w["text"] for w in line)
            if " " not in full_name:
                continue
            first, _, last = full_name.rpartition(" ")
            teams[label]["members"].append((first, last))

    return teams


def load_roster(pdf_path):
    return group_into_teams(extract_words(pdf_path))
