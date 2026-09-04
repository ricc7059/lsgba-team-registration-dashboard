"""Render the team-registration breakdown as one static HTML page.

Palette and design tokens are copied directly from the sibling
lsgba-registrations-dashboard project's scripts/render.py (same badge-sampled
colors, same "gold is the only quantity/fill color" rule -- that project
reserves green/red exclusively for one specific up/down chart, the
grade-cohort flow diagram, and explicitly treats gold as the neutral
"quantity" color everywhere else; there is no equivalent "up/down" concept
on this page, so gold is used throughout instead). This is a single page,
not a tabbed dashboard -- there is exactly one thing to show: current
registered-vs-rostered counts, by team.
"""

MAROON = "#8B1D41"
MAROON_DEEP = "#5E1230"
GOLD = "#D2B77C"
GOLD_DIM = "#8A7647"
# Sibling project's CREAM (#E8D8B8) as rgba(232, 216, 184, ...) -- used inline
# below for translucent labels/track fills rather than as a solid color.
GROUND = "#16171A"
SURFACE = "#1F2126"
EDGE = "#31363E"
TEXT = "#ECEDEF"
TEXT_DIM = "#8E959F"


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
  header h1 { margin: 0; font-size: 1.4rem; font-weight: 600; color: %(text)s; }
  .headline-label {
    margin-top: 18px; font-size: 0.72rem; text-transform: uppercase;
    letter-spacing: 0.19em; color: rgba(232, 216, 184, 0.75);
  }
  .headline {
    font-size: 2.6rem; font-weight: 700; margin: 4px 0 0; color: %(gold)s;
    font-variant-numeric: tabular-nums;
  }
  .headline .pct { font-size: 1.1rem; color: rgba(232, 216, 184, 0.75); margin-left: 8px; }
  main { max-width: 900px; margin: 0 auto; padding: 24px; }
  .grade-block { margin-bottom: 28px; }
  .grade-block h2 {
    font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.19em;
    color: %(text_dim)s; border-bottom: 1px solid %(edge)s; padding-bottom: 6px;
  }
  .team { background: %(surface)s; border: 1px solid %(edge)s; border-radius: 16px;
          padding: 14px 16px; margin-top: 10px; }
  .team-row { display: flex; justify-content: space-between; margin-bottom: 8px; }
  .team-label { font-weight: 600; color: %(text)s; }
  .team-count { color: %(gold)s; font-weight: 600; font-variant-numeric: tabular-nums; }
  .bar { height: 8px; border-radius: 4px; background: rgba(232, 216, 184, 0.07); overflow: hidden; }
  .bar-fill { height: 100%%; background: linear-gradient(90deg, %(gold_dim)s, %(gold)s); }
  .unmatched { margin-top: 8px; padding: 14px 16px; border-radius: 16px;
               background: %(surface)s; border: 1px solid %(edge)s; color: %(text_dim)s; }
  footer { text-align: center; color: %(text_dim)s; font-size: 0.85rem; padding: 24px; }
</style>
</head>
<body>
<header>
  <img src="assets/lsgba-badge-solid.png" alt="LSGBA">
  <h1>2026-2027 Travel Roster Registration</h1>
  <div class="headline-label">Registered / Rostered</div>
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
        "gold": GOLD, "gold_dim": GOLD_DIM, "text": TEXT, "text_dim": TEXT_DIM,
        "surface": SURFACE, "edge": EDGE,
        "total": total, "roster_total": roster_total, "pct": pct,
        "grade_sections": grade_sections, "unmatched": unmatched_html,
        "updated": escape(updated_stamp),
    }
