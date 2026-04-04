import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from parser import parse_match
from storage import save_partial_match, load_done_matches, is_match_done, mark_match_done

PAGE_LOAD_WAIT  = 1.0   # after initial page load
CLICK_WAIT      = 0.5   # after clicking nav toggle or matchday
MATCH_PAGE_WAIT = 3.0   # after navigating into a match

NAV_TOGGLE_XPATH      = "//div[@class='Opta-Nav']//h3[contains(@class,'Opta-Exp')]"
NAV_TOGGLE_OPEN_XPATH = "//div[@class='Opta-Nav']//h3[contains(@class,'Opta-Exp') and contains(@class,'Opta-Open')]"
MATCHDAY_LIST_XPATH   = "//ul[@class='Opta-Cf']"
MATCHDAY_ITEMS_XPATH  = "//ul[@class='Opta-Cf']//li/a"
MATCH_ROWS_XPATH      = "//tbody[contains(@class,'Opta-fixture')]"
MATCH_DIVIDER_XPATH   = ".//td[@class='Opta-Divider Opta-Dash']"

def _navbar_control(driver, click_name: str | None = None) -> list:
    """Open navbar if needed, click element and return matchday list."""

    if not driver.find_elements(By.XPATH, NAV_TOGGLE_OPEN_XPATH):
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, NAV_TOGGLE_XPATH))).click()
        time.sleep(CLICK_WAIT)

    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, MATCHDAY_LIST_XPATH)))
    matchday_list = driver.find_elements(By.XPATH, MATCHDAY_ITEMS_XPATH)

    if click_name:
        for link in matchday_list:
            if link.text.strip() == click_name:
                link.click()
                time.sleep(CLICK_WAIT)
                return matchday_list
        print(f"  Matchday '{click_name}' not found in nav list")

    return matchday_list

def _scrape_matchday(driver, matchday_name: str) -> dict:
    """For each match in the current matchday: click, parse, go back."""
    match_ids = [
        mid for row in driver.find_elements(By.XPATH, MATCH_ROWS_XPATH)
        if row.is_displayed() and (mid := row.get_attribute("data-match"))
    ]

def _scrape_matchday(driver, matchday_name: str, done_registry: dict, base_url: str) -> dict:
    """For each match in the current matchday: click, parse, go back."""
    match_ids = _get_match_ids(driver, matchday_name, base_url)

    if not match_ids:
        print(f"  [{matchday_name}] No match rows found skipping")
        return {}

    print(f"  [{matchday_name}] Found {len(match_ids)} matches")
    results = {}

    for match_id in match_ids:
        try:
            row = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//tbody[@data-match='{match_id}']")
                )
            )
            row.find_element(By.XPATH, MATCH_DIVIDER_XPATH).click()
            time.sleep(MATCH_PAGE_WAIT)

            parsed = parse_match(driver)
            match_data = {"match_id": match_id, "matchday": matchday_name, **parsed}

            if is_match_done(match_data, done_registry):
                print(f"    [{matchday_name}] Match {match_id} - already done, skipping")
                driver.back()
                time.sleep(CLICK_WAIT)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, MATCH_ROWS_XPATH))
                )
                continue

            results[match_id] = match_data
            print(f"    [{matchday_name}] Match {match_id} - {parsed.get('home_team')} vs {parsed.get('away_team')}")

            saved_path = save_partial_match(matchday_name, match_data)
            print(f"    [{matchday_name}] Saved partial {saved_path}")

            mark_match_done(match_data, done_registry)

            # Navigate back
            driver.back()
            time.sleep(CLICK_WAIT)

            # Wait for match list to reappear
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, MATCH_ROWS_XPATH))
            )

        except Exception as e:
            print(f"    [{matchday_name}] Match {match_id} — error: {e}")

    return results

def scrape_all_matchdays(driver, url: str) -> dict:
    done_registry = load_done_matches()

    print(f"Loading: {url}")
    driver.get(url)
    time.sleep(PAGE_LOAD_WAIT)

    matchday_names = [x.text.strip() for x in _navbar_control(driver) if x.text.strip()]

    if not matchday_names:
        print("No matchdays found - check NAV_TOGGLE_XPATH / MATCHDAY_ITEMS_XPATH")
        return {}

    all_results = {}

    for name in matchday_names:
        print(f"\n[{name}] Selecting...")
        _navbar_control(driver, click_name=name)
        all_results[name] = _scrape_matchday(driver, name, done_registry, url)
        print(f"  [{name}] Done — {len(all_results[name])} matches saved")


    return all_results
