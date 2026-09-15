import requests

LEAGUE_ID = 781990
SEASON = 2026

URL = (
    f"https://lm-api-reads.fantasy.espn.com/"
    f"apis/v3/games/ffl/seasons/{SEASON}/segments/0/"
    f"leagues/{LEAGUE_ID}"
)

response = requests.get(
    URL,
    params={
        "view": "mMatchupScore"
    }
)

response.raise_for_status()

data = response.json()

schedule = data.get("schedule", [])

print()
print("=" * 60)
print("CHOPPED CURRENT WEEK DETECTOR")
print("=" * 60)

if not schedule:
    print("No ESPN schedule data found.")
    raise SystemExit

# Find matchup periods that have actual scoring activity.
active_periods = []

for matchup in schedule:

    period = matchup.get("matchupPeriodId")

    if period is None:
        continue

    home = matchup.get("home", {})
    away = matchup.get("away", {})

    home_score = home.get("totalPointsLive", 0) or 0
    away_score = away.get("totalPointsLive", 0) or 0

    if home_score > 0 or away_score > 0:
        active_periods.append(period)


if active_periods:

    current_week = max(active_periods)

    print(f"Current ESPN scoring week: {current_week}")

else:

    print("No scoring activity detected yet.")
    print("The season may not have started.")

print("=" * 60)