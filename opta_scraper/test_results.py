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

@pytest.fixture(scope="session")
def matchdays_json():
    path = DATA_DIR / "matchdays.json"
    if not path.exists():
        pytest.skip(f"matchdays.json not found at {path} – run the scraper first")
    return json.loads(path.read_text(encoding="utf-8"))

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
