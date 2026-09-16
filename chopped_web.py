from flask import Flask, render_template_string
from pathlib import Path
import json
import os
import requests

app = Flask(__name__)

LEAGUE_ID = 781990
SEASON = 2026

ESPN_URL = (
    f"https://lm-api-reads.fantasy.espn.com/"
    f"apis/v3/games/ffl/seasons/{SEASON}/segments/0/"
    f"leagues/{LEAGUE_ID}"
)

def get_espn_current_week():
    try:
        response = requests.get(
            ESPN_URL,
            params={"view": "mSettings"},
            timeout=10
        )
        response.raise_for_status()

        data = response.json()

        return int(data["status"]["currentMatchupPeriod"])

    except Exception as e:
        print(f"Could not determine ESPN current week: {e}")
        return None
def get_espn_week_data(week):
    try:
        params = [
            ("view", "mTeam"),
            ("view", "mMatchupScore")
        ]

        response = requests.get(
            ESPN_URL,
            params=params,
            timeout=15
        )
        response.raise_for_status()

        data = response.json()

        team_names = {
            team["id"]: team.get("name", f"Team {team['id']}")
            for team in data.get("teams", [])
        }

        teams = []

        week_matchups = [
            matchup
            for matchup in data.get("schedule", [])
            if matchup.get("matchupPeriodId") == week
        ]

        status = "FINAL"

        for matchup in week_matchups:

            if matchup.get("winner") in (None, "UNDECIDED"):
                status = "LIVE"

            for side in ("home", "away"):

                entry = matchup.get(side)

                if not entry:
                    continue

                team_id = entry.get("teamId")

                teams.append({
                    "team_id": team_id,
                    "team_name": team_names.get(
                        team_id,
                        f"Team {team_id}"
                    ),
                    "score": entry.get(
                        "totalPointsLive",
                        entry.get("totalPoints", 0)
                    ),
                    "projected": entry.get(
                        "totalProjectedPointsLive",
                        entry.get("totalProjectedPoints", 0)
                    )
                })

        if not teams:
            return None

        return {
            "week": week,
            "status": status,
            "teams": teams
        }

    except Exception as e:
        print(f"Could not load ESPN Week {week}: {e}")
        return None
