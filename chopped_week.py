import requests
import json
from datetime import datetime

LEAGUE_ID = 781990
SEASON = 2026


def get_current_week():
    url = (
        f"https://lm-api-reads.fantasy.espn.com/"
        f"apis/v3/games/ffl/seasons/{SEASON}/segments/0/"
        f"leagues/{LEAGUE_ID}"
    )

    response = requests.get(
        url,
        params={"view": "mMatchupScore"}
    )

    response.raise_for_status()

    data = response.json()
    schedule = data.get("schedule", [])

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

    if not active_periods:
        return None

    return max(active_periods)


WEEK = get_current_week()

if WEEK is None:
    print("No active ESPN scoring week detected.")
    raise SystemExit
URL = (
    f"https://lm-api-reads.fantasy.espn.com/"
    f"apis/v3/games/ffl/seasons/{SEASON}/segments/0/"
    f"leagues/{LEAGUE_ID}"
)

def get_week_status(data):
    schedule = data.get("schedule", [])

    week_matchups = [
        matchup
        for matchup in schedule
        if matchup.get("matchupPeriodId") == WEEK
    ]

    if not week_matchups:
        return "LIVE"

    for matchup in week_matchups:
        winner = matchup.get("winner")

        if winner in (None, "UNDECIDED"):
            return "LIVE"

    return "FINAL"

def get_espn_data():

    params = [
        ("view", "mTeam"),
        ("view", "mMatchupScore"),
    ]

    response = requests.get(
        URL,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    return response.json()


def get_team_names(data):

    teams = {}

    for team in data.get("teams", []):

        team_id = team.get("id")
        team_name = team.get("name", "Unknown")

        teams[team_id] = team_name

    return teams


def get_week_scores(data):

    schedule = data.get("schedule", [])

    week_matchups = [
        matchup
        for matchup in schedule
        if matchup.get("matchupPeriodId") == WEEK
    ]

    scores = []

    for matchup in week_matchups:

        home = matchup.get("home", {})
        away = matchup.get("away", {})

        scores.append({
            "team_id": home.get("teamId"),
            "score": home.get("totalPointsLive", 0),
            "projected": home.get("totalProjectedPointsLive", 0)
        })

        scores.append({
            "team_id": away.get("teamId"),
            "score": away.get("totalPointsLive", 0),
            "projected": away.get("totalProjectedPointsLive", 0)
        })

    return scores


print()
print("=" * 70)
print("CHOPPED FANTASY FOOTBALL")
print(f"WEEK {WEEK}")
print("=" * 70)
print()

try:

    print("Connecting to ESPN...")

    data = get_espn_data()

    print("ESPN connection successful.")
    print()

    status = get_week_status(data)

    teams = get_team_names(data)
    scores = get_week_scores(data)

    results = []

    results = []

    for entry in scores:

        team_id = entry["team_id"]

        team_name = teams.get(
            team_id,
            f"Team {team_id}"
        )

        results.append({
            "team_id": team_id,
            "team_name": team_name,
            "score": entry["score"],
            "projected": entry["projected"]
        })

    results.sort(key=lambda x: x["score"])

    # ---------------------------------------------------------
    # DISPLAY RESULTS
    # ---------------------------------------------------------

    print("=" * 70)
    print(f"WEEK {WEEK} — CHOPPING BLOCK")
    print("=" * 70)
    print()

    for index, team in enumerate(results, start=1):

        if index == 1:
            marker = "🔴 CHOPPING BLOCK"
        elif index <= 3:
            marker = "🟠 DANGER ZONE"
        else:
            marker = ""

        print(
            f"{index:2}. "
            f"{team['team_name']:<30} "
            f"{team['score']:>7.2f} "
            f"(Proj: {team['projected']:>7.2f}) "
            f"{marker}"
        )

    print()
    print("=" * 70)

    lowest = results[0]

    print(
        f"CURRENT CHOPPING BLOCK: "
        f"{lowest['team_name']} "
        f"({lowest['score']:.2f})"
    )

    print("=" * 70)

    # ---------------------------------------------------------
    # SAVE DATA
    # ---------------------------------------------------------

    output = {
        "league_id": LEAGUE_ID,
        "season": SEASON,
        "week": WEEK,
        "updated_at": datetime.now().isoformat(),
        "status": status,
        "chopping_block": {
            "team_id": lowest["team_id"],
            "team_name": lowest["team_name"],
            "score": lowest["score"],
            "projected": lowest["projected"]
        },
        "teams": results
    }

    filename = f"week_{WEEK}_data.json"

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=2)

    print()
    print(f"Data saved to: {filename}")
    print()

except Exception as e:

    print()
    print("=" * 70)
    print("ERROR")
    print("=" * 70)
    print(type(e).__name__)
    print(e)