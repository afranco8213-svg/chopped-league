import json
import os
import requests

LEAGUE_ID = 781990
SEASON = 2026
HISTORY_FILE = "chopped_history.json"


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
    print()
    print("No active ESPN scoring week detected.")
    raise SystemExit

WEEK_FILE = f"week_{WEEK}_data.json"


def load_week_data():
    with open(WEEK_FILE, "r") as f:
        return json.load(f)


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)

    return {
        "eliminated": []
    }


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


week_data = load_week_data()
history = load_history()

week = week_data["week"]
status = week_data.get("status", "LIVE").upper()
teams = week_data["teams"]

print()
print("CHOPPED ELIMINATION ENGINE")
print(f"WEEK {week}")
print(f"STATUS: {status}")
print("=" * 70)

# ---------------------------------------------------------
# SAFETY CHECK — NEVER ELIMINATE DURING A LIVE WEEK
# ---------------------------------------------------------

if status != "FINAL":

    print()
    print("🟡 WEEK IS STILL LIVE")
    print()
    print("No team will be eliminated.")
    print()

    eliminated_ids = {
        item["team_id"]
        for item in history["eliminated"]
    }

    active_teams = [
        team
        for team in teams
        if team["team_id"] not in eliminated_ids
    ]

    if active_teams:

        lowest_score = min(
            team["score"]
            for team in active_teams
        )

        chopping_block = [
            team
            for team in active_teams
            if team["score"] == lowest_score
        ]

        print("Current chopping block:")

        for team in chopping_block:
            print(
                f"  {team['team_name']} — "
                f"{team['score']:.2f}"
            )

    print()
    raise SystemExit

# ---------------------------------------------------------
# SAFETY CHECK — FINAL WEEK MUST HAVE REAL SCORES
# ---------------------------------------------------------

if status == "FINAL":

    if not teams:
        print()
        print("ERROR: No team data found.")
        print("No elimination will be recorded.")
        raise SystemExit

    invalid_scores = [
        team
        for team in teams
        if team["score"] is None
    ]

    if invalid_scores:
        print()
        print("ERROR: Final scores are incomplete.")
        print("No elimination will be recorded.")
        raise SystemExit

# ---------------------------------------------------------
# IDENTIFY ALREADY ELIMINATED TEAMS
# ---------------------------------------------------------

eliminated_ids = {
    item["team_id"]
    for item in history["eliminated"]
}


# ---------------------------------------------------------
# SAFETY CHECK — DON'T PROCESS THE SAME WEEK TWICE
# ---------------------------------------------------------

week_already_processed = any(
    item["week"] == week
    for item in history["eliminated"]
)

if week_already_processed:

    print()
    print("⚠️  THIS WEEK HAS ALREADY BEEN PROCESSED.")
    print()
    print("No additional elimination will be recorded.")
    print()
    print("Current elimination history:")
    print()

    for item in history["eliminated"]:
        print(
            f"Week {item['week']}: "
            f"{item['team_name']} "
            f"({item['score']:.2f})"
        )

    print()
    raise SystemExit


# ---------------------------------------------------------
# ONLY ACTIVE TEAMS CAN BE ELIMINATED
# ---------------------------------------------------------

active_teams = [
    team
    for team in teams
    if team["team_id"] not in eliminated_ids
]


if not active_teams:

    print()
    print("🏆 NO ACTIVE TEAMS REMAIN.")
    raise SystemExit


# ---------------------------------------------------------
# FIND LOWEST SCORE
# ---------------------------------------------------------

lowest_score = min(
    team["score"]
    for team in active_teams
)


# ---------------------------------------------------------
# ALL TEAMS TIED FOR LOWEST ARE ELIMINATED
# ---------------------------------------------------------

eliminated_this_week = [
    team
    for team in active_teams
    if team["score"] == lowest_score
]


print()

if len(eliminated_this_week) > 1:
    print("🔴 TIE — MULTIPLE TEAMS ELIMINATED:")
else:
    print("🔴 TEAM ELIMINATED:")

print()

for team in eliminated_this_week:

    print(
        f"  {team['team_name']} — "
        f"{team['score']:.2f}"
    )

    history["eliminated"].append({
        "week": week,
        "team_id": team["team_id"],
        "team_name": team["team_name"],
        "score": team["score"]
    })


# ---------------------------------------------------------
# SAVE HISTORY
# ---------------------------------------------------------

save_history(history)


print()
print("=" * 70)
print("ELIMINATION HISTORY")
print("=" * 70)

for item in history["eliminated"]:

    print(
        f"Week {item['week']}: "
        f"{item['team_name']} "
        f"({item['score']:.2f})"
    )

print()
print(f"History saved to: {HISTORY_FILE}")