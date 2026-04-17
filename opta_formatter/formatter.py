import pandas as pd

DATA_START_DATE = "2023-01-01"
DATA_END_DATE   = "2024-12-12"
EVENT_TYPES: list[str] = [ "goal", "substitution", "yellow", "red", "second_yellow", "missed_penalty", "penalty_scored", "own_goal" ]

# schema missing:
# dimMatch:
# id int PK
# date (FK dimDate date)
# home_team_key (FK dimTeam name)
# away_team_key (FK dimTeam name)
# referee_key (FK dimReferee id int FK)
# venue_key (FK dimVenue name)
# matchday_nr 
# attendance 
# home_score 
# away_score 
# result

# factPlayerMatchStats:
# id int PK
# player_key id int FK
# match_key id int FK
# isHomeTeam bool
# goals
# assists
# red_cards
# yellow_cards
# corners_won
# shots
# shots_on_target
# blocked_shots
# passes
# crosses
# tackles
# offsides
# fouls_conceded
# fouls_won
# saves

# factMatchTimeline:
# timeline_key       id int PK
# match_key id int FK
# minute          (int)
# event_type_key  dimEventType name
# player_key      id int FK
# second_player_key id int FK nullable, sub on, or assist on goal
# isHomeTeam bool
# isFirstHalf    

def _iter_matches(matchdays: dict):
    """Yield every match dict regardless of matchday nesting."""
    for matchday_matches in matchdays.values():
        yield from matchday_matches.values()

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

def build_tables(matchdays: dict) -> dict[str, pd.DataFrame]:
    matches = list(_iter_matches(matchdays))

    # iter over all matches collecting players, enumerating and differentiating by team
    # results in 2 types of data problem:
    # - dublication by team ie. Mosór played for both Piast and Raków
    # - dublication due to surce inconsistency R. Gikiewicz / Rafał Tadeusz Gikiewicz are the same person
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
    }