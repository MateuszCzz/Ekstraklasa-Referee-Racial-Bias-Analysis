import time, re, requests, io
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from PIL import Image
import numpy as np

QUERY_RESULT_CSS = "li[data-layout='organic'] h2 a"
COOKIES_ACCEPT_BUTTON_CSS = ".accept-all"
CONSENT_IFRAME_CSS = "iframe[id^='sp_message_iframe']"
PLAYER_NAME_CSS = "h1.data-header__headline-wrapper"
BIRTH_DATE_CSS = "span[itemprop='birthDate']"
NATIONALITY_CSS = "span[itemprop='nationality']"
HEIGHT_CSS = "span[itemprop='height']"
PREFERRED_FOOT_TABLE_CSS = "//span[contains(@class,'info-table__content--regular') and contains(text(),'Foot:')]/following-sibling::span[contains(@class,'info-table__content--bold')]"
POSITION_TABLE_CSS = "//span[contains(@class,'info-table__content--regular') and contains(text(),'Position:')]/following-sibling::span[contains(@class,'info-table__content--bold')]"
PLAYER_IMAGE_CSS = "img.data-header__profile-image"

ELEMENT_LOAD_WAIT = 10 # delay for elements to become visible
SCROLL_PAUSE   = 2.0 # delay after scrolling

CROP_TOP_FRAC = 0.40    # skip this fraction from the top
CROP_BOTTOM_FRAC = 0.65 # skip this fraction from the bottom
CROP_SIDE_FRAC = 0.20   # skip this fraction from each side

def _dismiss_cookie_prompt(driver) -> None:
    # # cookies already cleared once
    if getattr(driver, "_cookies_accepted", False):
        return
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

        # set flag in driver
        driver._cookies_accepted = True

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

def _fitzpatrick_from_lightness(L: float) -> tuple[str, bool]:
    """Maps CIE L* to Fitzpatrick skin type label and POC flag"""
    if   L >= 70: return "Very light",  False
    elif L >= 60: return "Light",       False
    elif L >= 50: return "Medium light",False
    elif L >= 41: return "Medium",      True
    elif L >= 30: return "Medium dark", True
    else:         return "Dark",        True

def _cie_lightness(pixels_f: np.ndarray) -> float:
    """Returns CIE L* lightness (0 dark, 100 light)"""
    linear = np.where(pixels_f <= 0.04045, pixels_f / 12.92, ((pixels_f + 0.055) / 1.055) ** 2.4)
    Y = np.median(linear @ [0.2126, 0.7152, 0.0722])
    return 116 * (Y ** (1 / 3)) - 16 if Y > 0.008856 else 903.3 * Y

def _parse_name(driver) -> str:
    try:
        el = WebDriverWait(driver, ELEMENT_LOAD_WAIT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, PLAYER_NAME_CSS))
        )
        # strip prefix
        name_clean = re.sub(r"^#\d+\s*", "", el.text).strip()
        return name_clean
    except Exception as e:
        print(f" [parser] Failed to parse player full name: {e}")
        return ""
    
def _parse_birth_date(driver) -> tuple[str, str]:
    """Returns tuplet (date_of_birth, age) ('03/01/2006', '20')"""
    try:
        el = WebDriverWait(driver, ELEMENT_LOAD_WAIT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, BIRTH_DATE_CSS))
        )
        # split string into 2 groups, x/x/x and (x)
        date = re.match(r"(\d{2}/\d{2}/\d{4})\s*\((\d+)\)", el.text.strip())
        if date is None:
            raise ValueError(f" [parser] Failed to parse birth date from: '{el.text.strip()}'")
        return date.group(1), date.group(2)
    except Exception as e:
        print(f" [parser] Failed to parse player full name: {e}")
        return "", ""

def _parse_nationality(driver) -> str:
    try:
        el = WebDriverWait(driver, ELEMENT_LOAD_WAIT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, NATIONALITY_CSS))
        )
        return el.text.strip()
    except Exception as e:
        print(f" [parser] Failed to parse player nationality: {e}")
        return ""
    
def _parse_height(driver) -> str:
    try:
        el = WebDriverWait(driver, ELEMENT_LOAD_WAIT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, HEIGHT_CSS))
        )
        # strip unit and dots
        height_str = re.sub(r"[,. m]", "", el.text).strip()
        return height_str
    except Exception as e:
        print(f" [parser] Failed to parse player height: {e}")
        return ""
    
