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

# dimTeam:
# name

# dimPlayer:
# id int PK
# name

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

def build_tables(matchdays: dict) -> dict[str, pd.DataFrame]:
    matches = list(_iter_matches(matchdays))

    return {
        "dimDate":              build_dim_date(),
        "dimEventType":         build_dim_event_type(),
        "dimReferee":           build_dim_referee(matches),
        "dimVenue":             build_dim_venue(matches),
    }