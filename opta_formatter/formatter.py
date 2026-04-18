import pandas as pd

DATA_START_DATE = "2023-01-01"
DATA_END_DATE   = "2024-12-12"
EVENT_TYPES: list[str] = [ "goal", "substitution", "yellow", "red", "second_yellow", "missed_penalty", "penalty_scored", "own_goal" ]
STAT_COLS: list[str] = [
    "goals", "assists", "red_cards", "yellow_cards", "corners_won",
    "shots", "shots_on_target", "blocked_shots", "passes", "crosses",
    "tackles", "offsides", "fouls_conceded", "fouls_won", "saves",
]

def _iter_matches(matchdays: dict):
    """Yield every match dict"""
    for matchday_matches in matchdays.values():
        yield from matchday_matches.values()

def _get_nr_from_matchday(label: str) -> int | None:
    parts = label.split()
    return int(parts[-1]) if parts and parts[-1].isdigit() else None

def _parse_attendance(value: str) -> int:
    try:
        return int(value.replace(",", ""))
    except (ValueError, AttributeError):
        print(f"Could not parse attendance: {value!r}, defaulting to 0")
        return 0
    
def build_dim_date() -> pd.DataFrame:
    return pd.DataFrame({"date": pd.date_range(DATA_START_DATE, DATA_END_DATE, freq="D")})

def build_dim_event_type() -> pd.DataFrame:
    return pd.DataFrame({"name": EVENT_TYPES})

def build_dim_referee(matches: list[dict]) -> pd.DataFrame:
    refs = sorted({m["referee"] for m in matches})
    return pd.DataFrame({"id": range(1, len(refs) + 1), "name": refs})

def build_dim_venue(matches: list[dict]) -> pd.DataFrame:
    rows = sorted({(m["venue"], m["home_team"]) for m in matches})
    return pd.DataFrame(rows, columns=["name", "home_team"])

def build_dim_team(matches: list[dict]) -> pd.DataFrame:
    teams = sorted({m["home_team"] for m in matches} | {m["away_team"] for m in matches})
    return pd.DataFrame({"name": teams})

def build_dim_player(matches: list[dict]) -> pd.DataFrame:
    players = sorted({
        (r["player"], team)
        for m in matches
        for team, side in ((m["home_team"], "home_stats"), (m["away_team"], "away_stats"))
        for r in m[side]
        if r["player"] != "Total"
    })
    return pd.DataFrame(
        [{"id": i, "name": name, "team": team} for i, (name, team) in enumerate(players, start=1)]
    )

def build_dim_match(matches: list[dict]) -> pd.DataFrame:
    rows = [
        {
            "match_id": i,
            "source_match_id": m["match_id"],
            "date": pd.to_datetime(m["date"], format="%d %B %Y %H:%M"),
            "home_team": m["home_team"],
            "away_team": m["away_team"],
            "referee": m["referee"],
            "venue": m["venue"],
            "matchday_nr": _get_nr_from_matchday(m["matchday"]),
            # in case of data with no attendance default to 0 fix in power bi etl
            "attendance": _parse_attendance(m.get("attendance", "")),
            "home_score": m["home_goals"],
            "away_score": m["away_goals"],
            "result": m["result"],
        }
        for i, m in enumerate(matches, start=1)
    ]
    return pd.DataFrame(rows)

def build_fact_player_stats(matches: list[dict]) -> pd.DataFrame:
    rows = []
    for sid, (m, is_home, row) in enumerate(
        (
            (m, is_home, row)
            for m in matches
            for is_home, side in [(True, "home_stats"), (False, "away_stats")]
            for row in m[side]
            if row["player"] != "Total"
        ),
        start=1,
    ):
        rows.append({
            "id": sid,
            "player": row["player"],
            "team": m["home_team"] if is_home else m["away_team"],
            "source_match_id": m["match_id"],
            "is_home_team": is_home,
            **{col: int(row[col]) for col in STAT_COLS},
        })
    return pd.DataFrame(rows)

def build_fact_timeline(matches: list[dict]) -> pd.DataFrame:
    rows = []
    for tid, (m, event) in enumerate(
        ((m, event) for m in matches for event in m["match_timeline"]),
        start=1,
    ):
        team = m["home_team"] if event["is_home_team"] else m["away_team"]
        rows.append({
            "id": tid,
            "source_match_id": m["match_id"],
            "minute": event["minute"],
            "event_type": event["event_type"],
            "player": event["player"],
            "team": team,
            "second_player": event.get("second_player"),
            "is_home_team": event["is_home_team"],
            "is_first_half": event["is_first_half"],
        })
    return pd.DataFrame(rows)

def build_tables(matchdays: dict) -> dict[str, pd.DataFrame]:
    matches = list(_iter_matches(matchdays))

    # iter over all matches collecting players, enumerating and differentiating by team
    # results in 2 types of data problem:
    # - dublication by team ie. Mosór played for both Piast and Raków
    # - dublication due to source inconsistency R. Gikiewicz / Rafał Tadeusz Gikiewicz are the same person
    # first is required to the lower chance of records being squashed due to players with same name playing in the league. Chance of 2 players with same name is high, chance of both of them playing for same team is relatively minimal
    # chance of above happening is increased due to source using short for first names
    # both problems have to be solved in data enrichment stage later
    player_df = build_dim_player(matches)

    return {
        "dimDate":              build_dim_date(),
        "dimEventType":         build_dim_event_type(),
        "dimReferee":           build_dim_referee(matches),
        "dimVenue":             build_dim_venue(matches),
        "dimTeam":              build_dim_team(matches),
        "dimPlayer":            player_df,
        "dimMatch":             build_dim_match(matches),
        "factPlayerMatchStats": build_fact_player_stats(matches),
        "factMatchTimeline":    build_fact_timeline(matches),
    }