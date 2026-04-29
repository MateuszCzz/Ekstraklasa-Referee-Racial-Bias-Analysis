import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from parser import parse_search_results

PAGE_LOAD_WAIT  = 2.0   # after initial page load
CLICK_WAIT      = 2.5   # after clicking nav toggle or matchday

def build_search_url(url: str, player_name: str, player_team: str) -> str:
    query = f"{player_name} {player_team}"
    query = query.replace(".", "").replace(" ", "+")
    return f"{url}+{query}+&ia=web"

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

        # build url
        player_search_query = build_search_url(url, player_name, player_team)

        # search for player in duckduckgo
        driver.get(player_search_query)
        time.sleep(PAGE_LOAD_WAIT)

        if not (player_tm_id := parse_search_results(driver)):
            print(f"[query error] No transfermarkt id found for  {player_search_query}")
            continue
        print(player_tm_id)
        # 2. check url map
        # A3. pass page to parser
        # A4. save in cache
        # 5. save partial
    return result
