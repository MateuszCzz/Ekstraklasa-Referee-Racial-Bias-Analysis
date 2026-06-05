"""
test_results.py - Full test suite for matchdays.json produced by the optascraper.

"""

import json
import pytest
from pathlib import Path

DATA_DIR = Path("data/optascraper/result")

EXPECTED_MATCHDAYS      = 34
EXPECTED_TEAMS          = 18
FULL_MATCHDAY_SIZE      = 9
TOTAL_MATCHES           = FULL_MATCHDAY_SIZE * EXPECTED_MATCHDAYS

REQUIRED_MATCH_KEYS = {
    "match_id", "matchday",
    "home_team", "away_team",
    "home_goals", "away_goals", "result",
    "home_stats", "away_stats",
    "match_timeline",
}
VALID_RESULTS     = {"W", "L", "D"}

VALID_EVENT_TYPES = {
    "goal", "own_goal", "penalty_scored", "missed_penalty",
    "yellow", "second_yellow", "red",
    "substitution",
}
GOAL_EVENTS = {"goal", "own_goal", "penalty_scored"}
REQUIRED_TIMELINE_KEYS = {"minute", "event_type", "player", "is_home_team", "is_first_half"}

@pytest.fixture(scope="session")
def matchdays_json():
    path = DATA_DIR / "matchdays.json"
    if not path.exists():
        pytest.skip(f"matchdays.json not found at {path} – run the scraper first")
    return json.loads(path.read_text(encoding="utf-8"))

@pytest.fixture(scope="session")
def all_matches(matchdays_json):
    return [
        (season, md_name, match_id, match)
        for season, matchdays in matchdays_json.items()
        for md_name, matches in matchdays.items()
        for match_id, match in matches.items()
    ]

@pytest.fixture(scope="session")
def all_events(all_matches):
    return [
        (season, md_name, match_id, ev)
        for season, md_name, match_id, match in all_matches
        for ev in match.get("match_timeline", [])
    ]

class TestDataTotals:
    def test_matchday_count(self, matchdays_json):
        """Season contains exactly 34 matchdays"""
        bad = [
            f"{season}: got {len(matchdays)} matchdays"
            for season, matchdays in matchdays_json.items()
            if len(matchdays) != EXPECTED_MATCHDAYS
        ]
        assert not bad, "\n".join(bad)

    def test_total_matches(self, matchdays_json):
        """Total match count equals 306"""
        bad = [
            f"{season}: got {sum(len(md) for md in matchdays.values())} matches"
            for season, matchdays in matchdays_json.items()
            if sum(len(md) for md in matchdays.values()) != TOTAL_MATCHES
        ]
        assert not bad, "\n".join(bad)

    def test_matches_per_full_matchday(self, matchdays_json):
        """Every matchday has exactly 9 matches"""
        bad = {
            f"{season}/{name}": len(md)
            for season, matchdays in matchdays_json.items()
            for name, md in matchdays.items()
            if len(md) != FULL_MATCHDAY_SIZE
        }
        assert not bad, f"Unexpected match counts: {bad}"

    def test_unique_team_count(self, matchdays_json):
        """Exactly 18 unique teams appear across the season"""
        bad = []
        for season, matchdays in matchdays_json.items():
            teams = {
                team
                for md in matchdays.values()
                for match in md.values()
                for team in (match.get("home_team"), match.get("away_team"))
                if team
            }
            if len(teams) != EXPECTED_TEAMS:
                bad.append(f"{season}: got {len(teams)} teams")
        assert not bad, "\n".join(bad)


