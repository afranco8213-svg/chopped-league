import json
import os

WEEK_FILE = "week_2_data.json"
HISTORY_FILE = "chopped_history.json"


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


week_data = load_week_data()
history = load_history()

week = week_data["week"]
status = week_data.get("status", "LIVE").upper()
teams = week_data["teams"]

eliminated_ids = {
    item["team_id"]
    for item in history["eliminated"]
}

active_teams = [
    team
    for team in teams
    if team["team_id"] not in eliminated_ids
]

active_teams.sort(key=lambda x: x["score"])


print()
print("CHOPPED SEASON TRACKER")
print("=" * 70)
print(f"WEEK {week}")
print(f"STATUS: {status}")
print("=" * 70)


# ---------------------------------------------------------
# CURRENT CHOPPING BLOCK
# ---------------------------------------------------------

print()
print("CURRENT CHOPPING BLOCK")
print("-" * 70)

all_scores_zero = (
    active_teams
    and all(team["score"] == 0 for team in active_teams)
)

if all_scores_zero and status == "LIVE":

    print("⏳ Week has not started scoring yet.")

elif active_teams:

    lowest_score = active_teams[0]["score"]

    chopping_block = [
        team
        for team in active_teams
        if team["score"] == lowest_score
    ]

    for team in chopping_block:
        print(
            f"🔴 {team['team_name']:<32} "
            f"{team['score']:.2f}"
        )


# ---------------------------------------------------------
# DANGER ZONE
# ---------------------------------------------------------

print()
print("DANGER ZONE")
print("-" * 70)

if all_scores_zero and status == "LIVE":

    print("⏳ Waiting for Week 2 scoring.")

else:

    for team in active_teams[1:3]:

        print(
            f"🟠 {team['team_name']:<32} "
            f"{team['score']:.2f}"
        )


# ---------------------------------------------------------
# ACTIVE TEAMS
# ---------------------------------------------------------

print()
print("ACTIVE TEAMS")
print("-" * 70)

for index, team in enumerate(active_teams, start=1):

    print(
        f"{index:>2}. "
        f"{team['team_name']:<32} "
        f"{team['score']:>7.2f}"
    )


# ---------------------------------------------------------
# TEAM COUNTS
# ---------------------------------------------------------

print()
print(f"ACTIVE TEAMS: {len(active_teams)}")
print(f"ELIMINATED:   {len(eliminated_ids)}")
print(f"TOTAL TEAMS:  {len(teams)}")


# ---------------------------------------------------------
# ELIMINATION HISTORY
# ---------------------------------------------------------

print()
print("ELIMINATION HISTORY")
print("-" * 70)

if history["eliminated"]:

    for item in history["eliminated"]:

        print(
            f"Week {item['week']}: "
            f"{item['team_name']} "
            f"({item['score']:.2f})"
        )

else:

    print("No teams eliminated yet.")


print("=" * 70)