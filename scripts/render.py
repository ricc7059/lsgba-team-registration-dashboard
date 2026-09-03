"""Render the team-registration breakdown as one static HTML page.

Palette matches the sibling lsgba-registrations-dashboard project (sampled
from the association's badge) for visual continuity, but this is a single
page, not a tabbed dashboard -- there is exactly one thing to show: current
registered-vs-rostered counts, by team.
"""

MAROON = "#8B1D41"
MAROON_DEEP = "#5E1230"
GOLD = "#D2B77C"
GROUND = "#16171A"
SURFACE = "#1F2126"
SURFACE_2 = "#262A30"
EDGE = "#31363E"
TEXT = "#ECEDEF"
TEXT_DIM = "#8E959F"
GOOD = "#46AD69"


def escape(text):
    return (str(text)
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def _team_card(label, team):
    registered, size = team["registered"], team["size"]
    pct = 0 if size == 0 else min(100, round(100 * registered / size))
    return """
      <div class="team">
        <div class="team-row">
          <span class="team-label">%s</span>
          <span class="team-count">%d / %d</span>
        </div>
        <div class="bar"><div class="bar-fill" style="width:%d%%"></div></div>
      </div>""" % (escape(label), registered, size, pct)


def _grade_section(grade, teams_in_grade):
    cards = "".join(_team_card(label, team) for label, team in teams_in_grade)
    return """
    <section class="grade-block">
      <h2>Grade %s</h2>
      %s
    </section>""" % (escape(grade), cards)


def render_page(result, updated_stamp):
    teams = result["teams"]
    total = result["total"]
    roster_total = sum(t["size"] for t in teams.values())
    unmatched = result["unmatched"]
    pct = 0 if roster_total == 0 else round(100 * total / roster_total)

    by_grade = {}
    for label, team in teams.items():
        by_grade.setdefault(team["grade"], []).append((label, team))
    grade_sections = "".join(
        _grade_section(grade, sorted(by_grade[grade]))
        for grade in sorted(by_grade)
    )

    unmatched_html = ""
    if unmatched:
        unmatched_html = """
    <div class="unmatched">%d registration(s) could not be matched to a rostered team and are not counted above. Check the export against the roster.</div>""" % unmatched

    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LSGBA Team Registration</title>
<link rel="icon" href="assets/favicon.png">
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0; background: %(ground)s; color: %(text)s;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }
  header {
    padding: 32px 24px; text-align: center;
    background: linear-gradient(135deg, %(maroon)s, %(maroon_deep)s);
  }
  header img { height: 64px; margin-bottom: 12px; }
  header h1 { margin: 0; font-size: 1.4rem; font-weight: 600; }
  .headline { font-size: 3rem; font-weight: 700; margin: 12px 0 4px; }
  .headline .pct { font-size: 1.2rem; color: %(gold)s; margin-left: 8px; }
  main { max-width: 900px; margin: 0 auto; padding: 24px; }
  .grade-block { margin-bottom: 28px; }
  .grade-block h2 {
    font-size: 1rem; text-transform: uppercase; letter-spacing: 0.06em;
    color: %(text_dim)s; border-bottom: 1px solid %(edge)s; padding-bottom: 6px;
  }
  .team { background: %(surface)s; border: 1px solid %(edge)s; border-radius: 10px;
          padding: 14px 16px; margin-top: 10px; }
  .team-row { display: flex; justify-content: space-between; margin-bottom: 8px; }
  .team-label { font-weight: 600; }
  .team-count { color: %(text_dim)s; font-variant-numeric: tabular-nums; }
  .bar { height: 8px; border-radius: 4px; background: %(surface_2)s; overflow: hidden; }
  .bar-fill { height: 100%%; background: %(good)s; }
  .unmatched { margin-top: 8px; padding: 14px 16px; border-radius: 10px;
               background: %(surface)s; border: 1px solid %(edge)s; color: %(text_dim)s; }
  footer { text-align: center; color: %(text_dim)s; font-size: 0.85rem; padding: 24px; }
</style>
</head>
<body>
<header>
  <img src="assets/lsgba-badge-solid.png" alt="LSGBA">
  <h1>2026-2027 Travel Roster Registration</h1>
  <div class="headline">%(total)d / %(roster_total)d<span class="pct">%(pct)d%%</span></div>
</header>
<main>
%(grade_sections)s
%(unmatched)s
</main>
<footer>Updated %(updated)s</footer>
</body>
</html>
""" % {
        "ground": GROUND, "maroon": MAROON, "maroon_deep": MAROON_DEEP,
        "gold": GOLD, "text": TEXT, "text_dim": TEXT_DIM, "surface": SURFACE,
        "surface_2": SURFACE_2, "edge": EDGE, "good": GOOD,
        "total": total, "roster_total": roster_total, "pct": pct,
        "grade_sections": grade_sections, "unmatched": unmatched_html,
        "updated": escape(updated_stamp),
    }
