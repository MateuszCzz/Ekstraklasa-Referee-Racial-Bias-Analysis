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

@pytest.fixture(scope="session")
def matchdays_json():
    path = DATA_DIR / "matchdays.json"
    if not path.exists():
        pytest.skip(f"matchdays.json not found at {path} – run the scraper first")
    return json.loads(path.read_text(encoding="utf-8"))

@pytest.fixture(scope="session")
def all_matches(matchdays_json):
    return [
        (md_name, match_id, match)
        for md_name, matches in matchdays_json.items()
        for match_id, match in matches.items()
    ]

class TestDataTotals:
    def test_matchday_count(self, matchdays_json):
        """Season contains exactly 34 matchdays"""
        assert len(matchdays_json) == EXPECTED_MATCHDAYS

    def test_total_matches(self, matchdays_json):
        """Total match count equals 306"""
        total = sum(len(md) for md in matchdays_json.values())
        assert total == TOTAL_MATCHES

    def test_matches_per_full_matchday(self, matchdays_json):
        """Every matchday has exactly 9 matches"""
        bad = {
            name: len(md)
            for name, md in matchdays_json.items()
            if len(md) != FULL_MATCHDAY_SIZE
        }
        assert not bad, f"Unexpected match counts: {bad}"

    def test_unique_team_count(self, matchdays_json):
        """Exactly 18 unique teams appear across the season"""
        teams = {
            team
            for md in matchdays_json.values()
            for match in md.values()
            for team in (match.get("home_team"), match.get("away_team"))
            if team
        }
        assert len(teams) == EXPECTED_TEAMS

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

