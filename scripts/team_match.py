"""Cross-reference a registration export against a team roster.

This module is the one place in the pipeline allowed to hold an athlete's
name in memory. It reads First Name / Last Name / Grade -- columns the
sibling project's parse.py would drop as PII -- purely to decide which team
each registrant belongs to. The contract: match_export()'s return value
contains counts only. No name, DOB, or contact field may be added to it.
"""

import csv
import io
import re

GRADE_RE = re.compile(r"\d+")


def _strip_bom(text):
    if text.startswith("﻿"):
        return text[1:]
    if text.startswith("\\uFEFF"):
        return text[len("\\uFEFF"):]
    return text


def read_registrants(csv_path):
    """[{'first', 'last', 'grade'}, ...] -- PII, never returned by this module."""
    with io.open(csv_path, "r", encoding="utf-8") as handle:
        raw = handle.read()
    reader = csv.reader(io.StringIO(_strip_bom(raw)))
    rows = list(reader)
    if not rows:
        return []
    header = [_strip_bom(name).strip().lower() for name in rows[0]]
    try:
        first_i = header.index("first name")
        last_i = header.index("last name")
        grade_i = header.index("grade")
    except ValueError as error:
        raise ValueError("export is missing an expected column: %s" % error)

    registrants = []
    for row in rows[1:]:
        if not any(cell.strip() for cell in row):
            continue
        registrants.append({
            "first": row[first_i].strip() if first_i < len(row) else "",
            "last": row[last_i].strip() if last_i < len(row) else "",
            "grade": row[grade_i].strip() if grade_i < len(row) else "",
        })
    return registrants


def normalize_grade(text):
    """"3rd" / "3rd Grade" / "3" -> 3. None if no digits found."""
    match = GRADE_RE.search(text or "")
    return int(match.group()) if match else None


def match_registrant(first, last, grade, roster):
    """Team label, or None if zero or more than one distinct team matches."""
    matches = set()
    for label, team in roster.items():
        if team["grade"] != grade:
            continue
        for m_first, m_last in team["members"]:
            if (m_last.strip().lower() == (last or "").strip().lower()
                    and m_first.strip()[:1].lower() == (first or "").strip()[:1].lower()
                    and m_first.strip() and first.strip()):
                matches.add(label)
    return matches.pop() if len(matches) == 1 else None


def match_export(csv_path, roster):
    """{'total', 'teams': {label: {'grade','registered','size'}}, 'unmatched'}.

    Counts only -- see module docstring.
    """
    registrants = read_registrants(csv_path)
    teams = {
        label: {"grade": team["grade"], "registered": 0, "size": len(team["members"])}
        for label, team in roster.items()
    }
    unmatched = 0
    for person in registrants:
        grade = normalize_grade(person["grade"])
        label = match_registrant(person["first"], person["last"], grade, roster) if grade is not None else None
        if label is None:
            unmatched += 1
        else:
            teams[label]["registered"] += 1

    return {
        "total": len(registrants),
        "teams": teams,
        "unmatched": unmatched,
    }
