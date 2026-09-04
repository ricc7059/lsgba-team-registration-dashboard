"""Render the team-registration breakdown with the sibling dashboard's shell:
a left rail of tabs and a vertical bar chart per tab's content, copied
structurally from lsgba-registrations-dashboard's scripts/render.py (the
`.shell`/`.rail`/`.tab-button` markup+CSS+JS, and the `_columns()` plain-HTML
bar chart) -- same CSS classes, same tab-switching script, same bar-chart
shape. The rail's tabs are grades instead of registrations (this project
tracks one registration, not several), and an "Overview" tab carries the
big scoreboard number the sibling puts on every tab.

Palette is the same badge-sampled set as the sibling project. Green/red are
never used here, matching that project's rule that they are reserved for its
one specific up/down chart (the grade-cohort flow diagram) -- gold is the
palette's neutral "quantity/fill" color everywhere else, including here.
"""

STYLE = """
:root{
  --maroon:#8B1D41; --maroon-deep:#5E1230;
  --gold:#D2B77C; --gold-dim:#8A7647;
  --ground:#16171A; --surface:#1F2126; --surface-2:#262A30; --edge:#31363E;
  --text:#ECEDEF; --dim:#8E959F;
  --mono: ui-monospace, SFMono-Regular, Menlo, monospace;
}
* { box-sizing: border-box; }
body{margin:0;background:var(--ground);color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}

.shell{display:flex;min-height:100vh;align-items:stretch}

/* ---- left rail (copied structurally from the sibling dashboard) ---- */
.rail{flex:0 0 268px;background:var(--surface);border-right:1px solid var(--edge);
  padding:26px 20px;display:flex;flex-direction:column;gap:26px}
.brand{display:flex;align-items:center;gap:13px}
.brand img{width:54px;height:54px;flex:0 0 54px}
.brand-org{margin:0;font-size:.95rem;font-weight:800;letter-spacing:.02em;
  line-height:1.15}
.brand-sub{margin:2px 0 0;font-size:.72rem;color:var(--dim);letter-spacing:.13em;
  text-transform:uppercase}
.rail-label{margin:0 0 10px;font-size:.66rem;letter-spacing:.19em;
  text-transform:uppercase;color:var(--dim);font-weight:700}
.tabs{display:flex;flex-direction:column;gap:6px}
.tab-button{display:flex;align-items:center;gap:10px;width:100%;text-align:left;
  background:transparent;border:1px solid transparent;border-radius:11px;
  padding:11px 13px;color:var(--dim);font-family:inherit;font-size:.83rem;
  font-weight:600;cursor:pointer;transition:background .15s,color .15s}
.tab-button:hover{background:var(--surface-2);color:var(--text)}
.tab-button:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
.tab-button.is-active{background:var(--maroon);border-color:rgba(210,183,124,.5);
  color:#fff}
.tab-name{flex:1;line-height:1.3}
.tab-count{font-size:.9rem;font-weight:700;color:var(--gold);
  font-variant-numeric:tabular-nums}
.rail-foot{margin-top:auto}
.stamp{margin:0;font-size:.78rem;color:var(--text)}
.unmatched-note{margin:8px 0 0;font-size:.72rem;color:var(--dim)}

/* ---- main / tab panels ---- */
.main{flex:1;min-width:0;padding:30px 34px 56px}
.tab-panel{display:none}
.tab-panel.is-active{display:block}
.main h1{margin:0 0 18px;font-size:1.3rem;font-weight:700}

/* ---- scoreboard cell (Overview tab) ---- */
.board-cell{background:linear-gradient(135deg,var(--maroon),var(--maroon-deep));
  border:1px solid rgba(210,183,124,.28);border-radius:16px;
  padding:22px 26px;margin-bottom:16px}
.board-label{margin:0;font-size:.7rem;letter-spacing:.19em;text-transform:uppercase;
  color:rgba(232,216,184,.75)}
.board-value{margin:6px 0 0;font-size:2.6rem;font-weight:700;color:var(--gold);
  font-variant-numeric:tabular-nums;font-family:var(--mono)}
.board-value .pct{font-size:1.1rem;color:rgba(232,216,184,.75);margin-left:10px}

/* ---- card ---- */
.card{background:var(--surface);border:1px solid var(--edge);border-radius:16px;
  padding:19px 22px;margin-top:16px}
.card h3{margin:0 0 15px;font-size:.66rem;letter-spacing:.19em;
  text-transform:uppercase;color:var(--dim);font-weight:700;
  display:flex;align-items:baseline;justify-content:space-between;gap:10px}
.card h3 .sub{font-family:var(--mono);font-size:.85rem;letter-spacing:0;
  color:var(--gold);font-variant-numeric:tabular-nums}
.card.wide{grid-column:1/-1}

/* one tile per grade, as many across as the main column fits */
.card-grid{display:grid;gap:16px;
  grid-template-columns:repeat(auto-fit,minmax(268px,1fr))}
.card-grid .card{margin-top:0}

/* ---- vertical bars (copied from the sibling's _columns()/.vchart) ---- */
.vchart{display:flex;align-items:flex-end;justify-content:center;
  gap:clamp(8px,2vw,22px);padding-top:2px}
.vcol{flex:1 1 0;max-width:84px;min-width:44px;display:flex;
  flex-direction:column;align-items:center;gap:6px}
.vnum{font-family:var(--mono);font-variant-numeric:tabular-nums;
  font-size:.9rem;font-weight:700;color:var(--gold);line-height:1}
/* Unlike the sibling's count chart -- where the track is a bare baseline
   because a box would imply a target that doesn't exist -- these bars ARE
   percent-of-roster, so the target is real and the track has to be visible:
   without it no bar ever reaches the top and every column reads as a squat
   block floating under its own number. This is the same track treatment the
   sibling uses on its horizontal progress bars. */
.vtrack{width:100%;height:clamp(72px,8vw,104px);display:flex;
  align-items:flex-end;background:rgba(232,216,184,.07);
  border-radius:7px;overflow:hidden}
.vfill{width:100%;border-radius:7px 7px 0 0;min-height:3px;
  background:linear-gradient(180deg,var(--gold),var(--gold-dim))}
.vlabel{font-size:.78rem;color:var(--text);white-space:nowrap}

/* a focused grade tab is the same tile zoomed in, not stretched thin */
.card.wide .vcol{max-width:130px}
.card.wide .vtrack{height:clamp(120px,14vw,190px)}
.card.wide .vnum{font-size:1.05rem}

footer.credit{text-align:center;color:var(--dim);font-size:.75rem;padding:18px}

@media (max-width:860px){
  .shell{flex-direction:column}
  .rail{flex:0 0 auto;border-right:0;border-bottom:1px solid var(--edge);
    padding:18px 16px;gap:16px}
  .rail-foot{margin-top:0}
  .tabs{flex-direction:row;flex-wrap:wrap;gap:8px}
  .tab-button{flex:1 1 auto;border-radius:999px;padding:9px 15px}
  .tab-name{flex:1 1 auto}
  .main{padding:20px 16px 44px}
}
"""

