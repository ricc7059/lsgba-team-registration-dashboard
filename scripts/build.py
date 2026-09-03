"""Build index.html from state.json, the export it points at, and the roster PDF.

Usage:
  python3 scripts/build.py [--dry-run] [--downloads DIR] [--roster PATH]
"""

import argparse
import datetime
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import piiscan, render, roster as roster_mod, state, team_match  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DOWNLOADS = os.path.expanduser("~/Downloads")
REG_ID = "1132938"


def find_roster_pdf(downloads):
    """Most recently modified "*Travel Roster*.pdf" in downloads.

    Errors loudly on zero or multiple matches rather than guessing -- a wrong
    guess here would silently cross-reference against the wrong season.
    """
    matches = glob.glob(os.path.join(downloads, "*Travel Roster*.pdf"))
    if not matches:
        raise FileNotFoundError(
            "no '*Travel Roster*.pdf' found in %s -- pass --roster explicitly" % downloads)
    if len(matches) > 1:
        matches.sort(key=os.path.getmtime, reverse=True)
        print("WARNING: multiple roster PDFs found, using the most recent: %s"
              % matches[0], file=sys.stderr)
    return matches[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--downloads", default=DEFAULT_DOWNLOADS)
    parser.add_argument("--roster", default=None)
    parser.add_argument("--state", default=os.path.join(REPO, "state.json"))
    parser.add_argument("--out", default=os.path.join(REPO, "index.html"))
    args = parser.parse_args()

    data = state.load(args.state)
    entry = data.get("registrations", {}).get(REG_ID)
    if not entry or not entry.get("lastExport"):
        print("ERROR: no recorded export for %s in %s" % (REG_ID, args.state), file=sys.stderr)
        return 1

    export_path = os.path.join(args.downloads, entry["lastExport"])
    if not os.path.exists(export_path):
        print("ERROR: missing export %s" % export_path, file=sys.stderr)
        return 1

    roster_path = args.roster or find_roster_pdf(args.downloads)
    roster = roster_mod.load_roster(roster_path)

    result = team_match.match_export(export_path, roster)

    if result["total"] != entry.get("lastCount"):
        print("WARNING: %s has %d CSV rows but state says %s"
              % (REG_ID, result["total"], entry.get("lastCount")), file=sys.stderr)

    now = datetime.datetime.now()
    html = render.render_page(result, now.strftime("%b %-d, %Y %-I:%M %p"))

    piiscan.assert_clean(html)  # fail closed before anything touches disk

    with open(args.out, "w") as handle:
        handle.write(html)

    print("wrote %s -- %d/%d registered across %d teams, %d unmatched"
          % (args.out, result["total"], sum(t["size"] for t in result["teams"].values()),
             len(result["teams"]), result["unmatched"]))
    if args.dry_run:
        print("dry run: not committing or pushing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
