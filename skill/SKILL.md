---
name: lsgba-team-registration-dashboard
description: Use when the user wants to refresh the LSGBA team registration dashboard or check how many rostered athletes have completed official team registration. Checks one specific SportsEngine survey (the 2026-2027 Travel Roster Acceptance and Registration), cross-references registrants against the private team roster PDF, and rebuilds a published GitHub Pages page showing a per-team running count.
---

# LSGBA Team Registration Dashboard

Repo: `/Users/ricci/lsgba-team-registration-dashboard`
Published: https://ricc7059.github.io/lsgba-team-registration-dashboard/

Exports land in `/Users/ricci/Downloads` and are never committed. Same for
the roster PDF.

This is a sibling of the `/lsgba-registration-dashboard` skill, but tracks a
different kind of survey: not "how many people signed up over time" but "of
the kids already placed on a team, how many have registered" — which
requires cross-referencing against a roster the survey itself doesn't
capture. See `docs/superpowers/specs/2026-09-03-team-registration-dashboard-design.md`
for the full design rationale.

## 1. Read the current entry count

Navigate Chrome to `https://lsgba.sportngin.com/survey/show/1132938` — this
skill tracks exactly this one survey, not the Enabled list. If you land on a
login page, STOP and tell the user to log into SportsEngine in Chrome. Do
not try to authenticate.

Read the `TOTAL ENTRIES` figure from the header.

## 2. Decide whether there is work

```bash
cd /Users/ricci/lsgba-team-registration-dashboard
python3 scripts/check.py --counts '[{"id":"1132938","name":"2026-2027 LSGBA Travel Roster Acceptance and Registration","count":32}]'
```

Read the exit code exactly:

- **0** — changed. Continue.
- **3** — nothing moved. Report "no change since \<lastRun\>" and STOP. Do not
  export, rebuild, commit, or push.
- **2** — bad input or unreadable state. Report the error and STOP. Never
  report "no change" on a 2.

## 3. Export

1. On `/survey/show/1132938`, click the export link:
   ```javascript
   () => { document.querySelector('#exportCsvUnsaved').click(); return 'clicked'; }
   ```
2. Poll `~/Downloads` for a new `unnamed_report*.csv` for up to 30 seconds.
3. **Rename it immediately** to `lsgba-team-registration-YYYY-MM-DD-HHMM.csv`
   — the download is always called `unnamed_report.csv` and collides as
   `unnamed_report (1).csv` on a second export.
4. Record it:
   ```bash
   python3 scripts/record.py --id 1132938 \
     --name "2026-2027 LSGBA Travel Roster Acceptance and Registration" \
     --count <n> --export <filename>
   ```

If no file appears within 30 seconds, fall back to reading the report table
out of the DOM and writing the CSV yourself, paging through all results.
**Say so in your report** — a silent fallback hides a broken export.

## 4. Confirm the roster PDF is in place

`scripts/build.py` looks for `~/Downloads/*Travel Roster*.pdf` and uses the
most recently modified match. If none is found, it raises `FileNotFoundError`
— tell the user to place this season's roster PDF in Downloads (or pass
`--roster <path>` explicitly) and stop there.

## 5. Rebuild and publish

```bash
python3 scripts/build.py
python3 -m unittest discover tests
git add -A && git commit -m "Refresh team registration dashboard: <summary>" && git push
```

**Run one at a time, stop on the first non-zero exit.** `build.py` exits 1
if `state.json` has no recorded export for `1132938`, or if the recorded
export file is missing from `~/Downloads` — re-run step 3.

If `build.py` prints `WARNING: ... has N CSV rows but state says ...`, the
CSV row count and the count read off the SportsEngine page disagree. The
build still continues; carry the discrepancy into your report.

`build.py` also runs the PII scan before writing and refuses to publish if it
trips. If it raises `PIIFound`, STOP and report which pattern matched — never
bypass it.

Pages redeploys automatically on push, usually within a minute.

## 6. Report back

Tell the user:

- The new total registered vs. total roster size (e.g. "34 / 76").
- The per-team breakdown, e.g. "3 Gold — 8/8, 4 Gold — 7/9, ...".
- The unmatched count, if nonzero — this means some registrants could not be
  confidently matched to a team (grade + last name + first initial, exactly
  one team). This needs a human to investigate the source data; do not guess
  at who they are.
- Whether the CSV-fallback fired in step 3, or a count mismatch was printed
  in step 5.
- The dashboard URL.

## Notes

- Never open an order, payment, or discount page. This skill does not report
  financials.
- The matching rule has two phases, and phase 2 only ever runs after phase 1
  has already failed to resolve a registrant to exactly one team:
  1. Same grade, exact last name, matching first-name initial (all
     case-insensitive).
  2. Full name (first + last, lowercased) matched anywhere on the roster,
     regardless of grade. This exists because the survey's grade answer and
     the roster's grade can disagree (seen live: a parent answering with the
     athlete's just-finished grade instead of the grade their roster team
     plays at) — a case phase 1 alone would always miss.
  Neither phase is fuzzy/typo-tolerant. A registrant neither phase can
  uniquely resolve lands in the Unmatched count, not a guess.
- The roster PDF changes every season and is never committed (like the
  sibling project's frozen roster in `history.py`) — it is re-read fresh
  from Downloads on every build.
- If next season's survey gets a new SportsEngine id, update `REG_ID` in
  `scripts/build.py` and the id in this skill's steps 1-3.
- `--dry-run` on `build.py` writes `index.html` normally but skips the
  commit-and-push step and says so. It is a "stop before publishing" switch,
  not a "change nothing on disk" switch.
