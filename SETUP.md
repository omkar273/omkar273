# Setup — do this once

## 1. Drop these files into `omkar273/omkar273`

```
README.md
scripts/generate_cards.py
.github/workflows/metrics.yml
.github/workflows/snake.yml
```

Delete the old README content (assets/*.svg will be created automatically by
the workflow on its first run — don't create them by hand).

## 2. Create a token for the stats workflow

The default `GITHUB_TOKEN` that every Actions run gets automatically is
scoped to *this one repo* and can't call the GraphQL contributions API or
list your other repos, so `generate_cards.py` needs its own token:

1. GitHub → Settings → Developer settings → **Fine-grained tokens** → Generate new token
2. Resource owner: your account. Repository access: **Public repositories (read-only)** is enough.
3. Permissions: under "Account permissions" enable **Read access to profile** (this is what
   unlocks the GraphQL contribution stats).
4. Copy the token.
5. In `omkar273/omkar273` → Settings → Secrets and variables → Actions → **New repository secret**
   → name it `STATS_TOKEN`, paste the value.

## 3. Enable Actions write permissions

Repo → Settings → Actions → General → Workflow permissions → **Read and write permissions**.
(Both workflows commit files back to the repo; without this they'll fail silently.)

## 4. Run it once manually

Repo → Actions tab → "Regenerate profile stat cards" → Run workflow. Same for
"Generate contribution snake" (its first run also creates the `output`
branch the README's snake image points at — give it a minute after the run
finishes before checking the README).

After that, both run automatically every 6 hours — no more manual steps.

## 5. Sanity check

Open the repo's front page after both workflows have run once. If a card is
broken:
- `assets/*.svg` missing → the metrics workflow errored, check its log first (usually
  `STATS_TOKEN` missing/expired or missing the "Read access to profile" permission).
- Snake image broken → confirm the `output` branch was created (Platane/snk creates it on
  first successful run, not before).

## What's still on third-party services (intentionally)

`shields.io` (all the badge buttons), `readme-typing-svg.demolab.com` (the animated
name banner), and `komarev.com` (the view counter) still point off-repo. Those are
long-standing, widely-used, low-risk services — the same ones the inspiration profile
kept too — so replacing them wasn't worth the added maintenance. The stat cards and
snake were the pieces worth self-hosting because they're the ones known to go down.

## Notes on what I deliberately left out

- **Portfolio / resume links** — you don't have live ones yet. Send me the URLs whenever
  you do and I'll wire them into the socials row in one line.
- **DigiYoga, smart_agro, swastha-healthcare-app** — all three are WIP scaffolds with
  0 stars and default framework READMEs (no custom description set). Featuring them
  next to a 3.6k-star repo would undersell the profile, not help it. If any of them
  gets real substance later, tell me and I'll add a card.
- **Custom portrait / self-rated skill radar** (the dot-matrix headshot and the
  hand-scored radar chart in the inspiration profile) — the portrait needs an actual
  photo of you, and the skill radar is a self-assessment only you can make honestly.
  Both are easy to add later if you want them; I didn't want to fabricate either.
