import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

PAGE_LOAD_WAIT  = 2.0   # after initial page load
CLICK_WAIT      = 2.5   # after clicking nav toggle or matchday

def enrich_player_data(driver, url: str) -> str:
    print(f"Loading: {url}")
    driver.get(url)
    time.sleep(PAGE_LOAD_WAIT)

    return " "
