# Chopped Fantasy Football

A read-only dashboard for an ESPN fantasy football elimination league: every
week, the lowest-scoring active team gets chopped.

The site is fully static. The page talks to ESPN's public fantasy API straight
from the browser, so there is no server, no build step, and no scheduled job —
GitHub Pages can host it as-is.

## Layout

```
index.html               the dashboard page
assets/chopped-core.js   ESPN client + elimination logic (shared)
assets/app.js            browser rendering
assets/styles.css        styles
scripts/*.js             Node CLI equivalents
data/league_781990_history/     archived ESPN CSV export, 2018-2026
scripts/espn_league_history.py  regenerates that export from ESPN
```

`assets/chopped-core.js` has no DOM or Node dependencies, so the browser and
the CLI scripts run the exact same logic.

## Deploying to GitHub Pages

1. Push to `main`.
2. Repo **Settings → Pages → Build and deployment**.
3. Source: **Deploy from a branch**, branch `main`, folder `/ (root)`.

The dashboard is then live at `https://<user>.github.io/<repo>/`. Every visit
pulls fresh data from ESPN, and the page refreshes itself every 30 seconds.

To point the page at a different league without editing code, use query
parameters: `?league=781990&season=2026`.

## Running locally

Open `index.html` through a local web server — ES modules do not load over
`file://`:

```
npm run serve       # then open http://localhost:3000
```

## CLI

Node 18+ is required (for built-in `fetch`). There are no dependencies to
install.

```
npm run week            # current week's chopping block and standings
npm run elimination     # season elimination history
npm run current-week    # ESPN's current scoring week
npm start               # both of the first two, in order
```

## How elimination works

ESPN is the source of truth and nothing is cached to disk. On every load the
app fetches the league once and replays the season:

- Each week before the current one is checked; a week counts as `FINAL` only
  when ESPN has decided all of its matchups.
- In each completed week, the lowest-scoring team still active is eliminated.
  Teams tied for last are all eliminated together.
- The replay stops at the first week that is not final, so a live week can
  never eliminate anybody.

While a week is live, standings and the chopping block are ranked by ESPN's
live projections; once the week is final they rank by actual score.

## League history

The live dashboard reads only the current season from ESPN. `data/league_781990_history/`
is a point-in-time archive of the league's full recorded history, so past seasons
stay available even as ESPN ages them out:

```
standings_<year>.csv   final rank, owners, W/L/T, points for and against
matchups_<year>.csv    every recorded game: week, both teams, both scores, playoff flag
draft_<year>.csv       round, pick, team, player, keeper flag
all_<kind>.csv         the same rows for every season, combined
```

Seasons 2018 through 2025 have complete results. The 2026 file set holds
preseason standings only, with no matchups played yet.

Nothing in the app imports these files today; they are checked in as a durable
record. Regenerate them with:

```
pip install espn_api
cd data && python3 ../scripts/espn_league_history.py
```

The league is private, so the script needs session cookies — pass `--espn-s2`
and `--swid` (or set `ESPN_S2` and `SWID`), copied from fantasy.espn.com under
dev tools, Application, Cookies. `--first-year` and `--last-year` narrow the range.

These CSVs carry real manager names and are checked into a public repository.
