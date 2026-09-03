# LSGBA Team Registration Dashboard

Tracks the 2026-2027 LSGBA Travel Roster Acceptance and Registration survey,
published at https://ricc7059.github.io/lsgba-team-registration-dashboard/

Rebuilt by the `/lsgba-team-registration-dashboard` Claude Code skill, which
cross-references registrants against the private team roster PDF and
publishes a per-team running count (registered / roster size).

**This repo is public and contains aggregate counts only.** Raw Quick Report
exports and the roster PDF stay in `~/Downloads` and are blocked by
`.gitignore`. A fail-closed PII scan runs before every push.

Tests: `python3 -m unittest discover tests`

## The installed skill is a symlink

`~/.claude/skills/lsgba-team-registration-dashboard/SKILL.md` is a **symlink**
to `skill/SKILL.md` in this repo, so editing the repo copy updates the skill
Claude Code actually loads. Moving, renaming, or deleting this repo breaks
the installed skill; re-create the symlink if you relocate the checkout.

## Design

See `docs/superpowers/specs/2026-09-03-team-registration-dashboard-design.md`
for the full design rationale, including why the roster PDF needs
coordinate-based parsing rather than a plain-text column split.
