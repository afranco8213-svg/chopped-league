# Chopped Fantasy Football

A read-only dashboard for an ESPN fantasy football elimination league: every
week, the lowest-scoring active team gets chopped.

The site is fully static. The page talks to ESPN's public fantasy API straight
from the browser, so there is no server, no build step, and no scheduled job —
GitHub Pages can host it as-is.

## Layout

```
index.html                the dashboard page
assets/chopped-core.js    ESPN client + elimination logic (shared)
assets/schedule-core.js   offseason schedule + reminder logic (shared)
assets/app.js             browser rendering
assets/styles.css         styles
data/offseason.json       key offseason dates
scripts/*.js              Node CLI equivalents + the email notifier
.github/workflows/        the daily notification job
```

Neither `*-core.js` file has DOM or Node dependencies, so the browser, the CLI
scripts, and the notifier all run the exact same logic.

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
npm run schedule        # offseason key dates and countdowns
npm run notify:dry      # print today's reminder email without sending it
npm start               # both of the first two, in order
```

## Offseason schedule and email reminders

`data/offseason.json` holds the league's key dates — voting windows, dues
deadlines, draft day. The dashboard renders them at the bottom of the page, and
a GitHub Actions cron job emails the league as each one approaches.

Every event needs a `date` and a `name`; `description`, `link`, and
`remindersDaysBefore` are optional:

```json
{
    "id": "draft-date-vote-closes",
    "date": "2027-03-22",
    "name": "Draft Date Voting Closes",
    "description": "Final day to vote on the draft date.",
    "link": "https://forms.gle/example",
    "remindersDaysBefore": [7, 3, 1, 0]
}
```

`remindersDaysBefore` is how many days ahead of the date each email goes out;
`0` is the morning of. Leave it off and the event uses the default `[7, 1, 0]`.
The dates shipped in the file are placeholders — edit them and commit.

### Wiring up the emails

`.github/workflows/offseason-notify.yml` runs `scripts/notify.js` every day at
13:00 UTC. Anything due that day goes out as a single digest, so three
deadlines in one morning still means one email. Recipients are Bcc'd, which
keeps the league's addresses off each other's screens — and out of this repo,
since they live in a secret rather than a committed file.

In **Settings → Secrets and variables → Actions**, add these secrets:

| Secret | Value |
| --- | --- |
| `GMAIL_USER` | the Gmail address that sends the mail |
| `GMAIL_APP_PASSWORD` | a Google [app password](https://myaccount.google.com/apppasswords), not the account password |
| `NOTIFY_TO` | comma-separated league addresses |

And optionally, under the **Variables** tab:

| Variable | Value |
| --- | --- |
| `SITE_URL` | dashboard link to include in the email |
| `NOTIFY_FROM_NAME` | sender name (default `Chopped League`) |

App passwords require 2-Step Verification on the Google account, and only work
on accounts that allow them — some Workspace domains disable them.

### Testing it

Locally, without sending anything:

```
npm run notify:dry                              # today
node scripts/notify.js --dry-run --date=2027-03-22
```

On GitHub, the workflow's **Run workflow** button takes the same two options —
it defaults to a dry run, so an accidental click can't mail the league. Switch
the dry-run toggle off to send for real.

One caveat: the job has no memory of what it already sent. The cron fires once
a day so that's invisible in normal use, but manually running it for real twice
on the same date sends the same email twice.

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