def _parse_foot(driver) -> str:
    try:
        el = WebDriverWait(driver, ELEMENT_LOAD_WAIT).until(
            EC.presence_of_element_located((By.XPATH, PREFERRED_FOOT_TABLE_CSS))
        )
        return el.text.strip()
    except Exception as e:
        print(f" [parser] Failed to find a preferred foot for the player (safe to ignore)")
        return ""
    
def _parse_position(driver) -> tuple[str, str]:
    """Returns (position_group, main_position) e.g. ('Midfield', 'Defensive Midfield')"""
    try:
        el = WebDriverWait(driver, ELEMENT_LOAD_WAIT).until(
            EC.presence_of_element_located((By.XPATH, POSITION_TABLE_CSS))
        )
        parts = [p.strip() for p in el.text.split("-", 1)]
        if len(parts) == 2:
            return parts[0], parts[1]
        elif parts[0] == "Goalkeeper":
            return "Goalkeeper", "Goalkeeper"
        else:
            raise ValueError(f" [parser] Failed to parse position from: {el.text.strip()}")

    except Exception as e:
        print(f" [parser] Failed to parse position: {e}")
        return "", ""

def _parse_image(driver) -> tuple[str, float, Image.Image|None]:
    """Extracts dominant skin hex and HSV lightness"""
    try:
        el = WebDriverWait(driver, ELEMENT_LOAD_WAIT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, PLAYER_IMAGE_CSS))
        )
        
        # get image src
        src = el.get_attribute("src") or ""
        if not src:
            raise ValueError(f"[parser] Failed to parse image source from: {el.get_attribute('src')}")
        
        # prepare headers for request
        cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
        headers = {"User-Agent": driver.execute_script("return navigator.userAgent;")}

        # make request for image
        response = requests.get(src, cookies=cookies, headers=headers, timeout=10)
        response.raise_for_status()

        # prepare image
        img = Image.open(io.BytesIO(response.content)).convert("RGB")
        w, h = img.size   

        # get dimensions acording to settings
        left   = int(w * CROP_SIDE_FRAC)
        right  = int(w * (1.0 - CROP_SIDE_FRAC))
        top    = int(h * CROP_TOP_FRAC)
        bottom = int(h * CROP_BOTTOM_FRAC)

        # crop image
        cropped = img.crop((left, top, right, bottom))  

        # prepare pixels array
        pixels = np.array(cropped).reshape(-1, 3)    

        # calc per channel median
        med_r, med_g, med_b = int(np.median(pixels[:, 0])),  \
            int(np.median(pixels[:, 1])),  \
            int(np.median(pixels[:, 2]))
        skin_hex = f"#{med_r:02x}{med_g:02x}{med_b:02x}"

        # normalize to 0,1
        pixels_f = pixels.astype(np.float64) / 255.0

        # calc lightness of the median pixel by 
        # RGB into luminance Y into CIE L* (0 dark, 100 light)
        L = _cie_lightness(pixels_f)

        # handle placeholder, almost white image
        if L > 95:
            print(f" [parser] Image transfermarkt returned placeholder (L={L}), skipping")
            return "", 0, None
        
        return skin_hex, round(L, 2), img
    
    except Exception as e:
        print(f" [parser] Failed to parse player image: {e}")
        return "", 0, None
    
def parse_player_page(driver) -> tuple[dict, Image.Image]:
    """Gets player data from given transfermarkt page."""
    data: dict = {}

    # dismiss cookies prompt
    _dismiss_cookie_prompt(driver)

    # scroll up down to force dynamic rendering
    _scroll_and_wait(driver)

    # get full name
    data["full_name"] = _parse_name(driver)

    # get birth date and age
    data["date_of_birth"], data["age"] = _parse_birth_date(driver)

    # get nationality
    data["nationality"] = _parse_nationality(driver)

    # get height
    data["height"] = _parse_height(driver)

    # get foot
    data["preferred_foot"] = _parse_foot(driver)

    # get position 
    data["position_group"], data["position"] = _parse_position(driver)

    # get player image/skin color
    data["skin_hex"], skin_lightness, img  = _parse_image(driver)

    if data["skin_hex"]:
        # map lightness to human info
        data["skin_color_group"], data["is_poc"] = _fitzpatrick_from_lightness(skin_lightness)
        data["skin_lightness"] = str(skin_lightness)
    else:
        # handle image placeholder
        data["skin_color_group"], data["is_poc"], data["skin_lightness"] = "", "", ""
    return data, img

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
            tm_id = parts[-1]
            tm_string = parts[-4]

            # get string with dash before profil "lionel-messi/profil"
            if "-" in tm_string:
                return tm_id, tm_string
            
            # if single word check for profil at next position
            if parts[-3] == "profil":
                return tm_id, tm_string
    return "", ""
