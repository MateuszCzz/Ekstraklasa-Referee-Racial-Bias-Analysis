import time
from pathlib import Path
from parser import parse_search_results, parse_player_page
from storage import load_csv, save_csv

PAGE_LOAD_WAIT  = 2.0   # after initial page load
CLICK_WAIT      = 2.5   # after clicking nav toggle or matchday

PARTIAL_FIELDNAMES = ["id", "tm_id", "tm_string", "name", "team", "is_duplicate", "full_name"]

def _build_search_url(url: str, player_name: str, player_team: str) -> str:
    query = f"{player_name} {player_team} profil"
    query = query.replace(".", "").replace(" ", "+")
    return f"{url}+{query}+&ia=web"

def _build_player_url(tm_string: str, tm_id: str) -> str:
    return f"https://www.transfermarkt.com/{tm_string}/profil/spieler/{tm_id}"

def enrich_player_data(driver, url: str, test_mode:bool, players: list[dict], partial_result_path: Path) -> list[dict]:
    # if its only a test run limit to 3 rows
    if test_mode:
        total = len(players)
        players = players[:3]
        print(f"[TEST MODE] Running on {len(players)} of {total} players")

    # check if cached results exist
    if partial_result_path.exists():
        # filter out duplicated players from final result
        result = [row for row in load_csv(partial_result_path) if row["is_duplicate"] != "True"]
        done_id_map = {row["id"] for row in result} # map to skip done players  
        done_tm_id_map = {row["tm_id"] for row in result} # map to skip duplicated players
        print(f"Loaded {len(result)} cached players from {partial_result_path}")
    else:
        result = []
        done_id_map = set()
        done_tm_id_map = set()
        print(f"Player cached file not found at {partial_result_path}, skipping.")
        
    # iter over players
    for i, player in enumerate(players):
        player_id = player["id"]
        player_name = player["name"]
        player_team = player["team"]

        # skip if already done
        if player_id in done_id_map:
            print(f"[SKIP] [{i+1}/{len(players)}] id={player_id}  {player_name}  |  {player_team}")
            continue

        # build url
        player_search_query = _build_search_url(url, player_name, player_team)

        # search for player in duckduckgo
        driver.get(player_search_query)
        time.sleep(PAGE_LOAD_WAIT)

        # parse out both id and name string
        player_tm_id, player_tm_string = parse_search_results(driver)

        # ask user for id if its missing
        if not player_tm_id:
            print(f"[query error] No transfermarkt id found for {player_search_query}")
            player_tm_id = input(f"  Enter transfermarkt ID for '{player_name}' ({player_team}), or skip: \n").strip()
            if not player_tm_id:
                print(f"  [SKIP] Skipping {player_name}")
                continue

        # ask user for name string if its missing
        if not player_tm_string:
            print(f"[query error] No transfermarkt name string found for {player_search_query}")
            player_tm_string = input(f"  Enter transfermarkt name for '{player_name}' (e.g. 'lionel-messi'), or skip: \n").strip()
            if not player_tm_string:
                print(f"  [SKIP] Skipping {player_name}")
                continue

        # check if given name corresponds to already calculated transfermarkt 
        player_is_duplicate = player_tm_id in done_tm_id_map

        # prep data output
        row = {
            "id":           player_id,
            "tm_id":        player_tm_id,
            "tm_string":    player_tm_string,
            "name":         player_name,
            "team":         player_team,
            "is_duplicate": player_is_duplicate,
            "full_name":    "",
        }

        # if not already scraped
        if not player_is_duplicate:
            # prep right transfermarkt url
            driver.get(_build_player_url(player_tm_string, player_tm_id))
            time.sleep(PAGE_LOAD_WAIT)

            # scrap transfermarkt for new data and update
            row.update(parse_player_page(driver))
            
            # append to final results
            result.append(row)
            done_tm_id_map.add(player_tm_id)

        # save to cache
        save_csv(partial_result_path, [row], PARTIAL_FIELDNAMES,"a")
        print(f"[DONE] [{i+1}/{len(players)}] id={player_id}  {player_name}  |  {player_team} | dup:{player_is_duplicate}")
    return result
