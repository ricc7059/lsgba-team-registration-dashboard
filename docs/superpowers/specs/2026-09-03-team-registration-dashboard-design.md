# LSGBA Team Registration Dashboard — Design

## Purpose

Track the 2026-2027 LSGBA Travel Roster Acceptance and Registration survey
(SportsEngine survey id `1132938`) and publish, per run, how many rostered
athletes have completed registration — broken down by team — without ever
publishing or committing an athlete's name.

This is a sibling project to `lsgba-registrations-dashboard` (which tracks
Travel Tryout / Skills Course funnels over time). That project answers "how
many people signed up, over time." This one answers a different question —
"of the kids already placed on a team, how many have registered?" — which
requires cross-referencing the registration export against a private team
roster that the registration survey itself does not capture (the survey has
no "team" field).

## Source data

- **Registration survey**: `https://lsgba.sportngin.com/survey/show/1132938`,
  "2026-2027 LSGBA Travel Roster Acceptance and Registration". Fields: First
  Name, Last Name, Date of Birth, Grade, Guardian First/Last Name, Email,
  Registration Date, Order Number, Account Email, Order Status. No team
  field.
- **Team roster**: `~/Downloads/2026-2027 LSGBA Travel Roster.pdf`, a
  Google-Docs-rendered table, one column per team (e.g. "3 Gold", "4 Red", "8
  Gold"), team's leading digit is the grade level. 9 teams, 76 athletes
  total this season. This file contains children's full names and must never
  be committed, matching the existing project's treatment of its own private
  roster source (`history.py`'s docstring).

## Pipeline

1. **Check** — navigate directly to `/survey/show/1132938` (no Enabled-tab
   discovery; this skill tracks exactly one survey), read `TOTAL ENTRIES`,
   compare against `state.json` via `scripts/check.py` (copied verbatim from
   the sibling project — it is already generic over one-or-more ids).
2. **Export** — same `#exportCsvUnsaved` click + `unnamed_report*.csv` poll +
   immediate rename pattern as the sibling project. Rename to
   `lsgba-team-registration-YYYY-MM-DD-HHMM.csv`. Record via `scripts/record.py`
   (also copied verbatim).
3. **Cross-reference (the new part)** — `scripts/team_match.py` reads the
   *raw* export (First Name, Last Name, Grade — columns the sibling project's
   `parse.py` would drop) and `scripts/roster.py` reads the roster PDF fresh
   from disk via `pdftotext -bbox` (word-level bounding boxes, needed because
   names are center-aligned per column and a fixed-character-column parse
   would drift). For each registrant: within roster members at the same
   grade, match on **full last name (case-insensitive) + first-name initial
   (case-insensitive)**. Exactly one matching team → assign. Zero, or more
   than one *distinct team* matching → fall back to a **second phase**: full
   name (first + last, lowercased) matched anywhere on the roster,
   regardless of grade. This phase 2 was added 2026-09-03 after the first
   live run found 7/32 registrants unmatched purely because the survey's
   grade answer was one grade off from the roster's — the registrant's full
   name matched exactly once, just not at the grade they'd stated. Only when
   *both* phases fail to resolve to exactly one team does a registrant land
   in the `unmatched` bucket. **The only thing that leaves
   `team_match.match_export()` is counts** — no name, DOB, or contact field
   is returned, logged, or persisted anywhere.
4. **Render** — `scripts/render.py` builds one static page: total registered
   vs. total rostered, then each team as a `registered / roster size` line
   grouped by grade, plus the unmatched count if nonzero. Reuses the sibling
   project's dark maroon/gold palette and badge assets for visual continuity
   but is a single page, not a tabbed dashboard — there is only one thing to
   show.
5. **Publish** — `scripts/piiscan.py` (copied verbatim) scans the rendered
   HTML before write, as a fail-closed net. Commit and push to a new public
   repo `ricc7059/lsgba-team-registration-dashboard`, GitHub Pages serving
   `main` root, same as the sibling project.

## Roster PDF parsing

`pdftotext -bbox` emits every word's text and pixel bounding box. Parsing is
split into a thin, hard-to-unit-test I/O layer and a pure, fully-tested logic
layer:

- `extract_words(pdf_path)` — runs `pdftotext -bbox`, parses the XML into a
  flat list of `{"text", "xMin", "xMax", "yMin", "yMax"}`. Verified manually
  against the real file each season; not unit tested (no PDF-authoring tool
  available in this environment).
- `group_into_teams(words)` — pure function, fully unit tested against
  synthetic word lists shaped like `extract_words()`'s output. Detects header
  words (a digit token immediately followed by a color token on the same
  line), clusters headers into rows, derives each column's x-range as the
  midpoint boundary between adjacent header centers within that row, assigns
  every non-header word below a header row (and above the next header row,
  if any) to a column by x-range, groups words into name-lines by shared
  `yMin`, and splits each line's joined text on its last space into
  (first, last) — this also correctly handles a hyphenated or two-part last
  name.
- `load_roster(pdf_path)` = `group_into_teams(extract_words(pdf_path))`. A
  season with a differently-shaped PDF will need eyes on it; this is
  explicitly not designed to be bulletproof against arbitrary layouts, only
  against this template's known quirks (centered text, decorative
  "Go South!" cell with no header of its own, which is simply never assigned
  to a column since no header exists for it).

## What is NOT built

- No time-series / funnel charts. The prior season's registration dashboard
  needed those because it tracked a signup curve over an open window; this
  page reports current-state counts against a fixed roster and is rebuilt
  fresh each run.
- No fuzzy/typo-tolerant matching beyond the agreed rule (grade + last name +
  first initial). Anything that rule can't resolve uniquely is surfaced as a
  count-only "Unmatched" bucket, reported to the user in chat so they can
  investigate the source data themselves — never guessed at automatically.
- No mechanism to discover other team-registration surveys. If a second one
  appears in a future season, this skill's hardcoded survey id is the thing
  to change.

## Testing

`python3 -m unittest discover tests`, mirroring the sibling project. Fixtures
use synthetic names (`Ada Fake`, `Bea Fake`, ...) exactly as the sibling
project's fixtures do — never real athlete data.
