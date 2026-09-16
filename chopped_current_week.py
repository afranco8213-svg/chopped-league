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
        "view": "mSettings",
        "view": "mMatchupScore"
    }
)

response.raise_for_status()

data = response.json()

status = data.get("status", {})

print()
print("=" * 60)
print("CHOPPED CURRENT WEEK DETECTOR")
print("=" * 60)

print(f"ESPN current matchup period: {status.get('currentMatchupPeriod')}")
print(f"ESPN current scoring period: {status.get('currentScoringPeriodId')}")
print(f"ESPN season stage: {status.get('seasonId')}")

current_week = status.get("currentMatchupPeriod")

if current_week is not None:
    print()
    print(f"Current ESPN scoring week: {current_week}")
else:
    print()
    print("ESPN did not provide a current matchup period.")

print("=" * 60)