SCRIPT = """
document.querySelectorAll('.tab-button').forEach(function(button){
  button.addEventListener('click', function(){
    document.querySelectorAll('.tab-button').forEach(function(other){
      other.classList.remove('is-active');
      other.setAttribute('aria-selected','false');
    });
    document.querySelectorAll('.tab-panel').forEach(function(panel){
      panel.classList.remove('is-active');
    });
    button.classList.add('is-active');
    button.setAttribute('aria-selected','true');
    document.getElementById('panel-' + button.dataset.slug).classList.add('is-active');
  });
});
"""


def escape(text):
    return (str(text)
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def _vchart(pairs):
    """One vertical bar per (label, registered, size) triple.

    Bar height is that bar's OWN percent-of-roster-filled, not (as the
    sibling's plain _columns() does) a percentage of the tallest bar in the
    set -- "how full is this team" is the question this page answers, and a
    shared-max scale would make a small team's full roster look shorter than
    a big team's half-full one.
    """
    if not pairs:
        return '<p class="empty">No teams.</p>'
    cols = []
    for label, registered, size in pairs:
        pct = 0 if size == 0 else min(100, round(100 * registered / size))
        cols.append(
            '<div class="vcol" title="%s: %d of %d registered">'
            '<span class="vnum">%d / %d</span>'
            '<span class="vtrack"><span class="vfill" style="height:%d%%"></span></span>'
            '<span class="vlabel">%s</span>'
            '</div>' % (escape(label), registered, size, registered, size, pct, escape(label)))
    return '<div class="vchart">%s</div>' % "".join(cols)


def _tab_button(name, count_text, slug, active):
    return (
        '<button class="tab-button%s" data-slug="%s" role="tab" aria-selected="%s">'
        '<span class="tab-name">%s</span>'
        '<span class="tab-count">%s</span>'
        '</button>' % (" is-active" if active else "", slug,
                       "true" if active else "false", escape(name), escape(count_text)))


def _grade_tile(grade, teams, wide=False):
    """One tile per grade: the grade's own registered/rostered tally in the
    header, and a bar per team inside it."""
    registered = sum(r for _, r, _ in teams)
    size = sum(s for _, _, s in teams)
    return (
        '<section class="card%s">'
        '<h3>Grade %s <span class="sub">%d / %d</span></h3>'
        '%s'
        '</section>' % (" wide" if wide else "", escape(grade), registered, size,
                        _vchart(teams)))


def _overview_panel(slug, active, total, roster_total, pct, tiles):
    return (
        '<section class="tab-panel%s" id="panel-%s">'
        '<h1>Overview</h1>'
        '<div class="board-cell">'
        '<p class="board-label">Registered / Rostered</p>'
        '<p class="board-value">%d / %d<span class="pct">%d%%</span></p>'
        '</div>'
        '<div class="card-grid">%s</div>'
        '</section>' % (" is-active" if active else "", slug, total, roster_total, pct, tiles))


def _grade_panel(grade, slug, active, teams):
    return (
        '<section class="tab-panel%s" id="panel-%s">'
        '<h1>Grade %s</h1>'
        '%s'
        '</section>' % (" is-active" if active else "", slug, escape(grade),
                        _grade_tile(grade, teams, wide=True)))


def render_page(result, updated_stamp):
    teams = result["teams"]
    total = result["total"]
    roster_total = sum(t["size"] for t in teams.values())
    unmatched = result["unmatched"]
    pct = 0 if roster_total == 0 else round(100 * total / roster_total)

    by_grade = {}
    for label, team in teams.items():
        by_grade.setdefault(team["grade"], []).append((label, team["registered"], team["size"]))
    grades = sorted(by_grade)
    for grade in grades:
        by_grade[grade].sort()

    slugs = ["overview"] + ["grade-%s" % grade for grade in grades]
    names = ["Overview"] + ["Grade %s" % grade for grade in grades]
    count_texts = ["%d / %d" % (total, roster_total)] + [
        "%d / %d" % (sum(r for _, r, _ in by_grade[g]), sum(s for _, _, s in by_grade[g]))
        for g in grades
    ]

    tab_buttons = "".join(
        _tab_button(names[i], count_texts[i], slugs[i], i == 0)
        for i in range(len(slugs)))

    tiles = "".join(_grade_tile(grade, by_grade[grade]) for grade in grades)

    panels = _overview_panel("overview", True, total, roster_total, pct, tiles)
    panels += "".join(
        _grade_panel(grade, slugs[i + 1], False, by_grade[grade])
        for i, grade in enumerate(grades))

    unmatched_html = ""
    if unmatched:
        unmatched_html = ('<p class="unmatched-note">%d registration(s) could not be '
                          'matched to a rostered team and are not counted above.</p>'
                          % unmatched)

    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LSGBA Team Registration</title>
<link rel="icon" href="assets/favicon.png">
<style>%s</style>
</head>
<body>
<div class="shell">
  <aside class="rail">
    <div class="brand">
      <img src="assets/lsgba-badge-solid.png" alt="LSGBA">
      <div>
        <p class="brand-org">LSGBA</p>
        <p class="brand-sub">Team Registration</p>
      </div>
    </div>
    <div>
      <p class="rail-label">Grades</p>
      <nav class="tabs" role="tablist">%s</nav>
    </div>
    <div class="rail-foot">
      <p class="stamp">Updated %s</p>
      %s
    </div>
  </aside>
  <main class="main">%s</main>
</div>
<script>%s</script>
</body>
</html>
""" % (STYLE, tab_buttons, escape(updated_stamp), unmatched_html, panels, SCRIPT)
