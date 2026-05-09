from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

QUERY_RESULT_CSS = "li[data-layout='organic'] h2 a"

ELEMENT_LOAD_WAIT = 10 # delay for elements to become visible

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
