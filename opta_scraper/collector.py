import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from parser import parse_match
from storage import save_partial_match, is_match_done, load_partial_match

PAGE_LOAD_WAIT  = 2.0   # after initial page load
CLICK_WAIT      = 2.5   # after clicking nav toggle or matchday
MATCH_PAGE_WAIT = 4.0   # after navigating into a match

MIN_MATCHES_PER_ROUND = 9   # expected amount of matches per round; for extraklasa its 9
RETRY_WAIT            = 10  # wait time after hard error
MAX_RETRIES           = 3   # how many times to retry before giving up

NAV_TOGGLE_XPATH      = "//div[@class='Opta-Nav']//h3[contains(@class,'Opta-Exp')]"
NAV_TOGGLE_OPEN_XPATH = "//div[@class='Opta-Nav']//h3[contains(@class,'Opta-Exp') and contains(@class,'Opta-Open')]"
MATCHDAY_LIST_XPATH   = "//ul[@class='Opta-Cf']"
MATCHDAY_ITEMS_XPATH  = "//ul[@class='Opta-Cf']//li/a"
MATCH_ROWS_XPATH      = "//tbody[contains(@class,'Opta-fixture')]"
MATCH_DIVIDER_XPATH   = ".//td[@class='Opta-Divider Opta-Dash']"
HOME_TEAM_XPATH       = ".//td[contains(@class,'Opta-Home')]"
COOKIES_DENY_BUTTON_XPATH = "//*[@id='deny']"

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

def _deny_cookie_banner(driver):
    try:
        # Wait for div with shadow dom
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "usercentrics-cmp-ui"))
        )
        
        # find shadow DOM, click deny
        driver.execute_script("""
            const host = document.getElementById('usercentrics-cmp-ui');
            const shadowRoot = host.shadowRoot;
            const denyBtn = shadowRoot.getElementById('deny');
            if (denyBtn) denyBtn.click();
        """)
        
        # Wait for banner to disappear
        WebDriverWait(driver, 5).until(
            EC.invisibility_of_element_located((By.ID, "usercentrics-cmp-ui"))
        )
        
    except Exception:
        pass  # no banner, continue normally

def _read_matches(driver) -> list[tuple[str, str]]:
    matches = []
    for row in driver.find_elements(By.XPATH, MATCH_ROWS_XPATH):
        if not row.is_displayed():
            continue
        match_id = row.get_attribute("data-match")
        if not match_id:
            continue
        try:
            home_team = row.find_element(By.XPATH, HOME_TEAM_XPATH).text.strip()
        except Exception:
            home_team = ""
        matches.append((match_id, home_team))
    return matches


def _check_matches(driver, matchday_name: str, base_url: str) -> list:
    matches = _read_matches(driver)
    if len(matches) >= MIN_MATCHES_PER_ROUND:
        return matches

    for attempt in range(1, MAX_RETRIES + 1):
        print(
            f"  [{matchday_name}] Only {len(matches)} match(es) detected "
            f"(expected ≥{MIN_MATCHES_PER_ROUND}), attempt {attempt}/{MAX_RETRIES} "
            f"waiting {RETRY_WAIT}s then reloading..."
        )
        time.sleep(RETRY_WAIT)

        # error: not enough matches go full reload
        driver.get(base_url)
        time.sleep(PAGE_LOAD_WAIT)
        _navbar_control(driver, click_name=matchday_name)
        matches = _read_matches(driver)
        if len(matches) >= MIN_MATCHES_PER_ROUND:
            return matches

    print(f"  [{matchday_name}] Proceeding with {len(matches)} match(es) after {MAX_RETRIES} retries")
    return matches


def _scrape_matchday(driver, matchday_name: str, base_url: str) -> dict:
    """For each match in the current matchday: click, parse, go back."""
    matches = _check_matches(driver, matchday_name, base_url)

    if not matches:
        print(f"  [{matchday_name}] No match rows found skipping")
        return {}

    print(f"  [{matchday_name}] Found {len(matches)} matches")
    results = {}

    for match_id, home_team in matches:
        # Check done before going to match page
        if is_match_done(matchday_name, home_team):
            cached = load_partial_match(matchday_name, home_team)
            if cached:
                results[match_id] = cached
                print(f"    [{matchday_name}] {home_team}, already done, loaded from cache")
            continue

        try:
            # Re-locate row by match_id 
            row = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//tbody[@data-match='{match_id}']"))
            )
            row.find_element(By.XPATH, MATCH_DIVIDER_XPATH).click()
            time.sleep(MATCH_PAGE_WAIT)

            parsed = parse_match(driver)
            match_data = {"match_id": match_id, "matchday": matchday_name, **parsed}

            saved_path = save_partial_match(matchday_name, match_data, home_team)
            results[match_id] = match_data
            print(f"    [{matchday_name}] {parsed.get('home_team')} vs {parsed.get('away_team')} {saved_path}")

            # Navigate back
            driver.back()
            time.sleep(CLICK_WAIT)

            # Wait for match list to reappear
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, MATCH_ROWS_XPATH))
            )

        except Exception as e:
            print(f"    [{matchday_name}] Match {match_id} - error: {e}")

    return results

def scrape_all_matchdays(driver, url: str) -> dict:
    print(f"Loading: {url}")
    driver.get(url)
    time.sleep(PAGE_LOAD_WAIT)

    # click cookie banner deny
    _deny_cookie_banner(driver)

    matchday_names = [x.text.strip() for x in _navbar_control(driver) if x.text.strip()]

    if not matchday_names:
        print("No matchdays found - check NAV_TOGGLE_XPATH / MATCHDAY_ITEMS_XPATH")
        return {}

    all_results = {}

    for name in matchday_names:
        print(f"\n[{name}] Selecting...")
        _navbar_control(driver, click_name=name)
        all_results[name] = _scrape_matchday(driver, name, url)
        print(f"  [{name}] Done - {len(all_results[name])} matches saved")


    return all_results
