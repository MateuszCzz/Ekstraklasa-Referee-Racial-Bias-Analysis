import pandas as pd

DATA_START_DATE = "2023-01-01"
DATA_END_DATE   = "2024-12-12"

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

# dimReferee:
# id int PK
# name

# dimVenue:
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

# dimEventType:
# name: (goal,subbstitution,yellow,red,secondyellow,missed penalty,penaltyscored)

# factMatchTimeline:
# timeline_key       id int PK
# match_key id int FK
# minute          (int)
# event_type_key  dimEventType name
# player_key      id int FK
# second_player_key id int FK nullable, sub on, or assist on goal
# isHomeTeam bool
# isFirstHalf    

def build_dim_date() -> pd.DataFrame:
    return pd.DataFrame({"date": pd.date_range(DATA_START_DATE, DATA_END_DATE, freq="D")})

def build_tables(matchdays: dict) -> dict[str, pd.DataFrame]:
    return {
        "dimDate":              build_dim_date(),
    }