BASE_DIR = Path(__file__).resolve().parent
HISTORY_FILE = BASE_DIR / "chopped_history.json"

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Chopped Fantasy Football</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="30">

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, Helvetica, sans-serif;
            background: #0b1120;
            color: #f9fafb;
        }

        .header {
            background: linear-gradient(135deg, #111827, #1e293b);
            padding: 28px 35px;
            border-bottom: 1px solid #334155;
        }

        .header h1 {
            margin: 0;
            font-size: 32px;
        }

        .header p {
            margin: 8px 0 0;
            color: #94a3b8;
        }

        .container {
            max-width: 1250px;
            margin: 30px auto;
            padding: 0 20px;
        }

        .cards {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 18px;
        }

        .card {
            background: #111827;
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 22px;
            box-shadow: 0 8px 25px rgba(0,0,0,.18);
        }

        .stat-label {
            color: #94a3b8;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: .08em;
            margin-bottom: 10px;
        }

        .stat-value {
            font-size: 30px;
            font-weight: 700;
        }

        .live {
            color: #facc15;
        }

        .final {
            color: #4ade80;
        }

        .section {
            margin-top: 32px;
        }

        .section-title {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 14px;
        }

        .section-title h2 {
            margin: 0;
            font-size: 22px;
        }

        .section-title span {
            color: #64748b;
            font-size: 13px;
        }

        .chopping {
            border: 1px solid #dc2626;
            background: linear-gradient(135deg, #3f1111, #111827);
        }

        .danger {
            border: 1px solid #f59e0b;
        }

        .team-row {
            display: grid;
            grid-template-columns: 45px 1fr 120px 120px;
            gap: 15px;
            align-items: center;
            padding: 15px 0;
            border-bottom: 1px solid #263244;
        }

        .team-row:last-child {
            border-bottom: none;
        }

        .rank {
            color: #64748b;
            font-weight: bold;
        }

        .team-name {
            font-weight: 700;
        }

        .score {
            text-align: right;
            font-weight: 700;
        }

        .projection {
            text-align: right;
            color: #94a3b8;
        }

        .bar {
            height: 7px;
            background: #263244;
            border-radius: 10px;
            margin-top: 8px;
            overflow: hidden;
        }

        .bar-fill {
            height: 100%;
            background: #ef4444;
            border-radius: 10px;
        }

        .eliminated {
            display: grid;
            grid-template-columns: 1fr 100px 120px;
            gap: 15px;
            align-items: center;
        }

        .badge {
            display: inline-block;
            padding: 5px 9px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }

        .badge-live {
            background: #422006;
            color: #fbbf24;
        }

        .badge-final {
            background: #052e16;
            color: #4ade80;
        }

        .empty {
            color: #64748b;
            padding: 20px 0;
        }

        .footer {
            text-align: center;
            color: #475569;
            padding: 40px 0;
            font-size: 12px;
        }

        @media (max-width: 850px) {
            .cards {
                grid-template-columns: repeat(2, 1fr);
            }

            .team-row {
                grid-template-columns: 35px 1fr 90px;
            }

            .projection {
                display: none;
            }
        }

        @media (max-width: 550px) {
            .cards {
                grid-template-columns: 1fr 1fr;
            }

            .header {
                padding: 22px;
            }

            .header h1 {
                font-size: 25px;
            }

            .container {
                padding: 0 12px;
            }
        }
    </style>
</head>

<body>

<div class="header">
    <h1>THE LEAGUE — GUILLOTINE</h1>
    <p>Fantasy Football Elimination League • ESPN League 781990 • 2026</p>
</div>

<div class="container">

    <div class="cards">

        <div class="card">
            <div class="stat-label">Current Week</div>
            <div class="stat-value">{{ week }}</div>
        </div>

        <div class="card">
            <div class="stat-label">Week Status</div>
            <div class="stat-value {% if status == 'LIVE' %}live{% else %}final{% endif %}">
                {{ status }}
            </div>
        </div>

        <div class="card">
            <div class="stat-label">Teams Remaining</div>
            <div class="stat-value">{{ remaining }}</div>
        </div>

        <div class="card">
            <div class="stat-label">Teams Eliminated</div>
            <div class="stat-value">{{ eliminated }}</div>
        </div>

    </div>

<div class="section">

    <div class="section-title">
        <h2>⚠️ Danger Zone</h2>
        <span>Bottom 3 active teams</span>
    </div>

    <div class="card danger">

        {% for team in danger_zone %}

        <div class="team-row">

            <div class="rank">
                {{ loop.index }}
            </div>

            <div class="team-name">
                {{ team.team_name }}
            </div>

            <div class="score">
                Actual: {{ "%.2f"|format(team.score) }}
            </div>

            <div class="projection">
                Projected: {{ "%.2f"|format(team.projected) }}
            </div>

        </div>

        {% endfor %}

    </div>

</div>

    <div class="section">

        <div class="section-title">
            <h2>🔥 Chopping Block</h2>
            <span>Lowest active score</span>
        </div>

        {% if chopping_block %}

                        {% for team in chopping_block %}

            <div class="card chopping">

                <div class="stat-label">
                    Currently in danger
                </div>

                <div class="team-name">
                    {{ team.name }}
                </div>

                <div class="stat-value">
                    Actual: {{ "%.2f"|format(team.score) }}
                </div>

                <div class="projection">
                    Projected: {{ "%.2f"|format(team.projected) }}
                </div>

            </div>

            {% endfor %}

        {% else %}

            <div class="card empty">
                No chopping block information available.
            </div>

        {% endif %}

    </div>


    <div class="section">

        <div class="section-title">
            <h2>📊 Weekly Standings</h2>
            <span>ESPN scores</span>
        </div>

        <div class="card">

            {% if teams %}

                {% for team in teams %}

                <div class="team-row">

                    <div class="rank">
                        {{ loop.index }}
                    </div>

                    <div>
                        <div class="team-name">
                            {{ team.team_name }}
                        </div>

                        <div class="bar">
                            <div
                                class="bar-fill"
                                style="width: {{ team.percent }}%;">
                            </div>
                        </div>
                    </div>

                    <div class="score">
                        {{ "%.2f"|format(team.score) }}
                    </div>

                    <div class="projection">
                        Proj.
                        {{ "%.2f"|format(team.projected) }}
                    </div>

                </div>

                {% endfor %}

            {% else %}

                <div class="empty">
                    No team data available.
                </div>

            {% endif %}

        </div>

    </div>


    <div class="section">

        <div class="section-title">
            <h2>☠️ Eliminated Teams</h2>
            <span>Season history</span>
        </div>

        <div class="card">

            {% if eliminated_teams %}

                {% for team in eliminated_teams %}

                <div class="team-row eliminated">

                    <div class="team-name">
                        {{ team.team_name }}
                    </div>

                    <div>
                        Week {{ team.week }}
                    </div>

                    <div class="score">
                        {{ "%.2f"|format(team.score) }}
                    </div>

                </div>

                {% endfor %}

            {% else %}

                <div class="empty">
                    Nobody has been eliminated yet. 🔥
                </div>

            {% endif %}

        </div>

    </div>


    <div class="footer">
        CHOPPED • ESPN is the source of truth • Read-only dashboard
    </div>

</div>

</body>
</html>
"""


def load_data():

    history = {"eliminated": []}

    if HISTORY_FILE.exists():

        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)


    current_data = {}

    espn_week = get_espn_current_week()

    if espn_week is not None:
        espn_data = get_espn_week_data(espn_week)

        if espn_data:
            current_data = espn_data

    teams = current_data.get("teams", [])


    eliminated_ids = {
        item["team_id"]
        for item in history.get("eliminated", [])
    }


    active_teams = [
        team
        for team in teams
        if team.get("team_id") not in eliminated_ids
    ]


    if current_data.get("status", "LIVE").upper() == "FINAL":
        active_teams.sort(
            key=lambda team: team.get("score", 0),
            reverse=True
        )
    else:
        active_teams.sort(
            key=lambda team: team.get(
                "projected_score",
                team.get("projected", 0)
            ),
            reverse=True
        )


    if current_data.get("status", "LIVE").upper() == "FINAL":
        max_score = max(
            [team.get("score", 0) for team in active_teams],
            default=0
        )
    else:
        max_score = max(
            [
                team.get(
                    "projected_score",
                    team.get("projected", 0)
                )
                for team in active_teams
            ],
            default=0
        )

    if max_score <= 0:
        max_score = 1


    formatted_teams = []

    for team in active_teams:

        score = team.get("score", 0)
        projected = team.get(
            "projected_score",
            team.get("projected", 0)
        )

        percent = max(
            5,
            min(100, (score / max_score) * 100)
        )

        formatted_teams.append({
            "team_name": team.get("team_name", "Unknown"),
            "score": score,
            "projected": projected,
            "percent": percent
        })


    if active_teams:

        if current_data.get("status", "LIVE").upper() == "FINAL":
            lowest_score = min(
                team["score"]
                for team in active_teams
            )

            chopping_block = [
                {
                    "name": team["team_name"],
                    "score": team["score"],
                    "projected": team.get(
                        "projected_score",
                        team.get("projected", 0)
                    )
                }
                for team in active_teams
                if team["score"] == lowest_score
            ]

        else:
            lowest_projected = min(
                team.get(
                    "projected_score",
                    team.get("projected", 0)
                )
                for team in active_teams
            )

            chopping_block = [
                {
                    "name": team["team_name"],
                    "score": team.get("score", 0),
                    "projected": team.get(
                        "projected_score",
                        team.get("projected", 0)
                    )
                }
                for team in active_teams
                if team.get(
                    "projected_score",
                    team.get("projected", 0)
                ) == lowest_projected
            ]


    else:

        chopping_block = []

    if current_data.get("status", "LIVE").upper() == "FINAL":
        danger_zone = sorted(
            active_teams,
            key=lambda team: team.get("score", 0)
        )[:3]
    else:
        danger_zone = sorted(
            active_teams,
            key=lambda team: team.get(
                "projected_score",
                team.get("projected", 0)
            )
        )[:3]

    danger_zone = [
        {
            "team_name": team.get("team_name", "Unknown"),
            "score": team.get("score", 0),
            "projected": team.get(
                "projected_score",
                team.get("projected", 0)
            )
        }
        for team in danger_zone
    ]

    return {
        "week": current_data.get("week", "?"),
        "status": current_data.get("status", "UNKNOWN"),
        "eliminated": len(history.get("eliminated", [])),
        "remaining": len(active_teams),
        "chopping_block": chopping_block,
        "danger_zone": danger_zone,
        "teams": formatted_teams,
        "eliminated_teams": history.get("eliminated", [])
    }


@app.route("/")
def home():

    data = load_data()

    return render_template_string(
        HTML,
        **data
    )


if __name__ == "__main__":

    app.run(
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 5000)),
    debug=False
)