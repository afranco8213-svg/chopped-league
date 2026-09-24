#!/usr/bin/env python3
"""
Extract full ESPN fantasy football league history to CSV.

Usage:
    pip install espn_api
    python espn_league_history.py                     # public league
    python espn_league_history.py --espn-s2 "..." --swid "{...}"   # private league

Cookies (private leagues only): log into fantasy.espn.com, open dev tools ->
Application -> Cookies -> fantasy.espn.com, copy the values of `espn_s2` and
`SWID` (SWID includes the curly braces).

Output: a folder `league_781990_history/` with per-season CSVs:
    standings_<year>.csv, matchups_<year>.csv, draft_<year>.csv
plus an all-years combined file for each.
"""

import argparse
import csv
import os
import sys

from espn_api.football import League
from espn_api.requests.espn_requests import ESPNAccessDenied, ESPNInvalidLeague

LEAGUE_ID = 781990
FIRST_YEAR = 2018   # espn_api is reliable from ~2018 onward
LAST_YEAR = 2026    # current season; incomplete data is fine


def write_csv(path, rows, fieldnames):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {path} ({len(rows)} rows)")


def season_standings(league, year):
    rows = []
    for rank, team in enumerate(league.standings(), start=1):
        rows.append({
            "year": year,
            "final_rank": rank,
            "team": team.team_name,
            "owners": "; ".join(
                (o.get("firstName", "") + " " + o.get("lastName", "")).strip()
                if isinstance(o, dict) else str(o)
                for o in (team.owners or [])
            ),
            "wins": team.wins,
            "losses": team.losses,
            "ties": team.ties,
            "points_for": round(team.points_for, 2),
            "points_against": round(team.points_against, 2),
        })
    return rows


def season_matchups(league, year):
    rows = []
    # regular season + playoffs; scoreboard() covers played weeks
    total_weeks = getattr(league.settings, "reg_season_count", 14) + 3
    for week in range(1, total_weeks + 1):
        try:
            games = league.scoreboard(week)
        except Exception:
            break
        for g in games:
            home = getattr(g, "home_team", None)
            away = getattr(g, "away_team", None)
            if home is None or away is None:
                continue  # bye week
            if g.home_score == 0 and g.away_score == 0:
                continue  # unplayed
            rows.append({
                "year": year,
                "week": week,
                "home_team": home.team_name,
                "home_score": g.home_score,
                "away_team": away.team_name,
                "away_score": g.away_score,
                "playoff": getattr(g, "is_playoff", False),
            })
    return rows


def season_draft(league, year):
    rows = []
    for pick in league.draft:
        rows.append({
            "year": year,
            "round": pick.round_num,
            "pick": pick.round_pick,
            "team": pick.team.team_name if pick.team else "",
            "player": pick.playerName,
            "keeper": getattr(pick, "keeper_status", False),
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--espn-s2", default=os.environ.get("ESPN_S2"))
    ap.add_argument("--swid", default=os.environ.get("SWID"))
    ap.add_argument("--first-year", type=int, default=FIRST_YEAR)
    ap.add_argument("--last-year", type=int, default=LAST_YEAR)
    args = ap.parse_args()

    outdir = f"league_{LEAGUE_ID}_history"
    os.makedirs(outdir, exist_ok=True)

    all_standings, all_matchups, all_draft = [], [], []

    for year in range(args.first_year, args.last_year + 1):
        print(f"\n=== {year} ===")
        try:
            league = League(
                league_id=LEAGUE_ID, year=year,
                espn_s2=args.espn_s2, swid=args.swid,
            )
        except ESPNAccessDenied:
            print("  access denied — private league. Re-run with --espn-s2 and --swid.")
            sys.exit(1)
        except ESPNInvalidLeague:
            print("  no data for this year, skipping.")
            continue
        except Exception as e:
            print(f"  failed ({e}), skipping.")
            continue

        s = season_standings(league, year)
        m = season_matchups(league, year)
        d = season_draft(league, year)

        write_csv(os.path.join(outdir, f"standings_{year}.csv"), s, list(s[0]) if s else [])
        write_csv(os.path.join(outdir, f"matchups_{year}.csv"), m, list(m[0]) if m else [])
        write_csv(os.path.join(outdir, f"draft_{year}.csv"), d, list(d[0]) if d else [])

        all_standings += s
        all_matchups += m
        all_draft += d

    print("\n=== combined ===")
    if all_standings:
        write_csv(os.path.join(outdir, "all_standings.csv"), all_standings, list(all_standings[0]))
    if all_matchups:
        write_csv(os.path.join(outdir, "all_matchups.csv"), all_matchups, list(all_matchups[0]))
    if all_draft:
        write_csv(os.path.join(outdir, "all_draft.csv"), all_draft, list(all_draft[0]))

    print(f"\nDone. Everything is in ./{outdir}/")


if __name__ == "__main__":
    main()
