import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

MATCHDATA_CSS  = "div.Opta-Matchdata"
TABS_CSS       = "div.Opta-Cf.Opta-Tabs.Opta-TabsMore"
STATS_TABLE    = "table.Opta-Striped"
MATCHDATA_WAIT = 10
SCROLL_PAUSE   = 1.0
TAB_PAUSE      = 1.0


def _parse_meta(driver) -> dict:
    """Extract matchdata referee/venue/attendance + team names + date."""
    WebDriverWait(driver, MATCHDATA_WAIT).until(EC.presence_of_element_located((By.CSS_SELECTOR, MATCHDATA_CSS)))

    matchdata_div = driver.find_element(By.CSS_SELECTOR, MATCHDATA_CSS)

    result = {}

    for dl in matchdata_div.find_elements(By.TAG_NAME, "dl"):
        try:
            key   = dl.find_element(By.TAG_NAME, "dt").text.strip().lower()
            value = dl.find_element(By.TAG_NAME, "dd").text.strip()
            if key:
                result[key] = value
        except Exception:
            pass

    # team names
    for side, css_class in (("home_team", "Opta-Home"), ("away_team", "Opta-Away")):
        try:
            result[side] = driver.find_element(
                By.CSS_SELECTOR, f"td.Opta-TeamName.{css_class}"
            ).text.strip()
        except Exception:
            pass

    # date
    try:
        result["date"] = driver.find_element(By.CSS_SELECTOR, "span.Opta-Date").text.strip()
    except Exception:
        pass

    return result


def _is_empty_row(row: dict) -> bool:
    for key, val in row.items():
        if key == "player":
            continue
        v = str(val).strip()
        if v and v not in ("-", "—", "–", ""):
            return False
    return True


def _parse_stats_table(driver) -> list[dict]:
    """Parse table of players data"""
    # wait till at least one player populated
    WebDriverWait(driver, MATCHDATA_WAIT).until(
        lambda d: any(
            th.text.strip()
            for th in d.find_elements(By.CSS_SELECTOR, f"{STATS_TABLE} tbody th.Opta-Player")
        )
    )

    table = driver.find_element(By.CSS_SELECTOR, STATS_TABLE)

    # column headers
    headers = []
    for th in table.find_elements(By.CSS_SELECTOR, "thead th"):
        abbr = th.find_elements(By.TAG_NAME, "abbr")
        if abbr:
            headers.append(abbr[0].get_attribute("title").strip().lower().replace(" ", "_"))
        else:
            text = th.text.strip()
            headers.append(text.lower() if text else "player")

    players = []
    for tr in table.find_elements(By.CSS_SELECTOR, "tbody tr"):
        th = tr.find_element(By.CSS_SELECTOR, "th")
        tds = tr.find_elements(By.CSS_SELECTOR, "td")

        if not th and not tds:
            continue

        row = {}

        # player name from th
        row["player"] = th.get_attribute("textContent").strip()

        # rest of stats from td
        for i, td in enumerate(tds):
            if i + 1 >= len(headers):
                break
            srt = td.get_attribute("data-srt")
            row[headers[i + 1]] = srt if srt is not None else td.text.strip()

        # skip on no stats
        if not row.get("player") or _is_empty_row(row):
            continue

        players.append(row)

    return players


def _click_table_nav(driver, team_name: str) -> None:
    """Click the tab matching team_name"""
    for a in driver.find_element(By.CSS_SELECTOR, TABS_CSS).find_elements(By.TAG_NAME, "a"):
        if a.text.strip() == team_name:
            a.click()
            time.sleep(TAB_PAUSE)
            return
    raise ValueError(f"Tab for '{team_name}' not found")


def parse_match(driver) -> dict:
    """Parse all data from the currently loaded match page"""
    result = _parse_meta(driver)

    # scroll down, then wait for table to become visible
    driver.execute_script("window.scrollBy(0, 600);")
    time.sleep(SCROLL_PAUSE)
    WebDriverWait(driver, MATCHDATA_WAIT).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, TABS_CSS))
    )

    result["home_stats"] = []
    result["away_stats"] = []

    for team, key in ((result.get("home_team"), "home_stats"), (result.get("away_team"), "away_stats")):
        if not team:
            continue
        try:
            _click_table_nav(driver, team)
            result[key] = _parse_stats_table(driver)
        except Exception as e:
            print(f"    [parser] Stats for '{team}' — error: {e}")

    return result