class TestMatchStructure:
    def test_required_keys_present(self, all_matches):
        """Every match contains all required keys"""
        bad = [
            f"{md}/{mid}: missing {REQUIRED_MATCH_KEYS - match.keys()}"
            for md, mid, match in all_matches
            if REQUIRED_MATCH_KEYS - match.keys()
        ]
        assert not bad, "Matches missing keys:\n" + "\n".join(bad)

    def test_matchday_field_matches(self, all_matches):
        """matchday field must equal the parent matchday"""
        bad = [
            f"{md}/{mid}: matchday field={match.get('matchday')!r}"
            for md, mid, match in all_matches
            if match.get("matchday") != md
        ]
        assert not bad, "matchday field / parent key mismatches:\n" + "\n".join(bad)

    def test_result_values_valid(self, all_matches):
        """result must be 'W', 'L', or 'D'"""
        bad = [
            f"{md}/{mid}: result={match.get('result')!r}"
            for md, mid, match in all_matches
            if match.get("result") not in VALID_RESULTS
        ]
        assert not bad, "Invalid results:\n" + "\n".join(bad)

    def test_goals_are_non_negative_integers(self, all_matches):
        """home_goals and away_goals must be non-negative numbers"""
        bad = []
        for md, mid, match in all_matches:
            for key in ("home_goals", "away_goals"):
                v = match.get(key)
                if not isinstance(v, int) or v < 0:
                    bad.append(f"{md}/{mid} {key}={v!r}")
        assert not bad, "Invalid goal values:\n" + "\n".join(bad)

    def test_result_consistent_with_goals(self, all_matches):
        """W/L/D result must be consistent with goals"""
        bad = []
        for md, mid, match in all_matches:
            hg, ag, r = match.get("home_goals", 0), match.get("away_goals", 0), match.get("result")
            expected = "W" if hg > ag else ("L" if hg < ag else "D")
            if r != expected:
                bad.append(f"{md}/{mid}: {hg}-{ag} result={r!r} (expected {expected!r})")
        assert not bad, "Inconsistent results:\n" + "\n".join(bad)

    def test_team_names_non_empty(self, all_matches):
        """home_team and away_team must be non-empty strings"""
        bad = [
            f"{md}/{mid}: {key}"
            for md, mid, match in all_matches
            for key in ("home_team", "away_team")
            if not match.get(key)
        ]
        assert not bad, "Empty team names:\n" + "\n".join(bad)

    def test_home_and_away_teams_differ(self, all_matches):
        """home_team and away_team must be diffrent"""
        bad = [
            f"{md}/{mid}"
            for md, mid, match in all_matches
            if match.get("home_team") == match.get("away_team")
        ]
        assert not bad, "Matches with identical home/away teams:\n" + "\n".join(bad)

    def test_teams_have_at_least_11_players(self, all_matches):
        """Both home and away teams must list at least 11 players"""
        bad = []
        for md, mid, match in all_matches:
            for side, key in (("home", "home_stats"), ("away", "away_stats")):
                players = [
                    p for p in match.get(key, [])
                    if p.get("player") != "Total"
                ]
                if len(players) < 11:
                    bad.append(
                        f"{md}/{mid} {side}: only {len(players)} player(s) "
                        f"({match.get(side + '_team')})"
                    )
        assert not bad, "Teams with fewer than 11 players:\n" + "\n".join(bad)

class TestTimelineStructure:
    def test_event_types_valid(self, all_events):
        """Every timeline event must have a event_type"""
        bad = [
            f"{md}/{mid}: {ev.get('event_type')!r}"
            for md, mid, ev in all_events
            if ev.get("event_type") not in VALID_EVENT_TYPES
        ]
        assert not bad, "Unknown event types:\n" + "\n".join(bad)

    def test_required_event_keys_present(self, all_events):
        """Every event must contain required keys"""
        bad = [
            f"{md}/{mid}: {ev.get('event_type')} missing {REQUIRED_TIMELINE_KEYS - ev.keys()}"
            for md, mid, ev in all_events
            if REQUIRED_TIMELINE_KEYS - ev.keys()
        ]
        assert not bad, "Events with missing keys:\n" + "\n".join(bad)

    def test_event_minute_is_positive_integer(self, all_events):
        """Event minutes must be positive number"""
        bad = [
            f"{md}/{mid}: minute={ev.get('minute')!r}"
            for md, mid, ev in all_events
            if not isinstance(ev.get("minute"), int) or ev["minute"] <= 0
        ]
        assert not bad, "Events with invalid minute:\n" + "\n".join(bad)

    def test_event_player_present(self, all_events):
        """Every event must have a player name"""
        bad = [
            f"{md}/{mid}: {ev.get('event_type')} at {ev.get('minute')} has no player"
            for md, mid, ev in all_events
            if not ev.get("player")
        ]
        assert not bad, "Events missing player:\n" + "\n".join(bad)

    def test_substitution_has_second_player(self, all_events):
        """substitution events must have a second player name"""
        bad = [
            f"{md}/{mid}: substitution at {ev.get('minute')} — second_player={ev.get('second_player')!r}"
            for md, mid, ev in all_events
            if ev.get("event_type") == "substitution" and not ev.get("second_player")
        ]
        assert not bad, "Substitutions missing second player:\n" + "\n".join(bad)

    def test_goal_count_matches_score(self, all_matches):
        """Sum of goal-type timeline events per team must equal the match score"""
        bad = []
        for md_name, match_id, m in all_matches:
            home_tl = sum(
                1 for ev in m.get("match_timeline", [])
                if ev["event_type"] in GOAL_EVENTS and ev["is_home_team"]
            )
            away_tl = sum(
                1 for ev in m.get("match_timeline", [])
                if ev["event_type"] in GOAL_EVENTS and not ev["is_home_team"]
            )
            if home_tl != m["home_goals"] or away_tl != m["away_goals"]:
                bad.append(
                    f"{md_name}/{match_id}: "
                    f"timeline home={home_tl} score={m['home_goals']} | "
                    f"timeline away={away_tl} score={m['away_goals']} "
                    f"({m['home_team']} vs {m['away_team']})"
                )
        assert not bad, "Goal count mismatches:\n" + "\n".join(bad)
