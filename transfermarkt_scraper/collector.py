import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

PAGE_LOAD_WAIT  = 2.0   # after initial page load
CLICK_WAIT      = 2.5   # after clicking nav toggle or matchday
def enrich_player_data(driver, url: str, test_mode:bool, players: list[dict], url_cached: list[dict] | None,) -> list[dict]:
    result: list[dict] = []

    # if its only a test run limit to 3 rows
    if test_mode:
        total = len(players)
        players = players[:3]
        print(f"[TEST MODE] Running on {len(players)} of {total} players")

    # iter over players
    for i, player in enumerate(players):
        player_id = player["id"]
        player_name = player["name"]
        player_team = player["team"]

        print(f"\n[{i+1}/{len(players)}] id={player_id}  {player_name}  |  {player_team}")

        # 1. go web search
        # 2. check url map
        # A3. pass page to parser
        # A4. save in cache
        # 5. save partial
    return result
