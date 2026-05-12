from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

QUERY_RESULT_CSS = "li[data-layout='organic'] h2 a"
COOKIES_ACCEPT_BUTTON_CSS = ".accept-all"
CONSENT_IFRAME_CSS = "iframe[id^='sp_message_iframe']"

ELEMENT_LOAD_WAIT = 10 # delay for elements to become visible
SCROLL_PAUSE   = 2.0 # delay after scrolling

def _dismiss_cookie_prompt(driver) -> None:
    # # cookies already cleared once
    # if getattr(driver, "_cookies_accepted", False):
    #     return
    try:
        # switch into consent iframe
        iframe = WebDriverWait(driver, ELEMENT_LOAD_WAIT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, CONSENT_IFRAME_CSS))
        )
        driver.switch_to.frame(iframe)

        # get button
        WebDriverWait(driver, ELEMENT_LOAD_WAIT).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, COOKIES_ACCEPT_BUTTON_CSS))
        ).click()

        # # set flag in driver
        # driver._cookies_accepted = True

    except Exception as e:
        print(f" [parser] Failed to dismiss cookies prompt, safe to ignore: {e}")
        pass

    finally:
        # switch back
        driver.switch_to.default_content()  

def _scroll_and_wait(driver) -> None:
    """Press key to trigger dynamic rendering"""
    from selenium.webdriver.common.keys import Keys
    body = driver.find_element(By.TAG_NAME, "body")
    body.send_keys(Keys.END)
    time.sleep(SCROLL_PAUSE)
    body.send_keys(Keys.HOME)
    time.sleep(SCROLL_PAUSE)

def parse_player_page(driver) -> dict:
    """Gets player data from given transfermarkt page."""
    data: dict = {}

    # dismiss cookies prompt
    _dismiss_cookie_prompt(driver)

    # scroll up down to force dynamic rendering
    _scroll_and_wait(driver)

    return data

def parse_search_results(driver) -> tuple[str, str]:
    """Gets player transfermarkt id and name from first matching search results."""
    try:
        WebDriverWait(driver, ELEMENT_LOAD_WAIT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, QUERY_RESULT_CSS))
        )
    except TimeoutException:
        return "", ""
    
    # get first link with spieler
    for link in driver.find_elements(By.CSS_SELECTOR, QUERY_RESULT_CSS):
        href = link.get_attribute("href")
        if "/profil/spieler/" in href:
            # split based on slashes
            parts = href.rstrip("/").split("/")
            # get number from the end
            tm_id     = parts[-1]
            # get string before profil "lionel-messi/profil/spieler/28003"
            # validate by checking for "-"
            tm_string = parts[-4] if "-" in parts[-4] else ""
            return tm_id, tm_string
    return "", ""
